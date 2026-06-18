
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re

st.set_page_config(page_title="AIStock V27.6 Full Ultimate", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container{padding-top:1rem;padding-left:1rem;padding-right:1rem;max-width:1550px}
[data-testid="stMetric"]{background:rgba(245,247,250,.9);border:1px solid #e5e7eb;border-radius:14px;padding:12px}
.stButton>button{width:100%;border-radius:12px;font-weight:700}
@media(max-width:768px){.block-container{padding-left:.55rem;padding-right:.55rem}h1{font-size:1.35rem!important}h2,h3{font-size:1.05rem!important}[data-testid="stMetricValue"]{font-size:1.05rem!important}}
</style>
""", unsafe_allow_html=True)

TW_STOCKS = {
    "台積電":"2330.TW","聯電":"2303.TW","世界先進":"5347.TWO","和椿":"6215.TWO","台光電":"2383.TW",
    "威剛":"3260.TWO","台達電":"2308.TW","鴻海":"2317.TW","聯發科":"2454.TW","廣達":"2382.TW",
    "緯創":"3231.TW","英業達":"2356.TW","華碩":"2357.TW","技嘉":"2376.TW","欣興":"3037.TW",
    "南亞科":"2408.TW","瑞昱":"2379.TW","力積電":"6770.TW","宏捷科":"8086.TWO","穩懋":"3105.TWO",
    "全新":"2455.TW","凌陽":"2401.TW","立隆電":"2472.TW","國巨":"2327.TW","華新科":"2492.TW",
    "日月光投控":"3711.TW","矽力":"6415.TW","創意":"3443.TW"
}
WATCHLIST = ["2330.TW","2303.TW","5347.TWO","6215.TWO","2383.TW","3260.TWO","2308.TW","2317.TW","2454.TW","2382.TW"]

def tw_now():
    return (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S 台灣時間")

def clean_symbol(x):
    s = str(x).strip()
    if s in TW_STOCKS: return TW_STOCKS[s]
    if re.fullmatch(r"\d{4}", s):
        return f"{s}.TWO" if s in ["5347","6215","3260","3105","8086"] else f"{s}.TW"
    return s.upper() if s else "5347.TWO"

def display_name(symbol):
    for k,v in TW_STOCKS.items():
        if v == symbol: return f"{k} / {symbol}"
    return symbol

def safe_float(x, default=np.nan):
    try:
        v = float(x)
        return v if np.isfinite(v) else default
    except Exception:
        return default

@st.cache_data(show_spinner=False, ttl=60)
def fetch_price(symbol, period="2y"):
    try:
        df = yf.download(symbol, period=period, interval="1d", auto_adjust=False, progress=False)
        if df is None or df.empty: return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df = df.reset_index()
        df["Date"] = pd.to_datetime(df["Date"])
        return df.dropna(subset=["Close"])
    except Exception:
        return pd.DataFrame()

@st.cache_data(show_spinner=False, ttl=20)
def fetch_realtime(symbol):
    q = {"price":np.nan,"prev":np.nan,"open":np.nan,"high":np.nan,"low":np.nan,"volume":np.nan,"market_cap":np.nan,"pe":np.nan,"div_yield":np.nan,"time":tw_now(),"intraday":pd.DataFrame()}
    try:
        t = yf.Ticker(symbol)
        try: fast = t.fast_info
        except Exception: fast = {}
        def g(*keys):
            for k in keys:
                try:
                    val = fast.get(k) if hasattr(fast, "get") else getattr(fast, k)
                    if val is not None: return safe_float(val)
                except Exception: pass
            return np.nan
        q["price"]=g("last_price","lastPrice")
        q["prev"]=g("previous_close","previousClose")
        q["open"]=g("open")
        q["high"]=g("day_high","dayHigh")
        q["low"]=g("day_low","dayLow")
        q["volume"]=g("last_volume","lastVolume","volume")
        q["market_cap"]=g("market_cap","marketCap")
        try:
            info = t.info or {}
            q["pe"]=safe_float(info.get("trailingPE"))
            q["div_yield"]=safe_float(info.get("dividendYield"))
            if pd.isna(q["price"]): q["price"]=safe_float(info.get("currentPrice", info.get("regularMarketPrice")))
            if pd.isna(q["prev"]): q["prev"]=safe_float(info.get("previousClose"))
            if pd.isna(q["market_cap"]): q["market_cap"]=safe_float(info.get("marketCap"))
        except Exception: pass
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
        except Exception: pass
    except Exception: pass
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
    d["BB_UP"] = mid + 2 * std
    d["BB_DN"] = mid - 2 * std
    d["VOL_MA20"] = d["Volume"].rolling(20).mean()
    d["RET20"] = d["Close"].pct_change(20)
    d["RET60"] = d["Close"].pct_change(60)
    return d

def signal_status(d):
    names = ["黃金交叉","死亡交叉","MACD翻紅","KD黃金交叉","RSI突破50","布林突破上軌","均線多頭排列","爆量突破","創20日新高"]
    if d is None or d.empty or len(d) < 80: return {n:False for n in names}
    c, p = d.iloc[-1], d.iloc[-2]
    def v(row, col):
        try: return float(row.get(col, np.nan))
        except Exception: return np.nan
    close = v(c, "Close")
    return {
        "黃金交叉": v(p,"MA5") <= v(p,"MA20") and v(c,"MA5") > v(c,"MA20"),
        "死亡交叉": v(p,"MA5") >= v(p,"MA20") and v(c,"MA5") < v(c,"MA20"),
        "MACD翻紅": v(p,"MACD") <= v(p,"MACD_SIGNAL") and v(c,"MACD") > v(c,"MACD_SIGNAL"),
        "KD黃金交叉": v(p,"K") <= v(p,"D") and v(c,"K") > v(c,"D"),
        "RSI突破50": v(p,"RSI") < 50 and v(c,"RSI") >= 50,
        "布林突破上軌": close > v(c,"BB_UP"),
        "均線多頭排列": v(c,"MA5") > v(c,"MA20") > v(c,"MA60"),
        "爆量突破": close > v(c,"MA20") and v(c,"Volume") > v(c,"VOL_MA20") * 1.5,
        "創20日新高": close >= d["Close"].tail(20).max()
    }

def technical_score(d):
    if d.empty or len(d)<80: return 50, ["資料不足"]
    x = d.iloc[-1]; score=50; notes=[]
    if x["Close"] > x.get("MA20", np.inf): score += 8; notes.append("站上月線")
    if x.get("MA20",0) > x.get("MA60",1e9): score += 8; notes.append("中期均線偏多")
    if x.get("MA5",0) > x.get("MA20",1e9): score += 7; notes.append("短線動能偏強")
    if x.get("MACD",0) > x.get("MACD_SIGNAL",1e9): score += 8; notes.append("MACD多方")
    if 50 <= x.get("RSI",0) <= 75: score += 7; notes.append("RSI健康偏強")
    if x.get("Volume",0) > x.get("VOL_MA20",1e18): score += 5; notes.append("量能放大")
    if x.get("RET20",0) > 0: score += 4; notes.append("20日報酬為正")
    return int(np.clip(score,0,100)), notes

def chip_score(d):
    if d.empty or len(d)<30: return 50, ["籌碼以量價估算"]
    x=d.iloc[-1]; score=50; notes=["籌碼以量價估算"]
    if x.get("Volume",0)>x.get("VOL_MA20",1e18) and x.get("Close",0)>x.get("MA20",1e18): score+=18; notes.append("放量站上月線")
    if x.get("RET20",0)>0: score+=8; notes.append("近20日資金動能偏多")
    if x.get("RET60",0)>0: score+=6; notes.append("近60日趨勢偏多")
    return int(np.clip(score,0,100)), notes

def fundamental_score(symbol, q):
    score=55; notes=[]
    pe=q.get("pe", np.nan); dy=q.get("div_yield", np.nan)
    if pd.notna(pe):
        if 0<pe<15: score+=12; notes.append("本益比偏低")
        elif 15<=pe<=30: score+=8; notes.append("本益比合理")
        elif pe>50: score-=8; notes.append("本益比偏高")
    else: notes.append("本益比資料不足")
    if pd.notna(dy) and dy>0.03: score+=6; notes.append("殖利率具吸引力")
    return int(np.clip(score,0,100)), notes

def esg_score(symbol):
    if symbol in ["2330.TW","2308.TW","3711.TW"]: return 78, ["大型企業ESG估分較高"]
    if symbol.endswith(".TWO"): return 64, ["上櫃公司產業估分"]
    return 68, ["市場平均ESG估分"]

def rating(total):
    if total>=85: return "★★★★★ 強力買進觀察"
    if total>=75: return "★★★★ 買進觀察"
    if total>=60: return "★★★ 中立觀察"
    if total>=45: return "★★ 減碼觀察"
    return "★ 避開觀察"

def predict_ai(df, days):
    try:
        from sklearn.ensemble import ExtraTreesRegressor
        d=add_indicators(df).dropna()
        if len(d)<120: return pd.DataFrame()
        features=["Close","Volume","MA5","MA20","MA60","MACD","RSI","K","D","RET20","RET60"]
        X=d[features].values[:-1]; y=d["Close"].shift(-1).dropna().values
        model=ExtraTreesRegressor(n_estimators=130, random_state=42, min_samples_leaf=3)
        model.fit(X,y)
        last=d[features].iloc[-1:].values; cur=float(d["Close"].iloc[-1]); preds=[]
        for _ in range(days):
            p=float(model.predict(last)[0]); p=max(min(p,cur*1.15),cur*0.85); preds.append(p); cur=p
        dates=pd.date_range(df["Date"].iloc[-1]+pd.Timedelta(days=1), periods=days, freq="B")
        return pd.DataFrame({"Date":dates,"AI預測價":preds})
    except Exception: return pd.DataFrame()

def realtime_panel(symbol):
    q=fetch_realtime(symbol); price=q["price"]; prev=q["prev"]
    chg=price-prev if pd.notna(price) and pd.notna(prev) else np.nan
    pct=chg/prev if pd.notna(chg) and prev else np.nan
    st.subheader("⚡ 即時行情中心")
    a,b,c,d=st.columns(4)
    a.metric("即時/近即時價格","N/A" if pd.isna(price) else f"{price:.2f}",None if pd.isna(chg) else f"{chg:+.2f}")
    b.metric("漲跌幅","N/A" if pd.isna(pct) else f"{pct:+.2%}")
    c.metric("今日最高","N/A" if pd.isna(q["high"]) else f"{q['high']:.2f}")
    d.metric("今日最低","N/A" if pd.isna(q["low"]) else f"{q['low']:.2f}")
    e,f,g,h=st.columns(4)
    e.metric("今日開盤","N/A" if pd.isna(q["open"]) else f"{q['open']:.2f}")
    f.metric("昨收","N/A" if pd.isna(prev) else f"{prev:.2f}")
    g.metric("成交量","N/A" if pd.isna(q["volume"]) else f"{q['volume']:,.0f}")
    h.metric("資料時間", q["time"].replace(" 台灣時間",""))
    st.caption(f"🕒 資料更新時間：{q['time']}")
    if isinstance(q["intraday"],pd.DataFrame) and not q["intraday"].empty:
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=q["intraday"]["Time"],y=q["intraday"]["Close"],mode="lines",name="1分鐘走勢"))
        fig.update_layout(title="今日 1分鐘走勢",height=320,margin=dict(l=10,r=10,t=45,b=10))
        st.plotly_chart(fig,use_container_width=True)
    return q

def signal_panel(d, selected):
    st.subheader("🎯 技術訊號雷達")
    sig=signal_status(d); hit=0; cols=st.columns(3)
    for i,name in enumerate(selected):
        with cols[i%3]:
            if sig.get(name,False): st.success(f"✅ {name}"); hit+=1
            else: st.info(f"— {name}")
    if hit>=3: st.success(f"技術訊號偏強：符合 {hit} 項")
    elif hit>=1: st.warning(f"有部分轉強訊號：符合 {hit} 項")
    else: st.info("目前尚未觸發主要買進技術訊號。")
    return sig

def chart_panel(d, overlays):
    st.subheader("📊 K線與技術指標")
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=d["Date"],open=d["Open"],high=d["High"],low=d["Low"],close=d["Close"],name="K線"))
    for ma in overlays:
        if ma in d.columns: fig.add_trace(go.Scatter(x=d["Date"],y=d[ma],mode="lines",name=ma))
    if "布林通道" in overlays:
        fig.add_trace(go.Scatter(x=d["Date"],y=d["BB_UP"],mode="lines",name="BB上軌"))
        fig.add_trace(go.Scatter(x=d["Date"],y=d["BB_DN"],mode="lines",name="BB下軌"))
    fig.update_layout(height=620,xaxis_rangeslider_visible=False,margin=dict(l=10,r=10,t=45,b=10))
    st.plotly_chart(fig,use_container_width=True)

def valuation_panel(price, q, fund):
    st.subheader("💎 企業估值中心")
    if pd.isna(price): st.warning("缺少價格資料"); return
    pe=q.get("pe",np.nan); eps=price/pe if pd.notna(pe) and pe>0 else price/20
    bear,base,bull=eps*14,eps*20*(1+(fund-60)/500),eps*28
    a,b,c=st.columns(3); a.metric("保守價",f"{bear:.2f}"); b.metric("合理價",f"{base:.2f}"); c.metric("樂觀價",f"{bull:.2f}")

def radar_row(symbol):
    df=fetch_price(symbol,"1y")
    if df.empty: return {"股票":display_name(symbol),"AI分數":0,"評級":"查無資料"}
    d=add_indicators(df); q=fetch_realtime(symbol)
    te,_=technical_score(d); ch,_=chip_score(d); fu,_=fundamental_score(symbol,q); es,_=esg_score(symbol)
    total=round(te*.30+ch*.25+fu*.25+es*.20,1)
    return {"股票":display_name(symbol),"AI分數":total,"評級":rating(total),"技術":te,"籌碼":ch,"基本面":fu,"ESG":es,"價格":None if pd.isna(q["price"]) else round(q["price"],2)}

@st.cache_data(show_spinner=False, ttl=300)
def radar_rank(symbols):
    df=pd.DataFrame([radar_row(s) for s in symbols])
    return df.sort_values("AI分數",ascending=False) if not df.empty else df

st.title("📈 旗艦版 AI 股票平台 V27.6 Full Ultimate + AI Radar Pro")
st.caption("V27.6：完整版｜即時行情 + 黃金交叉/死亡交叉 + 技術訊號雷達 + AI Radar + 企業估值 + AI預測 + 台灣時間 + 手機雲端版")

with st.sidebar:
    st.header("查詢設定")
    raw=st.text_input("股票名稱 / 代碼",value="世界先進")
    symbol=clean_symbol(raw); st.success(symbol)
    period=st.radio("歷史期間",["6mo","1y","2y","5y","10y"],index=2,horizontal=True)
    forecast_days=st.slider("AI預測天數",7,180,30)
    overlays=st.multiselect("K線疊圖指標",["MA5","MA10","MA20","MA60","MA120","MA240","布林通道"],default=["MA20","MA60","布林通道"])
    selected_signals=st.multiselect("技術訊號篩選",["黃金交叉","死亡交叉","MACD翻紅","KD黃金交叉","RSI突破50","布林突破上軌","均線多頭排列","爆量突破","創20日新高"],default=["黃金交叉","MACD翻紅","KD黃金交叉","RSI突破50","均線多頭排列","爆量突破"])
    enable_forecast=st.checkbox("啟用AI預測",value=True)
    st.divider(); st.subheader("AI Radar")
    enable_radar=st.checkbox("顯示AI Radar排行榜",value=True)
    custom_list=st.text_area("自訂雷達股票清單",value=",".join(WATCHLIST),height=90)
    if st.button("手動刷新資料"):
        fetch_price.clear(); fetch_realtime.clear(); radar_rank.clear(); st.rerun()

st.info(f"目前查詢：{display_name(symbol)}")
df=fetch_price(symbol,period)
if df.empty:
    st.error("查無資料，請確認股票名稱、代碼或網路連線。"); st.stop()
d=add_indicators(df)
q=realtime_panel(symbol)
te,te_notes=technical_score(d); ch,ch_notes=chip_score(d); fu,fu_notes=fundamental_score(symbol,q); es,es_notes=esg_score(symbol)
total=round(te*.30+ch*.25+fu*.25+es*.20,1)

st.subheader("🔥 AI Radar Pro 綜合評分")
c1,c2,c3,c4,c5=st.columns(5)
c1.metric("AI總分",f"{total}"); c2.metric("技術面",f"{te}"); c3.metric("籌碼面",f"{ch}"); c4.metric("基本面",f"{fu}"); c5.metric("ESG",f"{es}")
st.success(f"AI Radar 評級：{rating(total)}")
with st.expander("AI Radar 判讀原因"):
    st.write("技術面：","、".join(te_notes)); st.write("籌碼面：","、".join(ch_notes)); st.write("基本面：","、".join(fu_notes)); st.write("ESG：","、".join(es_notes))

signal_panel(d, selected_signals)
chart_panel(d, overlays)

tab1,tab2,tab3,tab4=st.tabs(["AI預測","企業估值","AI Radar排行榜","資料表"])
with tab1:
    st.subheader("🤖 AI 股價預測")
    if enable_forecast:
        pred=predict_ai(df,forecast_days)
        if pred.empty: st.warning("資料不足或模型不可用，暫無法預測。")
        else:
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=df["Date"].tail(180),y=df["Close"].tail(180),mode="lines",name="歷史收盤"))
            fig.add_trace(go.Scatter(x=pred["Date"],y=pred["AI預測價"],mode="lines",name="AI預測"))
            fig.update_layout(height=430,margin=dict(l=10,r=10,t=45,b=10))
            st.plotly_chart(fig,use_container_width=True); st.dataframe(pred.tail(20),use_container_width=True)
with tab2:
    valuation_panel(q["price"],q,fu)
with tab3:
    if enable_radar:
        syms=[clean_symbol(x.strip()) for x in custom_list.split(",") if x.strip()]
        rd=radar_rank(syms); st.dataframe(rd,use_container_width=True,hide_index=True)
        if not rd.empty:
            fig=go.Figure(); fig.add_trace(go.Bar(x=rd["股票"],y=rd["AI分數"],name="AI分數"))
            fig.update_layout(title="AI Radar 排行榜",height=420,margin=dict(l=10,r=10,t=45,b=10))
            st.plotly_chart(fig,use_container_width=True)
with tab4:
    st.subheader("歷史資料與技術指標")
    st.dataframe(d.tail(120),use_container_width=True)
    st.download_button("下載CSV",d.to_csv(index=False).encode("utf-8-sig"),file_name=f"{symbol}_V27_6_data.csv",mime="text/csv")

st.caption("免責聲明：本平台為研究與教學用途，非投資建議。即時行情可能延遲，請以券商與交易所資料為準。")
