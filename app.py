# V27.5.1 Timezone Fix
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
from zoneinfo import zoneInfo
import time
import re

st.set_page_config(
    page_title="AIStock V27.5 Cloud Ultimate",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-left: 1rem; padding-right: 1rem; max-width: 1500px;}
[data-testid="stMetric"] {background: rgba(245,247,250,.85); border: 1px solid #e5e7eb; border-radius: 14px; padding: 12px;}
.stButton > button {width: 100%; border-radius: 12px; font-weight: 700;}
@media (max-width: 768px) {
    .block-container {padding-left: .55rem; padding-right: .55rem;}
    h1 {font-size: 1.35rem !important;}
    h2, h3 {font-size: 1.05rem !important;}
    [data-testid="stMetricValue"] {font-size: 1.05rem !important;}
}
</style>
""", unsafe_allow_html=True)

TW_STOCKS = {
    "台積電": "2330.TW", "聯電": "2303.TW", "世界先進": "5347.TWO", "和椿": "6215.TWO",
    "台光電": "2383.TW", "威剛": "3260.TWO", "台達電": "2308.TW", "鴻海": "2317.TW",
    "聯發科": "2454.TW", "廣達": "2382.TW", "緯創": "3231.TW", "英業達": "2356.TW",
    "華碩": "2357.TW", "技嘉": "2376.TW", "欣興": "3037.TW", "南亞科": "2408.TW",
    "瑞昱": "2379.TW", "力積電": "6770.TW", "宏捷科": "8086.TWO", "穩懋": "3105.TWO",
    "全新": "2455.TW", "凌陽": "2401.TW", "立隆電": "2472.TW", "國巨": "2327.TW",
    "華新科": "2492.TW", "日月光投控": "3711.TW", "矽力": "6415.TW", "創意": "3443.TW",
}

WATCHLIST = ["2330.TW", "2303.TW", "5347.TWO", "6215.TWO", "2383.TW", "3260.TWO", "2308.TW", "2317.TW", "2454.TW", "2382.TW"]

def clean_symbol(text: str) -> str:
    s = str(text).strip()
    if not s:
        return "5347.TWO"
    if s in TW_STOCKS:
        return TW_STOCKS[s]
    if s.upper() in ["TSM", "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "AMD", "TSLA"]:
        return s.upper()
    if re.fullmatch(r"\d{4}", s):
        # 常見上櫃代號
        if s in ["5347","6215","3260","3105","8086"]:
            return f"{s}.TWO"
        return f"{s}.TW"
    return s

def stock_display_name(symbol: str) -> str:
    for k, v in TW_STOCKS.items():
        if v == symbol:
            return f"{k} / {symbol}"
    return symbol

def safe_float(x, default=np.nan):
    try:
        if x is None:
            return default
        v = float(x)
        if np.isfinite(v):
            return v
        return default
    except Exception:
        return default

@st.cache_data(show_spinner=False, ttl=60)
def fetch_price(symbol: str, period: str = "2y"):
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
def fetch_realtime(symbol: str):
    result = {"price": np.nan, "prev": np.nan, "open": np.nan, "high": np.nan, "low": np.nan, "volume": np.nan,
              "market_cap": np.nan, "pe": np.nan, "div_yield": np.nan, "time": datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S 台灣時間"),
              "intraday": pd.DataFrame()}
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
        result["price"] = g("last_price", "lastPrice")
        result["prev"] = g("previous_close", "previousClose")
        result["open"] = g("open")
        result["high"] = g("day_high", "dayHigh")
        result["low"] = g("day_low", "dayLow")
        result["volume"] = g("last_volume", "lastVolume", "volume")
        result["market_cap"] = g("market_cap", "marketCap")
        try:
            info = t.info or {}
            result["pe"] = safe_float(info.get("trailingPE", np.nan))
            result["div_yield"] = safe_float(info.get("dividendYield", np.nan))
            if pd.isna(result["price"]): result["price"] = safe_float(info.get("currentPrice", info.get("regularMarketPrice")))
            if pd.isna(result["prev"]): result["prev"] = safe_float(info.get("previousClose"))
            if pd.isna(result["market_cap"]): result["market_cap"] = safe_float(info.get("marketCap"))
        except Exception:
            pass
        try:
            intra = t.history(period="1d", interval="1m")
            if intra is not None and not intra.empty:
                intra = intra.reset_index()
                time_col = "Datetime" if "Datetime" in intra.columns else "Date"
                intra[time_col] = pd.to_datetime(intra[time_col]).dt.tz_localize(None)
                intra = intra.rename(columns={time_col: "Time"})
                result["intraday"] = intra[["Time","Open","High","Low","Close","Volume"]].dropna(subset=["Close"])
                if pd.isna(result["price"]):
                    result["price"] = safe_float(result["intraday"]["Close"].iloc[-1])
                if pd.isna(result["high"]):
                    result["high"] = safe_float(result["intraday"]["High"].max())
                if pd.isna(result["low"]):
                    result["low"] = safe_float(result["intraday"]["Low"].min())
        except Exception:
            pass
    except Exception:
        pass
    return result

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
    d["BB_UP"] = mid + 2 * std
    d["BB_DN"] = mid - 2 * std
    d["VOL_MA20"] = d["Volume"].rolling(20).mean()
    d["RET20"] = d["Close"].pct_change(20)
    d["RET60"] = d["Close"].pct_change(60)
    return d

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
    return int(np.clip(score, 0, 100)), notes

def fundamental_score(symbol, quote):
    score = 55
    notes = []
    pe = quote.get("pe", np.nan)
    dy = quote.get("div_yield", np.nan)
    if pd.notna(pe):
        if 0 < pe < 15: score += 12; notes.append("本益比偏低")
        elif 15 <= pe <= 30: score += 8; notes.append("本益比合理")
        elif pe > 50: score -= 8; notes.append("本益比偏高")
    else:
        notes.append("本益比資料不足")
    if pd.notna(dy) and dy > 0.03:
        score += 6; notes.append("殖利率具吸引力")
    if symbol.endswith(".TW") or symbol.endswith(".TWO"):
        score += 3; notes.append("台股資料模式")
    return int(np.clip(score,0,100)), notes

def chip_score(d):
    if d.empty or len(d) < 30:
        return 50, ["籌碼資料不足，使用量價估算"]
    x = d.iloc[-1]
    score = 50
    notes = ["籌碼以量價動能估算"]
    if x.get("Volume",0) > x.get("VOL_MA20",1e18) and x.get("Close",0) > x.get("MA20",1e18):
        score += 18; notes.append("放量站上月線")
    if x.get("RET20",0) > 0:
        score += 8; notes.append("近20日資金動能偏多")
    if x.get("RET60",0) > 0:
        score += 6; notes.append("近60日趨勢偏多")
    if x.get("Close",0) < x.get("MA60",0):
        score -= 8; notes.append("跌破季線")
    return int(np.clip(score,0,100)), notes

def esg_score(symbol):
    # 雲端版先採產業市場估分；後續可接永續報告書與外部ESG API
    base = 68
    if symbol in ["2330.TW","2308.TW","3711.TW"]:
        base = 78
    elif symbol.endswith(".TWO"):
        base = 64
    notes = ["ESG採市場/產業估分，非正式評級"]
    return base, notes

def ai_radar_score(tech, chip, fund, esg):
    total = tech*0.30 + chip*0.25 + fund*0.25 + esg*0.20
    if total >= 85:
        rating = "★★★★★ 強力買進觀察"
    elif total >= 75:
        rating = "★★★★ 買進觀察"
    elif total >= 60:
        rating = "★★★ 中立觀察"
    elif total >= 45:
        rating = "★★ 減碼觀察"
    else:
        rating = "★ 避開觀察"
    return round(total, 1), rating

def xgb_predict(df, days):
    try:
        from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
        d = add_indicators(df).dropna().copy()
        if len(d) < 120:
            return None
        features = ["Close","Volume","MA5","MA20","MA60","MACD","RSI","K","D","RET20","RET60"]
        X = d[features].values
        y = d["Close"].shift(-1).dropna().values
        X = X[:-1]
        model = ExtraTreesRegressor(n_estimators=160, random_state=42, min_samples_leaf=3)
        model.fit(X, y)
        last = d[features].iloc[-1:].values
        preds = []
        cur = float(d["Close"].iloc[-1])
        for i in range(days):
            p = float(model.predict(last)[0])
            p = max(p, cur*0.85)
            p = min(p, cur*1.15)
            preds.append(p)
            cur = p
        future_dates = pd.date_range(df["Date"].iloc[-1] + pd.Timedelta(days=1), periods=days, freq="B")
        return pd.DataFrame({"Date": future_dates, "AI預測價": preds})
    except Exception:
        return None

def valuation_panel(price, quote, fund_score):
    pe = quote.get("pe", np.nan)
    if pd.isna(price):
        st.warning("缺少價格資料，無法估值。")
        return
    base_eps = price / pe if pd.notna(pe) and pe > 0 else price / 20
    pe_bear, pe_base, pe_bull = 14, 20, 28
    fair_bear = base_eps * pe_bear
    fair_base = base_eps * pe_base
    fair_bull = base_eps * pe_bull
    # ESG/fundamental adjustment
    adj = 1 + (fund_score - 60) / 500
    fair_base *= adj
    st.subheader("💎 企業估值中心")
    c1,c2,c3 = st.columns(3)
    c1.metric("保守價", f"{fair_bear:.2f}")
    c2.metric("合理價", f"{fair_base:.2f}")
    c3.metric("樂觀價", f"{fair_bull:.2f}")
    st.caption("估值模型：雲端簡化版 PE/EPS + 基本面調整。後續可擴充 DCF、FCFF、FCFE、EVA、EBO。")

def chart_panel(d, overlays):
    st.subheader("📊 K線與技術指標")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=d["Date"], open=d["Open"], high=d["High"], low=d["Low"], close=d["Close"], name="K線"))
    for ma in overlays:
        if ma in d.columns:
            fig.add_trace(go.Scatter(x=d["Date"], y=d[ma], mode="lines", name=ma))
    if "布林通道" in overlays:
        fig.add_trace(go.Scatter(x=d["Date"], y=d["BB_UP"], mode="lines", name="BB上軌"))
        fig.add_trace(go.Scatter(x=d["Date"], y=d["BB_DN"], mode="lines", name="BB下軌"))
    fig.update_layout(height=620, xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=45,b=10))
    st.plotly_chart(fig, use_container_width=True)

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
    h.metric("資料時間", q.get("time", ""))
    intra = q.get("intraday", pd.DataFrame())
    if isinstance(intra, pd.DataFrame) and not intra.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=intra["Time"], y=intra["Close"], mode="lines", name="1分鐘走勢"))
        fig.update_layout(title="今日 1分鐘走勢", height=320, margin=dict(l=10,r=10,t=45,b=10))
        st.plotly_chart(fig, use_container_width=True)
    st.caption("資料來源：Yahoo Finance / yfinance，可能為延遲或近即時資料，投資決策請以券商即時報價為準。")
    return q

def radar_card(symbol, period="1y"):
    df = fetch_price(symbol, period)
    if df.empty:
        return {"股票": stock_display_name(symbol), "AI分數": 0, "評級": "查無資料"}
    d = add_indicators(df)
    q = fetch_realtime(symbol)
    tech, _ = technical_score(d)
    chip, _ = chip_score(d)
    fund, _ = fundamental_score(symbol, q)
    esg, _ = esg_score(symbol)
    total, rating = ai_radar_score(tech, chip, fund, esg)
    return {
        "股票": stock_display_name(symbol), "AI分數": total, "評級": rating,
        "技術": tech, "籌碼": chip, "基本面": fund, "ESG": esg,
        "價格": np.nan if pd.isna(q.get("price")) else round(q.get("price"),2)
    }

@st.cache_data(show_spinner=False, ttl=300)
def radar_rank(symbols):
    rows = [radar_card(s) for s in symbols]
    df = pd.DataFrame(rows)
    if not df.empty and "AI分數" in df.columns:
        df = df.sort_values("AI分數", ascending=False)
    return df

st.title("📈 旗艦版 AI 股票平台 V27.5 Cloud Ultimate + AI Radar Pro")
st.caption("V27.5：即時行情 + AI Radar 排行榜 + 技術/籌碼/基本面/ESG 綜合評分 + 企業估值 + AI預測 + 手機雲端版")

with st.sidebar:
    st.header("查詢設定")
    raw = st.text_input("股票名稱 / 代碼", value="世界先進")
    symbol = clean_symbol(raw)
    st.success(symbol)
    period = st.radio("歷史期間", ["6mo","1y","2y","5y","10y"], index=2, horizontal=True)
    forecast_days = st.slider("AI預測天數", 7, 180, 30)
    overlays = st.multiselect("K線疊圖指標", ["MA5","MA10","MA20","MA60","MA120","MA240","布林通道"], default=["MA20","MA60","布林通道"])
    enable_forecast = st.checkbox("啟用AI預測", value=True)
    st.divider()
    st.subheader("AI Radar")
    enable_radar = st.checkbox("顯示AI Radar排行榜", value=True)
    custom_list = st.text_area("自訂雷達股票清單", value=",".join(WATCHLIST), height=90)
    if st.button("手動刷新資料"):
        fetch_realtime.clear()
        fetch_price.clear()
        radar_rank.clear()
        st.rerun()

display = stock_display_name(symbol)
st.info(f"目前查詢：{display}")

df = fetch_price(symbol, period)
if df.empty:
    st.error("查無資料，請確認股票名稱、代碼或網路連線。")
    st.stop()

d = add_indicators(df)
quote = realtime_panel(symbol)

tech, tech_notes = technical_score(d)
chip, chip_notes = chip_score(d)
fund, fund_notes = fundamental_score(symbol, quote)
esg, esg_notes = esg_score(symbol)
total, rating = ai_radar_score(tech, chip, fund, esg)

st.subheader("🔥 AI Radar Pro 綜合評分")
r1,r2,r3,r4,r5 = st.columns(5)
r1.metric("AI總分", f"{total}")
r2.metric("技術面", f"{tech}")
r3.metric("籌碼面", f"{chip}")
r4.metric("基本面", f"{fund}")
r5.metric("ESG", f"{esg}")
st.success(f"AI Radar 評級：{rating}")

with st.expander("AI Radar 判讀原因"):
    st.write("技術面：", "、".join(tech_notes))
    st.write("籌碼面：", "、".join(chip_notes))
    st.write("基本面：", "、".join(fund_notes))
    st.write("ESG：", "、".join(esg_notes))

chart_panel(d, overlays)

tab1, tab2, tab3, tab4 = st.tabs(["AI預測", "企業估值", "AI Radar排行榜", "資料表"])

with tab1:
    st.subheader("🤖 AI 股價預測")
    if enable_forecast:
        pred = xgb_predict(df, forecast_days)
        if pred is None or pred.empty:
            st.warning("資料不足或模型不可用，暫無法預測。")
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["Date"].tail(180), y=df["Close"].tail(180), mode="lines", name="歷史收盤"))
            fig.add_trace(go.Scatter(x=pred["Date"], y=pred["AI預測價"], mode="lines", name="AI預測"))
            fig.update_layout(height=430, margin=dict(l=10,r=10,t=45,b=10))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(pred.tail(20), use_container_width=True)
    else:
        st.info("AI預測未啟用。")

with tab2:
    valuation_panel(quote.get("price", np.nan), quote, fund)

with tab3:
    if enable_radar:
        syms = [clean_symbol(x.strip()) for x in custom_list.split(",") if x.strip()]
        rank_df = radar_rank(syms)
        st.dataframe(rank_df, use_container_width=True, hide_index=True)
        if not rank_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=rank_df["股票"], y=rank_df["AI分數"], name="AI分數"))
            fig.update_layout(title="AI Radar 排行榜", height=420, margin=dict(l=10,r=10,t=45,b=10))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("AI Radar 排行榜未啟用。")

with tab4:
    st.subheader("歷史資料與技術指標")
    st.dataframe(d.tail(120), use_container_width=True)
    csv = d.to_csv(index=False).encode("utf-8-sig")
    st.download_button("下載CSV", csv, file_name=f"{symbol}_V27_5_data.csv", mime="text/csv")

st.caption("免責聲明：本平台為研究與教學用途，非投資建議。即時行情可能延遲，請以券商與交易所資料為準。")
