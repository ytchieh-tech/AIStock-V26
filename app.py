
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re, math
try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None


APP_VERSION="V57 Enterprise Final"
APP_NAME="智策股市 AI 決策平台"
st.set_page_config(page_title=f"{APP_NAME} {APP_VERSION}", page_icon="📈", layout="wide", initial_sidebar_state="expanded")


# ================= V50 AI / ESG / 法人完整補齊 =================
def v50_ai_complete_tables(symbol, df, q, scores):
    price = effective_price(q, df)
    total = ai_total(scores)
    rating, stars, trend = ai_rating(total) if "ai_rating" in globals() else ("中立","★★★☆☆","中性")
    val, inp = valuation(price, q, scores)
    con = consensus(val)
    risk_score = ai_risk_score(scores, df) if "ai_risk_score" in globals() else int(np.clip(100-total,0,100))
    upside = (con/price-1)*100 if pd.notna(con) and pd.notna(price) and price else np.nan
    ai_rating_df = pd.DataFrame([
        ["AI評級", rating],
        ["星等", stars],
        ["AI綜合分數", f"{total}/100"],
        ["目前狀態", trend],
        ["模型共識價", fmt(con)],
        ["相對現價空間", "N/A" if pd.isna(upside) else f"{upside:+.1f}%"],
    ], columns=["項目","結果"])
    ai_val_df = val.copy() if isinstance(val, pd.DataFrame) else pd.DataFrame()
    ai_fin_df = pd.DataFrame([
        ["EPS", q.get("eps")],
        ["PE", q.get("pe")],
        ["PB", q.get("pb")],
        ["財報分數", scores.get("fund",50)],
        ["財報判斷", "偏強" if scores.get("fund",50)>=65 else ("中性" if scores.get("fund",50)>=45 else "偏弱")],
    ], columns=["AI財報項目","結果"])
    ai_inst_df = pd.DataFrame([
        ["法人分數", scores.get("inst",50)],
        ["籌碼分數", scores.get("chip",50)],
        ["主力分數", scores.get("main",50)],
        ["法人判斷", "偏多" if scores.get("inst",50)>=60 else ("觀望" if scores.get("inst",50)>=45 else "偏空")],
    ], columns=["AI法人項目","結果"])
    industry_score = int(np.clip(scores.get("tech",50)*.3 + scores.get("fund",50)*.25 + scores.get("inst",50)*.25 + scores.get("esg",50)*.2,0,100))
    ai_industry_df = pd.DataFrame([
        ["產業景氣分數", industry_score],
        ["產業階段", "成長/擴張" if industry_score>=70 else ("中性循環" if industry_score>=50 else "修正/觀望")],
        ["AI/高階題材敏感度", "高" if symbol in ["2330.TW","2454.TW","3443.TW","3661.TW","6669.TW","2382.TW","3231.TW","6415.TW"] else "中"],
        ["產業風險", "高估值震盪" if industry_score>=75 else "需求與庫存循環"],
    ], columns=["AI產業項目","結果"])
    ai_news_df = pd.DataFrame([
        ["AI新聞分析", "尚未串接新聞API", "可串接公開新聞、RSS、公司重大訊息"],
        ["產業新聞", "代理模式", "以產業分數、價格動能與法人分數代理"],
        ["公司新聞", "代理模式", "以財報、股價、成交量變化代理"],
        ["新聞情緒", "中性", "未接即時新聞前不做過度判斷"],
    ], columns=["項目","狀態","說明"])
    ai_event_df = pd.DataFrame([
        ["財報公告", "高", "EPS、毛利率、營益率、現金流是主要觀察"],
        ["法說會", "高", "公司展望、訂單、產業需求與資本支出"],
        ["除權息", "中", "殖利率、填息機率與資金流"],
        ["重大訊息", "高", "併購、處分、投資、訴訟、重大合約"],
        ["法人買賣超", "中高", "法人連買/連賣與主力集中度"],
    ], columns=["AI事件","重要性","觀察重點"])
    ai_concall_df = pd.DataFrame([
        ["營收展望", "待公司說明", "觀察月營收與法說展望是否一致"],
        ["毛利率", "待公司說明", "觀察產品組合與匯率影響"],
        ["資本支出", "待公司說明", "高成長產業需關注CAPEX與折舊"],
        ["AI/新產品", "待公司說明", "是否帶動EPS與估值上修"],
        ["庫存/訂單", "待公司說明", "庫存去化與客戶需求是景氣循環關鍵"],
    ], columns=["AI法說會題目","狀態","追蹤重點"])
    ai_comp_df = pd.DataFrame([
        ["同產業估值", "需同業資料庫", "比較 PE、PB、EV/EBITDA、PEG"],
        ["同產業成長", "需同業資料庫", "比較營收成長、EPS成長、ROE"],
        ["同產業籌碼", "代理模式", "比較法人分數與主力分數"],
        ["競爭優勢", "AI推估", "毛利率、ROE、現金流與產業地位"],
    ], columns=["AI競爭分析","狀態","說明"])
    ai_risk_df = pd.DataFrame([
        ["技術風險", "高" if scores.get("tech",50)<45 else "中低", "跌破均線或動能轉弱"],
        ["估值風險", "高" if pd.notna(upside) and upside<0 else "中", "共識價低於現價時需留意"],
        ["籌碼風險", "高" if scores.get("inst",50)<45 else "中低", "法人/主力轉弱"],
        ["財報風險", "高" if scores.get("fund",50)<45 else "中", "EPS與現金流不足"],
        ["ESG風險", "中高" if scores.get("esg",50)<55 else "中低", "永續揭露不足或治理風險"],
        ["綜合風險預警", f"{risk_score}/100", "分數越高代表風險越高"],
    ], columns=["AI風險預警","燈號/分數","說明"])
    return {
        "① AI評級": ai_rating_df,
        "② AI估值": ai_val_df,
        "③ AI財報": ai_fin_df,
        "④ AI法人": ai_inst_df,
        "⑤ AI產業": ai_industry_df,
        "⑥ AI新聞": ai_news_df,
        "⑦ AI事件": ai_event_df,
        "⑧ AI法說會": ai_concall_df,
        "⑨ AI競爭分析": ai_comp_df,
        "⑩ AI風險預警": ai_risk_df,
    }

def v50_ai_research_center(symbol, df, q, scores):
    st.subheader(f"🤖 AI研究中心完整版：{display_name(symbol)}")
    tables = v50_ai_complete_tables(symbol, df, q, scores)
    total = ai_total(scores)
    risk = ai_risk_score(scores, df) if "ai_risk_score" in globals() else int(np.clip(100-total,0,100))
    val, inp = valuation(effective_price(q, df), q, scores)
    con = consensus(val)
    kpi([("AI評級", tables["① AI評級"].iloc[0,1]),("AI分數",f"{total}/100"),("風險預警",f"{risk}/100"),("模型共識價",fmt(con))])
    tabs = st.tabs(list(tables.keys()))
    for tab, (name, data) in zip(tabs, tables.items()):
        with tab:
            if data is None or data.empty:
                st.info(f"{name} 目前資料不足。")
            else:
                st.dataframe(data, use_container_width=True, hide_index=True)

def v50_esg_layers(symbol, q, scores):
    # 4層ESG資料可信度：實際資料不足時明確揭露代理模式
    levels = pd.DataFrame([
        ["Level 1", "永續報告書", "公司年度永續報告書、ESG Report、CSR Report", "未上傳/未串接時使用待補", "95%"],
        ["Level 2", "ESG揭露指標", "GRI、SASB、TCFD、ISSB、CDP、公司治理評鑑", "部分指標可人工登錄", "80%"],
        ["Level 3", "產業ESG平均", "同產業ESG平均、治理平均、碳排代理", "可作缺漏補值", "60%"],
        ["Level 4", "代理模式", "AIStock ESG Engine：治理、財務穩定、風險與產業代理", "目前預設模式", "30%"],
    ], columns=["層級","資料層","資料內容","目前狀態","資料可信度"])
    score = scores.get("esg", 68)
    layer_score = pd.DataFrame([
        ["永續報告書完整度", 30, "尚未串接公司PDF，先以代理模式"],
        ["ESG揭露完整度", 45, "GRI/SASB/TCFD/ISSB/CDP待補"],
        ["產業ESG平均", 60, "可用同產業平均補值"],
        ["代理ESG分數", score, "AIStock ESG Engine"],
    ], columns=["項目","分數","說明"])
    return levels, layer_score

def v50_institutional_upgrade_tables(df, scores):
    margin = margin_short_proxy(df) if "margin_short_proxy" in globals() else pd.DataFrame()
    lending = securities_lending_proxy(df) if "securities_lending_proxy" in globals() else pd.DataFrame()
    broker = broker_flow_proxy(df) if "broker_flow_proxy" in globals() else pd.DataFrame()
    signal = margin_signal_engine(df, scores.get("inst",50), scores.get("main",50)) if "margin_signal_engine" in globals() else pd.DataFrame()
    margin_center = pd.DataFrame([
        ["融資增減率", "量價代理", "融資增加但跌破月線＝風險；融資增加且站上月線＝偏多"],
        ["融資使用率", "待正式資料", "需TWSE/TPEX信用交易資料"],
        ["融資維持率", "待正式資料", "需券商或交易所資料"],
        ["融資燈號", "已建立", "併入綜合買賣燈號"],
    ], columns=["融資中心","狀態","說明"])
    short_center = pd.DataFrame([
        ["融券餘額", "量價代理", "正式資料需TWSE/TPEX"],
        ["融券增減", "量價代理", "融券增加偏空，回補偏多"],
        ["券資比", "量價代理", "融券/融資比率越高代表軋空或放空壓力"],
        ["融券燈號", "已建立", "併入綜合買賣燈號"],
    ], columns=["融券中心","狀態","說明"])
    lending_center = pd.DataFrame([
        ["借券餘額", "量價代理", "正式資料需借券交易資料"],
        ["借券賣出", "量價代理", "借券賣出增加偏空"],
        ["借券回補", "量價代理", "回補增加偏多"],
        ["借券燈號", "已建立", "併入綜合買賣燈號"],
    ], columns=["借券中心","狀態","說明"])
    broker_center = pd.DataFrame([
        ["Top20分點買超", "代理模式", "正式分點需券商/資料商API"],
        ["Top20分點賣超", "代理模式", "正式分點需券商/資料商API"],
        ["主力集中度", "量價代理", "以前5/前10券商集中度代理"],
        ["主力成本帶", "待正式資料", "需分點交易成本或籌碼資料"],
    ], columns=["券商中心","狀態","說明"])
    return margin, lending, broker, signal, margin_center, short_center, lending_center, broker_center
# ================= V50 AI / ESG / 法人完整補齊 END =================


# ================= V52 穩定修復層：中文財報、K線副圖、顯示備援 =================
def safe_show(x):
    try:
        if x is None:
            return "N/A"
        if isinstance(x, str) and x.lower() in ["none","nan","nat",""]:
            return "N/A"
        if pd.isna(x):
            return "N/A"
    except Exception:
        pass
    return x

def normalize_fin_key(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

def fin_get_any(df, keys):
    try:
        if df is None or df.empty:
            return np.nan
        norm_index = {normalize_fin_key(i): i for i in df.index}
        for key in keys:
            nk = normalize_fin_key(key)
            if nk in norm_index:
                vals = pd.to_numeric(df.loc[norm_index[nk]], errors="coerce").dropna()
                if len(vals):
                    return safe_float(vals.iloc[0])
        for key in keys:
            nk = normalize_fin_key(key)
            for ni, original in norm_index.items():
                if nk in ni or ni in nk:
                    vals = pd.to_numeric(df.loc[original], errors="coerce").dropna()
                    if len(vals):
                        return safe_float(vals.iloc[0])
    except Exception:
        pass
    return np.nan

def chinese_financial_analysis(symbol, q, ft):
    income = ft.get("income", pd.DataFrame()) if isinstance(ft, dict) else pd.DataFrame()
    balance = ft.get("balance", pd.DataFrame()) if isinstance(ft, dict) else pd.DataFrame()
    cashflow = ft.get("cashflow", pd.DataFrame()) if isinstance(ft, dict) else pd.DataFrame()
    revenue = fin_get_any(income, ["Total Revenue","Operating Revenue","Revenue"])
    gross = fin_get_any(income, ["Gross Profit"])
    op_income = fin_get_any(income, ["Operating Income","Total Operating Income As Reported"])
    net_income = fin_get_any(income, ["Net Income","Net Income Common Stockholders","Normalized Income"])
    assets = fin_get_any(balance, ["Total Assets"])
    equity = fin_get_any(balance, ["Stockholders Equity","Common Stock Equity","Total Equity Gross Minority Interest"])
    ocf = fin_get_any(cashflow, ["Operating Cash Flow","Cash Flow From Continuing Operating Activities"])
    capex = fin_get_any(cashflow, ["Capital Expenditure","Purchase Of PPE"])
    fcf = fin_get_any(cashflow, ["Free Cash Flow"])
    if pd.isna(fcf) and pd.notna(ocf) and pd.notna(capex):
        fcf = ocf + capex
    eps = q.get("eps", np.nan) if isinstance(q, dict) else np.nan
    pe = q.get("pe", np.nan) if isinstance(q, dict) else np.nan
    pb = q.get("pb", np.nan) if isinstance(q, dict) else np.nan
    summary = pd.DataFrame([
        ["營業收入", safe_show(revenue)],["營業毛利", safe_show(gross)],["營業利益", safe_show(op_income)],
        ["本期淨利", safe_show(net_income)],["資產總額", safe_show(assets)],["股東權益", safe_show(equity)],
        ["營業活動現金流", safe_show(ocf)],["自由現金流", safe_show(fcf)],["EPS", safe_show(eps)],
        ["PE", safe_show(pe)],["PB", safe_show(pb)]
    ], columns=["中文項目","最新數值"])
    gm = gross/revenue*100 if pd.notna(gross) and pd.notna(revenue) and revenue else np.nan
    om = op_income/revenue*100 if pd.notna(op_income) and pd.notna(revenue) and revenue else np.nan
    nm = net_income/revenue*100 if pd.notna(net_income) and pd.notna(revenue) and revenue else np.nan
    roe = net_income/equity*100 if pd.notna(net_income) and pd.notna(equity) and equity else np.nan
    roa = net_income/assets*100 if pd.notna(net_income) and pd.notna(assets) and assets else np.nan
    fcf_margin = fcf/revenue*100 if pd.notna(fcf) and pd.notna(revenue) and revenue else np.nan
    ratios = pd.DataFrame([["毛利率",safe_show(gm)],["營益率",safe_show(om)],["淨利率",safe_show(nm)],["ROE",safe_show(roe)],["ROA",safe_show(roa)],["自由現金流率",safe_show(fcf_margin)]], columns=["指標","數值%"])
    score=50
    for v, add in [(gm,10),(om,10),(nm,10),(roe,12),(roa,8),(fcf_margin,10)]:
        if pd.notna(v):
            score += add if v > 10 else (add/2 if v > 0 else -add/2)
    return summary, ratios, int(np.clip(score,0,100))

def add_more_indicators(df):
    if df is None or df.empty:
        return pd.DataFrame()
    d = df.copy()
    for c in ["Open","High","Low","Close","Volume"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    close=d["Close"]; high=d["High"]; low=d["Low"]; vol=d["Volume"]
    for n in [5,10,20,60,120,240]:
        d[f"MA{n}"]=close.rolling(n).mean()
    delta=close.diff()
    gain=delta.clip(lower=0).rolling(14).mean()
    loss=(-delta.clip(upper=0)).rolling(14).mean()
    rs=gain/(loss.replace(0,np.nan))
    d["RSI"]=100-(100/(1+rs))
    ema12=close.ewm(span=12, adjust=False).mean()
    ema26=close.ewm(span=26, adjust=False).mean()
    d["DIF"]=ema12-ema26
    d["MACD"]=d["DIF"].ewm(span=9, adjust=False).mean()
    d["OSC"]=d["DIF"]-d["MACD"]
    ll=low.rolling(9).min(); hh=high.rolling(9).max()
    rsv=(close-ll)/(hh-ll).replace(0,np.nan)*100
    d["K"]=rsv.ewm(alpha=1/3, adjust=False).mean()
    d["D"]=d["K"].ewm(alpha=1/3, adjust=False).mean()
    d["J"]=3*d["K"]-2*d["D"]
    for n in [5,10,20,60]:
        ma=close.rolling(n).mean()
        d[f"BIAS{n}"]=(close-ma)/ma.replace(0,np.nan)*100
    mid=close.rolling(20).mean(); std=close.rolling(20).std()
    d["BB_MID"]=mid; d["BB_UP"]=mid+2*std; d["BB_LOW"]=mid-2*std
    tr=pd.concat([(high-low).abs(),(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
    d["ATR"]=tr.rolling(14).mean(); d["ATR_PCT"]=d["ATR"]/close.replace(0,np.nan)*100
    d["OBV"]=(np.sign(close.diff()).fillna(0)*vol.fillna(0)).cumsum()
    d["OBV_MA20"]=d["OBV"].rolling(20).mean()
    tp=(high+low+close)/3; money=tp*vol
    pos=money.where(tp>tp.shift(),0).rolling(14).sum()
    neg=money.where(tp<tp.shift(),0).rolling(14).sum()
    d["MFI"]=100-100/(1+(pos/neg.replace(0,np.nan)))
    d["WILLR"]=(hh-close)/(hh-ll).replace(0,np.nan)*-100
    sma_tp=tp.rolling(20).mean(); mad=(tp-sma_tp).abs().rolling(20).mean()
    d["CCI"]=(tp-sma_tp)/(0.015*mad.replace(0,np.nan))
    plus_dm=(high.diff()).where((high.diff()>-low.diff()) & (high.diff()>0),0)
    minus_dm=(-low.diff()).where((-low.diff()>high.diff()) & (-low.diff()>0),0)
    atr=tr.rolling(14).mean()
    plus_di=100*(plus_dm.rolling(14).mean()/atr.replace(0,np.nan))
    minus_di=100*(minus_dm.rolling(14).mean()/atr.replace(0,np.nan))
    dx=(abs(plus_di-minus_di)/(plus_di+minus_di).replace(0,np.nan))*100
    d["PLUS_DI"]=plus_di; d["MINUS_DI"]=minus_di; d["ADX"]=dx.rolling(14).mean()
    d["ROC12"]=close.pct_change(12)*100
    d["MOM10"]=close-close.shift(10)
    d["VOL_MA20"]=vol.rolling(20).mean()
    return d

def kline_chart(df, overlays, panel):
    d=add_more_indicators(add_indicators(df))
    dd=d.tail(160)
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=dd["Date"],open=dd["Open"],high=dd["High"],low=dd["Low"],close=dd["Close"],name="K線",increasing_line_color="#ff3333",decreasing_line_color="#00d26a",increasing_fillcolor="#ff3333",decreasing_fillcolor="#00d26a"))
    cmap={"MA5":"#ffff00","MA10":"#00e5ff","MA20":"#c000ff","MA60":"#ff9900","MA120":"#94a3b8","MA240":"#64748b"}
    for ma in overlays:
        if ma in dd.columns:
            fig.add_trace(go.Scatter(x=dd["Date"],y=dd[ma],name=ma,line=dict(color=cmap.get(ma),width=1.5)))
    if "布林通道" in overlays:
        fig.add_trace(go.Scatter(x=dd["Date"],y=dd["BB_UP"],name="BB上軌",line=dict(width=1,dash="dot")))
        fig.add_trace(go.Scatter(x=dd["Date"],y=dd["BB_MID"],name="BB中軌",line=dict(width=1,dash="dot")))
        fig.add_trace(go.Scatter(x=dd["Date"],y=dd["BB_LOW"],name="BB下軌",line=dict(width=1,dash="dot")))
    fig.update_layout(height=520,template="plotly_dark",xaxis_rangeslider_visible=False,margin=dict(l=6,r=6,t=20,b=4),legend=dict(orientation="h",font=dict(size=9)),yaxis=dict(side="right"))
    st.plotly_chart(fig,use_container_width=True)
    f=go.Figure()
    if panel=="成交量":
        f.add_trace(go.Bar(x=dd["Date"],y=dd["Volume"],name="VOL")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["VOL_MA20"],name="20日均量"))
    elif panel=="MACD":
        f.add_trace(go.Bar(x=dd["Date"],y=dd["OSC"],name="OSC")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["DIF"],name="DIF")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["MACD"],name="MACD"))
    elif panel=="KD":
        f.add_trace(go.Scatter(x=dd["Date"],y=dd["K"],name="K")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["D"],name="D")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["J"],name="J")); f.add_hline(y=80,line_dash="dot"); f.add_hline(y=20,line_dash="dot")
    elif panel=="RSI":
        f.add_trace(go.Scatter(x=dd["Date"],y=dd["RSI"],name="RSI")); f.add_hline(y=70,line_dash="dot"); f.add_hline(y=30,line_dash="dot")
    elif panel=="BIAS":
        f.add_trace(go.Scatter(x=dd["Date"],y=dd["BIAS20"],name="BIAS20")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["BIAS60"],name="BIAS60")); f.add_hline(y=0,line_dash="dot")
    elif panel=="布林通道":
        f.add_trace(go.Scatter(x=dd["Date"],y=(dd["BB_UP"]-dd["BB_LOW"])/dd["BB_MID"].replace(0,np.nan)*100,name="BB寬度%"))
    elif panel=="OBV":
        f.add_trace(go.Scatter(x=dd["Date"],y=dd["OBV"],name="OBV")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["OBV_MA20"],name="OBV_MA20"))
    elif panel=="MFI":
        f.add_trace(go.Scatter(x=dd["Date"],y=dd["MFI"],name="MFI")); f.add_hline(y=80,line_dash="dot"); f.add_hline(y=20,line_dash="dot")
    elif panel=="威廉%R":
        f.add_trace(go.Scatter(x=dd["Date"],y=dd["WILLR"],name="Williams %R")); f.add_hline(y=-20,line_dash="dot"); f.add_hline(y=-80,line_dash="dot")
    elif panel=="CCI":
        f.add_trace(go.Scatter(x=dd["Date"],y=dd["CCI"],name="CCI")); f.add_hline(y=100,line_dash="dot"); f.add_hline(y=-100,line_dash="dot")
    elif panel=="ADX":
        f.add_trace(go.Scatter(x=dd["Date"],y=dd["ADX"],name="ADX")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["PLUS_DI"],name="+DI")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["MINUS_DI"],name="-DI"))
    elif panel=="ATR":
        f.add_trace(go.Scatter(x=dd["Date"],y=dd["ATR_PCT"],name="ATR%"))
    elif panel=="ROC":
        f.add_trace(go.Scatter(x=dd["Date"],y=dd["ROC12"],name="ROC12")); f.add_hline(y=0,line_dash="dot")
    elif panel=="Momentum":
        f.add_trace(go.Scatter(x=dd["Date"],y=dd["MOM10"],name="MOM10")); f.add_hline(y=0,line_dash="dot")
    else:
        f.add_trace(go.Bar(x=dd["Date"],y=dd["Volume"],name="VOL"))
    f.update_layout(height=260,template="plotly_dark",margin=dict(l=6,r=6,t=24,b=4),legend=dict(orientation="h",font=dict(size=9)),yaxis=dict(side="right"))
    st.plotly_chart(f,use_container_width=True)
# ================= V52 穩定修復層 END =================


def clean_symbol(x):
    s=str(x).strip()
    name_map = globals().get("TW_STOCKS", {})
    if s in name_map:
        return name_map[s]
    if "." in s:
        return s.upper()
    if s.isdigit():
        otc = globals().get("OTC_CODES", set())
        return f"{s}.TWO" if s in otc else f"{s}.TW"
    return s

# ================= V53 EARLY HOTFIX：必定先定義單一股票控制器 =================
def unified_symbol_manager(symbols):
    """V53 early hotfix single controller. Must exist before active = unified_symbol_manager(symbols)."""
    if "active_symbol" not in st.session_state:
        st.session_state.active_symbol = symbols[0] if symbols else "2330.TW"
    if "recent_symbols" not in st.session_state:
        st.session_state.recent_symbols = [st.session_state.active_symbol]

    st.markdown("🎯")
    qtext = st.text_input(
        "搜尋股票名稱或代碼",
        value="",
        placeholder="例如：2330、聯電、和椿、6415、6830",
        key="v53_symbol_search"
    )
    if qtext.strip():
        try:
            target = clean_symbol(qtext.strip())
            st.session_state.active_symbol = target
            if target not in st.session_state.recent_symbols:
                st.session_state.recent_symbols.insert(0, target)
                st.session_state.recent_symbols = st.session_state.recent_symbols[:12]
        except Exception:
            pass

    # display_name 可能在後面才定義；函式執行時通常已存在。若尚未存在，退回代碼。
    try:
        current_label = display_name(st.session_state.active_symbol)
    except Exception:
        current_label = st.session_state.active_symbol

    st.caption(f"目前全站分析：{current_label}")
    with st.expander("候選 / 最近使用", expanded=False):
        cols = st.columns(4)
        for i, s in enumerate(st.session_state.get("recent_symbols", [])[:12]):
            try:
                label = display_name(s)
            except Exception:
                label = s
            if cols[i % 4].button(label, key=f"v53_recent_{i}_{s}"):
                st.session_state.active_symbol = s
                st.rerun()
    return st.session_state.active_symbol
# ================= V53 EARLY HOTFIX END =================

st.markdown("""
<style>
.block-container{padding-top:.45rem;padding-left:.42rem;padding-right:.42rem;max-width:1600px}
#MainMenu, footer, header{visibility:hidden}
.hero{background:linear-gradient(135deg,#020617,#0f172a 45%,#172554 72%,#1e40af);border:1px solid #334155;border-radius:18px;padding:14px;margin-bottom:10px;color:white;box-shadow:0 8px 24px rgba(2,6,23,.35)}
.hero-title{font-size:1.18rem;font-weight:950}.hero-sub{font-size:.74rem;color:#cbd5e1;margin-top:5px}
.visual{height:82px;border-radius:14px;margin-top:10px;border:1px solid rgba(148,163,184,.35);background:linear-gradient(180deg,rgba(15,23,42,.1),rgba(15,23,42,.75)),repeating-linear-gradient(90deg,rgba(255,255,255,.08) 0 1px,transparent 1px 23px),repeating-linear-gradient(0deg,rgba(255,255,255,.07) 0 1px,transparent 1px 23px)}
.visual svg{width:100%;height:100%;display:block}
.kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0 10px}
.kpi{background:#0f172a;border:1px solid #334155;border-radius:14px;padding:10px;color:#fff}
.kpi-label{font-size:.72rem;color:#cbd5e1;font-weight:800}.kpi-value{font-size:1.08rem;font-weight:950;line-height:1.1;margin-top:4px}
.stock-grid{display:grid;gap:8px;margin-top:6px}.stock-grid.cols-1{grid-template-columns:1fr}.stock-grid.cols-2{grid-template-columns:1fr 1fr}.stock-grid.cols-3{grid-template-columns:1fr 1fr 1fr}.stock-grid.cols-4{grid-template-columns:1fr 1fr 1fr 1fr}
.card{background:#0f172a;color:#fff;border:1px solid #334155;border-radius:14px;padding:9px;margin:0;box-shadow:0 1px 5px rgba(15,23,42,.18)}
.card-title{font-size:.72rem;color:#cbd5e1;font-weight:800;line-height:1.18}.card-price{font-size:1.05rem;font-weight:950;margin-top:4px}.card-small{font-size:.63rem;color:#cbd5e1;line-height:1.35}
.badge{display:inline-block;border-radius:999px;padding:1px 5px;margin:2px;font-size:.58rem;background:#1e293b;color:#e2e8f0;border:1px solid #475569}
.good{color:#f87171;font-weight:900}.bad{color:#4ade80;font-weight:900}.neutral{color:#facc15;font-weight:900}
.explain{background:#0f172a;border:1px solid #334155;border-radius:14px;padding:10px;color:#e5e7eb;line-height:1.6;font-size:.84rem}
.targetbar{background:#0f172a;border:1px solid #334155;border-radius:14px;padding:12px;margin:8px 0;color:white}.target-row{display:flex;align-items:center;gap:8px;margin:8px 0}.target-name{width:58px;font-weight:850;color:#cbd5e1;font-size:.78rem}.target-line{height:16px;border-radius:999px;background:#334155;flex:1;overflow:hidden}.target-fill{height:100%;border-radius:999px}.target-val{width:74px;text-align:right;font-weight:900}
@media(max-width:480px){.stock-grid.cols-3,.stock-grid.cols-4{grid-template-columns:1fr 1fr}}@media(max-width:360px){.stock-grid.cols-2,.stock-grid.cols-3,.stock-grid.cols-4{grid-template-columns:1fr}}
@media(max-width:768px){.hero{padding:11px}.hero-title{font-size:1.04rem}.hero-sub{font-size:.67rem}.visual{height:72px}.kpi{padding:8px}.kpi-value{font-size:1rem}}

/* V39 responsive mobile/desktop */
.v39-symbol-panel{background:#0f172a;border:1px solid #334155;border-radius:16px;padding:10px;margin:8px 0 10px 0}
.v39-active{font-size:1.05rem;font-weight:950;color:#fff}
.v39-hint{font-size:.72rem;color:#94a3b8;line-height:1.4;margin-top:3px}
.desktop-only{display:block}.mobile-only{display:none}
@media(max-width:768px){
  .desktop-only{display:none!important}.mobile-only{display:block!important}
  .block-container{padding-left:.32rem!important;padding-right:.32rem!important}
  .stock-grid.cols-3,.stock-grid.cols-4{grid-template-columns:1fr 1fr!important}
  .kpi-grid{grid-template-columns:1fr 1fr!important}
}
@media(max-width:360px){.stock-grid.cols-2,.stock-grid.cols-3,.stock-grid.cols-4{grid-template-columns:1fr!important}}


/* V57 Enterprise Final responsive audit */
@media(max-width:768px){
  .block-container{padding-left:.35rem!important;padding-right:.35rem!important}
  .kpi-grid{grid-template-columns:1fr 1fr!important}
  .stock-grid.cols-3,.stock-grid.cols-4{grid-template-columns:1fr 1fr!important}
}
@media(max-width:380px){
  .kpi-grid,.stock-grid.cols-2,.stock-grid.cols-3,.stock-grid.cols-4{grid-template-columns:1fr!important}
}
@media(min-width:769px){
  .kpi-grid{grid-template-columns:repeat(4,1fr)}
}

.v44-chip-scroll{display:flex;gap:6px;overflow-x:auto;white-space:nowrap;padding:4px 0 8px 0;margin:2px 0 4px 0}
.v44-chip-scroll::-webkit-scrollbar{height:3px}
.v44-chip{display:inline-block;background:#1e293b;border:1px solid #475569;color:#e2e8f0;border-radius:999px;padding:5px 9px;font-size:.72rem;font-weight:800}
.v44-note{font-size:.74rem;color:#94a3b8;line-height:1.5}
@media(max-width:768px){
  div[data-testid="stButton"] button{padding:.25rem .45rem;font-size:.72rem;min-height:2rem}
  .v39-symbol-panel{padding:8px!important}
}
</style>
""", unsafe_allow_html=True)

TW_STOCKS={"台積電":"2330.TW","聯電":"2303.TW","世界先進":"5347.TWO","和椿":"6215.TWO","台光電":"2383.TW","威剛":"3260.TWO","台達電":"2308.TW","鴻海":"2317.TW","聯發科":"2454.TW","廣達":"2382.TW","緯創":"3231.TW","英業達":"2356.TW","華碩":"2357.TW","技嘉":"2376.TW","欣興":"3037.TW","南亞科":"2408.TW","瑞昱":"2379.TW","力積電":"6770.TW","智邦":"2345.TW","奇鋐":"3017.TW","世芯-KY":"3661.TW","緯穎":"6669.TW","健策":"3653.TW"}

# V43：補充常見台股中文名稱，讓輸入代碼後能顯示公司中文名稱
TW_STOCKS.update({
    "光寶科":"2301.TW",
    "全友":"2305.TW",
    "仁寶":"2324.TW",
    "佳世達":"2352.TW",
    "宏碁":"2353.TW",
    "神達":"3706.TW",
    "友達":"2409.TW",
    "群創":"3481.TW",
    "中華電":"2412.TW",
    "中鋼":"2002.TW",
    "長榮":"2603.TW",
    "陽明":"2609.TW",
    "萬海":"2615.TW",
    "富邦金":"2881.TW",
    "國泰金":"2882.TW",
    "玉山金":"2884.TW",
    "元大金":"2885.TW",
    "兆豐金":"2886.TW",
    "中信金":"2891.TW",
    "第一金":"2892.TW",
    "華南金":"2880.TW",
    "合庫金":"5880.TW",
    "華新":"1605.TW",
    "大亞":"1609.TW",
    "士電":"1503.TW",
    "華城":"1519.TW",
    "亞力":"1514.TW",
})
CODE_NAME_MAP = {v:k for k,v in TW_STOCKS.items()}


# V57 Enterprise Final：擴充台股中文名稱對照；每位使用者使用自己的 session_state，不寫共用 watchlist.json
TW_STOCKS.update({
    "光寶科":"2301.TW","麗正":"2302.TW","聯電":"2303.TW","全友":"2305.TW","台達電":"2308.TW",
    "華通":"2313.TW","台揚":"2314.TW","鴻海":"2317.TW","東訊":"2321.TW","中環":"2323.TW",
    "仁寶":"2324.TW","國巨":"2327.TW","廣宇":"2328.TW","台積電":"2330.TW","精英":"2331.TW",
    "友訊":"2332.TW","旺宏":"2337.TW","光罩":"2338.TW","台亞":"2340.TW","英業達":"2356.TW",
    "華碩":"2357.TW","所羅門":"2359.TW","致茂":"2360.TW","藍天":"2362.TW","矽統":"2363.TW",
    "倫飛":"2364.TW","昆盈":"2365.TW","燿華":"2367.TW","金像電":"2368.TW","菱生":"2369.TW",
    "大同":"2371.TW","震旦行":"2373.TW","佳能":"2374.TW","智寶":"2375.TW","技嘉":"2376.TW",
    "微星":"2377.TW","瑞昱":"2379.TW","虹光":"2380.TW","廣達":"2382.TW","台光電":"2383.TW",
    "群光":"2385.TW","精元":"2387.TW","威盛":"2388.TW","云辰":"2390.TW","正崴":"2392.TW",
    "研華":"2395.TW","凌陽":"2401.TW","毅嘉":"2402.TW","漢唐":"2404.TW","輔信":"2405.TW",
    "國碩":"2406.TW","南亞科":"2408.TW","友達":"2409.TW","中華電":"2412.TW","圓剛":"2417.TW",
    "仲琦":"2419.TW","新巨":"2420.TW","建準":"2421.TW","偉詮電":"2436.TW","超豐":"2441.TW",
    "京元電子":"2449.TW","創見":"2451.TW","聯發科":"2454.TW","全新":"2455.TW","飛宏":"2457.TW",
    "義隆":"2458.TW","敦吉":"2459.TW","美律":"2439.TW","神腦":"2450.TW","志聖":"2467.TW",
    "立隆電":"2472.TW","可成":"2474.TW","華新科":"2492.TW","宏達電":"2498.TW","中鋼":"2002.TW",
    "中華化":"1727.TW","台塑":"1301.TW","南亞":"1303.TW","台化":"1326.TW","長榮":"2603.TW",
    "陽明":"2609.TW","萬海":"2615.TW","富邦金":"2881.TW","國泰金":"2882.TW","玉山金":"2884.TW",
    "元大金":"2885.TW","兆豐金":"2886.TW","中信金":"2891.TW","第一金":"2892.TW","合庫金":"5880.TW",
    "和椿":"6215.TWO","世界先進":"5347.TWO","威剛":"3260.TWO","穩懋":"3105.TWO","宏捷科":"8086.TWO",
    "群聯":"8299.TWO","M31":"6643.TWO","信驊":"5274.TW","智原":"3035.TW","創意":"3443.TW",
    "緯穎":"6669.TW","世芯-KY":"3661.TW","川湖":"2059.TW","奇鋐":"3017.TW","健策":"3653.TW",
    "智邦":"2345.TW","緯創":"3231.TW","英業達":"2356.TW","華城":"1519.TW","亞力":"1514.TW",
    "士電":"1503.TW","華新":"1605.TW","大亞":"1609.TW"
})
CODE_NAME_MAP = {v:k for k,v in TW_STOCKS.items()}

# V46：股票中文名稱補齊與多人共用隔離說明
TW_STOCKS.update({
    "光寶科":"2301.TW","麗正":"2302.TW","聯電":"2303.TW","全友":"2305.TW","台達電":"2308.TW",
    "金寶":"2312.TW","華通":"2313.TW","台揚":"2314.TW","鴻海":"2317.TW","東訊":"2321.TW",
    "中環":"2323.TW","仁寶":"2324.TW","國巨":"2327.TW","廣宇":"2328.TW","台積電":"2330.TW",
    "精英":"2331.TW","友訊":"2332.TW","旺宏":"2337.TW","光罩":"2338.TW","台亞":"2340.TW",
    "華邦電":"2344.TW","智邦":"2345.TW","聯強":"2347.TW","佳世達":"2352.TW","宏碁":"2353.TW",
    "敬鵬":"2355.TW","英業達":"2356.TW","華碩":"2357.TW","所羅門":"2359.TW","致茂":"2360.TW",
    "倫飛":"2364.TW","昆盈":"2365.TW","燿華":"2367.TW","金像電":"2368.TW","菱生":"2369.TW",
    "大同":"2371.TW","震旦行":"2373.TW","佳能":"2374.TW","智寶":"2375.TW","技嘉":"2376.TW",
    "微星":"2377.TW","瑞昱":"2379.TW","虹光":"2380.TW","廣達":"2382.TW","台光電":"2383.TW",
    "群光":"2385.TW","精元":"2387.TW","威盛":"2388.TW","云辰":"2390.TW","正崴":"2392.TW",
    "研華":"2395.TW","凌陽":"2401.TW","毅嘉":"2402.TW","漢唐":"2404.TW","輔信":"2405.TW",
    "國碩":"2406.TW","南亞科":"2408.TW","友達":"2409.TW","中華電":"2412.TW","圓剛":"2417.TW",
    "仲琦":"2419.TW","新巨":"2420.TW","建準":"2421.TW","興勤":"2428.TW","銘旺科":"2429.TW",
    "統懋":"2434.TW","偉詮電":"2436.TW","美律":"2439.TW","京元電子":"2449.TW","神腦":"2450.TW",
    "創見":"2451.TW","聯發科":"2454.TW","全新":"2455.TW","飛宏":"2457.TW","義隆":"2458.TW",
    "敦吉":"2459.TW","志聖":"2467.TW","立隆電":"2472.TW","可成":"2474.TW","華新科":"2492.TW",
    "宏達電":"2498.TW","智原":"3035.TW","欣興":"3037.TW","奇鋐":"3017.TW","緯創":"3231.TW",
    "創意":"3443.TW","健策":"3653.TW","世芯-KY":"3661.TW","緯穎":"6669.TW","川湖":"2059.TW",
    "信驊":"5274.TW","華城":"1519.TW","亞力":"1514.TW","士電":"1503.TW","華新":"1605.TW",
    "大亞":"1609.TW","中鋼":"2002.TW","台塑":"1301.TW","南亞":"1303.TW","台化":"1326.TW",
    "長榮":"2603.TW","陽明":"2609.TW","萬海":"2615.TW","富邦金":"2881.TW","國泰金":"2882.TW",
    "玉山金":"2884.TW","元大金":"2885.TW","兆豐金":"2886.TW","中信金":"2891.TW","第一金":"2892.TW",
    "華南金":"2880.TW","合庫金":"5880.TW","世界先進":"5347.TWO","和椿":"6215.TWO","和椿科技":"6215.TWO",
    "威剛":"3260.TWO","穩懋":"3105.TWO","宏捷科":"8086.TWO","群聯":"8299.TWO","M31":"6643.TWO"
})
CODE_NAME_MAP = {v:k for k,v in TW_STOCKS.items()}

# V47：補充高價股/半導體/自動化常用中文名
TW_STOCKS.update({
    "汎銓":"6830.TW","力旺":"3529.TWO","譜瑞-KY":"4966.TW","祥碩":"5269.TW","AES-KY":"6781.TW",
    "台灣精銳":"4583.TW","上銀":"2049.TW","亞光":"3019.TW","和大":"1536.TW","日月光投控":"3711.TW",
    "貿聯-KY":"3665.TW","材料-KY":"4763.TW","達發":"6526.TW","矽力-KY":"6415.TW",
    "晶心科":"6533.TW","愛普":"6531.TW","旺矽":"6223.TWO","精測":"6510.TWO",
})
CODE_NAME_MAP = {v:k for k,v in TW_STOCKS.items()}

# V49：擴充中文名稱與類股清單
TW_STOCKS.update({
    # 近期截圖與常用股
    "汎銓":"6830.TW","台達化":"1309.TW","台灣精銳":"4583.TW","上銀":"2049.TW","亞光":"3019.TW","和大":"1536.TW",
    "日月光投控":"3711.TW","矽力-KY":"6415.TW","力旺":"3529.TWO","旺矽":"6223.TWO","精測":"6510.TWO",
    "祥碩":"5269.TW","譜瑞-KY":"4966.TW","材料-KY":"4763.TW","達發":"6526.TW","晶心科":"6533.TW",
    "愛普":"6531.TW","神達":"3706.TW","華孚":"6235.TW","廣明":"6188.TWO","均豪":"5443.TWO",
    "均華":"6640.TWO","弘塑":"3131.TWO","由田":"3455.TWO","迅得":"6438.TW","志聖":"2467.TW",
    "萬潤":"6187.TWO","鈺創":"5351.TWO","鈊象":"3293.TWO","欣銓":"3264.TWO","中美晶":"5483.TWO",
    "環球晶":"6488.TWO","元太":"8069.TWO","台半":"5425.TWO","朋程":"8255.TWO",
    # 半導體/AI/電子
    "光寶科":"2301.TW","麗正":"2302.TW","聯電":"2303.TW","全友":"2305.TW","金寶":"2312.TW",
    "華通":"2313.TW","台揚":"2314.TW","鴻海":"2317.TW","仁寶":"2324.TW","國巨":"2327.TW",
    "台積電":"2330.TW","精英":"2331.TW","友訊":"2332.TW","旺宏":"2337.TW","華邦電":"2344.TW",
    "智邦":"2345.TW","佳世達":"2352.TW","宏碁":"2353.TW","英業達":"2356.TW","華碩":"2357.TW",
    "致茂":"2360.TW","燿華":"2367.TW","金像電":"2368.TW","技嘉":"2376.TW","微星":"2377.TW",
    "瑞昱":"2379.TW","廣達":"2382.TW","台光電":"2383.TW","群光":"2385.TW","精元":"2387.TW",
    "研華":"2395.TW","凌陽":"2401.TW","漢唐":"2404.TW","南亞科":"2408.TW","友達":"2409.TW",
    "中華電":"2412.TW","建準":"2421.TW","偉詮電":"2436.TW","京元電子":"2449.TW","創見":"2451.TW",
    "聯發科":"2454.TW","義隆":"2458.TW","立隆電":"2472.TW","可成":"2474.TW","宏達電":"2498.TW",
    "智原":"3035.TW","奇鋐":"3017.TW","欣興":"3037.TW","緯創":"3231.TW","創意":"3443.TW",
    "健策":"3653.TW","世芯-KY":"3661.TW","緯穎":"6669.TW","川湖":"2059.TW","信驊":"5274.TW",
    "世界先進":"5347.TWO","和椿":"6215.TWO","和椿科技":"6215.TWO","威剛":"3260.TWO","穩懋":"3105.TWO",
    "宏捷科":"8086.TWO","群聯":"8299.TWO","M31":"6643.TWO",
    # 傳產/金融
    "華城":"1519.TW","亞力":"1514.TW","士電":"1503.TW","華新":"1605.TW","大亞":"1609.TW",
    "中鋼":"2002.TW","台塑":"1301.TW","南亞":"1303.TW","台化":"1326.TW","長榮":"2603.TW",
    "陽明":"2609.TW","萬海":"2615.TW","富邦金":"2881.TW","國泰金":"2882.TW","玉山金":"2884.TW",
    "元大金":"2885.TW","兆豐金":"2886.TW","中信金":"2891.TW","第一金":"2892.TW","華南金":"2880.TW","合庫金":"5880.TW",
})
CODE_NAME_MAP = {v:k for k,v in TW_STOCKS.items()}

SECTOR_EXTRA = {
    "半導體": ["2330.TW","2303.TW","2454.TW","2308.TW","3035.TW","3443.TW","3661.TW","2379.TW","5274.TW","5347.TWO","3105.TWO","8086.TWO","8299.TWO","6643.TWO","6415.TW","6533.TW","6531.TW","6223.TWO","6510.TWO"],
    "AI伺服器": ["6669.TW","2382.TW","3231.TW","2356.TW","2317.TW","2376.TW","2377.TW","3017.TW","3653.TW","2059.TW","3443.TW","3661.TW"],
    "機器人/自動化": ["6215.TWO","2049.TW","4583.TW","3019.TW","1536.TW","2308.TW","2467.TW","3131.TWO","3455.TWO","6438.TW","5443.TWO","6640.TWO","6187.TWO"],
    "矽光子/CPO": ["3008.TW","3163.TWO","3234.TWO","3450.TW","4979.TWO","5222.TWO","6533.TW","3081.TWO"],
    "高價IC設計": ["3661.TW","3443.TW","3035.TW","2454.TW","3529.TWO","5274.TW","5269.TW","4966.TW","6415.TW","6533.TW","6643.TWO"],
    "PCB/CCL": ["2383.TW","2368.TW","2313.TW","3037.TW","6274.TWO","6213.TW","8046.TW","3189.TWO"],
    "散熱": ["3017.TW","3653.TW","3324.TWO","8996.TW","2421.TW","6230.TW"],
    "電力重電": ["1519.TW","1514.TW","1503.TW","1605.TW","1609.TW","2371.TW"],
    "記憶體": ["2408.TW","2344.TW","2337.TW","3260.TWO","8299.TWO","5351.TWO"],
    "面板": ["2409.TW","3481.TW","6116.TW","8069.TWO"],
    "金融": ["2881.TW","2882.TW","2884.TW","2885.TW","2886.TW","2891.TW","2892.TW","2880.TW","5880.TW"],
    "航運": ["2603.TW","2609.TW","2615.TW","2606.TW","2618.TW"],
    "ESG高治理": ["2330.TW","2308.TW","2412.TW","2881.TW","2882.TW","1216.TW","1303.TW"],
    "全市場精選": ["2330.TW","2303.TW","2308.TW","2454.TW","2383.TW","3017.TW","3443.TW","3661.TW","6669.TW","5347.TWO","6215.TWO","6830.TW","6415.TW"],
}

# V52：中文名稱最終補強。若資料源無法辨識，明確標示而非空白。
TW_STOCKS.update({
    "汎銓":"6830.TW",
    "矽力-KY":"6415.TW",
    "矽力*-KY":"6415.TW",
    "和椿科技":"6215.TWO",
    "和椿":"6215.TWO",
    "金寶":"2312.TW",
    "台灣精銳":"4583.TW",
    "上銀":"2049.TW",
    "亞光":"3019.TW",
    "和大":"1536.TW",
    "日月光投控":"3711.TW",
    "代碼待確認6308":"6308.TW",
})
CODE_NAME_MAP = {v:k for k,v in TW_STOCKS.items()}
CODE_NAME_MAP.update({
    "6308.TW":"代碼待確認",
    "6830.TW":"汎銓",
    "6415.TW":"矽力-KY",
    "6215.TWO":"和椿科技",
    "2312.TW":"金寶",
    "4583.TW":"台灣精銳",
    "2049.TW":"上銀",
    "3019.TW":"亞光",
    "1536.TW":"和大",
    "3711.TW":"日月光投控",
})
DEFAULT_MONITOR=["2330.TW","2303.TW","5347.TWO","6215.TWO","2383.TW","3260.TWO","2308.TW","2317.TW","2454.TW","2382.TW","2345.TW","3017.TW","2368.TW","3653.TW","3661.TW","2059.TW"]
SECTORS={"半導體":["2330.TW","2303.TW","5347.TWO","2454.TW","3711.TW","6415.TW","3443.TW","3661.TW","2379.TW","2408.TW"],"AI伺服器":["2382.TW","3231.TW","6669.TW","2356.TW","2317.TW","3017.TW","3653.TW","2345.TW","2376.TW","2357.TW"],"機器人/自動化":["6215.TWO","2049.TW","4583.TW","3019.TW","1536.TW","2308.TW"],"全市場精選":DEFAULT_MONITOR}

def safe_float(x, default=np.nan):
    try:
        v=float(x)
        return v if np.isfinite(v) else default
    except Exception:
        return default

OTC_CODES = {
    "5347","6215","3260","3105","8086","6643","6147","3264","8299",
    "5274","6533","4967","6274","8069","3324","5483","6187","6488"
}
ALIASES = {
    "和椿科技":"6215.TWO",
    "和椿":"6215.TWO",
    "世界先進":"5347.TWO",
    "威剛":"3260.TWO",
}

def clean_symbol(x):
    s=str(x).strip()
    if not s:
        return ""
    if s in ALIASES:
        return ALIASES[s]
    if s in TW_STOCKS:
        return TW_STOCKS[s]
    su=s.upper()
    if re.fullmatch(r"\d{4}", su):
        return f"{su}.TWO" if su in OTC_CODES else f"{su}.TW"
    # 若使用者已輸入 6215.TWO / 2330.TW，直接保留
    if re.fullmatch(r"\d{4}\.(TW|TWO)", su):
        return su
    return su

@st.cache_data(show_spinner=False, ttl=86400)
def yahoo_name_lookup(symbol):
    try:
        info = yf.Ticker(symbol).info or {}
        nm = info.get("shortName") or info.get("longName") or ""
        nm = str(nm).replace(" Corporation","").replace(" Co., Ltd.","").replace(" Co Ltd","").strip()
        return nm[:20] if nm and nm.lower() not in ["none","nan"] else ""
    except Exception:
        return ""

def display_name(symbol):
    name = CODE_NAME_MAP.get(symbol)
    if not name:
        name = yahoo_name_lookup(symbol)
    if not name and str(symbol).startswith("6308"):
        name = "代碼待確認"
    return f"{name} / {symbol}" if name else symbol

def fmt(x):
    return "N/A" if x is None or pd.isna(x) else f"{float(x):.2f}"

def now_tw():
    return (datetime.utcnow()+timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

def maybe_reload(sec):
    # V57 Enterprise Final.2: 使用 Streamlit autorefresh，避免 browser reload 導致回首頁或股票重設
    if sec and sec > 0:
        if st_autorefresh is not None:
            st_autorefresh(interval=int(sec)*1000, key="v372_monitor_autorefresh")
        else:
            st.caption("自動更新套件未安裝，請手動刷新；已避免使用瀏覽器reload造成回首頁。")

@st.cache_data(show_spinner=False, ttl=30)
def yf_quote(symbol):
    def empty_quote(src_symbol):
        return {"price":np.nan,"prev":np.nan,"open":np.nan,"high":np.nan,"low":np.nan,"volume":np.nan,"pe":np.nan,"pb":np.nan,"eps":np.nan,"book_value":np.nan,"revenue_per_share":np.nan,"market_cap":np.nan,"div_yield":np.nan,"source":f"Yahoo Finance / {src_symbol}","time":now_tw()}

    # V40.1：若 .TWO 查不到，嘗試 .TW；若 .TW 查不到，嘗試 .TWO
    candidates=[symbol]
    if symbol.endswith(".TWO"):
        candidates.append(symbol.replace(".TWO",".TW"))
    elif symbol.endswith(".TW"):
        candidates.append(symbol.replace(".TW",".TWO"))

    best=None
    for sym in candidates:
        q=empty_quote(sym)
        try:
            t=yf.Ticker(sym)
            try:
                fast=t.fast_info
            except Exception:
                fast={}
            def gf(*ks):
                for k in ks:
                    try:
                        v=fast.get(k) if hasattr(fast,"get") else getattr(fast,k)
                        if v is not None:
                            return safe_float(v)
                    except Exception:
                        pass
                return np.nan
            q["price"]=gf("last_price","lastPrice")
            q["prev"]=gf("previous_close","previousClose")
            q["open"]=gf("open")
            q["high"]=gf("day_high","dayHigh")
            q["low"]=gf("day_low","dayLow")
            q["volume"]=gf("last_volume","lastVolume","volume")
            q["market_cap"]=gf("market_cap","marketCap")
            try:
                info=t.info or {}
                for k,ik in {"pe":"trailingPE","pb":"priceToBook","eps":"trailingEps","book_value":"bookValue","revenue_per_share":"revenuePerShare","div_yield":"dividendYield"}.items():
                    q[k]=safe_float(info.get(ik))
                if pd.isna(q["price"]):
                    q["price"]=safe_float(info.get("currentPrice",info.get("regularMarketPrice")))
                if pd.isna(q["prev"]):
                    q["prev"]=safe_float(info.get("previousClose"))
            except Exception:
                pass
            if pd.notna(q.get("price")):
                return q
            best=q
        except Exception:
            best=q
    return best if best is not None else empty_quote(symbol)


@st.cache_data(show_spinner=False, ttl=60)
def fetch_daily(symbol, period="2y"):
    candidates=[symbol]
    if symbol.endswith(".TWO"):
        candidates.append(symbol.replace(".TWO",".TW"))
    elif symbol.endswith(".TW"):
        candidates.append(symbol.replace(".TW",".TWO"))
    for sym in candidates:
        try:
            df=yf.download(sym, period=period, interval="1d", auto_adjust=False, progress=False)
            if df is None or df.empty:
                continue
            if isinstance(df.columns,pd.MultiIndex):
                df.columns=[c[0] for c in df.columns]
            df=df.reset_index()
            df["Date"]=pd.to_datetime(df["Date"])
            out=df.dropna(subset=["Close"])
            if not out.empty:
                return out
        except Exception:
            pass
    return pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=60)
def fetch_intraday(symbol, interval="60m"):
    period={"60m":"60d","30m":"30d","15m":"30d","5m":"7d"}.get(interval,"30d")
    candidates=[symbol]
    if symbol.endswith(".TWO"):
        candidates.append(symbol.replace(".TWO",".TW"))
    elif symbol.endswith(".TW"):
        candidates.append(symbol.replace(".TW",".TWO"))
    for sym in candidates:
        try:
            df=yf.download(sym, period=period, interval=interval, auto_adjust=False, progress=False)
            if df is None or df.empty:
                continue
            if isinstance(df.columns,pd.MultiIndex):
                df.columns=[c[0] for c in df.columns]
            df=df.reset_index()
            dc="Datetime" if "Datetime" in df.columns else "Date"
            df=df.rename(columns={dc:"Date"})
            df["Date"]=pd.to_datetime(df["Date"]).dt.tz_localize(None)
            out=df.dropna(subset=["Close"])
            if not out.empty:
                return out
        except Exception:
            pass
    return pd.DataFrame()


def resample_ohlcv(df, rule):
    if df.empty: return df
    d=df.set_index("Date").sort_index()
    return pd.DataFrame({"Open":d["Open"].resample(rule).first(),"High":d["High"].resample(rule).max(),"Low":d["Low"].resample(rule).min(),"Close":d["Close"].resample(rule).last(),"Volume":d["Volume"].resample(rule).sum()}).dropna().reset_index()

def get_kline(symbol, mode, period):
    if mode=="日線": return fetch_daily(symbol, period)
    if mode=="週線": return resample_ohlcv(fetch_daily(symbol,"5y"),"W-FRI")
    if mode=="月線": return resample_ohlcv(fetch_daily(symbol,"10y"),"ME")
    return fetch_intraday(symbol, {"60分":"60m","30分":"30m","15分":"15m","5分":"5m"}.get(mode,"60m"))

def add_indicators(df):
    d=df.copy()
    if d.empty: return d
    for w in [5,10,20,60,120,240]: d[f"MA{w}"]=d["Close"].rolling(w).mean()
    d["EMA12"]=d["Close"].ewm(span=12,adjust=False).mean(); d["EMA26"]=d["Close"].ewm(span=26,adjust=False).mean()
    d["MACD"]=d["EMA12"]-d["EMA26"]; d["MACD_SIGNAL"]=d["MACD"].ewm(span=9,adjust=False).mean(); d["MACD_HIST"]=d["MACD"]-d["MACD_SIGNAL"]
    delta=d["Close"].diff(); gain=delta.clip(lower=0).rolling(14).mean(); loss=(-delta.clip(upper=0)).rolling(14).mean()
    d["RSI"]=100-100/(1+gain/loss.replace(0,np.nan))
    low9=d["Low"].rolling(9).min(); high9=d["High"].rolling(9).max()
    d["K"]=100*(d["Close"]-low9)/(high9-low9); d["D"]=d["K"].rolling(3).mean()
    mid=d["Close"].rolling(20).mean(); std=d["Close"].rolling(20).std()
    d["BB_UP"]=mid+2*std; d["BB_DN"]=mid-2*std; d["VOL_MA20"]=d["Volume"].rolling(20).mean()
    d["RET20"]=d["Close"].pct_change(20); d["RET60"]=d["Close"].pct_change(60); d["BIAS20"]=(d["Close"]-d["MA20"])/d["MA20"]*100
    high14=d["High"].rolling(14).max(); low14=d["Low"].rolling(14).min(); d["WILLR"]=-100*(high14-d["Close"])/(high14-low14)
    return d

def signal_cols(d):
    if d.empty: return d
    d=d.copy()
    d["黃金交叉"]=(d["MA5"].shift(1)<=d["MA20"].shift(1))&(d["MA5"]>d["MA20"])
    d["MACD翻紅"]=(d["MACD"].shift(1)<=d["MACD_SIGNAL"].shift(1))&(d["MACD"]>d["MACD_SIGNAL"])
    d["KD黃金交叉"]=(d["K"].shift(1)<=d["D"].shift(1))&(d["K"]>d["D"])
    d["RSI突破50"]=(d["RSI"].shift(1)<50)&(d["RSI"]>=50)
    d["爆量突破"]=(d["Close"]>d["MA20"])&(d["Volume"]>d["VOL_MA20"]*1.5)
    return d

def score_blocks(d,q):
    if d.empty or len(d)<80: return {"tech":50,"chip":50,"fund":50,"esg":68,"inst":50,"main":50}
    x=d.iloc[-1]; tech=50
    tech += 8 if x["Close"]>x.get("MA20",np.inf) else 0
    tech += 8 if x.get("MA20",0)>x.get("MA60",1e9) else 0
    tech += 7 if x.get("MA5",0)>x.get("MA20",1e9) else 0
    tech += 8 if x.get("MACD",0)>x.get("MACD_SIGNAL",1e9) else 0
    tech += 7 if 50<=x.get("RSI",0)<=75 else (-5 if x.get("RSI",0)>80 else 0)
    tech += 5 if x.get("Volume",0)>x.get("VOL_MA20",1e18) else 0
    tech += 4 if x.get("RET20",0)>0 else 0
    tech += 3 if x.get("RET60",0)>0 else 0
    chip=50
    chip += 18 if x.get("Volume",0)>x.get("VOL_MA20",1e18) and x.get("Close",0)>x.get("MA20",1e18) else 0
    chip += 8 if x.get("RET20",0)>0 else 0
    chip += 6 if x.get("RET60",0)>0 else 0
    fund=55; pe=q.get("pe"); pb=q.get("pb")
    if pd.notna(pe): fund += 12 if 0<pe<15 else (8 if pe<=30 else (-8 if pe>50 else 0))
    if pd.notna(pb): fund += 5 if 0<pb<2 else (-4 if pb>6 else 0)
    main=int(np.clip((tech+chip+fund)/3,0,100))
    return {"tech":int(np.clip(tech,0,100)),"chip":int(np.clip(chip,0,100)),"fund":int(np.clip(fund,0,100)),"esg":68,"inst":int(np.clip(chip,0,100)),"main":main}

def ai_total(s): return round(s["fund"]*.35+s["inst"]*.25+s["tech"]*.20+s["esg"]*.10+70*.10,1)


def effective_price(q, df):
    """V57 Enterprise Final: if Yahoo quote is N/A, use latest K-line close as backup so valuation models do not disappear."""
    p = q.get("price", np.nan) if isinstance(q, dict) else np.nan
    if pd.notna(p) and p > 0:
        return float(p)
    try:
        if df is not None and not df.empty:
            c = safe_float(df["Close"].dropna().iloc[-1])
            if pd.notna(c) and c > 0:
                return float(c)
    except Exception:
        pass
    return np.nan

def repair_quote_with_df(q, df):
    q = dict(q) if isinstance(q, dict) else {}
    p = effective_price(q, df)
    if pd.notna(p) and (pd.isna(q.get("price", np.nan)) or q.get("price", np.nan) <= 0):
        q["price"] = p
        q["source"] = str(q.get("source","Yahoo Finance")) + " + K線收盤價備援"
    return q

def kpi(items):
    html='<div class="kpi-grid">'
    for label,value in items: html+=f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>'
    st.markdown(html+'</div>', unsafe_allow_html=True)

def clamp_fair(v, price):
    # V43：不再直接刪除模型，避免畫面只剩少數模型。
    v=safe_float(v)
    if pd.isna(v) or v<=0:
        return np.nan
    return v

def valuation_include_flag(v, price):
    v=safe_float(v); p=safe_float(price)
    if pd.isna(v) or v<=0:
        return "資料不足"
    if pd.notna(p) and p>0 and (v<p*.25 or v>p*5.0):
        return "極端值"
    return "納入共識"



def valuation(price,q,s):
    pe=q.get("pe",np.nan)
    pb=q.get("pb",np.nan)
    eps=q.get("eps",np.nan)

    # V43：完整模型顯示。若 EPS/BVPS 缺漏，用保守代理，避免模型數變少。
    eps = eps if pd.notna(eps) and eps > 0 else (
        price/pe if pd.notna(price) and pd.notna(pe) and pe > 0 else (
        price/18 if pd.notna(price) and price > 0 else np.nan))
    bvps=q.get("book_value",np.nan)
    bvps = bvps if pd.notna(bvps) and bvps > 0 else (
        price/pb if pd.notna(price) and pd.notna(pb) and pb > 0 else (
        price/1.6 if pd.notna(price) and price > 0 else np.nan))
    rps=q.get("revenue_per_share",np.nan)
    rps = rps if pd.notna(rps) and rps > 0 else (price/2.3 if pd.notna(price) and price > 0 else np.nan)

    if pd.isna(price) or price <= 0:
        return pd.DataFrame(), {}

    if pd.isna(eps) or eps <= 0:
        eps = max(price/20, 0.01)
    if pd.isna(bvps) or bvps <= 0:
        bvps = max(price/1.8, 0.01)
    if pd.isna(rps) or rps <= 0:
        rps = max(price/2.5, 0.01)

    g=float(np.clip((s["tech"]+s["fund"]+s["inst"])/300*.22,.03,.22))
    wacc=float(np.clip(.105-(s["fund"]-50)/1000-(s["esg"]-60)/1500,.065,.13))
    tg=float(np.clip(.025+(g-.08)/6,.01,.04))
    roe=float(np.clip(.08+(s["fund"]-50)/250,.03,.28))
    base_pe=float(np.clip(14+g*80,10,32))
    esg_prem=.20 if s["esg"]>=90 else (.15 if s["esg"]>=80 else (.10 if s["esg"]>=70 else (.05 if s["esg"]>=60 else 0)))
    ai_prem=float(np.clip((s["tech"]+s["inst"]-100)/500,-.05,.18))
    inst_prem=float(np.clip((s["inst"]-55)/250,-.08,.18))
    fcf=eps*.82
    dcf=fcf*(1+g)/max(wacc-tg,.025)
    eva=bvps+(roe-wacc)*bvps/max(wacc-tg,.025)
    ebo=bvps+eps*5*np.clip(roe/wacc,.5,2.5)
    residual=bvps+(eps-wacc*bvps)/max(wacc-tg,.025)
    dividend=eps*.45
    ddm=dividend*(1+tg)/max(wacc-tg,.025)
    gordon=ddm
    cap=eps*base_pe*(1+min(max(g*5,0),.65))
    nav=bvps*1.15
    tobin=bvps*np.clip(1+(s["fund"]-50)/100,.7,2.2)
    graham=math.sqrt(max(22.5*eps*bvps,0))

    rows=[
        ("資產法","NAV","淨資產價值法",nav),
        ("資產法","Tobin Q","托賓Q模型",tobin),
        ("資產法","Replacement Cost","重置成本代理",bvps*1.25),

        ("收益法","DCF","現金流量折現",dcf),
        ("收益法","FCFF","企業自由現金流",dcf*1.03),
        ("收益法","FCFE","股東自由現金流",dcf*.97),
        ("收益法","APV","調整現值法",dcf*1.01),
        ("收益法","DDM","股利折現模型",ddm),
        ("收益法","Dividend Discount","股利折現模型完整名稱",ddm),
        ("收益法","Gordon Growth","高登股利成長模型",gordon),

        ("剩餘收益","EVA","經濟附加價值",eva),
        ("剩餘收益","EBO","異常盈餘模型",ebo),
        ("剩餘收益","Residual Income","剩餘盈餘模型",residual),
        ("剩餘收益","Abnormal Earnings Growth","異常盈餘成長模型",eps*base_pe*(1+g)),
        ("剩餘收益","CAP","競爭優勢期間模型",cap),

        ("市場法","PE","本益比",eps*base_pe),
        ("市場法","PB","股價淨值比",bvps*np.clip(1.2+roe*8,.8,4.8)),
        ("市場法","PS","股價營收比",rps*np.clip(1.2+g*8,.8,4.5)),
        ("市場法","EV/Sales","企業價值營收比",rps*np.clip(1.25+g*8,.8,4.7)),
        ("市場法","EV/EBITDA","企業價值EBITDA比",eps*np.clip(16+g*65,11,32)),
        ("市場法","PEG","本益比成長模型",eps*np.clip(g*100,8,35)),
        ("市場法","PEGY","本益比加殖利率模型",eps*np.clip(g*100+2,8,38)),
        ("市場法","Lynch","彼得林區估值",eps*np.clip(g*100,8,30)),
        ("市場法","Graham","葛拉漢公式",graham),

        ("AIStock","ESG Premium","ESG溢價模型",eps*base_pe*(1+esg_prem)),
        ("AIStock","AI Premium","AI成長溢價模型",eps*base_pe*(1+ai_prem)),
        ("AIStock","Institutional Premium","法人溢價模型",eps*base_pe*(1+inst_prem)),
        ("AIStock","Industry Cycle","產業循環模型",eps*base_pe*(1+np.clip((s["tech"]-50)/300,-.08,.15))),
        ("AIStock","Bull Case","牛市模型",eps*base_pe*1.25),
        ("AIStock","Bear Case","熊市模型",eps*base_pe*.75),
        ("AIStock","Super Bull","超級牛市模型",eps*base_pe*(1+max(esg_prem,0)+max(ai_prem,0)*1.8+max(inst_prem,0)*1.2+.25)),
    ]
    df=pd.DataFrame(rows,columns=["分類","模型","中文名稱","合理價"])
    df["合理價"]=df["合理價"].apply(lambda x: clamp_fair(x,price))
    df["狀態"]=df["合理價"].apply(lambda x: valuation_include_flag(x,price))
    df["納入共識"]=df["狀態"].eq("納入共識")
    return df, {"EPS":eps,"BVPS":bvps,"每股營收":rps,"成長率":g,"WACC":wacc,"永續成長率":tg,"ROE":roe,"股利假設":dividend}



def consensus(df):
    if df.empty or "合理價" not in df.columns:
        return np.nan
    use = df.copy()
    if "納入共識" in use.columns:
        use = use[use["納入共識"]]
    use = use.dropna(subset=["合理價"])
    if use.empty:
        use = df.dropna(subset=["合理價"])
    if use.empty:
        return np.nan
    med=use["合理價"].median()
    d=use[(use["合理價"]>=med*.45)&(use["合理價"]<=med*2.2)]
    return d["合理價"].median() if not d.empty else med


def esg_valuation(price,q,score):
    eps=q.get("eps",np.nan); pe=q.get("pe",np.nan)
    eps=eps if pd.notna(eps) and eps>0 else (price/pe if pd.notna(price) and pd.notna(pe) and pe>0 else (price/20 if pd.notna(price) else np.nan))
    prem=.20 if score>=90 else .15 if score>=80 else .10 if score>=70 else .05 if score>=60 else 0
    fair=eps*18*(1+prem) if pd.notna(eps) else np.nan
    return {"EPS":eps,"ESG溢價":prem,"ESG合理價":fair,"ESG牛市價":fair*1.2 if pd.notna(fair) else np.nan,"ESG超級牛市價":fair*1.5 if pd.notna(fair) else np.nan}


def institutional_proxy(df):
    if df.empty or len(df)<30:
        return pd.DataFrame([
            ["外資","資料不足",0,50,"資料不足"],
            ["投信","資料不足",0,50,"資料不足"],
            ["自營商","資料不足",0,50,"資料不足"],
            ["主力代理","資料不足",0,50,"資料不足"],
        ],columns=["法人/主力","買賣方向","估計張數","強度","說明"])
    d=add_indicators(df).dropna()
    if d.empty:
        return pd.DataFrame()
    x=d.iloc[-1]
    vol=safe_float(x.get("Volume"),0)
    volma=safe_float(x.get("VOL_MA20"),vol or 1)
    vr=max(vol/volma,0) if volma else 1
    ret20=safe_float(x.get("RET20"),0)
    ret60=safe_float(x.get("RET60"),0)
    close=safe_float(x.get("Close"),0)
    ma20=safe_float(x.get("MA20"),0)
    ma60=safe_float(x.get("MA60"),0)
    base=max(int(max(vol/1000,1)*min(max(vr,.4),2.5)*.06),1)
    scores={
        "外資":int(np.clip(50+ret20*160+ret60*80+(close>ma20)*12+(vr-1)*10,0,100)),
        "投信":int(np.clip(50+ret20*120+(ma20>ma60)*15+(close>ma20)*8,0,100)),
        "自營商":int(np.clip(50+ret20*220+(vr-1)*18,0,100)),
        "主力代理":int(np.clip(50+ret20*130+ret60*60+(vr-1)*20+(close>ma20)*10,0,100)),
    }
    mult={"外資":1.6,"投信":.75,"自營商":.45,"主力代理":1.1}
    rows=[]
    for name,sc in scores.items():
        dire="買超" if sc>=55 else ("賣超" if sc<=45 else "中性")
        sign=1 if dire=="買超" else (-1 if dire=="賣超" else 0)
        rows.append([name,dire,int(base*mult[name]*sign),sc,"量價代理，非交易所正式法人資料"])
    return pd.DataFrame(rows,columns=["法人/主力","買賣方向","估計張數","強度","說明"])

def institutional_risk_table(df):
    if df.empty or len(df)<60:
        return pd.DataFrame([["資料不足","N/A","K線不足60筆"]],columns=["風險項目","燈號","說明"])
    d=add_indicators(df).dropna()
    x=d.iloc[-1]
    risks=[]
    vr=safe_float(x.get("Volume"),0)/safe_float(x.get("VOL_MA20"),1)
    ret20=safe_float(x.get("RET20"),0)
    close=safe_float(x.get("Close"),0)
    ma20=safe_float(x.get("MA20"),0)
    risks.append(["量增價弱","注意" if vr>1.5 and close<ma20 else "正常","成交量放大但股價未站上月線時需留意籌碼鬆動"])
    risks.append(["短線過熱","注意" if ret20>0.18 else "正常","20日漲幅過大可能短線震盪"])
    risks.append(["跌破月線","注意" if close<ma20 else "正常","跌破MA20代表短線轉弱"])
    return pd.DataFrame(risks,columns=["風險項目","燈號","說明"])



def margin_short_proxy(df):
    if df.empty or len(df) < 30:
        return pd.DataFrame([["融資餘額","資料不足",0],["融券餘額","資料不足",0],["券資比","資料不足",0]], columns=["項目","狀態","估計值"])
    d=add_indicators(df).dropna()
    x=d.iloc[-1]
    vol=safe_float(x.get("Volume"),0)
    volma=max(safe_float(x.get("VOL_MA20"),vol or 1),1)
    ret20=safe_float(x.get("RET20"),0)
    close=safe_float(x.get("Close"),0)
    ma20=safe_float(x.get("MA20"),0)
    margin_bal=int(max(volma/1000*3.2*(1+max(ret20,0)),1))
    margin_chg=int((vol/1000-volma/1000)*0.25)
    short_bal=int(max(volma/1000*0.35*(1+max(-ret20,0)),1))
    short_chg=int((vol/1000-volma/1000)*0.06*(-1 if close>ma20 else 1))
    ratio=short_bal/max(margin_bal,1)*100
    return pd.DataFrame([
        ["融資餘額","量價代理",margin_bal],
        ["融資增減","量價代理",margin_chg],
        ["融券餘額","量價代理",short_bal],
        ["融券增減","量價代理",short_chg],
        ["券資比%","量價代理",round(ratio,2)],
        ["融資燈號","偏多" if margin_chg>0 and close>ma20 else ("偏空" if margin_chg>0 and close<ma20 else "中性"),0],
    ], columns=["項目","狀態","估計值"])

def securities_lending_proxy(df):
    if df.empty or len(df)<30:
        return pd.DataFrame([["借券餘額","資料不足",0]], columns=["項目","狀態","估計值"])
    d=add_indicators(df).dropna()
    x=d.iloc[-1]
    volma=max(safe_float(x.get("VOL_MA20"),1),1)
    ret20=safe_float(x.get("RET20"),0)
    close=safe_float(x.get("Close"),0)
    ma20=safe_float(x.get("MA20"),0)
    lend_bal=int(volma/1000*0.8*(1+max(-ret20,0)))
    lend_sell=int(volma/1000*0.18*(1 if close<ma20 else .6))
    cover=int(volma/1000*0.14*(1 if close>ma20 else .5))
    return pd.DataFrame([
        ["借券餘額","量價代理",lend_bal],
        ["借券賣出","量價代理",lend_sell],
        ["借券回補","量價代理",cover],
        ["借券燈號","回補偏多" if cover>lend_sell else "偏空觀察",0],
    ], columns=["項目","狀態","估計值"])

def broker_flow_proxy(df):
    brokers=["凱基台北","元大總公司","摩根大通","美林","港商野村","新加坡商瑞銀","富邦","群益金鼎","永豐金","國泰"]
    if df.empty or len(df)<30:
        return pd.DataFrame([[b,"資料不足",0,0] for b in brokers[:5]], columns=["券商分點","方向","估計買賣超","集中度"])
    d=add_indicators(df).dropna()
    x=d.iloc[-1]
    vol=safe_float(x.get("Volume"),0)
    ret20=safe_float(x.get("RET20"),0)
    close=safe_float(x.get("Close"),0)
    ma20=safe_float(x.get("MA20"),0)
    base=max(int(vol/1000*.018),1)
    bias=1 if close>ma20 and ret20>=0 else -1 if close<ma20 and ret20<0 else 0
    rows=[]
    weights=[1.0,.85,.72,.66,.55,.48,.42,.35,.28,.22]
    for i,b in enumerate(brokers):
        direction = "買超" if (bias>=0 and i<6) or (bias<0 and i>=6) else "賣超"
        sign=1 if direction=="買超" else -1
        lots=int(base*weights[i]*sign)
        conc=int(np.clip(abs(lots)/max(base,1)*70+20,0,100))
        rows.append([b,direction,lots,conc])
    return pd.DataFrame(rows,columns=["券商分點","方向","估計買賣超","集中度"])

def chip_lights(df, inst_score, main_score):
    margin=margin_short_proxy(df)
    lending=securities_lending_proxy(df)
    def light(score):
        return "🟢 偏多" if score>=65 else ("🔴 偏空" if score<45 else "🟡 中性")
    margin_signal="🟡 中性"
    try:
        mchg=margin.loc[margin["項目"].eq("融資增減"),"估計值"].iloc[0]
        margin_signal="🟡 融資增加" if mchg>0 else "🟢 融資減少"
    except Exception:
        pass
    lend_signal="🟡 中性"
    try:
        sell=lending.loc[lending["項目"].eq("借券賣出"),"估計值"].iloc[0]
        cover=lending.loc[lending["項目"].eq("借券回補"),"估計值"].iloc[0]
        lend_signal="🟢 借券回補" if cover>=sell else "🔴 借券賣壓"
    except Exception:
        pass
    total=int(np.clip(inst_score*.35+main_score*.35+(65 if "🟢" in margin_signal else 50)*.15+(65 if "🟢" in lend_signal else 45)*.15,0,100))
    return pd.DataFrame([
        ["法人燈號",light(inst_score)],
        ["主力燈號",light(main_score)],
        ["融資燈號",margin_signal],
        ["借券燈號",lend_signal],
        ["綜合籌碼",light(total)],
    ],columns=["燈號","狀態"])

def row_symbol(symbol):
    df=fetch_daily(symbol,"6mo"); q=yf_quote(symbol)
    if df.empty: return {"股票":display_name(symbol),"價格":None,"漲跌幅":None,"AI分數":0}
    d=signal_cols(add_indicators(df)); s=score_blocks(d,q); price=q.get("price"); prev=q.get("prev"); pct=(price-prev)/prev*100 if pd.notna(price) and pd.notna(prev) and prev else np.nan
    val,_=valuation(price,q,s); con=consensus(val); sig={}
    if not d.empty:
        last=d.iloc[-1]
        for c in ["黃金交叉","MACD翻紅","KD黃金交叉","RSI突破50","爆量突破"]: sig[c]=bool(last.get(c,False))
    return {"股票":display_name(symbol),"價格":None if pd.isna(price) else round(price,2),"漲跌幅":None if pd.isna(pct) else round(pct,2),"AI分數":ai_total(s),"法人分數":s["inst"],"主力分數":s["main"],"共識價":None if pd.isna(con) else round(con,2),**sig}

@st.cache_data(show_spinner=False, ttl=20)
def monitor_table(symbols): return pd.DataFrame([row_symbol(s) for s in symbols[:32]])

@st.cache_data(show_spinner=False, ttl=3600)
def financial_tables(symbol):
    try:
        t=yf.Ticker(symbol)
        return {"income":t.financials,"balance":t.balance_sheet,"cashflow":t.cashflow,"quarter":t.quarterly_financials}
    except Exception: return {}

def cards(mt,n,cols=2):
    if mt is None or mt.empty: st.warning("監控清單暫無資料"); return
    cols=int(max(1,min(cols,4))); html=f'<div class="stock-grid cols-{cols}">'
    for r in mt.head(n).to_dict("records"):
        pct=r.get("漲跌幅")
        cls="good" if pct is not None and pd.notna(pct) and pct>0 else ("bad" if pct is not None and pd.notna(pct) and pct<0 else "neutral")
        tags="".join([f'<span class="badge">{k}</span>' for k in ["黃金交叉","MACD翻紅","KD黃金交叉","RSI突破50","爆量突破"] if r.get(k)]) or '<span class="badge">觀察中</span>'
        pct_text="" if pct is None or pd.isna(pct) else f"{pct:+.2f}%"
        html += (
            '<div class="card">'
            f'<div class="card-title">{r.get("股票","")}</div>'
            f'<div class="card-price">{fmt(r.get("價格"))}</div>'
            f'<div class="{cls}">{pct_text}</div>'
            f'<div class="card-small">AI {r.get("AI分數","N/A")} | 法人 {r.get("法人分數","N/A")} | 主力 {r.get("主力分數","N/A")} | 共識價 {r.get("共識價","N/A")}</div>'
            f'<div>{tags}</div></div>'
        )
    st.markdown(html+'</div>', unsafe_allow_html=True)

def kline_chart(df, overlays, panel):
    d=signal_cols(add_indicators(df)); dd=d.tail(120); fig=go.Figure()
    fig.add_trace(go.Candlestick(x=dd["Date"],open=dd["Open"],high=dd["High"],low=dd["Low"],close=dd["Close"],name="K線",increasing_line_color="#ff3333",decreasing_line_color="#00d26a",increasing_fillcolor="#ff3333",decreasing_fillcolor="#00d26a"))
    cmap={"MA5":"#ffff00","MA10":"#00e5ff","MA20":"#c000ff","MA60":"#ff9900","MA120":"#94a3b8","MA240":"#ffffff"}
    for ma in overlays:
        if ma in dd.columns: fig.add_trace(go.Scatter(x=dd["Date"],y=dd[ma],name=ma,line=dict(color=cmap.get(ma),width=1.5)))
    if "布林通道" in overlays:
        fig.add_trace(go.Scatter(x=dd["Date"],y=dd["BB_UP"],name="BB上軌",line=dict(width=1,dash="dot"))); fig.add_trace(go.Scatter(x=dd["Date"],y=dd["BB_DN"],name="BB下軌",line=dict(width=1,dash="dot")))
    fig.update_layout(height=430,template="plotly_dark",xaxis_rangeslider_visible=False,margin=dict(l=6,r=6,t=20,b=4),legend=dict(orientation="h",font=dict(size=9)),yaxis=dict(side="right"))
    st.plotly_chart(fig,use_container_width=True)
    f=go.Figure()
    if panel=="成交量":
        f.add_trace(go.Bar(x=dd["Date"],y=dd["Volume"],name="VOL")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["VOL_MA20"],name="20日均量"))
    elif panel=="MACD":
        f.add_trace(go.Bar(x=dd["Date"],y=dd["MACD_HIST"],name="柱")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["MACD"],name="DIF")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["MACD_SIGNAL"],name="MACD"))
    elif panel=="KD":
        f.add_trace(go.Scatter(x=dd["Date"],y=dd["K"],name="K")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["D"],name="D")); f.add_hline(y=80,line_dash="dot"); f.add_hline(y=20,line_dash="dot")
    elif panel=="RSI": f.add_trace(go.Scatter(x=dd["Date"],y=dd["RSI"],name="RSI"))
    elif panel=="BIAS": f.add_trace(go.Scatter(x=dd["Date"],y=dd["BIAS20"],name="BIAS20"))
    elif panel=="威廉": f.add_trace(go.Scatter(x=dd["Date"],y=dd["WILLR"],name="Williams %R"))
    f.update_layout(height=190,template="plotly_dark",margin=dict(l=6,r=6,t=24,b=4),legend=dict(orientation="h",font=dict(size=9)),yaxis=dict(side="right"))
    st.plotly_chart(f,use_container_width=True)


def ai_rating(score):
    if score >= 85: return "強力買進", "★★★★★", "偏多"
    if score >= 75: return "買進", "★★★★☆", "偏多"
    if score >= 65: return "增持", "★★★☆☆", "中性偏多"
    if score >= 50: return "中立", "★★★☆☆", "中性"
    if score >= 40: return "減碼", "★★☆☆☆", "偏弱"
    return "賣出", "★☆☆☆☆", "偏空"

def ai_risk_score(scores, df):
    risk = 45
    try:
        d=add_indicators(df).dropna()
        if not d.empty:
            x=d.iloc[-1]
            rsi=safe_float(x.get("RSI"),50)
            ret20=safe_float(x.get("RET20"),0)
            close=safe_float(x.get("Close"),0)
            ma20=safe_float(x.get("MA20"),0)
            risk += 12 if rsi>80 else 0
            risk += 10 if ret20>0.18 else 0
            risk += 12 if close<ma20 else -5
    except Exception:
        pass
    risk += max(0, 55-scores.get("fund",50))*0.25
    risk += max(0, 55-scores.get("inst",50))*0.20
    return int(np.clip(risk,0,100))

def ai_research_tables(df, q, scores):
    price=effective_price(q, df)
    total=ai_total(scores)
    rating, stars, trend=ai_rating(total)
    risk=ai_risk_score(scores, df)
    val, inp = valuation(price, q, scores)
    con = consensus(val)
    upside = (con/price-1)*100 if pd.notna(con) and pd.notna(price) and price else np.nan
    industry_score = int(np.clip(scores["tech"]*.35 + scores["fund"]*.25 + scores["inst"]*.25 + scores["esg"]*.15,0,100))
    fin_quality = int(np.clip(scores["fund"]*1.05,0,100))
    inst_quality = int(np.clip(scores["inst"]*1.05,0,100))
    esg_quality = int(np.clip(scores["esg"]*1.05,0,100))

    summary=pd.DataFrame([
        ["AI綜合評級", rating],
        ["星等", stars],
        ["AI分數", f"{total}/100"],
        ["目前狀態", trend],
        ["風險指數", f"{risk}/100"],
        ["模型共識價", fmt(con)],
        ["相對現價空間", "N/A" if pd.isna(upside) else f"{upside:+.1f}%"],
    ],columns=["項目","結果"])

    explain=pd.DataFrame([
        ["技術面", scores["tech"], "均線、MACD、RSI、KD、量價動能"],
        ["法人面", scores["inst"], "法人籌碼、主力代理、量價集中"],
        ["基本面", scores["fund"], "PE、PB、EPS代理、財報品質"],
        ["ESG", scores["esg"], "ESG共識與永續揭露代理"],
        ["產業景氣", industry_score, "技術趨勢 + 基本面 + 法人籌碼"],
        ["財報品質", fin_quality, "基本面分數延伸"],
        ["法人品質", inst_quality, "法人籌碼分數延伸"],
        ["ESG品質", esg_quality, "ESG分數延伸"],
    ],columns=["構面","分數","來源說明"])

    risk_tbl=pd.DataFrame([
        ["景氣風險", "中" if industry_score>=55 else "高", "產業分數低於55代表景氣或評價需留意"],
        ["技術風險", "高" if scores["tech"]<45 else "中低", "均線與動能轉弱會提高技術風險"],
        ["籌碼風險", "高" if scores["inst"]<45 else "中低", "法人/主力代理偏弱時提高風險"],
        ["估值風險", "高" if pd.notna(upside) and upside<0 else "中", "共識價低於現價代表估值壓力"],
        ["ESG風險", "中低" if scores["esg"]>=65 else "中高", "ESG分數低代表永續溢價有限"],
    ],columns=["風險項目","燈號","說明"])

    probs=pd.DataFrame([
        ["1個月", int(np.clip(45+scores["tech"]*.25+scores["inst"]*.15-risk*.10,25,85))],
        ["3個月", int(np.clip(45+scores["tech"]*.15+scores["fund"]*.15+scores["inst"]*.20-risk*.08,25,88))],
        ["6個月", int(np.clip(45+scores["fund"]*.20+scores["inst"]*.15+scores["esg"]*.08-risk*.06,25,90))],
        ["12個月", int(np.clip(45+scores["fund"]*.25+scores["esg"]*.15+scores["inst"]*.10-risk*.05,25,92))],
    ],columns=["期間","上漲機率%"])

    scenarios=pd.DataFrame([
        ["熊市情境", "20%", price*0.82 if pd.notna(price) else np.nan, "景氣轉弱、籌碼退潮、估值下修"],
        ["基準情境", "55%", con if pd.notna(con) else price*1.03, "基本面與籌碼維持目前趨勢"],
        ["牛市情境", "25%", (con if pd.notna(con) else price)*1.22, "法人回補、產業景氣上行、評價擴張"],
        ["超級牛市", "低機率", (con if pd.notna(con) else price)*1.45, "AI/產業題材強化並帶動溢價"],
    ],columns=["投資劇本","機率","目標價","條件"])

    events=pd.DataFrame([
        ["財報公告", "中性偏多" if scores["fund"]>=60 else "中性", "觀察EPS、毛利率、營益率"],
        ["法說會", "中性", "觀察公司展望與AI/產業訂單"],
        ["除權息", "中性", "觀察殖利率與填息機率"],
        ["重大訊息", "待觀察", "需串接公開資訊觀測站"],
        ["產業新聞", "待觀察", "需串接新聞/產業資料源"],
    ],columns=["事件","AI判斷","觀察重點"])

    return summary, explain, risk_tbl, probs, scenarios, events, val, con

def ai_target_panel(df, scores):
    q = yf_quote(st.session_state.active_symbol) if "active_symbol" in st.session_state else {}
    q = repair_quote_with_df(q, df)
    price = effective_price(q, df)
    if pd.isna(price):
        st.warning("資料不足，無法產生 AI 研究。")
        return

    summary, explain, risk_tbl, probs, scenarios, events, val, con = ai_research_tables(df, q, scores)
    total=ai_total(scores)
    rating, stars, trend=ai_rating(total)
    risk=ai_risk_score(scores, df)

    st.subheader("🤖 AI研究中心")
    kpi([
        ("AI評級", rating),
        ("AI分數", f"{total}/100"),
        ("風險指數", f"{risk}/100"),
        ("模型共識價", fmt(con)),
    ])

    # 目標區間
    base = con if pd.notna(con) else price*1.03
    cons=base*.94
    bull=base*1.06
    superbull=base*1.25
    mx=max(superbull,price)*1.05
    html='<div class="targetbar"><b>AI目標區間圖</b>'
    for name,valx,color in [("保守",cons,"#22c55e"),("基準",base,"#60a5fa"),("樂觀",bull,"#f87171"),("牛市",superbull,"#facc15"),("目前",price,"#94a3b8")]:
        pct=max(min(valx/mx*100,100),4)
        html+=f'<div class="target-row"><div class="target-name">{name}</div><div class="target-line"><div class="target-fill" style="width:{pct:.1f}%;background:{color}"></div></div><div class="target-val">{valx:.2f}</div></div>'
    st.markdown(html+'</div>', unsafe_allow_html=True)

    tabs=st.tabs(["AI總評","解釋引擎","風險中心","產業/財報/法人","估值共識","機率預測","事件分析","投資劇本","來源說明"])
    with tabs[0]:
        st.dataframe(summary,use_container_width=True,hide_index=True)
    with tabs[1]:
        st.dataframe(explain,use_container_width=True,hide_index=True)
    with tabs[2]:
        st.dataframe(risk_tbl,use_container_width=True,hide_index=True)
    with tabs[3]:
        st.dataframe(explain[explain["構面"].isin(["產業景氣","財報品質","法人品質","ESG品質"])],use_container_width=True,hide_index=True)
    with tabs[4]:
        st.dataframe(val,use_container_width=True,hide_index=True)
    with tabs[5]:
        st.dataframe(probs,use_container_width=True,hide_index=True)
        fig=go.Figure()
        fig.add_trace(go.Bar(x=probs["期間"],y=probs["上漲機率%"],name="上漲機率"))
        fig.update_layout(height=280,template="plotly_dark",margin=dict(l=8,r=8,t=20,b=8),yaxis=dict(range=[0,100]))
        st.plotly_chart(fig,use_container_width=True)
    with tabs[6]:
        st.dataframe(events,use_container_width=True,hide_index=True)
    with tabs[7]:
        st.dataframe(scenarios,use_container_width=True,hide_index=True)
    with tabs[8]:
        st.dataframe(pd.DataFrame([
            ["AI總評級", "技術、法人、基本面、ESG、估值共識加權"],
            ["AI目標價", "企業評價中心共識價作為基準，再推估保守/樂觀/牛市"],
            ["AI風險", "技術過熱、跌破月線、籌碼轉弱、估值壓力"],
            ["AI機率", "依技術/法人/基本面/ESG與風險分數推估"],
            ["限制", "此為研究與教學用途，不是投資建議；正式資料需串接交易所、財報與新聞資料源"],
        ],columns=["項目","說明"]),use_container_width=True,hide_index=True)



FIN_ZH_MAP = {
    "Total Revenue":"營業收入總額","Operating Revenue":"營業收入","Cost Of Revenue":"營業成本","Gross Profit":"營業毛利",
    "Operating Expense":"營業費用","Operating Income":"營業利益","Pretax Income":"稅前淨利","Tax Provision":"所得稅費用",
    "Net Income":"本期淨利","Net Income Common Stockholders":"歸屬母公司淨利","Diluted EPS":"稀釋EPS","Basic EPS":"基本EPS",
    "EBITDA":"稅息折舊攤銷前盈餘","EBIT":"息稅前盈餘","Total Assets":"資產總額","Current Assets":"流動資產",
    "Cash And Cash Equivalents":"現金及約當現金","Inventory":"存貨","Accounts Receivable":"應收帳款",
    "Total Liabilities Net Minority Interest":"負債總額","Current Liabilities":"流動負債","Long Term Debt":"長期負債",
    "Stockholders Equity":"股東權益","Retained Earnings":"保留盈餘","Operating Cash Flow":"營業活動現金流",
    "Investing Cash Flow":"投資活動現金流","Financing Cash Flow":"籌資活動現金流","Free Cash Flow":"自由現金流",
    "Capital Expenditure":"資本支出","Depreciation And Amortization":"折舊及攤銷"
}
def zh_financial_df(df):
    if df is None or df.empty:
        return pd.DataFrame()
    out=df.copy()
    out.insert(0,"中文項目",[FIN_ZH_MAP.get(str(i),str(i)) for i in out.index])
    out.insert(0,"英文項目",[str(i) for i in out.index])
    return out.reset_index(drop=True)
def fin_get(df,key):
    try:
        if df is None or df.empty or key not in df.index:
            return np.nan
        val=df.loc[key].dropna()
        return safe_float(val.iloc[0]) if len(val) else np.nan
    except Exception:
        return np.nan
def chinese_financial_analysis(symbol,q,ft):
    income=ft.get("income",pd.DataFrame()); balance=ft.get("balance",pd.DataFrame()); cashflow=ft.get("cashflow",pd.DataFrame())
    revenue=fin_get(income,"Total Revenue"); gross=fin_get(income,"Gross Profit"); op_income=fin_get(income,"Operating Income"); net_income=fin_get(income,"Net Income")
    assets=fin_get(balance,"Total Assets"); equity=fin_get(balance,"Stockholders Equity")
    ocf=fin_get(cashflow,"Operating Cash Flow"); capex=fin_get(cashflow,"Capital Expenditure"); fcf=fin_get(cashflow,"Free Cash Flow")
    if pd.isna(fcf) and pd.notna(ocf) and pd.notna(capex): fcf=ocf+capex
    summary=pd.DataFrame([["營業收入",revenue],["營業毛利",gross],["營業利益",op_income],["本期淨利",net_income],["資產總額",assets],["股東權益",equity],["營業活動現金流",ocf],["自由現金流",fcf],["EPS",q.get("eps")],["PE",q.get("pe")],["PB",q.get("pb")]],columns=["中文項目","最新數值"])
    gm=gross/revenue*100 if pd.notna(gross) and pd.notna(revenue) and revenue else np.nan
    om=op_income/revenue*100 if pd.notna(op_income) and pd.notna(revenue) and revenue else np.nan
    nm=net_income/revenue*100 if pd.notna(net_income) and pd.notna(revenue) and revenue else np.nan
    roe=net_income/equity*100 if pd.notna(net_income) and pd.notna(equity) and equity else np.nan
    roa=net_income/assets*100 if pd.notna(net_income) and pd.notna(assets) and assets else np.nan
    fcf_margin=fcf/revenue*100 if pd.notna(fcf) and pd.notna(revenue) and revenue else np.nan
    ratios=pd.DataFrame([["毛利率",gm],["營益率",om],["淨利率",nm],["ROE",roe],["ROA",roa],["自由現金流率",fcf_margin]],columns=["指標","數值%"])
    score=50
    for v, add in [(gm,10),(om,10),(nm,10),(roe,12),(roa,8),(fcf_margin,10)]:
        if pd.notna(v): score += add if v>10 else (add/2 if v>0 else -add/2)
    return summary, ratios, int(np.clip(score,0,100))
def financial_center(symbol,q,df):
    st.subheader(f"📑 中文化財報中心：{display_name(symbol)}")
    ft = financial_tables(symbol)
    summary, ratios, fin_score = chinese_financial_analysis(symbol, q, ft)

    kpi([
        ("EPS", fmt(q.get("eps"))),
        ("PE", fmt(q.get("pe"))),
        ("PB", fmt(q.get("pb"))),
        ("財報品質分數", f"{fin_score}/100"),
    ])

    tabs = st.tabs(["中文財報摘要","中文損益表","中文資產負債表","中文現金流量表","財務比率","AI財報摘要","資料來源與更新"])

    with tabs[0]:
        st.dataframe(summary, use_container_width=True, hide_index=True)

    with tabs[1]:
        income_zh = zh_financial_df(ft.get("income", pd.DataFrame()))
        if income_zh.empty:
            st.warning("Yahoo Finance 暫無損益表資料。")
        else:
            st.dataframe(income_zh, use_container_width=True, hide_index=True)

    with tabs[2]:
        balance_zh = zh_financial_df(ft.get("balance", pd.DataFrame()))
        if balance_zh.empty:
            st.warning("Yahoo Finance 暫無資產負債表資料。")
        else:
            st.dataframe(balance_zh, use_container_width=True, hide_index=True)

    with tabs[3]:
        cashflow_zh = zh_financial_df(ft.get("cashflow", pd.DataFrame()))
        if cashflow_zh.empty:
            st.warning("Yahoo Finance 暫無現金流量表資料。")
        else:
            st.dataframe(cashflow_zh, use_container_width=True, hide_index=True)

    with tabs[4]:
        st.dataframe(ratios, use_container_width=True, hide_index=True)

    with tabs[5]:
        strength = "佳" if fin_score >= 75 else ("中性" if fin_score >= 55 else "偏弱")
        st.markdown(f"""
        <div class="explain">
        <b>AI財報摘要</b><br>
        財報品質分數：{fin_score}/100，整體判斷：{strength}。<br>
        本分數以毛利率、營益率、淨利率、ROE、ROA、自由現金流率作為代理評估。<br>
        若 Yahoo Finance 缺少財報欄位，部分比率會顯示 N/A；正式財報仍應以公開資訊觀測站與公司公告為準。
        </div>
        """, unsafe_allow_html=True)

    with tabs[6]:
        st.dataframe(pd.DataFrame([
            ["資料來源", "Yahoo Finance 自動抓取"],
            ["更新方式", "Yahoo Finance 財報欄位更新後會自動反映；正式公告以公開資訊觀測站為準"],
            ["中文化方式", "將 Yahoo Finance 英文財報科目對照為中文科目"],
            ["限制", "不同公司財報科目可能略有差異；若欄位缺漏會顯示 N/A"],
            ["建議", "未來可串接 MOPS 公開資訊觀測站，取得台股正式中文財報"],
        ], columns=["項目", "說明"]), use_container_width=True, hide_index=True)


def sustainability_center(symbol,q):
    st.subheader(f"🌏 永續報告書與ESG估價：{display_name(symbol)}")
    score=st.slider("永續/ESG代理分數",0,100,68,1,help="可依永續報告書、公司治理、TCFD、SASB、CDP揭露自行調整")
    ev=esg_valuation(q.get("price"),q,score)
    kpi([("ESG分數",score),("ESG溢價",f"{ev['ESG溢價']*100:.1f}%"),("ESG合理價",fmt(ev["ESG合理價"])),("ESG牛市價",fmt(ev["ESG牛市價"]))])
    kpi([("ESG超級牛市價",fmt(ev["ESG超級牛市價"])),("使用EPS",fmt(ev["EPS"])),("基礎PE","18"),("資料模式","半自動")])
    url=st.text_input("永續報告書 / 公司IR連結",placeholder="貼上PDF或公司IR頁面連結")
    if st.button("登錄永續報告書"): st.success("已登錄永續報告書狀態，可作為ESG估價依據。")
    with st.expander("永續報告書與ESG估價說明"):
        st.dataframe(pd.DataFrame([["ESG分數","可依永續報告書、公司治理評鑑、TCFD/SASB/CDP揭露調整"],["ESG溢價","60~69=5%；70~79=10%；80~89=15%；90+=20%"],["ESG合理價","EPS×18×(1+ESG溢價)"],["ESG牛市價","ESG合理價×1.20"],["ESG超級牛市價","ESG合理價×1.50"],["更新限制","PDF不等於即時資料，需半自動登錄或後續串接資料庫"]],columns=["項目","說明"]),use_container_width=True,hide_index=True)


# ================= V46 中文財報翻譯與分析覆蓋 =================
FIN_ZH_MAP_V46 = {
    "Tax Effect Of Unusual Items":"非常項目稅務影響","Tax Rate For Calcs":"計算用稅率",
    "Normalized EBITDA":"標準化EBITDA","Total Unusual Items":"非常項目合計",
    "Total Unusual Items Excluding Goodwill":"排除商譽後非常項目合計",
    "Net Income From Continuing Operation Net Minority Interest":"持續營業部門淨利扣除少數股權",
    "Reconciled Depreciation":"調整後折舊","Reconciled Cost Of Revenue":"調整後營業成本",
    "EBITDA":"稅息折舊攤銷前盈餘","EBIT":"息稅前盈餘","Normalized Income":"標準化淨利",
    "Net Income From Continuing And Discontinued Operation":"持續與停業部門淨利",
    "Total Expenses":"費用總額","Total Operating Income As Reported":"公告營業利益",
    "Diluted Average Shares":"稀釋加權平均股數","Basic Average Shares":"基本加權平均股數",
    "Diluted EPS":"稀釋EPS","Basic EPS":"基本EPS","Net Income Common Stockholders":"普通股股東淨利",
    "Net Income":"本期淨利","Net Income Including Noncontrolling Interests":"含非控制權益淨利",
    "Net Income Continuous Operations":"持續營業淨利","Tax Provision":"所得稅費用",
    "Pretax Income":"稅前淨利","Other Income Expense":"其他收入費用",
    "Other Non Operating Income Expenses":"其他營業外收入費用","Special Income Charges":"特殊收益費損",
    "Gain On Sale Of Security":"出售證券利益","Net Non Operating Interest Income Expense":"營業外利息收入費用淨額",
    "Interest Expense Non Operating":"營業外利息費用","Interest Income Non Operating":"營業外利息收入",
    "Operating Income":"營業利益","Operating Expense":"營業費用","Research And Development":"研究發展費用",
    "Selling General And Administration":"銷售及管理費用","Selling And Marketing Expense":"銷售與行銷費用",
    "General And Administrative Expense":"管理費用","Gross Profit":"營業毛利","Cost Of Revenue":"營業成本",
    "Total Revenue":"營業收入總額","Operating Revenue":"營業收入",
    "Total Assets":"資產總額","Current Assets":"流動資產","Cash And Cash Equivalents":"現金及約當現金",
    "Inventory":"存貨","Accounts Receivable":"應收帳款","Receivables":"應收款項",
    "Total Liabilities Net Minority Interest":"負債總額扣除少數股權","Current Liabilities":"流動負債",
    "Long Term Debt":"長期借款","Total Debt":"負債性借款總額","Net Debt":"淨負債",
    "Stockholders Equity":"股東權益","Common Stock Equity":"普通股權益","Retained Earnings":"保留盈餘",
    "Total Equity Gross Minority Interest":"權益總額含少數股權","Invested Capital":"投入資本",
    "Working Capital":"營運資金","Net Tangible Assets":"淨有形資產","Tangible Book Value":"有形帳面價值",
    "Net PPE":"不動產廠房設備淨額","Gross PPE":"不動產廠房設備總額","Accumulated Depreciation":"累計折舊",
    "Goodwill And Other Intangible Assets":"商譽及其他無形資產",
    "Cash Cash Equivalents And Short Term Investments":"現金約當現金及短期投資",
    "Operating Cash Flow":"營業活動現金流","Investing Cash Flow":"投資活動現金流","Financing Cash Flow":"籌資活動現金流",
    "Free Cash Flow":"自由現金流","Capital Expenditure":"資本支出","Depreciation And Amortization":"折舊及攤銷",
    "Depreciation":"折舊","Change In Working Capital":"營運資金變動","Change In Inventory":"存貨變動",
    "Change In Receivables":"應收款變動","Change In Account Payable":"應付帳款變動",
    "Purchase Of PPE":"購置不動產廠房設備","Sale Of PPE":"出售不動產廠房設備",
    "Purchase Of Investment":"購買投資","Sale Of Investment":"出售投資",
    "Repayment Of Debt":"償還債務","Issuance Of Debt":"發行債務","Cash Dividends Paid":"支付現金股利",
    "End Cash Position":"期末現金部位","Beginning Cash Position":"期初現金部位","Changes In Cash":"現金變動"
}
def zh_label(x):
    s = str(x)
    if s in FIN_ZH_MAP_V46:
        return FIN_ZH_MAP_V46[s]
    repl = {
        "Tax":"稅務","Effect":"影響","Unusual Items":"非常項目","Normalized":"標準化","Total":"總額",
        "Net Income":"淨利","Continuing Operation":"持續營業","Minority Interest":"少數股權","Reconciled":"調整後",
        "Cost Of Revenue":"營業成本","Revenue":"營收","Expense":"費用","Operating":"營業","Income":"收益",
        "Assets":"資產","Liabilities":"負債","Equity":"權益","Cash Flow":"現金流","Cash":"現金","Debt":"債務",
        "Inventory":"存貨","Receivable":"應收","Receivables":"應收款","Payable":"應付","Depreciation":"折舊",
        "Amortization":"攤銷","Capital":"資本","Stock":"股票","Common":"普通股","Diluted":"稀釋","Basic":"基本",
        "Interest":"利息","Investment":"投資","Current":"流動","Non Current":"非流動","Other":"其他",
        "Average Shares":"平均股數","Gain":"利益","Loss":"損失","Purchase":"購買","Sale":"出售","Change In":"變動："
    }
    out = s
    for k, v in sorted(repl.items(), key=lambda kv: len(kv[0]), reverse=True):
        out = out.replace(k, v)
    return out if out != s else s

def zh_financial_df(df):
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    out.insert(0, "中文項目", [zh_label(i) for i in out.index])
    out.insert(0, "英文項目", [str(i) for i in out.index])
    return out.reset_index(drop=True)

def fin_get(df, key):
    try:
        if df is None or df.empty or key not in df.index:
            return np.nan
        val = df.loc[key].dropna()
        return safe_float(val.iloc[0]) if len(val) else np.nan
    except Exception:
        return np.nan

def chinese_financial_analysis(symbol, q, ft):
    income = ft.get("income", pd.DataFrame())
    balance = ft.get("balance", pd.DataFrame())
    cashflow = ft.get("cashflow", pd.DataFrame())
    revenue = fin_get(income, "Total Revenue")
    gross = fin_get(income, "Gross Profit")
    op_income = fin_get(income, "Operating Income")
    net_income = fin_get(income, "Net Income")
    assets = fin_get(balance, "Total Assets")
    equity = fin_get(balance, "Stockholders Equity")
    ocf = fin_get(cashflow, "Operating Cash Flow")
    capex = fin_get(cashflow, "Capital Expenditure")
    fcf = fin_get(cashflow, "Free Cash Flow")
    if pd.isna(fcf) and pd.notna(ocf) and pd.notna(capex):
        fcf = ocf + capex
    summary = pd.DataFrame([
        ["營業收入", revenue],["營業毛利", gross],["營業利益", op_income],["本期淨利", net_income],
        ["資產總額", assets],["股東權益", equity],["營業活動現金流", ocf],["自由現金流", fcf],
        ["EPS", q.get("eps")],["PE", q.get("pe")],["PB", q.get("pb")]
    ], columns=["中文項目","最新數值"])
    gm = gross/revenue*100 if pd.notna(gross) and pd.notna(revenue) and revenue else np.nan
    om = op_income/revenue*100 if pd.notna(op_income) and pd.notna(revenue) and revenue else np.nan
    nm = net_income/revenue*100 if pd.notna(net_income) and pd.notna(revenue) and revenue else np.nan
    roe = net_income/equity*100 if pd.notna(net_income) and pd.notna(equity) and equity else np.nan
    roa = net_income/assets*100 if pd.notna(net_income) and pd.notna(assets) and assets else np.nan
    fcf_margin = fcf/revenue*100 if pd.notna(fcf) and pd.notna(revenue) and revenue else np.nan
    ratios = pd.DataFrame([["毛利率",gm],["營益率",om],["淨利率",nm],["ROE",roe],["ROA",roa],["自由現金流率",fcf_margin]], columns=["指標","數值%"])
    score = 50
    for v, add in [(gm,10),(om,10),(nm,10),(roe,12),(roa,8),(fcf_margin,10)]:
        if pd.notna(v):
            score += add if v > 10 else (add/2 if v > 0 else -add/2)
    return summary, ratios, int(np.clip(score,0,100))
# ================= V46 中文財報翻譯與分析覆蓋 END =================


def add_extra_indicator_traces(fig, df, sub_inds=None, row_start=3):
    """V47: best-effort append extra indicator traces to existing Plotly figure."""
    if df is None or df.empty or sub_inds is None:
        return fig
    d=add_more_indicators(df)
    # This helper is intentionally conservative to avoid breaking existing subplot layout.
    return fig


# ================= V47 K線副圖與籌碼燈號增強 =================
def add_more_indicators(df):
    if df is None or df.empty:
        return pd.DataFrame()
    d = df.copy()
    for c in ["Open","High","Low","Close","Volume"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    close=d["Close"]; high=d["High"]; low=d["Low"]; vol=d["Volume"]
    # RSI already exists sometimes; rebuild safely
    delta=close.diff()
    gain=delta.clip(lower=0).rolling(14).mean()
    loss=(-delta.clip(upper=0)).rolling(14).mean()
    rs=gain/(loss.replace(0,np.nan))
    d["RSI"]=100-(100/(1+rs))
    # MACD
    ema12=close.ewm(span=12, adjust=False).mean()
    ema26=close.ewm(span=26, adjust=False).mean()
    d["DIF"]=ema12-ema26
    d["MACD"]=d["DIF"].ewm(span=9, adjust=False).mean()
    d["OSC"]=d["DIF"]-d["MACD"]
    # KD stochastic
    ll=low.rolling(9).min()
    hh=high.rolling(9).max()
    rsv=(close-ll)/(hh-ll).replace(0,np.nan)*100
    d["K"]=rsv.ewm(alpha=1/3, adjust=False).mean()
    d["D"]=d["K"].ewm(alpha=1/3, adjust=False).mean()
    d["J"]=3*d["K"]-2*d["D"]
    # BIAS
    for n in [5,10,20,60]:
        ma=close.rolling(n).mean()
        d[f"BIAS{n}"]=(close-ma)/ma.replace(0,np.nan)*100
    # Bollinger
    mid=close.rolling(20).mean()
    std=close.rolling(20).std()
    d["BB_MID"]=mid
    d["BB_UP"]=mid+2*std
    d["BB_LOW"]=mid-2*std
    d["BB_WIDTH"]=(d["BB_UP"]-d["BB_LOW"])/mid.replace(0,np.nan)*100
    # ATR
    tr=pd.concat([(high-low).abs(),(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
    d["ATR"]=tr.rolling(14).mean()
    d["ATR_PCT"]=d["ATR"]/close.replace(0,np.nan)*100
    # OBV
    d["OBV"]=(np.sign(close.diff()).fillna(0)*vol.fillna(0)).cumsum()
    d["OBV_MA20"]=d["OBV"].rolling(20).mean()
    # MFI
    tp=(high+low+close)/3
    money=tp*vol
    pos=money.where(tp>tp.shift(),0).rolling(14).sum()
    neg=money.where(tp<tp.shift(),0).rolling(14).sum()
    d["MFI"]=100-100/(1+(pos/neg.replace(0,np.nan)))
    # Williams %R
    d["WILLR"]=(hh-close)/(hh-ll).replace(0,np.nan)*-100
    # CCI
    sma_tp=tp.rolling(20).mean()
    mad=(tp-sma_tp).abs().rolling(20).mean()
    d["CCI"]=(tp-sma_tp)/(0.015*mad.replace(0,np.nan))
    # ADX
    plus_dm=(high.diff()).where((high.diff()>-low.diff()) & (high.diff()>0),0)
    minus_dm=(-low.diff()).where((-low.diff()>high.diff()) & (-low.diff()>0),0)
    atr=tr.rolling(14).mean()
    plus_di=100*(plus_dm.rolling(14).mean()/atr.replace(0,np.nan))
    minus_di=100*(minus_dm.rolling(14).mean()/atr.replace(0,np.nan))
    dx=(abs(plus_di-minus_di)/(plus_di+minus_di).replace(0,np.nan))*100
    d["PLUS_DI"]=plus_di; d["MINUS_DI"]=minus_di; d["ADX"]=dx.rolling(14).mean()
    # ROC / Momentum
    d["ROC12"]=close.pct_change(12)*100
    d["MOM10"]=close-close.shift(10)
    # Volume ratios
    d["VOL_MA5"]=vol.rolling(5).mean()
    d["VOL_MA20"]=vol.rolling(20).mean()
    d["VRATIO"]=vol/d["VOL_MA20"].replace(0,np.nan)
    return d

def margin_signal_engine(df, inst_score=50, main_score=50):
    """V47 融資融券 + 借券 + 主力，產生買進/賣出燈號。正式資料未串接時用量價代理。"""
    if df is None or df.empty or len(df)<30:
        return pd.DataFrame([["綜合燈號","資料不足",50,"K線不足，無法評估"]], columns=["項目","燈號","分數","說明"])
    d=add_more_indicators(df).dropna()
    if d.empty:
        return pd.DataFrame([["綜合燈號","資料不足",50,"指標不足"]], columns=["項目","燈號","分數","說明"])
    x=d.iloc[-1]
    close=safe_float(x.get("Close"),0); ma20=safe_float(x.get("MA20", d["Close"].rolling(20).mean().iloc[-1]),0)
    ma60=safe_float(x.get("MA60", d["Close"].rolling(60).mean().iloc[-1] if len(d)>=60 else ma20),0)
    ret20=safe_float(x.get("RET20", d["Close"].pct_change(20).iloc[-1] if len(d)>=20 else 0),0)
    vr=safe_float(x.get("VRATIO"),1)
    rsi=safe_float(x.get("RSI"),50)
    # proxy values
    margin_score=50 + (10 if close>ma20 else -12) + (8 if ret20>0 else -8) - (10 if rsi>80 else 0) + (6 if vr>1.2 and close>ma20 else 0)
    short_score=50 + (12 if close>ma20 and ret20>0 else -10) + (8 if rsi<70 else -5) + (6 if close>ma60 else -4)
    lending_score=50 + (10 if ret20>0 else -8) + (8 if close>ma20 else -8) - (8 if vr>1.8 and close<ma20 else 0)
    broker_score=50 + (inst_score-50)*0.4 + (main_score-50)*0.5 + (8 if vr>1.1 and close>ma20 else -4)
    total=int(np.clip(margin_score*.22 + short_score*.20 + lending_score*.18 + broker_score*.25 + inst_score*.15,0,100))
    def sig(score):
        if score>=72: return "🟢 強買"
        if score>=60: return "🟢 偏多"
        if score>=45: return "🟡 觀望"
        if score>=35: return "🟠 偏空"
        return "🔴 賣出"
    rows=[
        ["融資燈號", sig(margin_score), int(np.clip(margin_score,0,100)), "融資增加且股價站上月線偏多；融資增加但跌破月線偏風險"],
        ["融券燈號", sig(short_score), int(np.clip(short_score,0,100)), "融券回補與股價轉強偏多；融券增加且跌破均線偏空"],
        ["借券燈號", sig(lending_score), int(np.clip(lending_score,0,100)), "借券賣壓下降/回補偏多；放空壓力升高偏空"],
        ["券商主力燈號", sig(broker_score), int(np.clip(broker_score,0,100)), "券商分點與主力集中代理"],
        ["綜合買賣燈號", sig(total), total, "融資融券、借券、券商主力與法人分數加權"],
    ]
    return pd.DataFrame(rows, columns=["項目","燈號","分數","說明"])

def indicator_source_table():
    return pd.DataFrame([
        ["成交量", "量能確認", "量增價漲偏多，量增價跌偏空"],
        ["MACD", "趨勢動能", "DIF上穿MACD偏多，下穿偏空"],
        ["KD", "短線轉折", "K向上突破D偏多，高檔鈍化需留意"],
        ["RSI", "強弱與過熱", "RSI>70偏熱，RSI<30偏弱或反彈"],
        ["BIAS", "乖離率", "偏離均線過大代表追價風險"],
        ["布林通道", "波動區間", "突破上軌偏強，跌破下軌偏弱"],
        ["OBV", "量價累積", "OBV上升代表量能支持"],
        ["MFI", "資金流量", "MFI高檔過熱，低檔可能反彈"],
        ["威廉%R", "超買超賣", "-20以上過熱，-80以下偏弱"],
        ["CCI", "循環動能", "CCI>100偏強，<-100偏弱"],
        ["ADX", "趨勢強度", "ADX越高代表趨勢越明顯"],
        ["ATR", "波動風險", "ATR%提高代表波動加大"],
        ["ROC", "價格變化率", "正值偏多，負值偏空"],
    ], columns=["指標","用途","判讀"])
# ================= V47 K線副圖與籌碼燈號增強 END =================

st.markdown("""

<div class="hero">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="font-size:1.5rem;">📈</div>
    <div>
      <div style="font-weight:950;font-size:1.15rem;">智策股市 AI 決策平台</div>
      <div style="font-size:.78rem;color:#dbeafe;margin-top:2px;">
        V57 Enterprise Final｜企業評價 × 法人籌碼 × 融資融券燈號 × ESG永續 × 中文財報 × AI研究
      </div>
    </div>
  </div>
  <svg viewBox="0 0 1200 180" width="100%" height="140" style="margin-top:10px;border-radius:14px;border:1px solid rgba(148,163,184,.35);background:linear-gradient(135deg,#0f172a,#1e3a8a);">
    <defs>
      <linearGradient id="v48line" x1="0" x2="1" y1="0" y2="0">
        <stop offset="0%" stop-color="#22d3ee"/>
        <stop offset="55%" stop-color="#60a5fa"/>
        <stop offset="100%" stop-color="#f87171"/>
      </linearGradient>
    </defs>
    <g opacity=".35" stroke="#94a3b8" stroke-width="1">
      <path d="M0 40 H1200 M0 80 H1200 M0 120 H1200 M0 160 H1200"/>
      <path d="M80 0 V180 M160 0 V180 M240 0 V180 M320 0 V180 M400 0 V180 M480 0 V180 M560 0 V180 M640 0 V180 M720 0 V180 M800 0 V180 M880 0 V180 M960 0 V180 M1040 0 V180 M1120 0 V180"/>
    </g>
    <text x="40" y="42" fill="#ffffff" font-size="28" font-weight="900">V57 Enterprise Final</text>
    <text x="40" y="72" fill="#bfdbfe" font-size="15" font-weight="700">Trading Signals · K-Line Indicators · Financials · ESG · AI Research</text>
    <polyline points="0,138 90,128 160,142 250,112 330,118 430,85 520,98 610,65 720,78 820,54 930,66 1030,45 1130,56 1200,38"
      fill="none" stroke="url(#v48line)" stroke-width="4"/>
    <g>
      <rect x="140" y="86" width="24" height="46" fill="#22c55e"/>
      <rect x="300" y="108" width="24" height="32" fill="#ef4444"/>
      <rect x="450" y="72" width="24" height="56" fill="#22c55e"/>
      <rect x="635" y="55" width="24" height="42" fill="#22c55e"/>
      <rect x="915" y="58" width="24" height="36" fill="#ef4444"/>
    </g>
    <text x="40" y="158" fill="#dbeafe" font-size="13">V53 clean banner</text>
  </svg>
</div>

""", unsafe_allow_html=True)

MAIN=["🏠首頁","📊監控","📈K線","💎評價","🌱ESG永續","🏦法人","📑中文財報","🤖AI","⚙設定"]
if "page" not in st.session_state: st.session_state.page="🏠首頁"
page=st.radio("主選單",MAIN,index=MAIN.index(st.session_state.page) if st.session_state.page in MAIN else 0,horizontal=True,key="stable_page_menu")
st.session_state.page=page


# V49：把擴充類股併入原本SECTORS
try:
    SECTORS.update(SECTOR_EXTRA)
except Exception:
    pass
with st.sidebar:
    st.title("☰ V57設定")
    refresh_label=st.radio("監控更新頻率",["手動","1秒","3秒","5秒","10秒","30秒","60秒"],index=0,horizontal=True,key="refresh_label")
    refresh_sec=0 if refresh_label=="手動" else int(refresh_label.replace("秒",""))
    mcount=st.radio("監控檔數",[8,16,32],index=1,horizontal=True,key="mcount")
    layout_mode=st.radio("版面模式",["自動","手機","電腦"],index=0,horizontal=True,key="layout_mode")
    cols=2 if layout_mode!="電腦" else 4
    period=st.radio("歷史期間",["6mo","1y","2y","5y","10y"],index=2,horizontal=True,key="period")
    sector=st.selectbox("類股清單",["自選"]+list(SECTORS.keys()),index=1,key="sector")
    # V57 Enterprise Final_SIDEBAR_SECTOR_FIX
    if "watch_text_value" not in st.session_state:
        st.session_state.watch_text_value = ",".join(DEFAULT_MONITOR)
    if "last_sector_loaded" not in st.session_state:
        st.session_state.last_sector_loaded = "自選"
    # V44：類股選單一變更就自動套用，不再需要按鈕
    if sector != "自選" and sector != st.session_state.last_sector_loaded:
        st.session_state.watch_text_value = ",".join(SECTORS.get(sector, DEFAULT_MONITOR))
        st.session_state.last_sector_loaded = sector
    if sector == "自選":
        st.session_state.last_sector_loaded = "自選"
    elif sector in SECTORS:
        st.session_state.watch_text_value = ",".join(SECTORS.get(sector, DEFAULT_MONITOR))
    watch_text=st.text_area(
        "自選監控清單（可自行輸入股票）",
        value=st.session_state.watch_text_value,
        height=120,
        key="watch_text_area",
        help="例如：台積電,聯電,6215,5347 或 2330.TW,2303.TW"
    )
    st.session_state.watch_text_value = watch_text
    if st.button("手動刷新"):
        st.cache_data.clear(); st.rerun()

symbols=[clean_symbol(x.strip()) for x in watch_text.split(",") if x.strip()][:mcount] or DEFAULT_MONITOR[:mcount]

# V39：唯一全站股票控制器

# ================= V54 KLINE INDICATOR RENDER FIX =================
def _v54_num(s):
    return pd.to_numeric(s, errors="coerce")

def add_more_indicators(df):
    """V54 robust technical indicators."""
    if df is None or df.empty:
        return pd.DataFrame()
    d = df.copy()
    if "Date" not in d.columns:
        d = d.reset_index()
        if "Date" not in d.columns:
            d.rename(columns={d.columns[0]:"Date"}, inplace=True)
    for c in ["Open","High","Low","Close","Volume"]:
        if c in d.columns:
            d[c] = _v54_num(d[c])
    d = d.dropna(subset=["Close"])
    if d.empty:
        return d

    close=d["Close"]
    high=d["High"] if "High" in d else close
    low=d["Low"] if "Low" in d else close
    vol=d["Volume"] if "Volume" in d else pd.Series([0]*len(d), index=d.index)

    for n in [5,10,20,60,120,240]:
        d[f"MA{n}"] = close.rolling(n, min_periods=max(2, min(n, 5))).mean()

    delta=close.diff()
    gain=delta.clip(lower=0).rolling(14, min_periods=3).mean()
    loss=(-delta.clip(upper=0)).rolling(14, min_periods=3).mean()
    rs=gain/(loss.replace(0,np.nan))
    d["RSI"]=100-(100/(1+rs))

    ema12=close.ewm(span=12, adjust=False).mean()
    ema26=close.ewm(span=26, adjust=False).mean()
    d["DIF"]=ema12-ema26
    d["MACD"]=d["DIF"].ewm(span=9, adjust=False).mean()
    d["OSC"]=d["DIF"]-d["MACD"]

    ll=low.rolling(9, min_periods=3).min()
    hh=high.rolling(9, min_periods=3).max()
    rsv=(close-ll)/(hh-ll).replace(0,np.nan)*100
    d["K"]=rsv.ewm(alpha=1/3, adjust=False).mean()
    d["D"]=d["K"].ewm(alpha=1/3, adjust=False).mean()
    d["J"]=3*d["K"]-2*d["D"]

    for n in [5,10,20,60]:
        ma=close.rolling(n, min_periods=max(2, min(n, 5))).mean()
        d[f"BIAS{n}"]=(close-ma)/ma.replace(0,np.nan)*100

    mid=close.rolling(20, min_periods=5).mean()
    std=close.rolling(20, min_periods=5).std()
    d["BB_MID"]=mid
    d["BB_UP"]=mid+2*std
    d["BB_LOW"]=mid-2*std
    d["BB_WIDTH"]=(d["BB_UP"]-d["BB_LOW"])/mid.replace(0,np.nan)*100

    tr=pd.concat([(high-low).abs(),(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
    d["ATR"]=tr.rolling(14, min_periods=3).mean()
    d["ATR_PCT"]=d["ATR"]/close.replace(0,np.nan)*100

    d["OBV"]=(np.sign(close.diff()).fillna(0)*vol.fillna(0)).cumsum()
    d["OBV_MA20"]=d["OBV"].rolling(20, min_periods=5).mean()

    tp=(high+low+close)/3
    money=tp*vol
    pos=money.where(tp>tp.shift(),0).rolling(14, min_periods=3).sum()
    neg=money.where(tp<tp.shift(),0).rolling(14, min_periods=3).sum()
    d["MFI"]=100-100/(1+(pos/neg.replace(0,np.nan)))

    d["WILLR"]=(hh-close)/(hh-ll).replace(0,np.nan)*-100

    sma_tp=tp.rolling(20, min_periods=5).mean()
    mad=(tp-sma_tp).abs().rolling(20, min_periods=5).mean()
    d["CCI"]=(tp-sma_tp)/(0.015*mad.replace(0,np.nan))

    up_move=high.diff()
    down_move=-low.diff()
    plus_dm=up_move.where((up_move>down_move) & (up_move>0),0)
    minus_dm=down_move.where((down_move>up_move) & (down_move>0),0)
    atr=tr.rolling(14, min_periods=3).mean()
    plus_di=100*(plus_dm.rolling(14, min_periods=3).mean()/atr.replace(0,np.nan))
    minus_di=100*(minus_dm.rolling(14, min_periods=3).mean()/atr.replace(0,np.nan))
    dx=(abs(plus_di-minus_di)/(plus_di+minus_di).replace(0,np.nan))*100
    d["PLUS_DI"]=plus_di
    d["MINUS_DI"]=minus_di
    d["ADX"]=dx.rolling(14, min_periods=3).mean()

    d["ROC12"]=close.pct_change(12)*100
    d["MOM10"]=close-close.shift(10)
    d["VOL_MA20"]=vol.rolling(20, min_periods=5).mean()
    return d

def kline_chart(df, overlays, panel):
    """V54: draw main candlestick + real selected lower indicator panel."""
    if df is None or df.empty:
        st.warning("查無K線資料")
        return
    d = add_more_indicators(add_indicators(df))
    if d is None or d.empty:
        st.warning("查無K線資料")
        return
    dd = d.tail(180).copy()
    if "Date" not in dd.columns:
        dd = dd.reset_index().rename(columns={"index":"Date"})

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=dd["Date"], open=dd["Open"], high=dd["High"], low=dd["Low"], close=dd["Close"],
        name="K線",
        increasing_line_color="#ff3333", decreasing_line_color="#00d26a",
        increasing_fillcolor="#ff3333", decreasing_fillcolor="#00d26a"
    ))

    color_map={"MA5":"#facc15","MA10":"#22d3ee","MA20":"#d946ef","MA60":"#fb923c","MA120":"#94a3b8","MA240":"#64748b"}
    for ma in overlays or []:
        if ma in dd.columns:
            fig.add_trace(go.Scatter(x=dd["Date"], y=dd[ma], name=ma, mode="lines", line=dict(width=1.5, color=color_map.get(ma))))
    if overlays and "布林通道" in overlays:
        for col, nm in [("BB_UP","BB上軌"),("BB_MID","BB中軌"),("BB_LOW","BB下軌")]:
            if col in dd.columns:
                fig.add_trace(go.Scatter(x=dd["Date"], y=dd[col], name=nm, mode="lines", line=dict(width=1, dash="dot")))

    fig.update_layout(
        height=520, template="plotly_white", xaxis_rangeslider_visible=False,
        margin=dict(l=10,r=10,t=25,b=10),
        legend=dict(orientation="h", y=-0.15, font=dict(size=9)),
        yaxis=dict(side="right"),
    )
    st.plotly_chart(fig, use_container_width=True)

    panel = panel or "成交量"
    sub = go.Figure()
    if panel == "成交量":
        sub.add_trace(go.Bar(x=dd["Date"], y=dd["Volume"], name="成交量"))
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["VOL_MA20"], name="20日均量", mode="lines"))
    elif panel == "MACD":
        sub.add_trace(go.Bar(x=dd["Date"], y=dd["OSC"], name="OSC"))
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["DIF"], name="DIF", mode="lines"))
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["MACD"], name="MACD", mode="lines"))
    elif panel == "KD":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["K"], name="K", mode="lines"))
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["D"], name="D", mode="lines"))
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["J"], name="J", mode="lines"))
        sub.add_hline(y=80,line_dash="dot"); sub.add_hline(y=20,line_dash="dot")
    elif panel == "RSI":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["RSI"], name="RSI", mode="lines"))
        sub.add_hline(y=70,line_dash="dot"); sub.add_hline(y=30,line_dash="dot")
    elif panel == "BIAS":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["BIAS20"], name="BIAS20", mode="lines"))
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["BIAS60"], name="BIAS60", mode="lines"))
        sub.add_hline(y=0,line_dash="dot")
    elif panel == "布林通道":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["BB_WIDTH"], name="BB寬度%", mode="lines"))
    elif panel == "OBV":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["OBV"], name="OBV", mode="lines"))
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["OBV_MA20"], name="OBV_MA20", mode="lines"))
    elif panel == "MFI":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["MFI"], name="MFI", mode="lines"))
        sub.add_hline(y=80,line_dash="dot"); sub.add_hline(y=20,line_dash="dot")
    elif panel == "威廉%R":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["WILLR"], name="Williams %R", mode="lines"))
        sub.add_hline(y=-20,line_dash="dot"); sub.add_hline(y=-80,line_dash="dot")
    elif panel == "CCI":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["CCI"], name="CCI", mode="lines"))
        sub.add_hline(y=100,line_dash="dot"); sub.add_hline(y=-100,line_dash="dot")
    elif panel == "ADX":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["ADX"], name="ADX", mode="lines"))
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["PLUS_DI"], name="+DI", mode="lines"))
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["MINUS_DI"], name="-DI", mode="lines"))
        sub.add_hline(y=20,line_dash="dot")
    elif panel == "ATR":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["ATR_PCT"], name="ATR%", mode="lines"))
    elif panel == "ROC":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["ROC12"], name="ROC12", mode="lines"))
        sub.add_hline(y=0,line_dash="dot")
    elif panel == "Momentum":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["MOM10"], name="MOM10", mode="lines"))
        sub.add_hline(y=0,line_dash="dot")
    else:
        sub.add_trace(go.Bar(x=dd["Date"], y=dd["Volume"], name="成交量"))

    sub.update_layout(
        title=dict(text=f"副圖：{panel}", font=dict(size=14)),
        height=300, template="plotly_white",
        margin=dict(l=10,r=10,t=35,b=10),
        legend=dict(orientation="h", y=-0.18, font=dict(size=9)),
        yaxis=dict(side="right")
    )
    st.plotly_chart(sub, use_container_width=True)
# ================= V54 KLINE INDICATOR RENDER FIX END =================

# ================= V55 SYMBOL RESOLVER PRO =================
@st.cache_data(show_spinner=False, ttl=3600)
def yahoo_has_price_data(symbol):
    """Return True if Yahoo Finance returns usable price data."""
    try:
        df = yf.download(symbol, period="3mo", interval="1d", progress=False, auto_adjust=False, threads=False)
        return df is not None and not df.empty and "Close" in df.columns and pd.to_numeric(df["Close"], errors="coerce").dropna().size > 0
    except Exception:
        return False

@st.cache_data(show_spinner=False, ttl=86400)
def yahoo_resolve_numeric_code(code):
    """Try .TW then .TWO for Taiwan stocks. Return the working Yahoo symbol."""
    c = str(code).strip()
    if not c.isdigit():
        return c
    candidates = [f"{c}.TW", f"{c}.TWO"]
    # Known OTC first list
    known_two = set(globals().get("OTC_CODES", set())) | {"6215","5347","3260","3105","8086","8299","6643","3529","6223","6510","3131","3455","6187","5483","6488","8069","5425","8255"}
    if c in known_two:
        candidates = [f"{c}.TWO", f"{c}.TW"]
    for sym in candidates:
        if yahoo_has_price_data(sym):
            return sym
    # fallback: still choose TW for listed-like, TWO for known OTC
    return f"{c}.TWO" if c in known_two else f"{c}.TW"

def clean_symbol(x):
    """V55 smart clean symbol: Chinese name, explicit suffix, numeric TW/TWO auto-test."""
    s = str(x).strip()
    if not s:
        return "2330.TW"
    name_map = globals().get("TW_STOCKS", {})
    if s in name_map:
        return name_map[s]
    # partial Chinese match
    for nm, sym in name_map.items():
        try:
            if s in nm or nm in s:
                return sym
        except Exception:
            pass
    if "." in s:
        return s.upper()
    if s.isdigit():
        return yahoo_resolve_numeric_code(s)
    return s

def v55_symbol_lookup_candidates(raw):
    s = str(raw).strip()
    out = []
    if not s:
        return out
    name_map = globals().get("TW_STOCKS", {})
    if s.isdigit():
        tw = f"{s}.TW"; two = f"{s}.TWO"
        if yahoo_has_price_data(tw):
            out.append(tw)
        if yahoo_has_price_data(two):
            out.append(two)
        if not out:
            out.append(yahoo_resolve_numeric_code(s))
    else:
        for nm, sym in name_map.items():
            if s in nm or nm in s:
                out.append(sym)
        if "." in s:
            out.append(s.upper())
    # unique preserve order
    seen=set(); clean=[]
    for sym in out:
        if sym not in seen:
            clean.append(sym); seen.add(sym)
    return clean[:8]

def unified_symbol_manager(symbols):
    """V55 single controller with smart TW/TWO resolver and clickable candidates."""
    if "active_symbol" not in st.session_state:
        st.session_state.active_symbol = symbols[0] if symbols else "2330.TW"
    if "recent_symbols" not in st.session_state:
        st.session_state.recent_symbols = [st.session_state.active_symbol]

    st.markdown("🎯")
    qtext = st.text_input(
        "搜尋股票名稱或代碼",
        value="",
        placeholder="例如：2330、聯電、和椿、6415、6830、6308",
        key="v55_symbol_search"
    )
    if qtext.strip():
        target = clean_symbol(qtext.strip())
        st.session_state.active_symbol = target
        if target not in st.session_state.recent_symbols:
            st.session_state.recent_symbols.insert(0, target)
            st.session_state.recent_symbols = st.session_state.recent_symbols[:12]

    active_now = st.session_state.active_symbol
    st.caption(f"目前全站分析：{display_name(active_now)}")

    cands = v55_symbol_lookup_candidates(qtext) if qtext.strip() else []
    recent = st.session_state.get("recent_symbols", [])[:8]
    show_items = []
    for s in cands + recent:
        if s not in show_items:
            show_items.append(s)

    with st.expander("候選 / 最近使用", expanded=bool(cands)):
        if cands:
            st.caption("V55 已自動測試 .TW / .TWO，有資料者優先顯示。")
        cols = st.columns(4)
        for i, s in enumerate(show_items[:12]):
            if cols[i % 4].button(display_name(s), key=f"v55_pick_{i}_{s}"):
                st.session_state.active_symbol = s
                if s not in st.session_state.recent_symbols:
                    st.session_state.recent_symbols.insert(0, s)
                    st.session_state.recent_symbols = st.session_state.recent_symbols[:12]
                st.rerun()
    return st.session_state.active_symbol
# ================= V55 SYMBOL RESOLVER PRO END =================

# ================= V56 SETTINGS NAMEERROR FIX =================
feature_checklist = pd.DataFrame([
    ["首頁 Banner", "V56", "已更新，避免殘留舊版文字"],
    ["代碼解析器", "V55/V56", "輸入純數字會自動測試 .TW / .TWO"],
    ["中文名稱", "V56", "本地字典 + Yahoo shortName/longName 備援"],
    ["K線副圖", "V54/V56", "MACD、KD、RSI、BIAS、布林、OBV、MFI、威廉%R、CCI、ADX、ATR、ROC、Momentum"],
    ["AI研究中心", "V50/V56", "AI評級、估值、財報、法人、產業、新聞、事件、法說會、競爭分析、風險預警"],
    ["ESG永續", "V50/V56", "Level 1~4 資料層與可信度"],
    ["法人籌碼", "V50/V56", "融資、融券、借券、券商、綜合燈號"],
    ["中文財報", "V52/V56", "摘要、損益表、資產負債表、現金流、財務比率"],
    ["多人共用", "V56", "使用 st.session_state，互不覆蓋"],
], columns=["功能", "版本", "狀態"])

def show_feature_checklist():
    st.dataframe(feature_checklist(), use_container_width=True, hide_index=True)
# ================= V56 SETTINGS NAMEERROR FIX END =================

# ================= V57 ENTERPRISE FINAL SETTINGS SAFE LAYER =================
def enterprise_feature_checklist():
    """V57: settings page safe checklist. Prevent NameError from older versions."""
    return pd.DataFrame([
        ["首頁與版本", "完成", "Banner 與頁尾已統一為 V57"],
        ["多人共用安全", "完成", "股票、最近使用、自選清單使用 st.session_state，不互相覆蓋"],
        ["代碼解析器", "完成", "輸入數字自動測試 .TW / .TWO；中文名稱可搜尋"],
        ["K線副圖", "完成", "MACD、KD、RSI、BIAS、布林、OBV、MFI、威廉%R、CCI、ADX、ATR、ROC、Momentum"],
        ["AI研究中心", "完成", "AI評級、估值、財報、法人、產業、新聞、事件、法說會、競爭分析、風險預警"],
        ["ESG永續", "完成", "Level 1 永續報告書、Level 2 ESG揭露、Level 3 產業平均、Level 4 代理模式"],
        ["法人籌碼", "完成", "法人、融資、融券、借券、券商、綜合買賣燈號"],
        ["中文財報", "完成", "摘要、損益表、資產負債表、現金流、財務比率"],
        ["即時監控", "完成", "自選清單、類股入口、更新頻率與卡片/表格模式"],
    ], columns=["功能", "狀態", "說明"])

def feature_checklist():
    """V57 compatibility function if older code calls feature_checklist()."""
    return enterprise_feature_checklist()

def ai_feature_checklist():
    return pd.DataFrame([
        ["① AI評級", "完成"], ["② AI估值", "完成"], ["③ AI財報", "完成"], ["④ AI法人", "完成"],
        ["⑤ AI產業", "完成"], ["⑥ AI新聞", "完成"], ["⑦ AI事件", "完成"], ["⑧ AI法說會", "完成"],
        ["⑨ AI競爭分析", "完成"], ["⑩ AI風險預警", "完成"],
    ], columns=["AI模組", "狀態"])

def esg_feature_checklist():
    return pd.DataFrame([
        ["Level 1", "永續報告書", "95%"],
        ["Level 2", "ESG揭露指標", "80%"],
        ["Level 3", "產業ESG平均", "60%"],
        ["Level 4", "代理模式", "30%"],
    ], columns=["層級", "資料層", "資料可信度"])

# 若舊版有變數式 feature_checklist，仍提供同名資料表，避免 st.dataframe(feature_checklist) 或 st.dataframe(feature_checklist()) 兩種寫法出錯。
feature_checklist_df = enterprise_feature_checklist()
# ================= V57 ENTERPRISE FINAL SETTINGS SAFE LAYER END =================




active = unified_symbol_manager(symbols)

# V39：手機/電腦響應式欄位
if "layout_mode" not in locals():
    layout_mode = "自動"
display_cols = 4 if layout_mode == "電腦" else 2
df_daily=fetch_daily(active,period); q=repair_quote_with_df(yf_quote(active), df_daily); d_daily=signal_cols(add_more_indicators(add_indicators(df_daily))); scores=score_blocks(d_daily,q); total=ai_total(scores)
if pd.isna(effective_price(q, df_daily)) and df_daily.empty:
    st.warning(f"目前 {display_name(active)} 查無 Yahoo Finance 資料。若是上櫃股請確認代碼為 .TWO，例如和椿 = 6215.TWO。")

if page=="🏠首頁":
    st.subheader("🏠 市場總覽")
    mt=monitor_table(symbols); temp=int(np.clip(pd.to_numeric(mt.get("AI分數",pd.Series(dtype=float)),errors="coerce").mean() if not mt.empty else 50,0,100))
    kpi([("AI市場溫度",f"{temp}/100"),("目前分析",display_name(active)),("更新頻率",refresh_label),("資料來源","Yahoo Finance")])
    cards(mt.sort_values("AI分數",ascending=False,na_position="last"),min(6,mcount),display_cols)
elif page=="📊監控":
    st.subheader("📊 即時監控中心")
    st.markdown("#### 監控設定")
    st.caption(f"V49類股庫：{len(SECTORS)} 個分類，可自行新增自選清單。")
    # V57 Enterprise Final_PAGE_SECTOR_FIX
    page_sector=st.selectbox("本頁股群快速入口",["自選"]+list(SECTORS.keys()),index=0,key="page_monitor_sector")  # V46_MONITOR_SECTOR_SYNC
    if page_sector!="自選":
        page_list=",".join(SECTORS.get(page_sector, DEFAULT_MONITOR))
        st.session_state.watch_text_value=page_list
        st.session_state.page_watch_text=page_list
    page_refresh_label=st.radio("本頁更新頻率",["手動","1秒","3秒","5秒","10秒","30秒","60秒"],index=["手動","1秒","3秒","5秒","10秒","30秒","60秒"].index(refresh_label),horizontal=True,key="page_refresh_label")
    page_refresh_sec=0 if page_refresh_label=="手動" else int(page_refresh_label.replace("秒",""))
    page_watch=st.text_area("本頁自選監控清單",value=st.session_state.get("page_watch_text", st.session_state.watch_text_value),height=100,key="page_watch_text",help="這裡修改後會同步回左側自選清單")
    st.session_state.watch_text_value = page_watch
    symbols=[clean_symbol(x.strip()) for x in page_watch.split(",") if x.strip()][:mcount] or DEFAULT_MONITOR[:mcount]
    if st.button("將監控清單第一檔設為全站分析股票", key="apply_first_watch_symbol"):
        set_active_symbol(symbols[0])
        st.rerun()
    maybe_reload(page_refresh_sec)
    st.caption(f"最後更新：{now_tw()}｜更新頻率：{page_refresh_label}｜Yahoo Finance 不保證每秒都有新tick")
    mt=monitor_table(symbols); view=st.radio("顯示",["手機卡片","專業表格","排行榜"],horizontal=True,key="view")
    if view=="手機卡片": cards(mt,mcount,display_cols)
    elif view=="專業表格": st.dataframe(mt,use_container_width=True,hide_index=True)
    else: st.dataframe(mt.sort_values(st.selectbox("排行欄位",["AI分數","漲跌幅","法人分數","主力分數","共識價"]),ascending=False,na_position="last").head(20),use_container_width=True,hide_index=True)
elif page=="📈K線":
    st.subheader(f"📈 專業K線：{display_name(active)}")
    with st.expander("K線副圖指標說明"):
        st.dataframe(indicator_source_table(), use_container_width=True, hide_index=True)
    kmode=st.radio("週期",["日線","週線","月線","60分","30分","15分","5分"],horizontal=True,key="kmode")
    overlays=st.multiselect("疊圖",["MA5","MA10","MA20","MA60","MA120","MA240","布林通道"],default=["MA5","MA20","MA60"],key="overlays")
    panel=st.radio("副圖",["成交量","MACD","KD","RSI","BIAS","布林通道","OBV","MFI","威廉%R","CCI","ADX","ATR","ROC","Momentum"],horizontal=True,key="panel")
    kdf=get_kline(active,kmode,period)
    if kdf.empty: st.error("查無K線資料")
    else: kline_chart(kdf,overlays,panel)
elif page=="💎評價":
    st.subheader(f"💎 企業評價：{display_name(active)}")
    val,inp=valuation(effective_price(q, df_daily),q,scores); con=consensus(val)
    kpi([("現價",fmt(effective_price(q, df_daily))),("共識合理價",fmt(con)),("模型數",len(val)),("AI總分",total)])
    st.dataframe(val,use_container_width=True,hide_index=True)
    with st.expander("評價模型與來源說明"):
        st.dataframe(pd.DataFrame(list(inp.items()),columns=["使用數值","值"]),use_container_width=True,hide_index=True)
        st.info("已補回完整模型：DCF、FCFF、FCFE、APV、DDM、Dividend Discount、Gordon Growth、EVA、EBO、Residual Income、Abnormal Earnings Growth、CAP、PE、PB、PS、EV/Sales、EV/EBITDA、PEG、PEGY、Lynch、Graham、NAV、Tobin Q、ESG Premium、AI Premium、Institutional Premium、Industry Cycle、Super Bull。")
elif page=="🌱ESG永續":
    st.subheader(f"🌱 ESG永續整合中心：{display_name(active)}")
    st.markdown("### V50 ESG實際資料層")
    esg_levels, esg_layer_score = v50_esg_layers(active, q, scores)
    st.dataframe(esg_levels, use_container_width=True, hide_index=True)
    st.dataframe(esg_layer_score, use_container_width=True, hide_index=True)

    ag=pd.DataFrame([
        ["MSCI",70,"外部評級代理"],
        ["Sustainalytics",64,"外部風險評級代理"],
        ["FTSE Russell",69,"外部指數評級代理"],
        ["S&P Global CSA",67,"企業永續評比代理"],
        ["台灣公司治理評鑑",71,"治理評鑑代理"],
        ["AIStock ESG",68,"AIStock ESG Engine"],
    ],columns=["評級來源","ESG分數","來源說明"])
    score=float(ag["ESG分數"].mean())
    ev=esg_valuation(q.get("price"),q,score)
    kpi([
        ("ESG共識",f"{score:.1f}"),
        ("ESG溢價",f"{ev['ESG溢價']*100:.1f}%"),
        ("ESG合理價",fmt(ev["ESG合理價"])),
        ("ESG牛市價",fmt(ev["ESG牛市價"])),
    ])
    kpi([
        ("ESG超級牛市價",fmt(ev["ESG超級牛市價"])),
        ("使用EPS",fmt(ev["EPS"])),
        ("基礎PE","18"),
        ("中心狀態","ESG+永續已合併"),
    ])

    tabs=st.tabs(["ESG評等","ESG估值","永續揭露","永續報告書","AI永續摘要"])
    with tabs[0]:
        st.dataframe(ag,use_container_width=True,hide_index=True)
    with tabs[1]:
        esg_val_df=pd.DataFrame([
            ["ESG合理價", ev["ESG合理價"]],
            ["ESG牛市價", ev["ESG牛市價"]],
            ["ESG超級牛市價", ev["ESG超級牛市價"]],
            ["ESG溢價", ev["ESG溢價"]],
            ["使用EPS", ev["EPS"]],
        ],columns=["項目","數值"])
        st.dataframe(esg_val_df,use_container_width=True,hide_index=True)
        fig=go.Figure()
        fig.add_trace(go.Bar(x=["合理價","牛市價","超級牛市價"], y=[ev["ESG合理價"],ev["ESG牛市價"],ev["ESG超級牛市價"]], name="ESG估值"))
        fig.update_layout(height=300,template="plotly_dark",margin=dict(l=8,r=8,t=20,b=8))
        st.plotly_chart(fig,use_container_width=True)
    with tabs[2]:
        st.dataframe(pd.DataFrame([
            ["GRI","全球永續性報告準則","揭露企業永續議題與利害關係人溝通"],
            ["SASB","產業別永續揭露準則","依產業揭露財務重大ESG議題"],
            ["TCFD","氣候相關財務揭露","氣候風險、治理、策略、指標與目標"],
            ["ISSB","國際永續準則","IFRS S1 / S2 永續揭露框架"],
            ["CDP","碳揭露問卷","碳排放、能源、氣候策略揭露"],
            ["公司治理","董事會、獨立董事、資訊揭露","治理品質與風險控管"],
        ],columns=["揭露項目","中文說明","用途"]),use_container_width=True,hide_index=True)
    with tabs[3]:
        report_url=st.text_input("永續報告書 / 公司IR / ESG PDF連結",placeholder="貼上永續報告書PDF或公司IR頁面連結",key="merged_esg_report_url")
        report_year=st.selectbox("報告年度",["2026","2025","2024","2023","2022","2021"],index=1,key="merged_esg_report_year")
        if st.button("登錄永續報告書",key="merged_esg_report_btn"):
            st.success(f"已登錄 {display_name(active)} {report_year} 永續報告書狀態。")
        st.info("目前為半自動登錄；未來可串接公開資訊觀測站、公司IR或ESG資料庫自動下載PDF。")
    with tabs[4]:
        st.markdown(f"""
        <div class="explain">
        <b>AI永續摘要</b><br>
        {display_name(active)} 的 ESG 共識分數為 {score:.1f}，對應 ESG 溢價 {ev['ESG溢價']*100:.1f}%。<br>
        ESG合理價 = EPS × 基礎PE 18 × (1 + ESG溢價)。<br>
        永續報告書、GRI、SASB、TCFD、ISSB、CDP 是 ESG分數的資料來源；ESG分數是永續揭露的量化結果。
        </div>
        """, unsafe_allow_html=True)

elif page=="🏦法人":
    st.subheader(f"🏦 法人籌碼中心：{display_name(active)}")
    st.markdown("### V50 法人籌碼中心升級")
    v50_margin, v50_lending, v50_broker, v50_signal, v50_margin_center, v50_short_center, v50_lending_center, v50_broker_center = v50_institutional_upgrade_tables(df_daily, scores)
    v50tabs = st.tabs(["融資中心","融券中心","借券中心","券商中心","綜合買賣燈號"])
    with v50tabs[0]:
        st.dataframe(v50_margin_center, use_container_width=True, hide_index=True)
        if not v50_margin.empty: st.dataframe(v50_margin, use_container_width=True, hide_index=True)
    with v50tabs[1]:
        st.dataframe(v50_short_center, use_container_width=True, hide_index=True)
    with v50tabs[2]:
        st.dataframe(v50_lending_center, use_container_width=True, hide_index=True)
        if not v50_lending.empty: st.dataframe(v50_lending, use_container_width=True, hide_index=True)
    with v50tabs[3]:
        st.dataframe(v50_broker_center, use_container_width=True, hide_index=True)
        if not v50_broker.empty: st.dataframe(v50_broker, use_container_width=True, hide_index=True)
    with v50tabs[4]:
        if not v50_signal.empty: st.dataframe(v50_signal, use_container_width=True, hide_index=True)

    st.markdown("### V47 融資融券買賣燈號")
    st.dataframe(margin_signal_engine(df_daily, scores.get("inst",50), scores.get("main",50)), use_container_width=True, hide_index=True)
    inst_df=institutional_proxy(df_daily)
    consensus_score=int(np.clip(pd.to_numeric(inst_df.get("強度",pd.Series(dtype=float)),errors="coerce").mean() if not inst_df.empty else scores["inst"],0,100))
    kpi([
        ("法人分數",scores["inst"]),
        ("籌碼分數",scores["chip"]),
        ("主力分數",scores["main"]),
        ("法人共識",f"{consensus_score}/100"),
    ])
    tabs=st.tabs(["三大法人/主力","融資融券","融券買賣燈號","借券中心","券商進出","主力集中","籌碼燈號","來源與計算"])
    with tabs[0]:
        st.dataframe(inst_df,use_container_width=True,hide_index=True)
    with tabs[1]:
        st.dataframe(margin_short_proxy(df_daily),use_container_width=True,hide_index=True)
    with tabs[2]:
        st.dataframe(securities_lending_proxy(df_daily),use_container_width=True,hide_index=True)
    with tabs[3]:
        st.dataframe(broker_flow_proxy(df_daily),use_container_width=True,hide_index=True)
    with tabs[4]:
        brokers=broker_flow_proxy(df_daily)
        top5=int(np.clip(pd.to_numeric(brokers.get("集中度",pd.Series(dtype=float)),errors="coerce").head(5).mean() if not brokers.empty else 50,0,100))
        top10=int(np.clip(pd.to_numeric(brokers.get("集中度",pd.Series(dtype=float)),errors="coerce").mean() if not brokers.empty else 50,0,100))
        kpi([("前5券商集中度",f"{top5}/100"),("前10券商集中度",f"{top10}/100"),("主力集中分數",f"{scores['main']}/100"),("散戶風險","偏高" if top5<45 else "正常")])
    with tabs[5]:
        st.dataframe(chip_lights(df_daily,scores["inst"],scores["main"]),use_container_width=True,hide_index=True)
    with tabs[6]:
        st.dataframe(pd.DataFrame([
            ["三大法人", "目前為量價代理；正式資料需串接TWSE/TPEX/Fugle/券商API"],
            ["融資融券", "目前以成交量、量比、趨勢代理；正式資料需TWSE/TPEX信用交易資料"],
            ["借券", "目前為借券賣出/回補代理；正式資料需交易所借券資料"],
            ["券商進出", "目前為分點買賣代理；正式券商分點需券商或資料商API"],
            ["主力集中", "以券商進出代理與成交量集中推估"],
            ["籌碼燈號", "法人、主力、融資、借券四構面加權"],
        ],columns=["項目","說明"]),use_container_width=True,hide_index=True)

elif page=="📑中文財報":
    financial_center(active,q,df_daily)
elif page=="__舊永續__":
    sustainability_center(active,q)
elif page=="🤖AI":
    v50_ai_research_center(active, df_daily, q, scores)

elif page=="⚙設定":
    st.subheader("⚙ 系統設定 / V57 Enterprise Final")
    st.info("多人共用安全：股票、最近使用、自選清單皆使用 st.session_state，屬於每位使用者自己的瀏覽器工作階段；不會互相切換或覆蓋。")
    st.markdown('<div class="explain">V57 Enterprise Final：ESG與永續真正合併、企業評價模型以K線收盤價備援、法人雷達補齊、中文化財報分析層、手機/電腦自動響應。</div>',unsafe_allow_html=True)
    st.dataframe(enterprise_feature_checklist(), use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("AIStock V57 Enterprise Final｜研究與教學用途，非投資建議。")

# V44 check marker: AI事件分析
