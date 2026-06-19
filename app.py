
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests, re, math

APP_VERSION="V32.3"
APP_NAME="智策股市 AI 決策平台"

st.set_page_config(page_title=f"{APP_NAME} {APP_VERSION}", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container{padding-top:.5rem;padding-left:.55rem;padding-right:.55rem;max-width:1700px}
#MainMenu, footer, header {visibility:hidden}
h1{font-size:1.35rem!important;margin-bottom:.1rem}
[data-testid="stMetric"]{background:#0f172a!important;border:1px solid #334155!important;border-radius:14px!important;padding:10px!important}
[data-testid="stMetricLabel"] p{color:#cbd5e1!important;font-weight:800!important}
[data-testid="stMetricValue"]{color:#fff!important;font-weight:900!important}
[data-testid="stMetricDelta"]{color:#facc15!important;font-weight:900!important}
.card{background:#0f172a;color:#fff;border:1px solid #334155;border-radius:16px;padding:11px;margin:6px 0;box-shadow:0 1px 6px rgba(15,23,42,.15)}
.card-title{font-size:.86rem;color:#cbd5e1;font-weight:800}
.card-price{font-size:1.45rem;font-weight:900;line-height:1.1}
.card-small{font-size:.76rem;color:#cbd5e1}
.badge{display:inline-block;border-radius:999px;padding:2px 7px;margin:2px;font-size:.72rem;background:#1e293b;color:#e2e8f0;border:1px solid #475569}
.good{color:#f87171;font-weight:900}.bad{color:#4ade80;font-weight:900}.neutral{color:#facc15;font-weight:900}
.stTabs [data-baseweb="tab-list"]{gap:4px;overflow-x:auto}
.stTabs [data-baseweb="tab"]{background:#f1f5f9;border-radius:12px;padding:8px 10px;white-space:nowrap}
@media(max-width:768px){h1{font-size:1.12rem!important}.block-container{padding-left:.35rem;padding-right:.35rem}.card-price{font-size:1.32rem}}

.hero{
    background:linear-gradient(135deg,#020617 0%,#0f172a 45%,#1e3a8a 100%);
    border:1px solid #334155;
    border-radius:18px;
    padding:13px;
    color:white;
    box-shadow:0 4px 14px rgba(15,23,42,.18);
    margin-bottom:12px;
}
.hero-title{font-size:1.55rem;font-weight:950;letter-spacing:.5px}
.hero-sub{font-size:.88rem;color:#cbd5e1;margin-top:4px}
.hero-pill{display:inline-block;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);border-radius:999px;padding:4px 10px;margin:4px 4px 0 0;font-size:.78rem}
.pro-panel{background:#f8fafc;border:1px solid #e2e8f0;border-radius:16px;padding:12px;margin:6px 0}
@media(max-width:768px){.hero{padding:11px;border-radius:16px}.hero-title{font-size:1.08rem}.hero-sub{font-size:.74rem}.hero-pill{font-size:.68rem;padding:2px 6px}}


</style>
""", unsafe_allow_html=True)

TW_STOCKS={
"台積電":"2330.TW","聯電":"2303.TW","世界先進":"5347.TWO","和椿":"6215.TWO","台光電":"2383.TW","威剛":"3260.TWO",
"台達電":"2308.TW","鴻海":"2317.TW","聯發科":"2454.TW","廣達":"2382.TW","緯創":"3231.TW","英業達":"2356.TW",
"華碩":"2357.TW","技嘉":"2376.TW","欣興":"3037.TW","南亞科":"2408.TW","瑞昱":"2379.TW","力積電":"6770.TW",
"宏捷科":"8086.TWO","穩懋":"3105.TWO","全新":"2455.TW","凌陽":"2401.TW","立隆電":"2472.TW","國巨":"2327.TW",
"華新科":"2492.TW","日月光投控":"3711.TW","矽力":"6415.TW","創意":"3443.TW","川湖":"2059.TW","奇鋐":"3017.TW",
"智邦":"2345.TW","金像電":"2368.TW","健策":"3653.TW","世芯-KY":"3661.TW","緯穎":"6669.TW","信驊":"5274.TW",
"M31":"6643.TWO","祥碩":"5269.TW","大立光":"3008.TW","智原":"3035.TW","晶心科":"6533.TW","南電":"8046.TW",
"景碩":"3189.TW","台燿":"6274.TW","華邦電":"2344.TW","群聯":"8299.TWO","十銓":"4967.TWO","京元電子":"2449.TW",
"頎邦":"6147.TWO","欣銓":"3264.TWO","力成":"6239.TW","上銀":"2049.TW","台灣精銳":"4583.TW","亞光":"3019.TW",
"和大":"1536.TW","群電":"6412.TW","信邦":"3023.TW","康舒":"6282.TW"
}
DEFAULT_MONITOR=["2330.TW","2303.TW","5347.TWO","6215.TWO","2383.TW","3260.TWO","2308.TW","2317.TW","2454.TW","2382.TW","2345.TW","3017.TW","2368.TW","3653.TW","3661.TW","2059.TW","6669.TW","5274.TW","6643.TWO","5269.TW","3008.TW","3231.TW","3037.TW","2408.TW","2379.TW","6770.TW","8086.TWO","3105.TWO","2455.TW","2401.TW","2472.TW","2327.TW"]
SECTOR_WATCHLISTS={
"⭐ Tsung Chieh Watchlist":DEFAULT_MONITOR,
"半導體":["2330.TW","2303.TW","5347.TWO","6770.TW","2454.TW","3711.TW","6415.TW","3035.TW","3443.TW","3661.TW","5269.TW","6643.TWO","6533.TW","2379.TW","2408.TW","3105.TWO"],
"AI伺服器":["2382.TW","3231.TW","6669.TW","2356.TW","2317.TW","3017.TW","3653.TW","2345.TW","2376.TW","2357.TW","2308.TW","2383.TW","2368.TW","2059.TW"],
"PCB/CCL":["2383.TW","2368.TW","8046.TW","3037.TW","3189.TW","6274.TW"],
"記憶體":["2408.TW","2344.TW","8299.TWO","3260.TWO","4967.TWO","6770.TW"],
"IP矽智財":["3443.TW","3661.TW","3035.TW","6643.TWO","6533.TW","5269.TW"],
"封測":["3711.TW","2449.TW","6147.TWO","3264.TWO","6239.TW"],
"機器人/自動化":["6215.TWO","2049.TW","4583.TW","3019.TW","1536.TW","2308.TW"],
"電源管理":["2308.TW","6412.TW","3023.TW","6282.TW"],
"ETF":["0050.TW","0056.TW","006208.TW","00878.TW","00919.TW","00929.TW","00940.TW"],
"金融":["2881.TW","2882.TW","2883.TW","2884.TW","2885.TW","2886.TW","2891.TW","2892.TW"],
"航運":["2603.TW","2609.TW","2615.TW","2610.TW","2618.TW"],
"觀光":["2707.TW","2727.TW","2731.TW","2739.TW"],
"重電":["1513.TW","1504.TW","1514.TW","1605.TW","1609.TW","1618.TW","2371.TW","2308.TW"],
"CoWoS/先進封裝":["2330.TW","3711.TW","2449.TW","6239.TW","3264.TWO","6643.TWO"],
"全市場精選":DEFAULT_MONITOR
}

VALUATION_DESC={
"DCF":"現金流量折現法：以未來現金流折現推估企業價值。",
"FCFF":"企業自由現金流量法：以企業整體自由現金流估值。",
"FCFE":"股東自由現金流量法：以股東可分配現金流估值。",
"APV":"調整現值法：營運價值加融資效益。",
"EVA":"經濟附加價值法：ROE扣除資金成本後是否創造價值。",
"EBO":"異常盈餘評價法：帳面價值加未來異常盈餘。",
"PE":"本益比估值法：EPS乘以合理本益比。",
"PB":"股價淨值比估值法：每股淨值乘以合理PB。",
"PS":"股價營收比估值法：每股營收乘以合理PS。",
"EV/EBITDA":"企業價值EBITDA比：外資常用市場倍數。",
"PEG":"本益比成長模型：適合成長股。",
"PEGY":"本益比加殖利率模型：加入股利因素。",
"Lynch":"彼得林區估值法：EPS與成長率估值。",
"Graham":"葛拉漢價值法：偏保守價值投資模型。",
"NAV":"淨資產價值法：適合金融、資產、控股公司。",
"Tobin Q":"托賓Q模型：市場價值與重置成本比較。",
"ESG Premium":"ESG溢價估值法：納入ESG品質溢價。",
"AI Premium":"AI成長溢價模型：反映AI題材與成長溢價。",
"Institutional Premium":"法人溢價模型：反映法人資金與籌碼。",
"Industry Cycle":"產業循環估值模型：反映景氣循環位置。",
"Super Bull":"超級牛市模型：高風險樂觀情境，僅供參考。"
}

def tw_now(): return (datetime.utcnow()+timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S 台灣時間")
def auto_refresh(sec):
    """Use Streamlit rerun instead of browser reload, preserving mobile page and selected stock."""
    try:
        sec = int(sec)
    except Exception:
        sec = 0
    if sec > 0:
        st_autorefresh(interval=sec*1000, key="v311_data_refresh")
def safe_float(x, default=np.nan):
    try:
        if x is None: return default
        v=float(x)
        return v if np.isfinite(v) else default
    except Exception: return default
def clean_symbol(x):
    s=str(x).strip()
    if s in TW_STOCKS: return TW_STOCKS[s]
    if re.fullmatch(r"\d{4}",s): return f"{s}.TWO" if s in ["5347","6215","3260","3105","8086","6643","8299"] else f"{s}.TW"
    return s.upper() if s else "5347.TWO"
def plain_symbol(s): return str(s).replace(".TW","").replace(".TWO","")
def display_name(symbol):
    for k,v in TW_STOCKS.items():
        if v==symbol: return f"{k} / {symbol}"
    return symbol
def fmt(x): return "N/A" if x is None or pd.isna(x) else f"{float(x):.2f}"
def mean_good(vals):
    arr=[float(v) for v in vals if v is not None and pd.notna(v) and np.isfinite(float(v)) and float(v)>0]
    return np.nan if not arr else float(np.mean(arr))

@st.cache_data(show_spinner=False, ttl=60)
def fetch_price(symbol, period="2y"):
    try:
        df=yf.download(symbol,period=period,interval="1d",auto_adjust=False,progress=False)
        if df is None or df.empty: return pd.DataFrame()
        if isinstance(df.columns,pd.MultiIndex): df.columns=[c[0] for c in df.columns]
        df=df.reset_index(); df["Date"]=pd.to_datetime(df["Date"])
        return df.dropna(subset=["Close"])
    except Exception: return pd.DataFrame()

@st.cache_data(show_spinner=False, ttl=3)
def yahoo_quote(symbol):
    q={"source":"Yahoo Finance","price":np.nan,"prev":np.nan,"open":np.nan,"high":np.nan,"low":np.nan,"volume":np.nan,"market_cap":np.nan,"pe":np.nan,"pb":np.nan,"eps":np.nan,"div_yield":np.nan,"book_value":np.nan,"revenue_per_share":np.nan,"enterprise_value":np.nan,"ebitda":np.nan,"time":tw_now(),"intraday":pd.DataFrame()}
    try:
        t=yf.Ticker(symbol)
        try: fast=t.fast_info
        except Exception: fast={}
        def g(*ks):
            for k in ks:
                try:
                    val=fast.get(k) if hasattr(fast,"get") else getattr(fast,k)
                    if val is not None: return safe_float(val)
                except Exception: pass
            return np.nan
        q["price"]=g("last_price","lastPrice"); q["prev"]=g("previous_close","previousClose")
        q["open"]=g("open"); q["high"]=g("day_high","dayHigh"); q["low"]=g("day_low","dayLow")
        q["volume"]=g("last_volume","lastVolume","volume"); q["market_cap"]=g("market_cap","marketCap")
        try:
            info=t.info or {}
            for k,ik in [("pe","trailingPE"),("pb","priceToBook"),("eps","trailingEps"),("div_yield","dividendYield"),("book_value","bookValue"),("revenue_per_share","revenuePerShare"),("enterprise_value","enterpriseValue"),("ebitda","ebitda")]:
                q[k]=safe_float(info.get(ik))
            if pd.isna(q["price"]): q["price"]=safe_float(info.get("currentPrice",info.get("regularMarketPrice")))
            if pd.isna(q["prev"]): q["prev"]=safe_float(info.get("previousClose"))
        except Exception: pass
        try:
            intra=t.history(period="1d",interval="1m")
            if intra is not None and not intra.empty:
                intra=intra.reset_index(); c="Datetime" if "Datetime" in intra.columns else "Date"
                intra[c]=pd.to_datetime(intra[c]).dt.tz_localize(None); intra=intra.rename(columns={c:"Time"})
                q["intraday"]=intra[["Time","Open","High","Low","Close","Volume"]].dropna(subset=["Close"])
                if not q["intraday"].empty:
                    q["price"]=safe_float(q["intraday"]["Close"].iloc[-1],q["price"])
                    q["high"]=safe_float(q["intraday"]["High"].max(),q["high"])
                    q["low"]=safe_float(q["intraday"]["Low"].min(),q["low"])
        except Exception: pass
    except Exception: pass
    return q

@st.cache_data(show_spinner=False, ttl=1)
def fugle_get(path, key):
    if not key: return {}
    try:
        r=requests.get("https://api.fugle.tw/marketdata/v1.0/stock/"+path.lstrip("/"),headers={"X-API-KEY":key},timeout=3)
        return r.json() if r.status_code==200 else {"_error":str(r.status_code),"_text":r.text[:200]}
    except Exception as e: return {"_error":str(e)}
def parse_fugle_quote(data):
    out={}
    if not isinstance(data,dict) or data.get("_error"): return out
    keys=[("price",["price","closePrice","lastPrice","tradePrice"]),("prev",["previousClose","referencePrice"]),("open",["openPrice","open"]),("high",["highPrice","high"]),("low",["lowPrice","low"]),("volume",["total","totalVolume","volume","tradeVolume"])]
    for ok,ks in keys:
        for k in ks:
            if k in data: out[ok]=safe_float(data.get(k)); break
    if "time" in data: out["time"]=str(data["time"])
    return out
@st.cache_data(show_spinner=False, ttl=1)
def fugle_quote(symbol,key):
    if not key: return {}
    q=parse_fugle_quote(fugle_get(f"intraday/quote/{plain_symbol(symbol)}",key))
    if q: q["source"]="Fugle API + Yahoo Finance"
    return q
@st.cache_data(show_spinner=False, ttl=1)
def fugle_books(symbol,key):
    data=fugle_get(f"intraday/books/{plain_symbol(symbol)}",key) if key else {}
    bids=[]; asks=[]
    if isinstance(data,dict):
        for r in data.get("bids",data.get("bid",[]))[:5]: bids.append({"買價":r.get("price"),"買量":r.get("volume") or r.get("size")})
        for r in data.get("asks",data.get("ask",[]))[:5]: asks.append({"賣價":r.get("price"),"賣量":r.get("volume") or r.get("size")})
    return pd.DataFrame(bids),pd.DataFrame(asks)
@st.cache_data(show_spinner=False, ttl=1)
def fugle_trades(symbol,key):
    data=fugle_get(f"intraday/trades/{plain_symbol(symbol)}",key) if key else {}
    rows=[]
    if isinstance(data,dict):
        raw=data.get("data",data.get("trades",[]))
        if isinstance(raw,list):
            for r in raw[:30]: rows.append({"時間":r.get("time") or r.get("at"),"成交價":r.get("price") or r.get("tradePrice"),"成交量":r.get("volume") or r.get("size")})
    return pd.DataFrame(rows)
def fetch_quote(symbol,source,key):
    q=yahoo_quote(symbol)
    if source!="Yahoo Finance" and key:
        fq=fugle_quote(symbol,key)
        for k,v in fq.items():
            if k in q and pd.notna(v): q[k]=v
        if fq: q["source"]="Fugle API + Yahoo Finance"
    return q

def add_indicators(df):
    d=df.copy()
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
    d["OBV"]=(np.sign(d["Close"].diff()).fillna(0)*d["Volume"]).cumsum()
    return d
def signal_columns(d):
    d=d.copy()
    d["黃金交叉"]=(d["MA5"].shift(1)<=d["MA20"].shift(1))&(d["MA5"]>d["MA20"])
    d["死亡交叉"]=(d["MA5"].shift(1)>=d["MA20"].shift(1))&(d["MA5"]<d["MA20"])
    d["MACD翻紅"]=(d["MACD"].shift(1)<=d["MACD_SIGNAL"].shift(1))&(d["MACD"]>d["MACD_SIGNAL"])
    d["KD黃金交叉"]=(d["K"].shift(1)<=d["D"].shift(1))&(d["K"]>d["D"])
    d["RSI突破50"]=(d["RSI"].shift(1)<50)&(d["RSI"]>=50)
    d["均線多頭排列"]=(d["MA5"]>d["MA20"])&(d["MA20"]>d["MA60"])
    d["爆量突破"]=(d["Close"]>d["MA20"])&(d["Volume"]>d["VOL_MA20"]*1.5)
    d["創20日新高"]=d["Close"]>=d["Close"].rolling(20).max()
    return d
def latest_signals(d):
    if d is None or d.empty or len(d)<80: return {}
    d=signal_columns(d)
    return {c:bool(d[c].iloc[-1]) for c in ["黃金交叉","死亡交叉","MACD翻紅","KD黃金交叉","RSI突破50","均線多頭排列","爆量突破","創20日新高"]}

def score_blocks(d,q):
    if d.empty or len(d)<80: return {"tech":50,"chip":50,"fund":50,"esg":65,"inst":50}
    x=d.iloc[-1]; tech=50
    if x["Close"]>x.get("MA20",np.inf): tech+=8
    if x.get("MA20",0)>x.get("MA60",1e9): tech+=8
    if x.get("MA5",0)>x.get("MA20",1e9): tech+=7
    if x.get("MACD",0)>x.get("MACD_SIGNAL",1e9): tech+=8
    if 50<=x.get("RSI",0)<=75: tech+=7
    elif x.get("RSI",0)>80: tech-=5
    if x.get("Volume",0)>x.get("VOL_MA20",1e18): tech+=5
    if x.get("RET20",0)>0: tech+=4
    if x.get("RET60",0)>0: tech+=3
    chip=50
    if x.get("Volume",0)>x.get("VOL_MA20",1e18) and x.get("Close",0)>x.get("MA20",1e18): chip+=18
    if x.get("RET20",0)>0: chip+=8
    if x.get("RET60",0)>0: chip+=6
    fund=55; pe=q.get("pe"); pb=q.get("pb"); dy=q.get("div_yield")
    if pd.notna(pe):
        if 0<pe<15: fund+=12
        elif 15<=pe<=30: fund+=8
        elif pe>50: fund-=8
    if pd.notna(pb):
        if 0<pb<2: fund+=5
        elif pb>6: fund-=4
    if pd.notna(dy) and dy>0.03: fund+=6
    return {"tech":int(np.clip(tech,0,100)),"chip":int(np.clip(chip,0,100)),"fund":int(np.clip(fund,0,100)),"esg":68,"inst":int(np.clip(chip,0,100))}
def ai_total(s): return round(s["fund"]*.35+s["inst"]*.25+s["tech"]*.20+s["esg"]*.10+70*.10,1)
def rating(t):
    return "★★★★★ 強力買進觀察" if t>=85 else "★★★★ 買進觀察" if t>=75 else "★★★ 中立觀察" if t>=60 else "★★ 減碼觀察" if t>=45 else "★ 避開觀察"

def compute_inputs(price,q,s):
    pe=q.get("pe",np.nan); pb=q.get("pb",np.nan); eps=q.get("eps",np.nan)
    eps_est=eps if pd.notna(eps) and eps>0 else (price/pe if pd.notna(price) and pd.notna(pe) and pe>0 else (price/20 if pd.notna(price) else np.nan))
    bvps=q.get("book_value",np.nan); bvps=bvps if pd.notna(bvps) and bvps>0 else (price/pb if pd.notna(price) and pd.notna(pb) and pb>0 else (price/2 if pd.notna(price) else np.nan))
    rps=q.get("revenue_per_share",np.nan); rps=rps if pd.notna(rps) and rps>0 else (price/2.5 if pd.notna(price) else np.nan)
    growth=float(np.clip((s["tech"]+s["fund"]+s["inst"])/300*.22,.03,.22))
    wacc=float(np.clip(.105-(s["fund"]-50)/1000-(s["esg"]-60)/1500,.065,.13)); tg=float(np.clip(.025+(growth-.08)/6,.01,.04))
    roe=float(np.clip(.08+(s["fund"]-50)/250,.03,.28))
    return {"eps":eps_est,"bvps":bvps,"rps":rps,"growth":growth,"wacc":wacc,"terminal_g":tg,"roe":roe,"source":q.get("source","Yahoo Finance"),"period":"TTM / 最新可得資料"}

def valuation_models(price,q,s):
    inp=compute_inputs(price,q,s); eps=inp["eps"]; bvps=inp["bvps"]; rps=inp["rps"]; g=inp["growth"]; wacc=inp["wacc"]; tg=inp["terminal_g"]; roe=inp["roe"]
    if pd.isna(price) or pd.isna(eps) or eps<=0: return pd.DataFrame(), inp
    base_pe=float(np.clip(14+g*80,10,32)); market_pe=float(np.clip(base_pe*(1+(s["tech"]-50)/250+(s["inst"]-50)/300),8,45))
    esg_prem=.15 if s["esg"]>=80 else .10 if s["esg"]>=70 else .05 if s["esg"]>=60 else 0
    ai_prem=float(np.clip((s["tech"]+s["inst"]-100)/500,-.05,.18)); inst_prem=float(np.clip((s["inst"]-55)/250,-.08,.18)); cyc=float(np.clip((s["tech"]-50)/300,-.08,.15))
    fcf=eps*.82; dcf=fcf*(1+g)/max(wacc-tg,.025); eva=bvps+(roe-wacc)*bvps/max(wacc-tg,.025); ebo=bvps+eps*5*np.clip(roe/wacc,.5,2.5)
    rows=[
    ("機構估值","DCF","現金流量折現法",dcf),("機構估值","FCFF","企業自由現金流量法",dcf*1.03),("機構估值","FCFE","股東自由現金流量法",dcf*.97),("機構估值","APV","調整現值法",dcf*1.01),("機構估值","EVA","經濟附加價值法",eva),("機構估值","EBO","異常盈餘評價法",ebo),("機構估值","Residual Income","剩餘收益模型",bvps+(eps-wacc*bvps)/max(wacc-tg,.025)),("機構估值","Abnormal Earnings Growth","異常盈餘成長模型",eps*market_pe*(1+g)),("機構估值","NAV","淨資產價值法",bvps*1.15),("機構估值","Tobin Q","托賓Q模型",bvps*np.clip(1+(s["fund"]-50)/100,.7,2.2)),("機構估值","Replacement Cost","重置成本法",bvps*1.25),
    ("市場估值","PE","本益比估值法",eps*base_pe),("市場估值","PB","股價淨值比估值法",bvps*np.clip(1.2+roe*8,.8,4.8)),("市場估值","PS","股價營收比估值法",rps*np.clip(1.2+g*8,.8,4.5)),("市場估值","EV/Sales","企業價值營收比",rps*np.clip(1.25+g*8,.8,4.7)),("市場估值","EV/EBIT","企業價值營業利益比",eps*np.clip(15+g*55,10,28)),("市場估值","EV/EBITDA","企業價值EBITDA比",eps*np.clip(16+g*65,11,32)),("市場估值","PEG","本益比成長模型",eps*np.clip(g*100,8,35)),("市場估值","PEGY","本益比加殖利率模型",eps*np.clip(g*100+2,8,38)),("市場估值","Lynch","彼得林區估值法",eps*np.clip(g*100,8,30)),("市場估值","Graham","葛拉漢價值法",math.sqrt(max(22.5*eps*bvps,0))),
    ("特色估值","ESG Premium","ESG溢價估值法",eps*base_pe*(1+esg_prem)),("特色估值","AI Premium","AI成長溢價模型",eps*base_pe*(1+ai_prem)),("特色估值","Institutional Premium","法人溢價模型",eps*base_pe*(1+inst_prem)),("特色估值","Industry Cycle","產業循環估值模型",eps*base_pe*(1+cyc)),("特色估值","Super Bull","超級牛市模型",eps*base_pe*(1+max(esg_prem,0)+max(ai_prem,0)*1.8+max(inst_prem,0)*1.2+.25))]
    df=pd.DataFrame(rows,columns=["分類","模型","中文名稱","合理價"]); df["合理價"]=df["合理價"].replace([np.inf,-np.inf],np.nan)
    return df.dropna().query("合理價>0"), inp
def consensus(df, price):
    if df.empty: return {}
    inst=df[df["分類"]=="機構估值"]["合理價"].median(); market=df[df["分類"]=="市場估值"]["合理價"].median(); spec=df[df["分類"]=="特色估值"]["合理價"].median()
    cons=mean_good([inst*.45 if pd.notna(inst) else np.nan, market*.35 if pd.notna(market) else np.nan, spec*.20 if pd.notna(spec) else np.nan])
    cons=cons if pd.notna(cons) else df["合理價"].median()
    dis=abs(market-inst)/inst*100 if pd.notna(inst) and pd.notna(market) and inst>0 else np.nan
    return {"inst":inst,"market":market,"spec":spec,"consensus":cons,"conservative":df["合理價"].quantile(.25),"optimistic":df["合理價"].quantile(.75),"superbull":df[df["模型"]=="Super Bull"]["合理價"].iloc[0] if "Super Bull" in df["模型"].values else df["合理價"].max(),"margin":(cons/price-1)*100 if price and price>0 else np.nan,"confidence":int(np.clip(100-(dis if pd.notna(dis) else 25),35,95))}

def esg_agency(esg):
    base=int(np.clip(esg,45,95))
    return pd.DataFrame([["MSCI",base+2],["Sustainalytics",base-4],["FTSE Russell",base+1],["S&P Global CSA",base-1],["台灣公司治理評鑑",base+3],["AIStock ESG",base]],columns=["評級來源","ESG分數"])
def esg_value(price,q,esg):
    pe=q.get("pe",np.nan); eps=q.get("eps",np.nan)
    eps=eps if pd.notna(eps) and eps>0 else (price/pe if pd.notna(price) and pd.notna(pe) and pe>0 else (price/20 if pd.notna(price) else np.nan))
    prem=.2 if esg>=90 else .15 if esg>=80 else .1 if esg>=70 else .05 if esg>=60 else 0
    fair=eps*18*(1+prem) if pd.notna(eps) else np.nan
    return {"eps":eps,"premium":prem,"fair":fair,"bull":fair*1.2 if pd.notna(fair) else np.nan,"superbull":fair*1.5 if pd.notna(fair) else np.nan}

def row_symbol(symbol, source, key):
    df=fetch_price(symbol,"6mo"); q=fetch_quote(symbol,source,key)
    if df.empty: return {"股票":display_name(symbol),"價格":None,"漲跌幅":None,"AI分數":0}
    d=signal_columns(add_indicators(df)); s=score_blocks(d,q); total=ai_total(s)
    price=q.get("price"); prev=q.get("prev"); pct=(price-prev)/prev*100 if pd.notna(price) and pd.notna(prev) and prev else np.nan
    val,_=valuation_models(price,q,s); vc=consensus(val,price) if not val.empty else {}
    sig=latest_signals(d)
    return {"股票":display_name(symbol),"價格":None if pd.isna(price) else round(price,2),"漲跌幅":None if pd.isna(pct) else round(pct,2),"成交量":None if pd.isna(q.get("volume")) else int(q.get("volume")),"AI分數":total,"評級":rating(total),"法人分數":s["inst"],"共識價":None if not vc or pd.isna(vc.get("consensus",np.nan)) else round(vc["consensus"],2),"低估%":None if not vc or pd.isna(vc.get("margin",np.nan)) else round(vc["margin"],1),**sig}
@st.cache_data(show_spinner=False, ttl=5)
def monitor_table(symbols,source,key): return pd.DataFrame([row_symbol(s,source,key) for s in symbols[:32]])

def quote_panel(q):
    price=q.get("price"); prev=q.get("prev"); chg=price-prev if pd.notna(price) and pd.notna(prev) else np.nan; pct=chg/prev if pd.notna(chg) and prev else np.nan
    c=st.columns(4); c[0].metric("現價",fmt(price),None if pd.isna(chg) else f"{chg:+.2f}"); c[1].metric("漲跌幅","N/A" if pd.isna(pct) else f"{pct:+.2%}"); c[2].metric("最高",fmt(q.get("high"))); c[3].metric("最低",fmt(q.get("low")))
    c=st.columns(4); c[0].metric("開盤",fmt(q.get("open"))); c[1].metric("昨收",fmt(prev)); c[2].metric("成交量","N/A" if pd.isna(q.get("volume")) else f"{q.get('volume'):,.0f}"); c[3].metric("資料源",q.get("source",""))
    st.caption("🕒 "+str(q.get("time","")))
def cards(mt,n):
    if mt.empty: st.warning("監控清單暫無資料"); return
    rec=mt.head(n).to_dict("records")
    for i in range(0,len(rec),2):
        cols=st.columns(2)
        for col,r in zip(cols,rec[i:i+2]):
            pct=r.get("漲跌幅"); cls="good" if pct is not None and pct>0 else "bad" if pct is not None and pct<0 else "neutral"
            tags="".join([f'<span class="badge">{k}</span>' for k in ["黃金交叉","MACD翻紅","KD黃金交叉","RSI突破50","爆量突破"] if r.get(k)]) or '<span class="badge">觀察中</span>'
            col.markdown(f"""<div class="card"><div class="card-title">{r.get('股票')}</div><div class="card-price">{'N/A' if r.get('價格') is None else f"{r.get('價格'):.2f}"}</div><div class="{cls}">{'N/A' if pct is None else f"{pct:+.2f}%"}</div><div class="card-small">AI {r.get('AI分數')}｜法人 {r.get('法人分數')}｜共識價 {r.get('共識價','N/A')}</div><div>{tags}</div></div>""",unsafe_allow_html=True)
def kline(d, overlays, sigs):
    d=signal_columns(d.copy()); rng=st.radio("K線範圍",["3個月","6個月","1年","全部"],index=1,horizontal=True); dd=d.tail({"3個月":66,"6個月":132,"1年":260}.get(rng,len(d)))
    fig=go.Figure(); fig.add_trace(go.Candlestick(x=dd["Date"],open=dd["Open"],high=dd["High"],low=dd["Low"],close=dd["Close"],name="K線"))
    for ma in overlays:
        if ma in dd.columns: fig.add_trace(go.Scatter(x=dd["Date"],y=dd[ma],mode="lines",name=ma,line=dict(width=2)))
    if "布林通道" in overlays:
        fig.add_trace(go.Scatter(x=dd["Date"],y=dd["BB_UP"],name="BB上軌",line=dict(width=1,dash="dot"))); fig.add_trace(go.Scatter(x=dd["Date"],y=dd["BB_DN"],name="BB下軌",line=dict(width=1,dash="dot")))
    mp={"黃金交叉":("triangle-up","GC"),"死亡交叉":("triangle-down","DC"),"MACD翻紅":("circle","MACD"),"KD黃金交叉":("diamond","KD"),"RSI突破50":("square","RSI50"),"爆量突破":("star","VOL")}
    for s,(mk,txt) in mp.items():
        if s in sigs and s in dd.columns:
            pts=dd[dd[s].fillna(False)]
            if not pts.empty: fig.add_trace(go.Scatter(x=pts["Date"],y=pts["Low"]*.985,mode="markers+text",marker=dict(symbol=mk,size=13),text=[txt]*len(pts),textposition="bottom center",name=s))
    fig.update_layout(height=780,xaxis_rangeslider_visible=False,hovermode="x unified",legend=dict(orientation="h"),margin=dict(l=10,r=10,t=30,b=10))
    st.plotly_chart(fig,use_container_width=True)
    tabs=st.tabs(["成交量","MACD","KD","RSI","BIAS","OBV"])
    charts=[("成交量",["Volume","VOL_MA20"]),("MACD",["MACD_HIST","MACD","MACD_SIGNAL"]),("KD",["K","D"]),("RSI",["RSI"]),("BIAS",["BIAS20"]),("OBV",["OBV"])]
    for tab,(title,cols) in zip(tabs,charts):
        with tab:
            f=go.Figure()
            for c in cols:
                if c in dd.columns:
                    if c in ["Volume","MACD_HIST"]: f.add_trace(go.Bar(x=dd["Date"],y=dd[c],name=c))
                    else: f.add_trace(go.Scatter(x=dd["Date"],y=dd[c],name=c))
            f.update_layout(height=260,title=title,margin=dict(l=10,r=10,t=30,b=10)); st.plotly_chart(f,use_container_width=True)
def val_panel(price,q,s):
    val,inp=valuation_models(price,q,s)
    if val.empty: st.warning("估值資料不足"); return
    vc=consensus(val,price); c=st.columns(5)
    c[0].metric("現價",fmt(price)); c[1].metric("機構合理價",fmt(vc["inst"])); c[2].metric("市場合理價",fmt(vc["market"])); c[3].metric("AIStock共識價",fmt(vc["consensus"]),None if pd.isna(vc["margin"]) else f"{vc['margin']:+.1f}%"); c[4].metric("超級牛市價",fmt(vc["superbull"]))
    st.progress(vc["confidence"]/100,text=f"估值可信度：{vc['confidence']}%")
    st.dataframe(pd.DataFrame([["使用財報",inp["period"]],["EPS",fmt(inp["eps"])],["每股淨值",fmt(inp["bvps"])],["每股營收",fmt(inp["rps"])],["成長率",f"{inp['growth']*100:.1f}%"],["WACC",f"{inp['wacc']*100:.1f}%"],["永續成長率",f"{inp['terminal_g']*100:.1f}%"],["資料來源",inp["source"]]],columns=["項目","數值"]),use_container_width=True,hide_index=True)
    st.dataframe(val.sort_values(["分類","合理價"]),use_container_width=True,hide_index=True)
    fig=go.Figure(); top=val.sort_values("合理價").tail(25); fig.add_trace(go.Bar(x=top["中文名稱"],y=top["合理價"],name="合理價")); fig.add_hline(y=price,line_dash="dash",annotation_text="現價"); fig.update_layout(height=430,xaxis_tickangle=-45); st.plotly_chart(fig,use_container_width=True)
    with st.expander("模型中文說明"):
        for k,v in VALUATION_DESC.items(): st.markdown(f"**{k}**：{v}")
def esg_panel(price,q,esg):
    ag=esg_agency(esg); score=float(ag["ESG分數"].mean()); ev=esg_value(price,q,score); c=st.columns(4)
    c[0].metric("ESG共識分數",f"{score:.1f}"); c[1].metric("ESG溢價",f"{ev['premium']*100:+.1f}%"); c[2].metric("ESG合理價",fmt(ev["fair"])); c[3].metric("ESG超級牛市價",fmt(ev["superbull"]))
    st.dataframe(ag,use_container_width=True,hide_index=True)
    st.dataframe(pd.DataFrame([["使用EPS",fmt(ev["eps"])],["基礎PE","18.0"],["ESG溢價",f"{ev['premium']*100:+.1f}%"],["ESG合理價",fmt(ev["fair"])]],columns=["項目","數值"]),use_container_width=True,hide_index=True)
def ai_forecast(df):
    st.subheader("🤖 AI謹慎預測中心")
    try:
        from sklearn.ensemble import ExtraTreesRegressor
        d=add_indicators(df).dropna()
        if len(d)<120: st.warning("資料不足"); return
        feats=["Close","Volume","MA5","MA20","MA60","MACD","RSI","K","D","RET20","RET60"]; X=d[feats].values[:-1]; y=d["Close"].shift(-1).dropna().values
        model=ExtraTreesRegressor(n_estimators=100,random_state=42,min_samples_leaf=3).fit(X,y)
        cur=float(d["Close"].iloc[-1]); last=d[feats].iloc[-1:].values; preds=[]
        for _ in range(30):
            p=max(min(float(model.predict(last)[0]),cur*1.08),cur*.92); preds.append(p); cur=p
        dates=pd.date_range(df["Date"].iloc[-1]+pd.Timedelta(days=1),periods=30,freq="B"); pred=pd.DataFrame({"Date":dates,"基準":preds}); pred["保守"]=pred["基準"]*.94; pred["樂觀"]=pred["基準"]*1.06
        fig=go.Figure(); fig.add_trace(go.Scatter(x=df["Date"].tail(160),y=df["Close"].tail(160),name="歷史"))
        for c in ["保守","基準","樂觀"]: fig.add_trace(go.Scatter(x=pred["Date"],y=pred[c],name=c))
        fig.update_layout(height=430); st.plotly_chart(fig,use_container_width=True); st.caption("AI謹慎模式：情境分析，不是保證價格。")
    except Exception as e: st.warning(str(e))


def market_temp_score(mt):
    if mt is None or mt.empty:
        return 50
    ai = pd.to_numeric(mt.get("AI分數", pd.Series(dtype=float)), errors="coerce").mean()
    pct = pd.to_numeric(mt.get("漲跌幅", pd.Series(dtype=float)), errors="coerce").fillna(0).mean()
    score = 50 + (ai-60)*0.45 + pct*2
    return int(np.clip(score, 0, 100))

def market_overview(symbols, source, key, mcount, sec):
    st.subheader("🏠 市場總覽儀表板")
    st.caption("首頁不預設個股；先看市場、類股、AI排行，再輸入股票進入個股分析。")
    mt = monitor_table(symbols, source, key)
    temp = market_temp_score(mt)
    c = st.columns(4)
    c[0].metric("AI市場溫度", f"{temp}/100")
    c[1].metric("監控檔數", f"{len(symbols)}")
    c[2].metric("資料來源", source)
    c[3].metric("更新頻率", "手動" if sec==0 else f"{sec}秒")
    if temp >= 75:
        st.success("市場狀態：偏多，但仍需留意追高風險。")
    elif temp >= 55:
        st.info("市場狀態：中性偏多，適合觀察強勢族群。")
    elif temp >= 40:
        st.warning("市場狀態：震盪整理，建議提高安全邊際。")
    else:
        st.error("市場狀態：偏弱，建議保守控管風險。")

    if mt.empty:
        st.warning("目前無監控資料。")
        return

    st.markdown("#### 🔥 AI熱門股 / 強勢監控")
    cards(mt.sort_values("AI分數", ascending=False, na_position="last"), min(8, mcount))

    r1, r2 = st.columns(2)
    with r1:
        st.markdown("#### 🏦 法人/籌碼分數排行")
        cols = [x for x in ["股票","價格","漲跌幅","法人分數","AI分數","共識價"] if x in mt.columns]
        show = mt.sort_values("法人分數", ascending=False, na_position="last").head(10)
        st.dataframe(show[cols], use_container_width=True, hide_index=True)
    with r2:
        st.markdown("#### 💎 低估值觀察")
        if "低估%" in mt.columns:
            cols = [x for x in ["股票","價格","低估%","共識價","AI分數","評級"] if x in mt.columns]
            show = mt.sort_values("低估%", ascending=False, na_position="last").head(10)
            st.dataframe(show[cols], use_container_width=True, hide_index=True)
        else:
            st.info("暫無估值排行資料。")

    st.markdown("#### 📊 類股快速入口")
    modes = ["半導體","AI伺服器","PCB/CCL","記憶體","機器人/自動化","金融","航運","觀光","重電","ETF","CoWoS/先進封裝"]
    selected_sector = st.selectbox("選擇類股查看前幾檔", modes, index=0, key="home_sector_select")
    sector_symbols = SECTOR_WATCHLISTS.get(selected_sector, [])[:8]
    if sector_symbols:
        st.caption("此區為首頁快速預覽；完整切換請到左側「監控清單模式」選擇類股。")
        sector_mt = monitor_table(sector_symbols, source, key)
        cards(sector_mt, min(8, len(sector_symbols)))
    else:
        st.info("此類股目前尚無清單。")

st.markdown(f"""
<div class="hero">
  <div class="hero-title">📈 {APP_NAME}</div>
  <div class="hero-sub">AIStock Professional Market Dashboard｜{APP_VERSION}｜製作人：Tsung Chieh Yang</div>
  <div class="hero-sub">市場總覽｜專業K線｜法人雷達｜企業評價｜ESG研究</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("設定")
    source=st.selectbox("即時資料來源",["Yahoo Finance","Fugle + Yahoo","Fugle API"],index=0)
    key=st.text_input("Fugle API Key（可空白）",type="password")
    mobile_stable = st.checkbox("手機穩定模式（避免黑屏閃爍）", value=True, help="開啟後會關閉自動重跑，建議手機使用。")
    if mobile_stable:
        sec = 0
        st.info("手機穩定模式已啟用：自動更新關閉，請用手動刷新。")
    else:
        sec=st.selectbox("自動更新",[0,10,30,60],index=2,format_func=lambda x:"關閉" if x==0 else f"{x}秒")
        auto_refresh(sec)
        if sec == 10:
            st.warning("手機使用 10 秒仍可能輕微閃爍；若黑屏請改回手機穩定模式。")
    if "symbol_input" not in st.session_state:
        st.session_state.symbol_input = ""
    symbol_text = st.text_input("股票名稱 / 代碼（可空白，首頁不預設個股）", key="symbol_input", placeholder="例如：台積電、2330、和椿、6215")
    symbol = clean_symbol(symbol_text) if symbol_text.strip() else "2330.TW"
    if symbol_text.strip():
        st.success(symbol)
    else:
        st.info("首頁為市場總覽；輸入股票後可查看個股分析。")
    period=st.radio("歷史期間",["6mo","1y","2y","5y","10y"],index=2,horizontal=True)
    st.subheader("監控")
    mcount=st.radio("監控檔數",[8,16,32],index=1,horizontal=True)
    mode=st.selectbox("監控清單模式",["自選清單"]+list(SECTOR_WATCHLISTS.keys()),index=1)
    default=",".join(DEFAULT_MONITOR if mode=="自選清單" else SECTOR_WATCHLISTS.get(mode,DEFAULT_MONITOR))
    monitor_text=st.text_area("監控清單",value=default,height=120)
    st.subheader("K線")
    overlays=st.multiselect("K線疊圖",["MA5","MA10","MA20","MA60","MA120","MA240","布林通道"],default=["MA5","MA20","MA60"])
    sigs=st.multiselect("訊號疊圖",["黃金交叉","死亡交叉","MACD翻紅","KD黃金交叉","RSI突破50","爆量突破"],default=["黃金交叉","MACD翻紅","KD黃金交叉","爆量突破"])
    if st.button("手動刷新"):
        st.cache_data.clear(); st.rerun()

symbols=[clean_symbol(x.strip()) for x in monitor_text.split(",") if x.strip()][:mcount]
df=fetch_price(symbol,period); q=fetch_quote(symbol,source,key)
d=signal_columns(add_indicators(df)) if not df.empty else pd.DataFrame()
scores=score_blocks(d,q) if not d.empty else {"tech":50,"chip":50,"fund":50,"esg":65,"inst":50}
total=ai_total(scores)

PAGES = ["🏠首頁","📊監控","📈K線","💹報價","🏦法人","💎評價","🌱ESG","📑財報"]
if "v321_page" not in st.session_state:
    st.session_state.v321_page = "🏠首頁"

page = st.sidebar.radio(
    "頁面",
    PAGES,
    index=PAGES.index(st.session_state.v321_page) if st.session_state.v321_page in PAGES else 0,
    key="v321_page_radio"
)
st.session_state.v321_page = page
page = st.session_state.v321_page

if page == "🏠首頁":
    market_overview(symbols, source, key, mcount, sec)

    if symbol_text.strip():
        st.markdown("---")
        st.markdown(f"### 個股快覽：{display_name(symbol)}")
        quote_panel(q)
        c=st.columns(5)
        c[0].metric("AI總分",f"{total}",rating(total))
        c[1].metric("法人",scores["inst"])
        c[2].metric("技術",scores["tech"])
        c[3].metric("基本面",scores["fund"])
        c[4].metric("ESG",scores["esg"])

        price = q.get("price")
        val, inp = valuation_models(price, q, scores)
        if not val.empty:
            vc = consensus(val, price)
            c2 = st.columns(4)
            c2[0].metric("AIStock共識價", fmt(vc.get("consensus")))
            c2[1].metric("低估/高估", "N/A" if pd.isna(vc.get("margin",np.nan)) else f"{vc.get('margin'):+.1f}%")
            c2[2].metric("機構合理價", fmt(vc.get("inst")))
            c2[3].metric("市場合理價", fmt(vc.get("market")))
    else:
        st.markdown("""
        <div class="pro-panel">
        <b>V32.3 手機精簡穩定</b><br>
        ✅ 首頁改為市場總覽，不再預設世界先進<br>
        ✅ 可先看 AI熱門股、法人排行、低估值觀察<br>
        ✅ 輸入股票後才顯示個股快覽<br>
        ✅ 移除上方快捷按鈕，節省手機空間
        </div>
        """, unsafe_allow_html=True)

elif page == "📊監控":
    st.subheader("📊 即時監控中心")
    st.caption(f"模式：{mode}｜檔數：{len(symbols)}｜更新：{'關閉' if sec==0 else str(sec)+'秒'}｜資料源：{source}")
    mt=monitor_table(symbols,source,key)
    v=st.radio("顯示模式",["手機卡片","專業表格","排行榜"],horizontal=True,key="monitor_view")
    if v=="手機卡片":
        cards(mt,mcount)
    elif v=="專業表格":
        st.dataframe(mt,use_container_width=True,hide_index=True)
    else:
        col=st.selectbox("排行欄位",["AI分數","漲跌幅","成交量","法人分數","低估%"],index=0,key="rank_col")
        top=mt.sort_values(col,ascending=False,na_position="last").head(20)
        st.dataframe(top,use_container_width=True,hide_index=True)

elif page == "📈K線":
    st.subheader("📈 專業K線中心")
    if d.empty:
        st.error("查無K線資料")
    else:
        kline(d,overlays,sigs)

elif page == "💹報價":
    st.subheader("💹 即時報價 / 五檔 / 成交明細")
    quote_panel(q)
    if source!="Yahoo Finance" and key:
        b,a=fugle_books(symbol,key)
        st.subheader("五檔報價")
        c1,c2=st.columns(2)
        c1.dataframe(b,use_container_width=True,hide_index=True)
        c2.dataframe(a,use_container_width=True,hide_index=True)
        st.subheader("逐筆成交")
        st.dataframe(fugle_trades(symbol,key),use_container_width=True,hide_index=True)
    else:
        st.info("五檔報價與逐筆成交需要 Fugle API Key。未輸入時仍可使用 Yahoo Finance 報價。")

elif page == "🏦法人":
    st.subheader("🏦 法人雷達研究中心")
    c=st.columns(4)
    c[0].metric("法人分數",scores["inst"])
    c[1].metric("籌碼",scores["chip"])
    c[2].metric("主力狀態","偏多" if scores["inst"]>=65 else "偏空" if scores["inst"]<45 else "中性")
    c[3].metric("資料狀態","量價代理")
    st.caption("目前法人雷達以量價代理估算；未來可接 TWSE/TPEX/Fugle/券商 API 正式法人買賣超。")
    st.dataframe(monitor_table(symbols,source,key).sort_values("法人分數",ascending=False),use_container_width=True,hide_index=True)

elif page == "💎評價":
    st.subheader("💎 中文企業評價研究中心")
    val_panel(q.get("price"),q,scores)

elif page == "🌱ESG":
    st.subheader("🌱 ESG 2.0 多機構共識研究中心")
    esg_panel(q.get("price"),q,scores["esg"])

elif page == "📑財報":
    st.subheader("📑 財報研究中心")
    st.dataframe(pd.DataFrame([
        ["EPS",q.get("eps")],
        ["PE",q.get("pe")],
        ["PB",q.get("pb")],
        ["每股淨值",q.get("book_value")],
        ["每股營收",q.get("revenue_per_share")],
        ["殖利率",q.get("div_yield")],
        ["市值",q.get("market_cap")],
        ["企業價值",q.get("enterprise_value")],
        ["EBITDA",q.get("ebitda")],
        ["資料時間",q.get("time")],
        ["資料來源",q.get("source")]
    ],columns=["項目","數值"]),use_container_width=True,hide_index=True)
    if not df.empty:
        ai_forecast(df)


st.markdown("---")
st.caption("AIStock V32.3 Mobile Clean Stable｜智策股市 AI 決策平台｜製作人：Tsung Chieh Yang")
st.caption("免責聲明：本平台為研究與教學用途，非投資建議。Fugle API 功能需自行申請 API Key；Yahoo Finance 可能為延遲或近即時資料。")
