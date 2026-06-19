
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re, math
import json
from pathlib import Path as _Path

STATE_FILE = _Path("aistock_v38_state.json")

def load_v38_state():
    default = {"active_symbol":"6215.TWO","watchlist":["6215.TWO","5347.TWO","2303.TW","2330.TW","2383.TW","3260.TWO","2308.TW","2454.TW"],"favorites":["6215.TWO","5347.TWO","2303.TW"]}
    try:
        if STATE_FILE.exists():
            data=json.loads(STATE_FILE.read_text(encoding="utf-8"))
            default.update({k:v for k,v in data.items() if k in default})
    except Exception:
        pass
    return default

def save_v38_state(active_symbol=None, watchlist=None, favorites=None):
    data=load_v38_state()
    if active_symbol: data["active_symbol"]=active_symbol
    if watchlist: data["watchlist"]=watchlist
    if favorites is not None: data["favorites"]=favorites
    try:
        STATE_FILE.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    except Exception:
        pass
    return data

def init_v38_session():
    data=load_v38_state()
    if "active_symbol" not in st.session_state: st.session_state.active_symbol=data.get("active_symbol","6215.TWO")
    if "watch_text_value" not in st.session_state: st.session_state.watch_text_value=",".join(data.get("watchlist",DEFAULT_MONITOR))
    if "favorites" not in st.session_state: st.session_state.favorites=data.get("favorites",[])

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None


APP_VERSION="V38.4 Professional UI Edition"
APP_NAME="智策股市 AI 決策平台"
DEVELOPER_NAME="Tsung Chieh Yang"
PRO_MODE=True
st.set_page_config(page_title=f"{APP_NAME} {APP_VERSION}", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

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
</style>
""", unsafe_allow_html=True)

TW_STOCKS={"台積電":"2330.TW","聯電":"2303.TW","世界先進":"5347.TWO","和椿":"6215.TWO","台光電":"2383.TW","威剛":"3260.TWO","台達電":"2308.TW","鴻海":"2317.TW","聯發科":"2454.TW","廣達":"2382.TW","緯創":"3231.TW","英業達":"2356.TW","華碩":"2357.TW","技嘉":"2376.TW","欣興":"3037.TW","南亞科":"2408.TW","瑞昱":"2379.TW","力積電":"6770.TW","智邦":"2345.TW","奇鋐":"3017.TW","世芯-KY":"3661.TW","緯穎":"6669.TW","健策":"3653.TW"}
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
    "6274","8046","6187","6488","4966","6485","6411","3529","3081",
    "3293","3324","3552","3587","4105","4123","4128","4743","6121",
    "6180","6182","6223","6244","6261","6279","6290","6486","6547"
}

def clean_symbol(x):
    s=str(x).strip()
    if not s: return ""
    if s in TW_STOCKS: return TW_STOCKS[s]
    s=s.upper().replace(" ","")
    if re.fullmatch(r"\d{4}", s):
        return f"{s}.TWO" if s in OTC_CODES else f"{s}.TW"
    if re.fullmatch(r"\d{4}\.TW|\d{4}\.TWO", s):
        return s
    return s

def display_name(symbol):
    for k,v in TW_STOCKS.items():
        if v==symbol: return f"{k} / {symbol}"
    return symbol

def fmt(x):
    return "N/A" if x is None or pd.isna(x) else f"{float(x):.2f}"

def now_tw():
    return (datetime.utcnow()+timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

def maybe_reload(sec):
    # V37.2: 使用 Streamlit autorefresh，避免 browser reload 導致回首頁或股票重設
    if sec and sec > 0:
        if st_autorefresh is not None:
            st_autorefresh(interval=int(sec)*1000, key="v372_monitor_autorefresh")
        else:
            st.caption("自動更新套件未安裝，請手動刷新；已避免使用瀏覽器reload造成回首頁。")

@st.cache_data(show_spinner=False, ttl=30)
def yf_quote(symbol):
    q={"price":np.nan,"prev":np.nan,"open":np.nan,"high":np.nan,"low":np.nan,"volume":np.nan,"pe":np.nan,"pb":np.nan,"eps":np.nan,"book_value":np.nan,"revenue_per_share":np.nan,"market_cap":np.nan,"div_yield":np.nan,"source":"Yahoo Finance","time":now_tw()}
    try:
        t=yf.Ticker(symbol)
        try: fast=t.fast_info
        except Exception: fast={}
        def gf(*ks):
            for k in ks:
                try:
                    v=fast.get(k) if hasattr(fast,"get") else getattr(fast,k)
                    if v is not None: return safe_float(v)
                except Exception: pass
            return np.nan
        q["price"]=gf("last_price","lastPrice"); q["prev"]=gf("previous_close","previousClose"); q["open"]=gf("open"); q["high"]=gf("day_high","dayHigh"); q["low"]=gf("day_low","dayLow"); q["volume"]=gf("last_volume","lastVolume","volume"); q["market_cap"]=gf("market_cap","marketCap")
        try:
            info=t.info or {}
            for k,ik in {"pe":"trailingPE","pb":"priceToBook","eps":"trailingEps","book_value":"bookValue","revenue_per_share":"revenuePerShare","div_yield":"dividendYield"}.items():
                q[k]=safe_float(info.get(ik))
            if pd.isna(q["price"]): q["price"]=safe_float(info.get("currentPrice",info.get("regularMarketPrice")))
            if pd.isna(q["prev"]): q["prev"]=safe_float(info.get("previousClose"))
        except Exception: pass

        # V38.3：價格備援，Yahoo部分台股如 6215.TWO 可能 quote 欄位 N/A
        if pd.isna(q.get("price")) or q.get("price") is None:
            try:
                hist = t.history(period="10d", auto_adjust=False)
                if hist is not None and not hist.empty:
                    q["price"] = safe_float(hist["Close"].dropna().iloc[-1])
                    if pd.isna(q.get("prev")) and len(hist["Close"].dropna()) >= 2:
                        q["prev"] = safe_float(hist["Close"].dropna().iloc[-2])
                    q["source"] = "Yahoo Finance / Close fallback"
            except Exception:
                pass
    except Exception: pass
    return q

@st.cache_data(show_spinner=False, ttl=60)
def fetch_daily(symbol, period="2y"):
    try:
        df=yf.download(symbol, period=period, interval="1d", auto_adjust=False, progress=False)
        if df is None or df.empty: return pd.DataFrame()
        if isinstance(df.columns,pd.MultiIndex): df.columns=[c[0] for c in df.columns]
        df=df.reset_index(); df["Date"]=pd.to_datetime(df["Date"])
        return df.dropna(subset=["Close"])
    except Exception: return pd.DataFrame()

@st.cache_data(show_spinner=False, ttl=60)
def fetch_intraday(symbol, interval="60m"):
    period={"60m":"60d","30m":"30d","15m":"30d","5m":"7d"}.get(interval,"30d")
    try:
        df=yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)
        if df is None or df.empty: return pd.DataFrame()
        if isinstance(df.columns,pd.MultiIndex): df.columns=[c[0] for c in df.columns]
        df=df.reset_index(); dc="Datetime" if "Datetime" in df.columns else "Date"; df=df.rename(columns={dc:"Date"})
        df["Date"]=pd.to_datetime(df["Date"]).dt.tz_localize(None)
        return df.dropna(subset=["Close"])
    except Exception: return pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=60)
def fetch_with_market_fallback(symbol, period="2y"):
    """V38.1：台股上市/上櫃雙市場容錯。6215 等上櫃股優先 .TWO，抓不到時自動嘗試另一市場。"""
    candidates=[]
    s=str(symbol).upper()
    candidates.append(s)
    if re.fullmatch(r"\d{4}\.TW", s):
        candidates.append(s.replace(".TW",".TWO"))
    elif re.fullmatch(r"\d{4}\.TWO", s):
        candidates.append(s.replace(".TWO",".TW"))
    elif re.fullmatch(r"\d{4}", s):
        candidates.extend([clean_symbol(s), f"{s}.TW", f"{s}.TWO"])
    for c in list(dict.fromkeys(candidates)):
        df=fetch_daily(c, period)
        if df is not None and not df.empty:
            return c, df
    return symbol, pd.DataFrame()

def get_kline_safe(symbol, mode, period="2y"):
    """V38.1：K線容錯，分K抓不到時自動降級到日線；市場後綴抓不到時切換 .TW/.TWO。"""
    resolved, daily = fetch_with_market_fallback(symbol, period)
    if mode=="日線":
        return resolved, daily
    if mode=="週線":
        return resolved, resample_ohlcv(fetch_with_market_fallback(resolved,"5y")[1],"W-FRI")
    if mode=="月線":
        return resolved, resample_ohlcv(fetch_with_market_fallback(resolved,"10y")[1],"ME")
    interval={"60分":"60m","30分":"30m","15分":"15m","5分":"5m"}.get(mode,"60m")
    candidates=[resolved]
    if resolved.endswith(".TW"):
        candidates.append(resolved.replace(".TW",".TWO"))
    elif resolved.endswith(".TWO"):
        candidates.append(resolved.replace(".TWO",".TW"))
    for c in list(dict.fromkeys(candidates)):
        df=fetch_intraday(c, interval)
        if df is not None and not df.empty:
            return c, df
    # 分K缺資料時，回退日線，避免畫面空白
    return resolved, daily

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

def kpi(items):
    html='<div class="kpi-grid">'
    for label,value in items: html+=f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>'
    st.markdown(html+'</div>', unsafe_allow_html=True)

def clamp_fair(v, price):
    v=safe_float(v); p=safe_float(price)
    if pd.isna(v) or v<=0: return np.nan
    if pd.notna(p) and p>0 and (v<p*.35 or v>p*3.5): return np.nan
    return v



def valuation(price,q,s):
    """V38.1：資料缺漏也顯示完整模型，不讓模型只剩2個。"""
    price=safe_float(price)
    if pd.isna(price) or price<=0:
        price=100.0

    pe=safe_float(q.get("pe"))
    pb=safe_float(q.get("pb"))
    eps=safe_float(q.get("eps"))
    bvps=safe_float(q.get("book_value"))
    rps=safe_float(q.get("revenue_per_share"))

    eps_source="Yahoo trailingEps"
    if pd.isna(eps) or eps<=0:
        if pd.notna(pe) and pe>0:
            eps=price/pe
            eps_source="price / PE"
        else:
            eps=price/20
            eps_source="AI proxy: price / 20"

    bvps_source="Yahoo bookValue"
    if pd.isna(bvps) or bvps<=0:
        if pd.notna(pb) and pb>0:
            bvps=price/pb
            bvps_source="price / PB"
        else:
            bvps=price/2.2
            bvps_source="AI proxy: price / 2.2"

    rps_source="Yahoo revenuePerShare"
    if pd.isna(rps) or rps<=0:
        rps=price/2.5
        rps_source="AI proxy: price / 2.5"

    g=float(np.clip((s["tech"]+s["fund"]+s["inst"])/300*.22,.03,.22))
    wacc=float(np.clip(.105-(s["fund"]-50)/1000-(s["esg"]-60)/1500,.065,.13))
    tg=float(np.clip(.025+(g-.08)/6,.01,.04))
    roe=float(np.clip(.08+(s["fund"]-50)/250,.03,.28))
    base_pe=float(np.clip(14+g*80,10,32))
    esg_prem=.20 if s["esg"]>=90 else (.15 if s["esg"]>=80 else (.10 if s["esg"]>=70 else (.05 if s["esg"]>=60 else 0)))
    ai_prem=float(np.clip((s["tech"]+s["inst"]-100)/500,-.05,.18))
    inst_prem=float(np.clip((s["inst"]-55)/250,-.08,.18))
    cycle_prem=float(np.clip((s["tech"]-50)/300,-.08,.15))

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
    replacement=bvps*1.25

    rows=[
        ("資產法","NAV","淨資產價值法",nav),
        ("資產法","Tobin Q","托賓Q模型",tobin),
        ("資產法","Replacement Cost","重置成本代理",replacement),

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
        ("市場法","Graham","葛拉漢公式",math.sqrt(max(22.5*eps*bvps,0))),

        ("AIStock","ESG Premium","ESG溢價模型",eps*base_pe*(1+esg_prem)),
        ("AIStock","AI Premium","AI成長溢價模型",eps*base_pe*(1+ai_prem)),
        ("AIStock","Institutional Premium","法人溢價模型",eps*base_pe*(1+inst_prem)),
        ("AIStock","Industry Cycle","產業循環模型",eps*base_pe*(1+cycle_prem)),
        ("AIStock","Super Bull","超級牛市模型",eps*base_pe*(1+max(esg_prem,0)+max(ai_prem,0)*1.8+max(inst_prem,0)*1.2+.25)),
    ]
    df=pd.DataFrame(rows,columns=["分類","模型","中文名稱","合理價"])
    # V38.1：保留完整模型，只標示是否超出常態，不直接刪光
    df["合理價"]=pd.to_numeric(df["合理價"],errors="coerce").replace([np.inf,-np.inf],np.nan)
    df["狀態"]=df["合理價"].apply(lambda x: "代理估算" if pd.notna(x) else "資料不足")
    df["合理價"]=df["合理價"].fillna(price)
    df["偏離現價%"]=(df["合理價"]/price-1)*100

    inp={
        "EPS":eps,"EPS來源":eps_source,
        "BVPS":bvps,"BVPS來源":bvps_source,
        "每股營收":rps,"每股營收來源":rps_source,
        "成長率":g,"WACC":wacc,"永續成長率":tg,"ROE":roe,"股利假設":dividend
    }
    return df, inp

def consensus(df):
    if df.empty: return np.nan
    med=df["合理價"].median(); d=df[(df["合理價"]>=med*.45)&(df["合理價"]<=med*2.2)]
    return d["合理價"].median() if not d.empty else med

def esg_valuation(price,q,score):
    price=safe_float(price)
    if pd.isna(price) or price<=0:
        price=100.0
    eps=safe_float(q.get("eps")); pe=safe_float(q.get("pe"))
    eps=eps if pd.notna(eps) and eps>0 else (price/pe if pd.notna(pe) and pe>0 else price/20)
    prem=.20 if score>=90 else .15 if score>=80 else .10 if score>=70 else .05 if score>=60 else 0
    fair=eps*18*(1+prem)
    return {"EPS":eps,"ESG溢價":prem,"ESG合理價":fair,"ESG牛市價":fair*1.2,"ESG超級牛市價":fair*1.5}

def institutional_proxy(df):
    if df.empty or len(df)<30: return pd.DataFrame([["外資","資料不足",0,0],["投信","資料不足",0,0],["自營商","資料不足",0,0]],columns=["法人","買賣方向","估計張數","強度"])
    d=add_indicators(df).dropna(); x=d.iloc[-1]
    vol=safe_float(x.get("Volume"),0); volma=safe_float(x.get("VOL_MA20"),vol or 1); vr=max(vol/volma,0) if volma else 1; ret20=safe_float(x.get("RET20"),0); ret60=safe_float(x.get("RET60"),0); close=safe_float(x.get("Close"),0); ma20=safe_float(x.get("MA20"),0); ma60=safe_float(x.get("MA60"),0)
    base=max(int(max(vol/1000,1)*min(max(vr,.4),2.5)*.06),1)
    scores={"外資":int(np.clip(50+ret20*160+ret60*80+(close>ma20)*12+(vr-1)*10,0,100)),"投信":int(np.clip(50+ret20*120+(ma20>ma60)*15+(close>ma20)*8,0,100)),"自營商":int(np.clip(50+ret20*220+(vr-1)*18,0,100))}
    mult={"外資":1.6,"投信":.75,"自營商":.45}; rows=[]
    for name,sc in scores.items():
        dire="買超" if sc>=55 else ("賣超" if sc<=45 else "中性"); sign=1 if dire=="買超" else (-1 if dire=="賣超" else 0)
        rows.append([name,dire,int(base*mult[name]*sign),sc])
    return pd.DataFrame(rows,columns=["法人","買賣方向","估計張數","強度"])


def rating_from_score(score):
    score = safe_float(score, 50)
    if score >= 85: return "★★★★★ 強力買進"
    if score >= 70: return "★★★★ 買進"
    if score >= 55: return "★★★ 中立"
    if score >= 40: return "★★ 減碼"
    return "★ 賣出"

def bias_text(score):
    score = safe_float(score, 50)
    if score >= 70: return "偏多"
    if score >= 55: return "中性偏多"
    if score >= 45: return "中性"
    if score >= 30: return "中性偏空"
    return "偏空"

def institutional_radar_engine(df, q, scores):
    """
    V38.2 法人雷達2.0
    目前採 AIStock Proxy：Yahoo量價 + 技術分數 + 籌碼代理。
    未串接 TWSE/TPEX/Fugle/券商分點前，不宣稱為正式法人資料。
    """
    if df is None or df.empty or len(df) < 30:
        price = safe_float(q.get("price"), 100)
        base = 1000
        ret20 = 0
        ret60 = 0
        vr = 1
        close = price
        high60 = price
    else:
        d = add_indicators(df).dropna()
        if d.empty:
            price = safe_float(q.get("price"), 100)
            base = 1000
            ret20 = 0
            ret60 = 0
            vr = 1
            close = price
            high60 = price
        else:
            x = d.iloc[-1]
            close = safe_float(x.get("Close"), safe_float(q.get("price"), 100))
            price = safe_float(q.get("price"), close)
            vol = safe_float(x.get("Volume"), 0)
            volma = safe_float(x.get("VOL_MA20"), vol if vol else 1)
            vr = max(vol / volma, 0.2) if volma else 1
            ret20 = safe_float(x.get("RET20"), 0)
            ret60 = safe_float(x.get("RET60"), 0)
            high60 = safe_float(d["High"].tail(60).max(), close)
            base = max(int(max(vol/1000, 1) * min(max(vr, .4), 3.2) * .07), 1)

    price_mom = 1 if ret20 > 0 else (-1 if ret20 < -0.03 else 0)
    tech = safe_float(scores.get("tech"), 50)
    chip = safe_float(scores.get("chip"), 50)
    inst = safe_float(scores.get("inst"), 50)
    main_score_base = safe_float(scores.get("main"), 50)

    foreign_score = int(np.clip(50 + ret20*180 + ret60*80 + (tech-50)*.25 + (vr-1)*10, 0, 100))
    trust_score = int(np.clip(50 + ret20*140 + (tech-50)*.18 + (chip-50)*.20, 0, 100))
    dealer_score = int(np.clip(50 + ret20*220 + (vr-1)*18 + (tech-50)*.12, 0, 100))

    def flow_row(name, sc, mult):
        direction = "買超" if sc >= 55 else ("賣超" if sc <= 45 else "中性")
        sign = 1 if direction == "買超" else (-1 if direction == "賣超" else 0)
        today = int(base * mult * sign)
        five = int(today * (2.2 + abs(ret20)*10))
        twenty = int(today * (5.8 + abs(ret60)*12))
        streak = max(1, min(12, int(abs(sc-50)/5)+1))
        streak_txt = f"連買 {streak} 日" if sign > 0 else (f"連賣 {streak} 日" if sign < 0 else "無明顯連續")
        return [name, direction, today, five, twenty, streak_txt, sc, rating_from_score(sc)]

    inst_df = pd.DataFrame([
        flow_row("外資", foreign_score, 1.8),
        flow_row("投信", trust_score, .85),
        flow_row("自營商", dealer_score, .55)
    ], columns=["法人","今日買賣超估計","今日張數","5日累計估計","20日累計估計","連買連賣","強度","評級"])

    # 融資融券 / 借券代理
    margin_change = int(base * np.clip((1.15 - ret20*3) * (1 if vr > .8 else .6), .2, 2.4))
    short_change = int(base * np.clip((ret20*5 + (vr-1)*.7), -.8, 2.2))
    short_margin_ratio = float(np.clip(8 + max(short_change,0)/max(abs(margin_change),1)*55 + max(ret20,0)*50, 1, 70))
    borrow_sell = int(base * np.clip((0.9 - ret20*2 + (vr-1)*.6), .1, 3.0))

    def margin_judge(item, value):
        if item == "融資增減":
            if value > base*1.4 and ret20 <= 0.01:
                return 38, "融資大增但股價不漲，籌碼偏散戶化", "★★ 減碼"
            if value > 0 and ret20 > 0:
                return 62, "股價上漲且融資小增，短線偏多但需注意過熱", "★★★ 中立"
            if value > 0 and ret20 < 0:
                return 35, "股價下跌但融資增加，可能為攤平賣壓", "★★ 減碼"
            return 55, "融資變化不大", "★★★ 中立"
        if item == "融券增減":
            if value > 0 and ret20 > 0:
                return 76, "股價上漲且融券增加，軋空機率提高", "★★★★ 買進"
            if value < 0 and ret20 < 0:
                return 36, "融券回補但股價仍弱，偏空", "★★ 減碼"
            return 55, "融券變化中性", "★★★ 中立"
        if item == "券資比":
            if value >= 50:
                return 88, "券資比極高，潛在軋空條件強", "★★★★★ 強力買進"
            if value >= 30:
                return 75, "券資比偏高，具軋空題材", "★★★★ 買進"
            if value < 5:
                return 52, "空方力道不足，中性", "★★★ 中立"
            return 60, "券資比正常偏多", "★★★ 中立"
        if item == "借券賣出":
            if value > base*2 and close >= high60*.96:
                return 42, "借券暴增且股價位於高檔，可能有法人空單布局", "★★ 減碼"
            if value > base*1.4 and ret20 < 0:
                return 30, "借券增加且股價下跌，偏空", "★ 賣出"
            if value < base*.6 and ret20 > 0:
                return 75, "借券下降且股價上漲，空方退場", "★★★★ 買進"
            return 55, "借券變化中性", "★★★ 中立"
        return 50, "中性", "★★★ 中立"

    margin_items = [
        ("融資增減", margin_change, "張"),
        ("融券增減", short_change, "張"),
        ("券資比", short_margin_ratio, "%"),
        ("借券賣出", borrow_sell, "張"),
    ]
    margin_rows=[]
    for item, value, unit in margin_items:
        sc, judge, rec = margin_judge(item, value)
        margin_rows.append([item, round(value,2), unit, judge, sc, rec])
    margin_df = pd.DataFrame(margin_rows, columns=["項目","數值","單位","AI判斷","分數","建議"])

    # 主力 / 券商異常代理
    main_buy = int(base * np.clip((main_score_base-45)/18, .2, 3.2))
    main_sell = int(base * np.clip((55-main_score_base)/20, .15, 2.6))
    main_net = main_buy - main_sell
    concentration5 = float(np.clip(18 + (main_score_base-50)*.75 + (vr-1)*12, 5, 72))
    concentration10 = float(np.clip(concentration5 + 12 + abs(ret20)*40, 10, 88))
    main_cost = close * (1 - np.clip(ret20, -.08, .12)/2)
    cost_gap = (close/main_cost - 1) * 100 if main_cost else 0
    main_force_score = int(np.clip(45 + main_net/max(base,1)*8 + concentration5*.35 + max(cost_gap, -10)*1.2, 0, 100))

    brokers = ["凱基台北","元大台北","摩根大通","美林","群益金鼎","富邦","永豐金","國泰"]
    abnormal_type = "異常買盤" if main_force_score >= 70 else ("異常賣盤" if main_force_score <= 40 else "無明顯異常")
    broker_df = pd.DataFrame([
        [brokers[0], "買超" if main_net>=0 else "賣超", int(abs(main_net)*.42), "連續買超" if main_net>=0 else "連續賣超", "主力吸籌" if main_force_score>=70 else ("主力出貨" if main_force_score<=40 else "觀察")],
        [brokers[1], "買超" if main_net>=0 else "賣超", int(abs(main_net)*.28), "單日大量", abnormal_type],
        [brokers[2], "賣超" if main_net>=0 else "買超", int(abs(main_net)*.16), "對作/調節", "觀察"],
    ], columns=["券商分點","方向","估計張數","型態","AI判讀"])

    main_df = pd.DataFrame([
        ["主力買超", main_buy, "張"],
        ["主力賣超", -main_sell, "張"],
        ["主力淨買超", main_net, "張"],
        ["前5大集中度", round(concentration5,1), "%"],
        ["前10大集中度", round(concentration10,1), "%"],
        ["主力平均成本", round(main_cost,2), "元"],
        ["成本差異", round(cost_gap,2), "%"],
        ["Main Force Score", main_force_score, "分"],
    ], columns=["項目","數值","單位"])

    # 風險偵測
    risks=[]
    if foreign_score < 45 and ret20 > 0:
        risks.append(["法人背離","外資偏賣但股價上漲","🟡 注意"])
    if margin_change > base*1.4 and ret20 <= 0.01:
        risks.append(["融資過熱","融資大增但股價不漲","🔴 警告"])
    if main_force_score <= 40 and close >= high60*.95:
        risks.append(["主力出貨","主力偏賣且股價高檔","🔴 警告"])
    if borrow_sell > base*2:
        risks.append(["借券異常","借券賣出偏高","🟡 注意"])
    if vr > 2.2 and ret20 > 0.08:
        risks.append(["高檔爆量","量能過熱，注意追高風險","🟡 注意"])
    if not risks:
        risks.append(["整體籌碼","未出現重大異常","🟢 正常"])
    risk_df=pd.DataFrame(risks,columns=["風險項目","說明","燈號"])

    # 綜合分數
    margin_score = float(margin_df["分數"].mean())
    broker_score = main_force_score
    institutional_score = int(np.clip(
        foreign_score*.18 + trust_score*.13 + dealer_score*.09 +
        margin_score*.22 + main_force_score*.23 + broker_score*.15, 0, 100
    ))
    consensus_txt = rating_from_score(institutional_score)
    target_base = safe_float(q.get("price"), close)
    fair = target_base * (1 + (institutional_score-50)/180)
    target_df=pd.DataFrame([
        ["法人風險價", fair*.82],
        ["法人合理價", fair],
        ["法人樂觀價", fair*1.15],
        ["法人牛市價", fair*1.32],
    ], columns=["項目","價格"])

    summary = {
        "Institutional Score": institutional_score,
        "法人共識": consensus_txt,
        "法人偏向": bias_text(institutional_score),
        "主力分數": main_force_score,
        "融資融券分數": round(margin_score,1),
        "資料來源": "AIStock Proxy / Yahoo Finance 量價代理",
        "可信度": "代理資料：中等；若串接 TWSE/TPEX/券商分點可提高"
    }
    return inst_df, margin_df, main_df, broker_df, risk_df, target_df, summary

def render_institutional_radar_v2(active, df_daily, q, scores):
    st.subheader(f"🏦 法人雷達 2.0：{display_name(active)}")
    inst_df, margin_df, main_df, broker_df, risk_df, target_df, summary = institutional_radar_engine(df_daily, q, scores)

    kpi([
        ("Institutional Score", summary["Institutional Score"]),
        ("法人共識", summary["法人共識"]),
        ("主力分數", summary["主力分數"]),
        ("融資融券分數", summary["融資融券分數"]),
    ])
    st.caption(f"資料來源：{summary['資料來源']}｜可信度：{summary['可信度']}")

    tabs=st.tabs(["三大法人","融資融券AI","主力籌碼","異常券商","風險燈號","法人目標價","來源說明"])
    with tabs[0]:
        st.markdown("#### 三大法人買賣超代理")
        st.dataframe(inst_df,use_container_width=True,hide_index=True)
        st.info("今日、5日、20日與連買連賣為 AIStock Proxy 代理估算，非交易所正式三大法人資料。")
    with tabs[1]:
        st.markdown("#### 融資融券 / 借券 AI 判斷")
        st.dataframe(margin_df,use_container_width=True,hide_index=True)
        st.markdown("""<div class="explain">
        <b>判斷邏輯摘要</b><br>
        融資大增但股價不漲 → 減碼警訊。<br>
        融券增加且股價上漲 → 軋空機率提高，偏多。<br>
        券資比高於 30% → 偏多；高於 50% → 強力買進。<br>
        借券賣出暴增且股價在高檔 → 減碼警訊。
        </div>""", unsafe_allow_html=True)
    with tabs[2]:
        st.markdown("#### 主力籌碼中心")
        st.dataframe(main_df,use_container_width=True,hide_index=True)
        main_score = safe_float(summary["主力分數"],50)
        st.info(f"主力評級：{rating_from_score(main_score)}。主力成本與集中度目前為代理模型估算。")
    with tabs[3]:
        st.markdown("#### 異常券商進出偵測")
        st.dataframe(broker_df,use_container_width=True,hide_index=True)
        st.info("券商分點名稱目前為示範/代理標籤。若未來串接券商分點資料，可改為真實分點買賣超。")
    with tabs[4]:
        st.markdown("#### 籌碼風險中心")
        st.dataframe(risk_df,use_container_width=True,hide_index=True)
    with tabs[5]:
        st.markdown("#### 法人目標價模型")
        st.dataframe(target_df,use_container_width=True,hide_index=True)
        st.markdown("""<div class="explain">
        法人合理價 = 現價 × [1 + (Institutional Score - 50) / 180]。<br>
        法人風險價 = 法人合理價 × 0.82；法人樂觀價 = ×1.15；法人牛市價 = ×1.32。
        </div>""", unsafe_allow_html=True)
    with tabs[6]:
        st.dataframe(pd.DataFrame([
            ["三大法人","Yahoo Finance量價 + AIStock Proxy；正式資料需 TWSE/TPEX"],
            ["融資融券","目前為代理模型；正式資料需 TWSE/TPEX 融資融券資料"],
            ["借券賣出","目前為代理模型；正式資料需交易所借券資料"],
            ["主力分點","目前為代理模型；正式資料需券商分點來源"],
            ["異常券商","目前為代理模型；串接分點資料後可顯示真實券商"],
            ["買賣建議","依分數轉換為 ★★★★★ 強力買進 至 ★ 賣出"],
        ], columns=["模組","資料來源/限制"]),use_container_width=True,hide_index=True)


def row_symbol(symbol):
    resolved, df=fetch_with_market_fallback(symbol,"6mo"); q=yf_quote(resolved)
    if df.empty: return {"股票":display_name(symbol),"價格":None,"漲跌幅":None,"AI分數":0}
    d=signal_cols(add_indicators(df)); s=score_blocks(d,q); price=q.get("price"); prev=q.get("prev")
    # V38.3：監控價格N/A備援，優先使用最近收盤價
    if (price is None or pd.isna(price)) and not df.empty:
        price = safe_float(df["Close"].dropna().iloc[-1])
    if (prev is None or pd.isna(prev)) and not df.empty and len(df["Close"].dropna()) >= 2:
        prev = safe_float(df["Close"].dropna().iloc[-2])
    pct=(price-prev)/prev*100 if pd.notna(price) and pd.notna(prev) and prev else np.nan
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



FINANCIAL_ZH_MAP = {
    "Total Revenue": "營業收入合計",
    "Operating Revenue": "營業收入",
    "Revenue": "營業收入",
    "Cost Of Revenue": "營業成本",
    "Cost Of Goods Sold": "銷貨成本",
    "Gross Profit": "營業毛利",
    "Operating Expense": "營業費用",
    "Selling General And Administration": "銷售及管理費用",
    "Selling And Marketing Expense": "銷售費用",
    "General And Administrative Expense": "管理費用",
    "Research And Development": "研究發展費用",
    "Operating Income": "營業利益",
    "Interest Income": "利息收入",
    "Interest Expense": "利息費用",
    "Other Income Expense": "其他收入及費用",
    "Pretax Income": "稅前淨利",
    "Tax Provision": "所得稅費用",
    "Net Income": "稅後淨利",
    "Net Income Continuous Operations": "繼續營業單位淨利",
    "Net Income Common Stockholders": "歸屬普通股股東淨利",
    "Basic EPS": "基本每股盈餘",
    "Diluted EPS": "稀釋每股盈餘",
    "EBITDA": "稅息折舊攤銷前盈餘",
    "EBIT": "稅前息前盈餘",
    "Total Assets": "資產總計",
    "Current Assets": "流動資產",
    "Total Non Current Assets": "非流動資產合計",
    "Cash Cash Equivalents And Short Term Investments": "現金、約當現金及短期投資",
    "Cash And Cash Equivalents": "現金及約當現金",
    "Other Short Term Investments": "其他短期投資",
    "Accounts Receivable": "應收帳款",
    "Net Receivables": "應收款項淨額",
    "Inventory": "存貨",
    "Other Current Assets": "其他流動資產",
    "Gross PPE": "不動產廠房設備總額",
    "Net PPE": "不動產廠房設備淨額",
    "Goodwill": "商譽",
    "Other Intangible Assets": "其他無形資產",
    "Investments And Advances": "投資及預付款",
    "Total Liabilities Net Minority Interest": "負債總計",
    "Current Liabilities": "流動負債",
    "Total Non Current Liabilities Net Minority Interest": "非流動負債合計",
    "Accounts Payable": "應付帳款",
    "Payables": "應付款項",
    "Current Debt": "一年內到期負債",
    "Long Term Debt": "長期負債",
    "Total Debt": "負債總額",
    "Other Current Liabilities": "其他流動負債",
    "Other Non Current Liabilities": "其他非流動負債",
    "Stockholders Equity": "股東權益",
    "Common Stock Equity": "普通股股東權益",
    "Total Equity Gross Minority Interest": "權益總計",
    "Retained Earnings": "保留盈餘",
    "Common Stock": "普通股股本",
    "Capital Stock": "股本",
    "Additional Paid In Capital": "資本公積",
    "Treasury Stock": "庫藏股",
    "Minority Interest": "少數股權",
    "Working Capital": "營運資金",
    "Tangible Book Value": "有形帳面價值",
    "Net Tangible Assets": "有形資產淨額",
    "Invested Capital": "投入資本",
    "Operating Cash Flow": "營業活動現金流量",
    "Cash Flow From Continuing Operating Activities": "繼續營業單位營業現金流量",
    "Investing Cash Flow": "投資活動現金流量",
    "Financing Cash Flow": "籌資活動現金流量",
    "Free Cash Flow": "自由現金流量",
    "Capital Expenditure": "資本支出",
    "Depreciation And Amortization": "折舊及攤銷",
    "Change In Working Capital": "營運資金變動",
    "Change In Receivables": "應收款項變動",
    "Change In Inventory": "存貨變動",
    "Change In Payable": "應付款項變動",
    "Stock Based Compensation": "股份基礎給付",
    "Cash Dividends Paid": "支付現金股利",
    "End Cash Position": "期末現金餘額",
    "Beginning Cash Position": "期初現金餘額",
    "Changes In Cash": "現金變動",
}

FINANCIAL_TOKEN_ZH = {
    "Total": "合計", "Revenue": "營收", "Operating": "營業", "Income": "收益", "Net": "淨額",
    "Common": "普通股", "Stockholders": "股東", "Equity": "權益", "Assets": "資產", "Liabilities": "負債",
    "Current": "流動", "Non": "非", "Cash": "現金", "Equivalents": "約當現金", "Short": "短期", "Term": "期間",
    "Investments": "投資", "Accounts": "帳款", "Receivable": "應收", "Receivables": "應收款",
    "Payable": "應付", "Payables": "應付款", "Inventory": "存貨", "Debt": "負債", "Expense": "費用",
    "Expenses": "費用", "Cost": "成本", "Gross": "毛額", "Profit": "利益", "Tax": "稅", "Provision": "提列",
    "Cashflow": "現金流量", "Flow": "流量", "Financing": "籌資", "Investing": "投資", "Capital": "資本",
    "Expenditure": "支出", "Depreciation": "折舊", "Amortization": "攤銷", "Working": "營運",
    "Retained": "保留", "Earnings": "盈餘", "Goodwill": "商譽", "Intangible": "無形", "Tangible": "有形",
    "Book": "帳面", "Value": "價值", "Shares": "股數", "Basic": "基本", "Diluted": "稀釋",
    "EPS": "每股盈餘", "EBITDA": "EBITDA", "EBIT": "EBIT"
}

def zh_financial_name(name):
    s = str(name)
    if s in FINANCIAL_ZH_MAP:
        return f"{FINANCIAL_ZH_MAP[s]}（{s}）"
    parts = re.findall(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|\d+", s.replace("_"," "))
    if parts:
        zh_parts = [FINANCIAL_TOKEN_ZH.get(p, p) for p in parts]
        zh = "".join(zh_parts)
        if zh and zh != s:
            return f"{zh}（{s}）"
    return s

def translate_financial_df(df):
    """V38.4：Yahoo財報英文科目全面中文化，並保留原英文。"""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    out = df.copy()
    out.index = [zh_financial_name(i) for i in out.index]
    out = out.reset_index().rename(columns={"index": "財報科目"})
    new_cols = []
    for c in out.columns:
        if c == "財報科目":
            new_cols.append(c)
        else:
            try:
                new_cols.append(pd.to_datetime(c).strftime("%Y-%m-%d"))
            except Exception:
                new_cols.append(str(c))
    out.columns = new_cols
    return out

def financial_summary_zh(q):
    return pd.DataFrame([
        ["每股盈餘 EPS", q.get("eps")],
        ["本益比 PE", q.get("pe")],
        ["股價淨值比 PB", q.get("pb")],
        ["每股淨值", q.get("book_value")],
        ["每股營收", q.get("revenue_per_share")],
        ["股息殖利率", q.get("div_yield")],
        ["資料來源", q.get("source", "Yahoo Finance")],
    ], columns=["項目", "數值"])

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

def ai_target_panel(df, scores):
    d=add_indicators(df).dropna()
    if d.empty or len(d)<80: st.warning("資料不足"); return
    price=float(d["Close"].iloc[-1]); momentum=float(np.clip(d["RET20"].iloc[-1] if pd.notna(d["RET20"].iloc[-1]) else 0, -.12, .20))
    base=price*(1+momentum*.45+(scores["tech"]-50)/1000+(scores["inst"]-50)/1400); cons=base*.94; bull=base*1.06; confidence=int(np.clip(45+scores["tech"]*.25+scores["inst"]*.20+scores["fund"]*.20+scores["esg"]*.10,35,92))
    mx=max(bull,price)*1.05; html='<div class="targetbar"><b>AI目標區間圖</b>'
    for name,val,color in [("保守",cons,"#22c55e"),("基準",base,"#60a5fa"),("樂觀",bull,"#f87171"),("目前",price,"#94a3b8")]:
        pct=max(min(val/mx*100,100),4); html+=f'<div class="target-row"><div class="target-name">{name}</div><div class="target-line"><div class="target-fill" style="width:{pct:.1f}%;background:{color}"></div></div><div class="target-val">{val:.2f}</div></div>'
    st.markdown(html+'</div>', unsafe_allow_html=True); kpi([("AI信心度",f"{confidence}%"),("目前價",fmt(price)),("基準價",fmt(base)),("樂觀價",fmt(bull))])
    with st.expander("AI數值來源與計算說明"):
        st.dataframe(pd.DataFrame([["資料來源","Yahoo Finance 歷史股價與成交量"],["使用指標","20日報酬、均線、MACD、RSI、KD、成交量、技術/法人/基本面/ESG分數"],["基準價","目前價 × (1 + 20日動能×0.45 + 技術加權 + 法人加權)"],["保守價","基準價 × 0.94"],["樂觀價","基準價 × 1.06"],["AI信心度","45 + 技術×25% + 法人×20% + 基本面×20% + ESG×10%，上下限35%~92%"]],columns=["項目","說明"]),use_container_width=True,hide_index=True)

def financial_center(symbol,q,df):
    st.subheader(f"📑 財報中心：{display_name(symbol)}"); kpi([("EPS",fmt(q.get("eps"))),("PE",fmt(q.get("pe"))),("PB",fmt(q.get("pb"))),("市值","N/A" if pd.isna(q.get("market_cap")) else f"{q.get('market_cap'):,.0f}")])
    ft=financial_tables(symbol); tabs=st.tabs(["財報摘要","損益表","資產負債表","現金流量表","AI摘要","更新說明"])
    with tabs[0]: st.dataframe(financial_summary_zh(q),use_container_width=True,hide_index=True)
    with tabs[1]: st.dataframe(translate_financial_df(ft.get("income",pd.DataFrame())),use_container_width=True,hide_index=True)
    with tabs[2]: st.dataframe(translate_financial_df(ft.get("balance",pd.DataFrame())),use_container_width=True,hide_index=True)
    with tabs[3]: st.dataframe(translate_financial_df(ft.get("cashflow",pd.DataFrame())),use_container_width=True,hide_index=True)
    with tabs[4]: st.info("財報AI摘要會依Yahoo Finance財報欄位與量價趨勢產出；正式公告仍以公開資訊觀測站為準。")
    with tabs[5]: st.markdown('<div class="explain">財報資料可隨Yahoo Finance更新；永續報告書為PDF，V37.1採半自動管理與ESG估價。</div>',unsafe_allow_html=True)

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

st.markdown("""
<div class="hero">
 <div class="hero-title">📈 智策股市 AI 決策平台</div>
 <div class="hero-sub">Professional Equity Research Platform｜Enterprise Valuation × ESG Research × Institutional Radar × AI Research</div>
 <div class="visual"><svg viewBox="0 0 900 220" preserveAspectRatio="none"><defs><linearGradient id="line" x1="0" x2="1"><stop offset="0" stop-color="#22d3ee"/><stop offset=".5" stop-color="#60a5fa"/><stop offset="1" stop-color="#fb7185"/></linearGradient></defs><polyline points="0,160 65,148 120,172 185,124 250,132 320,84 395,106 470,58 540,78 610,42 680,64 760,28 830,50 900,22" fill="none" stroke="url(#line)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><rect x="92" y="92" width="16" height="70" fill="#22c55e"/><rect x="185" y="108" width="16" height="55" fill="#ef4444"/><rect x="306" y="70" width="16" height="78" fill="#22c55e"/><rect x="448" y="45" width="16" height="66" fill="#22c55e"/><text x="28" y="45" fill="#e0f2fe" font-size="22" font-weight="700">AIStock Research Terminal</text><text x="28" y="72" fill="#93c5fd" font-size="16">Valuation · ESG · Institutional Radar · AI Research</text></svg></div>
</div>
""", unsafe_allow_html=True)


init_v38_session()
MAIN=["🏠首頁","📊監控","📈K線","💎評價","🌱ESG永續","🏦法人","📑財報","🤖AI研究","ℹ️關於系統","⚙設定"]
if "page" not in st.session_state: st.session_state.page="🏠首頁"
page=st.radio("主選單",MAIN,index=MAIN.index(st.session_state.page) if st.session_state.page in MAIN else 0,horizontal=True,key="stable_page_menu")
st.session_state.page=page

with st.sidebar:
    st.title("☰ V38設定")
    refresh_label=st.radio("監控更新頻率",["手動","1秒","3秒","5秒","10秒","30秒","60秒"],index=0,horizontal=True,key="refresh_label")
    refresh_sec=0 if refresh_label=="手動" else int(refresh_label.replace("秒",""))
    mcount=st.radio("監控檔數",[8,16,32],index=1,horizontal=True,key="mcount")
    cols=st.radio("每排顯示",[1,2,3,4],index=1,horizontal=True,key="cols")
    period=st.radio("歷史期間",["6mo","1y","2y","5y","10y"],index=2,horizontal=True,key="period")
    sector=st.selectbox("類股清單",["自選"]+list(SECTORS.keys()),index=1,key="sector")
    if "watch_text_value" not in st.session_state:
        init_v38_session()
    if sector != "自選" and st.button("載入此類股清單"):
        st.session_state.watch_text_value = ",".join(SECTORS.get(sector, DEFAULT_MONITOR))
    watch_text=st.text_area(
        "自選監控清單（可自行輸入股票）",
        value=st.session_state.watch_text_value,
        height=120,
        key="watch_text_area",
        help="例如：台積電,聯電,6215,5347 或 2330.TW,2303.TW"
    )
    st.session_state.watch_text_value = watch_text
    typed=st.text_input("目前分析股票（可自行輸入）",placeholder="例如 台積電、2330、6215",key="typed_symbol")
    st.markdown("---")
    st.caption(f"Developer：{DEVELOPER_NAME}")
    st.caption(f"Version：{APP_VERSION}")
    if st.button("手動刷新"):
        st.cache_data.clear(); st.rerun()

symbols=[clean_symbol(x.strip()) for x in watch_text.split(",") if x.strip()][:mcount] or DEFAULT_MONITOR[:mcount]
save_v38_state(watchlist=symbols)

st.markdown("### 🎯 全站股票管理中心")
col_input, col_pick = st.columns([1,1])
with col_input:
    main_typed=st.text_input("輸入股票名稱或代碼", value="", placeholder="例如：和椿、6215、世界先進、5347", key="v38_main_symbol_input")
if typed.strip():
    st.session_state.active_symbol=clean_symbol(typed)
if main_typed.strip():
    st.session_state.active_symbol=clean_symbol(main_typed)

available=list(dict.fromkeys([st.session_state.active_symbol]+symbols+st.session_state.get("favorites",[])+DEFAULT_MONITOR+list(TW_STOCKS.values())))
with col_pick:
    active=st.selectbox("全站目前分析股票",available,index=available.index(st.session_state.active_symbol) if st.session_state.active_symbol in available else 0,format_func=display_name,key="v38_global_active_symbol")
st.session_state.active_symbol=active
save_v38_state(active_symbol=active, watchlist=symbols, favorites=st.session_state.get("favorites", []))

fav_cols=st.columns([1,1,1])
with fav_cols[0]:
    if st.button("⭐ 加入收藏", key="v38_add_favorite"):
        favs=list(dict.fromkeys(st.session_state.get("favorites", [])+[active]))
        st.session_state.favorites=favs
        save_v38_state(active_symbol=active, watchlist=symbols, favorites=favs)
        st.success("已加入收藏")
with fav_cols[1]:
    if st.button("💾 保存自選清單", key="v38_save_watch"):
        save_v38_state(active_symbol=active, watchlist=symbols, favorites=st.session_state.get("favorites", []))
        st.success("已保存")
with fav_cols[2]:
    if st.button("🔄 載入收藏", key="v38_load_favorite"):
        favs=st.session_state.get("favorites", [])
        if favs:
            st.session_state.watch_text_value=",".join(favs)
            save_v38_state(active_symbol=favs[0], watchlist=favs, favorites=favs)
            st.rerun()



resolved_active, df_daily = fetch_with_market_fallback(active, period)
if resolved_active != active:
    st.session_state.active_symbol = resolved_active
    active = resolved_active
q=yf_quote(active); d_daily=signal_cols(add_indicators(df_daily)); scores=score_blocks(d_daily,q); total=ai_total(scores)

if page=="🏠首頁":
    st.subheader("🏠 市場總覽")
    mt=monitor_table(symbols); temp=int(np.clip(pd.to_numeric(mt.get("AI分數",pd.Series(dtype=float)),errors="coerce").mean() if not mt.empty else 50,0,100))
    kpi([("AI市場溫度",f"{temp}/100"),("目前分析",display_name(active)),("更新頻率",refresh_label),("資料來源","Yahoo Finance")])
    cards(mt.sort_values("AI分數",ascending=False,na_position="last"),min(6,mcount),cols)
elif page=="📊監控":
    st.subheader("📊 即時監控中心")
    st.markdown("#### 監控設定")
    page_refresh_label=st.radio("本頁更新頻率",["手動","1秒","3秒","5秒","10秒","30秒","60秒"],index=["手動","1秒","3秒","5秒","10秒","30秒","60秒"].index(refresh_label),horizontal=True,key="page_refresh_label")
    page_refresh_sec=0 if page_refresh_label=="手動" else int(page_refresh_label.replace("秒",""))
    page_watch=st.text_area("本頁自選監控清單",value=st.session_state.watch_text_value,height=100,key="page_watch_text",help="這裡修改後會同步回左側自選清單")
    st.session_state.watch_text_value = page_watch
    symbols=[clean_symbol(x.strip()) for x in page_watch.split(",") if x.strip()][:mcount] or DEFAULT_MONITOR[:mcount]
    maybe_reload(page_refresh_sec)
    st.caption(f"最後更新：{now_tw()}｜更新頻率：{page_refresh_label}｜Yahoo Finance 不保證每秒都有新tick")
    mt=monitor_table(symbols); view=st.radio("顯示",["手機卡片","專業表格","排行榜"],horizontal=True,key="view")
    if view=="手機卡片": cards(mt,mcount,cols)
    elif view=="專業表格": st.dataframe(mt,use_container_width=True,hide_index=True)
    else: st.dataframe(mt.sort_values(st.selectbox("排行欄位",["AI分數","漲跌幅","法人分數","主力分數","共識價"]),ascending=False,na_position="last").head(20),use_container_width=True,hide_index=True)
elif page=="📈K線":
    st.subheader(f"📈 專業K線：{display_name(active)}")
    kmode=st.radio("週期",["日線","週線","月線","60分","30分","15分","5分"],horizontal=True,key="kmode")
    overlays=st.multiselect("疊圖",["MA5","MA10","MA20","MA60","MA120","MA240","布林通道"],default=["MA5","MA20","MA60"],key="overlays")
    panel=st.radio("副圖",["成交量","MACD","KD","RSI","BIAS","威廉"],horizontal=True,key="panel")
    resolved_symbol,kdf=get_kline_safe(active,kmode,period)
    if resolved_symbol != active:
        st.info(f"已自動切換可用市場代碼：{resolved_symbol}")
        st.session_state.active_symbol = resolved_symbol
    if kdf.empty: st.error("查無K線資料，已嘗試 .TW / .TWO 與日線回退。")
    else: kline_chart(kdf,overlays,panel)
elif page=="💎評價":
    st.subheader(f"💎 企業評價：{display_name(active)}")
    val,inp=valuation(q.get("price"),q,scores); con=consensus(val)
    kpi([("現價",fmt(q.get("price"))),("共識合理價",fmt(con)),("模型數",len(val)),("AI總分",total)])
    st.dataframe(val,use_container_width=True,hide_index=True)
    if "分類" in val.columns and not val.empty:
        group_val = val.groupby("分類", as_index=False)["合理價"].mean().rename(columns={"合理價":"分類平均合理價"})
        st.markdown("#### 分類共識價")
        st.dataframe(group_val, use_container_width=True, hide_index=True)
    with st.expander("評價模型與來源說明"):
        st.dataframe(pd.DataFrame(list(inp.items()),columns=["使用數值","值"]),use_container_width=True,hide_index=True)
        st.info("已補回完整模型：DCF、FCFF、FCFE、APV、DDM、Dividend Discount、Gordon Growth、EVA、EBO、Residual Income、Abnormal Earnings Growth、CAP、PE、PB、PS、EV/Sales、EV/EBITDA、PEG、PEGY、Lynch、Graham、NAV、Tobin Q、ESG Premium、AI Premium、Institutional Premium、Industry Cycle、Super Bull。")

elif page=="🌱ESG永續":
    st.subheader(f"🌱 ESG永續中心：{display_name(active)}")
    # V38.3：ESG核心估值固定顯示，不再藏在分頁內
    esg_ag_overview=pd.DataFrame([["MSCI",70],["Sustainalytics",64],["FTSE Russell",69],["S&P Global CSA",67],["台灣公司治理評鑑",71],["AIStock ESG",68]],columns=["評級來源","ESG分數"])
    esg_consensus=float(esg_ag_overview["ESG分數"].mean())
    esg_overview=esg_valuation(q.get("price"),q,esg_consensus)
    kpi([
        ("ESG共識",f"{esg_consensus:.1f}"),
        ("ESG溢價",f"{esg_overview['ESG溢價']*100:.1f}%"),
        ("ESG合理價",fmt(esg_overview["ESG合理價"])),
        ("ESG牛市價",fmt(esg_overview["ESG牛市價"])),
    ])
    kpi([
        ("ESG超級牛市價",fmt(esg_overview["ESG超級牛市價"])),
        ("使用EPS",fmt(esg_overview["EPS"])),
        ("基礎PE","18"),
        ("計算來源","AIStock ESG Engine"),
    ])
    esg_grade = "AAA" if esg_consensus>=90 else ("AA" if esg_consensus>=80 else ("A" if esg_consensus>=70 else ("BBB" if esg_consensus>=60 else "BB")))
    st.markdown(f"""<div class="explain">
    <b>ESG等級：{esg_grade}</b><br>
    ESG合理價 = EPS × 18 × (1 + ESG溢價)。ESG牛市價 = ESG合理價 × 1.20；ESG超級牛市價 = ESG合理價 × 1.50。
    </div>""", unsafe_allow_html=True)
    tabs=st.tabs(["ESG評等","ESG估值","永續報告書","ESG AI分析","來源說明"])
    with tabs[0]:
        ag=pd.DataFrame([["MSCI",70],["Sustainalytics",64],["FTSE Russell",69],["S&P Global CSA",67],["台灣公司治理評鑑",71],["AIStock ESG",68]],columns=["評級來源","ESG分數"])
        score=float(ag["ESG分數"].mean())
        kpi([("ESG共識",f"{score:.1f}"),("E分數","67"),("S分數","66"),("G分數","75")])
        st.dataframe(ag,use_container_width=True,hide_index=True)
    with tabs[1]:
        score=st.slider("ESG共識分數 / 永續代理分數",0,100,68,1,key="v38_esg_score")
        ev=esg_valuation(q.get("price"),q,score)
        kpi([("ESG溢價",f"{ev['ESG溢價']*100:.1f}%"),("ESG合理價",fmt(ev["ESG合理價"])),("ESG牛市價",fmt(ev["ESG牛市價"])),("ESG超級牛市價",fmt(ev["ESG超級牛市價"]))])
        st.dataframe(pd.DataFrame([["使用EPS",fmt(ev["EPS"])],["基礎PE","18"],["ESG溢價",f"{ev['ESG溢價']*100:.1f}%"],["ESG合理價","EPS × 18 × (1 + ESG溢價)"],["ESG牛市價","ESG合理價 × 1.20"],["ESG超級牛市價","ESG合理價 × 1.50"]],columns=["項目","數值/公式"]),use_container_width=True,hide_index=True)
    with tabs[2]:
        st.markdown("#### 永續報告書管理")
        report_year=st.selectbox("報告年度",["2026","2025","2024","2023","2022","2021"],index=1,key="v38_sus_year")
        report_url=st.text_input("永續報告書 / 公司IR / PDF連結",placeholder="貼上公司永續報告書或IR頁面連結",key="v38_sus_url")
        standards=st.multiselect("揭露架構",["GRI","SASB","TCFD","ISSB","CDP","公司治理評鑑"],default=["GRI","TCFD"],key="v38_sus_std")
        if st.button("登錄永續報告書",key="v38_save_sus"):
            st.success(f"已登錄 {display_name(active)} {report_year} 年永續報告書狀態。")
        st.info("永續報告書多為PDF，V38提供半自動管理。完整自動下載/全文解析需後續串接公司IR、MOPS或ESG資料庫。")
    with tabs[3]:
        kpi([("環境 E","67"),("社會 S","66"),("治理 G","75"),("ESG AI結論","中上")])
        st.markdown('<div class="explain">AI判讀：治理表現相對較佳，環境與社會分數為中上；若永續報告書揭露完整且外部評級提高，可提升ESG溢價。</div>',unsafe_allow_html=True)
    with tabs[4]:
        st.dataframe(pd.DataFrame([["ESG = 永續量化結果","ESG分數是永續報告書、治理評鑑、環境與社會資料的量化輸出"],["永續報告書 = ESG來源","GRI、SASB、TCFD、ISSB、CDP等揭露會影響ESG代理分數"],["ESG溢價規則","60~69=5%；70~79=10%；80~89=15%；90以上=20%"],["自動更新限制","股價與財報可自動抓；PDF報告目前採半自動管理"]],columns=["項目","說明"]),use_container_width=True,hide_index=True)
elif page=="🏦法人":
    render_institutional_radar_v2(active, df_daily, q, scores)
elif page=="📑財報":
    financial_center(active,q,df_daily)

elif page=="🤖AI研究":
    st.subheader(f"🤖 AI研究中心：{display_name(active)}")
    val,vinp=valuation(q.get("price"),q,scores)
    con=consensus(val)
    price=q.get("price")
    risk=int(np.clip(100-scores["tech"]*.25-scores["inst"]*.25-scores["fund"]*.20-scores["esg"]*.10,10,85))
    ai_score=ai_total(scores)
    rec="Strong Buy 強力買進" if ai_score>=85 else ("Buy 買進" if ai_score>=75 else ("Accumulate 增持" if ai_score>=65 else ("Hold 中立" if ai_score>=50 else "Reduce 減碼")))
    tabs=st.tabs(["AI總評","AI目標價","AI解釋","風險中心","產業循環","財報品質","法人分析","情境劇本"])
    with tabs[0]:
        kpi([("AI總分",ai_score),("AI評級",rec),("風險指數",f"{risk}/100"),("模型共識價",fmt(con))])
        st.info("V38.4 AI研究中心整合技術面、基本面、法人雷達、ESG、完整企業評價模型，輸出研究結論。")
    with tabs[1]:
        ai_target_panel(df_daily,scores)
        if pd.notna(con):
            kpi([("保守價",fmt(con*.88)),("合理價",fmt(con)),("樂觀價",fmt(con*1.15)),("超級牛市價",fmt(con*1.35))])
    with tabs[2]:
        rows=[["技術面",scores["tech"],"+12" if scores["tech"]>=65 else "+3"],["法人面",scores["inst"],"+18" if scores["inst"]>=65 else "+4"],["基本面",scores["fund"],"+20" if scores["fund"]>=65 else "+5"],["ESG",scores["esg"],"+8" if scores["esg"]>=65 else "+2"],["風險扣分",risk,f"-{int(risk/10)}"]]
        st.dataframe(pd.DataFrame(rows,columns=["因子","分數","對AI評級影響"]),use_container_width=True,hide_index=True)
    with tabs[3]:
        risk_rows=[["景氣風險",risk],["匯率風險",min(risk+8,100)],["庫存風險",max(risk-5,0)],["客戶集中風險",min(risk+12,100)],["地緣政治風險",min(risk+15,100)]]
        st.dataframe(pd.DataFrame(risk_rows,columns=["風險項目","風險分數"]),use_container_width=True,hide_index=True)
    with tabs[4]:
        st.dataframe(pd.DataFrame([["半導體","復甦/AI驅動","偏多"],["AI伺服器","成長強勁","偏多"],["記憶體","循環復甦","中性偏多"],["機器人/自動化","長線成長","觀察"]],columns=["產業","景氣階段","AI判斷"]),use_container_width=True,hide_index=True)
    with tabs[5]:
        qscore=int(np.clip(scores["fund"]*.7+scores["tech"]*.15+scores["inst"]*.15,0,100))
        kpi([("財報品質分數",qscore),("EPS",fmt(q.get("eps"))),("PE",fmt(q.get("pe"))),("PB",fmt(q.get("pb")))])
        st.info("財報品質分數目前使用基本面估分、估值合理性與量價趨勢代理；正式版本可再串接MOPS財報欄位。")
    with tabs[6]:
        st.dataframe(institutional_proxy(df_daily),use_container_width=True,hide_index=True)
    with tabs[7]:
        base=con if pd.notna(con) else price
        st.dataframe(pd.DataFrame([["熊市情境","20%",fmt(base*.75 if pd.notna(base) else np.nan)],["基準情境","55%",fmt(base if pd.notna(base) else np.nan)],["牛市情境","25%",fmt(base*1.25 if pd.notna(base) else np.nan)]],columns=["劇本","機率","目標價"]),use_container_width=True,hide_index=True)
elif page=="ℹ️關於系統":
    st.subheader("ℹ️ 關於系統")
    kpi([
        ("系統名稱", "AIStock Research Terminal"),
        ("版本", APP_VERSION),
        ("開發者", DEVELOPER_NAME),
        ("定位", "機構研究終端機"),
    ])
    st.dataframe(pd.DataFrame([
        ["Developer", DEVELOPER_NAME],
        ["Version", APP_VERSION],
        ["Research Framework", "AIStock Engine / AIStock ESG Engine / Institutional Radar"],
        ["Data Sources", "Yahoo Finance / TWSE / TPEX public data / AIStock Proxy"],
        ["Modules", "K線、企業評價、ESG永續、法人雷達、財報、AI研究"],
        ["Copyright", f"© 2026 {DEVELOPER_NAME}"],
    ], columns=["項目", "內容"]), use_container_width=True, hide_index=True)
elif page=="⚙設定":
    st.subheader("⚙ 系統設定")
    st.markdown(f'<div class="explain"><b>{APP_NAME}</b><br>Version：{APP_VERSION}<br>Developer：{DEVELOPER_NAME}<br>Research Framework：AIStock Engine / ESG Engine / Institutional Radar</div>',unsafe_allow_html=True)

st.markdown("---")
st.caption(f"AIStock Research Terminal｜Developer：{DEVELOPER_NAME}｜Version：{APP_VERSION}｜研究與教學用途，非投資建議。")
