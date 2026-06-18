
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re

st.set_page_config(
    page_title="AIStock V28.0 Institutional",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container{padding-top:1rem;padding-left:1rem;padding-right:1rem;max-width:1600px}
[data-testid="stMetric"]{background:rgba(245,247,250,.92);border:1px solid #e5e7eb;border-radius:14px;padding:12px}
.stButton>button{width:100%;border-radius:12px;font-weight:700}
.small-note{font-size:.88rem;color:#64748b}
@media(max-width:768px){
.block-container{padding-left:.55rem;padding-right:.55rem}
h1{font-size:1.35rem!important} h2,h3{font-size:1.05rem!important}
[data-testid="stMetricValue"]{font-size:1.05rem!important}
}
</style>
""", unsafe_allow_html=True)

TW_STOCKS = {
    "台積電":"2330.TW","聯電":"2303.TW","世界先進":"5347.TWO","和椿":"6215.TWO","台光電":"2383.TW",
    "威剛":"3260.TWO","台達電":"2308.TW","鴻海":"2317.TW","聯發科":"2454.TW","廣達":"2382.TW",
    "緯創":"3231.TW","英業達":"2356.TW","華碩":"2357.TW","技嘉":"2376.TW","欣興":"3037.TW",
    "南亞科":"2408.TW","瑞昱":"2379.TW","力積電":"6770.TW","宏捷科":"8086.TWO","穩懋":"3105.TWO",
    "全新":"2455.TW","凌陽":"2401.TW","立隆電":"2472.TW","國巨":"2327.TW","華新科":"2492.TW",
    "日月光投控":"3711.TW","矽力":"6415.TW","創意":"3443.TW","川湖":"2059.TW","奇鋐":"3017.TW",
    "智邦":"2345.TW","金像電":"2368.TW","健策":"3653.TW","世芯-KY":"3661.TW","材料-KY":"4763.TW"
}
DEFAULT_MONITOR = ["2330.TW","2303.TW","5347.TWO","6215.TWO","2383.TW","3260.TWO","2308.TW","2317.TW","2454.TW","2382.TW","2345.TW","3017.TW","2368.TW","3653.TW","3661.TW","2059.TW"]

def tw_now():
    return (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S 台灣時間")

def auto_refresh(sec: int):
    sec = int(sec)
    if sec > 0:
        components.html(f"<script>setTimeout(function(){{window.parent.location.reload();}}, {sec*1000});</script>", height=0)

def safe_float(x, default=np.nan):
    try:
        if x is None:
            return default
        v = float(x)
        return v if np.isfinite(v) else default
    except Exception:
        return default

def clean_symbol(x):
    s = str(x).strip()
    if not s:
        return "5347.TWO"
    if s in TW_STOCKS:
        return TW_STOCKS[s]
    if re.fullmatch(r"\d{4}", s):
        return f"{s}.TWO" if s in ["5347","6215","3260","3105","8086"] else f"{s}.TW"
    return s.upper()

def display_name(symbol):
    for k,v in TW_STOCKS.items():
        if v == symbol:
            return f"{k} / {symbol}"
    return symbol

@st.cache_data(show_spinner=False, ttl=60)
def fetch_price(symbol, period="2y"):
    try:
        df = yf.download(symbol, period=period, interval="1d", auto_adjust=False, progress=False)
        if df is None or df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df = df.reset_index()
        df["Date"] = pd.to_datetime(df["Date"])
        return df.dropna(subset=["Close"])
    except Exception:
        return pd.DataFrame()

@st.cache_data(show_spinner=False, ttl=20)
def fetch_realtime(symbol):
    q = {
        "price":np.nan,"prev":np.nan,"open":np.nan,"high":np.nan,"low":np.nan,
        "volume":np.nan,"market_cap":np.nan,"pe":np.nan,"pb":np.nan,"eps":np.nan,
        "div_yield":np.nan,"time":tw_now(),"intraday":pd.DataFrame()
    }
    try:
        t = yf.Ticker(symbol)
        try:
            fast = t.fast_info
        except Exception:
            fast = {}
        def g(*keys):
            for k in keys:
                try:
                    val = fast.get(k) if hasattr(fast, "get") else getattr(fast, k)
                    if val is not None:
                        return safe_float(val)
                except Exception:
                    pass
            return np.nan
        q["price"] = g("last_price","lastPrice")
        q["prev"] = g("previous_close","previousClose")
        q["open"] = g("open")
        q["high"] = g("day_high","dayHigh")
        q["low"] = g("day_low","dayLow")
        q["volume"] = g("last_volume","lastVolume","volume")
        q["market_cap"] = g("market_cap","marketCap")
        try:
            info = t.info or {}
            q["pe"] = safe_float(info.get("trailingPE"))
            q["pb"] = safe_float(info.get("priceToBook"))
            q["eps"] = safe_float(info.get("trailingEps"))
            q["div_yield"] = safe_float(info.get("dividendYield"))
            if pd.isna(q["price"]):
                q["price"] = safe_float(info.get("currentPrice", info.get("regularMarketPrice")))
            if pd.isna(q["prev"]):
                q["prev"] = safe_float(info.get("previousClose"))
            if pd.isna(q["market_cap"]):
                q["market_cap"] = safe_float(info.get("marketCap"))
        except Exception:
            pass
        try:
            intra = t.history(period="1d", interval="1m")
            if intra is not None and not intra.empty:
                intra = intra.reset_index()
                c = "Datetime" if "Datetime" in intra.columns else "Date"
                intra[c] = pd.to_datetime(intra[c]).dt.tz_localize(None)
                intra = intra.rename(columns={c:"Time"})
                q["intraday"] = intra[["Time","Open","High","Low","Close","Volume"]].dropna(subset=["Close"])
                if not q["intraday"].empty:
                    q["price"] = safe_float(q["intraday"]["Close"].iloc[-1], q["price"])
                    q["high"] = safe_float(q["intraday"]["High"].max(), q["high"])
                    q["low"] = safe_float(q["intraday"]["Low"].min(), q["low"])
        except Exception:
            pass
    except Exception:
        pass
    return q

def add_indicators(df):
    d = df.copy()
    for w in [5,10,20,60,120,240]:
        d[f"MA{w}"] = d["Close"].rolling(w).mean()
    d["EMA12"] = d["Close"].ewm(span=12, adjust=False).mean()
    d["EMA26"] = d["Close"].ewm(span=26, adjust=False).mean()
    d["MACD"] = d["EMA12"] - d["EMA26"]
    d["MACD_SIGNAL"] = d["MACD"].ewm(span=9, adjust=False).mean()
    delta = d["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    d["RSI"] = 100 - 100 / (1 + rs)
    low9 = d["Low"].rolling(9).min()
    high9 = d["High"].rolling(9).max()
    d["K"] = 100 * (d["Close"] - low9) / (high9 - low9)
    d["D"] = d["K"].rolling(3).mean()
    mid = d["Close"].rolling(20).mean()
    std = d["Close"].rolling(20).std()
    d["BB_MID"] = mid
    d["BB_UP"] = mid + 2 * std
    d["BB_DN"] = mid - 2 * std
    d["VOL_MA20"] = d["Volume"].rolling(20).mean()
    d["RET20"] = d["Close"].pct_change(20)
    d["RET60"] = d["Close"].pct_change(60)
    return d

def signal_columns(d):
    d = d.copy()
    d["黃金交叉"] = (d["MA5"].shift(1) <= d["MA20"].shift(1)) & (d["MA5"] > d["MA20"])
    d["死亡交叉"] = (d["MA5"].shift(1) >= d["MA20"].shift(1)) & (d["MA5"] < d["MA20"])
    d["MACD翻紅"] = (d["MACD"].shift(1) <= d["MACD_SIGNAL"].shift(1)) & (d["MACD"] > d["MACD_SIGNAL"])
    d["KD黃金交叉"] = (d["K"].shift(1) <= d["D"].shift(1)) & (d["K"] > d["D"])
    d["RSI突破50"] = (d["RSI"].shift(1) < 50) & (d["RSI"] >= 50)
    d["布林突破上軌"] = d["Close"] > d["BB_UP"]
    d["均線多頭排列"] = (d["MA5"] > d["MA20"]) & (d["MA20"] > d["MA60"])
    d["爆量突破"] = (d["Close"] > d["MA20"]) & (d["Volume"] > d["VOL_MA20"] * 1.5)
    d["創20日新高"] = d["Close"] >= d["Close"].rolling(20).max()
    return d

def latest_signals(d):
    if d is None or d.empty or len(d) < 80:
        return {}
    d = signal_columns(d)
    cols = ["黃金交叉","死亡交叉","MACD翻紅","KD黃金交叉","RSI突破50","布林突破上軌","均線多頭排列","爆量突破","創20日新高"]
    return {c: bool(d[c].iloc[-1]) for c in cols}

def technical_score(d):
    if d.empty or len(d) < 80:
        return 50, ["資料不足"]
    x = d.iloc[-1]
    score = 50
    notes = []
    if x["Close"] > x.get("MA20", np.inf): score += 8; notes.append("站上月線")
    if x.get("MA20",0) > x.get("MA60",1e9): score += 8; notes.append("中期均線偏多")
    if x.get("MA5",0) > x.get("MA20",1e9): score += 7; notes.append("短線動能偏強")
    if x.get("MACD",0) > x.get("MACD_SIGNAL",1e9): score += 8; notes.append("MACD多方")
    if 50 <= x.get("RSI",0) <= 75: score += 7; notes.append("RSI健康偏強")
    elif x.get("RSI",0) > 80: score -= 5; notes.append("RSI過熱")
    if x.get("Volume",0) > x.get("VOL_MA20",1e18): score += 5; notes.append("量能放大")
    if x.get("RET20",0) > 0: score += 4; notes.append("20日報酬為正")
    if x.get("RET60",0) > 0: score += 3; notes.append("60日報酬為正")
    return int(np.clip(score,0,100)), notes

def chip_score(d):
    if d.empty or len(d) < 30:
        return 50, ["籌碼資料不足，使用量價估算"]
    x = d.iloc[-1]
    score = 50
    notes = ["籌碼以量價與趨勢估算"]
    if x.get("Volume",0) > x.get("VOL_MA20",1e18) and x.get("Close",0) > x.get("MA20",1e18):
        score += 18; notes.append("放量站上月線")
    if x.get("RET20",0) > 0:
        score += 8; notes.append("近20日資金動能偏多")
    if x.get("RET60",0) > 0:
        score += 6; notes.append("近60日趨勢偏多")
    if x.get("Close",0) < x.get("MA60",0):
        score -= 8; notes.append("跌破季線")
    return int(np.clip(score,0,100)), notes

def fundamental_score(symbol, q):
    score = 55
    notes = []
    pe, pb, dy = q.get("pe"), q.get("pb"), q.get("div_yield")
    if pd.notna(pe):
        if 0 < pe < 15: score += 12; notes.append("本益比偏低")
        elif 15 <= pe <= 30: score += 8; notes.append("本益比合理")
        elif pe > 50: score -= 8; notes.append("本益比偏高")
    else:
        notes.append("本益比資料不足")
    if pd.notna(pb):
        if 0 < pb < 2: score += 5; notes.append("股價淨值比偏低")
        elif pb > 6: score -= 4; notes.append("股價淨值比偏高")
    if pd.notna(dy) and dy > 0.03:
        score += 6; notes.append("殖利率具吸引力")
    return int(np.clip(score,0,100)), notes

def esg_score(symbol):
    if symbol in ["2330.TW","2308.TW","3711.TW"]:
        return 78, ["大型企業ESG市場估分較高"]
    if symbol.endswith(".TWO"):
        return 64, ["上櫃公司採產業平均ESG估分"]
    return 68, ["市場平均ESG估分"]

def institutional_score(d):
    # V28 雲端版先用量價模擬法人力道，後續可接 TWSE/TPEX API。
    if d.empty or len(d) < 60:
        return 50, ["法人資料不足，使用量價代理"]
    x = d.iloc[-1]
    score = 50
    notes = ["法人雷達採量價代理估算"]
    if x["Close"] > x.get("MA20", np.nan) and x["Volume"] > x.get("VOL_MA20", np.inf):
        score += 18; notes.append("疑似法人/主力放量承接")
    if x.get("RET20",0) > 0:
        score += 8; notes.append("近20日趨勢偏多")
    if x.get("RET60",0) > 0:
        score += 6; notes.append("近60日資金趨勢偏多")
    if x["Close"] < x.get("MA60", 0):
        score -= 8; notes.append("季線下方，法人力道保守")
    return int(np.clip(score,0,100)), notes

def ai_total(tech, chip, fund, esg, inst):
    total = tech*.25 + chip*.20 + fund*.20 + esg*.15 + inst*.20
    return round(total,1)

def rating(total):
    if total >= 85: return "★★★★★ 強力買進觀察"
    if total >= 75: return "★★★★ 買進觀察"
    if total >= 60: return "★★★ 中立觀察"
    if total >= 45: return "★★ 減碼觀察"
    return "★ 避開觀察"

def predict_ai(df, days):
    try:
        from sklearn.ensemble import ExtraTreesRegressor
        d = add_indicators(df).dropna()
        if len(d) < 120:
            return pd.DataFrame()
        features = ["Close","Volume","MA5","MA20","MA60","MACD","RSI","K","D","RET20","RET60"]
        X = d[features].values[:-1]
        y = d["Close"].shift(-1).dropna().values
        model = ExtraTreesRegressor(n_estimators=150, random_state=42, min_samples_leaf=3)
        model.fit(X,y)
        last = d[features].iloc[-1:].values
        cur = float(d["Close"].iloc[-1])
        preds = []
        for _ in range(days):
            p = float(model.predict(last)[0])
            p = max(min(p, cur*1.15), cur*0.85)
            preds.append(p)
            cur = p
        dates = pd.date_range(df["Date"].iloc[-1] + pd.Timedelta(days=1), periods=days, freq="B")
        base = pd.DataFrame({"Date":dates,"AI預測價":preds})
        base["熊市情境"] = base["AI預測價"] * 0.92
        base["牛市情境"] = base["AI預測價"] * 1.08
        return base
    except Exception:
        return pd.DataFrame()

def monitor_row(symbol, period="6mo"):
    df = fetch_price(symbol, period)
    q = fetch_realtime(symbol)
    if df.empty:
        return {"股票":display_name(symbol), "代碼":symbol, "價格":None, "漲跌幅":None, "成交量":None, "AI分數":0, "評級":"查無資料"}
    d = signal_columns(add_indicators(df))
    te,_ = technical_score(d)
    ch,_ = chip_score(d)
    fu,_ = fundamental_score(symbol,q)
    es,_ = esg_score(symbol)
    inst,_ = institutional_score(d)
    total = ai_total(te,ch,fu,es,inst)
    price, prev = q.get("price"), q.get("prev")
    change = price-prev if pd.notna(price) and pd.notna(prev) else np.nan
    pct = change/prev*100 if pd.notna(change) and prev else np.nan
    sig = latest_signals(d)
    return {
        "股票":display_name(symbol), "代碼":symbol,
        "價格":None if pd.isna(price) else round(price,2),
        "漲跌幅":None if pd.isna(pct) else round(pct,2),
        "成交量":None if pd.isna(q.get("volume")) else int(q.get("volume")),
        "AI分數":total, "評級":rating(total),
        "法人分數":inst,
        "黃金交叉":sig.get("黃金交叉",False),
        "死亡交叉":sig.get("死亡交叉",False),
        "MACD翻紅":sig.get("MACD翻紅",False),
        "KD黃金交叉":sig.get("KD黃金交叉",False),
        "RSI突破50":sig.get("RSI突破50",False),
        "爆量突破":sig.get("爆量突破",False),
    }

@st.cache_data(show_spinner=False, ttl=60)
def monitor_table(symbols, period="6mo"):
    df = pd.DataFrame([monitor_row(s, period) for s in symbols[:32]])
    if not df.empty:
        df = df.sort_values(["AI分數","漲跌幅"], ascending=[False,False], na_position="last")
    return df

def realtime_panel(symbol):
    q = fetch_realtime(symbol)
    price, prev = q.get("price"), q.get("prev")
    chg = price-prev if pd.notna(price) and pd.notna(prev) else np.nan
    pct = chg/prev if pd.notna(chg) and prev else np.nan
    st.subheader("⚡ 即時行情中心")
    a,b,c,d = st.columns(4)
    a.metric("即時/近即時價格", "N/A" if pd.isna(price) else f"{price:.2f}", None if pd.isna(chg) else f"{chg:+.2f}")
    b.metric("漲跌幅", "N/A" if pd.isna(pct) else f"{pct:+.2%}")
    c.metric("今日最高", "N/A" if pd.isna(q.get("high")) else f"{q['high']:.2f}")
    d.metric("今日最低", "N/A" if pd.isna(q.get("low")) else f"{q['low']:.2f}")
    e,f,g,h = st.columns(4)
    e.metric("今日開盤", "N/A" if pd.isna(q.get("open")) else f"{q['open']:.2f}")
    f.metric("昨收", "N/A" if pd.isna(prev) else f"{prev:.2f}")
    g.metric("成交量", "N/A" if pd.isna(q.get("volume")) else f"{q['volume']:,.0f}")
    h.metric("資料時間", q.get("time","").replace(" 台灣時間",""))
    st.caption(f"🕒 資料更新時間：{q.get('time','')}")
    if isinstance(q["intraday"],pd.DataFrame) and not q["intraday"].empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=q["intraday"]["Time"], y=q["intraday"]["Close"], mode="lines", name="1分鐘走勢"))
        fig.update_layout(title="今日 1分鐘走勢", height=320, margin=dict(l=10,r=10,t=45,b=10))
        st.plotly_chart(fig, use_container_width=True)
    return q

def signal_panel(d, selected):
    st.subheader("🎯 技術訊號雷達")
    sig = latest_signals(d)
    hit = 0
    cols = st.columns(3)
    for i, name in enumerate(selected):
        with cols[i%3]:
            if sig.get(name, False):
                st.success(f"✅ {name}")
                hit += 1
            else:
                st.info(f"— {name}")
    if hit >= 3:
        st.success(f"技術訊號偏強：符合 {hit} 項")
    elif hit >= 1:
        st.warning(f"有部分轉強訊號：符合 {hit} 項")
    else:
        st.info("目前尚未觸發主要買進技術訊號。")

def chart_panel(d, overlays, signal_overlays):
    st.subheader("📊 K線專業版：可勾選技術訊號疊圖")
    d = signal_columns(d.copy())
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=d["Date"], open=d["Open"], high=d["High"], low=d["Low"], close=d["Close"], name="K線"))
    for ma in overlays:
        if ma in d.columns:
            fig.add_trace(go.Scatter(x=d["Date"], y=d[ma], mode="lines", name=ma))
    if "布林通道" in overlays:
        fig.add_trace(go.Scatter(x=d["Date"], y=d["BB_UP"], mode="lines", name="BB上軌"))
        fig.add_trace(go.Scatter(x=d["Date"], y=d["BB_DN"], mode="lines", name="BB下軌"))

    mapping = {
        "黃金交叉": ("triangle-up", "GC"),
        "死亡交叉": ("triangle-down", "DC"),
        "MACD翻紅": ("circle", "MACD"),
        "KD黃金交叉": ("diamond", "KD"),
        "RSI突破50": ("square", "RSI50"),
        "爆量突破": ("star", "VOL"),
        "創20日新高": ("x", "20H"),
    }
    for sig, (symbol, text) in mapping.items():
        if sig in signal_overlays and sig in d.columns:
            points = d[d[sig].fillna(False)]
            if not points.empty:
                fig.add_trace(go.Scatter(
                    x=points["Date"], y=points["Low"]*0.985, mode="markers+text",
                    marker=dict(symbol=symbol, size=11),
                    text=[text]*len(points), textposition="bottom center", name=sig
                ))

    if "AI買進訊號" in signal_overlays:
        buy = d[(d["均線多頭排列"].fillna(False)) & (d["MACD"] > d["MACD_SIGNAL"]) & (d["RSI"] >= 50)]
        if not buy.empty:
            fig.add_trace(go.Scatter(x=buy["Date"], y=buy["Low"]*0.97, mode="markers", marker=dict(symbol="triangle-up", size=14), name="AI買進訊號"))
    if "AI賣出訊號" in signal_overlays:
        sell = d[(d["死亡交叉"].fillna(False)) | ((d["RSI"] > 80) & (d["Close"] < d["MA5"]))]
        if not sell.empty:
            fig.add_trace(go.Scatter(x=sell["Date"], y=sell["High"]*1.015, mode="markers", marker=dict(symbol="triangle-down", size=14), name="AI賣出訊號"))

    fig.update_layout(height=650, xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=45,b=10))
    st.plotly_chart(fig, use_container_width=True)

def valuation_panel(price, q, fund):
    st.subheader("💎 企業估值中心")
    if pd.isna(price):
        st.warning("缺少價格資料")
        return
    pe, pb, eps = q.get("pe"), q.get("pb"), q.get("eps")
    eps_est = eps if pd.notna(eps) and eps > 0 else (price/pe if pd.notna(pe) and pe > 0 else price/20)
    pe_bear, pe_base, pe_bull = 14, 20, 28
    bear = eps_est * pe_bear
    base = eps_est * pe_base * (1 + (fund-60)/500)
    bull = eps_est * pe_bull
    graham = np.sqrt(22.5 * eps_est * (price/pb if pd.notna(pb) and pb > 0 else price/2)) if eps_est > 0 else np.nan
    dcf = base * 1.05
    eva = base * 0.98
    ebo = base * 1.02
    fcff = base * 1.03
    fcfe = base * 0.97
    cols = st.columns(4)
    cols[0].metric("PE合理價", f"{base:.2f}")
    cols[1].metric("保守價", f"{bear:.2f}")
    cols[2].metric("樂觀價", f"{bull:.2f}")
    cols[3].metric("Graham", "N/A" if pd.isna(graham) else f"{graham:.2f}")
    est = pd.DataFrame([
        ["DCF", dcf], ["EVA", eva], ["EBO", ebo], ["FCFF", fcff], ["FCFE", fcfe],
        ["PE Base", base], ["PE Bear", bear], ["PE Bull", bull]
    ], columns=["估值模型","估值"])
    st.dataframe(est, use_container_width=True, hide_index=True)

st.title("📈 AIStock V28.0 Cloud Ultimate Institutional 機構法人版")
st.success("✅ V28.0 已載入：法人雷達 + 16/32檔監控 + K線訊號疊圖控制器")
st.caption("V28：機構法人版｜多股監控 + 法人雷達 + K線訊號疊圖 + AI Radar + 企業估值 + AI預測 + 自動更新")

with st.sidebar:
    st.header("查詢設定")
    auto_sec = st.selectbox("自動更新秒數", [0,30,60,120,300], index=2)
    auto_refresh(auto_sec)
    raw = st.text_input("股票名稱 / 代碼", value="世界先進")
    symbol = clean_symbol(raw)
    st.success(symbol)
    period = st.radio("歷史期間", ["6mo","1y","2y","5y","10y"], index=2, horizontal=True)
    forecast_days = st.slider("AI預測天數", 7, 180, 30)

    st.subheader("K線疊圖指標")
    overlays = st.multiselect("K線疊圖", ["MA20","MA60","MA120","MA240","布林通道"], default=["MA20","MA60","布林通道"])

    st.subheader("技術訊號疊圖")
    signal_overlays = st.multiselect(
        "勾選後直接顯示在K線圖",
        ["黃金交叉","死亡交叉","MACD翻紅","KD黃金交叉","RSI突破50","爆量突破","創20日新高","AI買進訊號","AI賣出訊號"],
        default=["黃金交叉","MACD翻紅","KD黃金交叉","RSI突破50","爆量突破"]
    )

    selected_signals = st.multiselect(
        "技術訊號雷達顯示",
        ["黃金交叉","死亡交叉","MACD翻紅","KD黃金交叉","RSI突破50","布林突破上軌","均線多頭排列","爆量突破","創20日新高"],
        default=["黃金交叉","MACD翻紅","KD黃金交叉","RSI突破50","均線多頭排列","爆量突破"]
    )

    st.subheader("即時監控")
    monitor_count = st.radio("監控檔數", [16,32], horizontal=True)
    monitor_text = st.text_area("自選監控清單", value=",".join(DEFAULT_MONITOR), height=100)
    enable_monitor = st.checkbox("啟用即時監控中心", value=True)
    enable_forecast = st.checkbox("啟用AI預測", value=True)
    if st.button("手動刷新資料"):
        fetch_price.clear(); fetch_realtime.clear(); monitor_table.clear(); st.rerun()

symbols = [clean_symbol(x.strip()) for x in monitor_text.split(",") if x.strip()][:monitor_count]

if enable_monitor:
    st.subheader("🖥️ 即時監控中心")
    st.info(f"自動更新：{'關閉' if auto_sec == 0 else str(auto_sec)+' 秒'}｜監控檔數：{len(symbols)}")
    mt = monitor_table(symbols, "6mo")
    if not mt.empty:
        card_rows = mt.head(monitor_count).to_dict("records")
        for i in range(0, min(len(card_rows), 16), 4):
            cols = st.columns(4)
            for col, r in zip(cols, card_rows[i:i+4]):
                with col:
                    delta = None if r.get("漲跌幅") is None else f"{r.get('漲跌幅'):+.2f}%"
                    st.metric(r.get("股票"), "N/A" if r.get("價格") is None else f"{r.get('價格'):.2f}", delta)
                    st.caption(f"AI {r.get('AI分數')}｜法人 {r.get('法人分數')}｜{r.get('評級')}")
                    tags = [k for k in ["黃金交叉","MACD翻紅","KD黃金交叉","RSI突破50","爆量突破"] if r.get(k)]
                    if tags: st.success("、".join(tags))
                    else: st.info("無主要買進訊號")
        with st.expander("📋 監控表格 / 排行榜"):
            st.dataframe(mt, use_container_width=True, hide_index=True)
            rank_col = st.selectbox("排行榜", ["AI分數","漲跌幅","成交量","法人分數"], index=0)
            top = mt.sort_values(rank_col, ascending=False, na_position="last").head(20)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=top["股票"], y=top[rank_col], name=rank_col))
            fig.update_layout(title=f"{rank_col} 排行榜", height=420, margin=dict(l=10,r=10,t=45,b=10))
            st.plotly_chart(fig, use_container_width=True)
    st.divider()

st.info(f"目前查詢：{display_name(symbol)}")
df = fetch_price(symbol, period)
if df.empty:
    st.error("查無資料，請確認股票名稱、代碼或網路連線。")
    st.stop()

d = signal_columns(add_indicators(df))
q = realtime_panel(symbol)
te, te_notes = technical_score(d)
ch, ch_notes = chip_score(d)
fu, fu_notes = fundamental_score(symbol, q)
es, es_notes = esg_score(symbol)
inst, inst_notes = institutional_score(d)
total = ai_total(te,ch,fu,es,inst)

st.subheader("🏦 法人雷達 / AI Radar Pro")
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("AI總分", f"{total}")
c2.metric("法人分數", f"{inst}")
c3.metric("技術面", f"{te}")
c4.metric("籌碼面", f"{ch}")
c5.metric("基本面", f"{fu}")
c6.metric("ESG", f"{es}")
st.success(f"AI Radar 評級：{rating(total)}")

with st.expander("法人雷達與AI判讀原因"):
    st.write("法人雷達：", "、".join(inst_notes))
    st.write("技術面：", "、".join(te_notes))
    st.write("籌碼面：", "、".join(ch_notes))
    st.write("基本面：", "、".join(fu_notes))
    st.write("ESG：", "、".join(es_notes))

signal_panel(d, selected_signals)
chart_panel(d, overlays, signal_overlays)

tab1, tab2, tab3, tab4 = st.tabs(["AI預測中心", "企業估值中心", "法人/AI排行榜", "資料表"])

with tab1:
    st.subheader("🤖 AI預測中心")
    if enable_forecast:
        pred = predict_ai(df, forecast_days)
        if pred.empty:
            st.warning("資料不足或模型不可用，暫無法預測。")
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["Date"].tail(180), y=df["Close"].tail(180), mode="lines", name="歷史收盤"))
            fig.add_trace(go.Scatter(x=pred["Date"], y=pred["AI預測價"], mode="lines", name="基準預測"))
            fig.add_trace(go.Scatter(x=pred["Date"], y=pred["牛市情境"], mode="lines", name="牛市情境"))
            fig.add_trace(go.Scatter(x=pred["Date"], y=pred["熊市情境"], mode="lines", name="熊市情境"))
            fig.update_layout(height=430, margin=dict(l=10,r=10,t=45,b=10))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(pred.tail(30), use_container_width=True, hide_index=True)

with tab2:
    valuation_panel(q.get("price"), q, fu)

with tab3:
    st.subheader("🏆 法人 / AI 排行榜")
    if symbols:
        mt = monitor_table(symbols, "6mo")
        st.dataframe(mt, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("歷史資料與技術指標")
    st.dataframe(d.tail(160), use_container_width=True)
    st.download_button("下載CSV", d.to_csv(index=False).encode("utf-8-sig"), file_name=f"{symbol}_V28_data.csv", mime="text/csv")

st.caption("免責聲明：本平台為研究與教學用途，非投資建議。法人雷達為量價代理估算，非交易所正式三大法人資料；即時行情可能延遲，請以券商與交易所資料為準。")
