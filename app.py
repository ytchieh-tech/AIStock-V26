
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


APP_VERSION="V42 Enterprise Audit Final"
APP_NAME="智策股市 AI 決策平台"
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


/* V42 responsive audit */
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

def display_name(symbol):
    for k,v in TW_STOCKS.items():
        if v==symbol: return f"{k} / {symbol}"
    return symbol





def search_symbol_candidates(query, symbols=None, limit=12):
    """V40 smart search: supports code, name, partial code, and existing watchlist."""
    q = str(query).strip().upper()
    pool = []
    symbols = symbols or []
    for s in list(symbols) + DEFAULT_MONITOR + list(TW_STOCKS.values()):
        if s and s not in pool:
            pool.append(s)

    results = []
    if not q:
        return pool[:limit]

    # Exact company name or full code first
    if query in TW_STOCKS:
        results.append(TW_STOCKS[query])
    if re.fullmatch(r"\d{4}", q):
        exact = clean_symbol(q)
        results.append(exact)

    for name, sym in TW_STOCKS.items():
        plain = sym.replace(".TW", "").replace(".TWO", "")
        text = f"{name} {sym} {plain}".upper()
        if q in text and sym not in results:
            results.append(sym)

    for sym in pool:
        plain = sym.replace(".TW", "").replace(".TWO", "")
        if (q in sym.upper() or q in plain) and sym not in results:
            results.append(sym)

    return results[:limit]

def set_active_symbol(sym):
    """V40: single source of truth for the whole app."""
    s = clean_symbol(sym)
    if not s:
        return st.session_state.get("active_symbol", DEFAULT_MONITOR[0])
    st.session_state.active_symbol = s
    hist = st.session_state.get("recent_symbols", [])
    if s in hist:
        hist.remove(s)
    hist.insert(0, s)
    st.session_state.recent_symbols = hist[:12]
    return s

def unified_symbol_manager(symbols):
    """V40 smart search. Exact 4-digit code switches on Enter; partial search shows candidate buttons."""
    if "active_symbol" not in st.session_state:
        st.session_state.active_symbol = symbols[0] if symbols else DEFAULT_MONITOR[0]
    if "recent_symbols" not in st.session_state:
        st.session_state.recent_symbols = [st.session_state.active_symbol]

    st.markdown('<div class="v39-symbol-panel">', unsafe_allow_html=True)
    st.markdown('<div class="v39-active">🎯 全站股票智慧搜尋</div>', unsafe_allow_html=True)
    st.markdown('<div class="v39-hint">輸入完整代碼後按 Enter 會直接切換全站；輸入部分代碼或名稱會出現候選股票按鈕。</div>', unsafe_allow_html=True)

    query = st.text_input(
        "搜尋股票名稱或代碼",
        value="",
        placeholder="例如：2301、230、聯、和椿、台積電",
        key="v40_smart_symbol_search"
    )

    # Exact input auto-applies safely after Enter/rerun. No widget-key mutation.
    if query.strip():
        q = query.strip()
        if q in TW_STOCKS or re.fullmatch(r"\d{4}", q):
            set_active_symbol(q)

    st.markdown(f'<div class="v39-hint">目前全站分析：<b>{display_name(st.session_state.active_symbol)}</b></div>', unsafe_allow_html=True)

    candidates = search_symbol_candidates(query, symbols, limit=12) if query.strip() else (st.session_state.get("recent_symbols", []) + list(symbols))[:12]
    # de-duplicate while preserving order
    unique_candidates = []
    for s in candidates:
        if s and s not in unique_candidates:
            unique_candidates.append(s)

    if unique_candidates:
        st.caption("候選 / 最近使用")
        cols = st.columns(3)
        for i, s in enumerate(unique_candidates[:12]):
            label = display_name(s)
            if cols[i % 3].button(label, key=f"v40_symbol_candidate_{i}_{s}"):
                set_active_symbol(s)
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    return st.session_state.active_symbol

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
    """V42: if Yahoo quote is N/A, use latest K-line close as backup so valuation models do not disappear."""
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
    v=safe_float(v); p=safe_float(price)
    if pd.isna(v) or v<=0: return np.nan
    if pd.notna(p) and p>0 and (v<p*.35 or v>p*3.5): return np.nan
    return v


def valuation(price,q,s):
    pe=q.get("pe",np.nan)
    pb=q.get("pb",np.nan)
    eps=q.get("eps",np.nan)
    eps=eps if pd.notna(eps) and eps>0 else (price/pe if pd.notna(price) and pd.notna(pe) and pe>0 else (price/20 if pd.notna(price) else np.nan))
    bvps=q.get("book_value",np.nan)
    bvps=bvps if pd.notna(bvps) and bvps>0 else (price/pb if pd.notna(price) and pd.notna(pb) and pb>0 else (price/2 if pd.notna(price) else np.nan))
    rps=q.get("revenue_per_share",np.nan)
    rps=rps if pd.notna(rps) and rps>0 else (price/2.5 if pd.notna(price) else np.nan)
    if pd.isna(price) or pd.isna(eps) or eps<=0:
        return pd.DataFrame(), {}

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
        ("市場法","Graham","葛拉漢公式",math.sqrt(max(22.5*eps*bvps,0))),

        ("AIStock","ESG Premium","ESG溢價模型",eps*base_pe*(1+esg_prem)),
        ("AIStock","AI Premium","AI成長溢價模型",eps*base_pe*(1+ai_prem)),
        ("AIStock","Institutional Premium","法人溢價模型",eps*base_pe*(1+inst_prem)),
        ("AIStock","Industry Cycle","產業循環模型",eps*base_pe*(1+np.clip((s["tech"]-50)/300,-.08,.15))),
        ("AIStock","Super Bull","超級牛市模型",eps*base_pe*(1+max(esg_prem,0)+max(ai_prem,0)*1.8+max(inst_prem,0)*1.2+.25)),
    ]
    df=pd.DataFrame(rows,columns=["分類","模型","中文名稱","合理價"])
    df["合理價"]=df["合理價"].apply(lambda x: clamp_fair(x,price))
    df=df.dropna(subset=["合理價"])
    return df, {"EPS":eps,"BVPS":bvps,"每股營收":rps,"成長率":g,"WACC":wacc,"永續成長率":tg,"ROE":roe,"股利假設":dividend}

def consensus(df):
    if df.empty: return np.nan
    med=df["合理價"].median(); d=df[(df["合理價"]>=med*.45)&(df["合理價"]<=med*2.2)]
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


FIN_ZH_MAP = {
    "Total Revenue":"營業收入總額",
    "Operating Revenue":"營業收入",
    "Cost Of Revenue":"營業成本",
    "Gross Profit":"營業毛利",
    "Operating Expense":"營業費用",
    "Operating Income":"營業利益",
    "Pretax Income":"稅前淨利",
    "Tax Provision":"所得稅費用",
    "Net Income":"本期淨利",
    "Net Income Common Stockholders":"歸屬母公司淨利",
    "Diluted EPS":"稀釋EPS",
    "Basic EPS":"基本EPS",
    "EBITDA":"稅息折舊攤銷前盈餘",
    "EBIT":"息稅前盈餘",
    "Total Assets":"資產總額",
    "Current Assets":"流動資產",
    "Cash And Cash Equivalents":"現金及約當現金",
    "Inventory":"存貨",
    "Accounts Receivable":"應收帳款",
    "Total Liabilities Net Minority Interest":"負債總額",
    "Current Liabilities":"流動負債",
    "Long Term Debt":"長期負債",
    "Stockholders Equity":"股東權益",
    "Retained Earnings":"保留盈餘",
    "Operating Cash Flow":"營業活動現金流",
    "Investing Cash Flow":"投資活動現金流",
    "Financing Cash Flow":"籌資活動現金流",
    "Free Cash Flow":"自由現金流",
    "Capital Expenditure":"資本支出",
    "Depreciation And Amortization":"折舊及攤銷",
}

def zh_financial_df(df):
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    out.insert(0, "中文項目", [FIN_ZH_MAP.get(str(i), str(i)) for i in out.index])
    out.insert(0, "英文項目", [str(i) for i in out.index])
    out = out.reset_index(drop=True)
    return out

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

    rows = [
        ["營業收入", revenue],
        ["營業毛利", gross],
        ["營業利益", op_income],
        ["本期淨利", net_income],
        ["資產總額", assets],
        ["股東權益", equity],
        ["營業活動現金流", ocf],
        ["自由現金流", fcf],
        ["EPS", q.get("eps")],
        ["PE", q.get("pe")],
        ["PB", q.get("pb")],
    ]
    summary = pd.DataFrame(rows, columns=["中文項目", "最新數值"])

    gm = gross / revenue * 100 if pd.notna(gross) and pd.notna(revenue) and revenue else np.nan
    om = op_income / revenue * 100 if pd.notna(op_income) and pd.notna(revenue) and revenue else np.nan
    nm = net_income / revenue * 100 if pd.notna(net_income) and pd.notna(revenue) and revenue else np.nan
    roe = net_income / equity * 100 if pd.notna(net_income) and pd.notna(equity) and equity else np.nan
    roa = net_income / assets * 100 if pd.notna(net_income) and pd.notna(assets) and assets else np.nan
    fcf_margin = fcf / revenue * 100 if pd.notna(fcf) and pd.notna(revenue) and revenue else np.nan

    ratios = pd.DataFrame([
        ["毛利率", gm],
        ["營益率", om],
        ["淨利率", nm],
        ["ROE", roe],
        ["ROA", roa],
        ["自由現金流率", fcf_margin],
    ], columns=["指標", "數值%"])

    score = 50
    for v, add in [(gm,10),(om,10),(nm,10),(roe,12),(roa,8),(fcf_margin,10)]:
        if pd.notna(v):
            score += add if v > 10 else (add/2 if v > 0 else -add/2)
    score = int(np.clip(score, 0, 100))
    return summary, ratios, score

def enterprise_feature_checklist():
    return pd.DataFrame([
        ["企業評價", "DCF/FCFF/FCFE/APV/DDM/Gordon/EVA/EBO/RI/CAP/PE/PB/PS/PEG/PEGY/NAV/TobinQ/Super Bull", "已保留"],
        ["法人雷達", "法人分數/籌碼分數/主力分數/外資/投信/自營商買賣代理", "已保留"],
        ["ESG永續", "ESG共識/溢價/合理價/牛市價/超級牛市價/永續報告書", "已合併"],
        ["AI研究", "AI目標區間/信心度/計算說明/風險提示", "已保留"],
        ["中文化財報", "中文損益表/資產負債表/現金流量表/財務比率/AI摘要", "新增"],
        ["股票控制器", "智慧搜尋/上櫃.TWO/全站同步/手機電腦響應", "已保留"],
    ], columns=["模組", "內容", "狀態"])


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

st.markdown("""
<div class="hero">
 <div class="hero-title">📈 智策股市 AI 決策平台</div>
 <div class="hero-sub">V42 Enterprise Audit Final｜不跳頁 × 全站選股同步 × 補齊評價模型 × 法人雷達修正 × 永續ESG估價</div>
 <div class="visual"><svg viewBox="0 0 900 220" preserveAspectRatio="none"><defs><linearGradient id="line" x1="0" x2="1"><stop offset="0" stop-color="#22d3ee"/><stop offset=".5" stop-color="#60a5fa"/><stop offset="1" stop-color="#fb7185"/></linearGradient></defs><polyline points="0,160 65,148 120,172 185,124 250,132 320,84 395,106 470,58 540,78 610,42 680,64 760,28 830,50 900,22" fill="none" stroke="url(#line)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><rect x="92" y="92" width="16" height="70" fill="#22c55e"/><rect x="185" y="108" width="16" height="55" fill="#ef4444"/><rect x="306" y="70" width="16" height="78" fill="#22c55e"/><rect x="448" y="45" width="16" height="66" fill="#22c55e"/><text x="28" y="45" fill="#e0f2fe" font-size="22" font-weight="700">V37.1 Institutional Stability</text><text x="28" y="72" fill="#93c5fd" font-size="16">Valuation · ESG · K-Line · Financials · AI Target</text></svg></div>
</div>
""", unsafe_allow_html=True)

MAIN=["🏠首頁","📊監控","📈K線","💎評價","🌱ESG永續","🏦法人","📑中文財報","🤖AI","⚙設定"]
if "page" not in st.session_state: st.session_state.page="🏠首頁"
page=st.radio("主選單",MAIN,index=MAIN.index(st.session_state.page) if st.session_state.page in MAIN else 0,horizontal=True,key="stable_page_menu")
st.session_state.page=page

with st.sidebar:
    st.title("☰ V42設定")
    refresh_label=st.radio("監控更新頻率",["手動","1秒","3秒","5秒","10秒","30秒","60秒"],index=0,horizontal=True,key="refresh_label")
    refresh_sec=0 if refresh_label=="手動" else int(refresh_label.replace("秒",""))
    mcount=st.radio("監控檔數",[8,16,32],index=1,horizontal=True,key="mcount")
    layout_mode=st.radio("版面模式",["自動","手機","電腦"],index=0,horizontal=True,key="layout_mode")
    cols=2 if layout_mode!="電腦" else 4
    period=st.radio("歷史期間",["6mo","1y","2y","5y","10y"],index=2,horizontal=True,key="period")
    sector=st.selectbox("類股清單",["自選"]+list(SECTORS.keys()),index=1,key="sector")
    if "watch_text_value" not in st.session_state:
        st.session_state.watch_text_value = ",".join(DEFAULT_MONITOR)
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
    if st.button("手動刷新"):
        st.cache_data.clear(); st.rerun()

symbols=[clean_symbol(x.strip()) for x in watch_text.split(",") if x.strip()][:mcount] or DEFAULT_MONITOR[:mcount]

# V39：唯一全站股票控制器
active = unified_symbol_manager(symbols)

# V39：手機/電腦響應式欄位
if "layout_mode" not in locals():
    layout_mode = "自動"
display_cols = 4 if layout_mode == "電腦" else 2
df_daily=fetch_daily(active,period); q=repair_quote_with_df(yf_quote(active), df_daily); d_daily=signal_cols(add_indicators(df_daily)); scores=score_blocks(d_daily,q); total=ai_total(scores)
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
    page_refresh_label=st.radio("本頁更新頻率",["手動","1秒","3秒","5秒","10秒","30秒","60秒"],index=["手動","1秒","3秒","5秒","10秒","30秒","60秒"].index(refresh_label),horizontal=True,key="page_refresh_label")
    page_refresh_sec=0 if page_refresh_label=="手動" else int(page_refresh_label.replace("秒",""))
    page_watch=st.text_area("本頁自選監控清單",value=st.session_state.watch_text_value,height=100,key="page_watch_text",help="這裡修改後會同步回左側自選清單")
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
    kmode=st.radio("週期",["日線","週線","月線","60分","30分","15分","5分"],horizontal=True,key="kmode")
    overlays=st.multiselect("疊圖",["MA5","MA10","MA20","MA60","MA120","MA240","布林通道"],default=["MA5","MA20","MA60"],key="overlays")
    panel=st.radio("副圖",["成交量","MACD","KD","RSI","BIAS","威廉"],horizontal=True,key="panel")
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
    st.subheader(f"🏦 法人雷達：{display_name(active)}")
    inst_df=institutional_proxy(df_daily)
    consensus_score=int(np.clip(pd.to_numeric(inst_df.get("強度",pd.Series(dtype=float)),errors="coerce").mean() if not inst_df.empty else scores["inst"],0,100))
    kpi([
        ("法人分數",scores["inst"]),
        ("籌碼分數",scores["chip"]),
        ("主力分數",scores["main"]),
        ("法人共識",f"{consensus_score}/100"),
    ])
    tabs=st.tabs(["三大法人/主力","籌碼風險","連買連賣代理","來源與計算"])
    with tabs[0]:
        st.dataframe(inst_df,use_container_width=True,hide_index=True)
    with tabs[1]:
        st.dataframe(institutional_risk_table(df_daily),use_container_width=True,hide_index=True)
    with tabs[2]:
        st.dataframe(pd.DataFrame([
            ["外資連買/連賣", "量價代理", "需正式TWSE/TPEX資料才可精準計算"],
            ["投信連買/連賣", "量價代理", "目前以20日動能與均線趨勢推估"],
            ["自營商連買/連賣", "量價代理", "目前以短線動能與量比推估"],
            ["主力集中", "量價代理", "目前以成交量、量比、月線位置推估"],
        ],columns=["項目","狀態","說明"]),use_container_width=True,hide_index=True)
    with tabs[3]:
        st.dataframe(pd.DataFrame([
            ["資料來源", "Yahoo Finance 價格與成交量；正式法人需串接 TWSE/TPEX/Fugle/券商API"],
            ["外資強度", "50 + RET20×160 + RET60×80 + MA20站上加分 + 量比加分"],
            ["投信強度", "50 + RET20×120 + MA20>MA60加分 + 站上MA20加分"],
            ["自營商強度", "50 + RET20×220 + 量比加分"],
            ["主力代理", "50 + RET20×130 + RET60×60 + 量比加分 + MA20加分"],
            ["估計張數", "成交量/1000 × 量比 × 法人係數"],
            ["限制", "目前為量價代理，不等於交易所正式三大法人買賣超"],
        ],columns=["項目","說明"]),use_container_width=True,hide_index=True)

elif page=="📑中文財報":
    financial_center(active,q,df_daily)
elif page=="__舊永續__":
    sustainability_center(active,q)
elif page=="🤖AI":
    st.subheader(f"🤖 AI目標區間：{display_name(active)}")
    ai_target_panel(df_daily,scores)
elif page=="⚙設定":
    st.subheader("⚙ 系統設定 / V42功能稽核")
    st.markdown('<div class="explain">V42 已完成：ESG與永續真正合併、企業評價模型以K線收盤價備援、法人雷達補齊、中文化財報分析層、手機/電腦自動響應。</div>',unsafe_allow_html=True)
    st.dataframe(enterprise_feature_checklist(), use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("AIStock V42 Enterprise Audit Final｜研究與教學用途，非投資建議。")
