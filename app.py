
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

APP_VERSION = "V83 Clean Research Engine"
st.set_page_config(page_title="AI企業價值研究院 V83", page_icon="🏛", layout="wide")

# =========================
# 基礎工具
# =========================
TW_NAMES = {
    "2330":"台積電","2303":"聯電","2454":"聯發科","2308":"台達電","2317":"鴻海","3030":"德律",
    "3715":"定穎投控","6415":"矽力-KY","6830":"汎銓","6308":"台表科","5347":"世界先進",
    "2379":"瑞昱","3374":"精材","6570":"維田","3046":"建碁","9942":"茂順",
    "3105":"穩懋","8112":"至上","2049":"上銀","3596":"智易"
}

def norm_symbol(s: str) -> str:
    s = str(s or "2330").strip().upper()
    if not s:
        return "2330.TW"
    if "." in s:
        return s
    # 預設上市 .TW；若抓不到，程式會自動嘗試 .TWO
    return f"{s}.TW"

def base_code(symbol: str) -> str:
    return str(symbol).split(".")[0].upper()

def cname(symbol: str) -> str:
    c = base_code(symbol)
    return TW_NAMES.get(c, c)

@st.cache_data(ttl=900)
def load_hist(symbol: str, period="1y", interval="1d"):
    sym = norm_symbol(symbol)
    try:
        df = yf.download(sym, period=period, interval=interval, auto_adjust=False, progress=False)
        if df is None or df.empty:
            alt = sym.replace(".TW", ".TWO") if sym.endswith(".TW") else sym.replace(".TWO", ".TW")
            df = yf.download(alt, period=period, interval=interval, auto_adjust=False, progress=False)
            sym = alt if df is not None and not df.empty else sym
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df = df.reset_index()
        return sym, df
    except Exception:
        return sym, pd.DataFrame()

@st.cache_data(ttl=1800)
def load_info(symbol: str):
    sym = norm_symbol(symbol)
    try:
        t = yf.Ticker(sym)
        info = t.info or {}
        if not info:
            alt = sym.replace(".TW", ".TWO") if sym.endswith(".TW") else sym.replace(".TWO", ".TW")
            t = yf.Ticker(alt)
            info = t.info or {}
            sym = alt
        return sym, info
    except Exception:
        return sym, {}

@st.cache_data(ttl=3600)
def load_statements(symbol: str):
    sym = norm_symbol(symbol)
    try:
        t = yf.Ticker(sym)
        fin = t.financials
        bal = t.balance_sheet
        cf = t.cashflow
        if (fin is None or fin.empty) and sym.endswith(".TW"):
            alt = sym.replace(".TW", ".TWO")
            t = yf.Ticker(alt)
            fin, bal, cf = t.financials, t.balance_sheet, t.cashflow
            sym = alt
        return sym, fin, bal, cf
    except Exception:
        return sym, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def num(x, default=np.nan):
    try:
        if x is None:
            return default
        if isinstance(x, str) and x.strip() in ["", "N/A", "None", "nan"]:
            return default
        return float(str(x).replace(",", "").replace("%", ""))
    except Exception:
        return default

def fmt(x, digits=2):
    try:
        if x is None or pd.isna(float(x)):
            return "N/A"
        return f"{float(x):,.{digits}f}"
    except Exception:
        return str(x)

def safe_df(df):
    if df is None:
        return pd.DataFrame()
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    out = df.copy()
    out.columns = [str(c) for c in out.columns]
    for c in out.columns:
        out[c] = out[c].map(lambda v: "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v))
    return out

def extract_quote(symbol):
    used, info = load_info(symbol)
    used2, hist = load_hist(used, "6mo", "1d")
    price = np.nan
    if not hist.empty and "Close" in hist:
        price = num(hist["Close"].dropna().iloc[-1])
    price = num(info.get("currentPrice"), price)
    eps = num(info.get("trailingEps"))
    pe = num(info.get("trailingPE"))
    pb = num(info.get("priceToBook"))
    roe = num(info.get("returnOnEquity"))
    market_cap = num(info.get("marketCap"))
    revenue = num(info.get("totalRevenue"))
    gross_margin = num(info.get("grossMargins"))
    op_margin = num(info.get("operatingMargins"))
    fcf = num(info.get("freeCashflow"))
    if pd.isna(eps) and pd.notna(price) and pd.notna(pe) and pe > 0:
        eps = price / pe
    return {
        "symbol": used,
        "name": info.get("longName") or info.get("shortName") or cname(used),
        "price": price, "eps": eps, "pe": pe, "pb": pb, "roe": roe,
        "market_cap": market_cap, "revenue": revenue,
        "gross_margin": gross_margin, "operating_margin": op_margin, "free_cashflow": fcf
    }

# =========================
# 產業 / 模型
# =========================
def profile(symbol):
    c = base_code(symbol)
    db = {
        "2330": ["電子","半導體","晶圓代工","先進製程","AI/HPC","中游","Foundry晶圓代工","成熟成長型","技術/規模/客戶"],
        "2303": ["電子","半導體","晶圓代工","成熟製程","車用/工控","中游","Foundry晶圓代工","成熟循環型","產能/客戶"],
        "5347": ["電子","半導體","晶圓代工","特殊製程","車用/工控","中游","特殊製程代工","成熟循環型","製程/客戶"],
        "3030": ["電子","設備","AOI檢測設備","PCB/半導體檢測","自動化檢測","中游","設備銷售","成長循環型","技術/客戶認證"],
        "3374": ["電子","半導體","封測/影像感測","晶圓級封裝","CIS/先進封裝","中游","封測服務","成長循環型","製程/客戶"],
        "6570": ["電子","工業電腦","嵌入式系統","邊緣運算","AIoT","中游","硬體設備/系統整合","成長型","客製化/通路"],
    }
    row = db.get(c, ["待分類","待分類","待分類","待分類","待分類","待確認","待確認","待確認","待確認"])
    return {
        "公司名稱": cname(symbol), "股票代號": norm_symbol(symbol),
        "Level 1 大類": row[0], "Level 2 產業": row[1], "Level 3 次產業": row[2],
        "Level 4 細分領域": row[3], "Level 5 投資主題": row[4],
        "產業鏈位置": row[5], "商業模式": row[6], "產業成熟度": row[7], "護城河": row[8]
    }

def model_template(symbol):
    p = profile(symbol)
    text = "".join(str(v) for v in p.values())
    if "金融" in text:
        return "金融股模型", "金融股價值主要由PB、ROE、資本品質、股利與風險控管驅動。"
    if any(k in text for k in ["設備","AOI","自動化","檢測"]):
        return "成長型設備股模型", "設備股受產業景氣、訂單週期與成長率影響，估值重視PE/PEG/EBO與產業前景。"
    if any(k in text for k in ["晶圓代工","半導體","先進製程","AI"]):
        return "成熟科技龍頭/成長科技模型", "科技股價值來自護城河、現金流、成長性、技術領先與法人覆蓋。"
    if any(k in text for k in ["航運","鋼鐵","塑化","面板"]):
        return "循環產業模型", "循環產業估值重視PB/NAV、景氣循環、供需週期與資產價值。"
    return "一般企業價值模型", "資料不足以歸類到特殊模板，採PE/PB/DCF/EBO/ESG/法人綜合模型。"

def rating_weights(symbol):
    t, reason = model_template(symbol)
    if t == "成長型設備股模型":
        rows = [
            ["企業品質",20,"技術與客戶認證重要，但設備股仍受景氣循環影響"],
            ["財務體質",15,"財務穩健重要，但非最主要定價因子"],
            ["估值吸引力",25,"設備股市場常用PE/PEG反映成長與訂單循環"],
            ["法人籌碼",15,"法人與主力資金常提前反映訂單與景氣轉折"],
            ["ESG",5,"ESG屬輔助因子，對設備股短期定價權重較低"],
            ["產業前景",20,"設備需求高度取決於資本支出與產業景氣"],
        ]
    elif t == "成熟科技龍頭/成長科技模型":
        rows = [
            ["企業品質",30,"科技龍頭價值主要來自技術護城河、市占率與客戶黏著"],
            ["財務體質",25,"現金流、ROE與資本配置能力直接支撐企業價值"],
            ["估值吸引力",15,"成熟科技股估值重要，但不能高於基本面品質"],
            ["法人籌碼",10,"法人覆蓋高，短期影響存在但資訊較透明"],
            ["ESG",10,"國際資金與大型科技企業ESG權重提高"],
            ["產業前景",10,"成熟龍頭已反映部分產業前景，故不過度放大"],
        ]
    else:
        rows = [
            ["企業品質",25,"一般企業價值首先取決於商業模式與競爭力"],
            ["財務體質",20,"財務穩健度決定企業長期存續與估值基礎"],
            ["估值吸引力",20,"合理價格與安全邊際是投資決策核心"],
            ["法人籌碼",15,"資金流向影響市場重估速度"],
            ["ESG",10,"ESG作為風險折價或溢價調整因子"],
            ["產業前景",10,"產業前景影響成長假設與估值倍數"],
        ]
    return t, reason, pd.DataFrame(rows, columns=["評級項目","權重%","權重來源/理由"])

def value_weights(symbol):
    t, reason = model_template(symbol)
    if t == "成長型設備股模型":
        rows = [["PE",25,"設備股市場主流估值"],["EBO",20,"高ROE設備商適用超額報酬模型"],["DCF",10,"設備股受循環影響，DCF作輔助"],["法人",15,"訂單循環常由法人資金提前反映"],["ESG",5,"ESG輔助風險調整"],["產業",25,"CAPEX循環是設備股主要驅動"]]
    elif t == "成熟科技龍頭/成長科技模型":
        rows = [["DCF",30,"現金流與護城河是大型科技企業核心"],["EBO",20,"ROE/超額報酬反映競爭優勢"],["PE",15,"市場倍數作為輔助"],["ESG",10,"國際資金重視永續治理"],["法人",15,"法人覆蓋高且影響資金評價"],["產業",10,"產業景氣影響成長假設"]]
    else:
        rows = [["DCF",20,"一般企業長期價值基礎"],["PE",20,"市場常用倍數"],["PB",10,"資產價值輔助"],["EBO",15,"ROE與超額報酬"],["ESG",10,"風險與溢價調整"],["法人",15,"市場資金預期"],["產業",10,"產業景氣與成長性"]]
    return t, reason, pd.DataFrame(rows, columns=["模型","權重%","權重來源/理由"])

# =========================
# 研究引擎
# =========================
def financial_research(q):
    rows = [
        ["現價", fmt(q["price"]), "Yahoo Finance / 歷史收盤"],
        ["EPS", fmt(q["eps"]), "Yahoo trailing EPS；若缺值用價格/PE反推"],
        ["PE", fmt(q["pe"]), "Yahoo trailing PE"],
        ["PB", fmt(q["pb"]), "Yahoo Price to Book"],
        ["ROE", fmt(q["roe"]*100 if pd.notna(q["roe"]) else np.nan) + "%", "Yahoo returnOnEquity"],
        ["營收", fmt(q["revenue"]/1e6 if pd.notna(q["revenue"]) else np.nan), "百萬元"],
        ["毛利率", fmt(q["gross_margin"]*100 if pd.notna(q["gross_margin"]) else np.nan) + "%", "Yahoo grossMargins"],
        ["營益率", fmt(q["operating_margin"]*100 if pd.notna(q["operating_margin"]) else np.nan) + "%", "Yahoo operatingMargins"],
        ["自由現金流", fmt(q["free_cashflow"]/1e6 if pd.notna(q["free_cashflow"]) else np.nan), "百萬元"],
    ]
    score = 50
    if pd.notna(q["eps"]) and q["eps"] > 0: score += 15
    if pd.notna(q["roe"]) and q["roe"] > 0.12: score += 15
    if pd.notna(q["pe"]): score += 10
    if pd.notna(q["pb"]): score += 10
    score = max(0, min(100, score))
    rows += [["財報品質分數", fmt(score), "EPS/ROE/PE/PB可得性與品質代理"],
             ["財報燈號", "🟢 綠燈" if score>=75 else "🟡 黃燈" if score>=55 else "🔴 紅燈", "依財報品質分數轉換"]]
    return pd.DataFrame(rows, columns=["項目","數值","資料來源/說明"])

def industry_research(symbol):
    p = profile(symbol)
    text = "".join(p.values())
    health = 60
    if any(k in text for k in ["AI","半導體","先進製程","電力","光通訊","散熱"]): health += 20
    if any(k in text for k in ["面板","航運","鋼鐵","塑化"]): health -= 5
    health = max(0, min(100, health))
    base = pd.DataFrame([
        ["產業定位", p["Level 2 產業"], "主要產業"],
        ["次產業", p["Level 3 次產業"], "細分產業"],
        ["產業鏈位置", p["產業鏈位置"], "上游/中游/下游"],
        ["產業健康度", fmt(health), "景氣、成長主題、產業循環代理"],
        ["景氣燈號", "🟢 擴張" if health>=80 else "🟡 中立" if health>=55 else "🔴 低迷", "由產業健康度轉換"],
        ["主要驅動", p["Level 5 投資主題"], "需求來源與投資主題"],
    ], columns=["項目","內容","說明"])
    five = pd.DataFrame([
        ["產業競爭強度","中高","同業價格與技術競爭"],
        ["新進入者威脅","中","資本與技術門檻影響"],
        ["替代品威脅","中","技術迭代或替代方案"],
        ["供應商議價力","中","關鍵材料/設備供應商"],
        ["客戶議價力","中高","大客戶集中度影響"],
    ], columns=["五力項目","判斷","說明"])
    return base, five, health

def competitors(symbol):
    c = base_code(symbol)
    if c == "2330":
        rows = [["台積電","2330.TW","台灣","本公司/晶圓代工"],["Samsung Foundry","005930.KS","韓國","全球競爭"],["Intel Foundry","INTC","美國","全球競爭"],["GlobalFoundries","GFS","美國","全球競爭"],["聯電","2303.TW","台灣","成熟製程同業"],["世界先進","5347.TWO","台灣","特殊製程同業"]]
    elif c == "3030":
        rows = [["德律","3030.TW","台灣","本公司/AOI檢測"],["由田","3455.TW","台灣","AOI設備"],["致茂","2360.TW","台灣","測試設備"],["Camtek","CAMT","以色列","全球AOI/檢測"],["Koh Young","098460.KQ","韓國","3D檢測"],["Mirtec","N/A","韓國","AOI設備"]]
    else:
        rows = [["台積電","2330.TW","台灣","大型指標同業/參考"],["聯電","2303.TW","台灣","半導體參考"],["世界先進","5347.TWO","台灣","半導體參考"]]
    return pd.DataFrame(rows, columns=["公司","代碼","國家","競爭/關聯角色"])

def peer_compare(symbol):
    rows = []
    for _, r in competitors(symbol).iterrows():
        sym = r["代碼"]
        if sym == "N/A":
            rows.append([r["公司"],sym,r["國家"],r["競爭/關聯角色"],"N/A","N/A","N/A","N/A"])
            continue
        q = extract_quote(sym)
        rows.append([r["公司"],sym,r["國家"],r["競爭/關聯角色"],fmt(q["price"]),fmt(q["eps"]),fmt(q["pe"]),fmt(q["pb"])])
    return pd.DataFrame(rows, columns=["公司","代碼","國家","角色","現價","EPS","PE","PB"])

def valuation_models(symbol, q):
    eps, price, pe, pb = q["eps"], q["price"], q["pe"], q["pb"]
    vals, rows = [], []
    if pd.notna(eps):
        for name, mult in [("PE保守價",15),("PE基準價",18),("PE樂觀價",22),("EBO代理價",20),("DCF代理價",19)]:
            val = eps * mult
            rows.append([name, fmt(val), f"EPS({fmt(eps)}) × {mult}", "納入"])
            vals.append(val)
    if pd.notna(price) and pd.notna(pb) and pb > 0:
        bvps = price / pb
        val = bvps * 2.5
        rows.append(["PB代理價", fmt(val), f"BVPS({fmt(bvps)}) × 2.5", "納入"])
        vals.append(val)
    fair = float(np.nanmedian(vals)) if vals else np.nan
    rows.append(["AI企業合理價", fmt(fair), "納入模型中位數，降低極端值影響", "最終"])
    return pd.DataFrame(rows, columns=["模型","合理價","計算方式","狀態"]), fair

def esg_value(symbol, q):
    eps = q["eps"]
    company_esg = 70
    industry_esg = 65
    diff = company_esg - industry_esg
    premium = max(0, min(0.2, diff * 0.005))
    base_pe = 18
    base = eps * base_pe if pd.notna(eps) else np.nan
    plus = base * premium if pd.notna(base) else np.nan
    fair = base + plus if pd.notna(base) else np.nan
    return pd.DataFrame([
        ["公司ESG分數", fmt(company_esg), "代理ESG分數；正式版可接永續報告/評級資料"],
        ["產業ESG平均", fmt(industry_esg), "同產業平均代理"],
        ["ESG超額分數", fmt(diff), "公司ESG - 產業平均"],
        ["ESG溢價率", f"{premium*100:.1f}%", "ESG超額分數 × 0.5%，上限20%"],
        ["ESG基礎估值", fmt(base), f"EPS × 基礎PE = {fmt(eps)} × {base_pe}"],
        ["ESG溢價股價金額", fmt(plus), "ESG基礎估值 × ESG溢價率"],
        ["ESG合理價", fmt(fair), "ESG基礎估值 + ESG溢價金額"],
    ], columns=["項目","數值","計算說明"]), fair

def institutional_value(q):
    inst_score = 60
    price, eps, pe = q["price"], q["eps"], q["pe"]
    factor = 1 + max(-0.18, min(0.22, (inst_score-60)/180))
    target = eps * (pe if pd.notna(pe) else 18) * factor if pd.notna(eps) else (price * factor if pd.notna(price) else np.nan)
    return pd.DataFrame([
        ["外資分數", fmt(inst_score), "代理法人分數"],
        ["投信分數", fmt(inst_score), "代理法人分數"],
        ["自營商分數", fmt(inst_score), "代理法人分數"],
        ["法人共識分數", fmt(inst_score), "三大法人代理分數"],
        ["法人估值係數", fmt(factor), "1 + (法人分數-60)/180，上下限修正"],
        ["法人共識價", fmt(target), "EPS×PE×法人係數；EPS缺值則現價×係數"],
        ["法人燈號", "🟡 中立", "依法人共識分數轉換"],
    ], columns=["項目","數值","計算說明"]), target

def score_components(symbol, q):
    template, reason, wdf = rating_weights(symbol)
    _, _, health = industry_research(symbol)
    quality = 60
    if profile(symbol)["護城河"] != "待確認": quality += 10
    if pd.notna(q["roe"]): quality += min(15, max(-10, q["roe"]*50))
    finance = 60 + (10 if pd.notna(q["eps"]) and q["eps"]>0 else 0) + (15 if pd.notna(q["roe"]) and q["roe"]>0.12 else 0)
    valuation = 65 + (10 if pd.notna(q["pe"]) and q["pe"]<20 else -10 if pd.notna(q["pe"]) and q["pe"]>40 else 0)
    inst, esg = 60, 70
    score_map = {"企業品質":quality,"財務體質":finance,"估值吸引力":valuation,"法人籌碼":inst,"ESG":esg,"產業前景":health}
    rows, total = [], 0
    for _, r in wdf.iterrows():
        item = r["評級項目"]; weight = float(r["權重%"]); score = max(0,min(100,float(score_map.get(item,60))))
        contrib = score * weight / 100
        total += contrib
        rows.append([item, f"{weight:.0f}%", fmt(score), fmt(contrib), r["權重來源/理由"]])
    grade = "SS級" if total >= 90 else "S級" if total >= 85 else "A級" if total >= 80 else "B級" if total >= 70 else "C級" if total >= 60 else "D級"
    return template, reason, total, grade, pd.DataFrame(rows, columns=["項目","權重","得分","貢獻","權重來源/理由"])

def consensus_value(symbol, q):
    vdf, fair = valuation_models(symbol, q)
    edf, esg_fair = esg_value(symbol, q)
    idf, inst_fair = institutional_value(q)
    template, reason, wdf = value_weights(symbol)
    pe_val = num(vdf[vdf["模型"]=="PE基準價"]["合理價"].iloc[0]) if not vdf[vdf["模型"]=="PE基準價"].empty else np.nan
    pb_val = num(vdf[vdf["模型"]=="PB代理價"]["合理價"].iloc[0]) if not vdf[vdf["模型"]=="PB代理價"].empty else np.nan
    dcf_val = num(vdf[vdf["模型"]=="DCF代理價"]["合理價"].iloc[0]) if not vdf[vdf["模型"]=="DCF代理價"].empty else np.nan
    ebo_val = num(vdf[vdf["模型"]=="EBO代理價"]["合理價"].iloc[0]) if not vdf[vdf["模型"]=="EBO代理價"].empty else np.nan
    industry_val = np.nanmedian([x for x in [pe_val,pb_val,dcf_val,ebo_val,esg_fair,inst_fair] if pd.notna(x)]) if any(pd.notna(x) for x in [pe_val,pb_val,dcf_val,ebo_val,esg_fair,inst_fair]) else np.nan
    lookup = {"DCF":dcf_val,"PE":pe_val,"PB":pb_val,"EBO":ebo_val,"ESG":esg_fair,"法人":inst_fair,"產業":industry_val}
    rows, total_w, weighted = [], 0, 0
    for _, r in wdf.iterrows():
        model = r["模型"]; w = float(r["權重%"]); val = lookup.get(model, np.nan)
        if pd.notna(val):
            total_w += w; weighted += val*w; contrib = val*w/100
        else:
            contrib = np.nan
        rows.append([model, fmt(val), f"{w:.0f}%", fmt(contrib), r["權重來源/理由"]])
    consensus = weighted/total_w if total_w else np.nan
    rows.append(["AI共識價", fmt(consensus), "重新正規化後100%", "最終", f"模型模板：{template}；{reason}"])
    return pd.DataFrame(rows, columns=["模型","價格","權重","加權貢獻","權重來源/理由"]), consensus

def decision(symbol, q):
    cdf, cons = consensus_value(symbol, q)
    price = q["price"]
    margin = (cons-price)/cons*100 if pd.notna(cons) and pd.notna(price) and cons>0 else np.nan
    valuation_state = "明顯低估" if pd.notna(margin) and margin>=30 else "低估" if pd.notna(margin) and margin>=15 else "合理" if pd.notna(margin) and margin>=-15 else "高估" if pd.notna(margin) and margin>=-30 else "明顯高估" if pd.notna(margin) else "資料不足"
    _, _, total, grade, _ = score_components(symbol, q)
    q_state = "高" if total>=80 else "中" if total>=65 else "低"
    if valuation_state in ["明顯低估","低估"] and q_state == "高":
        advice = "積極布局" if valuation_state == "明顯低估" else "分批布局"
    elif valuation_state in ["明顯低估","低估"] and q_state == "中":
        advice = "分批布局"
    elif valuation_state == "合理":
        advice = "觀察"
    elif valuation_state == "高估":
        advice = "減碼"
    else:
        advice = "避開/賣出" if valuation_state == "明顯高估" else "資料不足"
    return pd.DataFrame([
        ["目前股價", fmt(price), "Yahoo/即時價格"],
        ["AI共識價", fmt(cons), "模型加權共識價"],
        ["安全邊際", f"{margin:.1f}%" if pd.notna(margin) else "N/A", "(AI共識價 - 現價) / AI共識價"],
        ["估值判定", valuation_state, "30%以上明顯低估；15~30低估；±15合理；-15~-30高估；-30以下明顯高估"],
        ["AI總分", fmt(total), "企業品質、財務、估值、法人、ESG、產業加權"],
        ["AI評級", grade, "90+ SS；85~89 S；80~84 A；70~79 B；60~69 C；60以下 D"],
        ["品質區間", q_state, "80以上高；65~79中；65以下低"],
        ["投資建議", advice, "依估值判定 × 品質區間決策矩陣"],
    ], columns=["項目","結果","依據"])

# =========================
# 畫面
# =========================
def hero():
    st.markdown("""
    <style>
    .hero{border-radius:32px;padding:42px 46px;background:radial-gradient(circle at 12% 20%, rgba(212,175,55,.30), transparent 25%),linear-gradient(135deg,#020617 0%,#0f172a 34%,#1e3a8a 68%,#0f766e 100%);color:white;box-shadow:0 20px 46px rgba(2,6,23,.35);border:1px solid rgba(212,175,55,.38);margin:16px 0 28px 0;}
    .hero h1{font-size:48px;font-weight:950;margin:0 0 10px 0}.hero h2{font-size:24px;font-weight:850;color:#f8e6a0;margin:0 0 14px 0}.hero p{font-size:17px;opacity:.95;margin:6px 0}
    </style>
    <div class="hero">
      <h1>🏛 AI企業價值研究院</h1>
      <h2>Enterprise Valuation Institute｜V83 Clean Research Engine</h2>
      <p>企業價值 × 財報研究 × 產業研究 × 全球競爭 × ESG × 法人資金 × AI共識價</p>
      <p><b>找出企業真正價值，而非追逐市場情緒。</b></p>
    </div>
    """, unsafe_allow_html=True)

def kpi(items):
    cols = st.columns(min(4, len(items)))
    for col, (a,b,c) in zip(cols, items):
        col.markdown(f"<div style='border-radius:18px;padding:16px;background:#0f172a;color:white'><div style='opacity:.7'>{a}</div><div style='font-size:26px;font-weight:900;color:#f8e6a0'>{b}</div><div style='opacity:.65;font-size:12px'>{c}</div></div>", unsafe_allow_html=True)

def kline_page(symbol):
    used, df = load_hist(symbol, "1y", "1d")
    st.header(f"📈 K線中心：{cname(used)} / {used}")
    if df.empty:
        st.warning("目前抓不到K線資料，請確認代碼。")
        return
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA60"] = df["Close"].rolling(60).mean()
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.72,0.28])
    fig.add_trace(go.Candlestick(x=df["Date"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="K線"), row=1,col=1)
    for ma in ["MA5","MA20","MA60"]:
        fig.add_trace(go.Scatter(x=df["Date"], y=df[ma], mode="lines", name=ma), row=1,col=1)
    fig.add_trace(go.Bar(x=df["Date"], y=df["Volume"], name="成交量"), row=2,col=1)
    fig.update_layout(height=720, xaxis_rangeslider_visible=False, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

def monitor_page(symbol):
    st.header("📊 監控中心")
    watch = st.text_area("監控清單", value=f"{norm_symbol(symbol)},2330.TW,2303.TW,2454.TW,3030.TW")
    syms = [x.strip() for x in watch.replace("，",",").split(",") if x.strip()]
    rows = []
    for s in syms[:20]:
        q = extract_quote(s)
        rows.append([q["name"], q["symbol"], fmt(q["price"]), fmt(q["eps"]), fmt(q["pe"]), fmt(q["pb"])])
    st.dataframe(pd.DataFrame(rows, columns=["公司","代碼","現價","EPS","PE","PB"]), use_container_width=True, hide_index=True)

def enterprise_page(symbol):
    q = extract_quote(symbol)
    hero()
    st.subheader(f"研究標的：{q['name']} / {q['symbol']}")
    kpi([("現價", fmt(q["price"]), "Yahoo Finance"),("EPS", fmt(q["eps"]), "Trailing EPS"),("PE", fmt(q["pe"]), "本益比"),("PB", fmt(q["pb"]), "股價淨值比")])
    tabs = st.tabs(["①公司DNA","②產業研究院","③全球競爭研究院","④同業比較研究院","⑤財報研究院","⑥企業評價研究院","⑦ESG研究院","⑧法人研究院","⑨AI共識價研究院","⑩AI評級透明化中心","⑪模型依據中心","⑫投資決策中心"])
    with tabs[0]:
        st.dataframe(pd.DataFrame(list(profile(q["symbol"]).items()), columns=["項目","內容"]), use_container_width=True, hide_index=True)
    with tabs[1]:
        base, five, _ = industry_research(q["symbol"])
        st.dataframe(base, use_container_width=True, hide_index=True)
        st.markdown("#### 五力分析")
        st.dataframe(five, use_container_width=True, hide_index=True)
    with tabs[2]:
        st.dataframe(competitors(q["symbol"]), use_container_width=True, hide_index=True)
    with tabs[3]:
        st.dataframe(peer_compare(q["symbol"]), use_container_width=True, hide_index=True)
    with tabs[4]:
        st.dataframe(financial_research(q), use_container_width=True, hide_index=True)
        used, fin, bal, cf = load_statements(q["symbol"])
        with st.expander("原始損益表 / 資產負債表 / 現金流量表"):
            st.write("損益表")
            st.dataframe(safe_df(fin.head(20)), use_container_width=True)
            st.write("資產負債表")
            st.dataframe(safe_df(bal.head(20)), use_container_width=True)
            st.write("現金流量表")
            st.dataframe(safe_df(cf.head(20)), use_container_width=True)
    with tabs[5]:
        vdf, fair = valuation_models(q["symbol"], q)
        st.dataframe(vdf, use_container_width=True, hide_index=True)
        st.markdown("#### 企業評價模型權重依據")
        _, _, wdf = value_weights(q["symbol"])
        st.dataframe(wdf, use_container_width=True, hide_index=True)
    with tabs[6]:
        edf, _ = esg_value(q["symbol"], q)
        st.dataframe(edf, use_container_width=True, hide_index=True)
    with tabs[7]:
        idf, _ = institutional_value(q)
        st.dataframe(idf, use_container_width=True, hide_index=True)
    with tabs[8]:
        cdf, _ = consensus_value(q["symbol"], q)
        st.dataframe(cdf, use_container_width=True, hide_index=True)
    with tabs[9]:
        template, reason, total, grade, comp = score_components(q["symbol"], q)
        st.metric("AI評級", grade, f"總分 {fmt(total)}")
        st.caption(f"權重模板：{template}｜{reason}")
        st.dataframe(comp, use_container_width=True, hide_index=True)
    with tabs[10]:
        template, reason, rw = rating_weights(q["symbol"])
        vt, vr, vw = value_weights(q["symbol"])
        st.info("V83原則：每個權重、評級、共識價與投資建議都必須可追溯、可驗證、可解釋。")
        st.markdown(f"#### 評級模板：{template}")
        st.write(reason)
        st.dataframe(rw, use_container_width=True, hide_index=True)
        st.markdown(f"#### 估值模板：{vt}")
        st.write(vr)
        st.dataframe(vw, use_container_width=True, hide_index=True)
        st.markdown("#### 安全邊際規則")
        st.dataframe(pd.DataFrame([["30%以上","明顯低估"],["15%~30%","低估"],["-15%~15%","合理"],["-30%~-15%","高估"],["-30%以下","明顯高估"]], columns=["安全邊際","判定"]), use_container_width=True, hide_index=True)
    with tabs[11]:
        st.dataframe(decision(q["symbol"], q), use_container_width=True, hide_index=True)

# =========================
# 主程式
# =========================
st.markdown("""
<div style="padding:22px;border-radius:20px;background:#0f172a;color:white;margin-bottom:16px;">
  <div style="font-size:24px;font-weight:900;">📈 AI企業價值研究院</div>
  <div style="font-size:14px;">V83 Clean Research Engine｜企業評價 × 財報研究 × ESG × 法人 × AI共識價</div>
</div>
""", unsafe_allow_html=True)

page = st.radio("主選單", ["🏠首頁","📊監控","📈K線","🏛企業價值研究院","⚙設定"], horizontal=True)
raw = st.text_input("搜尋股票名稱或代碼", value="2330", placeholder="例如：2330、台積電、3030")
if raw in TW_NAMES.values():
    raw = next(k for k,v in TW_NAMES.items() if v == raw)
symbol = norm_symbol(raw)
q0 = extract_quote(symbol)
st.caption(f"目前全站分析：{q0['name']} / {q0['symbol']}")

if page == "🏠首頁":
    hero()
    kpi([("研究引擎","V83","乾淨重建，不再接舊空白頁"),("財報研究院","已併入","含原始財表展開"),("AI共識價","已啟用","權重與貢獻透明"),("目前標的",f"{q0['name']}",q0["symbol"])])
    st.markdown("### 🚀 研究院模組")
    st.dataframe(pd.DataFrame([
        ["公司DNA","公司定位、商業模式、產業鏈、護城河"],
        ["產業研究院","產業健康度、景氣燈號、五力分析"],
        ["財報研究院","EPS/PE/PB/ROE/現金流與原始財表"],
        ["企業評價研究院","PE/PB/DCF/EBO代理模型與權重"],
        ["ESG研究院","ESG溢價與ESG合理價"],
        ["法人研究院","法人分數、估值係數、法人共識價"],
        ["AI共識價研究院","模型價格、權重、貢獻、最終共識價"],
        ["投資決策中心","安全邊際、AI評級、投資建議"],
    ], columns=["模組","說明"]), use_container_width=True, hide_index=True)
elif page == "📊監控":
    monitor_page(symbol)
elif page == "📈K線":
    kline_page(symbol)
elif page == "🏛企業價值研究院":
    enterprise_page(symbol)
else:
    st.header("⚙設定")
    st.write("V83 Clean Research Engine。研究與教學用途，非投資建議。")
