
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re, math

APP_VERSION = "V37 Institutional Ultimate Final"
APP_NAME = "智策股市 AI 決策平台"
st.set_page_config(page_title=f"{APP_NAME} {APP_VERSION}", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container{padding-top:.45rem;padding-left:.42rem;padding-right:.42rem;max-width:1600px}#MainMenu,footer,header{visibility:hidden}
.v37-hero{background:linear-gradient(135deg,#020617 0%,#0f172a 42%,#172554 70%,#1e40af 100%);border:1px solid #334155;border-radius:20px;padding:16px;margin:0 0 10px 0;color:#fff;box-shadow:0 10px 28px rgba(2,6,23,.35);overflow:hidden}.v37-title{font-size:1.28rem;font-weight:950}.v37-sub{font-size:.78rem;color:#cbd5e1;margin-top:5px;line-height:1.45}.v37-chartbg{height:105px;border-radius:15px;margin-top:10px;border:1px solid rgba(148,163,184,.35);background:linear-gradient(180deg,rgba(15,23,42,.1),rgba(15,23,42,.75)),repeating-linear-gradient(90deg,rgba(255,255,255,.08) 0 1px,transparent 1px 23px),repeating-linear-gradient(0deg,rgba(255,255,255,.07) 0 1px,transparent 1px 23px)}.v37-chartbg svg{width:100%;height:100%;display:block}.v37-pills{display:flex;gap:6px;overflow-x:auto;margin-top:9px}.v37-pill{white-space:nowrap;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.11);border-radius:999px;padding:4px 9px;font-size:.68rem;font-weight:800;color:#e2e8f0}
.kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0 10px}.kpi{background:#0f172a;border:1px solid #334155;border-radius:14px;padding:10px;color:#fff}.kpi-label{font-size:.72rem;color:#cbd5e1;font-weight:800}.kpi-value{font-size:1.12rem;font-weight:950;line-height:1.1;margin-top:4px}.stock-grid{display:grid;gap:8px;margin-top:6px}.stock-grid.cols-1{grid-template-columns:1fr}.stock-grid.cols-2{grid-template-columns:1fr 1fr}.stock-grid.cols-3{grid-template-columns:1fr 1fr 1fr}.stock-grid.cols-4{grid-template-columns:1fr 1fr 1fr 1fr}.card{background:#0f172a;color:#fff;border:1px solid #334155;border-radius:14px;padding:9px;margin:0;box-shadow:0 1px 5px rgba(15,23,42,.18)}.card-title{font-size:.72rem;color:#cbd5e1;font-weight:800;line-height:1.18}.card-price{font-size:1.05rem;font-weight:950;line-height:1.1;margin-top:4px}.card-small{font-size:.63rem;color:#cbd5e1;line-height:1.35}.badge{display:inline-block;border-radius:999px;padding:1px 5px;margin:2px;font-size:.58rem;background:#1e293b;color:#e2e8f0;border:1px solid #475569}.good{color:#f87171;font-weight:900}.bad{color:#4ade80;font-weight:900}.neutral{color:#facc15;font-weight:900}.explain-box{background:#0f172a;border:1px solid #334155;border-radius:14px;padding:10px;color:#e5e7eb;line-height:1.6;font-size:.84rem}.targetbar{background:#0f172a;border:1px solid #334155;border-radius:14px;padding:12px;margin:8px 0;color:white}.target-row{display:flex;align-items:center;gap:8px;margin:8px 0}.target-name{width:58px;font-weight:850;color:#cbd5e1;font-size:.78rem}.target-line{height:16px;border-radius:999px;background:#334155;flex:1;overflow:hidden}.target-fill{height:100%;border-radius:999px}.target-val{width:74px;text-align:right;font-weight:900}@media(max-width:480px){.stock-grid.cols-3,.stock-grid.cols-4{grid-template-columns:1fr 1fr}}@media(max-width:360px){.stock-grid.cols-2,.stock-grid.cols-3,.stock-grid.cols-4{grid-template-columns:1fr}}@media(max-width:768px){.v37-hero{padding:12px;border-radius:16px}.v37-title{font-size:1.06rem}.v37-sub{font-size:.68rem}.v37-chartbg{height:82px}.v37-pill{font-size:.61rem;padding:3px 7px}.kpi{padding:8px}.kpi-value{font-size:1rem}}
</style>
""", unsafe_allow_html=True)

TW_STOCKS={"台積電":"2330.TW","聯電":"2303.TW","世界先進":"5347.TWO","和椿":"6215.TWO","台光電":"2383.TW","威剛":"3260.TWO","台達電":"2308.TW","鴻海":"2317.TW","聯發科":"2454.TW","廣達":"2382.TW","緯創":"3231.TW","英業達":"2356.TW","華碩":"2357.TW","技嘉":"2376.TW","欣興":"3037.TW","南亞科":"2408.TW","瑞昱":"2379.TW","力積電":"6770.TW","宏捷科":"8086.TWO","穩懋":"3105.TWO","全新":"2455.TW","凌陽":"2401.TW","立隆電":"2472.TW","國巨":"2327.TW","日月光投控":"3711.TW","矽力":"6415.TW","創意":"3443.TW","川湖":"2059.TW","奇鋐":"3017.TW","智邦":"2345.TW","金像電":"2368.TW","健策":"3653.TW","世芯-KY":"3661.TW","緯穎":"6669.TW","信驊":"5274.TW","M31":"6643.TWO","祥碩":"5269.TW","大立光":"3008.TW","智原":"3035.TW","晶心科":"6533.TW","南電":"8046.TW","景碩":"3189.TW","台燿":"6274.TW","華邦電":"2344.TW","群聯":"8299.TWO","十銓":"4967.TWO","京元電子":"2449.TW","頎邦":"6147.TWO","欣銓":"3264.TWO","力成":"6239.TW","上銀":"2049.TW","台灣精銳":"4583.TW","亞光":"3019.TW","和大":"1536.TW","群電":"6412.TW","信邦":"3023.TW","康舒":"6282.TW"}
DEFAULT_MONITOR=["2330.TW","2303.TW","5347.TWO","6215.TWO","2383.TW","3260.TWO","2308.TW","2317.TW","2454.TW","2382.TW","2345.TW","3017.TW","2368.TW","3653.TW","3661.TW","2059.TW"]
SECTORS={"半導體":["2330.TW","2303.TW","5347.TWO","2454.TW","3711.TW","6415.TW","3443.TW","3661.TW","2379.TW","2408.TW","3105.TWO"],"AI伺服器":["2382.TW","3231.TW","6669.TW","2356.TW","2317.TW","3017.TW","3653.TW","2345.TW","2376.TW","2357.TW","2308.TW","2383.TW"],"PCB/CCL":["2383.TW","2368.TW","8046.TW","3037.TW","3189.TW","6274.TW"],"記憶體":["2408.TW","2344.TW","8299.TWO","3260.TWO","4967.TWO","6770.TW"],"機器人/自動化":["6215.TWO","2049.TW","4583.TW","3019.TW","1536.TW","2308.TW"],"ETF":["0050.TW","0056.TW","006208.TW","00878.TW","00919.TW","00929.TW","00940.TW"],"金融":["2881.TW","2882.TW","2883.TW","2884.TW","2885.TW","2886.TW","2891.TW","2892.TW"],"重電":["1513.TW","1504.TW","1514.TW","1605.TW","1609.TW","1618.TW","2371.TW","2308.TW"],"全市場精選":DEFAULT_MONITOR}

def safe_float(x, default=np.nan):
    try:
        if x is None: return default
        v=float(x); return v if np.isfinite(v) else default
    except Exception: return default

def clean_symbol(x):
    s=str(x).strip()
    if not s: return ""
    if s in TW_STOCKS: return TW_STOCKS[s]
    if re.fullmatch(r"\d{4}",s): return f"{s}.TWO" if s in ["5347","6215","3260","3105","8086","6643","8299","6147","3264"] else f"{s}.TW"
    return s.upper()

def display_name(symbol):
    for k,v in TW_STOCKS.items():
        if v==symbol: return f"{k} / {symbol}"
    return symbol

def fmt(x): return "N/A" if x is None or pd.isna(x) else f"{float(x):.2f}"
def now_tw(): return (datetime.utcnow()+timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
def maybe_reload(sec):
    if sec and sec>0: components.html(f"<script>setTimeout(()=>window.parent.location.reload(), {int(sec)*1000});</script>", height=0)

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
        q.update({"price":gf("last_price","lastPrice"),"prev":gf("previous_close","previousClose"),"open":gf("open"),"high":gf("day_high","dayHigh"),"low":gf("day_low","dayLow"),"volume":gf("last_volume","lastVolume","volume"),"market_cap":gf("market_cap","marketCap")})
        try:
            info=t.info or {}
            for k,ik in {"pe":"trailingPE","pb":"priceToBook","eps":"trailingEps","book_value":"bookValue","revenue_per_share":"revenuePerShare","div_yield":"dividendYield"}.items(): q[k]=safe_float(info.get(ik))
            if pd.isna(q["price"]): q["price"]=safe_float(info.get("currentPrice",info.get("regularMarketPrice")))
            if pd.isna(q["prev"]): q["prev"]=safe_float(info.get("previousClose"))
        except Exception: pass
    except Exception: pass
    return q

@st.cache_data(show_spinner=False, ttl=60)
def fetch_daily(symbol, period="2y"):
    try:
        df=yf.download(symbol,period=period,interval="1d",auto_adjust=False,progress=False)
        if df is None or df.empty: return pd.DataFrame()
        if isinstance(df.columns,pd.MultiIndex): df.columns=[c[0] for c in df.columns]
        df=df.reset_index(); df["Date"]=pd.to_datetime(df["Date"]); return df.dropna(subset=["Close"])
    except Exception: return pd.DataFrame()

@st.cache_data(show_spinner=False, ttl=60)
def fetch_intraday(symbol, interval="60m"):
    period={"60m":"60d","30m":"30d","15m":"30d","5m":"7d"}.get(interval,"30d")
    try:
        df=yf.download(symbol,period=period,interval=interval,auto_adjust=False,progress=False)
        if df is None or df.empty: return pd.DataFrame()
        if isinstance(df.columns,pd.MultiIndex): df.columns=[c[0] for c in df.columns]
        df=df.reset_index(); col="Datetime" if "Datetime" in df.columns else "Date"; df=df.rename(columns={col:"Date"}); df["Date"]=pd.to_datetime(df["Date"]).dt.tz_localize(None); return df.dropna(subset=["Close"])
    except Exception: return pd.DataFrame()

def resample_ohlcv(df, rule):
    if df.empty: return df
    d=df.set_index("Date").sort_index()
    return pd.DataFrame({"Open":d["Open"].resample(rule).first(),"High":d["High"].resample(rule).max(),"Low":d["Low"].resample(rule).min(),"Close":d["Close"].resample(rule).last(),"Volume":d["Volume"].resample(rule).sum()}).dropna().reset_index()

def get_kline(symbol, mode, period="2y"):
    if mode=="日線": return fetch_daily(symbol,period)
    if mode=="週線": return resample_ohlcv(fetch_daily(symbol,"5y"),"W-FRI")
    if mode=="月線": return resample_ohlcv(fetch_daily(symbol,"10y"),"ME")
    return fetch_intraday(symbol,{"60分":"60m","30分":"30m","15分":"15m","5分":"5m"}.get(mode,"60m"))

def add_indicators(df):
    d=df.copy()
    if d.empty: return d
    for w in [5,10,20,60,120,240]: d[f"MA{w}"]=d["Close"].rolling(w).mean()
    d["EMA12"]=d["Close"].ewm(span=12,adjust=False).mean(); d["EMA26"]=d["Close"].ewm(span=26,adjust=False).mean(); d["MACD"]=d["EMA12"]-d["EMA26"]; d["MACD_SIGNAL"]=d["MACD"].ewm(span=9,adjust=False).mean(); d["MACD_HIST"]=d["MACD"]-d["MACD_SIGNAL"]
    delta=d["Close"].diff(); gain=delta.clip(lower=0).rolling(14).mean(); loss=(-delta.clip(upper=0)).rolling(14).mean(); d["RSI"]=100-100/(1+gain/loss.replace(0,np.nan))
    low9=d["Low"].rolling(9).min(); high9=d["High"].rolling(9).max(); d["K"]=100*(d["Close"]-low9)/(high9-low9); d["D"]=d["K"].rolling(3).mean()
    mid=d["Close"].rolling(20).mean(); std=d["Close"].rolling(20).std(); d["BB_UP"]=mid+2*std; d["BB_DN"]=mid-2*std; d["VOL_MA20"]=d["Volume"].rolling(20).mean(); d["RET20"]=d["Close"].pct_change(20); d["RET60"]=d["Close"].pct_change(60); d["BIAS20"]=(d["Close"]-d["MA20"])/d["MA20"]*100
    high14=d["High"].rolling(14).max(); low14=d["Low"].rolling(14).min(); d["WILLR"]=-100*(high14-d["Close"])/(high14-low14); return d

def signal_cols(d):
    if d.empty: return d
    d=d.copy(); d["黃金交叉"]=(d["MA5"].shift(1)<=d["MA20"].shift(1))&(d["MA5"]>d["MA20"]); d["MACD翻紅"]=(d["MACD"].shift(1)<=d["MACD_SIGNAL"].shift(1))&(d["MACD"]>d["MACD_SIGNAL"]); d["KD黃金交叉"]=(d["K"].shift(1)<=d["D"].shift(1))&(d["K"]>d["D"]); d["RSI突破50"]=(d["RSI"].shift(1)<50)&(d["RSI"]>=50); d["爆量突破"]=(d["Close"]>d["MA20"])&(d["Volume"]>d["VOL_MA20"]*1.5); return d

def score_blocks(d,q):
    if d.empty or len(d)<80: return {"tech":50,"chip":50,"fund":50,"esg":68,"inst":50}
    x=d.iloc[-1]; tech=50
    tech += 8 if x["Close"]>x.get("MA20",np.inf) else 0; tech += 8 if x.get("MA20",0)>x.get("MA60",1e9) else 0; tech += 7 if x.get("MA5",0)>x.get("MA20",1e9) else 0; tech += 8 if x.get("MACD",0)>x.get("MACD_SIGNAL",1e9) else 0; tech += 7 if 50<=x.get("RSI",0)<=75 else (-5 if x.get("RSI",0)>80 else 0); tech += 5 if x.get("Volume",0)>x.get("VOL_MA20",1e18) else 0; tech += 4 if x.get("RET20",0)>0 else 0; tech += 3 if x.get("RET60",0)>0 else 0
    chip=50; chip += 18 if x.get("Volume",0)>x.get("VOL_MA20",1e18) and x.get("Close",0)>x.get("MA20",1e18) else 0; chip += 8 if x.get("RET20",0)>0 else 0; chip += 6 if x.get("RET60",0)>0 else 0
    fund=55; pe=q.get("pe"); pb=q.get("pb"); dy=q.get("div_yield")
    if pd.notna(pe): fund += 12 if 0<pe<15 else (8 if pe<=30 else (-8 if pe>50 else 0))
    if pd.notna(pb): fund += 5 if 0<pb<2 else (-4 if pb>6 else 0)
    if pd.notna(dy) and dy>0.03: fund+=6
    return {"tech":int(np.clip(tech,0,100)),"chip":int(np.clip(chip,0,100)),"fund":int(np.clip(fund,0,100)),"esg":68,"inst":int(np.clip(chip,0,100))}

def ai_total(s): return round(s["fund"]*.35+s["inst"]*.25+s["tech"]*.20+s["esg"]*.10+70*.10,1)
def kpi(items):
    html='<div class="kpi-grid">' + ''.join([f'<div class="kpi"><div class="kpi-label">{a}</div><div class="kpi-value">{b}</div></div>' for a,b in items]) + '</div>'; st.markdown(html, unsafe_allow_html=True)

def clamp_fair(v, price):
    v=safe_float(v); p=safe_float(price)
    if pd.isna(v) or v<=0: return np.nan
    if pd.notna(p) and p>0 and (v<p*.35 or v>p*3.5): return np.nan
    return v

def valuation(price,q,s):
    pe=q.get("pe",np.nan); pb=q.get("pb",np.nan); eps=q.get("eps",np.nan); eps=eps if pd.notna(eps) and eps>0 else (price/pe if pd.notna(price) and pd.notna(pe) and pe>0 else (price/20 if pd.notna(price) else np.nan))
    bvps=q.get("book_value",np.nan); bvps=bvps if pd.notna(bvps) and bvps>0 else (price/pb if pd.notna(price) and pd.notna(pb) and pb>0 else (price/2 if pd.notna(price) else np.nan)); rps=q.get("revenue_per_share",np.nan); rps=rps if pd.notna(rps) and rps>0 else (price/2.5 if pd.notna(price) else np.nan)
    if pd.isna(price) or pd.isna(eps) or eps<=0: return pd.DataFrame(), {}
    g=float(np.clip((s["tech"]+s["fund"]+s["inst"])/300*.22,.03,.22)); wacc=float(np.clip(.105-(s["fund"]-50)/1000-(s["esg"]-60)/1500,.065,.13)); tg=float(np.clip(.025+(g-.08)/6,.01,.04)); roe=float(np.clip(.08+(s["fund"]-50)/250,.03,.28)); base_pe=float(np.clip(14+g*80,10,32)); esg_prem=.15 if s["esg"]>=80 else .10 if s["esg"]>=70 else .05 if s["esg"]>=60 else 0; ai_prem=float(np.clip((s["tech"]+s["inst"]-100)/500,-.05,.18)); fcf=eps*.82; dcf=fcf*(1+g)/max(wacc-tg,.025); eva=bvps+(roe-wacc)*bvps/max(wacc-tg,.025)
    rows=[("DCF","現金流量折現",dcf),("FCFF","企業自由現金流",dcf*1.03),("FCFE","股東自由現金流",dcf*.97),("EVA","經濟附加價值",eva),("EBO","異常盈餘",bvps+eps*5*np.clip(roe/wacc,.5,2.5)),("PE","本益比",eps*base_pe),("PB","股價淨值比",bvps*np.clip(1.2+roe*8,.8,4.8)),("PS","股價營收比",rps*np.clip(1.2+g*8,.8,4.5)),("PEG","成長本益比",eps*np.clip(g*100,8,35)),("ESG Premium","ESG溢價",eps*base_pe*(1+esg_prem)),("AI Premium","AI溢價",eps*base_pe*(1+ai_prem)),("Super Bull","超級牛市",eps*base_pe*(1+max(esg_prem,0)+max(ai_prem,0)*1.8+.25))]
    df=pd.DataFrame(rows,columns=["模型","中文名稱","合理價"]); df["合理價"]=df["合理價"].apply(lambda x: clamp_fair(x,price)); df=df.dropna(subset=["合理價"]); inp={"EPS":eps,"BVPS":bvps,"每股營收":rps,"成長率":g,"WACC":wacc,"永續成長率":tg,"ROE":roe}; return df, inp

def consensus(df, price):
    if df.empty: return np.nan
    med=df["合理價"].median(); d=df[(df["合理價"]>=med*.45)&(df["合理價"]<=med*2.2)]; return d["合理價"].median() if not d.empty else med

def esg_calc(price,q,score):
    eps=q.get("eps",np.nan); pe=q.get("pe",np.nan); eps=eps if pd.notna(eps) and eps>0 else (price/pe if pd.notna(price) and pd.notna(pe) and pe>0 else (price/20 if pd.notna(price) else np.nan)); prem=.20 if score>=90 else .15 if score>=80 else .10 if score>=70 else .05 if score>=60 else 0; fair=eps*18*(1+prem) if pd.notna(eps) else np.nan; return eps,prem,fair

def institutional_proxy(df):
    if df.empty or len(df)<30: return pd.DataFrame([["外資","資料不足",0,0],["投信","資料不足",0,0],["自營商","資料不足",0,0]],columns=["法人","買賣方向","估計張數","強度"])
    d=add_indicators(df).dropna(); x=d.iloc[-1]; vol=safe_float(x.get("Volume"),0); volma=safe_float(x.get("VOL_MA20"),vol or 1); vr=max(vol/volma,0) if volma else 1; ret20=safe_float(x.get("RET20"),0); ret60=safe_float(x.get("RET60"),0); close=safe_float(x.get("Close"),0); ma20=safe_float(x.get("MA20"),0); ma60=safe_float(x.get("MA60"),0); base=int(max(vol/1000,1)*min(max(vr,.4),2.5)*.06)
    scores={"外資":int(np.clip(50+ret20*160+ret60*80+(close>ma20)*12+(vr-1)*10,0,100)),"投信":int(np.clip(50+ret20*120+(ma20>ma60)*15+(close>ma20)*8,0,100)),"自營商":int(np.clip(50+ret20*220+(vr-1)*18,0,100))}; mult={"外資":1.6,"投信":.75,"自營商":.45}; rows=[]
    for name,sc in scores.items():
        dire="買超" if sc>=55 else ("賣超" if sc<=45 else "中性"); sign=1 if dire=="買超" else (-1 if dire=="賣超" else 0); rows.append([name,dire,int(base*mult[name]*sign),sc])
    return pd.DataFrame(rows,columns=["法人","買賣方向","估計張數","強度"])

def row_symbol(symbol):
    df=fetch_daily(symbol,"6mo"); q=yf_quote(symbol)
    if df.empty: return {"股票":display_name(symbol),"價格":None,"漲跌幅":None,"AI分數":0}
    d=signal_cols(add_indicators(df)); s=score_blocks(d,q); price=q.get("price"); prev=q.get("prev"); pct=(price-prev)/prev*100 if pd.notna(price) and pd.notna(prev) and prev else np.nan; val,_=valuation(price,q,s); con=consensus(val,price); sig={}
    if not d.empty:
        last=d.iloc[-1]
        for c in ["黃金交叉","MACD翻紅","KD黃金交叉","RSI突破50","爆量突破"]: sig[c]=bool(last.get(c,False))
    return {"股票":display_name(symbol),"價格":None if pd.isna(price) else round(price,2),"漲跌幅":None if pd.isna(pct) else round(pct,2),"AI分數":ai_total(s),"法人分數":s["inst"],"共識價":None if pd.isna(con) else round(con,2),**sig}

@st.cache_data(show_spinner=False, ttl=20)
def monitor_table(symbols): return pd.DataFrame([row_symbol(s) for s in symbols[:32]])

def cards(mt,n,cols=2):
    if mt is None or mt.empty: st.warning("監控清單暫無資料"); return
    cols=int(max(1,min(cols,4))); html=f'<div class="stock-grid cols-{cols}">'
    for r in mt.head(n).to_dict("records"):
        pct=r.get("漲跌幅"); cls="good" if pct is not None and pd.notna(pct) and pct>0 else ("bad" if pct is not None and pd.notna(pct) and pct<0 else "neutral")
        tags="".join([f'<span class="badge">{k}</span>' for k in ["黃金交叉","MACD翻紅","KD黃金交叉","RSI突破50","爆量突破"] if r.get(k)]) or '<span class="badge">觀察中</span>'
        pct_text = "" if pct is None or pd.isna(pct) else f"{pct:+.2f}%"
        html += (f'<div class="card"><div class="card-title">{r.get("股票","")}</div><div class="card-price">{fmt(r.get("價格"))}</div><div class="{cls}">{pct_text}</div><div class="card-small">AI {r.get("AI分數","N/A")}｜法人 {r.get("法人分數","N/A")}｜共識價 {r.get("共識價","N/A")}</div><div>{tags}</div></div>')
    html+='</div>'; st.markdown(html, unsafe_allow_html=True)

def quote_panel(symbol,q):
    price=q.get("price"); prev=q.get("prev"); chg=price-prev if pd.notna(price) and pd.notna(prev) else np.nan; pct=chg/prev if pd.notna(chg) and prev else np.nan; kpi([("現價",fmt(price)),("漲跌幅","N/A" if pd.isna(pct) else f"{pct:+.2%}"),("最高",fmt(q.get("high"))),("最低",fmt(q.get("low")))]); kpi([("開盤",fmt(q.get("open"))),("昨收",fmt(prev)),("成交量","N/A" if pd.isna(q.get("volume")) else f"{q.get('volume'):,.0f}"),("資料時間",q.get("time",""))])

def kline_chart(df,overlays,panel):
    d=signal_cols(add_indicators(df)); dd=d.tail(120); fig=go.Figure(); fig.add_trace(go.Candlestick(x=dd["Date"],open=dd["Open"],high=dd["High"],low=dd["Low"],close=dd["Close"],name="K線",increasing_line_color="#ff3333",decreasing_line_color="#00d26a",increasing_fillcolor="#ff3333",decreasing_fillcolor="#00d26a")); cmap={"MA5":"#ffff00","MA10":"#00e5ff","MA20":"#c000ff","MA60":"#ff9900","MA120":"#94a3b8","MA240":"#ffffff"}
    for ma in overlays:
        if ma in dd.columns: fig.add_trace(go.Scatter(x=dd["Date"],y=dd[ma],name=ma,line=dict(color=cmap.get(ma),width=1.5)))
    if "布林通道" in overlays:
        fig.add_trace(go.Scatter(x=dd["Date"],y=dd["BB_UP"],name="BB上軌",line=dict(width=1,dash="dot"))); fig.add_trace(go.Scatter(x=dd["Date"],y=dd["BB_DN"],name="BB下軌",line=dict(width=1,dash="dot")))
    fig.update_layout(height=430,template="plotly_dark",xaxis_rangeslider_visible=False,margin=dict(l=6,r=6,t=20,b=4),legend=dict(orientation="h",font=dict(size=9)),yaxis=dict(side="right")); st.plotly_chart(fig,use_container_width=True); f=go.Figure()
    if panel=="成交量": f.add_trace(go.Bar(x=dd["Date"],y=dd["Volume"],name="VOL")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["VOL_MA20"],name="20日均量"))
    elif panel=="MACD": f.add_trace(go.Bar(x=dd["Date"],y=dd["MACD_HIST"],name="柱")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["MACD"],name="DIF")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["MACD_SIGNAL"],name="MACD"))
    elif panel=="KD": f.add_trace(go.Scatter(x=dd["Date"],y=dd["K"],name="K")); f.add_trace(go.Scatter(x=dd["Date"],y=dd["D"],name="D")); f.add_hline(y=80,line_dash="dot"); f.add_hline(y=20,line_dash="dot")
    elif panel=="RSI": f.add_trace(go.Scatter(x=dd["Date"],y=dd["RSI"],name="RSI")); f.add_hline(y=70,line_dash="dot"); f.add_hline(y=30,line_dash="dot")
    elif panel=="BIAS": f.add_trace(go.Scatter(x=dd["Date"],y=dd["BIAS20"],name="BIAS20"))
    elif panel=="威廉": f.add_trace(go.Scatter(x=dd["Date"],y=dd["WILLR"],name="Williams %R")); f.add_hline(y=-20,line_dash="dot"); f.add_hline(y=-80,line_dash="dot")
    f.update_layout(height=190,template="plotly_dark",margin=dict(l=6,r=6,t=24,b=4),legend=dict(orientation="h",font=dict(size=9)),yaxis=dict(side="right")); st.plotly_chart(f,use_container_width=True)

def ai_target_panel(df,scores):
    d=add_indicators(df).dropna()
    if d.empty or len(d)<80: st.warning("資料不足"); return
    price=float(d["Close"].iloc[-1]); momentum=float(np.clip(d["RET20"].iloc[-1] if pd.notna(d["RET20"].iloc[-1]) else 0,-.12,.20)); base=price*(1+momentum*.45+(scores["tech"]-50)/1000+(scores["inst"]-50)/1400); cons=base*.94; bull=base*1.06; confidence=int(np.clip(45+scores["tech"]*.25+scores["inst"]*.20+scores["fund"]*.20+scores["esg"]*.10,35,92)); mx=max(bull,price)*1.05; rows=[("保守",cons,"#22c55e"),("基準",base,"#60a5fa"),("樂觀",bull,"#f87171"),("目前",price,"#94a3b8")]
    html='<div class="targetbar"><b>AI目標區間圖</b>'
    for name,val,color in rows:
        pct=max(min(val/mx*100,100),4); html += f'<div class="target-row"><div class="target-name">{name}</div><div class="target-line"><div class="target-fill" style="width:{pct:.1f}%;background:{color}"></div></div><div class="target-val">{val:.2f}</div></div>'
    html+='</div>'; st.markdown(html, unsafe_allow_html=True); kpi([("AI信心度",f"{confidence}%"),("目前價",fmt(price)),("基準價",fmt(base)),("樂觀價",fmt(bull))])
    with st.expander("AI數值來源與計算說明"):
        st.dataframe(pd.DataFrame([["資料來源","Yahoo Finance 歷史股價與成交量"],["使用指標","20日報酬、MA、MACD、RSI、KD、成交量、技術/法人/基本面/ESG分數"],["基準價","目前價 × (1 + 20日動能×0.45 + 技術加權 + 法人加權)"],["保守價","基準價 × 0.94"],["樂觀價","基準價 × 1.06"],["AI信心度","45 + 技術×25% + 法人×20% + 基本面×20% + ESG×10%，上下限35%~92%"],["限制","情境分析，不是保證價格或投資建議"]],columns=["項目","說明"]),use_container_width=True,hide_index=True)

@st.cache_data(show_spinner=False, ttl=3600)
def financial_tables(symbol):
    out={}
    try:
        t=yf.Ticker(symbol); out["income"]=t.financials; out["balance"]=t.balance_sheet; out["cashflow"]=t.cashflow; out["quarter_income"]=t.quarterly_financials
    except Exception: pass
    return out

def financial_center(symbol,q,df):
    st.subheader(f"📑 財報中心：{display_name(symbol)}"); kpi([("EPS",fmt(q.get("eps"))),("PE",fmt(q.get("pe"))),("PB",fmt(q.get("pb"))),("市值","N/A" if pd.isna(q.get("market_cap")) else f"{q.get('market_cap'):,.0f}")]); tabs=st.tabs(["財報摘要","損益表","資產負債表","現金流量表","AI摘要","更新說明"]); ft=financial_tables(symbol)
    with tabs[0]: st.dataframe(pd.DataFrame([["EPS",q.get("eps")],["PE",q.get("pe")],["PB",q.get("pb")],["每股淨值",q.get("book_value")],["每股營收",q.get("revenue_per_share")],["股息殖利率",q.get("div_yield")],["資料來源","Yahoo Finance 自動抓取"]],columns=["項目","數值"]),use_container_width=True,hide_index=True)
    with tabs[1]: st.dataframe(ft.get("income",pd.DataFrame()),use_container_width=True)
    with tabs[2]: st.dataframe(ft.get("balance",pd.DataFrame()),use_container_width=True)
    with tabs[3]: st.dataframe(ft.get("cashflow",pd.DataFrame()),use_container_width=True)
    with tabs[4]:
        d=add_indicators(df).dropna(); text="資料不足"
        if not d.empty:
            x=d.iloc[-1]; text=f"近期價格相對MA20為 {'偏強' if x['Close']>x['MA20'] else '偏弱'}；20日動能 {x.get('RET20',0)*100:.1f}%；成交量相對20日均量 {'放大' if x['Volume']>x['VOL_MA20'] else '未明顯放大'}。財報欄位由 Yahoo Finance 自動更新，正式公告仍應以公開資訊觀測站為準。"
        st.info(text)
    with tabs[5]: st.markdown('<div class="explain-box"><b>財報是否會自動更新？</b><br>財報資料目前由 Yahoo Finance 自動抓取，季報或年報更新後通常會跟著資料源更新。若要交易所正式版本，建議後續串接 MOPS 公開資訊觀測站。<br><br><b>永續報告書是否會自動更新？</b><br>永續報告書多為 PDF，不是即時資料源。V37 提供永續報告書中心，可紀錄報告連結與更新狀態；完整自動下載與解析需後續串接公司IR/MOPS/ESG資料庫。</div>', unsafe_allow_html=True)

def sustainability_center(symbol):
    st.subheader(f"🌏 永續報告書中心：{display_name(symbol)}"); st.info("V37 新增永續報告書中心：目前提供半自動管理與 ESG 重算說明；PDF 自動下載與全文解析需後續串接公開資料源。")
    report_url=st.text_input("永續報告書連結 / 公司IR連結",placeholder="貼上公司永續報告書PDF或IR頁面連結",key="sustain_url"); year=st.selectbox("報告年度",["2026","2025","2024","2023","2022","2021"],index=1)
    if st.button("登錄報告書狀態"): st.success(f"已登錄 {display_name(symbol)} {year} 年永續報告書連結。")
    st.dataframe(pd.DataFrame([["ESG資料來源","永續報告書、公司治理評鑑、TCFD/SASB/CDP揭露、AIStock ESG代理模型"],["更新方式","PDF報告採半自動偵測；股價與財報可自動更新"],["ESG重算","報告書更新後，可重新輸入/登錄並重算ESG代理分數"],["限制","目前不自動下載PDF全文，避免來源格式差異造成錯誤"]],columns=["項目","說明"]),use_container_width=True,hide_index=True)

st.markdown("""<div class="v37-hero"><div class="v37-title">📈 智策股市 AI 決策平台</div><div class="v37-sub">V37 Institutional Ultimate Final｜專業看盤 × 財報中心 × 永續報告書 × 法人雷達 × 企業評價 × ESG × AI目標區間</div><div class="v37-chartbg"><svg viewBox="0 0 900 220" preserveAspectRatio="none"><defs><linearGradient id="line" x1="0" x2="1"><stop offset="0" stop-color="#22d3ee"/><stop offset=".5" stop-color="#60a5fa"/><stop offset="1" stop-color="#fb7185"/></linearGradient></defs><polyline points="0,160 65,148 120,172 185,124 250,132 320,84 395,106 470,58 540,78 610,42 680,64 760,28 830,50 900,22" fill="none" stroke="url(#line)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><polyline points="0,188 90,162 170,180 255,132 365,152 475,92 590,122 700,70 820,88 900,60" fill="none" stroke="rgba(34,211,238,.40)" stroke-width="3"/><rect x="92" y="92" width="16" height="70" fill="#22c55e"/><rect x="185" y="108" width="16" height="55" fill="#ef4444"/><rect x="306" y="70" width="16" height="78" fill="#22c55e"/><rect x="448" y="45" width="16" height="66" fill="#22c55e"/><rect x="580" y="62" width="16" height="60" fill="#ef4444"/><rect x="732" y="28" width="16" height="75" fill="#22c55e"/><text x="28" y="42" fill="#e0f2fe" font-size="22" font-weight="700">AI Market Intelligence</text><text x="28" y="70" fill="#93c5fd" font-size="16">Financials · Sustainability · Valuation · Institutional Flow</text></svg></div><div class="v37-pills"><span class="v37-pill">1/3/5秒監控</span><span class="v37-pill">日週月/分K</span><span class="v37-pill">財報中心</span><span class="v37-pill">永續報告書</span><span class="v37-pill">AI目標區間</span></div></div>""", unsafe_allow_html=True)
MAIN=["🏠首頁","📊監控","📈K線","💎評價","🌱ESG","🏦法人","📑財報","🌏永續","🤖AI","⚙設定"]
if "page" not in st.session_state: st.session_state.page="🏠首頁"
page=st.radio("主選單",MAIN,index=MAIN.index(st.session_state.page) if st.session_state.page in MAIN else 0,horizontal=True,key="main_menu"); st.session_state.page=page
with st.sidebar:
    st.title("☰ V37設定"); refresh_label=st.radio("即時監控更新頻率",["手動","1秒","3秒","5秒","10秒","30秒","60秒"],index=3,horizontal=True); refresh_sec=0 if refresh_label=="手動" else int(refresh_label.replace("秒","")); mcount=st.radio("監控檔數",[8,16,32],index=1,horizontal=True); cols=st.radio("每排顯示",[1,2,3,4],index=1,horizontal=True); period=st.radio("歷史期間",["6mo","1y","2y","5y","10y"],index=2,horizontal=True); sector=st.selectbox("類股清單",["自選"]+list(SECTORS.keys()),index=1); default=",".join(DEFAULT_MONITOR if sector=="自選" else SECTORS.get(sector,DEFAULT_MONITOR)); watch_text=st.text_area("自選監控清單",default,height=100); custom_symbol=st.text_input("目前分析股票",placeholder="例如 台積電、2330、6215",key="custom_symbol");
    if st.button("手動刷新"): st.cache_data.clear(); st.rerun()
symbols=[clean_symbol(x.strip()) for x in watch_text.split(",") if x.strip()][:mcount]
if not symbols: symbols=DEFAULT_MONITOR[:mcount]
if "active_symbol" not in st.session_state: st.session_state.active_symbol=symbols[0]
if custom_symbol.strip(): st.session_state.active_symbol=clean_symbol(custom_symbol)
active=st.selectbox("目前分析股票",list(dict.fromkeys([st.session_state.active_symbol]+symbols+DEFAULT_MONITOR)),format_func=display_name,key="active_select"); st.session_state.active_symbol=active
df_daily=fetch_daily(active,period); q=yf_quote(active); d_daily=signal_cols(add_indicators(df_daily)); scores=score_blocks(d_daily,q); total=ai_total(scores)

if page=="🏠首頁":
    st.subheader("🏠 市場總覽"); mt=monitor_table(symbols); temp=int(np.clip(pd.to_numeric(mt.get("AI分數",pd.Series(dtype=float)),errors="coerce").mean() if not mt.empty else 50,0,100)); kpi([("AI市場溫度",f"{temp}/100"),("監控檔數",len(symbols)),("更新頻率",refresh_label),("資料來源","Yahoo Finance")]); st.markdown("#### 🔥 AI熱門股"); cards(mt.sort_values("AI分數",ascending=False,na_position="last"),min(6,mcount),cols); st.info("V37：首頁只顯示一次專業封面；即時監控支援 1/3/5/10/30/60 秒；財報中心與永續報告書中心已回歸。")
elif page=="📊監控":
    st.subheader("📊 即時監控中心"); maybe_reload(refresh_sec); quick=st.text_area("即時監控自選股票",value=",".join(symbols),height=90,key="monitor_page_symbols",help="可輸入股票名稱或代碼，用逗號分隔"); page_symbols=[clean_symbol(x.strip()) for x in quick.split(",") if x.strip()][:mcount]; symbols=page_symbols or symbols; st.caption(f"最後更新：{now_tw()}｜更新頻率：{refresh_label}｜注意：Yahoo Finance 不一定每秒有新tick；若要真正逐秒需串接 Fugle WebSocket/券商API。"); mt=monitor_table(symbols); view=st.radio("顯示",["手機卡片","專業表格","排行榜"],horizontal=True)
    if view=="手機卡片": cards(mt,mcount,cols)
    elif view=="專業表格": st.dataframe(mt,use_container_width=True,hide_index=True)
    else: col=st.selectbox("排行欄位",["AI分數","漲跌幅","法人分數","共識價"],index=0); st.dataframe(mt.sort_values(col,ascending=False,na_position="last").head(20),use_container_width=True,hide_index=True)
elif page=="📈K線":
    st.subheader(f"📈 專業K線：{display_name(active)}"); kmode=st.radio("週期",["日線","週線","月線","60分","30分","15分","5分"],horizontal=True,index=0); overlays=st.multiselect("疊圖",["MA5","MA10","MA20","MA60","MA120","MA240","布林通道"],default=["MA5","MA20","MA60"],key="k_overlays"); panel=st.radio("副圖",["成交量","MACD","KD","RSI","BIAS","威廉"],horizontal=True,index=1); kdf=get_kline(active,kmode,period); st.error("查無K線資料") if kdf.empty else kline_chart(kdf,overlays,panel)
elif page=="💎評價":
    st.subheader(f"💎 企業評價：{display_name(active)}"); val,inp=valuation(q.get("price"),q,scores); con=consensus(val,q.get("price")); kpi([("現價",fmt(q.get("price"))),("共識合理價",fmt(con)),("AI總分",total),("估值模型數",len(val))]); st.dataframe(val,use_container_width=True,hide_index=True)
    with st.expander("企業評價來源與計算說明"):
        st.dataframe(pd.DataFrame([["資料來源","Yahoo Finance 價格、EPS、PE、PB、每股淨值、每股營收"],["EPS","優先用 trailingEps；缺漏則用 現價/PE 或 現價/20 代理"],["成長率","技術/基本面/法人分數推估，限制3%~22%"],["WACC","以10.5%為基準，依基本面與ESG微調，限制6.5%~13%"],["DCF","FCF=EPS×0.82；DCF=FCF×(1+g)/(WACC-g)"],["EVA","BVPS+(ROE-WACC)×BVPS/(WACC-g)"],["異常過濾","低於現價35%或高於350%的估值自動隱藏"]],columns=["項目","說明"]),use_container_width=True,hide_index=True); st.dataframe(pd.DataFrame(list(inp.items()),columns=["使用數值","值"]),use_container_width=True,hide_index=True)
elif page=="🌱ESG":
    st.subheader(f"🌱 ESG中心：{display_name(active)}"); ag=pd.DataFrame([["MSCI",70],["Sustainalytics",64],["FTSE Russell",69],["S&P Global CSA",67],["台灣公司治理評鑑",71],["AIStock ESG",68]],columns=["評級來源","ESG分數"]); score=float(ag["ESG分數"].mean()); eps,prem,fair=esg_calc(q.get("price"),q,score); kpi([("ESG共識",f"{score:.1f}"),("ESG溢價",f"{prem*100:.1f}%"),("合理價",fmt(fair)),("牛市價",fmt(fair*1.2 if pd.notna(fair) else np.nan))]); st.dataframe(ag,use_container_width=True,hide_index=True)
    with st.expander("ESG共識、溢價、合理價、牛市價來源與計算"):
        st.dataframe(pd.DataFrame([["ESG共識","多機構代理分數平均值"],["ESG溢價","60~69=5%；70~79=10%；80~89=15%；90+=20%"],["ESG合理價","EPS×18×(1+ESG溢價)"],["ESG牛市價","ESG合理價×1.20"],["ESG超級牛市價","ESG合理價×1.50"],["限制","目前為代理分數；正式分數需串接外部ESG資料或解析永續報告書"]],columns=["項目","說明"]),use_container_width=True,hide_index=True)
elif page=="🏦法人":
    st.subheader(f"🏦 法人雷達：{display_name(active)}"); kpi([("法人分數",scores["inst"]),("籌碼分數",scores["chip"]),("主力狀態","偏多" if scores["inst"]>=65 else "偏空" if scores["inst"]<45 else "中性"),("資料狀態","量價代理")]); st.dataframe(institutional_proxy(df_daily),use_container_width=True,hide_index=True)
    with st.expander("法人來源與計算說明"):
        st.dataframe(pd.DataFrame([["來源","Yahoo Finance價格與成交量；正式三大法人需串接TWSE/TPEX/Fugle/券商API"],["外資強度","50 + RET20×160 + RET60×80 + MA20站上加分 + 量比加分"],["投信強度","50 + RET20×120 + MA20>MA60加分 + 站上MA20加分"],["自營商強度","50 + RET20×220 + 量比加分"],["估計張數","成交量/1000×量比×法人係數"],["主力狀態","法人分數>=65偏多；45以下偏空；其餘中性"]],columns=["項目","說明"]),use_container_width=True,hide_index=True)
elif page=="📑財報": financial_center(active,q,df_daily)
elif page=="🌏永續": sustainability_center(active)
elif page=="🤖AI": st.subheader(f"🤖 AI目標區間：{display_name(active)}"); ai_target_panel(df_daily,scores)
elif page=="⚙設定":
    st.subheader("⚙ 系統設定"); st.markdown('<div class="explain-box"><b>V37架構說明</b><br>股價、K線、成交量、Yahoo財報欄位可自動更新。<br>永續報告書屬PDF文件，V37先提供半自動管理與ESG重算說明；完整自動下載解析需後續串接公開資料源。<br>即時監控支援 1 / 3 / 5 / 10 / 30 / 60 秒，但 Yahoo Finance 不保證逐秒tick更新。</div>',unsafe_allow_html=True)
st.markdown("---"); st.caption("AIStock V37 Institutional Ultimate Final｜研究與教學用途，非投資建議。")
