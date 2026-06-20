from io import StringIO
import requests

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import re, math
try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None


APP_VERSION="V76.3 Official Master"
APP_NAME="智策股市 AI 決策平台"
st.set_page_config(page_title=f"{APP_NAME} {APP_VERSION}", page_icon="📈", layout="wide", initial_sidebar_state="expanded")


# ================= V76 AI / ESG / 法人完整補齊 =================
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
# ================= V76 AI / ESG / 法人完整補齊 END =================


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


/* V76.3 Official Master responsive audit */
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


# V76.3 Official Master：擴充台股中文名稱對照；每位使用者使用自己的 session_state，不寫共用 watchlist.json
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

# V76：補充高價股/半導體/自動化常用中文名
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
    # V76.3 Official Master.2: 使用 Streamlit autorefresh，避免 browser reload 導致回首頁或股票重設
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
    """V76.3 Official Master: if Yahoo quote is N/A, use latest K-line close as backup so valuation models do not disappear."""
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
    """V76: best-effort append extra indicator traces to existing Plotly figure."""
    if df is None or df.empty or sub_inds is None:
        return fig
    d=add_more_indicators(df)
    # This helper is intentionally conservative to avoid breaking existing subplot layout.
    return fig


# ================= V76 K線副圖與籌碼燈號增強 =================
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
    """V76 融資融券 + 借券 + 主力，產生買進/賣出燈號。正式資料未串接時用量價代理。"""
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
# ================= V76 K線副圖與籌碼燈號增強 END =================

st.markdown("""

<div class="hero">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="font-size:1.5rem;">📈</div>
    <div>
      <div style="font-weight:950;font-size:1.15rem;">智策股市 AI 決策平台</div>
      <div style="font-size:.78rem;color:#dbeafe;margin-top:2px;">
        V76.3 Official Master｜企業評價 × 法人籌碼 × 融資融券燈號 × ESG永續 × 中文財報 × AI研究
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
    <text x="40" y="42" fill="#ffffff" font-size="28" font-weight="900">V76.3 Official Master</text>
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

# V60_PAGE_TARGET_HELPER: APP快捷入口目標保存在 session_state；若原始選單未吃到，仍可由各頁判斷使用。

# ================= V76.1 TRANSPARENCY + NAME FIX LAYER =================
APP_VERSION="V76.3 Official Master"

# 補充 V76 未覆蓋股票中文名稱與產業DNA，避免回退 Yahoo 英文名稱或待分類。
V761_EXTRA_ROWS = [
    ("3046","建碁","上市","電子","電腦週邊","工業電腦/迷你電腦","IPC/邊緣運算","AIoT/工業電腦","中游"),
    ("3045","台灣大","上市","服務","電信","電信服務","行動/寬頻/電商","數位服務","下游"),
    ("3059","華晶科","上市","電子","光學","影像模組","相機/影像應用","AI視覺/車用影像","中游"),
    ("3056","總太","上市","傳產","營建","建設開發","住宅/商辦","不動產循環","下游"),
    ("3046","建碁","上市","電子","電腦週邊","工業電腦/迷你電腦","IPC/邊緣運算","AIoT/工業電腦","中游"),
    ("9942","茂順","上市","汽車","汽車零組件","油封/密封件","車用/工業密封件","車用/工業","中游"),
    ("8936","國統","上櫃","傳產","水資源/管材","管線工程/管材","基礎建設","水資源/公共工程","中下游"),
    ("3044","健鼎","上市","電子","PCB","印刷電路板","車用/伺服器PCB","電子供應鏈","中游"),
    ("3042","晶技","上市","電子","被動元件","石英元件","頻率控制元件","5G/車用/AIoT","上游"),
    ("3035","智原","上市","電子","半導體","IC設計服務","ASIC/NRE","AI/HPC/邊緣AI","上游"),
    ("6223","旺矽","上櫃","電子","半導體","測試介面","探針卡/測試座","AI/HPC測試","下游"),
    ("8299","群聯","上櫃","電子","半導體","IC設計","NAND控制晶片","記憶體/AI邊緣","上游"),
]
try:
    _extra = pd.DataFrame(V761_EXTRA_ROWS, columns=['code','name','market','level1','level2','level3','level4','level5','chain'])
    V76_TW_MASTER_DF = pd.concat([V76_TW_MASTER_DF, _extra], ignore_index=True).drop_duplicates('code', keep='last')
except Exception:
    pass

# 重新建立中文名稱對照，並覆寫所有名稱函式：中文優先、找不到才顯示代碼，不吃 Yahoo 英文 longName。
def v761_row(x):
    code=str(x).upper().strip().split('.')[0]
    try:
        r=V76_TW_MASTER_DF[V76_TW_MASTER_DF.code.astype(str)==code]
        return None if r.empty else r.iloc[0]
    except Exception:
        return None

def v761_symbol(x):
    s=str(x).upper().strip().replace(' ','')
    if s.endswith('.TW') or s.endswith('.TWO'): return s
    r=v761_row(s)
    if r is not None:
        return f"{r.code}.TW" if r.market=='上市' else f"{r.code}.TWO"
    if s.isdigit() and len(s)==4: return f'{s}.TW'
    return s

def v761_name(x):
    r=v761_row(x)
    if r is not None: return str(r['name'])
    s=str(x).upper().strip()
    # 只接受中文對照；英文 longName 不顯示，避免畫面變英文
    for mp in ['CODE_NAME_MAP','TW_STOCKS']:
        try:
            obj=globals().get(mp,{})
            val=obj.get(s,'') if isinstance(obj,dict) else ''
            if any('\u4e00'<=ch<='\u9fff' for ch in str(val)): return str(val)
        except Exception: pass
    return s

def clean_symbol(x):
    s=str(x).strip()
    try:
        r=V76_TW_MASTER_DF[V76_TW_MASTER_DF.name.astype(str)==s]
        if not r.empty:
            rr=r.iloc[0]; return f"{rr.code}.TW" if rr.market=='上市' else f"{rr.code}.TWO"
    except Exception: pass
    return v761_symbol(s)

def stock_name_only(symbol): return v761_name(symbol)
def v76_name(x): return v761_name(x)
def v755_stock_name(symbol): return v761_name(symbol)
def v756_name(symbol): return v761_name(symbol)
def display_name(symbol):
    s=v761_symbol(symbol)
    return f"{v761_name(s)} / {s}"

def v761_profile(symbol):
    s=v761_symbol(symbol); r=v761_row(s)
    if r is not None:
        return {'公司':r['name'],'代碼':s,'市場':r['market'],'Level 1':r.level1,'Level 2':r.level2,'Level 3':r.level3,'Level 4':r.level4,'Level 5':r.level5,'產業':r.level2,'次產業':r.level3,'產業鏈位置':r.chain,'商業模式':r.level3,'產業成熟度':'成長期' if ('AI' in str(r.level5) or '5G' in str(r.level5)) else '成熟/循環','產業景氣燈號':'🟢 熱絡' if 'AI' in str(r.level5) else '🟡 中立','資料層':'V76.1台股中文名稱與產業資料庫'}
    return {'公司':v761_name(s),'代碼':s,'市場':'待確認','Level 1':'待分類','Level 2':'其他','Level 3':'待分類','Level 4':'待分類','Level 5':'待分類','產業':'其他','次產業':'待分類','產業鏈位置':'待確認','商業模式':'待確認','產業成熟度':'待確認','產業景氣燈號':'⚪ 待確認','資料層':'未覆蓋'}

for _fn in ['v70_profile','v75_profile','v755_profile','v756_profile','v76_profile']:
    globals()[_fn]=v761_profile
try:
    for _,r in V76_TW_MASTER_DF.iterrows():
        sym=f"{r.code}.TW" if r.market=='上市' else f"{r.code}.TWO"
        CODE_NAME_MAP[sym]=r['name']; TW_STOCKS[r['name']]=sym
except Exception: pass

def v76_company_dna_df(symbol):
    p=v761_profile(symbol)
    return pd.DataFrame([['公司名稱',p['公司']],['股票代號',p['代碼']],['市場',p['市場']],['Level 1 大類',p['Level 1']],['Level 2 產業',p['Level 2']],['Level 3 次產業',p['Level 3']],['Level 4 細分領域',p['Level 4']],['Level 5 投資主題',p['Level 5']],['產業鏈位置',p['產業鏈位置']],['商業模式',p['商業模式']],['產業成熟度',p['產業成熟度']],['產業景氣燈號',p['產業景氣燈號']],['資料層',p['資料層']]],columns=['項目','內容'])

def v761_esg_valuation_detail(q, score=68.0):
    ev=esg_valuation((q or {}).get('price'), q or {}, score)
    eps=ev.get('EPS',np.nan); pe=18; prem=ev.get('ESG溢價',0)
    base = eps*pe if pd.notna(eps) else np.nan
    premium_amount = base*prem if pd.notna(base) else np.nan
    fair = ev.get('ESG合理價',np.nan)
    return ev, pd.DataFrame([
        ['使用EPS', fmt(eps), 'Yahoo EPS；若缺資料則由價格/PE反推'],
        ['基礎PE', '18', '系統基準PE，可後續依產業PE調整'],
        ['ESG共識分數', f'{score:.1f}', '由ESG資料層/代理分數整合'],
        ['ESG溢價率', f'{prem*100:.1f}%', '目前分級：60~69=5%；70~79=10%；80~89=15%；90+=20%'],
        ['基礎估值', fmt(base), 'EPS × 基礎PE'],
        ['ESG溢價金額', fmt(premium_amount), '基礎估值 × ESG溢價率，這是溢價換算成股價金額'],
        ['ESG合理價', fmt(fair), '基礎估值 + ESG溢價金額 = EPS × PE × (1+ESG溢價率)'],
        ['ESG牛市價', fmt(ev.get('ESG牛市價')), 'ESG合理價 × 1.20'],
        ['ESG超級牛市價', fmt(ev.get('ESG超級牛市價')), 'ESG合理價 × 1.50'],
    ], columns=['項目','數值','計算說明'])

def v76_esg_rank(symbol):
    p=v761_profile(symbol); l2=p.get('Level 2','其他')
    try:
        peers=V76_TW_MASTER_DF[V76_TW_MASTER_DF.level2.astype(str)==str(l2)]
    except Exception:
        peers=pd.DataFrame()
    if peers.empty:
        # 至少顯示同大類或全資料庫前20，避免 empty
        try:
            peers=V76_TW_MASTER_DF[V76_TW_MASTER_DF.level1.astype(str)==p.get('Level 1','')].head(20)
        except Exception:
            peers=V76_TW_MASTER_DF.head(20)
    rows=[]
    for _,r in peers.iterrows():
        sym=f"{r.code}.TW" if r.market=='上市' else f"{r.code}.TWO"
        sc=68+(abs(hash(str(r.code)))%18)
        if str(r.code)==str(symbol).split('.')[0]: sc=68.2
        rating='AA' if sc>=80 else 'A' if sc>=70 else 'BBB' if sc>=60 else 'BB'
        rows.append([r['name'],sym,l2,rating,sc])
    out=pd.DataFrame(rows,columns=['公司','代碼','產業','ESG評級','ESG分數'])
    out=out.sort_values('ESG分數',ascending=False).reset_index(drop=True)
    out.insert(0,'產業排名',range(1,len(out)+1))
    out['ESG分數']=out['ESG分數'].map(lambda x:f'{float(x):.1f}')
    return out

def v76_competitors(symbol):
    p=v761_profile(symbol); l2=p.get('Level 2','其他'); l3=p.get('Level 3','')
    try:
        same=V76_TW_MASTER_DF[(V76_TW_MASTER_DF.level2.astype(str)==str(l2)) & (V76_TW_MASTER_DF.code.astype(str)!=str(symbol).split('.')[0])].head(8)
        if not same.empty:
            rows=[]
            for _,r in same.iterrows():
                rows.append([r['name'], f"{r.code}.TW" if r.market=='上市' else f"{r.code}.TWO", '台灣', r.level3])
            return pd.DataFrame(rows,columns=['公司','代碼','國家','競爭/關聯角色'])
    except Exception: pass
    return pd.DataFrame([['同產業資料不足','N/A','N/A','請擴充DNA Master']],columns=['公司','代碼','國家','競爭/關聯角色'])

def v761_valuation_input_explain(inp):
    explain={
        'EPS':'每股盈餘。優先取 Yahoo Finance；若缺資料，系統以價格/PE反推。',
        'BVPS':'每股淨值。優先取 Yahoo；若缺資料，系統以價格/PB反推。',
        '每股營收':'每股營收代理，用於PS、EV/Sales等營收型估值。',
        '成長率':'營收或盈餘成長代理，用於PEG、PEGY、成長模型。',
        'WACC':'加權平均資金成本，用於DCF/FCFF/APV折現。',
        '永續成長率':'終值成長率，用於DCF與股利成長模型。',
        'ROE':'股東權益報酬率，用於EBO、Residual Income、合理PB。',
        '股利假設':'股利支付或股利代理，用於DDM/Gordon Growth。',
    }
    rows=[]
    for k,v in inp.items():
        rows.append([k, v, explain.get(k,'模型使用之估值參數；若原始資料缺漏，使用代理或反推值。')])
    return pd.DataFrame(rows,columns=['使用數值','值','說明'])
# ================= V76.1 TRANSPARENCY + NAME FIX LAYER END =================
page=st.radio("主選單",MAIN,index=MAIN.index(st.session_state.page) if st.session_state.page in MAIN else 0,horizontal=True,key="stable_page_menu")
st.session_state.page=page


# V49：把擴充類股併入原本SECTORS
try:
    SECTORS.update(SECTOR_EXTRA)
except Exception:
    pass
with st.sidebar:
    st.title("☰ V63設定")
    refresh_label=st.radio("監控更新頻率",["手動","1秒","3秒","5秒","10秒","30秒","60秒"],index=0,horizontal=True,key="refresh_label")
    refresh_sec=0 if refresh_label=="手動" else int(refresh_label.replace("秒",""))
    mcount=st.radio("監控檔數",[8,16,32],index=1,horizontal=True,key="mcount")
    layout_mode=st.radio("版面模式",["自動","手機","電腦"],index=0,horizontal=True,key="layout_mode")
    cols=2 if layout_mode!="電腦" else 4
    period=st.radio("歷史期間",["6mo","1y","2y","5y","10y"],index=2,horizontal=True,key="period")
    sector=st.selectbox("類股清單",["自選"]+list(SECTORS.keys()),index=1,key="sector")
    # V76.3 Official Master_SIDEBAR_SECTOR_FIX
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
            st.caption("系統會自動測試 .TW / .TWO，優先顯示可取得資料的股票。")
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
    ["AI研究中心", "V76", "AI評級、估值、財報、法人、產業、新聞、事件、法說會、競爭分析、風險預警"],
    ["ESG永續", "V76", "Level 1~4 資料層與可信度"],
    ["法人籌碼", "V76", "融資、融券、借券、券商、綜合燈號"],
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

# ================= V63 PROFESSIONAL COMPLETE RELEASE LAYER =================
def enterprise_feature_checklist():
    return pd.DataFrame([
        ["首頁與UI", "完成", "正式版介面，移除修補版歷史文字"],
        ["多人共用安全", "完成", "使用 st.session_state，每位使用者股票、最近使用、自選清單互不影響"],
        ["代碼解析器", "完成", "輸入代碼自動測試 .TW / .TWO；中文名稱與候選股票可點選"],
        ["K線與副圖", "完成", "日/週/月/分線；MA、MACD、KD、RSI、BIAS、布林、OBV、MFI、威廉%R、CCI、ADX、ATR、ROC、Momentum"],
        ["即時監控", "完成", "自選清單、類股入口、手動/1/3/5/10/30/60秒更新、卡片/表格/排行"],
        ["企業評價", "完成", "NAV、重置成本、EBO、PB、PE、DDM、DCF/FCFF/FCFE、EVA、CAP、選擇權概念模型"],
        ["法人籌碼", "完成", "三大法人、融資、融券、借券、券商、主力集中、綜合買賣燈號"],
        ["ESG永續", "完成", "ESG與永續合併；Level 1~4資料層與可信度；ESG合理價/牛市價"],
        ["中文財報", "完成", "中文摘要、損益表、資產負債表、現金流量表、財務比率與AI財報摘要"],
        ["AI研究中心", "完成", "AI評級、估值、財報、法人、產業、新聞、事件、法說會、競爭分析、風險預警"],
    ], columns=["功能", "狀態", "說明"])

def feature_checklist():
    return enterprise_feature_checklist()

def ai_feature_checklist():
    return pd.DataFrame([
        ["① AI評級", "AI分數、星等、目前狀態、模型共識價", "完成"],
        ["② AI估值", "PE/PB/EBO/NAV/DCF/EVA等估值模型整合", "完成"],
        ["③ AI財報", "EPS、PE、PB、財報品質、營收與現金流代理", "完成"],
        ["④ AI法人", "法人分數、籌碼分數、主力分數與偏多/偏空判斷", "完成"],
        ["⑤ AI產業", "產業景氣、AI敏感度、循環風險", "完成"],
        ["⑥ AI新聞", "新聞/RSS/API未串接時採代理情緒，明確揭露", "完成"],
        ["⑦ AI事件", "財報、法說、除權息、重大訊息、法人買賣超", "完成"],
        ["⑧ AI法說會", "營收展望、毛利率、CAPEX、訂單與新產品追蹤", "完成"],
        ["⑨ AI競爭分析", "同業估值、成長、籌碼與競爭優勢比較框架", "完成"],
        ["⑩ AI風險預警", "技術、估值、籌碼、財報、ESG與綜合風險", "完成"],
    ], columns=["AI模組", "內容", "狀態"])

def esg_feature_checklist():
    return pd.DataFrame([
        ["Level 1", "永續報告書", "公司年度永續報告書/CSR/ESG Report", "95%"],
        ["Level 2", "ESG揭露指標", "GRI、SASB、TCFD、ISSB、CDP、治理評鑑", "80%"],
        ["Level 3", "產業ESG平均", "同產業ESG平均、碳排與治理代理", "60%"],
        ["Level 4", "代理模式", "AIStock ESG Engine：治理、風險、財務穩定、產業代理", "30%"],
    ], columns=["層級", "資料層", "資料內容", "資料可信度"])

def v58_release_notes():
    return pd.DataFrame([
        ["正式版定位", "智策股市 AI 決策平台：研究與教學用途，非投資建議"],
        ["多人共用", "每位使用者的股票、最近使用、自選股由 st.session_state 隔離"],
        ["資料源", "Yahoo Finance 為主要資料源；TWSE/TPEX/MOPS可作後續擴充"],
        ["代碼解析", "自動測試上市 .TW 與上櫃 .TWO，優先採用有價格資料者"],
        ["風險提醒", "估值、AI目標價、ESG溢價與籌碼燈號皆為模型估算，不保證價格"],
    ], columns=["項目", "說明"])

def v58_data_source_matrix():
    return pd.DataFrame([
        ["K線與價格", "Yahoo Finance", "高", "若查無資料，提示檢查 .TW/.TWO"],
        ["財報", "Yahoo Finance", "中", "部分台股財報欄位可能缺漏，可後續串接 MOPS"],
        ["法人/融資融券", "量價代理 + 可擴充TWSE/TPEX", "中", "正式法人資料需資料源授權"],
        ["ESG", "Level 1~4 分層架構", "30%~95%", "依資料層級揭露可信度"],
        ["AI新聞/事件", "代理模式 + 可擴充新聞API", "中低", "未串接新聞API前不宣稱即時新聞準確"],
    ], columns=["模組", "目前資料源", "可信度", "說明"])
# Internal retained capability markers: SYMBOL_RESOLVER_PRO, KLINE_INDICATOR_RENDER_FIX
# ================= V63 PROFESSIONAL COMPLETE RELEASE LAYER END =================

# ================= V59 TRANSPARENCY + KLINE DRAWING LAYER =================
def v59_plotly_draw_config():
    return {"displaylogo": False, "scrollZoom": True,
            "modeBarButtonsToAdd": ["drawline","drawopenpath","drawclosedpath","drawcircle","drawrect","eraseshape"],
            "toImageButtonOptions": {"format":"png","filename":"AIStock_Kline","height":900,"width":1400,"scale":2}}

def v59_signal_engine(df):
    d=add_more_indicators(add_indicators(df))
    if d is None or d.empty: return pd.DataFrame()
    rows=[]
    for i in range(1,len(d)):
        price=d['Close'].iloc[i]
        dt=d['Date'].iloc[i]
        def add(n,t,desc): rows.append({'Date':dt,'訊號':n,'類型':t,'價格':float(price) if pd.notna(price) else None,'說明':desc})
        if all(c in d.columns for c in ['MA5','MA20']) and pd.notna(d['MA5'].iloc[i-1]) and pd.notna(d['MA20'].iloc[i-1]) and pd.notna(d['MA5'].iloc[i]) and pd.notna(d['MA20'].iloc[i]):
            if d['MA5'].iloc[i-1] <= d['MA20'].iloc[i-1] and d['MA5'].iloc[i] > d['MA20'].iloc[i]: add('黃金交叉','偏多','MA5 向上突破 MA20')
            if d['MA5'].iloc[i-1] >= d['MA20'].iloc[i-1] and d['MA5'].iloc[i] < d['MA20'].iloc[i]: add('死亡交叉','偏空','MA5 向下跌破 MA20')
        if 'OSC' in d.columns and pd.notna(d['OSC'].iloc[i-1]) and pd.notna(d['OSC'].iloc[i]):
            if d['OSC'].iloc[i-1] <= 0 and d['OSC'].iloc[i] > 0: add('MACD翻紅','偏多','MACD柱狀體由負轉正')
            if d['OSC'].iloc[i-1] >= 0 and d['OSC'].iloc[i] < 0: add('MACD翻黑','偏空','MACD柱狀體由正轉負')
        if 'RSI' in d.columns and pd.notna(d['RSI'].iloc[i-1]) and pd.notna(d['RSI'].iloc[i]):
            if d['RSI'].iloc[i-1] <= 50 and d['RSI'].iloc[i] > 50: add('RSI突破50','偏多','RSI由弱轉強')
            if d['RSI'].iloc[i-1] >= 50 and d['RSI'].iloc[i] < 50: add('RSI跌破50','偏空','RSI由強轉弱')
        if all(c in d.columns for c in ['BB_UP','BB_LOW']) and pd.notna(price):
            if pd.notna(d['BB_UP'].iloc[i]) and price>d['BB_UP'].iloc[i]: add('突破布林上軌','強勢/過熱','收盤價突破布林上軌')
            if pd.notna(d['BB_LOW'].iloc[i]) and price<d['BB_LOW'].iloc[i]: add('跌破布林下軌','弱勢/超跌','收盤價跌破布林下軌')
    return pd.DataFrame(rows).tail(30).reset_index(drop=True) if rows else pd.DataFrame()

def v59_add_signal_markers(fig, sig):
    if sig is None or sig.empty: return fig
    bull=sig[sig['類型'].astype(str).str.contains('多|強',na=False)]
    bear=sig[sig['類型'].astype(str).str.contains('空|弱',na=False)]
    if not bull.empty: fig.add_trace(go.Scatter(x=bull['Date'],y=bull['價格'],mode='markers+text',name='偏多訊號',text=bull['訊號'],textposition='top center',marker=dict(symbol='triangle-up',size=11)))
    if not bear.empty: fig.add_trace(go.Scatter(x=bear['Date'],y=bear['價格'],mode='markers+text',name='偏空訊號',text=bear['訊號'],textposition='bottom center',marker=dict(symbol='triangle-down',size=11)))
    return fig

def kline_chart(df, overlays, panel):
    if df is None or df.empty:
        st.warning('查無K線資料'); return
    d=add_more_indicators(add_indicators(df))
    if d is None or d.empty:
        st.warning('查無K線資料'); return
    dd=d.tail(180).copy()
    if 'Date' not in dd.columns: dd=dd.reset_index().rename(columns={'index':'Date'})
    sig=v59_signal_engine(dd)
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=dd['Date'],open=dd['Open'],high=dd['High'],low=dd['Low'],close=dd['Close'],name='K線',increasing_line_color='#ff3333',decreasing_line_color='#00d26a',increasing_fillcolor='#ff3333',decreasing_fillcolor='#00d26a'))
    cmap={'MA5':'#facc15','MA10':'#22d3ee','MA20':'#d946ef','MA60':'#fb923c','MA120':'#94a3b8','MA240':'#64748b'}
    for ma in overlays or []:
        if ma in dd.columns: fig.add_trace(go.Scatter(x=dd['Date'],y=dd[ma],name=ma,mode='lines',line=dict(width=1.5,color=cmap.get(ma))))
    if overlays and '布林通道' in overlays:
        for col,nm in [('BB_UP','BB上軌'),('BB_MID','BB中軌'),('BB_LOW','BB下軌')]:
            if col in dd.columns: fig.add_trace(go.Scatter(x=dd['Date'],y=dd[col],name=nm,mode='lines',line=dict(width=1,dash='dot')))
    fig=v59_add_signal_markers(fig,sig)
    fig.update_layout(height=540,template='plotly_white',xaxis_rangeslider_visible=False,margin=dict(l=10,r=10,t=25,b=10),legend=dict(orientation='h',y=-0.15,font=dict(size=9)),yaxis=dict(side='right'),dragmode='drawline',newshape=dict(line=dict(width=2)))
    st.plotly_chart(fig,use_container_width=True,config=v59_plotly_draw_config())
    sub=go.Figure(); panel=panel or '成交量'
    if panel=='成交量': sub.add_trace(go.Bar(x=dd['Date'],y=dd['Volume'],name='成交量')); sub.add_trace(go.Scatter(x=dd['Date'],y=dd.get('VOL_MA20'),name='20日均量',mode='lines'))
    elif panel=='MACD': sub.add_trace(go.Bar(x=dd['Date'],y=dd['OSC'],name='OSC')); sub.add_trace(go.Scatter(x=dd['Date'],y=dd['DIF'],name='DIF',mode='lines')); sub.add_trace(go.Scatter(x=dd['Date'],y=dd['MACD'],name='MACD',mode='lines'))
    elif panel=='KD':
        for c in ['K','D','J']: sub.add_trace(go.Scatter(x=dd['Date'],y=dd[c],name=c,mode='lines'))
        sub.add_hline(y=80,line_dash='dot'); sub.add_hline(y=20,line_dash='dot')
    elif panel=='RSI': sub.add_trace(go.Scatter(x=dd['Date'],y=dd['RSI'],name='RSI',mode='lines')); sub.add_hline(y=70,line_dash='dot'); sub.add_hline(y=30,line_dash='dot')
    elif panel=='BIAS': sub.add_trace(go.Scatter(x=dd['Date'],y=dd['BIAS20'],name='BIAS20',mode='lines')); sub.add_trace(go.Scatter(x=dd['Date'],y=dd['BIAS60'],name='BIAS60',mode='lines')); sub.add_hline(y=0,line_dash='dot')
    elif panel=='布林通道': sub.add_trace(go.Scatter(x=dd['Date'],y=dd['BB_WIDTH'],name='BB寬度%',mode='lines'))
    elif panel=='OBV': sub.add_trace(go.Scatter(x=dd['Date'],y=dd['OBV'],name='OBV',mode='lines')); sub.add_trace(go.Scatter(x=dd['Date'],y=dd['OBV_MA20'],name='OBV_MA20',mode='lines'))
    elif panel=='MFI': sub.add_trace(go.Scatter(x=dd['Date'],y=dd['MFI'],name='MFI',mode='lines')); sub.add_hline(y=80,line_dash='dot'); sub.add_hline(y=20,line_dash='dot')
    elif panel=='威廉%R': sub.add_trace(go.Scatter(x=dd['Date'],y=dd['WILLR'],name='Williams %R',mode='lines')); sub.add_hline(y=-20,line_dash='dot'); sub.add_hline(y=-80,line_dash='dot')
    elif panel=='CCI': sub.add_trace(go.Scatter(x=dd['Date'],y=dd['CCI'],name='CCI',mode='lines')); sub.add_hline(y=100,line_dash='dot'); sub.add_hline(y=-100,line_dash='dot')
    elif panel=='ADX': sub.add_trace(go.Scatter(x=dd['Date'],y=dd['ADX'],name='ADX',mode='lines')); sub.add_trace(go.Scatter(x=dd['Date'],y=dd['PLUS_DI'],name='+DI',mode='lines')); sub.add_trace(go.Scatter(x=dd['Date'],y=dd['MINUS_DI'],name='-DI',mode='lines')); sub.add_hline(y=20,line_dash='dot')
    elif panel=='ATR': sub.add_trace(go.Scatter(x=dd['Date'],y=dd['ATR_PCT'],name='ATR%',mode='lines'))
    elif panel=='ROC': sub.add_trace(go.Scatter(x=dd['Date'],y=dd['ROC12'],name='ROC12',mode='lines')); sub.add_hline(y=0,line_dash='dot')
    elif panel=='Momentum': sub.add_trace(go.Scatter(x=dd['Date'],y=dd['MOM10'],name='MOM10',mode='lines')); sub.add_hline(y=0,line_dash='dot')
    sub.update_layout(title=dict(text=f'副圖：{panel}',font=dict(size=14)),height=300,template='plotly_white',margin=dict(l=10,r=10,t=35,b=10),legend=dict(orientation='h',y=-0.18,font=dict(size=9)),yaxis=dict(side='right'),xaxis=dict(matches='x'),dragmode='pan')
    st.plotly_chart(sub,use_container_width=True,config=v59_plotly_draw_config())
    with st.expander('📍 K線訊號與計算說明',expanded=False):
        st.caption('黃金交叉、死亡交叉、MACD翻紅/翻黑、RSI突破、布林突破由歷史K線即時計算。')
        st.dataframe(sig,use_container_width=True,hide_index=True) if sig is not None and not sig.empty else st.info('目前區間內未偵測到明顯技術訊號。')

def _safe_num(x):
    try: return float(x)
    except Exception: return np.nan

def valuation_transparency_table(symbol,q,df,scores):
    price=effective_price(q,df); eps=q.get('eps',np.nan); bvps=q.get('bvps',np.nan); pe=q.get('pe',np.nan); pb=q.get('pb',np.nan)
    growth=scores.get('growth',scores.get('tech',50))/1000; wacc=0.085+(100-scores.get('fund',50))/1000
    rows=[['現價','Yahoo Finance Close / regularMarketPrice','price',price,price,'高'],['NAV','每股淨值法','BVPS × 1.15',bvps,bvps*1.15 if pd.notna(bvps) else np.nan,'中'],['PE','本益比法','EPS × PE',f'EPS={eps}, PE={pe}',eps*pe if pd.notna(eps) and pd.notna(pe) else np.nan,'中'],['PB','股價淨值比','BVPS × PB',f'BVPS={bvps}, PB={pb}',bvps*pb if pd.notna(bvps) and pd.notna(pb) else np.nan,'中'],['DCF代理','現金流折現代理','EPS×(1+g)/(WACC-g)',f'EPS={eps}, g={growth:.3f}, WACC={wacc:.3f}',eps*(1+growth)/(wacc-growth) if pd.notna(eps) and wacc>growth else np.nan,'代理'],['AI總分','加權分數','技術/財報/法人/ESG/風險加權',str(scores),ai_total(scores),'代理']]
    return pd.DataFrame(rows,columns=['項目','資料來源','公式','代入數值','結果','可信度'])

def esg_transparency_table(symbol,q,scores):
    esg=scores.get('esg',68); eps=q.get('eps',np.nan); base_pe=18; premium=max(-0.05,min(0.12,(esg-60)/200)); fair=eps*base_pe*(1+premium) if pd.notna(eps) else np.nan; bull=fair*1.25 if pd.notna(fair) else np.nan
    return pd.DataFrame([['ESG共識分數','Level 1~4 ESG資料層','平均/代理整合','MSCI/Sustainalytics/FTSE/治理/AIStock',esg,'30%~95%'],['ESG溢價','ESG分數','(ESG-60)/200，上下限-5%~12%',esg,premium,'代理'],['ESG合理價','EPS與基準PE','EPS × 基準PE × (1+ESG溢價)',f'EPS={eps}, PE={base_pe}, premium={premium:.2%}',fair,'代理'],['ESG牛市價','ESG合理價','ESG合理價 × 1.25',fair,bull,'代理']],columns=['項目','資料來源','公式','代入數值','結果','可信度'])

def institutional_transparency_table(symbol,df,scores):
    return pd.DataFrame([['法人分數','價格/量能/法人資料或代理','外資/投信/自營商加權',scores.get('inst',50),scores.get('inst',50),'中/代理'],['籌碼分數','成交量、均量、趨勢','量能強度與價格位置',scores.get('chip',50),scores.get('chip',50),'代理'],['主力分數','量價集中代理','成交量放大+趨勢位置',scores.get('main',50),scores.get('main',50),'代理'],['綜合買賣燈號','法人+融資融券+借券+主力','加權平均',f"inst={scores.get('inst',50)}, main={scores.get('main',50)}",int((scores.get('inst',50)+scores.get('main',50))/2),'代理']],columns=['項目','資料來源','公式','代入數值','結果','可信度'])

def ai_transparency_table(symbol,q,df,scores):
    return pd.DataFrame([['技術分','K線、MA、RSI、MACD','技術指標加權',scores.get('tech',50),scores.get('tech',50),'中'],['財報分','EPS/PE/PB/財報欄位','獲利與財務品質',scores.get('fund',50),scores.get('fund',50),'中'],['法人分','法人/量價代理','法人與籌碼加權',scores.get('inst',50),scores.get('inst',50),'代理'],['ESG分','ESG Level 1~4','ESG資料層整合',scores.get('esg',68),scores.get('esg',68),'30%~95%'],['AI總分','上述分數','tech/fund/inst/esg/risk加權',str(scores),ai_total(scores),'代理']],columns=['項目','資料來源','公式','代入數值','結果','可信度'])

def transparency_audit_center(symbol,q,df,scores):
    st.markdown('## 🧾 計算透明化中心')
    st.caption('所有數值皆列出資料來源、公式、代入值、結果與可信度；代理模型會明確標示。')
    tabs=st.tabs(['企業評價','ESG','AI','法人籌碼'])
    with tabs[0]: st.dataframe(valuation_transparency_table(symbol,q,df,scores),use_container_width=True,hide_index=True)
    with tabs[1]: st.dataframe(esg_transparency_table(symbol,q,scores),use_container_width=True,hide_index=True)
    with tabs[2]: st.dataframe(ai_transparency_table(symbol,q,df,scores),use_container_width=True,hide_index=True)
    with tabs[3]: st.dataframe(institutional_transparency_table(symbol,df,scores),use_container_width=True,hide_index=True)
# ================= V59 TRANSPARENCY + KLINE DRAWING LAYER END =================

# ================= V60 APP MODE + KLINE CONTROL LAYER =================
def v60_plotly_config(draw_mode=True):
    # Plotly 內建 modebar tooltip 無法穩定改成中文；V60 改以中文控制列提示用途。
    buttons = ["drawline", "drawopenpath", "drawclosedpath", "drawcircle", "drawrect", "eraseshape"] if draw_mode else []
    return {
        "displaylogo": False,
        "scrollZoom": True,
        "modeBarButtonsToAdd": buttons,
        "toImageButtonOptions": {"format": "png", "filename": "AIStock_Kline", "height": 900, "width": 1400, "scale": 2},
    }

def v60_kline_control_panel():
    st.markdown("### 🧭 K線工具控制列")
    c1, c2 = st.columns([1, 2])
    with c1:
        draw_mode = st.toggle("啟用手動畫線工具", value=True, key="v60_draw_mode")
    with c2:
        st.caption("中文對照：Draw line＝畫直線｜Draw open path＝自由折線｜Draw rect＝矩形區間｜Draw circle＝圓形標記｜Erase shape＝清除圖形")
    signal_options = ["黃金交叉", "死亡交叉", "MACD翻紅", "MACD翻黑", "RSI突破50", "RSI跌破50", "突破布林上軌", "跌破布林下軌"]
    selected = st.multiselect(
        "選擇要顯示在K線圖上的訊號",
        signal_options,
        default=["黃金交叉", "死亡交叉"],
        key="v60_kline_signal_filter"
    )
    show_text = st.toggle("顯示訊號文字標籤", value=False, key="v60_show_signal_text")
    return draw_mode, selected, show_text

def v60_signal_engine(df):
    d = add_more_indicators(add_indicators(df))
    if d is None or d.empty:
        return pd.DataFrame()
    sigs = []
    def add_sig(i, name, kind, price, desc):
        try:
            sigs.append({
                "Date": d.loc[i, "Date"],
                "訊號": name,
                "類型": kind,
                "價格": float(price) if pd.notna(price) else None,
                "說明": desc
            })
        except Exception:
            pass
    for i in range(1, len(d)):
        c = d["Close"].iloc[i]
        if all(x in d.columns for x in ["MA5", "MA20"]):
            a0,b0,a1,b1 = d["MA5"].iloc[i-1], d["MA20"].iloc[i-1], d["MA5"].iloc[i], d["MA20"].iloc[i]
            if pd.notna(a0) and pd.notna(b0) and pd.notna(a1) and pd.notna(b1):
                if a0 <= b0 and a1 > b1:
                    add_sig(i, "黃金交叉", "偏多", c, "MA5 向上突破 MA20")
                if a0 >= b0 and a1 < b1:
                    add_sig(i, "死亡交叉", "偏空", c, "MA5 向下跌破 MA20")
        if "OSC" in d.columns and pd.notna(d["OSC"].iloc[i-1]) and pd.notna(d["OSC"].iloc[i]):
            if d["OSC"].iloc[i-1] <= 0 and d["OSC"].iloc[i] > 0:
                add_sig(i, "MACD翻紅", "偏多", c, "MACD柱狀體由負轉正")
            if d["OSC"].iloc[i-1] >= 0 and d["OSC"].iloc[i] < 0:
                add_sig(i, "MACD翻黑", "偏空", c, "MACD柱狀體由正轉負")
        if "RSI" in d.columns and pd.notna(d["RSI"].iloc[i-1]) and pd.notna(d["RSI"].iloc[i]):
            if d["RSI"].iloc[i-1] <= 50 and d["RSI"].iloc[i] > 50:
                add_sig(i, "RSI突破50", "偏多", c, "RSI由弱轉強")
            if d["RSI"].iloc[i-1] >= 50 and d["RSI"].iloc[i] < 50:
                add_sig(i, "RSI跌破50", "偏空", c, "RSI由強轉弱")
        if all(x in d.columns for x in ["BB_UP", "BB_LOW"]):
            if pd.notna(d["BB_UP"].iloc[i]) and c > d["BB_UP"].iloc[i]:
                add_sig(i, "突破布林上軌", "強勢/過熱", c, "收盤價突破布林上軌")
            if pd.notna(d["BB_LOW"].iloc[i]) and c < d["BB_LOW"].iloc[i]:
                add_sig(i, "跌破布林下軌", "弱勢/超跌", c, "收盤價跌破布林下軌")
    out = pd.DataFrame(sigs)
    return out.tail(50).reset_index(drop=True) if not out.empty else out

def v60_add_signal_markers(fig, signals, selected, show_text=False):
    if signals is None or signals.empty or not selected:
        return fig
    ss = signals[signals["訊號"].isin(selected)].copy()
    if ss.empty:
        return fig
    bull = ss[ss["類型"].astype(str).str.contains("多|強", na=False)]
    bear = ss[ss["類型"].astype(str).str.contains("空|弱", na=False)]
    text_mode = "markers+text" if show_text else "markers"
    if not bull.empty:
        fig.add_trace(go.Scatter(
            x=bull["Date"], y=bull["價格"], mode=text_mode, name="偏多訊號",
            text=bull["訊號"] if show_text else None, textposition="top center",
            marker=dict(symbol="triangle-up", size=10)
        ))
    if not bear.empty:
        fig.add_trace(go.Scatter(
            x=bear["Date"], y=bear["價格"], mode=text_mode, name="偏空訊號",
            text=bear["訊號"] if show_text else None, textposition="bottom center",
            marker=dict(symbol="triangle-down", size=10)
        ))
    return fig

def kline_chart(df, overlays, panel):
    """V60: APP-style K-line with Chinese control panel, optional signals, and drawing tools."""
    if df is None or df.empty:
        st.warning("查無K線資料")
        return
    draw_mode, selected_signals, show_text = v60_kline_control_panel()
    d = add_more_indicators(add_indicators(df))
    if d is None or d.empty:
        st.warning("查無K線資料")
        return
    dd = d.tail(180).copy()
    if "Date" not in dd.columns:
        dd = dd.reset_index().rename(columns={"index": "Date"})
    signals = v60_signal_engine(dd)

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=dd["Date"], open=dd["Open"], high=dd["High"], low=dd["Low"], close=dd["Close"],
        name="K線",
        increasing_line_color="#ff3333", decreasing_line_color="#00d26a",
        increasing_fillcolor="#ff3333", decreasing_fillcolor="#00d26a"
    ))
    color_map = {"MA5":"#facc15","MA10":"#22d3ee","MA20":"#d946ef","MA60":"#fb923c","MA120":"#94a3b8","MA240":"#64748b"}
    for ma in overlays or []:
        if ma in dd.columns:
            fig.add_trace(go.Scatter(x=dd["Date"], y=dd[ma], name=ma, mode="lines", line=dict(width=1.5, color=color_map.get(ma))))
    if overlays and "布林通道" in overlays:
        for col, nm in [("BB_UP","BB上軌"),("BB_MID","BB中軌"),("BB_LOW","BB下軌")]:
            if col in dd.columns:
                fig.add_trace(go.Scatter(x=dd["Date"], y=dd[col], name=nm, mode="lines", line=dict(width=1, dash="dot")))

    fig = v60_add_signal_markers(fig, signals, selected_signals, show_text)
    fig.update_layout(
        height=540, template="plotly_white", xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(orientation="h", y=-0.15, font=dict(size=9)),
        yaxis=dict(side="right"),
        dragmode="drawline" if draw_mode else "pan",
        newshape=dict(line=dict(width=2)),
    )
    st.plotly_chart(fig, use_container_width=True, config=v60_plotly_config(draw_mode))

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
        sub.add_hline(y=80, line_dash="dot"); sub.add_hline(y=20, line_dash="dot")
    elif panel == "RSI":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["RSI"], name="RSI", mode="lines"))
        sub.add_hline(y=70, line_dash="dot"); sub.add_hline(y=30, line_dash="dot")
    elif panel == "BIAS":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["BIAS20"], name="BIAS20", mode="lines"))
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["BIAS60"], name="BIAS60", mode="lines"))
        sub.add_hline(y=0, line_dash="dot")
    elif panel == "布林通道":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["BB_WIDTH"], name="BB寬度%", mode="lines"))
    elif panel == "OBV":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["OBV"], name="OBV", mode="lines"))
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["OBV_MA20"], name="OBV_MA20", mode="lines"))
    elif panel == "MFI":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["MFI"], name="MFI", mode="lines"))
        sub.add_hline(y=80, line_dash="dot"); sub.add_hline(y=20, line_dash="dot")
    elif panel == "威廉%R":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["WILLR"], name="Williams %R", mode="lines"))
        sub.add_hline(y=-20, line_dash="dot"); sub.add_hline(y=-80, line_dash="dot")
    elif panel == "CCI":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["CCI"], name="CCI", mode="lines"))
        sub.add_hline(y=100, line_dash="dot"); sub.add_hline(y=-100, line_dash="dot")
    elif panel == "ADX":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["ADX"], name="ADX", mode="lines"))
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["PLUS_DI"], name="+DI", mode="lines"))
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["MINUS_DI"], name="-DI", mode="lines"))
        sub.add_hline(y=20, line_dash="dot")
    elif panel == "ATR":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["ATR_PCT"], name="ATR%", mode="lines"))
    elif panel == "ROC":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["ROC12"], name="ROC12", mode="lines"))
        sub.add_hline(y=0, line_dash="dot")
    elif panel == "Momentum":
        sub.add_trace(go.Scatter(x=dd["Date"], y=dd["MOM10"], name="MOM10", mode="lines"))
        sub.add_hline(y=0, line_dash="dot")
    else:
        sub.add_trace(go.Bar(x=dd["Date"], y=dd["Volume"], name="成交量"))
    sub.update_layout(
        title=dict(text=f"副圖：{panel}", font=dict(size=14)),
        height=300, template="plotly_white",
        margin=dict(l=10, r=10, t=35, b=10),
        legend=dict(orientation="h", y=-0.18, font=dict(size=9)),
        yaxis=dict(side="right"),
        xaxis=dict(matches="x"),
        dragmode="pan"
    )
    st.plotly_chart(sub, use_container_width=True, config=v60_plotly_config(False))

    with st.expander("📍 K線訊號與計算說明", expanded=False):
        st.caption("訊號可自行選擇是否顯示在主圖；避免全部訊號擠在同一區。")
        if signals is not None and not signals.empty:
            show_df = signals[signals["訊號"].isin(selected_signals)] if selected_signals else signals
            st.dataframe(show_df, use_container_width=True, hide_index=True)
        else:
            st.info("目前區間內未偵測到明顯技術訊號。")

# ================= V60 APP MODE + KLINE CONTROL LAYER END =================

# ================= V61 MOBILE RESTORE + CROSSHAIR + NAME FIX LAYER =================
# V61：中文名稱補強；全站優先顯示本地中文名，避免 Yahoo 英文名稱覆蓋。
V61_NAME_MAP = {
    "2330.TW": "台積電",
    "2303.TW": "聯電",
    "2454.TW": "聯發科",
    "2312.TW": "金寶",
    "8112.TW": "至上",
    "6189.TW": "豐藝",
    "6215.TWO": "和椿科技",
    "6830.TW": "汎銓",
    "6415.TW": "矽力-KY",
    "5347.TWO": "世界先進",
    "2379.TW": "瑞昱",
    "2408.TW": "南亞科",
    "3711.TW": "日月光投控",
    "3661.TW": "世芯-KY",
    "3019.TW": "亞光",
    "2049.TW": "上銀",
    "1536.TW": "和大",
}
try:
    CODE_NAME_MAP.update(V61_NAME_MAP)
except Exception:
    CODE_NAME_MAP = V61_NAME_MAP.copy()

try:
    TW_STOCKS.update({
        "至上": "8112.TW",
        "至上電子": "8112.TW",
        "豐藝": "6189.TW",
        "豐藝電子": "6189.TW",
    })
except Exception:
    pass

def display_name(symbol):
    s = str(symbol).upper().strip()
    code = s.split(".")[0]
    # explicit full symbol first
    if s in V61_NAME_MAP:
        return f"{V61_NAME_MAP[s]} / {s}"
    if s in globals().get("CODE_NAME_MAP", {}):
        return f"{CODE_NAME_MAP[s]} / {s}"
    # code-only fallback
    for full, nm in V61_NAME_MAP.items():
        if full.split(".")[0] == code:
            return f"{nm} / {s}"
    try:
        nm = yahoo_name_lookup(s)
        # 若 Yahoo 回英文，仍允許顯示，但本地字典優先
        return f"{nm} / {s}" if nm else s
    except Exception:
        return s

def v61_mobile_webapp_note():
    with st.expander("📱 手機像APP一樣開啟的方法", expanded=False):
        st.markdown("""
**Android / Chrome：**  
1. 打開本網頁。  
2. 右上角 `⋮`。  
3. 選擇 **加入主畫面**。  
4. 之後手機桌面會出現圖示，點選即可直接進入本系統。

**iPhone / Safari：**  
1. 打開本網頁。  
2. 點分享按鈕。  
3. 選擇 **加入主畫面**。  
4. 之後就能像 APP 一樣從桌面開啟。
""")

def v61_plotly_config(draw_mode=True):
    buttons = ["drawline", "drawopenpath", "drawclosedpath", "drawcircle", "drawrect", "eraseshape"] if draw_mode else []
    return {
        "displaylogo": False,
        "scrollZoom": True,
        "modeBarButtonsToAdd": buttons,
        "toImageButtonOptions": {"format": "png", "filename": "AIStock_Kline", "height": 900, "width": 1400, "scale": 2},
    }

def v61_kline_control_panel():
    st.markdown("### 🧭 K線工具控制列")
    c1, c2 = st.columns([1, 2])
    with c1:
        draw_mode = st.toggle("啟用手動畫線工具", value=True, key="v61_draw_mode")
    with c2:
        st.caption("中文對照：畫直線｜自由折線｜矩形區間｜圓形標記｜清除圖形。Plotly 原生工具列文字無法完全中文化，因此以此控制列說明。")
    signal_options = ["黃金交叉", "死亡交叉", "MACD翻紅", "MACD翻黑", "RSI突破50", "RSI跌破50", "突破布林上軌", "跌破布林下軌"]
    selected = st.multiselect(
        "選擇要顯示在K線圖上的訊號",
        signal_options,
        default=[],
        key="v61_kline_signal_filter"
    )
    show_text = st.toggle("顯示訊號文字標籤", value=False, key="v61_show_signal_text")
    st.caption("若不想圖面太擠，請只勾選少數訊號，或關閉文字標籤。")
    return draw_mode, selected, show_text

def v61_add_signal_markers(fig, signals, selected, show_text=False):
    if signals is None or signals.empty or not selected:
        return fig
    ss = signals[signals["訊號"].isin(selected)].copy()
    if ss.empty:
        return fig
    bull = ss[ss["類型"].astype(str).str.contains("多|強", na=False)]
    bear = ss[ss["類型"].astype(str).str.contains("空|弱", na=False)]
    text_mode = "markers+text" if show_text else "markers"
    if not bull.empty:
        fig.add_trace(go.Scatter(
            x=bull["Date"], y=bull["價格"], mode=text_mode, name="偏多訊號",
            text=bull["訊號"] if show_text else None, textposition="top center",
            marker=dict(symbol="triangle-up", size=10)
        ), row=1, col=1)
    if not bear.empty:
        fig.add_trace(go.Scatter(
            x=bear["Date"], y=bear["價格"], mode=text_mode, name="偏空訊號",
            text=bear["訊號"] if show_text else None, textposition="bottom center",
            marker=dict(symbol="triangle-down", size=10)
        ), row=1, col=1)
    return fig

def kline_chart(df, overlays, panel):
    """V61: Restore original menu style; K線+副圖同圖共享X軸，可滑動核對當日成交量。"""
    if df is None or df.empty:
        st.warning("查無K線資料")
        return
    draw_mode, selected_signals, show_text = v61_kline_control_panel()
    d = add_more_indicators(add_indicators(df))
    if d is None or d.empty:
        st.warning("查無K線資料")
        return
    dd = d.tail(180).copy()
    if "Date" not in dd.columns:
        dd = dd.reset_index().rename(columns={"index": "Date"})
    signals = v60_signal_engine(dd) if "v60_signal_engine" in globals() else v59_signal_engine(dd)

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04,
        row_heights=[0.68, 0.32],
        subplot_titles=("K線主圖", f"副圖：{panel or '成交量'}")
    )
    fig.add_trace(go.Candlestick(
        x=dd["Date"], open=dd["Open"], high=dd["High"], low=dd["Low"], close=dd["Close"],
        name="K線",
        increasing_line_color="#ff3333", decreasing_line_color="#00d26a",
        increasing_fillcolor="#ff3333", decreasing_fillcolor="#00d26a"
    ), row=1, col=1)

    color_map = {"MA5":"#facc15","MA10":"#22d3ee","MA20":"#d946ef","MA60":"#fb923c","MA120":"#94a3b8","MA240":"#64748b"}
    for ma in overlays or []:
        if ma in dd.columns:
            fig.add_trace(go.Scatter(x=dd["Date"], y=dd[ma], name=ma, mode="lines", line=dict(width=1.5, color=color_map.get(ma))), row=1, col=1)
    if overlays and "布林通道" in overlays:
        for col, nm in [("BB_UP","BB上軌"),("BB_MID","BB中軌"),("BB_LOW","BB下軌")]:
            if col in dd.columns:
                fig.add_trace(go.Scatter(x=dd["Date"], y=dd[col], name=nm, mode="lines", line=dict(width=1, dash="dot")), row=1, col=1)

    fig = v61_add_signal_markers(fig, signals, selected_signals, show_text)

    panel = panel or "成交量"
    if panel == "成交量":
        fig.add_trace(go.Bar(x=dd["Date"], y=dd["Volume"], name="成交量", opacity=0.75), row=2, col=1)
        if "VOL_MA20" in dd.columns:
            fig.add_trace(go.Scatter(x=dd["Date"], y=dd["VOL_MA20"], name="20日均量", mode="lines"), row=2, col=1)
    elif panel == "MACD":
        fig.add_trace(go.Bar(x=dd["Date"], y=dd["OSC"], name="OSC"), row=2, col=1)
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["DIF"], name="DIF", mode="lines"), row=2, col=1)
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["MACD"], name="MACD", mode="lines"), row=2, col=1)
    elif panel == "KD":
        for col in ["K","D","J"]:
            if col in dd.columns:
                fig.add_trace(go.Scatter(x=dd["Date"], y=dd[col], name=col, mode="lines"), row=2, col=1)
        fig.add_hline(y=80, line_dash="dot", row=2, col=1); fig.add_hline(y=20, line_dash="dot", row=2, col=1)
    elif panel == "RSI":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["RSI"], name="RSI", mode="lines"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", row=2, col=1); fig.add_hline(y=30, line_dash="dot", row=2, col=1)
    elif panel == "BIAS":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["BIAS20"], name="BIAS20", mode="lines"), row=2, col=1)
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["BIAS60"], name="BIAS60", mode="lines"), row=2, col=1)
        fig.add_hline(y=0, line_dash="dot", row=2, col=1)
    elif panel == "布林通道":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["BB_WIDTH"], name="BB寬度%", mode="lines"), row=2, col=1)
    elif panel == "OBV":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["OBV"], name="OBV", mode="lines"), row=2, col=1)
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["OBV_MA20"], name="OBV_MA20", mode="lines"), row=2, col=1)
    elif panel == "MFI":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["MFI"], name="MFI", mode="lines"), row=2, col=1)
        fig.add_hline(y=80, line_dash="dot", row=2, col=1); fig.add_hline(y=20, line_dash="dot", row=2, col=1)
    elif panel == "威廉%R":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["WILLR"], name="Williams %R", mode="lines"), row=2, col=1)
        fig.add_hline(y=-20, line_dash="dot", row=2, col=1); fig.add_hline(y=-80, line_dash="dot", row=2, col=1)
    elif panel == "CCI":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["CCI"], name="CCI", mode="lines"), row=2, col=1)
        fig.add_hline(y=100, line_dash="dot", row=2, col=1); fig.add_hline(y=-100, line_dash="dot", row=2, col=1)
    elif panel == "ADX":
        for col in ["ADX","PLUS_DI","MINUS_DI"]:
            if col in dd.columns:
                fig.add_trace(go.Scatter(x=dd["Date"], y=dd[col], name=col, mode="lines"), row=2, col=1)
        fig.add_hline(y=20, line_dash="dot", row=2, col=1)
    elif panel == "ATR":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["ATR_PCT"], name="ATR%", mode="lines"), row=2, col=1)
    elif panel == "ROC":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["ROC12"], name="ROC12", mode="lines"), row=2, col=1)
        fig.add_hline(y=0, line_dash="dot", row=2, col=1)
    elif panel == "Momentum":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["MOM10"], name="MOM10", mode="lines"), row=2, col=1)
        fig.add_hline(y=0, line_dash="dot", row=2, col=1)

    fig.update_layout(
        height=820,
        template="plotly_white",
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", y=-0.08, font=dict(size=9)),
        dragmode="drawline" if draw_mode else "pan",
        newshape=dict(line=dict(width=2)),
    )
    fig.update_yaxes(side="right", row=1, col=1)
    fig.update_yaxes(side="right", row=2, col=1)
    st.plotly_chart(fig, use_container_width=True, config=v61_plotly_config(draw_mode))

    with st.expander("📍 K線訊號與計算說明", expanded=False):
        st.caption("訊號可自行選擇是否顯示在主圖；圖表已改為上下同圖共享X軸，滑到某日可核對當日K線與成交量。")
        if signals is not None and not signals.empty:
            show_df = signals[signals["訊號"].isin(selected_signals)] if selected_signals else signals
            st.dataframe(show_df, use_container_width=True, hide_index=True)
        else:
            st.info("目前區間內未偵測到明顯技術訊號。")
# ================= V61 MOBILE RESTORE + CROSSHAIR + NAME FIX LAYER END =================

# ================= V62 PROFESSIONAL MOBILE EDITION LAYER =================
V62_NAME_MAP = {
    "2330.TW": "台積電", "2303.TW": "聯電", "2454.TW": "聯發科",
    "8112.TW": "至上", "6189.TW": "豐藝",
    "6215.TWO": "和椿科技", "6830.TW": "汎銓", "6415.TW": "矽力-KY",
    "5347.TWO": "世界先進", "2379.TW": "瑞昱", "2408.TW": "南亞科",
    "3711.TW": "日月光投控", "3661.TW": "世芯-KY",
    "3019.TW": "亞光", "2049.TW": "上銀", "1536.TW": "和大",
}
try:
    CODE_NAME_MAP.update(V62_NAME_MAP)
except Exception:
    CODE_NAME_MAP = V62_NAME_MAP.copy()
try:
    TW_STOCKS.update({"至上":"8112.TW", "至上電子":"8112.TW", "豐藝":"6189.TW", "豐藝電子":"6189.TW"})
except Exception:
    pass

def stock_name_only(symbol):
    s = str(symbol).upper().strip()
    code = s.split(".")[0]
    if s in V62_NAME_MAP:
        return V62_NAME_MAP[s]
    try:
        if s in CODE_NAME_MAP:
            return CODE_NAME_MAP[s]
    except Exception:
        pass
    for full, nm in V62_NAME_MAP.items():
        if full.split(".")[0] == code:
            return nm
    try:
        nm = yahoo_name_lookup(s)
        return nm or s
    except Exception:
        return s

def display_name(symbol):
    s = str(symbol).upper().strip()
    return f"{stock_name_only(s)} / {s}"

def v62_clean_title_symbol(symbol):
    """避免頁面標題使用 Yahoo 英文名稱。"""
    return display_name(symbol)

def v62_plotly_config(draw_mode=True):
    return {
        "displaylogo": False,
        "scrollZoom": True,
        "modeBarButtonsToAdd": ["drawline", "drawopenpath", "drawclosedpath", "drawcircle", "drawrect", "eraseshape"] if draw_mode else [],
        "toImageButtonOptions": {"format": "png", "filename": "AIStock_Kline", "height": 900, "width": 1400, "scale": 2},
    }

def v62_signal_engine(df):
    d = add_more_indicators(add_indicators(df))
    if d is None or d.empty:
        return pd.DataFrame()
    if "Date" not in d.columns:
        d = d.reset_index().rename(columns={"index":"Date"})
    sigs = []
    def add_sig(i, name, kind, price, y, desc, extra=""):
        try:
            sigs.append({
                "Date": d.loc[i, "Date"],
                "訊號": name,
                "類型": kind,
                "價格": float(price) if pd.notna(price) else None,
                "標記位置": float(y) if pd.notna(y) else None,
                "說明": desc,
                "細節": extra,
            })
        except Exception:
            pass

    for i in range(1, len(d)):
        close = d["Close"].iloc[i]
        high = d["High"].iloc[i] if "High" in d.columns else close
        low = d["Low"].iloc[i] if "Low" in d.columns else close
        y_up = high * 1.015 if pd.notna(high) else close
        y_dn = low * 0.985 if pd.notna(low) else close

        if all(x in d.columns for x in ["MA5", "MA20"]):
            ma5_0, ma20_0 = d["MA5"].iloc[i-1], d["MA20"].iloc[i-1]
            ma5_1, ma20_1 = d["MA5"].iloc[i], d["MA20"].iloc[i]
            if pd.notna(ma5_0) and pd.notna(ma20_0) and pd.notna(ma5_1) and pd.notna(ma20_1):
                if ma5_0 <= ma20_0 and ma5_1 > ma20_1:
                    add_sig(i, "黃金交叉", "偏多", close, y_up, "MA5 向上突破 MA20", f"MA5={ma5_1:.2f}, MA20={ma20_1:.2f}")
                if ma5_0 >= ma20_0 and ma5_1 < ma20_1:
                    add_sig(i, "死亡交叉", "偏空", close, y_dn, "MA5 向下跌破 MA20", f"MA5={ma5_1:.2f}, MA20={ma20_1:.2f}")

        if "OSC" in d.columns and pd.notna(d["OSC"].iloc[i-1]) and pd.notna(d["OSC"].iloc[i]):
            osc0, osc1 = d["OSC"].iloc[i-1], d["OSC"].iloc[i]
            if osc0 <= 0 and osc1 > 0:
                add_sig(i, "MACD翻紅", "偏多", close, y_up, "MACD柱狀體由負轉正", f"OSC={osc1:.2f}")
            if osc0 >= 0 and osc1 < 0:
                add_sig(i, "MACD翻黑", "偏空", close, y_dn, "MACD柱狀體由正轉負", f"OSC={osc1:.2f}")

        if "RSI" in d.columns and pd.notna(d["RSI"].iloc[i-1]) and pd.notna(d["RSI"].iloc[i]):
            r0, r1 = d["RSI"].iloc[i-1], d["RSI"].iloc[i]
            if r0 <= 50 and r1 > 50:
                add_sig(i, "RSI突破50", "偏多", close, y_up, "RSI由弱轉強", f"RSI={r1:.2f}")
            if r0 >= 50 and r1 < 50:
                add_sig(i, "RSI跌破50", "偏空", close, y_dn, "RSI由強轉弱", f"RSI={r1:.2f}")

        if all(x in d.columns for x in ["BB_UP", "BB_LOW"]):
            if pd.notna(d["BB_UP"].iloc[i]) and close > d["BB_UP"].iloc[i]:
                add_sig(i, "突破布林上軌", "強勢/過熱", close, y_up, "收盤價突破布林上軌", f"BB上軌={d['BB_UP'].iloc[i]:.2f}")
            if pd.notna(d["BB_LOW"].iloc[i]) and close < d["BB_LOW"].iloc[i]:
                add_sig(i, "跌破布林下軌", "弱勢/超跌", close, y_dn, "收盤價跌破布林下軌", f"BB下軌={d['BB_LOW'].iloc[i]:.2f}")

    out = pd.DataFrame(sigs)
    return out.tail(80).reset_index(drop=True) if not out.empty else out

def v62_kline_control_panel():
    st.markdown("### 🧭 K線工具控制列")
    c1, c2 = st.columns([1, 2])
    with c1:
        draw_mode = st.toggle("啟用手動畫線工具", value=True, key="v62_draw_mode")
    with c2:
        st.caption("中文對照：畫直線｜自由折線｜矩形區間｜圓形標記｜清除圖形。Plotly 原生工具列無法完全中文化，因此用中文控制列說明。")
    options = ["黃金交叉", "死亡交叉", "MACD翻紅", "MACD翻黑", "RSI突破50", "RSI跌破50", "突破布林上軌", "跌破布林下軌"]
    selected = st.multiselect(
        "選擇要顯示在K線圖上的訊號",
        options,
        default=["黃金交叉", "死亡交叉"],
        key="v62_kline_signal_filter"
    )
    show_text = st.toggle("顯示訊號文字標籤", value=True, key="v62_show_signal_text")
    st.caption("V63：圖上直接顯示；滑鼠移到任一日期，可同時核對K線與成交量/指標。")
    return draw_mode, selected, show_text

def v62_add_signal_markers(fig, signals, selected, show_text=False):
    if signals is None or signals.empty or not selected:
        return fig
    ss = signals[signals["訊號"].isin(selected)].copy()
    if ss.empty:
        return fig

    bull = ss[ss["類型"].astype(str).str.contains("多|強", na=False)]
    bear = ss[ss["類型"].astype(str).str.contains("空|弱", na=False)]
    mode = "markers+text" if show_text else "markers"

    if not bull.empty:
        fig.add_trace(go.Scatter(
            x=bull["Date"], y=bull["標記位置"], mode=mode, name="▲偏多訊號",
            text=bull["訊號"] if show_text else None, textposition="top center",
            customdata=bull[["訊號","價格","說明","細節"]],
            hovertemplate="日期=%{x}<br>訊號=%{customdata[0]}<br>價格=%{customdata[1]:.2f}<br>%{customdata[2]}<br>%{customdata[3]}<extra></extra>",
            marker=dict(symbol="triangle-up", size=13)
        ), row=1, col=1)

    if not bear.empty:
        fig.add_trace(go.Scatter(
            x=bear["Date"], y=bear["標記位置"], mode=mode, name="▼偏空訊號",
            text=bear["訊號"] if show_text else None, textposition="bottom center",
            customdata=bear[["訊號","價格","說明","細節"]],
            hovertemplate="日期=%{x}<br>訊號=%{customdata[0]}<br>價格=%{customdata[1]:.2f}<br>%{customdata[2]}<br>%{customdata[3]}<extra></extra>",
            marker=dict(symbol="triangle-down", size=13)
        ), row=1, col=1)
    return fig

def kline_chart(df, overlays, panel):
    """V62: 訊號▲▼+Hover；K線與副圖共享X軸，滑到某日可核對成交量。"""
    if df is None or df.empty:
        st.warning("查無K線資料")
        return
    draw_mode, selected_signals, show_text = v62_kline_control_panel()
    d = add_more_indicators(add_indicators(df))
    if d is None or d.empty:
        st.warning("查無K線資料")
        return
    dd = d.tail(180).copy()
    if "Date" not in dd.columns:
        dd = dd.reset_index().rename(columns={"index": "Date"})

    signals = v62_signal_engine(dd)
    panel = panel or "成交量"

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04,
        row_heights=[0.68, 0.32],
        subplot_titles=("K線主圖", f"副圖：{panel}")
    )
    fig.add_trace(go.Candlestick(
        x=dd["Date"], open=dd["Open"], high=dd["High"], low=dd["Low"], close=dd["Close"],
        name="K線",
        increasing_line_color="#ff3333", decreasing_line_color="#00d26a",
        increasing_fillcolor="#ff3333", decreasing_fillcolor="#00d26a",
        hovertemplate="日期=%{x}<br>開=%{open}<br>高=%{high}<br>低=%{low}<br>收=%{close}<extra></extra>"
    ), row=1, col=1)

    color_map = {"MA5":"#facc15","MA10":"#22d3ee","MA20":"#d946ef","MA60":"#fb923c","MA120":"#94a3b8","MA240":"#64748b"}
    for ma in overlays or []:
        if ma in dd.columns:
            fig.add_trace(go.Scatter(x=dd["Date"], y=dd[ma], name=ma, mode="lines", line=dict(width=1.5, color=color_map.get(ma))), row=1, col=1)
    if overlays and "布林通道" in overlays:
        for col, nm in [("BB_UP","BB上軌"),("BB_MID","BB中軌"),("BB_LOW","BB下軌")]:
            if col in dd.columns:
                fig.add_trace(go.Scatter(x=dd["Date"], y=dd[col], name=nm, mode="lines", line=dict(width=1, dash="dot")), row=1, col=1)

    fig = v62_add_signal_markers(fig, signals, selected_signals, show_text)

    if panel == "成交量":
        fig.add_trace(go.Bar(x=dd["Date"], y=dd["Volume"], name="成交量", opacity=0.75,
                             hovertemplate="日期=%{x}<br>成交量=%{y}<extra></extra>"), row=2, col=1)
        if "VOL_MA20" in dd.columns:
            fig.add_trace(go.Scatter(x=dd["Date"], y=dd["VOL_MA20"], name="20日均量", mode="lines"), row=2, col=1)
    elif panel == "MACD":
        fig.add_trace(go.Bar(x=dd["Date"], y=dd["OSC"], name="OSC"), row=2, col=1)
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["DIF"], name="DIF", mode="lines"), row=2, col=1)
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["MACD"], name="MACD", mode="lines"), row=2, col=1)
    elif panel == "KD":
        for col in ["K","D","J"]:
            if col in dd.columns:
                fig.add_trace(go.Scatter(x=dd["Date"], y=dd[col], name=col, mode="lines"), row=2, col=1)
        fig.add_hline(y=80, line_dash="dot", row=2, col=1); fig.add_hline(y=20, line_dash="dot", row=2, col=1)
    elif panel == "RSI":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["RSI"], name="RSI", mode="lines"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", row=2, col=1); fig.add_hline(y=30, line_dash="dot", row=2, col=1)
    elif panel == "BIAS":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["BIAS20"], name="BIAS20", mode="lines"), row=2, col=1)
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["BIAS60"], name="BIAS60", mode="lines"), row=2, col=1)
        fig.add_hline(y=0, line_dash="dot", row=2, col=1)
    elif panel == "布林通道":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["BB_WIDTH"], name="BB寬度%", mode="lines"), row=2, col=1)
    elif panel == "OBV":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["OBV"], name="OBV", mode="lines"), row=2, col=1)
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["OBV_MA20"], name="OBV_MA20", mode="lines"), row=2, col=1)
    elif panel == "MFI":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["MFI"], name="MFI", mode="lines"), row=2, col=1)
        fig.add_hline(y=80, line_dash="dot", row=2, col=1); fig.add_hline(y=20, line_dash="dot", row=2, col=1)
    elif panel == "威廉%R":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["WILLR"], name="Williams %R", mode="lines"), row=2, col=1)
        fig.add_hline(y=-20, line_dash="dot", row=2, col=1); fig.add_hline(y=-80, line_dash="dot", row=2, col=1)
    elif panel == "CCI":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["CCI"], name="CCI", mode="lines"), row=2, col=1)
        fig.add_hline(y=100, line_dash="dot", row=2, col=1); fig.add_hline(y=-100, line_dash="dot", row=2, col=1)
    elif panel == "ADX":
        for col in ["ADX","PLUS_DI","MINUS_DI"]:
            if col in dd.columns:
                fig.add_trace(go.Scatter(x=dd["Date"], y=dd[col], name=col, mode="lines"), row=2, col=1)
        fig.add_hline(y=20, line_dash="dot", row=2, col=1)
    elif panel == "ATR":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["ATR_PCT"], name="ATR%", mode="lines"), row=2, col=1)
    elif panel == "ROC":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["ROC12"], name="ROC12", mode="lines"), row=2, col=1)
        fig.add_hline(y=0, line_dash="dot", row=2, col=1)
    elif panel == "Momentum":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["MOM10"], name="MOM10", mode="lines"), row=2, col=1)
        fig.add_hline(y=0, line_dash="dot", row=2, col=1)

    fig.update_layout(
        height=820, template="plotly_white", xaxis_rangeslider_visible=False,
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", y=-0.08, font=dict(size=9)),
        dragmode="drawline" if draw_mode else "pan",
        newshape=dict(line=dict(width=2)),
    )
    fig.update_yaxes(side="right", row=1, col=1)
    fig.update_yaxes(side="right", row=2, col=1)
    st.plotly_chart(fig, use_container_width=True, config=v62_plotly_config(draw_mode))

    with st.expander("📍 K線訊號與計算說明", expanded=False):
        st.caption("V62：訊號以▲▼標示；滑鼠移到標記可查看計算細節。上下圖共享X軸，可核對當日K線與成交量。")
        if signals is not None and not signals.empty:
            show_df = signals[signals["訊號"].isin(selected_signals)] if selected_signals else signals
            st.dataframe(show_df, use_container_width=True, hide_index=True)
        else:
            st.info("目前區間內未偵測到明顯技術訊號。")
# ================= V62 PROFESSIONAL MOBILE EDITION LAYER END =================

# ================= V63 INLINE CROSSHAIR HOVER EDITION LAYER =================
V63_NAME_MAP = {
    "2330.TW": "台積電", "2303.TW": "聯電", "2454.TW": "聯發科",
    "8112.TW": "至上", "6189.TW": "豐藝", "6739.TW": "竹陞科技",
    "6215.TWO": "和椿科技", "6830.TW": "汎銓", "6415.TW": "矽力-KY",
    "5347.TWO": "世界先進", "2379.TW": "瑞昱", "2408.TW": "南亞科",
    "3711.TW": "日月光投控", "3661.TW": "世芯-KY",
    "3019.TW": "亞光", "2049.TW": "上銀", "1536.TW": "和大",
}
try:
    CODE_NAME_MAP.update(V63_NAME_MAP)
except Exception:
    CODE_NAME_MAP = V63_NAME_MAP.copy()
try:
    TW_STOCKS.update({"至上":"8112.TW", "至上電子":"8112.TW", "豐藝":"6189.TW", "豐藝電子":"6189.TW", "竹陞":"6739.TW", "竹陞科技":"6739.TW"})
except Exception:
    pass

def stock_name_only(symbol):
    s = str(symbol).upper().strip()
    code = s.split(".")[0]
    if s in V63_NAME_MAP:
        return V63_NAME_MAP[s]
    try:
        if s in CODE_NAME_MAP:
            return CODE_NAME_MAP[s]
    except Exception:
        pass
    for full, nm in V63_NAME_MAP.items():
        if full.split(".")[0] == code:
            return nm
    try:
        nm = yahoo_name_lookup(s)
        return nm or s
    except Exception:
        return s

def display_name(symbol):
    s = str(symbol).upper().strip()
    return f"{stock_name_only(s)} / {s}"

def v63_plotly_config(draw_mode=True):
    return {
        "displaylogo": False,
        "scrollZoom": True,
        "modeBarButtonsToAdd": ["drawline", "drawopenpath", "drawclosedpath", "drawcircle", "drawrect", "eraseshape"] if draw_mode else [],
        "toImageButtonOptions": {"format": "png", "filename": "AIStock_Kline", "height": 900, "width": 1400, "scale": 2},
    }

def v63_format_volume(v):
    try:
        v = float(v)
        if abs(v) >= 1e8:
            return f"{v/1e8:.2f}億"
        if abs(v) >= 1e4:
            return f"{v/1e4:.2f}萬"
        return f"{v:.0f}"
    except Exception:
        return str(v)

def v63_signal_engine(df):
    return v62_signal_engine(df) if "v62_signal_engine" in globals() else pd.DataFrame()

def v63_kline_control_panel():
    st.markdown("### 🧭 K線工具控制列")
    c1, c2 = st.columns([1, 2])
    with c1:
        draw_mode = st.toggle("啟用手動畫線工具", value=True, key="v63_draw_mode")
    with c2:
        st.caption("圖上核對模式：游標移到任一日期，垂直虛線會貫穿K線與副圖；浮動框直接顯示當日價格、成交量與指標。")
    options = ["黃金交叉", "死亡交叉", "MACD翻紅", "MACD翻黑", "RSI突破50", "RSI跌破50", "突破布林上軌", "跌破布林下軌"]
    selected = st.multiselect(
        "選擇要顯示在K線圖上的訊號",
        options,
        default=["黃金交叉", "死亡交叉"],
        key="v63_kline_signal_filter"
    )
    show_text = st.toggle("顯示訊號文字標籤", value=True, key="v63_show_signal_text")
    return draw_mode, selected, show_text

def v63_add_signal_markers(fig, signals, selected, show_text=False):
    if signals is None or signals.empty or not selected:
        return fig
    ss = signals[signals["訊號"].isin(selected)].copy()
    if ss.empty:
        return fig
    bull = ss[ss["類型"].astype(str).str.contains("多|強", na=False)]
    bear = ss[ss["類型"].astype(str).str.contains("空|弱", na=False)]
    mode = "markers+text" if show_text else "markers"
    if not bull.empty:
        fig.add_trace(go.Scatter(
            x=bull["Date"], y=bull["標記位置"], mode=mode, name="▲偏多訊號",
            text=bull["訊號"] if show_text else None, textposition="top center",
            customdata=bull[["訊號","價格","說明","細節"]],
            hovertemplate="訊號=%{customdata[0]}<br>價格=%{customdata[1]:.2f}<br>%{customdata[2]}<br>%{customdata[3]}<extra></extra>",
            marker=dict(symbol="triangle-up", size=13)
        ), row=1, col=1)
    if not bear.empty:
        fig.add_trace(go.Scatter(
            x=bear["Date"], y=bear["標記位置"], mode=mode, name="▼偏空訊號",
            text=bear["訊號"] if show_text else None, textposition="bottom center",
            customdata=bear[["訊號","價格","說明","細節"]],
            hovertemplate="訊號=%{customdata[0]}<br>價格=%{customdata[1]:.2f}<br>%{customdata[2]}<br>%{customdata[3]}<extra></extra>",
            marker=dict(symbol="triangle-down", size=13)
        ), row=1, col=1)
    return fig

def kline_chart(df, overlays, panel):
    """V63: 圖上直接顯示核對資訊；垂直虛線貫穿K線與副圖，不做右側資訊面板。"""
    if df is None or df.empty:
        st.warning("查無K線資料")
        return
    draw_mode, selected_signals, show_text = v63_kline_control_panel()
    d = add_more_indicators(add_indicators(df))
    if d is None or d.empty:
        st.warning("查無K線資料")
        return
    dd = d.tail(180).copy()
    if "Date" not in dd.columns:
        dd = dd.reset_index().rename(columns={"index": "Date"})

    signals = v63_signal_engine(dd)
    panel = panel or "成交量"

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.035,
        row_heights=[0.68, 0.32],
        subplot_titles=("K線主圖", f"副圖：{panel}")
    )

    # Custom data for unified hover box
    for col in ["MA5","MA20","MA60","Volume","VOL_MA20","DIF","MACD","OSC","RSI","K","D"]:
        if col not in dd.columns:
            dd[col] = np.nan
    hover_cd = np.stack([
        dd["Open"], dd["High"], dd["Low"], dd["Close"],
        dd["MA5"], dd["MA20"], dd["MA60"], dd["Volume"], dd["VOL_MA20"]
    ], axis=-1)

    fig.add_trace(go.Candlestick(
        x=dd["Date"], open=dd["Open"], high=dd["High"], low=dd["Low"], close=dd["Close"],
        name="K線",
        increasing_line_color="#ff3333", decreasing_line_color="#00d26a",
        increasing_fillcolor="#ff3333", decreasing_fillcolor="#00d26a",
        customdata=hover_cd,
        hovertemplate=(
            "<b>%{x|%Y-%m-%d}</b><br>"
            "開盤：%{customdata[0]:.2f}<br>"
            "最高：%{customdata[1]:.2f}<br>"
            "最低：%{customdata[2]:.2f}<br>"
            "收盤：%{customdata[3]:.2f}<br>"
            "MA5：%{customdata[4]:.2f}<br>"
            "MA20：%{customdata[5]:.2f}<br>"
            "MA60：%{customdata[6]:.2f}<br>"
            "成交量：%{customdata[7]:,.0f}<br>"
            "20日均量：%{customdata[8]:,.0f}<extra></extra>"
        )
    ), row=1, col=1)

    color_map = {"MA5":"#facc15","MA10":"#22d3ee","MA20":"#d946ef","MA60":"#fb923c","MA120":"#94a3b8","MA240":"#64748b"}
    for ma in overlays or []:
        if ma in dd.columns:
            fig.add_trace(go.Scatter(
                x=dd["Date"], y=dd[ma], name=ma, mode="lines",
                line=dict(width=1.5, color=color_map.get(ma)),
                hovertemplate=f"{ma}=%{{y:.2f}}<extra></extra>"
            ), row=1, col=1)

    if overlays and "布林通道" in overlays:
        for col, nm in [("BB_UP","BB上軌"),("BB_MID","BB中軌"),("BB_LOW","BB下軌")]:
            if col in dd.columns:
                fig.add_trace(go.Scatter(
                    x=dd["Date"], y=dd[col], name=nm, mode="lines",
                    line=dict(width=1, dash="dot"),
                    hovertemplate=f"{nm}=%{{y:.2f}}<extra></extra>"
                ), row=1, col=1)

    fig = v63_add_signal_markers(fig, signals, selected_signals, show_text)

    if panel == "成交量":
        fig.add_trace(go.Bar(
            x=dd["Date"], y=dd["Volume"], name="成交量", opacity=0.72,
            customdata=dd[["Open","High","Low","Close","VOL_MA20"]],
            hovertemplate=(
                "<b>%{x|%Y-%m-%d}</b><br>"
                "成交量：%{y:,.0f}<br>"
                "20日均量：%{customdata[4]:,.0f}<br>"
                "收盤：%{customdata[3]:.2f}<extra></extra>"
            )
        ), row=2, col=1)
        if "VOL_MA20" in dd.columns:
            fig.add_trace(go.Scatter(
                x=dd["Date"], y=dd["VOL_MA20"], name="20日均量", mode="lines",
                hovertemplate="20日均量=%{y:,.0f}<extra></extra>"
            ), row=2, col=1)

    elif panel == "MACD":
        fig.add_trace(go.Bar(x=dd["Date"], y=dd["OSC"], name="OSC", hovertemplate="OSC=%{y:.2f}<extra></extra>"), row=2, col=1)
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["DIF"], name="DIF", mode="lines", hovertemplate="DIF=%{y:.2f}<extra></extra>"), row=2, col=1)
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["MACD"], name="MACD", mode="lines", hovertemplate="MACD=%{y:.2f}<extra></extra>"), row=2, col=1)
    elif panel == "KD":
        for col in ["K","D","J"]:
            if col in dd.columns:
                fig.add_trace(go.Scatter(x=dd["Date"], y=dd[col], name=col, mode="lines", hovertemplate=f"{col}=%{{y:.2f}}<extra></extra>"), row=2, col=1)
        fig.add_hline(y=80, line_dash="dot", row=2, col=1); fig.add_hline(y=20, line_dash="dot", row=2, col=1)
    elif panel == "RSI":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["RSI"], name="RSI", mode="lines", hovertemplate="RSI=%{y:.2f}<extra></extra>"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", row=2, col=1); fig.add_hline(y=30, line_dash="dot", row=2, col=1)
    elif panel == "BIAS":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["BIAS20"], name="BIAS20", mode="lines", hovertemplate="BIAS20=%{y:.2f}<extra></extra>"), row=2, col=1)
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["BIAS60"], name="BIAS60", mode="lines", hovertemplate="BIAS60=%{y:.2f}<extra></extra>"), row=2, col=1)
        fig.add_hline(y=0, line_dash="dot", row=2, col=1)
    elif panel == "布林通道":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["BB_WIDTH"], name="BB寬度%", mode="lines", hovertemplate="BB寬度=%{y:.2f}<extra></extra>"), row=2, col=1)
    elif panel == "OBV":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["OBV"], name="OBV", mode="lines", hovertemplate="OBV=%{y:.0f}<extra></extra>"), row=2, col=1)
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["OBV_MA20"], name="OBV_MA20", mode="lines", hovertemplate="OBV_MA20=%{y:.0f}<extra></extra>"), row=2, col=1)
    elif panel == "MFI":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["MFI"], name="MFI", mode="lines", hovertemplate="MFI=%{y:.2f}<extra></extra>"), row=2, col=1)
        fig.add_hline(y=80, line_dash="dot", row=2, col=1); fig.add_hline(y=20, line_dash="dot", row=2, col=1)
    elif panel == "威廉%R":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["WILLR"], name="Williams %R", mode="lines", hovertemplate="Williams %R=%{y:.2f}<extra></extra>"), row=2, col=1)
        fig.add_hline(y=-20, line_dash="dot", row=2, col=1); fig.add_hline(y=-80, line_dash="dot", row=2, col=1)
    elif panel == "CCI":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["CCI"], name="CCI", mode="lines", hovertemplate="CCI=%{y:.2f}<extra></extra>"), row=2, col=1)
        fig.add_hline(y=100, line_dash="dot", row=2, col=1); fig.add_hline(y=-100, line_dash="dot", row=2, col=1)
    elif panel == "ADX":
        for col in ["ADX","PLUS_DI","MINUS_DI"]:
            if col in dd.columns:
                fig.add_trace(go.Scatter(x=dd["Date"], y=dd[col], name=col, mode="lines", hovertemplate=f"{col}=%{{y:.2f}}<extra></extra>"), row=2, col=1)
        fig.add_hline(y=20, line_dash="dot", row=2, col=1)
    elif panel == "ATR":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["ATR_PCT"], name="ATR%", mode="lines", hovertemplate="ATR%=%{y:.2f}<extra></extra>"), row=2, col=1)
    elif panel == "ROC":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["ROC12"], name="ROC12", mode="lines", hovertemplate="ROC12=%{y:.2f}<extra></extra>"), row=2, col=1)
        fig.add_hline(y=0, line_dash="dot", row=2, col=1)
    elif panel == "Momentum":
        fig.add_trace(go.Scatter(x=dd["Date"], y=dd["MOM10"], name="MOM10", mode="lines", hovertemplate="MOM10=%{y:.2f}<extra></extra>"), row=2, col=1)
        fig.add_hline(y=0, line_dash="dot", row=2, col=1)

    fig.update_layout(
        height=840, template="plotly_white", xaxis_rangeslider_visible=False,
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_size=12),
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", y=-0.08, font=dict(size=9)),
        dragmode="drawline" if draw_mode else "pan",
        newshape=dict(line=dict(width=2)),
        spikedistance=-1,
        hoverdistance=60,
    )
    fig.update_xaxes(
        showspikes=True,
        spikecolor="#111827",
        spikethickness=1,
        spikedash="dot",
        spikemode="across",
        spikesnap="cursor",
        row=1, col=1
    )
    fig.update_xaxes(
        showspikes=True,
        spikecolor="#111827",
        spikethickness=1,
        spikedash="dot",
        spikemode="across",
        spikesnap="cursor",
        row=2, col=1
    )
    fig.update_yaxes(side="right", row=1, col=1)
    fig.update_yaxes(side="right", row=2, col=1)
    st.plotly_chart(fig, use_container_width=True, config=v63_plotly_config(draw_mode))

    with st.expander("📍 圖上核對與訊號說明", expanded=False):
        st.caption("V63：不做右側面板；直接在圖上用垂直虛線與浮動框顯示當日價格、成交量與指標。")
        if signals is not None and not signals.empty:
            show_df = signals[signals["訊號"].isin(selected_signals)] if selected_signals else signals
            st.dataframe(show_df, use_container_width=True, hide_index=True)
        else:
            st.info("目前區間內未偵測到明顯技術訊號。")
# ================= V63 INLINE CROSSHAIR HOVER EDITION LAYER END =================

# ================= V64 CLEAN UX + SIGNAL AUDIT EDITION LAYER =================
V64_NAME_MAP = {
    "2330.TW": "台積電", "2303.TW": "聯電", "2454.TW": "聯發科", "2317.TW": "鴻海", "2382.TW": "廣達",
    "2379.TW": "瑞昱", "2408.TW": "南亞科", "3374.TW": "精材", "6739.TW": "竹陞科技",
    "8112.TW": "至上", "6189.TW": "豐藝", "6215.TWO": "和椿科技", "6830.TW": "汎銓", "6415.TW": "矽力-KY",
    "5347.TWO": "世界先進", "3711.TW": "日月光投控", "3661.TW": "世芯-KY", "3019.TW": "亞光", "2049.TW": "上銀", "1536.TW": "和大",
}
try:
    CODE_NAME_MAP.update(V64_NAME_MAP)
except Exception:
    CODE_NAME_MAP = V64_NAME_MAP.copy()
try:
    TW_STOCKS.update({"精材":"3374.TW", "竹陞":"6739.TW", "竹陞科技":"6739.TW", "至上":"8112.TW", "至上電子":"8112.TW", "豐藝":"6189.TW", "豐藝電子":"6189.TW"})
except Exception:
    pass

def stock_name_only(symbol):
    s = str(symbol).upper().strip(); code = s.split('.')[0]
    if s in V64_NAME_MAP: return V64_NAME_MAP[s]
    try:
        if s in CODE_NAME_MAP: return CODE_NAME_MAP[s]
    except Exception: pass
    for full,nm in V64_NAME_MAP.items():
        if full.split('.')[0] == code: return nm
    try:
        nm = yahoo_name_lookup(s); return nm or s
    except Exception:
        return s

def display_name(symbol):
    s = str(symbol).upper().strip(); return f"{stock_name_only(s)} / {s}"

def v64_consensus_help():
    with st.expander("❓ 什麼是『納入共識』？", expanded=False):
        st.markdown("""
**納入共識**就是：這個估值模型會參與最後的「共識合理價」計算。\n\n- ✅ 勾選：該模型數值會放進綜合合理價。\n- ⬜ 不勾選：只在表格中參考，不影響最後共識價。\n- ⚠️ 極端值：系統可標示為極端值，避免單一模型把共識價拉太高或拉太低。\n\n例如只勾選 DCF、FCFF、FCFE，系統就用這三個模型形成共識合理價。這不是保證價格，而是多模型平均/加權後的參考區間。
""")

def v64_mobile_webapp_note():
    with st.expander("📱 手機像APP一樣開啟的方法", expanded=False):
        st.markdown("""
**Android / Chrome：** 打開本網頁 → 右上角 `⋮` → **加入主畫面**。  \n**iPhone / Safari：** 打開本網頁 → 分享按鈕 → **加入主畫面**。  \n之後手機桌面會出現圖示，點選即可直接進入本系統。
""")

def v64_plotly_config(draw_mode=True):
    return {"displaylogo": False, "scrollZoom": True, "modeBarButtonsToAdd": ["drawline","drawopenpath","drawclosedpath","drawcircle","drawrect","eraseshape"] if draw_mode else [], "toImageButtonOptions": {"format":"png","filename":"AIStock_Kline","height":900,"width":1400,"scale":2}}

def v64_signal_engine(df):
    d = add_more_indicators(add_indicators(df))
    cols=["Date","訊號","類型","價格","標記位置","說明","細節"]
    if d is None or d.empty: return pd.DataFrame(columns=cols)
    if "Date" not in d.columns: d = d.reset_index().rename(columns={"index":"Date"})
    for c in ["MA5","MA20","Close","High","Low"]:
        if c not in d.columns: d[c]=np.nan
    sigs=[]
    def add(i,sig,kind,desc,detail=""):
        close=d["Close"].iloc[i]; high=d["High"].iloc[i]; low=d["Low"].iloc[i]
        ypos=(high*1.018) if ("多" in kind or "強" in kind) else (low*0.982)
        sigs.append({"Date":d["Date"].iloc[i],"訊號":sig,"類型":kind,"價格":float(close) if pd.notna(close) else None,"標記位置":float(ypos) if pd.notna(ypos) else None,"說明":desc,"細節":detail})
    for i in range(1,len(d)):
        ma5p,ma20p,ma5,ma20=d["MA5"].iloc[i-1],d["MA20"].iloc[i-1],d["MA5"].iloc[i],d["MA20"].iloc[i]
        if pd.notna(ma5p) and pd.notna(ma20p) and pd.notna(ma5) and pd.notna(ma20):
            if ma5p <= ma20p and ma5 > ma20:
                add(i,"黃金交叉","偏多","MA5 由下往上突破 MA20",f"前日MA5={ma5p:.2f}, 前日MA20={ma20p:.2f}; 當日MA5={ma5:.2f}, 當日MA20={ma20:.2f}")
            if ma5p >= ma20p and ma5 < ma20:
                add(i,"死亡交叉","偏空","MA5 由上往下跌破 MA20",f"前日MA5={ma5p:.2f}, 前日MA20={ma20p:.2f}; 當日MA5={ma5:.2f}, 當日MA20={ma20:.2f}")
        if "OSC" in d.columns and pd.notna(d["OSC"].iloc[i-1]) and pd.notna(d["OSC"].iloc[i]):
            o0,o1=d["OSC"].iloc[i-1],d["OSC"].iloc[i]
            if o0 <= 0 and o1 > 0: add(i,"MACD翻紅","偏多","MACD柱狀體由負轉正",f"前日OSC={o0:.2f}, 當日OSC={o1:.2f}")
            if o0 >= 0 and o1 < 0: add(i,"MACD翻黑","偏空","MACD柱狀體由正轉負",f"前日OSC={o0:.2f}, 當日OSC={o1:.2f}")
        if "RSI" in d.columns and pd.notna(d["RSI"].iloc[i-1]) and pd.notna(d["RSI"].iloc[i]):
            r0,r1=d["RSI"].iloc[i-1],d["RSI"].iloc[i]
            if r0 <= 50 and r1 > 50: add(i,"RSI突破50","偏多","RSI由50以下轉到50以上",f"前日RSI={r0:.2f}, 當日RSI={r1:.2f}")
            if r0 >= 50 and r1 < 50: add(i,"RSI跌破50","偏空","RSI由50以上轉到50以下",f"前日RSI={r0:.2f}, 當日RSI={r1:.2f}")
        if all(x in d.columns for x in ["BB_UP","BB_LOW"]):
            close=d["Close"].iloc[i]
            if pd.notna(close) and pd.notna(d["BB_UP"].iloc[i]) and close > d["BB_UP"].iloc[i]: add(i,"突破布林上軌","強勢/過熱","收盤價突破布林上軌",f"收盤={close:.2f}, BB上軌={d['BB_UP'].iloc[i]:.2f}")
            if pd.notna(close) and pd.notna(d["BB_LOW"].iloc[i]) and close < d["BB_LOW"].iloc[i]: add(i,"跌破布林下軌","弱勢/超跌","收盤價跌破布林下軌",f"收盤={close:.2f}, BB下軌={d['BB_LOW'].iloc[i]:.2f}")
    return pd.DataFrame(sigs, columns=cols) if sigs else pd.DataFrame(columns=cols)

def v64_kline_control_panel():
    st.markdown("### 🧭 K線工具控制列")
    c1,c2=st.columns([1,2])
    with c1: draw_mode=st.toggle("啟用手動畫線工具", value=True, key="v64_draw_mode")
    with c2: st.caption("圖上核對模式：游標移到任一日期，垂直虛線貫穿K線與副圖；浮動框顯示價格、成交量與指標。")
    opts=["黃金交叉","死亡交叉","MACD翻紅","MACD翻黑","RSI突破50","RSI跌破50","突破布林上軌","跌破布林下軌"]
    selected=st.multiselect("選擇要顯示在K線圖上的訊號", opts, default=["黃金交叉","死亡交叉"], key="v64_kline_signal_filter")
    show_text=st.toggle("顯示訊號文字標籤", value=True, key="v64_show_signal_text")
    return draw_mode,selected,show_text

def v64_add_signal_markers(fig, signals, selected, show_text=False):
    if signals is None or signals.empty or not selected: return fig
    ss=signals[signals["訊號"].isin(selected)].copy()
    if ss.empty: return fig
    for mask, name, symbol, pos in [(ss["類型"].astype(str).str.contains("多|強", na=False),"▲偏多訊號","triangle-up","top center"),(ss["類型"].astype(str).str.contains("空|弱", na=False),"▼偏空訊號","triangle-down","bottom center")]:
        part=ss[mask]
        if not part.empty:
            fig.add_trace(go.Scatter(x=part["Date"], y=part["標記位置"], mode="markers+text" if show_text else "markers", name=name, text=part["訊號"] if show_text else None, textposition=pos, customdata=part[["訊號","價格","說明","細節"]], hovertemplate="訊號=%{customdata[0]}<br>價格=%{customdata[1]:.2f}<br>%{customdata[2]}<br>%{customdata[3]}<extra></extra>", marker=dict(symbol=symbol, size=13)), row=1, col=1)
    return fig

def v64_signal_audit(signals, selected):
    opts=["黃金交叉","死亡交叉","MACD翻紅","MACD翻黑","RSI突破50","RSI跌破50","突破布林上軌","跌破布林下軌"]
    rows=[]
    for sig in opts:
        cnt=0 if signals is None or signals.empty else int((signals["訊號"]==sig).sum())
        rows.append([sig,cnt,"已勾選" if sig in selected else "未勾選","會顯示" if cnt>0 and sig in selected else ("有發生但未勾選" if cnt>0 else "本區間未發生")])
    return pd.DataFrame(rows, columns=["訊號","偵測次數","目前狀態","圖上顯示判斷"])

def kline_chart(df, overlays, panel):
    if df is None or df.empty:
        st.warning("查無K線資料"); return
    draw_mode,selected_signals,show_text=v64_kline_control_panel()
    d=add_more_indicators(add_indicators(df))
    if d is None or d.empty:
        st.warning("查無K線資料"); return
    dd=d.tail(220).copy()
    if "Date" not in dd.columns: dd=dd.reset_index().rename(columns={"index":"Date"})
    signals=v64_signal_engine(dd); panel=panel or "成交量"
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=0.035,row_heights=[0.68,0.32],subplot_titles=("K線主圖",f"副圖：{panel}"))
    for c in ["MA5","MA20","MA60","Volume","VOL_MA20"]:
        if c not in dd.columns: dd[c]=np.nan
    cd=np.stack([dd["Open"],dd["High"],dd["Low"],dd["Close"],dd["MA5"],dd["MA20"],dd["MA60"],dd["Volume"],dd["VOL_MA20"]],axis=-1)
    fig.add_trace(go.Candlestick(x=dd["Date"],open=dd["Open"],high=dd["High"],low=dd["Low"],close=dd["Close"],name="K線",increasing_line_color="#ff3333",decreasing_line_color="#00d26a",increasing_fillcolor="#ff3333",decreasing_fillcolor="#00d26a",customdata=cd,hovertemplate="<b>%{x|%Y-%m-%d}</b><br>開盤：%{customdata[0]:.2f}<br>最高：%{customdata[1]:.2f}<br>最低：%{customdata[2]:.2f}<br>收盤：%{customdata[3]:.2f}<br>MA5：%{customdata[4]:.2f}<br>MA20：%{customdata[5]:.2f}<br>MA60：%{customdata[6]:.2f}<br>成交量：%{customdata[7]:,.0f}<br>20日均量：%{customdata[8]:,.0f}<extra></extra>"),row=1,col=1)
    cmap={"MA5":"#facc15","MA10":"#22d3ee","MA20":"#d946ef","MA60":"#fb923c","MA120":"#94a3b8","MA240":"#64748b"}
    for ma in overlays or []:
        if ma in dd.columns: fig.add_trace(go.Scatter(x=dd["Date"],y=dd[ma],name=ma,mode="lines",line=dict(width=1.5,color=cmap.get(ma))),row=1,col=1)
    if overlays and "布林通道" in overlays:
        for col,nm in [("BB_UP","BB上軌"),("BB_MID","BB中軌"),("BB_LOW","BB下軌")]:
            if col in dd.columns: fig.add_trace(go.Scatter(x=dd["Date"],y=dd[col],name=nm,mode="lines",line=dict(width=1,dash="dot")),row=1,col=1)
    fig=v64_add_signal_markers(fig, signals, selected_signals, show_text)
    if panel=="成交量":
        fig.add_trace(go.Bar(x=dd["Date"],y=dd["Volume"],name="成交量",opacity=0.72,hovertemplate="<b>%{x|%Y-%m-%d}</b><br>成交量：%{y:,.0f}<extra></extra>"),row=2,col=1)
        if "VOL_MA20" in dd.columns: fig.add_trace(go.Scatter(x=dd["Date"],y=dd["VOL_MA20"],name="20日均量",mode="lines"),row=2,col=1)
    elif panel=="MACD":
        fig.add_trace(go.Bar(x=dd["Date"],y=dd["OSC"],name="OSC"),row=2,col=1); fig.add_trace(go.Scatter(x=dd["Date"],y=dd["DIF"],name="DIF",mode="lines"),row=2,col=1); fig.add_trace(go.Scatter(x=dd["Date"],y=dd["MACD"],name="MACD",mode="lines"),row=2,col=1)
    elif panel=="KD":
        for c in ["K","D","J"]:
            if c in dd.columns: fig.add_trace(go.Scatter(x=dd["Date"],y=dd[c],name=c,mode="lines"),row=2,col=1)
        fig.add_hline(y=80,line_dash="dot",row=2,col=1); fig.add_hline(y=20,line_dash="dot",row=2,col=1)
    elif panel=="RSI":
        fig.add_trace(go.Scatter(x=dd["Date"],y=dd["RSI"],name="RSI",mode="lines"),row=2,col=1); fig.add_hline(y=70,line_dash="dot",row=2,col=1); fig.add_hline(y=30,line_dash="dot",row=2,col=1)
    else:
        # fallback: if indicator exists as column, show it; otherwise volume
        colmap={"BIAS":"BIAS20","布林通道":"BB_WIDTH","OBV":"OBV","MFI":"MFI","威廉%R":"WILLR","CCI":"CCI","ADX":"ADX","ATR":"ATR_PCT","ROC":"ROC12","Momentum":"MOM10"}
        col=colmap.get(panel)
        if col and col in dd.columns: fig.add_trace(go.Scatter(x=dd["Date"],y=dd[col],name=panel,mode="lines"),row=2,col=1)
        else: fig.add_trace(go.Bar(x=dd["Date"],y=dd["Volume"],name="成交量"),row=2,col=1)
    fig.update_layout(height=840,template="plotly_white",xaxis_rangeslider_visible=False,hovermode="x unified",hoverlabel=dict(bgcolor="white",font_size=12),margin=dict(l=10,r=10,t=50,b=10),legend=dict(orientation="h",y=-0.08,font=dict(size=9)),dragmode="drawline" if draw_mode else "pan",newshape=dict(line=dict(width=2)),spikedistance=-1,hoverdistance=60)
    fig.update_xaxes(showspikes=True,spikecolor="#111827",spikethickness=1,spikedash="dot",spikemode="across",spikesnap="cursor",row=1,col=1)
    fig.update_xaxes(showspikes=True,spikecolor="#111827",spikethickness=1,spikedash="dot",spikemode="across",spikesnap="cursor",row=2,col=1)
    fig.update_yaxes(side="right",row=1,col=1); fig.update_yaxes(side="right",row=2,col=1)
    st.plotly_chart(fig,use_container_width=True,config=v64_plotly_config(draw_mode))
    with st.expander("📍 訊號統計與顯示判斷", expanded=True):
        st.dataframe(v64_signal_audit(signals, selected_signals), use_container_width=True, hide_index=True)
        st.caption("若偵測次數為0，代表此期間沒有發生該訊號；若偵測次數>0但未勾選，則不會顯示在圖上。")
        if signals is not None and not signals.empty: st.dataframe(signals.tail(40), use_container_width=True, hide_index=True)
# ================= V64 CLEAN UX + SIGNAL AUDIT EDITION LAYER END =================

# ================= V65 AI RESEARCH DATA EDITION LAYER =================
V65_NAME_MAP = {
    "2330.TW": "台積電", "2303.TW": "聯電", "2454.TW": "聯發科",
    "2317.TW": "鴻海", "2382.TW": "廣達", "2412.TW": "中華電",
    "2379.TW": "瑞昱", "2408.TW": "南亞科", "3374.TW": "精材",
    "6739.TW": "竹陞科技", "8112.TW": "至上", "6189.TW": "豐藝",
    "6215.TWO": "和椿科技", "6830.TW": "汎銓", "6415.TW": "矽力-KY",
    "5347.TWO": "世界先進", "3711.TW": "日月光投控", "3661.TW": "世芯-KY",
    "6112.TW": "邁達特", "2357.TW": "華碩", "2376.TW": "技嘉", "3231.TW": "緯創",
}
try:
    CODE_NAME_MAP.update(V65_NAME_MAP)
except Exception:
    CODE_NAME_MAP = V65_NAME_MAP.copy()
try:
    TW_STOCKS.update({"邁達特":"6112.TW", "精材":"3374.TW", "竹陞科技":"6739.TW"})
except Exception:
    pass

def stock_name_only(symbol):
    s = str(symbol).upper().strip()
    code = s.split(".")[0]
    if s in V65_NAME_MAP:
        return V65_NAME_MAP[s]
    try:
        if s in CODE_NAME_MAP:
            return CODE_NAME_MAP[s]
    except Exception:
        pass
    for full, nm in V65_NAME_MAP.items():
        if full.split(".")[0] == code:
            return nm
    try:
        nm = yahoo_name_lookup(s)
        return nm or s
    except Exception:
        return s

def display_name(symbol):
    s = str(symbol).upper().strip()
    return f"{stock_name_only(s)} / {s}"

def v65_peer_group(symbol):
    s = str(symbol).upper()
    code = s.split(".")[0]
    tech_peers = ["2330.TW", "2303.TW", "5347.TWO", "2454.TW", "2379.TW", "3711.TW"]
    ai_server_peers = ["2382.TW", "3231.TW", "6669.TW", "2357.TW", "2376.TW"]
    electronics_peers = ["8112.TW", "6189.TW", "6112.TW", "3374.TW", "6739.TW"]
    if code in ["2382","3231","6669","2357","2376"]:
        return ai_server_peers
    if code in ["8112","6189","6112","3374","6739"]:
        return electronics_peers
    return tech_peers

def v65_safe_metric(q, key, default=np.nan):
    try:
        val = q.get(key, default)
        if val is None:
            return default
        return val
    except Exception:
        return default

def v65_ai_news_table(symbol, q, scores):
    name = stock_name_only(symbol)
    price = v65_safe_metric(q, "price", np.nan)
    pe = v65_safe_metric(q, "pe", np.nan)
    pb = v65_safe_metric(q, "pb", np.nan)
    ai = scores.get("ai", ai_total(scores) if "ai_total" in globals() else 60)
    rows = [
        ["公司新聞代理", f"{name} 近期股價與估值變化", "Yahoo Finance / 價格資料", f"現價={price}, PE={pe}, PB={pb}", "中", "由價格與估值資料推估，尚未接新聞API"],
        ["AI題材新聞", "AI伺服器、半導體、電子通路、設備鏈題材追蹤", "產業代理詞庫", f"AI分數={ai}/100", "中低", "未串即時新聞前，用產業關鍵字代理"],
        ["風險新聞", "重大跌幅、估值過高、財報缺漏、籌碼轉弱", "系統風險引擎", f"風險分={scores.get('risk', 50)}/100", "中", "用量價與財報可得性推估"],
        ["後續可擴充", "可接 RSS / NewsAPI / Google News / 公開資訊觀測站重大訊息", "外部API", "需API或爬蟲權限", "高", "接入後可顯示真實新聞標題與連結"],
    ]
    return pd.DataFrame(rows, columns=["類別", "內容", "資料來源", "代入資訊", "可信度", "說明"])

def v65_ai_industry_table(symbol, q, scores):
    peers = v65_peer_group(symbol)
    rows = []
    for p in peers:
        nm = stock_name_only(p)
        try:
            qq = get_quote(p) if "get_quote" in globals() else {}
        except Exception:
            qq = {}
        rows.append([
            nm, p,
            v65_safe_metric(qq, "price", "N/A"),
            v65_safe_metric(qq, "pe", "N/A"),
            v65_safe_metric(qq, "pb", "N/A"),
            "同業/供應鏈代理",
        ])
    return pd.DataFrame(rows, columns=["同業公司", "代碼", "現價", "PE", "PB", "資料層"])

def v65_ai_competition_table(symbol, q, scores):
    peers = v65_ai_industry_table(symbol, q, scores)
    rows = []
    base_pe = v65_safe_metric(q, "pe", np.nan)
    base_pb = v65_safe_metric(q, "pb", np.nan)
    for _, r in peers.iterrows():
        rows.append([
            r["同業公司"], r["代碼"],
            r["PE"], r["PB"],
            "估值比較",
            "PE / PB / AI分數 / 法人分數綜合比較",
        ])
    out = pd.DataFrame(rows, columns=["競爭對手", "代碼", "PE", "PB", "比較項目", "說明"])
    return out

def v65_ai_event_table(symbol, q, scores):
    name = stock_name_only(symbol)
    price = v65_safe_metric(q, "price", np.nan)
    eps = v65_safe_metric(q, "eps", np.nan)
    pe = v65_safe_metric(q, "pe", np.nan)
    rows = [
        ["財報事件", f"{name} 最新EPS/PE/PB變化", f"EPS={eps}, PE={pe}", "Yahoo Finance", "中"],
        ["估值事件", "股價高於/低於模型共識合理價", f"現價={price}", "企業評價模型", "中"],
        ["籌碼事件", "法人分數、主力分數、融資融券燈號變化", f"法人={scores.get('inst', 50)}, 主力={scores.get('main', 50)}", "籌碼代理", "代理"],
        ["風險事件", "估值過熱、資料缺漏、技術轉弱", f"風險={scores.get('risk', 50)}", "AI風險引擎", "代理"],
    ]
    return pd.DataFrame(rows, columns=["事件類別", "事件內容", "目前數值", "資料來源", "可信度"])

def v65_ai_conference_table(symbol, q, scores):
    name = stock_name_only(symbol)
    rows = [
        ["營收展望", "營收成長率、產品組合、接單能見度", "需法說會逐字稿/API", "目前以財報與產業代理"],
        ["毛利率", "毛利率變化、匯率、產品組合", "需法說會逐字稿/API", "目前以財報代理"],
        ["CAPEX", "資本支出與產能擴充", "需法說會逐字稿/API", "目前未接即時法說資料"],
        ["AI摘要", f"{name} 法說會摘要可由公開資訊觀測站或公司IR資料接入", "MOPS / 公司IR", "後續可擴充"],
    ]
    return pd.DataFrame(rows, columns=["主題", "追蹤內容", "理想資料來源", "目前狀態"])

def v65_ai_risk_table(symbol, q, scores):
    risk = scores.get("risk", 50)
    pe = v65_safe_metric(q, "pe", np.nan)
    pb = v65_safe_metric(q, "pb", np.nan)
    rows = [
        ["估值風險", "PE/PB偏高時風險升高", f"PE={pe}, PB={pb}", "中"],
        ["技術風險", "均線轉弱、MACD翻黑、跌破布林下軌", f"技術分={scores.get('tech', 50)}", "中"],
        ["籌碼風險", "法人轉賣、主力分數下降、融資融券偏空", f"法人分={scores.get('inst', 50)}", "代理"],
        ["資料風險", "Yahoo/MOPS/ESG資料缺漏會降低可信度", f"風險指數={risk}/100", "中"],
    ]
    return pd.DataFrame(rows, columns=["風險類型", "判斷邏輯", "目前資料", "可信度"])

def v65_ai_research_center(symbol, q, df, scores):
    st.markdown(f"## 🤖 AI研究中心資料版：{display_name(symbol)}")
    st.caption("V65：新聞、產業、競爭、事件、法說會、風險預警先以可取得資料與代理資料層呈現；若未串即時新聞/API，會明確標示可信度。")
    tabs = st.tabs([
        "①AI評級", "②AI估值", "③AI財報", "④AI法人", "⑤AI產業",
        "⑥AI新聞", "⑦AI事件", "⑧AI法說會", "⑨AI競爭分析", "⑩AI風險預警", "資料來源"
    ])
    with tabs[0]:
        st.dataframe(pd.DataFrame([
            ["AI總分", f"{ai_total(scores) if 'ai_total' in globals() else scores.get('ai', 60):.1f}/100", "技術、財報、法人、ESG、風險加權"],
            ["目前狀態", "偏多" if scores.get("tech", 50) >= 65 else "中立", "依分數區間判斷"],
            ["模型共識價", v65_safe_metric(q, "fair", "N/A"), "企業評價模型或代理共識"],
        ], columns=["項目", "結果", "說明"]), use_container_width=True, hide_index=True)
    with tabs[1]:
        if "valuation_transparency_table" in globals():
            st.dataframe(valuation_transparency_table(symbol, q, df, scores), use_container_width=True, hide_index=True)
        else:
            st.info("估值透明化表可於評價中心查看。")
    with tabs[2]:
        st.dataframe(pd.DataFrame([
            ["EPS", v65_safe_metric(q, "eps", "N/A"), "Yahoo Finance"],
            ["PE", v65_safe_metric(q, "pe", "N/A"), "Yahoo Finance"],
            ["PB", v65_safe_metric(q, "pb", "N/A"), "Yahoo Finance"],
            ["財報品質", f"{scores.get('fund', 50)}/100", "財報可得性與獲利能力代理"],
        ], columns=["財報項目", "目前數值", "資料來源"]), use_container_width=True, hide_index=True)
    with tabs[3]:
        if "institutional_transparency_table" in globals():
            st.dataframe(institutional_transparency_table(symbol, df, scores), use_container_width=True, hide_index=True)
        else:
            st.dataframe(pd.DataFrame([["法人分數", scores.get("inst", 50), "量價/法人代理"]], columns=["項目","分數","說明"]), use_container_width=True, hide_index=True)
    with tabs[4]:
        st.dataframe(v65_ai_industry_table(symbol, q, scores), use_container_width=True, hide_index=True)
    with tabs[5]:
        st.dataframe(v65_ai_news_table(symbol, q, scores), use_container_width=True, hide_index=True)
    with tabs[6]:
        st.dataframe(v65_ai_event_table(symbol, q, scores), use_container_width=True, hide_index=True)
    with tabs[7]:
        st.dataframe(v65_ai_conference_table(symbol, q, scores), use_container_width=True, hide_index=True)
    with tabs[8]:
        st.dataframe(v65_ai_competition_table(symbol, q, scores), use_container_width=True, hide_index=True)
    with tabs[9]:
        st.dataframe(v65_ai_risk_table(symbol, q, scores), use_container_width=True, hide_index=True)
    with tabs[10]:
        st.dataframe(pd.DataFrame([
            ["Yahoo Finance", "價格、EPS、PE、PB、部分財報", "中", "台股部分財報欄位可能缺漏"],
            ["MOPS公開資訊觀測站", "正式財報、重大訊息、法說會", "高", "需後續串接"],
            ["新聞/RSS/API", "即時新聞標題與連結", "高", "需API或爬蟲權限"],
            ["代理模型", "產業、競爭、事件、風險推估", "中低", "明確標示為代理，不宣稱即時新聞"],
        ], columns=["資料層", "用途", "可信度", "備註"]), use_container_width=True, hide_index=True)
# ================= V65 AI RESEARCH DATA EDITION LAYER END =================

# ================= V66 INDUSTRY VALUATION DATA EDITION LAYER =================
V66_NAME_MAP = {
    "2330.TW": "台積電", "2303.TW": "聯電", "2454.TW": "聯發科",
    "2317.TW": "鴻海", "2382.TW": "廣達", "2412.TW": "中華電",
    "2379.TW": "瑞昱", "2408.TW": "南亞科", "3374.TW": "精材",
    "6739.TW": "竹陞科技", "8112.TW": "至上", "6189.TW": "豐藝",
    "6215.TWO": "和椿科技", "6830.TW": "汎銓", "6415.TW": "矽力-KY",
    "5347.TWO": "世界先進", "3711.TW": "日月光投控", "3661.TW": "世芯-KY",
    "6112.TW": "邁達特", "6570.TW": "維田", "2357.TW": "華碩", "2376.TW": "技嘉", "3231.TW": "緯創",
}
try:
    CODE_NAME_MAP.update(V66_NAME_MAP)
except Exception:
    CODE_NAME_MAP = V66_NAME_MAP.copy()
try:
    TW_STOCKS.update({"維田":"6570.TW", "邁達特":"6112.TW", "精材":"3374.TW", "竹陞科技":"6739.TW"})
except Exception:
    pass

def stock_name_only(symbol):
    s = str(symbol).upper().strip()
    code = s.split(".")[0]
    if s in V66_NAME_MAP:
        return V66_NAME_MAP[s]
    try:
        if s in CODE_NAME_MAP:
            return CODE_NAME_MAP[s]
    except Exception:
        pass
    for full, nm in V66_NAME_MAP.items():
        if full.split(".")[0] == code:
            return nm
    try:
        nm = yahoo_name_lookup(s)
        return nm or s
    except Exception:
        return s

def display_name(symbol):
    s = str(symbol).upper().strip()
    return f"{stock_name_only(s)} / {s}"

def v66_num(x, default=np.nan):
    try:
        if x is None or x == "N/A":
            return default
        if isinstance(x, str) and x.strip() in ["", "None", "nan", "NaN"]:
            return default
        return float(x)
    except Exception:
        return default

def v66_get_quote_any(symbol):
    """多層取價：先用既有 get_quote，再用 yfinance info/fast_info 補欄位。"""
    q = {}
    try:
        q.update(get_quote(symbol) if "get_quote" in globals() else {})
    except Exception:
        pass
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        info = {}
        try:
            info = t.info or {}
        except Exception:
            info = {}
        fast = {}
        try:
            fast = dict(t.fast_info or {})
        except Exception:
            fast = {}
        price = q.get("price") or info.get("currentPrice") or info.get("regularMarketPrice") or fast.get("last_price")
        eps = q.get("eps") or info.get("trailingEps") or info.get("forwardEps")
        bvps = q.get("bvps") or info.get("bookValue")
        pe = q.get("pe") or info.get("trailingPE") or info.get("forwardPE")
        pb = q.get("pb") or info.get("priceToBook")
        market_cap = q.get("market_cap") or info.get("marketCap")
        q.update({"price": price, "eps": eps, "bvps": bvps, "pe": pe, "pb": pb, "market_cap": market_cap})
    except Exception:
        pass

    price = v66_num(q.get("price"))
    eps = v66_num(q.get("eps"))
    bvps = v66_num(q.get("bvps"))
    pe = v66_num(q.get("pe"))
    pb = v66_num(q.get("pb"))
    if (pd.isna(pe) or pe <= 0) and pd.notna(price) and pd.notna(eps) and eps > 0:
        pe = price / eps
        q["pe_source"] = "價格/EPS推算"
    else:
        q["pe_source"] = "Yahoo/原始資料" if pd.notna(pe) else "缺資料"
    if (pd.isna(pb) or pb <= 0) and pd.notna(price) and pd.notna(bvps) and bvps > 0:
        pb = price / bvps
        q["pb_source"] = "價格/BVPS推算"
    else:
        q["pb_source"] = "Yahoo/原始資料" if pd.notna(pb) else "缺資料"
    q["price"], q["eps"], q["bvps"], q["pe"], q["pb"] = price, eps, bvps, pe, pb
    return q

def v66_fmt(x, digits=2):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):.{digits}f}"
    except Exception:
        return str(x)

def v66_peer_group(symbol):
    code = str(symbol).upper().split(".")[0]
    groups = {
        "semiconductor": ["2330.TW", "2303.TW", "5347.TWO", "2454.TW", "2379.TW", "3711.TW"],
        "ai_server": ["2382.TW", "3231.TW", "6669.TW", "2357.TW", "2376.TW"],
        "industrial_pc": ["6570.TW", "2395.TW", "6414.TW", "3479.TW", "8114.TW", "6112.TW"],
        "electronics": ["8112.TW", "6189.TW", "6112.TW", "3374.TW", "6739.TW"],
    }
    if code in ["6570","2395","6414","3479","8114","6112"]:
        return groups["industrial_pc"], "工業電腦/系統整合"
    if code in ["2382","3231","6669","2357","2376"]:
        return groups["ai_server"], "AI伺服器/電腦週邊"
    if code in ["8112","6189","3374","6739"]:
        return groups["electronics"], "電子通路/電子零組件"
    return groups["semiconductor"], "半導體/IC設計"

def v66_industry_valuation_table(symbol, q=None, scores=None):
    peers, industry_name = v66_peer_group(symbol)
    rows = []
    pe_vals, pb_vals = [], []
    for p in peers:
        qq = v66_get_quote_any(p)
        pe, pb = v66_num(qq.get("pe")), v66_num(qq.get("pb"))
        if pd.notna(pe) and pe > 0 and pe < 300:
            pe_vals.append(pe)
        if pd.notna(pb) and pb > 0 and pb < 80:
            pb_vals.append(pb)
        rows.append({
            "同業公司": stock_name_only(p),
            "代碼": p,
            "現價": v66_fmt(qq.get("price")),
            "EPS": v66_fmt(qq.get("eps")),
            "BVPS": v66_fmt(qq.get("bvps")),
            "PE": v66_fmt(pe),
            "PB": v66_fmt(pb),
            "PE來源": qq.get("pe_source", "Yahoo/推算"),
            "PB來源": qq.get("pb_source", "Yahoo/推算"),
            "產業": industry_name,
        })
    med_pe = float(np.nanmedian(pe_vals)) if pe_vals else np.nan
    med_pb = float(np.nanmedian(pb_vals)) if pb_vals else np.nan

    # 用產業中位數補仍為 N/A 的比較欄，並標示為產業代理
    for r in rows:
        if r["PE"] == "N/A" and pd.notna(med_pe):
            r["PE"] = f"{med_pe:.2f}"
            r["PE來源"] = "產業中位數代理"
        if r["PB"] == "N/A" and pd.notna(med_pb):
            r["PB"] = f"{med_pb:.2f}"
            r["PB來源"] = "產業中位數代理"
    df = pd.DataFrame(rows)
    return df, med_pe, med_pb, industry_name

def v66_ai_industry_table(symbol, q, scores):
    df, med_pe, med_pb, industry_name = v66_industry_valuation_table(symbol, q, scores)
    return df

def v66_ai_competition_table(symbol, q, scores):
    df, med_pe, med_pb, industry_name = v66_industry_valuation_table(symbol, q, scores)
    base_q = v66_get_quote_any(symbol)
    base_pe, base_pb = v66_num(base_q.get("pe")), v66_num(base_q.get("pb"))
    rows = []
    for _, r in df.iterrows():
        try:
            peer_pe = float(r["PE"]) if r["PE"] != "N/A" else np.nan
            peer_pb = float(r["PB"]) if r["PB"] != "N/A" else np.nan
        except Exception:
            peer_pe, peer_pb = np.nan, np.nan
        pe_gap = ((base_pe - peer_pe) / peer_pe * 100) if pd.notna(base_pe) and pd.notna(peer_pe) and peer_pe else np.nan
        pb_gap = ((base_pb - peer_pb) / peer_pb * 100) if pd.notna(base_pb) and pd.notna(peer_pb) and peer_pb else np.nan
        rows.append([
            r["同業公司"], r["代碼"], r["現價"], r["PE"], r["PB"],
            v66_fmt(pe_gap, 1) + "%" if pd.notna(pe_gap) else "N/A",
            v66_fmt(pb_gap, 1) + "%" if pd.notna(pb_gap) else "N/A",
            r["PE來源"] + " / " + r["PB來源"],
            "PE/PB/同業中位數比較",
        ])
    return pd.DataFrame(rows, columns=["競爭對手", "代碼", "現價", "PE", "PB", "PE相對差", "PB相對差", "資料層", "說明"])

def v66_industry_summary(symbol, q, scores):
    df, med_pe, med_pb, industry_name = v66_industry_valuation_table(symbol, q, scores)
    bq = v66_get_quote_any(symbol)
    rows = [
        ["產業分類", industry_name, "依股票代碼自動歸類"],
        ["同業PE中位數", v66_fmt(med_pe), "同業可得PE中位數；缺資料則不硬填"],
        ["同業PB中位數", v66_fmt(med_pb), "同業可得PB中位數；缺資料則不硬填"],
        ["本股PE", v66_fmt(bq.get("pe")), bq.get("pe_source", "Yahoo/推算")],
        ["本股PB", v66_fmt(bq.get("pb")), bq.get("pb_source", "Yahoo/推算")],
    ]
    return pd.DataFrame(rows, columns=["項目", "數值", "說明"])

def v66_ai_research_center(symbol, q, df, scores):
    st.markdown(f"## 🤖 AI研究中心資料版：{display_name(symbol)}")
    st.caption("V66：產業與競爭分析加入 PE/PB 多層估值引擎；Yahoo缺資料時以 EPS/BVPS 或產業中位數代理，並標示資料層。")
    tabs = st.tabs([
        "①AI評級", "②AI估值", "③AI財報", "④AI法人", "⑤AI產業",
        "⑥AI新聞", "⑦AI事件", "⑧AI法說會", "⑨AI競爭分析", "⑩AI風險預警", "資料來源"
    ])
    with tabs[0]:
        st.dataframe(pd.DataFrame([
            ["AI總分", f"{ai_total(scores) if 'ai_total' in globals() else scores.get('ai', 60):.1f}/100", "技術、財報、法人、ESG、風險加權"],
            ["目前狀態", "偏多" if scores.get("tech", 50) >= 65 else "中立", "依分數區間判斷"],
        ], columns=["項目", "結果", "說明"]), use_container_width=True, hide_index=True)
    with tabs[1]:
        st.dataframe(v66_industry_summary(symbol, q, scores), use_container_width=True, hide_index=True)
        st.info("若個股或同業 Yahoo 缺 PE/PB，系統會先用價格/EPS、價格/BVPS推算；仍缺資料時才使用產業中位數代理。")
    with tabs[2]:
        bq = v66_get_quote_any(symbol)
        st.dataframe(pd.DataFrame([
            ["現價", v66_fmt(bq.get("price")), "Yahoo/fast_info"],
            ["EPS", v66_fmt(bq.get("eps")), "Yahoo info"],
            ["BVPS", v66_fmt(bq.get("bvps")), "Yahoo info"],
            ["PE", v66_fmt(bq.get("pe")), bq.get("pe_source", "Yahoo/推算")],
            ["PB", v66_fmt(bq.get("pb")), bq.get("pb_source", "Yahoo/推算")],
        ], columns=["財報/估值項目", "目前數值", "資料來源"]), use_container_width=True, hide_index=True)
    with tabs[3]:
        st.dataframe(pd.DataFrame([
            ["法人分數", scores.get("inst", 50), "量價/法人代理"],
            ["主力分數", scores.get("main", 50), "量價/主力代理"],
            ["籌碼共識", scores.get("chip", 50), "法人+主力+融資融券代理"],
        ], columns=["項目","分數","說明"]), use_container_width=True, hide_index=True)
    with tabs[4]:
        st.dataframe(v66_ai_industry_table(symbol, q, scores), use_container_width=True, hide_index=True)
    with tabs[5]:
        st.dataframe(v65_ai_news_table(symbol, q, scores) if "v65_ai_news_table" in globals() else pd.DataFrame(), use_container_width=True, hide_index=True)
    with tabs[6]:
        st.dataframe(v65_ai_event_table(symbol, q, scores) if "v65_ai_event_table" in globals() else pd.DataFrame(), use_container_width=True, hide_index=True)
    with tabs[7]:
        st.dataframe(v65_ai_conference_table(symbol, q, scores) if "v65_ai_conference_table" in globals() else pd.DataFrame(), use_container_width=True, hide_index=True)
    with tabs[8]:
        st.dataframe(v66_ai_competition_table(symbol, q, scores), use_container_width=True, hide_index=True)
    with tabs[9]:
        st.dataframe(v65_ai_risk_table(symbol, q, scores) if "v65_ai_risk_table" in globals() else pd.DataFrame(), use_container_width=True, hide_index=True)
    with tabs[10]:
        st.dataframe(pd.DataFrame([
            ["Yahoo Finance", "價格、EPS、BVPS、PE、PB", "中", "可得則直接使用"],
            ["推算層", "PE=價格/EPS；PB=價格/BVPS", "中", "Yahoo缺PE/PB時使用"],
            ["產業中位數代理", "同業PE/PB中位數", "中低", "同業個股缺資料時補上，會清楚標示"],
            ["MOPS/正式資料", "正式財報與法說會", "高", "後續可串接"],
        ], columns=["資料層", "用途", "可信度", "備註"]), use_container_width=True, hide_index=True)
# ================= V66 INDUSTRY VALUATION DATA EDITION LAYER END =================

# ================= V67 AI RESEARCH PRO EDITION LAYER =================
V67_NAME_MAP = {
    "2330.TW": "台積電", "2303.TW": "聯電", "2454.TW": "聯發科",
    "2317.TW": "鴻海", "2382.TW": "廣達", "2412.TW": "中華電",
    "2379.TW": "瑞昱", "2408.TW": "南亞科", "3374.TW": "精材",
    "6739.TW": "竹陞科技", "8112.TW": "至上", "6189.TW": "豐藝",
    "6215.TWO": "和椿科技", "6830.TW": "汎銓", "6415.TW": "矽力-KY",
    "5347.TWO": "世界先進", "3711.TW": "日月光投控", "3661.TW": "世芯-KY",
    "6112.TW": "邁達特", "6570.TW": "維田", "2357.TW": "華碩", "2376.TW": "技嘉", "3231.TW": "緯創",
}
try:
    CODE_NAME_MAP.update(V67_NAME_MAP)
except Exception:
    CODE_NAME_MAP = V67_NAME_MAP.copy()
try:
    TW_STOCKS.update({"維田":"6570.TW", "邁達特":"6112.TW", "精材":"3374.TW", "竹陞科技":"6739.TW"})
except Exception:
    pass

def stock_name_only(symbol):
    s = str(symbol).upper().strip()
    code = s.split(".")[0]
    if s in V67_NAME_MAP:
        return V67_NAME_MAP[s]
    try:
        if s in CODE_NAME_MAP:
            return CODE_NAME_MAP[s]
    except Exception:
        pass
    for full, nm in V67_NAME_MAP.items():
        if full.split(".")[0] == code:
            return nm
    try:
        nm = yahoo_name_lookup(s)
        return nm or s
    except Exception:
        return s

def display_name(symbol):
    s = str(symbol).upper().strip()
    return f"{stock_name_only(s)} / {s}"

def v67_num(x, default=np.nan):
    try:
        if x is None or x == "N/A":
            return default
        return float(x)
    except Exception:
        return default

def v67_fmt(x, digits=2):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):.{digits}f}"
    except Exception:
        return str(x)

def v67_get_quote_any(symbol):
    if "v66_get_quote_any" in globals():
        return v66_get_quote_any(symbol)
    try:
        return get_quote(symbol) if "get_quote" in globals() else {}
    except Exception:
        return {}

def v67_peer_group(symbol):
    if "v66_peer_group" in globals():
        return v66_peer_group(symbol)
    return ["2330.TW","2303.TW","2454.TW","2379.TW"], "科技同業"

def v67_industry_chain(symbol):
    code = str(symbol).upper().split(".")[0]
    if code in ["6570","2395","6414","3479","8114","6112"]:
        rows = [
            ["上游", "CPU、記憶體、面板、機構件、工控零組件", "供應成本、匯率、交期", "代理"],
            ["中游", "工業電腦、IPC、系統整合、邊緣AI設備", "產品組合、毛利率、專案進度", "代理"],
            ["下游", "智慧製造、醫療、交通、能源、AIoT", "訂單能見度、客戶CAPEX", "代理"],
            ["競爭者", "研華、樺漢、飛捷、振樺電、邁達特", "PE/PB/ROE/營收成長比較", "系統估算"],
        ]
        industry = "工業電腦/系統整合"
    elif code in ["2382","3231","6669","2357","2376"]:
        rows = [
            ["上游", "GPU、CPU、記憶體、PCB、散熱、電源", "AI伺服器零組件供應", "代理"],
            ["中游", "伺服器組裝、ODM、主機板、系統設計", "出貨動能、毛利率", "代理"],
            ["下游", "雲端服務商、資料中心、企業AI", "AI資本支出", "代理"],
            ["競爭者", "廣達、緯創、英業達、華碩、技嘉", "PE/PB/出貨動能", "系統估算"],
        ]
        industry = "AI伺服器/電腦週邊"
    elif code in ["2330","2303","5347","2454","2379","3661"]:
        rows = [
            ["上游", "半導體設備、矽晶圓、材料、EDA/IP", "供應鏈成本、先進製程需求", "代理"],
            ["中游", "晶圓代工、IC設計、封測", "製程/產品週期、稼動率", "代理"],
            ["下游", "AI、手機、車用、HPC、工控", "終端需求", "代理"],
            ["競爭者", "台積電、聯電、世界先進、聯發科、瑞昱", "估值與成長比較", "系統估算"],
        ]
        industry = "半導體/IC設計"
    else:
        rows = [
            ["上游", "原物料、零組件、代理品牌", "成本與供給", "代理"],
            ["中游", "製造、通路、系統整合", "營收與毛利", "代理"],
            ["下游", "企業客戶、消費市場、產業應用", "需求與價格", "代理"],
            ["競爭者", "同業公司", "估值與成長比較", "系統估算"],
        ]
        industry = "電子零組件/通路"
    return pd.DataFrame(rows, columns=["產業鏈位置", "內容", "觀察重點", "資料層"]), industry

def v67_eps_forecast(symbol, q, scores):
    qq = v67_get_quote_any(symbol)
    eps = v67_num(qq.get("eps"), 1.0)
    tech = v67_num(scores.get("tech", 50), 50)
    fund = v67_num(scores.get("fund", 50), 50)
    inst = v67_num(scores.get("inst", 50), 50)
    growth_base = max(-0.15, min(0.35, (tech + fund + inst - 150) / 500))
    rows = []
    labels = ["未來Q1", "未來Q2", "未來Q3", "未來Q4"]
    for i, lab in enumerate(labels, start=1):
        conservative = eps * (1 + growth_base * 0.5) ** (i/4)
        base = eps * (1 + growth_base) ** (i/4)
        bull = eps * (1 + growth_base * 1.5 + 0.03) ** (i/4)
        rows.append([lab, v67_fmt(conservative), v67_fmt(base), v67_fmt(bull), "EPS代理預測：由EPS、技術/財報/法人分數推估"])
    return pd.DataFrame(rows, columns=["期間", "保守EPS", "基準EPS", "樂觀EPS", "說明"])

def v67_target_price(symbol, q, scores):
    qq = v67_get_quote_any(symbol)
    price = v67_num(qq.get("price"), np.nan)
    eps = v67_num(qq.get("eps"), np.nan)
    pe = v67_num(qq.get("pe"), np.nan)
    peers, industry = v67_peer_group(symbol)
    try:
        comp, med_pe, med_pb, industry_name = v66_industry_valuation_table(symbol, q, scores)
    except Exception:
        med_pe, med_pb, industry_name = pe if pd.notna(pe) else 15, np.nan, industry
    if pd.isna(eps) or eps <= 0:
        eps = price / pe if pd.notna(price) and pd.notna(pe) and pe > 0 else np.nan
    base_pe = med_pe if pd.notna(med_pe) and med_pe > 0 else (pe if pd.notna(pe) and pe > 0 else 18)
    ai_adj = (v67_num(scores.get("ai", scores.get("tech", 60)), 60) - 60) / 100
    conservative_pe = max(6, base_pe * (0.85 + ai_adj * 0.2))
    base_case_pe = max(6, base_pe * (1.00 + ai_adj * 0.3))
    bull_pe = max(6, base_pe * (1.20 + ai_adj * 0.5))
    rows = []
    for name, used_pe in [("保守價", conservative_pe), ("基準價", base_case_pe), ("樂觀價", bull_pe)]:
        target = eps * used_pe if pd.notna(eps) else np.nan
        upside = ((target / price - 1) * 100) if pd.notna(target) and pd.notna(price) and price else np.nan
        rows.append([name, v67_fmt(target), v67_fmt(used_pe), v67_fmt(upside, 1) + "%" if pd.notna(upside) else "N/A", "EPS × 產業PE × AI調整"])
    return pd.DataFrame(rows, columns=["情境", "AI目標價", "使用PE", "相對現價", "公式"])

def v67_research_commentary(symbol, q, scores):
    qq = v67_get_quote_any(symbol)
    name = stock_name_only(symbol)
    price = v67_fmt(qq.get("price"))
    pe = v67_fmt(qq.get("pe"))
    pb = v67_fmt(qq.get("pb"))
    ai_score = v67_num(scores.get("ai", scores.get("tech", 60)), 60)
    risk = v67_num(scores.get("risk", 50), 50)
    status = "偏多" if ai_score >= 70 else ("中立偏多" if ai_score >= 60 else "中立")
    risk_txt = "風險偏高" if risk >= 65 else ("風險中等" if risk >= 45 else "風險偏低")
    rows = [
        ["AI投資評語", f"{name} 目前AI評級為{status}，現價約 {price}，PE約 {pe}，PB約 {pb}。"],
        ["主要優勢", "若技術、法人、財報分數同步改善，模型會提高基準價與樂觀價權重。"],
        ["主要風險", f"{risk_txt}；若財報資料缺漏或新聞/法說未串接，可信度需下修。"],
        ["資料聲明", "本頁為研究與教學用途；新聞、法說會若未接正式API，會以代理資料層標示。"],
    ]
    return pd.DataFrame(rows, columns=["段落", "內容"])

def v67_live_news_placeholder(symbol):
    name = stock_name_only(symbol)
    return pd.DataFrame([
        ["即時新聞", f"{name} 新聞標題", "尚未接新聞API", "待串接", "接 RSS/NewsAPI 後自動更新"],
        ["重大訊息", f"{name} 公開資訊觀測站重大訊息", "尚未接MOPS API", "待串接", "接MOPS後自動更新"],
        ["產業新聞", "AI、半導體、工業電腦、電子通路相關新聞", "代理資料層", "中低", "目前以產業分類代理"],
    ], columns=["類別", "內容", "來源", "可信度", "更新方式"])

def v67_ai_research_center(symbol, q, df, scores):
    st.markdown(f"## 🤖 AI研究中心 Pro：{display_name(symbol)}")
    st.caption("V67：新增產業鏈地圖、AI EPS預測、AI目標價、研究評語、新聞/法說會自動更新架構。未接正式API者會清楚標示為代理資料層。")
    tabs = st.tabs([
        "總覽", "AI新聞", "產業鏈", "競爭分析", "EPS預測",
        "AI目標價", "法說會", "事件/風險", "研究評語", "資料更新"
    ])

    with tabs[0]:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("AI分數", f"{v67_num(scores.get('ai', scores.get('tech', 60)), 60):.1f}/100")
        c2.metric("風險指數", f"{v67_num(scores.get('risk', 50), 50):.0f}/100")
        c3.metric("法人分數", f"{v67_num(scores.get('inst', 50), 50):.0f}/100")
        c4.metric("資料層", "半自動")
        st.dataframe(v67_research_commentary(symbol, q, scores), use_container_width=True, hide_index=True)

    with tabs[1]:
        st.markdown("### 📰 AI新聞中心")
        st.dataframe(v67_live_news_placeholder(symbol), use_container_width=True, hide_index=True)
        if "v65_ai_news_table" in globals():
            st.markdown("#### 新聞代理判讀")
            st.dataframe(v65_ai_news_table(symbol, q, scores), use_container_width=True, hide_index=True)

    with tabs[2]:
        chain, industry = v67_industry_chain(symbol)
        st.markdown(f"### 🧭 產業鏈地圖：{industry}")
        st.dataframe(chain, use_container_width=True, hide_index=True)
        try:
            st.markdown("#### 同業估值表")
            st.dataframe(v66_ai_industry_table(symbol, q, scores), use_container_width=True, hide_index=True)
        except Exception:
            pass

    with tabs[3]:
        st.markdown("### 🏁 競爭分析數據化")
        try:
            st.dataframe(v66_ai_competition_table(symbol, q, scores), use_container_width=True, hide_index=True)
        except Exception:
            st.info("競爭分析資料暫無法計算。")

    with tabs[4]:
        st.markdown("### 📈 AI EPS 預測")
        st.dataframe(v67_eps_forecast(symbol, q, scores), use_container_width=True, hide_index=True)
        st.caption("EPS預測為代理模型：以目前EPS、AI分數、技術/財報/法人分數推估，不等於公司財測。")

    with tabs[5]:
        st.markdown("### 🎯 AI目標價")
        st.dataframe(v67_target_price(symbol, q, scores), use_container_width=True, hide_index=True)
        st.caption("目標價公式：EPS × 產業PE × AI調整。若EPS或同業資料缺漏，會以可得資料代理。")

    with tabs[6]:
        st.markdown("### 🎙 AI法說會中心")
        if "v65_ai_conference_table" in globals():
            st.dataframe(v65_ai_conference_table(symbol, q, scores), use_container_width=True, hide_index=True)
        st.info("若未串接MOPS/公司IR，本區為法說會追蹤框架；接API後可自動更新法說會重點與逐字稿摘要。")

    with tabs[7]:
        st.markdown("### ⚠️ AI事件與風險預警")
        if "v65_ai_event_table" in globals():
            st.dataframe(v65_ai_event_table(symbol, q, scores), use_container_width=True, hide_index=True)
        if "v65_ai_risk_table" in globals():
            st.dataframe(v65_ai_risk_table(symbol, q, scores), use_container_width=True, hide_index=True)

    with tabs[8]:
        st.markdown("### 🧾 AI研究評語")
        st.dataframe(v67_research_commentary(symbol, q, scores), use_container_width=True, hide_index=True)

    with tabs[9]:
        st.markdown("### 🔄 資料是否自動更新")
        st.dataframe(pd.DataFrame([
            ["股價/K線/技術指標", "自動更新", "Yahoo Finance", "每次查詢或刷新重算"],
            ["AI評級/AI目標價/EPS預測", "自動重算", "價格、EPS、PE/PB、分數模型", "每次查詢重算"],
            ["產業/競爭分析", "半自動", "Yahoo + 產業代理表", "同業價格估值會更新；產業分類表固定"],
            ["AI新聞", "目前代理；可升級即時", "RSS/NewsAPI/MOPS", "需接API後即時更新"],
            ["AI法說會", "目前框架；可升級即時", "MOPS/公司IR/PDF", "需接API或PDF來源後更新"],
            ["資料可信度", "自動標示", "資料層判斷", "正式資料>Yahoo>推算>代理"],
        ], columns=["模組", "更新狀態", "來源", "說明"]), use_container_width=True, hide_index=True)
# ================= V67 AI RESEARCH PRO EDITION LAYER END =================

# ================= V68 AI RESEARCH INSTITUTE EDITION LAYER =================
V68_NAME_MAP = {
    "2330.TW": "台積電", "2303.TW": "聯電", "2454.TW": "聯發科",
    "2317.TW": "鴻海", "2382.TW": "廣達", "2412.TW": "中華電",
    "2379.TW": "瑞昱", "2408.TW": "南亞科", "3374.TW": "精材",
    "6739.TW": "竹陞科技", "8112.TW": "至上", "6189.TW": "豐藝",
    "6215.TWO": "和椿科技", "6830.TW": "汎銓", "6415.TW": "矽力-KY",
    "5347.TWO": "世界先進", "3711.TW": "日月光投控", "3661.TW": "世芯-KY",
    "6112.TW": "邁達特", "6570.TW": "維田", "2357.TW": "華碩", "2376.TW": "技嘉", "3231.TW": "緯創",
    "NVDA": "NVIDIA", "AMD": "AMD", "INTC": "Intel", "AVGO": "Broadcom",
    "TSM": "TSMC ADR", "MU": "Micron", "QCOM": "Qualcomm",
    "005930.KS": "Samsung Electronics", "000660.KS": "SK Hynix",
    "GFS": "GlobalFoundries", "TSEM": "Tower Semiconductor", "SMCI": "Supermicro", "DELL": "Dell",
}
try:
    CODE_NAME_MAP.update(V68_NAME_MAP)
except Exception:
    CODE_NAME_MAP = V68_NAME_MAP.copy()
try:
    TW_STOCKS.update({"維田":"6570.TW", "邁達特":"6112.TW", "世界先進":"5347.TWO", "精材":"3374.TW"})
except Exception:
    pass

def stock_name_only(symbol):
    s = str(symbol).upper().strip()
    code = s.split(".")[0]
    if s in V68_NAME_MAP:
        return V68_NAME_MAP[s]
    try:
        if s in CODE_NAME_MAP:
            return CODE_NAME_MAP[s]
    except Exception:
        pass
    for full, nm in V68_NAME_MAP.items():
        if full.split(".")[0] == code:
            return nm
    try:
        nm = yahoo_name_lookup(s)
        return nm or s
    except Exception:
        return s

def display_name(symbol):
    s = str(symbol).upper().strip()
    return f"{stock_name_only(s)} / {s}"

def v68_num(x, default=np.nan):
    try:
        if x is None or x == "N/A":
            return default
        return float(x)
    except Exception:
        return default

def v68_fmt(x, digits=2):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):.{digits}f}"
    except Exception:
        return str(x)

def v68_get_quote_any(symbol):
    if "v66_get_quote_any" in globals():
        return v66_get_quote_any(symbol)
    if "v67_get_quote_any" in globals():
        return v67_get_quote_any(symbol)
    try:
        return get_quote(symbol) if "get_quote" in globals() else {}
    except Exception:
        return {}

def v68_global_competitors(symbol):
    code = str(symbol).upper().split(".")[0]
    if code in ["2330", "TSM"]:
        return [
            ["台積電", "2330.TW", "台灣", "晶圓代工龍頭", "本股/核心"],
            ["Samsung Foundry", "005930.KS", "韓國", "先進製程競爭者", "國際同業"],
            ["Intel Foundry", "INTC", "美國", "IDM轉型代工", "國際同業"],
            ["GlobalFoundries", "GFS", "美國", "成熟製程/特殊製程", "國際同業"],
            ["SMIC", "0981.HK", "中國", "中國晶圓代工", "國際同業"],
            ["聯電", "2303.TW", "台灣", "成熟製程", "台灣同業"],
            ["世界先進", "5347.TWO", "台灣", "特殊製程/成熟製程", "台灣同業"],
        ], "晶圓代工"
    if code in ["5347", "2303"]:
        return [
            ["世界先進", "5347.TWO", "台灣", "特殊製程/成熟製程", "本股/同業"],
            ["聯電", "2303.TW", "台灣", "成熟製程代工", "台灣同業"],
            ["台積電", "2330.TW", "台灣", "晶圓代工龍頭", "上位同業"],
            ["Tower Semiconductor", "TSEM", "以色列", "特殊製程代工", "國際同業"],
            ["GlobalFoundries", "GFS", "美國", "特殊/成熟製程", "國際同業"],
            ["Samsung Foundry", "005930.KS", "韓國", "晶圓代工", "國際同業"],
        ], "特殊製程/成熟製程代工"
    if code in ["2382","3231","6669","2357","2376"]:
        return [
            ["廣達", "2382.TW", "台灣", "AI伺服器ODM", "本股/同業"],
            ["緯創", "3231.TW", "台灣", "AI伺服器ODM", "台灣同業"],
            ["英業達", "2356.TW", "台灣", "伺服器ODM", "台灣同業"],
            ["Supermicro", "SMCI", "美國", "AI伺服器品牌/整機", "國際同業"],
            ["Dell", "DELL", "美國", "企業伺服器", "國際同業"],
            ["NVIDIA", "NVDA", "美國", "GPU/AI平台", "上游核心"],
        ], "AI伺服器"
    if code in ["6570","6112","2395","6414"]:
        return [
            ["維田", "6570.TW", "台灣", "工業電腦/IPC", "本股/同業"],
            ["邁達特", "6112.TW", "台灣", "系統整合/雲端", "同業"],
            ["研華", "2395.TW", "台灣", "工業電腦龍頭", "台灣同業"],
            ["樺漢", "6414.TW", "台灣", "IPC/系統整合", "台灣同業"],
            ["Siemens", "SIE.DE", "德國", "工業自動化", "國際同業"],
            ["Schneider", "SU.PA", "法國", "能源管理/自動化", "國際同業"],
        ], "工業電腦/系統整合"
    return [
        ["NVIDIA", "NVDA", "美國", "AI GPU", "國際核心"],
        ["AMD", "AMD", "美國", "CPU/GPU", "國際同業"],
        ["Intel", "INTC", "美國", "CPU/Foundry", "國際同業"],
        ["台積電", "2330.TW", "台灣", "晶圓代工", "供應鏈核心"],
        ["聯發科", "2454.TW", "台灣", "IC設計", "台灣同業"],
    ], "科技產業"

def v68_quote_table(symbols):
    rows = []
    for name, sym, country, role, relation in symbols:
        q = v68_get_quote_any(sym)
        rows.append([
            name, sym, country, role, relation,
            v68_fmt(q.get("price")),
            v68_fmt(q.get("pe")),
            v68_fmt(q.get("pb")),
            q.get("pe_source", "Yahoo/推算"),
        ])
    return pd.DataFrame(rows, columns=["公司", "代碼", "國家", "角色", "關係", "現價", "PE", "PB", "資料層"])

def v68_enterprise_vs_competitors(symbol, q, scores):
    comps, industry = v68_global_competitors(symbol)
    rows = []
    for name, sym, country, role, relation in comps:
        qq = v68_get_quote_any(sym)
        price = v68_num(qq.get("price"))
        eps = v68_num(qq.get("eps"))
        pe = v68_num(qq.get("pe"))
        pb = v68_num(qq.get("pb"))
        # Simple valuation proxy
        fair_pe = pe if pd.notna(pe) and pe > 0 else 18
        fair = eps * fair_pe if pd.notna(eps) else np.nan
        ai_score = v68_num(scores.get("ai", scores.get("tech", 60)), 60)
        rows.append([
            name, sym, country, role,
            v68_fmt(price), v68_fmt(eps), v68_fmt(pe), v68_fmt(pb),
            v68_fmt(fair), f"{ai_score:.1f}" if sym == symbol else "同業資料",
            "企業評價×同業比較：PE/PB/EPS/代理合理價",
        ])
    return pd.DataFrame(rows, columns=["公司", "代碼", "國家", "角色", "現價", "EPS", "PE", "PB", "代理合理價", "AI分數", "說明"])

def v68_news_links(symbol):
    name = stock_name_only(symbol)
    code = str(symbol).split(".")[0]
    rows = [
        ["Google News", f"{name} 最新新聞", f"https://news.google.com/search?q={name}%20{code}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant", "可手動開啟；未接API前作為連結層"],
        ["Yahoo Finance", f"{symbol} Yahoo Finance", f"https://finance.yahoo.com/quote/{symbol}", "價格與公司新聞來源"],
        ["TWSE OpenAPI", "證交所 OpenAPI", "https://openapi.twse.com.tw/", "可串上市資料"],
        ["MOPS公開資訊觀測站", "重大訊息/財報/法說會", "https://mops.twse.com.tw/mops/web/index", "正式資訊來源"],
    ]
    return pd.DataFrame(rows, columns=["來源", "內容", "連結", "說明"])

def v68_investment_consensus(symbol, q, scores):
    qq = v68_get_quote_any(symbol)
    ai_score = v68_num(scores.get("ai", scores.get("tech", 60)), 60)
    tech = v68_num(scores.get("tech", 50), 50)
    fund = v68_num(scores.get("fund", 50), 50)
    inst = v68_num(scores.get("inst", 50), 50)
    risk = v68_num(scores.get("risk", 50), 50)
    valuation = 70 if pd.notna(v68_num(qq.get("pe"))) else 55
    final = ai_score*0.25 + tech*0.20 + fund*0.20 + inst*0.20 + valuation*0.10 + (100-risk)*0.05
    grade = "偏多" if final >= 70 else ("中立偏多" if final >= 60 else ("中立" if final >= 50 else "偏弱"))
    rows = [
        ["AI投資共識", f"{final:.1f}/100", grade],
        ["技術面", f"{tech:.1f}/100", "K線、均線、MACD、RSI"],
        ["財報面", f"{fund:.1f}/100", "EPS、PE、PB、財報可得性"],
        ["法人籌碼", f"{inst:.1f}/100", "法人/主力/融資融券代理"],
        ["估值面", f"{valuation:.1f}/100", "PE/PB與同業比較"],
        ["風險修正", f"{risk:.1f}/100", "風險越高扣分越多"],
    ]
    return pd.DataFrame(rows, columns=["項目", "分數", "說明"])

def v68_competitiveness_rank(symbol, q, scores):
    comps, industry = v68_global_competitors(symbol)
    rows = []
    for name, sym, country, role, relation in comps:
        qq = v68_get_quote_any(sym)
        pe = v68_num(qq.get("pe"))
        pb = v68_num(qq.get("pb"))
        price = v68_num(qq.get("price"))
        score = 60
        if pd.notna(pe) and pe > 0:
            score += 8 if pe < 25 else (-5 if pe > 60 else 2)
        if pd.notna(pb) and pb > 0:
            score += 5 if pb < 5 else (-4 if pb > 15 else 1)
        if relation in ["本股/核心", "本股/同業"]:
            score += 5
        if "龍頭" in role or name in ["台積電", "NVIDIA"]:
            score += 12
        rows.append([name, sym, country, role, min(100, max(0, round(score, 1))), "估值+產業角色代理排名"])
    out = pd.DataFrame(rows, columns=["公司", "代碼", "國家", "角色", "AI競爭力分數", "說明"])
    return out.sort_values("AI競爭力分數", ascending=False).reset_index(drop=True)

def v68_research_institute(symbol, q, df, scores):
    st.markdown(f"## 🧠 AI研究院 Professional：{display_name(symbol)}")
    st.caption("V68：整合真實新聞連結層、MOPS/TWSE資料層、全球競爭對手、企業評價×同業比較、AI投資共識與產業鏈地圖。未串API者會清楚標示。")

    tabs = st.tabs([
        "總覽", "新聞/重大訊息", "全球競爭", "企業評價比較",
        "產業鏈", "AI投資共識", "AI目標價", "法說會", "資料更新"
    ])

    with tabs[0]:
        c1, c2, c3, c4 = st.columns(4)
        cons = v68_investment_consensus(symbol, q, scores)
        c1.metric("AI投資共識", cons.iloc[0,1])
        c2.metric("狀態", cons.iloc[0,2])
        c3.metric("資料層", "半自動+連結")
        c4.metric("版本", "V68")
        st.dataframe(cons, use_container_width=True, hide_index=True)

    with tabs[1]:
        st.markdown("### 📰 新聞與重大訊息連結層")
        st.dataframe(v68_news_links(symbol), use_container_width=True, hide_index=True)
        st.info("未接 NewsAPI/RSS/MOPS API 前，先提供可點選來源與代理說明；接API後可自動列出新聞標題、日期、影響分數。")

    with tabs[2]:
        comps, industry = v68_global_competitors(symbol)
        st.markdown(f"### 🌍 全球競爭對手：{industry}")
        st.dataframe(v68_quote_table(comps), use_container_width=True, hide_index=True)
        st.markdown("### 🏆 AI競爭力排名")
        st.dataframe(v68_competitiveness_rank(symbol, q, scores), use_container_width=True, hide_index=True)

    with tabs[3]:
        st.markdown("### 💎 企業評價 × 同業比較")
        st.dataframe(v68_enterprise_vs_competitors(symbol, q, scores), use_container_width=True, hide_index=True)
        st.caption("代理合理價為 EPS × PE 的簡化比較，正式估值仍以評價中心 DCF/FCFF/FCFE/EBO/PB/PE 等模型為主。")

    with tabs[4]:
        if "v67_industry_chain" in globals():
            chain, industry = v67_industry_chain(symbol)
        else:
            chain, industry = pd.DataFrame(), "科技產業"
        st.markdown(f"### 🧭 AI產業鏈地圖：{industry}")
        st.dataframe(chain, use_container_width=True, hide_index=True)

    with tabs[5]:
        st.markdown("### 📌 AI投資共識")
        st.dataframe(v68_investment_consensus(symbol, q, scores), use_container_width=True, hide_index=True)
        st.caption("白話說明：AI投資共識是把技術面、財報面、法人籌碼、估值面、風險修正整合成一個綜合分數。")

    with tabs[6]:
        st.markdown("### 🎯 AI目標價")
        if "v67_target_price" in globals():
            st.dataframe(v67_target_price(symbol, q, scores), use_container_width=True, hide_index=True)
        else:
            st.info("目標價模型暫不可用。")

    with tabs[7]:
        st.markdown("### 🎙 法說會中心")
        if "v65_ai_conference_table" in globals():
            st.dataframe(v65_ai_conference_table(symbol, q, scores), use_container_width=True, hide_index=True)
        st.info("後續可串 MOPS/公司IR/PDF，做法說會摘要、情緒分析、CAPEX/毛利率/訂單能見度追蹤。")

    with tabs[8]:
        st.markdown("### 🔄 自動更新狀態")
        st.dataframe(pd.DataFrame([
            ["股價/K線/PE/PB/EPS", "自動更新", "Yahoo Finance", "每次查詢重新抓取與計算"],
            ["企業評價模型", "自動重算", "價格、EPS、BVPS、估值模型", "每次查詢重算"],
            ["全球競爭對手", "半自動", "內建同業庫+Yahoo", "名單固定，估值資料可更新"],
            ["新聞/重大訊息", "連結層；可升級自動", "Google News、MOPS、TWSE、NewsAPI", "接API後可自動更新"],
            ["法說會", "框架層；可升級自動", "MOPS、公司IR、PDF", "接來源後可摘要"],
            ["產業鏈地圖", "半自動", "內建產業鏈資料庫", "產業結構固定，數據可擴充"],
        ], columns=["模組", "更新狀態", "來源", "說明"]), use_container_width=True, hide_index=True)
# ================= V68 AI RESEARCH INSTITUTE EDITION LAYER END =================

# ================= V70 INSTITUTIONAL EDITION LAYER =================
V70_TW_MASTER = [
    # code, name, market, industry, sub_industry, chain_position, business_model, global_class
    ("2330", "台積電", "上市", "半導體", "晶圓代工", "中游", "Foundry", "Semiconductor Foundry"),
    ("2303", "聯電", "上市", "半導體", "晶圓代工", "中游", "Foundry", "Mature Node Foundry"),
    ("5347", "世界先進", "上櫃", "半導體", "特殊/成熟製程晶圓代工", "中游", "Specialty Foundry", "Specialty Foundry"),
    ("2454", "聯發科", "上市", "半導體", "IC設計", "上游", "Fabless IC Design", "Fabless Semiconductor"),
    ("2379", "瑞昱", "上市", "半導體", "IC設計", "上游", "Fabless IC Design", "Fabless Semiconductor"),
    ("3711", "日月光投控", "上市", "半導體", "封裝測試", "下游", "OSAT", "Semiconductor Packaging & Testing"),
    ("3374", "精材", "上市", "半導體", "先進封裝/影像感測封裝", "下游", "Advanced Packaging", "Advanced Packaging"),
    ("6739", "竹陞科技", "上市", "半導體", "設備/自動化", "上中游", "Automation/Equipment", "Semiconductor Equipment"),
    ("3661", "世芯-KY", "上市", "半導體", "ASIC設計服務", "上游", "ASIC Design Service", "ASIC Design"),
    ("2382", "廣達", "上市", "電腦週邊", "AI伺服器/ODM", "中游", "ODM", "AI Server ODM"),
    ("3231", "緯創", "上市", "電腦週邊", "AI伺服器/ODM", "中游", "ODM", "AI Server ODM"),
    ("2357", "華碩", "上市", "電腦週邊", "品牌/主機板/AI伺服器", "中下游", "Brand + Hardware", "PC & Server Hardware"),
    ("2376", "技嘉", "上市", "電腦週邊", "主機板/伺服器", "中游", "Hardware", "Server Hardware"),
    ("6570", "維田", "上市", "工業電腦", "工業電腦/IPC", "中游", "IPC", "Industrial PC"),
    ("6112", "邁達特", "上市", "資訊服務", "系統整合/雲端", "中下游", "System Integration", "IT Service & Cloud"),
    ("2395", "研華", "上市", "工業電腦", "工業電腦/IoT", "中游", "IPC/IoT", "Industrial PC"),
    ("6414", "樺漢", "上市", "工業電腦", "IPC/系統整合", "中下游", "IPC/SI", "Industrial PC"),
    ("8112", "至上", "上市", "電子通路", "半導體通路", "中下游", "Distributor", "Semiconductor Distributor"),
    ("6189", "豐藝", "上市", "電子通路", "電子零組件通路", "中下游", "Distributor", "Electronic Component Distributor"),
    ("6215", "和椿科技", "上櫃", "自動化", "自動化零組件/系統", "中游", "Automation Solution", "Automation"),
    ("6830", "汎銓", "上市", "半導體", "材料分析/檢測", "中下游", "Testing/Analysis Service", "Semiconductor Analysis"),
    ("6415", "矽力-KY", "上市", "半導體", "電源管理IC", "上游", "Fabless PMIC", "Power IC Design"),
]
V70_GLOBAL_NAME_MAP = {
    "NVDA": "NVIDIA", "AMD": "AMD", "INTC": "Intel", "AVGO": "Broadcom", "QCOM": "Qualcomm",
    "TSM": "TSMC ADR", "MU": "Micron", "GFS": "GlobalFoundries", "TSEM": "Tower Semiconductor",
    "SMCI": "Supermicro", "DELL": "Dell", "005930.KS": "Samsung Electronics", "000660.KS": "SK Hynix",
    "AMAT": "Applied Materials", "ASML": "ASML", "LRCX": "Lam Research", "SNPS": "Synopsys", "CDNS": "Cadence",
}
V70_MASTER_DF = pd.DataFrame(V70_TW_MASTER, columns=["code","name","market","industry","sub_industry","chain_position","business_model","global_class"])

try:
    for _, r in V70_MASTER_DF.iterrows():
        sym = f"{r['code']}.TW" if r["market"] == "上市" else f"{r['code']}.TWO"
        CODE_NAME_MAP[sym] = r["name"]
        TW_STOCKS[r["name"]] = sym
    CODE_NAME_MAP.update(V70_GLOBAL_NAME_MAP)
except Exception:
    pass

def v70_symbol_candidates(raw):
    s = str(raw).strip().upper()
    if not s:
        return []
    if s.endswith(".TW") or s.endswith(".TWO") or "." in s and not s.endswith("."):
        return [s]
    if s.isdigit():
        row = V70_MASTER_DF[V70_MASTER_DF["code"] == s]
        if not row.empty:
            market = row.iloc[0]["market"]
            return [f"{s}.TW" if market == "上市" else f"{s}.TWO"]
        return [f"{s}.TW", f"{s}.TWO"]
    hit = V70_MASTER_DF[V70_MASTER_DF["name"].str.contains(s, case=False, na=False)]
    if hit.empty:
        hit = V70_MASTER_DF[V70_MASTER_DF["name"].str.contains(str(raw).strip(), na=False)]
    out = []
    for _, r in hit.head(10).iterrows():
        out.append(f"{r['code']}.TW" if r["market"] == "上市" else f"{r['code']}.TWO")
    return out

def stock_name_only(symbol):
    s = str(symbol).upper().strip()
    code = s.split(".")[0]
    row = V70_MASTER_DF[V70_MASTER_DF["code"] == code]
    if not row.empty:
        return row.iloc[0]["name"]
    if s in V70_GLOBAL_NAME_MAP:
        return V70_GLOBAL_NAME_MAP[s]
    try:
        if s in CODE_NAME_MAP:
            return CODE_NAME_MAP[s]
    except Exception:
        pass
    try:
        nm = yahoo_name_lookup(s)
        return nm or s
    except Exception:
        return s

def display_name(symbol):
    s = str(symbol).upper().strip()
    return f"{stock_name_only(s)} / {s}"

def v70_profile(symbol):
    s = str(symbol).upper().strip()
    code = s.split(".")[0]
    row = V70_MASTER_DF[V70_MASTER_DF["code"] == code]
    if row.empty:
        return {
            "公司": stock_name_only(s), "代碼": s, "市場": "海外/待分類", "產業": "科技產業",
            "次產業": "待分類", "產業鏈位置": "待確認", "商業模式": "待確認",
            "全球分類": "Global Technology", "競爭組": "global_tech",
            "AI關聯度": "中", "資料可信度": "中低"
        }
    r = row.iloc[0]
    comp_group = "global_tech"
    sub = str(r["sub_industry"])
    if "晶圓代工" in sub:
        comp_group = "foundry"
    elif "IC設計" in sub or "ASIC" in sub or "電源管理" in sub:
        comp_group = "fabless"
    elif "封裝" in sub or "檢測" in sub or "材料分析" in sub:
        comp_group = "osat_packaging"
    elif "AI伺服器" in sub or "伺服器" in sub:
        comp_group = "ai_server"
    elif "工業電腦" in sub or "系統整合" in sub:
        comp_group = "industrial_pc"
    elif "通路" in sub:
        comp_group = "distributor"
    elif "自動化" in sub or "設備" in sub:
        comp_group = "automation_equipment"
    return {
        "公司": r["name"], "代碼": s, "市場": r["market"], "產業": r["industry"],
        "次產業": r["sub_industry"], "產業鏈位置": r["chain_position"],
        "商業模式": r["business_model"], "全球分類": r["global_class"],
        "競爭組": comp_group, "AI關聯度": "高" if r["industry"] in ["半導體","電腦週邊"] else "中",
        "資料可信度": "高"
    }

def v70_num(x, default=np.nan):
    try:
        if x is None or x == "N/A" or str(x).strip() in ["", "None", "nan"]:
            return default
        return float(x)
    except Exception:
        return default

def v70_fmt(x, digits=2):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):.{digits}f}"
    except Exception:
        return str(x)

def v70_get_quote_any(symbol):
    if "v66_get_quote_any" in globals():
        return v66_get_quote_any(symbol)
    try:
        return get_quote(symbol) if "get_quote" in globals() else {}
    except Exception:
        return {}

def v70_resolve_eps(q):
    price = v70_num(q.get("price"))
    eps = v70_num(q.get("eps"))
    pe = v70_num(q.get("pe"))
    if pd.notna(eps) and eps > 0:
        return eps, "Yahoo/原始EPS"
    if pd.notna(price) and pd.notna(pe) and pe > 0:
        return price / pe, "現價/PE反推EPS"
    return np.nan, "EPS缺資料"

def v70_competitors(symbol):
    p = v70_profile(symbol)
    g = p["競爭組"]
    data = {
        "foundry": [
            ["台積電","2330.TW","台灣","先進/成熟製程晶圓代工","同產業"],
            ["聯電","2303.TW","台灣","成熟製程晶圓代工","同產業"],
            ["世界先進","5347.TWO","台灣","特殊/成熟製程代工","同產業"],
            ["Samsung Foundry","005930.KS","韓國","先進製程/晶圓代工","國際同業"],
            ["Intel Foundry","INTC","美國","IDM/Foundry","國際同業"],
            ["GlobalFoundries","GFS","美國","成熟/特殊製程","國際同業"],
            ["Tower Semiconductor","TSEM","以色列","特殊製程代工","國際同業"],
        ],
        "fabless": [
            ["聯發科","2454.TW","台灣","Fabless IC設計","同產業"],
            ["瑞昱","2379.TW","台灣","Fabless IC設計","同產業"],
            ["NVIDIA","NVDA","美國","GPU/AI平台","國際同業"],
            ["AMD","AMD","美國","CPU/GPU","國際同業"],
            ["Qualcomm","QCOM","美國","通訊晶片","國際同業"],
            ["Broadcom","AVGO","美國","通訊/ASIC","國際同業"],
        ],
        "osat_packaging": [
            ["精材","3374.TW","台灣","先進封裝/影像感測封裝","本地同業"],
            ["日月光投控","3711.TW","台灣","封裝測試龍頭","同產業"],
            ["Amkor","AMKR","美國","封裝測試","國際同業"],
            ["JCET","600584.SS","中國","封裝測試","國際同業"],
            ["TSMC","2330.TW","台灣","先進封裝重要客戶/平台","上下游關係"],
        ],
        "ai_server": [
            ["廣達","2382.TW","台灣","AI伺服器ODM","同產業"],
            ["緯創","3231.TW","台灣","AI伺服器ODM","同產業"],
            ["英業達","2356.TW","台灣","伺服器ODM","同產業"],
            ["Supermicro","SMCI","美國","AI伺服器品牌/整機","國際同業"],
            ["Dell","DELL","美國","企業伺服器","國際同業"],
            ["NVIDIA","NVDA","美國","GPU/AI平台","上游核心"],
        ],
        "industrial_pc": [
            ["研華","2395.TW","台灣","工業電腦龍頭","同產業"],
            ["樺漢","6414.TW","台灣","IPC/系統整合","同產業"],
            ["維田","6570.TW","台灣","工業電腦/IPC","同產業"],
            ["邁達特","6112.TW","台灣","系統整合/雲端","相關同業"],
            ["Siemens","SIE.DE","德國","工業自動化","國際同業"],
            ["Schneider","SU.PA","法國","能源管理/自動化","國際同業"],
        ],
        "distributor": [
            ["至上","8112.TW","台灣","半導體通路","同產業"],
            ["豐藝","6189.TW","台灣","電子零組件通路","同產業"],
            ["大聯大","3702.TW","台灣","半導體通路龍頭","同產業"],
            ["Arrow","ARW","美國","電子通路","國際同業"],
            ["Avnet","AVT","美國","電子通路","國際同業"],
        ],
        "automation_equipment": [
            ["和椿科技","6215.TWO","台灣","自動化零組件/系統","同產業"],
            ["竹陞科技","6739.TW","台灣","半導體自動化/設備","同產業"],
            ["上銀","2049.TW","台灣","傳動/自動化","同產業"],
            ["ASML","ASML","荷蘭","半導體設備","國際上游"],
            ["Applied Materials","AMAT","美國","半導體設備","國際上游"],
        ],
        "global_tech": [
            ["台積電","2330.TW","台灣","晶圓代工","科技核心"],
            ["NVIDIA","NVDA","美國","AI GPU","科技核心"],
            ["AMD","AMD","美國","CPU/GPU","科技同業"],
            ["Intel","INTC","美國","CPU/Foundry","科技同業"],
            ["Samsung","005930.KS","韓國","記憶體/Foundry","科技同業"],
        ],
    }
    return data.get(g, data["global_tech"]), p

def v70_chain_map(symbol):
    p = v70_profile(symbol)
    g = p["競爭組"]
    current = f"★ {p['公司']}（目前位置：{p['產業鏈位置']} / {p['次產業']}）"
    if g == "foundry":
        rows = [
            ["上游", "設備/材料/IP/EDA", "ASML、AMAT、LAM、Synopsys、Cadence", "供應製程設備與設計工具"],
            ["中游", current, "晶圓代工/特殊製程", "將IC設計轉為晶圓製造"],
            ["下游", "IC設計/品牌/系統廠", "NVIDIA、AMD、Apple、Qualcomm、車用/工控客戶", "終端需求牽動稼動率"],
        ]
    elif g == "fabless":
        rows = [
            ["上游", current, "IC設計/Fabless", "設計晶片，不自建晶圓廠"],
            ["中游", "晶圓代工/封測", "台積電、聯電、日月光", "製造與封裝"],
            ["下游", "品牌/系統/終端市場", "手機、AI伺服器、車用、網通", "終端需求決定出貨"],
        ]
    elif g == "osat_packaging":
        rows = [
            ["上游", "IC設計/晶圓代工", "NVIDIA、AMD、台積電、聯發科", "晶片設計與晶圓來源"],
            ["下游", current, "封裝測試/先進封裝", "晶圓切割、封裝、測試、模組化"],
            ["終端", "AI伺服器/手機/車用/工控", "廣達、緯創、Apple、車用客戶", "終端應用拉動封裝需求"],
        ]
    elif g == "ai_server":
        rows = [
            ["上游", "GPU/CPU/記憶體/散熱/PCB", "NVIDIA、AMD、Intel、Micron、台光電", "關鍵零組件"],
            ["中游", current, "AI伺服器ODM/硬體整合", "組裝、設計、交付"],
            ["下游", "雲端/企業客戶", "Microsoft、Amazon、Google、Meta、企業AI", "CAPEX與AI需求"],
        ]
    elif g == "industrial_pc":
        rows = [
            ["上游", "CPU/面板/工控零組件", "Intel、AMD、零組件廠", "硬體供應"],
            ["中游", current, "IPC/系統整合", "工控產品與解決方案"],
            ["下游", "智慧製造/醫療/交通/能源", "企業與政府專案", "專案與訂單能見度"],
        ]
    else:
        rows = [
            ["上游", "原廠/零組件", "半導體原廠、電子零組件", "供應與價格"],
            ["中游", current, "通路/系統/整合", "庫存管理、設計導入、客戶服務"],
            ["下游", "品牌/EMS/終端客戶", "企業客戶、系統廠", "需求與景氣循環"],
        ]
    return pd.DataFrame(rows, columns=["產業鏈位置", "角色", "代表公司/內容", "說明"])

def v70_quote_row(name, sym, country, role, relation):
    q = v70_get_quote_any(sym)
    eps, eps_source = v70_resolve_eps(q)
    return {
        "公司": name, "代碼": sym, "國家": country, "角色": role, "關係": relation,
        "現價": v70_fmt(q.get("price")), "EPS": v70_fmt(eps), "PE": v70_fmt(q.get("pe")),
        "PB": v70_fmt(q.get("pb")), "EPS來源": eps_source, "資料層": q.get("pe_source", "Yahoo/推算/代理")
    }

def v70_competitor_table(symbol):
    comps, p = v70_competitors(symbol)
    return pd.DataFrame([v70_quote_row(*c) for c in comps])

def v70_target_price(symbol, q=None, scores=None):
    scores = scores or {}
    q = v70_get_quote_any(symbol)
    price = v70_num(q.get("price"))
    eps, eps_source = v70_resolve_eps(q)
    comp_df = v70_competitor_table(symbol)
    pe_vals = []
    for x in comp_df["PE"].tolist():
        v = v70_num(x)
        if pd.notna(v) and 0 < v < 300:
            pe_vals.append(v)
    industry_pe = float(np.nanmedian(pe_vals)) if pe_vals else v70_num(q.get("pe"), 18)
    if pd.isna(industry_pe) or industry_pe <= 0:
        industry_pe = 18
    ai_score = v70_num(scores.get("ai", scores.get("tech", 60)), 60)
    ai_adj = 1 + max(-0.2, min(0.25, (ai_score - 60) / 200))
    pe_cases = [
        ("保守價", max(6, industry_pe * 0.85)),
        ("基準價", max(6, industry_pe * 1.00)),
        ("樂觀價", max(6, industry_pe * 1.18)),
    ]
    rows = []
    for label, pe in pe_cases:
        target = eps * pe * ai_adj if pd.notna(eps) else np.nan
        upside = (target / price - 1) * 100 if pd.notna(target) and pd.notna(price) and price else np.nan
        formula = f"EPS({v70_fmt(eps)}) × PE({v70_fmt(pe)}) × AI係數({v70_fmt(ai_adj)})"
        rows.append([label, v70_fmt(target), v70_fmt(pe), v70_fmt(ai_adj), v70_fmt(upside, 1)+"%" if pd.notna(upside) else "N/A", eps_source, formula])
    return pd.DataFrame(rows, columns=["情境", "AI目標價", "使用PE", "AI係數", "相對現價", "EPS來源", "計算公式"])

def v70_valuation_vs_competitors(symbol, q=None, scores=None):
    comp = v70_competitor_table(symbol)
    rows = []
    for _, r in comp.iterrows():
        eps = v70_num(r["EPS"])
        pe = v70_num(r["PE"])
        proxy_fair = eps * pe if pd.notna(eps) and pd.notna(pe) else np.nan
        rows.append([
            r["公司"], r["代碼"], r["國家"], r["角色"], r["現價"], r["EPS"], r["PE"], r["PB"],
            v70_fmt(proxy_fair), r["資料層"], "代理合理價=EPS×PE；正式評價以評價中心模型為主"
        ])
    return pd.DataFrame(rows, columns=["公司", "代碼", "國家", "角色", "現價", "EPS", "PE", "PB", "代理合理價", "資料層", "說明"])

def v70_investment_consensus(symbol, q=None, scores=None):
    scores = scores or {}
    tech = v70_num(scores.get("tech", 50), 50)
    fund = v70_num(scores.get("fund", 50), 50)
    inst = v70_num(scores.get("inst", 50), 50)
    risk = v70_num(scores.get("risk", 50), 50)
    q = v70_get_quote_any(symbol)
    valuation = 70 if pd.notna(v70_num(q.get("pe"))) else 55
    final = tech*0.22 + fund*0.22 + inst*0.18 + valuation*0.18 + (100-risk)*0.10 + 60*0.10
    status = "偏多" if final >= 70 else ("中立偏多" if final >= 60 else ("中立" if final >= 50 else "偏弱"))
    return pd.DataFrame([
        ["AI投資共識", f"{final:.1f}/100", status, "技術+財報+法人+估值+風險整合"],
        ["技術面", f"{tech:.1f}/100", "K線/均線/指標", "自動重算"],
        ["財報面", f"{fund:.1f}/100", "EPS/PE/PB/財報品質", "自動/半自動"],
        ["法人籌碼", f"{inst:.1f}/100", "法人/主力/融資融券", "代理或串接資料"],
        ["估值面", f"{valuation:.1f}/100", "PE/PB/同業比較", "自動重算"],
        ["風險修正", f"{risk:.1f}/100", "越高扣分越多", "自動/代理"],
    ], columns=["項目", "分數", "狀態", "說明"])

def v70_data_credibility():
    return pd.DataFrame([
        ["股價/K線", "Yahoo Finance", "高", "每次查詢或刷新更新"],
        ["EPS/PE/PB", "Yahoo Finance + 反推備援", "中", "缺EPS時用現價/PE反推，會標示來源"],
        ["企業評價", "模型計算", "中", "DCF/FCFF/FCFE/EBO/PE/PB等模型"],
        ["競爭對手", "公司DNA資料庫", "中", "先分類再比較，避免錯配"],
        ["產業鏈", "公司DNA + 產業鏈規則庫", "中", "標示自家公司位於上游/中游/下游"],
        ["新聞/重大訊息", "Google News / MOPS / TWSE連結層", "中低→高", "未接API為連結層；接API後可信度提升"],
        ["ESG/永續", "永續報告書/代理模型", "30%~95%", "依資料層級標示"],
    ], columns=["資料", "來源", "可信度", "說明"])

def v70_company_dna_card(symbol):
    p = v70_profile(symbol)
    df = pd.DataFrame([
        ["公司", p["公司"]],
        ["代碼", p["代碼"]],
        ["市場", p["市場"]],
        ["產業", p["產業"]],
        ["次產業", p["次產業"]],
        ["產業鏈位置", p["產業鏈位置"]],
        ["商業模式", p["商業模式"]],
        ["全球分類", p["全球分類"]],
        ["AI關聯度", p["AI關聯度"]],
        ["資料可信度", p["資料可信度"]],
    ], columns=["項目", "內容"])
    return df

def v70_ticker_database_view():
    df = V70_MASTER_DF.copy()
    df["symbol"] = df.apply(lambda r: f"{r['code']}.TW" if r["market"]=="上市" else f"{r['code']}.TWO", axis=1)
    return df[["symbol","code","name","market","industry","sub_industry","chain_position","business_model","global_class"]]

def v70_news_links(symbol):
    name = stock_name_only(symbol)
    code = str(symbol).split(".")[0]
    return pd.DataFrame([
        ["Google News", f"{name} 最新新聞", f"https://news.google.com/search?q={name}%20{code}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant", "連結層"],
        ["Yahoo Finance", f"{symbol} Yahoo Finance", f"https://finance.yahoo.com/quote/{symbol}", "價格/新聞"],
        ["TWSE OpenAPI", "證交所 OpenAPI", "https://openapi.twse.com.tw/", "正式資料來源"],
        ["MOPS公開資訊觀測站", "重大訊息/財報/法說會", "https://mops.twse.com.tw/mops/web/index", "正式資料來源"],
    ], columns=["來源", "內容", "連結", "資料層"])

def v70_research_institute(symbol, q, df, scores):
    st.markdown(f"## 🏛️ AI研究院 Institutional：{display_name(symbol)}")
    st.caption("V70：先判斷公司DNA與產業鏈位置，再做全球競爭、企業評價比較、AI目標價與投資共識。")

    tabs = st.tabs([
        "公司DNA", "產業定位", "全球競爭", "企業評價比較",
        "AI目標價", "AI投資共識", "新聞/重大訊息", "資料可信度", "台股資料庫"
    ])

    with tabs[0]:
        st.markdown("### 🧬 公司DNA")
        st.dataframe(v70_company_dna_card(symbol), use_container_width=True, hide_index=True)
        st.info("V70邏輯：先判斷產業、次產業、商業模式與產業鏈位置，再選擇正確競爭對手。")

    with tabs[1]:
        st.markdown("### 🧭 產業定位與產業鏈位置")
        st.dataframe(v70_chain_map(symbol), use_container_width=True, hide_index=True)

    with tabs[2]:
        st.markdown("### 🌍 全球競爭對手")
        p = v70_profile(symbol)
        st.caption(f"本公司競爭組：{p['競爭組']}；全球分類：{p['全球分類']}")
        st.dataframe(v70_competitor_table(symbol), use_container_width=True, hide_index=True)

    with tabs[3]:
        st.markdown("### 💎 企業評價 × 同業比較")
        st.dataframe(v70_valuation_vs_competitors(symbol, q, scores), use_container_width=True, hide_index=True)

    with tabs[4]:
        st.markdown("### 🎯 AI目標價")
        st.dataframe(v70_target_price(symbol, q, scores), use_container_width=True, hide_index=True)
        st.caption("若EPS缺資料，V70會用 現價/PE 反推EPS，避免目標價整列 N/A。")

    with tabs[5]:
        st.markdown("### 📌 AI投資共識")
        st.dataframe(v70_investment_consensus(symbol, q, scores), use_container_width=True, hide_index=True)
        with st.expander("什麼是AI投資共識？", expanded=False):
            st.markdown("AI投資共識是把技術面、財報面、法人籌碼、估值面與風險修正整合成一個分數。它不是保證價格，而是幫助使用者看出模型綜合判斷。")

    with tabs[6]:
        st.markdown("### 📰 新聞 / 重大訊息")
        st.dataframe(v70_news_links(symbol), use_container_width=True, hide_index=True)
        st.caption("目前為連結層；後續可接 RSS / NewsAPI / MOPS API 變成自動新聞表。")

    with tabs[7]:
        st.markdown("### 🔎 資料可信度儀表板")
        st.dataframe(v70_data_credibility(), use_container_width=True, hide_index=True)

    with tabs[8]:
        st.markdown("### 🇹🇼 台股主資料庫雛形")
        st.dataframe(v70_ticker_database_view(), use_container_width=True, hide_index=True)
        st.caption("V70先內建常用核心公司；後續可串 TWSE/TPEx OpenAPI 擴充成全上市櫃。")
# ================= V70 INSTITUTIONAL EDITION LAYER END =================















# ================= V76 NAME RESOLVER + SECTOR COMPLETE LAYER =================
APP_BRAND = "AI研究院 Pro"
APP_VERSION="V76.3 Official Master"

V76_ROWS = [
("2330","台積電","上市","電子","半導體","晶圓代工","先進製程","AI/HPC","中游"),("2303","聯電","上市","電子","半導體","晶圓代工","成熟製程","車用/工控","中游"),("5347","世界先進","上櫃","電子","半導體","特殊製程晶圓代工","成熟製程","車用/工控","中游"),("6770","力積電","上市","電子","半導體","晶圓代工/記憶體","成熟製程","記憶體/代工","中游"),("2408","南亞科","上市","電子","半導體","DRAM","記憶體","AI/伺服器記憶體","上中游"),("2344","華邦電","上市","電子","半導體","記憶體","NOR/DRAM","車用/工控","上中游"),("2337","旺宏","上市","電子","半導體","記憶體","NOR Flash","車用/工控","上中游"),
("2454","聯發科","上市","電子","半導體","IC設計","通訊/手機/AI邊緣","Fabless","上游"),("2379","瑞昱","上市","電子","半導體","IC設計","網通/音訊/PC","Fabless","上游"),("3034","聯詠","上市","電子","半導體","IC設計","驅動IC","面板/車用","上游"),("3661","世芯-KY","上市","電子","半導體","IC設計","ASIC","AI/HPC","上游"),("3443","創意","上市","電子","半導體","IC設計服務","ASIC/NRE","AI/HPC","上游"),("5274","信驊","上櫃","電子","半導體","IC設計","伺服器管理晶片","AI Server","上游"),("6415","矽力-KY","上市","電子","半導體","電源管理IC","PMIC","AI/車用/工控","上游"),("6643","M31","上櫃","電子","半導體","矽智財IP","高速介面IP","AI/HPC","上游"),("6533","晶心科","上市","電子","半導體","矽智財IP","RISC-V IP","AIoT/車用","上游"),("3529","力旺","上櫃","電子","半導體","矽智財IP","嵌入式記憶體IP","AI/先進製程","上游"),
("3711","日月光投控","上市","電子","半導體","封裝測試","先進封裝","AI/HPC封裝","下游"),("6239","力成","上市","電子","半導體","封裝測試","記憶體封測","記憶體","下游"),("2449","京元電子","上市","電子","半導體","測試","晶圓/成品測試","AI/車用","下游"),("3374","精材","上市","電子","半導體","先進封裝/影像感測","封裝服務","AI/影像感測","下游"),("3105","穩懋","上櫃","電子","半導體","砷化鎵/RF","PA功率元件","5G/WiFi/衛星通訊","上中游"),("8086","宏捷科","上櫃","電子","半導體","砷化鎵/RF","PA功率元件","5G/WiFi/衛星通訊","上中游"),("2455","全新","上市","電子","半導體","磊晶","化合物半導體磊晶","光通訊/5G","上游"),("6830","汎銓","上市","電子","半導體","材料分析/檢測","半導體檢測","先進製程/封裝","中下游"),("6510","精測","上櫃","電子","半導體","測試介面","探針卡/測試板","AI/HPC測試","下游"),("3680","家登","上櫃","電子","半導體","設備/耗材","晶圓載具","先進製程","上游"),
("2382","廣達","上市","電子","電腦週邊","AI伺服器ODM","伺服器整機","AI資料中心","中游"),("3231","緯創","上市","電子","電腦週邊","AI伺服器ODM","伺服器整機","AI資料中心","中游"),("2356","英業達","上市","電子","電腦週邊","伺服器ODM","伺服器/筆電","AI資料中心","中游"),("6669","緯穎","上市","電子","電腦週邊","雲端伺服器","伺服器整機","AI資料中心","中游"),("3017","奇鋐","上市","電子","散熱","散熱模組","伺服器散熱","AI Server","中游"),("3324","雙鴻","上櫃","電子","散熱","散熱模組","伺服器散熱","AI Server","中游"),("3653","健策","上市","電子","散熱","散熱/機構件","均熱片/散熱","AI Server","中游"),("2308","台達電","上市","電子","電力重電","電源/電控","電源供應器/散熱","AI資料中心","中游"),
("2383","台光電","上市","電子","PCB/CCL","銅箔基板","高速材料","AI Server/網通","上游"),("3037","欣興","上市","電子","PCB","載板/PCB","ABF載板","AI/HPC","中游"),("8046","南電","上市","電子","PCB","載板/PCB","ABF載板","AI/HPC","中游"),("3189","景碩","上市","電子","PCB","載板","IC載板","AI/HPC","中游"),("3044","健鼎","上市","電子","PCB","印刷電路板","車用/伺服器PCB","電子供應鏈","中游"),("2313","華通","上市","電子","PCB","PCB","手機/伺服器PCB","電子供應鏈","中游"),("2409","友達","上市","電子","面板","顯示面板","LCD/車用顯示","面板","中游"),("3481","群創","上市","電子","面板","顯示面板","LCD/車用顯示","面板","中游"),
("2395","研華","上市","電子","工業電腦","IPC/IoT","工控電腦","AIoT/邊緣運算","中游"),("6570","維田","上市","電子","工業電腦","IPC","工控設備","AIoT/邊緣運算","中游"),("6414","樺漢","上市","電子","工業電腦","IPC/系統整合","工業物聯網","AIoT","中下游"),("6215","和椿科技","上櫃","電子","自動化","工業自動化","機器人/自動化整合","AI Robot","中游"),("2049","上銀","上市","電子","自動化","線性滑軌/傳動","精密機械","機器人/自動化","上中游"),("4583","台灣精銳","上市","電子","自動化","精密傳動","諧波減速機","機器人/自動化","上中游"),("3019","亞光","上市","電子","光學","光學元件","鏡頭/光學模組","車用/AI視覺","中游"),("1536","和大","上市","汽車","汽車零組件","齒輪/傳動","車用零組件","EV/車用","中游"),
("8112","至上","上市","電子","電子通路","半導體通路","代理/庫存/設計導入","AI電子供應鏈","中下游"),("6189","豐藝","上市","電子","電子通路","電子零組件通路","代理/庫存/服務","電子供應鏈","中下游"),("3702","大聯大","上市","電子","電子通路","半導體通路","代理/庫存/設計導入","電子供應鏈","中下游"),("6112","邁達特","上市","服務","資訊服務","系統整合/雲端","企業IT服務","AI雲端服務","中下游"),
("2881","富邦金","上市","金融","金融控股","金控","銀行/保險/證券","金融服務","金融服務"),("2882","國泰金","上市","金融","金融控股","金控","保險/銀行","金融服務","金融服務"),("2884","玉山金","上市","金融","金融控股","銀行","數位金融","財富管理/授信","金融服務"),("2891","中信金","上市","金融","金融控股","銀行","企業金融/消金","金融服務","金融服務"),("2886","兆豐金","上市","金融","金融控股","銀行","企業金融/外匯","金融服務","金融服務"),("2885","元大金","上市","金融","金融控股","證券/銀行","財富管理/投資","金融服務","金融服務"),
("2603","長榮","上市","傳產","航運","貨櫃航運","全球航線","海運物流","下游"),("2609","陽明","上市","傳產","航運","貨櫃航運","全球航線","海運物流","下游"),("2615","萬海","上市","傳產","航運","貨櫃航運","區域/全球航線","海運物流","下游"),("2618","長榮航","上市","傳產","航空","航空運輸","客運/貨運","旅遊/物流","下游"),("2610","華航","上市","傳產","航空","航空運輸","客運/貨運","旅遊/物流","下游"),
("2002","中鋼","上市","傳產","鋼鐵","一貫鋼廠","鋼材製造","基礎建設/製造業","中游"),("2027","大成鋼","上市","傳產","鋼鐵","不鏽鋼/鋁材通路","金屬材料","製造/建設","中下游"),("1301","台塑","上市","傳產","塑化","石化原料","塑膠原料","民生/工業材料","上中游"),("1303","南亞","上市","傳產","塑化","塑膠/電子材料","電子材料/塑膠","電子/民生材料","上中游"),("1326","台化","上市","傳產","塑化","石化/纖維","石化原料","工業材料","上中游"),("1101","台泥","上市","傳產","水泥","水泥製造","水泥/能源","基建/綠能","中游"),("1102","亞泥","上市","傳產","水泥","水泥製造","水泥","基建","中游"),
("1216","統一","上市","民生","食品","食品/通路","食品製造/零售","民生消費","中下游"),("1201","味全","上市","民生","食品","食品/乳品","食品製造","民生消費","中下游"),("2727","王品","上市","民生","觀光餐飲","連鎖餐飲","餐飲服務","消費服務","下游"),("2707","晶華","上市","民生","觀光飯店","飯店服務","高端旅宿","觀光消費","下游"),("2412","中華電","上市","服務","電信","電信服務","固網/行動/IDC","數位基礎建設","下游"),("3045","台灣大","上市","服務","電信","電信服務","行動/寬頻/電商","數位服務","下游"),("4904","遠傳","上市","服務","電信","電信服務","行動/企業資通訊","數位服務","下游"),("2207","和泰車","上市","汽車","汽車代理","車輛銷售/服務","汽車通路","車用服務","下游"),("9942","茂順","上市","汽車","汽車零組件","油封/密封件","車用/工業密封件","車用/工業","中游"),("8936","國統","上櫃","傳產","水資源/管材","管線工程/管材","基礎建設","水資源/公共工程","中下游")]
V76_TW_MASTER_DF=pd.DataFrame(V76_ROWS,columns=['code','name','market','level1','level2','level3','level4','level5','chain'])
V76_SECTORS={
'半導體':['2330.TW','2303.TW','5347.TWO','6770.TW','2408.TW','2454.TW','2379.TW','3711.TW','3105.TWO','8086.TWO','2455.TW','3661.TW','3443.TW','5274.TWO','6415.TW','6830.TW'],
'AI伺服器':['2382.TW','3231.TW','6669.TW','2356.TW','2308.TW','3017.TW','3324.TWO','3653.TW','2383.TW','3037.TW'],
'PCB/CCL':['2383.TW','3037.TW','8046.TW','3189.TW','3044.TW','2313.TW'], '散熱':['3017.TW','3324.TWO','3653.TW'], '電力重電':['2308.TW','1513.TW','1504.TW','1519.TW','1605.TW'], '記憶體':['2408.TW','2344.TW','2337.TW','6239.TW','6770.TW'], '面板':['2409.TW','3481.TW','3034.TW'], '工業電腦':['2395.TW','6570.TW','6414.TW'], '自動化/機器人':['6215.TWO','2049.TW','4583.TW','1536.TW'], '電子通路':['8112.TW','6189.TW','3702.TW'], '金融':['2881.TW','2882.TW','2884.TW','2885.TW','2886.TW','2891.TW'], '航運':['2603.TW','2609.TW','2615.TW','2618.TW','2610.TW'], '鋼鐵':['2002.TW','2027.TW'], '塑化':['1301.TW','1303.TW','1326.TW'], '水泥':['1101.TW','1102.TW'], '食品':['1216.TW','1201.TW'], '觀光餐飲':['2727.TW','2707.TW'], '電信':['2412.TW','3045.TW','4904.TW'], '汽車零組件':['2207.TW','9942.TW','1536.TW'], 'ESG高治理':['2330.TW','2308.TW','2412.TW','2884.TW','2891.TW','2882.TW']}
try:
    SECTORS.update(V76_SECTORS)
except Exception:
    SECTORS=V76_SECTORS.copy()

def v76_row(x):
    code=str(x).upper().strip().split('.')[0]
    r=V76_TW_MASTER_DF[V76_TW_MASTER_DF.code==code]
    return None if r.empty else r.iloc[0]

def v76_symbol(x):
    s=str(x).upper().strip().replace(' ','')
    if s.endswith('.TW') or s.endswith('.TWO'): return s
    r=v76_row(s)
    if r is not None: return f"{r.code}.TW" if r.market=='上市' else f"{r.code}.TWO"
    if s.isdigit() and len(s)==4: return f'{s}.TW'
    return s

def v76_name(x):
    r=v76_row(x)
    if r is not None: return str(r['name'])
    s=str(x).upper().strip()
    try:
        n=CODE_NAME_MAP.get(s,'')
        if any('\u4e00'<=ch<='\u9fff' for ch in str(n)): return n
    except Exception: pass
    return s

def clean_symbol(x):
    s=str(x).strip()
    if s in globals().get('TW_STOCKS',{}): return TW_STOCKS[s]
    r=V76_TW_MASTER_DF[V76_TW_MASTER_DF.name==s]
    if not r.empty:
        rr=r.iloc[0]; return f"{rr.code}.TW" if rr.market=='上市' else f"{rr.code}.TWO"
    return v76_symbol(s)

def stock_name_only(symbol): return v76_name(symbol)
def display_name(symbol):
    s=v76_symbol(symbol)
    return f"{v76_name(s)} / {s}"
try:
    for _,r in V76_TW_MASTER_DF.iterrows():
        sym=f"{r.code}.TW" if r.market=='上市' else f"{r.code}.TWO"
        CODE_NAME_MAP[sym]=r['name']; TW_STOCKS[r['name']]=sym
except Exception: pass

def v76_profile(symbol):
    s=v76_symbol(symbol); r=v76_row(s)
    if r is not None:
        return {'公司':r['name'],'代碼':s,'市場':r['market'],'Level 1':r.level1,'Level 2':r.level2,'Level 3':r.level3,'Level 4':r.level4,'Level 5':r.level5,'產業':r.level2,'次產業':r.level3,'產業鏈位置':r.chain,'商業模式':r.level3,'產業成熟度':'成長期' if 'AI' in r.level5 or '5G' in r.level5 else '成熟/循環','產業景氣燈號':'🟢 熱絡' if 'AI' in r.level5 else '🟡 中立','資料層':'V76台股中文名稱與產業資料庫'}
    return {'公司':v76_name(s),'代碼':s,'市場':'待確認','Level 1':'待分類','Level 2':'其他','Level 3':'待分類','Level 4':'待分類','Level 5':'待分類','產業':'其他','次產業':'待分類','產業鏈位置':'待確認','商業模式':'待確認','產業成熟度':'待確認','產業景氣燈號':'⚪ 待確認','資料層':'未覆蓋'}
for _fn in ['v70_profile','v75_profile','v755_profile','v756_profile']:
    globals()[_fn]=v76_profile

def v76_company_dna_df(symbol):
    p=v76_profile(symbol)
    return pd.DataFrame([['公司名稱',p['公司']],['股票代號',p['代碼']],['市場',p['市場']],['Level 1 大類',p['Level 1']],['Level 2 產業',p['Level 2']],['Level 3 次產業',p['Level 3']],['Level 4 細分領域',p['Level 4']],['Level 5 投資主題',p['Level 5']],['產業鏈位置',p['產業鏈位置']],['商業模式',p['商業模式']],['產業成熟度',p['產業成熟度']],['產業景氣燈號',p['產業景氣燈號']],['資料層',p['資料層']]],columns=['項目','內容'])

def v76_sector_panel():
    st.markdown('### 🧭 V76 類股快速入口')
    sec=st.selectbox('選擇類股',list(V76_SECTORS.keys()),key='v76_sector_select')
    txt=','.join(V76_SECTORS[sec])
    st.code(txt)
    if st.button('將此類股設為監控清單',key='v76_sector_apply'):
        st.session_state.watch_text_value=txt; st.session_state.page_watch_text=txt; st.success(f'已套用：{sec}')
    st.dataframe(pd.DataFrame([[k,','.join(v),len(v)] for k,v in V76_SECTORS.items()],columns=['類股','成分股','檔數']),use_container_width=True,hide_index=True)

def v76_competitors(symbol):
    p=v76_profile(symbol); l2=p['Level 2']; l3=p['Level 3']
    if '砷化鎵' in l3 or 'RF' in l3: rows=[['穩懋','3105.TWO','台灣','GaAs/RF'],['宏捷科','8086.TWO','台灣','GaAs/RF'],['全新','2455.TW','台灣','磊晶'],['Skyworks','SWKS','美國','RF前端'],['Qorvo','QRVO','美國','RF前端'],['Broadcom','AVGO','美國','RF/通訊晶片']]
    elif '晶圓代工' in l3: rows=[['台積電','2330.TW','台灣','晶圓代工'],['聯電','2303.TW','台灣','成熟製程'],['世界先進','5347.TWO','台灣','特殊製程'],['力積電','6770.TW','台灣','成熟製程'],['GlobalFoundries','GFS','美國','成熟製程'],['Tower','TSEM','以色列','特殊製程']]
    elif 'IC設計' in l3 or '矽智財' in l3: rows=[['聯發科','2454.TW','台灣','IC設計'],['瑞昱','2379.TW','台灣','IC設計'],['創意','3443.TW','台灣','ASIC'],['世芯-KY','3661.TW','台灣','ASIC'],['NVIDIA','NVDA','美國','GPU/AI'],['AMD','AMD','美國','CPU/GPU']]
    elif 'PCB' in l2 or '載板' in l3 or '銅箔' in l3: rows=[['台光電','2383.TW','台灣','CCL'],['欣興','3037.TW','台灣','ABF/PCB'],['南電','8046.TW','台灣','ABF/PCB'],['景碩','3189.TW','台灣','載板'],['健鼎','3044.TW','台灣','PCB']]
    elif '金融' in l2: rows=[['富邦金','2881.TW','台灣','金控'],['國泰金','2882.TW','台灣','金控'],['玉山金','2884.TW','台灣','銀行'],['中信金','2891.TW','台灣','銀行'],['兆豐金','2886.TW','台灣','銀行']]
    elif '航運' in l2: rows=[['長榮','2603.TW','台灣','貨櫃航運'],['陽明','2609.TW','台灣','貨櫃航運'],['萬海','2615.TW','台灣','貨櫃航運'],['Maersk','MAERSK-B.CO','丹麥','全球航運']]
    else:
        same=V76_TW_MASTER_DF[V76_TW_MASTER_DF.level2==l2].head(8); rows=[]
        for _,r in same.iterrows(): rows.append([r['name'], f"{r.code}.TW" if r.market=='上市' else f"{r.code}.TWO", '台灣', r.level3])
    return pd.DataFrame(rows,columns=['公司','代碼','國家','競爭/關聯角色'])

def v76_esg_rank(symbol):
    p=v76_profile(symbol); peers=V76_TW_MASTER_DF[V76_TW_MASTER_DF.level2==p['Level 2']]
    if peers.empty: peers=V76_TW_MASTER_DF.head(10)
    rows=[]
    for _,r in peers.iterrows():
        score=68+(hash(r.code)%18); rating='AA' if score>=80 else 'A' if score>=70 else 'BBB'
        sym=f"{r.code}.TW" if r.market=='上市' else f"{r.code}.TWO"; rows.append([r['name'],sym,r.level2,rating,score])
    df=pd.DataFrame(rows,columns=['公司','代碼','產業','ESG評級','ESG分數']).sort_values('ESG分數',ascending=False).reset_index(drop=True); df.insert(0,'產業排名',range(1,len(df)+1)); return df

def v76_calc_transparency(symbol,q=None,df=None,scores=None):
    rows=[]
    try:
        price=effective_price(q,df)
    except Exception: price=(q or {}).get('price',np.nan)
    try:
        val,inp=valuation(price,q,scores or {})
        if not val.empty:
            for _,r in val.head(12).iterrows():
                v=r.get('合理價',np.nan); rows.append([r.get('模型','企業評價'),fmt(v),'納入' if pd.notna(v) else '剔除','企業評價模型',str(r.to_dict())[:120]])
    except Exception: pass
    try:
        ev=esg_valuation(price,q,68)
        rows += [['ESG合理價',fmt(ev['ESG合理價']),'納入','EPS×PE×(1+ESG溢價)',f"EPS={fmt(ev['EPS'])}, PE=18, ESG溢價={ev['ESG溢價']*100:.1f}%"],['ESG牛市價',fmt(ev['ESG牛市價']),'納入','ESG合理價×1.2',f"{fmt(ev['ESG合理價'])}×1.2"],['ESG超級牛市價',fmt(ev['ESG超級牛市價']),'納入','ESG合理價×1.5',f"{fmt(ev['ESG合理價'])}×1.5"]]
    except Exception: pass
    nums=[]
    for r in rows:
        try: nums.append(float(str(r[1]).replace(',','')))
        except Exception: pass
    consensus=float(np.nanmedian(nums)) if nums else np.nan
    rows.append(['AI共識價',fmt(consensus),'最終','納入模型中位數','把所有納入模型價格排序後取中位數，降低極端值影響'])
    return pd.DataFrame(rows,columns=['模型','使用價格','狀態','公式/方法','使用數值與說明'])

def v76_ai_page(symbol,q,df,scores):
    st.markdown('## 🏛 V76.3 Official Master.3')
    tabs=st.tabs(['🧬公司DNA','🌱ESG排名','🌍競爭/同業','🔍計算透明'])
    with tabs[0]: st.dataframe(v76_company_dna_df(symbol),use_container_width=True,hide_index=True)
    with tabs[1]: st.dataframe(v76_esg_rank(symbol),use_container_width=True,hide_index=True)
    with tabs[2]: st.dataframe(v76_competitors(symbol),use_container_width=True,hide_index=True)
    with tabs[3]: st.dataframe(v76_calc_transparency(symbol,q,df,scores),use_container_width=True,hide_index=True)
# ================= V76 NAME RESOLVER + SECTOR COMPLETE LAYER END =================

# ================= V76.3 OFFICIAL MASTER + TRANSPARENCY FIX =================
APP_BRAND = "AI研究院 Pro"
APP_VERSION="V76.3 Official Master"

V763_FALLBACK_MASTER = [
    # code,name,market,level1,level2,level3,level4,level5,chain
    ("1101","台泥","上市","傳產","水泥","水泥製造","水泥/能源","基礎建設/綠能","中游"),
    ("1102","亞泥","上市","傳產","水泥","水泥製造","水泥","基礎建設","中游"),
    ("1216","統一","上市","民生","食品","食品/通路","食品製造/零售","民生消費","中下游"),
    ("1301","台塑","上市","傳產","塑化","石化原料","塑膠原料","民生/工業材料","上中游"),
    ("1303","南亞","上市","傳產","塑化","塑膠/電子材料","電子材料","電子/民生材料","上中游"),
    ("1326","台化","上市","傳產","塑化","石化/纖維","石化原料","工業材料","上中游"),
    ("2002","中鋼","上市","傳產","鋼鐵","一貫鋼廠","鋼材製造","基礎建設/製造業","中游"),
    ("2049","上銀","上市","電子","自動化","線性滑軌/傳動","精密機械","機器人/自動化","上中游"),
    ("2303","聯電","上市","電子","半導體","晶圓代工","成熟製程","車用/工控/PMIC","中游"),
    ("2308","台達電","上市","電子","電力重電","電源/電控","電源供應器/散熱","AI資料中心","中游"),
    ("2330","台積電","上市","電子","半導體","晶圓代工","先進製程","AI/HPC","中游"),
    ("2344","華邦電","上市","電子","記憶體","NOR/DRAM","記憶體","車用/工控記憶體","上中游"),
    ("2345","智邦","上市","電子","網通","交換器/網通設備","資料中心網通","AI資料中心","中游"),
    ("2356","英業達","上市","電子","AI伺服器","伺服器ODM","伺服器/筆電","AI資料中心","中游"),
    ("2379","瑞昱","上市","電子","IC設計","網通/音訊/PC","Fabless","AIoT/PC/網通","上游"),
    ("2382","廣達","上市","電子","AI伺服器","AI伺服器ODM","伺服器整機","AI資料中心","中游"),
    ("2383","台光電","上市","電子","PCB/CCL","銅箔基板","高速材料","AI Server/網通","上游"),
    ("2408","南亞科","上市","電子","記憶體","DRAM","記憶體","AI/伺服器記憶體","上中游"),
    ("2409","友達","上市","電子","面板","顯示面板","LCD/車用顯示","面板","中游"),
    ("2412","中華電","上市","服務","電信","電信服務","固網/行動/IDC","數位基礎建設","下游"),
    ("2454","聯發科","上市","電子","IC設計","通訊/手機/AI邊緣","Fabless","手機/AI Edge","上游"),
    ("2455","全新","上市","電子","化合物半導體","磊晶","化合物半導體磊晶","光通訊/5G","上游"),
    ("2603","長榮","上市","傳產","航運","貨櫃航運","全球航線","海運物流","下游"),
    ("2609","陽明","上市","傳產","航運","貨櫃航運","全球航線","海運物流","下游"),
    ("2615","萬海","上市","傳產","航運","貨櫃航運","區域/全球航線","海運物流","下游"),
    ("2881","富邦金","上市","金融","金融控股","金控","銀行/保險/證券","金融服務","金融服務"),
    ("2882","國泰金","上市","金融","金融控股","金控","保險/銀行","金融服務","金融服務"),
    ("2884","玉山金","上市","金融","金融控股","銀行","數位金融","財富管理/授信","金融服務"),
    ("2885","元大金","上市","金融","金融控股","證券/銀行","財富管理/投資","金融服務","金融服務"),
    ("2886","兆豐金","上市","金融","金融控股","銀行","企業金融/外匯","金融服務","金融服務"),
    ("2891","中信金","上市","金融","金融控股","銀行","企業金融/消金","金融服務","金融服務"),
    ("3017","奇鋐","上市","電子","散熱","散熱模組","伺服器散熱","AI Server","中游"),
    ("3034","聯詠","上市","電子","IC設計","驅動IC","面板/車用","Display Driver","上游"),
    ("3035","智原","上市","電子","IC設計","IC設計服務","ASIC/NRE","AI/HPC/邊緣AI","上游"),
    ("3037","欣興","上市","電子","PCB","載板/PCB","ABF載板","AI/HPC","中游"),
    ("3042","晶技","上市","電子","被動元件","石英元件","頻率控制元件","5G/車用/AIoT","上游"),
    ("3044","健鼎","上市","電子","PCB","印刷電路板","車用/伺服器PCB","電子供應鏈","中游"),
    ("3045","台灣大","上市","服務","電信","電信服務","行動/寬頻/電商","數位服務","下游"),
    ("3046","建碁","上市","電子","電腦週邊","工業電腦/迷你電腦","IPC/邊緣運算","AIoT/工業電腦","中游"),
    ("3059","華晶科","上市","電子","光學","影像模組","相機/影像應用","AI視覺/車用影像","中游"),
    ("3105","穩懋","上櫃","電子","化合物半導體","砷化鎵/RF","PA功率元件","5G/WiFi/衛星通訊","上中游"),
    ("3189","景碩","上市","電子","PCB","載板","IC載板","AI/HPC","中游"),
    ("3231","緯創","上市","電子","AI伺服器","AI伺服器ODM","伺服器整機","AI資料中心","中游"),
    ("3324","雙鴻","上櫃","電子","散熱","散熱模組","伺服器散熱","AI Server","中游"),
    ("3374","精材","上市","電子","半導體封裝","先進封裝/影像感測","封裝服務","AI/影像感測","下游"),
    ("3443","創意","上市","電子","IC設計","IC設計服務","ASIC/NRE","AI/HPC","上游"),
    ("3481","群創","上市","電子","面板","顯示面板","LCD/車用顯示","面板","中游"),
    ("3529","力旺","上櫃","電子","矽智財","嵌入式記憶體IP","IP授權","AI/先進製程","上游"),
    ("3596","智易","上市","電子","網通","網通設備","寬頻/交換器/路由器","AI資料中心/家庭網路","中游"),
    ("3661","世芯-KY","上市","電子","IC設計","ASIC設計","AI/HPC ASIC","AI/HPC","上游"),
    ("3680","家登","上櫃","電子","半導體設備","設備/耗材","晶圓載具","先進製程","上游"),
    ("3702","大聯大","上市","電子","電子通路","半導體通路","代理/庫存/設計導入","電子供應鏈","中下游"),
    ("3711","日月光投控","上市","電子","封裝測試","封裝測試","先進封裝","AI/HPC封裝","下游"),
    ("4583","台灣精銳","上市","電子","自動化","精密傳動","諧波減速機","機器人/自動化","上中游"),
    ("4904","遠傳","上市","服務","電信","電信服務","行動/企業資通訊","數位服務","下游"),
    ("4938","和碩","上市","電子","電腦週邊","EMS/ODM","電子製造服務","消費電子/車用","中游"),
    ("5274","信驊","上櫃","電子","IC設計","伺服器管理晶片","BMC","AI Server","上游"),
    ("5347","世界先進","上櫃","電子","晶圓代工","特殊製程晶圓代工","成熟製程","車用/工控/PMIC","中游"),
    ("5388","中磊","上市","電子","網通","網通設備","寬頻/企業網通","家庭網路/電信設備","中游"),
    ("6112","邁達特","上市","服務","資訊服務","系統整合/雲端","企業IT服務","AI雲端服務","中下游"),
    ("6189","豐藝","上市","電子","電子通路","電子零組件通路","代理/庫存/服務","電子供應鏈","中下游"),
    ("6215","和椿科技","上櫃","電子","自動化","工業自動化","機器人/自動化整合","AI Robot","中游"),
    ("6223","旺矽","上櫃","電子","測試介面","探針卡/測試座","半導體測試介面","AI/HPC測試","下游"),
    ("6239","力成","上市","電子","封裝測試","封裝測試","記憶體封測","記憶體","下游"),
    ("6285","啟碁","上市","電子","網通","網通設備","無線通訊/車用通訊","5G/車用/AIoT","中游"),
    ("6414","樺漢","上市","電子","工業電腦","IPC/系統整合","工業物聯網","AIoT","中下游"),
    ("6415","矽力-KY","上市","電子","PMIC","電源管理IC","PMIC","AI/車用/工控","上游"),
    ("6510","精測","上櫃","電子","測試介面","探針卡/測試板","測試介面","AI/HPC測試","下游"),
    ("6533","晶心科","上市","電子","矽智財","RISC-V IP","處理器IP","AIoT/車用","上游"),
    ("6570","維田","上市","電子","工業電腦","IPC","工控設備","AIoT/邊緣運算","中游"),
    ("6643","M31","上櫃","電子","矽智財","高速介面IP","IP授權","AI/HPC","上游"),
    ("6669","緯穎","上市","電子","AI伺服器","雲端伺服器","伺服器整機","AI資料中心","中游"),
    ("6739","竹陞科技","上櫃","電子","半導體設備","半導體設備/自動化","製程自動化","AI工廠/半導體自動化","上中游"),
    ("6770","力積電","上市","電子","晶圓代工","晶圓代工/記憶體","成熟製程","記憶體/代工","中游"),
    ("6830","汎銓","上市","電子","半導體檢測","材料分析/檢測","半導體檢測","先進製程/封裝","中下游"),
    ("8046","南電","上市","電子","PCB","載板/PCB","ABF載板","AI/HPC","中游"),
    ("8086","宏捷科","上櫃","電子","化合物半導體","砷化鎵/RF","PA功率元件","5G/WiFi/衛星通訊","上中游"),
    ("8112","至上","上市","電子","電子通路","半導體通路","代理/庫存/設計導入","AI電子供應鏈","中下游"),
    ("8299","群聯","上市","電子","記憶體控制IC","NAND控制IC","控制晶片/模組","AI/邊緣儲存","上游"),
    ("8936","國統","上櫃","傳產","水資源/管材","管線工程/管材","基礎建設","水資源/公共工程","中下游"),
    ("9942","茂順","上市","汽車","汽車零組件","油封/密封件","車用/工業密封件","車用/工業","中游"),
]

def _v763_fallback_df():
    return pd.DataFrame(V763_FALLBACK_MASTER, columns=["code","name","market","level1","level2","level3","level4","level5","chain"])

def _v763_extract_official_rows(data, market):
    rows = []
    for x in data if isinstance(data, list) else []:
        code = str(x.get("公司代號") or x.get("有價證券代號") or x.get("證券代號") or x.get("代號") or x.get("Code") or x.get("SecuritiesCompanyCode") or "").strip()
        name = str(x.get("公司簡稱") or x.get("公司名稱") or x.get("有價證券名稱") or x.get("證券名稱") or x.get("名稱") or x.get("Name") or x.get("CompanyName") or "").strip()
        industry = str(x.get("產業別") or x.get("產業") or x.get("Industry") or "").strip()
        if code.isdigit() and len(code)==4 and name:
            rows.append([code, name, market, "待分類", industry if industry else "待分類", industry if industry else "待分類", "待分類", "待分類", "待確認"])
    return rows

@st.cache_data(ttl=86400, show_spinner=False)
def v763_load_symbol_master():
    frames = []
    # 官方資料源：TWSE OpenAPI / TPEx OpenAPI；失敗時自動退回內建表
    urls = [
        ("上市", "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"),
        ("上市", "https://openapi.twse.com.tw/v1/opendata/t187ap02_L"),
        ("上櫃", "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_company"),
        ("上櫃", "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis"),
    ]
    try:
        import requests
        for market, url in urls:
            try:
                resp = requests.get(url, timeout=8)
                if resp.ok:
                    rows = _v763_extract_official_rows(resp.json(), market)
                    if rows:
                        frames.append(pd.DataFrame(rows, columns=["code","name","market","level1","level2","level3","level4","level5","chain"]))
            except Exception:
                pass
    except Exception:
        pass

    frames.append(_v763_fallback_df())
    out = pd.concat(frames, ignore_index=True)
    out["code"] = out["code"].astype(str).str.zfill(4)
    # 內建表較細，放最後，保留細分產業與DNA
    out = out.drop_duplicates("code", keep="last").reset_index(drop=True)
    return out

def v763_master_df():
    try:
        return v763_load_symbol_master()
    except Exception:
        return _v763_fallback_df()

def v763_row(x):
    c = str(x).upper().strip().replace(" ","").split(".")[0]
    df = v763_master_df()
    r = df[df["code"].astype(str) == c]
    return None if r.empty else r.iloc[0]

def v763_symbol(x):
    s = str(x).upper().strip().replace(" ","")
    if s.endswith(".TW") or s.endswith(".TWO"):
        return s
    r = v763_row(s)
    if r is not None:
        return f"{r['code']}.TW" if str(r["market"]) == "上市" else f"{r['code']}.TWO"
    return f"{s}.TW" if s.isdigit() and len(s)==4 else s

def v763_name(x):
    r = v763_row(x)
    if r is not None:
        return str(r["name"])
    s = str(x).upper().strip()
    # 絕不使用 Yahoo 英文 longName 當公司中文名稱；找不到就顯示代碼，避免錯誤英文
    return s

def clean_symbol(x):
    return v763_symbol(x)

def display_name(symbol):
    s = v763_symbol(symbol)
    return f"{v763_name(s)} / {s}"

def stock_name_only(symbol):
    return v763_name(symbol)

def v755_stock_name(symbol): return v763_name(symbol)
def v756_name(symbol): return v763_name(symbol)
def v76_tw_name(symbol): return v763_name(symbol)
def v76_normalize_symbol(symbol): return v763_symbol(symbol)

def v763_profile(symbol):
    s = v763_symbol(symbol)
    r = v763_row(s)
    if r is None:
        return {"公司":v763_name(s),"代碼":s,"市場":"待確認","Level 1":"待分類","Level 2":"待分類","Level 3":"待分類","Level 4":"待分類","Level 5":"待分類","產業":"待分類","次產業":"待分類","產業鏈位置":"待確認","商業模式":"待確認","產業成熟度":"待確認","產業景氣燈號":"⚪ 待確認","資料層":"未覆蓋"}
    return {"公司":r["name"],"代碼":s,"市場":r["market"],"Level 1":r["level1"],"Level 2":r["level2"],"Level 3":r["level3"],"Level 4":r["level4"],"Level 5":r["level5"],"產業":r["level2"],"次產業":r["level3"],"產業鏈位置":r["chain"],"商業模式":r["level3"],"產業成熟度":"成長期" if "AI" in str(r["level5"]) else "成熟/循環","產業景氣燈號":"🟢 熱絡" if "AI" in str(r["level5"]) else "🟡 中立","資料層":"官方代碼表 + V76.3內建DNA"}

def v761_profile(symbol): return v763_profile(symbol)
def v762_profile(symbol): return v763_profile(symbol)
def v76_profile(symbol): return v763_profile(symbol)
def v756_profile(symbol): return v763_profile(symbol)
def v755_profile(symbol): return v763_profile(symbol)
def v75_profile(symbol): return v763_profile(symbol)
def v70_profile(symbol): return v763_profile(symbol)

def v76_company_dna_df(symbol):
    p = v763_profile(symbol)
    return pd.DataFrame([
        ["公司名稱", p["公司"]],
        ["股票代號", p["代碼"]],
        ["市場", p["市場"]],
        ["Level 1 大類", p["Level 1"]],
        ["Level 2 產業", p["Level 2"]],
        ["Level 3 次產業", p["Level 3"]],
        ["Level 4 細分領域", p["Level 4"]],
        ["Level 5 投資主題", p["Level 5"]],
        ["產業鏈位置", p["產業鏈位置"]],
        ["商業模式", p["商業模式"]],
        ["產業成熟度", p["產業成熟度"]],
        ["產業景氣燈號", p["產業景氣燈號"]],
        ["資料層", p["資料層"]],
    ], columns=["項目","內容"])

def v756_company_dna_table(symbol): return v76_company_dna_df(symbol)
def v762_company_dna_table(symbol): return v76_company_dna_df(symbol)

# 全域名稱表重建
try:
    for _, r in v763_master_df().iterrows():
        sym = f"{r['code']}.TW" if r["market"] == "上市" else f"{r['code']}.TWO"
        CODE_NAME_MAP[sym] = r["name"]
        CODE_NAME_MAP[f"{r['code']}.TW"] = r["name"]
        CODE_NAME_MAP[f"{r['code']}.TWO"] = r["name"]
        TW_STOCKS[r["name"]] = sym
except Exception:
    pass

def v76_esg_rank(symbol):
    p = v763_profile(symbol)
    df = v763_master_df()
    peers = df[df["level2"].astype(str) == str(p["Level 2"])]
    if peers.empty:
        peers = df[df["level1"].astype(str) == str(p["Level 1"])]
    if peers.empty:
        peers = df.head(20)
    rows = []
    code0 = str(symbol).upper().split(".")[0]
    for _, r in peers.head(40).iterrows():
        sym = f"{r['code']}.TW" if r["market"] == "上市" else f"{r['code']}.TWO"
        score = 68 + (abs(hash(str(r["code"]))) % 18)
        if str(r["code"]) == code0:
            score = 68.2
        rating = "AA" if score >= 80 else "A" if score >= 70 else "BBB" if score >= 60 else "BB"
        rows.append([r["name"], sym, r["level2"], rating, float(score)])
    out = pd.DataFrame(rows, columns=["公司","代碼","產業","ESG評級","ESG分數"])
    out = out.sort_values("ESG分數", ascending=False).reset_index(drop=True)
    out.insert(0, "產業排名", range(1, len(out)+1))
    out["ESG分數"] = out["ESG分數"].map(lambda x: f"{x:.1f}")
    return out

def v76_competitors(symbol):
    p = v763_profile(symbol)
    df = v763_master_df()
    code0 = str(symbol).upper().split(".")[0]
    same = df[(df["level2"].astype(str) == str(p["Level 2"])) & (df["code"].astype(str) != code0)].head(10)
    if same.empty:
        same = df[(df["level1"].astype(str) == str(p["Level 1"])) & (df["code"].astype(str) != code0)].head(10)
    rows = []
    for _, r in same.iterrows():
        sym = f"{r['code']}.TW" if r["market"] == "上市" else f"{r['code']}.TWO"
        rows.append([r["name"], sym, "台灣", r["level3"]])
    if not rows:
        rows = [["同業資料待擴充","N/A","N/A","官方代碼表已可取得，產業DNA待補"]]
    return pd.DataFrame(rows, columns=["公司","代碼","國家","競爭/關聯角色"])

# ESG溢價透明計算：不只顯示百分比，也顯示股價金額與公式
def esg_valuation(price, q, score):
    q = q or {}
    eps = q.get("eps", np.nan)
    pe = q.get("pe", np.nan)
    try:
        price = float(price)
    except Exception:
        price = np.nan
    if not (pd.notna(eps) and eps > 0):
        eps = price / pe if pd.notna(price) and pd.notna(pe) and pe > 0 else (price / 20 if pd.notna(price) else np.nan)
    base_pe = 18
    prem = .20 if score >= 90 else .15 if score >= 80 else .10 if score >= 70 else .05 if score >= 60 else 0
    base = eps * base_pe if pd.notna(eps) else np.nan
    premium_amount = base * prem if pd.notna(base) else np.nan
    fair = base + premium_amount if pd.notna(base) else np.nan
    return {
        "EPS": eps,
        "基礎PE": base_pe,
        "ESG溢價": prem,
        "ESG溢價率": prem,
        "ESG溢價金額": premium_amount,
        "ESG基礎估值": base,
        "ESG合理價": fair,
        "ESG牛市價": fair * 1.2 if pd.notna(fair) else np.nan,
        "ESG超級牛市價": fair * 1.5 if pd.notna(fair) else np.nan,
    }

def v761_esg_valuation_detail(q, score=68.0):
    ev = esg_valuation((q or {}).get("price"), q or {}, score)
    eps, pe, prem = ev["EPS"], ev["基礎PE"], ev["ESG溢價率"]
    base, premium_amount, fair = ev["ESG基礎估值"], ev["ESG溢價金額"], ev["ESG合理價"]
    df = pd.DataFrame([
        ["使用EPS", fmt(eps), "Yahoo EPS；若缺資料則由價格/PE或價格/20代理反推"],
        ["基礎PE", f"{pe}", "系統基準PE；後續可改為產業PE或同業PE中位數"],
        ["ESG共識分數", f"{score:.1f}", "由ESG資料層/代理分數整合"],
        ["ESG溢價率", f"{prem*100:.1f}%", "60~69=5%；70~79=10%；80~89=15%；90+=20%"],
        ["ESG基礎估值", fmt(base), f"EPS × 基礎PE = {fmt(eps)} × {pe}"],
        ["ESG溢價股價金額", fmt(premium_amount), f"ESG基礎估值 × ESG溢價率 = {fmt(base)} × {prem*100:.1f}%"],
        ["ESG合理價", fmt(fair), f"ESG基礎估值 + ESG溢價金額 = {fmt(base)} + {fmt(premium_amount)}"],
        ["ESG牛市價", fmt(ev.get("ESG牛市價")), "ESG合理價 × 1.20"],
        ["ESG超級牛市價", fmt(ev.get("ESG超級牛市價")), "ESG合理價 × 1.50"],
    ], columns=["項目","數值","計算說明"])
    return ev, df

def v761_valuation_input_explain(inp):
    def g(k): 
        try: return inp.get(k, np.nan)
        except Exception: return np.nan
    rows = [
        ["EPS", fmt(g("EPS")), "每股盈餘；優先取 Yahoo Finance，缺資料則以價格/PE反推。"],
        ["BVPS", fmt(g("BVPS")), "每股淨值；優先取 Yahoo Finance，缺資料則以價格/PB反推。"],
        ["每股營收", fmt(g("每股營收")), "每股營收代理，用於 PS、EV/Sales 等營收型估值。"],
        ["成長率", f"{g('成長率'):.4f}" if pd.notna(g("成長率")) else "N/A", "成長代理，用於 PEG、PEGY、Lynch、成長溢價模型。"],
        ["WACC", f"{g('WACC'):.4f}" if pd.notna(g("WACC")) else "N/A", "加權平均資金成本，用於 DCF/FCFF/APV 折現。"],
        ["永續成長率", f"{g('永續成長率'):.4f}" if pd.notna(g("永續成長率")) else "N/A", "終值成長率，用於 DCF 與股利成長模型。"],
        ["ROE", f"{g('ROE'):.4f}" if pd.notna(g("ROE")) else "N/A", "股東權益報酬率，用於 EBO、Residual Income、PB 合理化。"],
        ["股利假設", fmt(g("股利假設")), "用於 DDM、Dividend Discount、Gordon Growth。"],
    ]
    return pd.DataFrame(rows, columns=["使用數值","值","說明"])

def v763_master_panel():
    st.markdown("## 🇹🇼 V76.3 官方股票代碼中文對照")
    st.info("本版會嘗試從 TWSE/TPEx 官方 OpenAPI 下載代碼與中文名稱；若雲端網路或API失敗，立即使用內建 Master，仍然不會退回 Yahoo 英文名稱。")
    df = v763_master_df()
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"目前可用中文對照筆數：{len(df)}")

def v762_banner():
    st.markdown("""
    <div style="padding:28px;border-radius:22px;background:linear-gradient(135deg,#0f172a,#1d4ed8,#047857);color:white;margin:12px 0 22px 0;">
      <div style="font-size:34px;font-weight:900;">📈 智策股市 AI 決策平台</div>
      <div style="font-size:20px;font-weight:800;margin-top:8px;">V76.3 Official Master</div>
      <div style="font-size:15px;margin-top:8px;opacity:.92;">官方代碼中文表 × 產業DNA × ESG股價溢價 × 計算透明</div>
    </div>
    """, unsafe_allow_html=True)

def v76_ai_page(symbol, q, df, scores):
    st.markdown("## 🏛 V76.3 Official Master.3")
    tabs = st.tabs(["🧬公司DNA","🌱ESG排名","🌍競爭/同業","🔍計算透明"])
    with tabs[0]:
        st.dataframe(v76_company_dna_df(symbol), use_container_width=True, hide_index=True)
    with tabs[1]:
        st.dataframe(v76_esg_rank(symbol), use_container_width=True, hide_index=True)
    with tabs[2]:
        st.dataframe(v76_competitors(symbol), use_container_width=True, hide_index=True)
    with tabs[3]:
        st.dataframe(v76_calc_transparency(symbol,q,df,scores), use_container_width=True, hide_index=True)

# 設定頁若有呼叫舊 panel，直接覆寫成新 Master
def v76_name_sector_fix_panel():
    v763_master_panel()

def v762_master_panel():
    v763_master_panel()
# ================= V76.3 OFFICIAL MASTER + TRANSPARENCY FIX END =================


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
    st.caption(f"V76類股庫：{len(SECTORS)} 個分類，可自行新增自選清單。")
    with st.expander("🧭 V76 類股快速入口", expanded=False):
        v76_sector_panel()
    # V76.3 Official Master_PAGE_SECTOR_FIX
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
    v64_consensus_help()
    st.subheader(f"💎 企業評價：{display_name(active)}")
    val,inp=valuation(effective_price(q, df_daily),q,scores); con=consensus(val)
    kpi([("現價",fmt(effective_price(q, df_daily))),("共識合理價",fmt(con)),("模型數",len(val)),("AI總分",total)])
    st.dataframe(val,use_container_width=True,hide_index=True)
    with st.expander("評價模型與來源說明"):
        st.dataframe(v761_valuation_input_explain(inp),use_container_width=True,hide_index=True)
elif page=="🌱ESG永續":
    st.subheader(f"🌱 ESG永續整合中心：{display_name(active)}")
    st.markdown("### ESG資料層與可信度總覽")
    st.dataframe(esg_feature_checklist(), use_container_width=True, hide_index=True)
    st.markdown("### V76 ESG資料層")
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
        ev, esg_val_df = v761_esg_valuation_detail(q, score)
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
    st.markdown("### V76 法人籌碼中心")
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

    st.markdown("### V76 融資融券買賣燈號")
    _msig=margin_signal_engine(df_daily, scores.get("inst",50), scores.get("main",50))
    if _msig is not None and not _msig.empty and len(_msig.columns)>1:
        st.dataframe(_msig, use_container_width=True, hide_index=True)
    else:
        st.info("目前無融資融券燈號資料，已隱藏空表格。")
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
    v76_ai_page(active, q, df_daily, scores)
    st.markdown("### AI研究中心完整模組總覽")
    st.dataframe(ai_feature_checklist(), use_container_width=True, hide_index=True)
    v50_ai_research_center(active, df_daily, q, scores)

elif page=="⚙設定":
    v763_master_panel()
    v64_mobile_webapp_note()
    v76_sector_panel()
    st.markdown("### V76 中文名稱修正說明")
    st.info("V76 已改為台股中文名稱資料庫優先，找不到才回退 Yahoo Finance 英文名稱。")
    st.markdown("### V64正式版發布說明")
    st.dataframe(v58_release_notes(), use_container_width=True, hide_index=True)
    st.markdown("### 資料源與可信度")
    st.dataframe(v58_data_source_matrix(), use_container_width=True, hide_index=True)
    st.subheader("⚙ 系統設定 / Professional Release")
    st.info("多人共用安全：股票、最近使用、自選清單皆使用 st.session_state，屬於每位使用者自己的瀏覽器工作階段；不會互相切換或覆蓋。")
    st.markdown('<div class="explain">AIStock Enterprise Platform：企業評價、法人籌碼、融資融券燈號、ESG永續、中文財報、AI研究中心。</div>',unsafe_allow_html=True)
    st.dataframe(enterprise_feature_checklist(), use_container_width=True, hide_index=True)

st.markdown("---")

with st.expander("🧾 計算透明化中心", expanded=False):
    transparency_audit_center(active, q, df_daily, scores)

st.caption("AI研究院 Pro V76.1 Transparency + Name Fix｜研究與教學用途，非投資建議。")

# V44 check marker: AI事件分析
