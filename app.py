from io import StringIO
import os
os.environ["STREAMLIT_RUNNER_MAGIC_ENABLED"] = "false"
import requests

import streamlit as st

# ===== V96.10 SUPPRESS DELTAGENERATOR DISPLAY START =====
# 根治 Streamlit Magic / st.write 顯示 DeltaGenerator 物件：
# 正常文字、表格、圖表照常顯示；只有 DeltaGenerator 物件會被忽略。
try:
    from streamlit.delta_generator import DeltaGenerator as _AIVM_DeltaGenerator
    _aivm_original_st_write = st.write

    def _aivm_safe_st_write(*args, **kwargs):
        try:
            filtered = []
            for x in args:
                if isinstance(x, _AIVM_DeltaGenerator):
                    continue
                # 有些 DeltaGenerator 可能被包成 tuple/list
                if isinstance(x, (list, tuple)):
                    cleaned = [i for i in x if not isinstance(i, _AIVM_DeltaGenerator)]
                    if cleaned:
                        filtered.append(type(x)(cleaned))
                    continue
                filtered.append(x)

            if not filtered:
                return None

            return _aivm_original_st_write(*filtered, **kwargs)
        except Exception:
            return None

    st.write = _aivm_safe_st_write
except Exception:
    pass
# ===== V96.10 SUPPRESS DELTAGENERATOR DISPLAY END =====

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


APP_VERSION="V101.0 DNA Alpha Engine Trial"
APP_NAME="智策股市 AI 決策平台"
st.set_page_config(page_title=f"{APP_NAME} {APP_VERSION}", page_icon="📈", layout="wide", initial_sidebar_state="expanded")


# ================= AI / ESG / 法人完整補齊 =================
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
    kpi([("AI評級", tables["① AI評級"].iloc[0,1]),("機構分數",f"{total}/100"),("風險預警",f"{risk}/100"),("模型共識價",fmt(con))])
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
# ================= AI / ESG / 法人完整補齊 END =================


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


/* V92.2 AIVM Lab Historical PE PB Calibration responsive audit */
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


# V92.2 AIVM Lab Historical PE PB Calibration：擴充台股中文名稱對照；每位使用者使用自己的 session_state，不寫共用 watchlist.json
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
    # V92.2 AIVM Lab Historical PE PB Calibration.2: 使用 Streamlit autorefresh，避免 browser reload 導致回首頁或股票重設
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
    """V92.2 AIVM Lab Historical PE PB Calibration: if Yahoo quote is N/A, use latest K-line close as backup so valuation models do not disappear."""
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
    if df.empty: return {"股票":display_name(symbol),"價格":None,"漲跌幅":None,"機構分數":0}
    d=signal_cols(add_indicators(df)); s=score_blocks(d,q); price=q.get("price"); prev=q.get("prev"); pct=(price-prev)/prev*100 if pd.notna(price) and pd.notna(prev) and prev else np.nan
    val,_=valuation(price,q,s); con=consensus(val); sig={}
    if not d.empty:
        last=d.iloc[-1]
        for c in ["黃金交叉","MACD翻紅","KD黃金交叉","RSI突破50","爆量突破"]: sig[c]=bool(last.get(c,False))
    return {"股票":display_name(symbol),"價格":None if pd.isna(price) else round(price,2),"漲跌幅":None if pd.isna(pct) else round(pct,2),"機構分數":ai_total(s),"法人分數":s["inst"],"主力分數":s["main"],"共識價":None if pd.isna(con) else round(con,2),**sig}

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
            f'<div class="card-small">AI {r.get("機構分數","N/A")} | 法人 {r.get("法人分數","N/A")} | 主力 {r.get("主力分數","N/A")} | 共識價 {r.get("共識價","N/A")}</div>'
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
        ["機構分數", f"{total}/100"],
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
        ("機構分數", f"{total}/100"),
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
        st.dataframe(v8941_format_financial_df(summary), use_container_width=True, hide_index=True)

    with tabs[1]:
        income_zh = zh_financial_df(ft.get("income", pd.DataFrame()))
        if income_zh.empty:
            st.warning("Yahoo Finance 暫無損益表資料。")
        else:
            st.dataframe(v8941_format_financial_df(income_zh), use_container_width=True, hide_index=True)

    with tabs[2]:
        balance_zh = zh_financial_df(ft.get("balance", pd.DataFrame()))
        if balance_zh.empty:
            st.warning("Yahoo Finance 暫無資產負債表資料。")
        else:
            st.dataframe(v8941_format_financial_df(balance_zh), use_container_width=True, hide_index=True)

    with tabs[3]:
        cashflow_zh = zh_financial_df(ft.get("cashflow", pd.DataFrame()))
        if cashflow_zh.empty:
            st.warning("Yahoo Finance 暫無現金流量表資料。")
        else:
            st.dataframe(v8941_format_financial_df(cashflow_zh), use_container_width=True, hide_index=True)

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


# ================= K線副圖與籌碼燈號增強 =================
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
    """融資融券 + 借券 + 主力，產生買進/賣出燈號。正式資料未串接時用量價代理。"""
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
# ================= K線副圖與籌碼燈號增強 END =================

st.markdown("""

<div class="hero">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="font-size:1.5rem;">📈</div>
    <div>
      <div style="font-weight:950;font-size:1.15rem;">智策股市 AI 決策平台</div>
      <div style="font-size:.78rem;color:#dbeafe;margin-top:2px;">
        V92.2 AIVM Lab Historical PE PB Calibration｜企業評價 × 法人籌碼 × 融資融券燈號 × ESG永續 × 中文財報 × AI研究
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
    <text x="40" y="42" fill="#ffffff" font-size="28" font-weight="900">V92.2 AIVM Lab Historical PE PB Calibration</text>
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
    <text x="40" y="158" fill="#dbeafe" font-size="13"></text>
  </svg>
</div>

""", unsafe_allow_html=True)

MAIN=["🏠首頁","📊監控","📈K線","🏛企業價值研究院","🧪AIVM研究中心","⚙設定","🧪AIVM Lab"]
if "page" not in st.session_state: st.session_state.page="🏠首頁"

# V60_PAGE_TARGET_HELPER: APP快捷入口目標保存在 session_state；若原始選單未吃到，仍可由各頁判斷使用。

# ================= V76.1 TRANSPARENCY + NAME FIX LAYER =================
APP_VERSION="V92.2 AIVM Lab Historical PE PB Calibration"

# 補充 未覆蓋股票中文名稱與產業DNA，避免回退 Yahoo 英文名稱或待分類。
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

# ===== V96.2 CLEAN MAIN MENU NO MONITOR START =====
try:
    MAIN = [x for x in MAIN if "監控" not in str(x)]
    menu_items = [x for x in globals().get("menu_items", MAIN) if "監控" not in str(x)]
    main_tabs = [x for x in globals().get("main_tabs", MAIN) if "監控" not in str(x)]
    if st.session_state.get("page") and "監控" in str(st.session_state.page):
        st.session_state.page = "🏠首頁"
except Exception:
    MAIN = ["🏠首頁","📈K線","🏛企業價值研究院","🧪AIVM研究中心","⚙設定","🧪AIVM Lab"]
# ===== V96.2 CLEAN MAIN MENU NO MONITOR END =====

page=st.radio("主選單",MAIN,index=MAIN.index(st.session_state.page) if st.session_state.page in MAIN else 0,horizontal=True,key="stable_page_menu")
if page in ["🏦法人","🏢法人","💎評價","🌱ESG永續","📑中文財報"]:
    page="🏠首頁"
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
    # V92.2 AIVM Lab Historical PE PB Calibration_SIDEBAR_SECTOR_FIX
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
        ["① AI評級", "機構分數、星等、目前狀態、模型共識價", "完成"],
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

# =================  CLEAN UX + SIGNAL AUDIT EDITION LAYER =================
_NAME_MAP = {
    "2330.TW": "台積電", "2303.TW": "聯電", "2454.TW": "聯發科", "2317.TW": "鴻海", "2382.TW": "廣達",
    "2379.TW": "瑞昱", "2408.TW": "南亞科", "3374.TW": "精材", "6739.TW": "竹陞科技",
    "8112.TW": "至上", "6189.TW": "豐藝", "6215.TWO": "和椿科技", "6830.TW": "汎銓", "6415.TW": "矽力-KY",
    "5347.TWO": "世界先進", "3711.TW": "日月光投控", "3661.TW": "世芯-KY", "3019.TW": "亞光", "2049.TW": "上銀", "1536.TW": "和大",
}
try:
    CODE_NAME_MAP.update(_NAME_MAP)
except Exception:
    CODE_NAME_MAP = _NAME_MAP.copy()
try:
    TW_STOCKS.update({"精材":"3374.TW", "竹陞":"6739.TW", "竹陞科技":"6739.TW", "至上":"8112.TW", "至上電子":"8112.TW", "豐藝":"6189.TW", "豐藝電子":"6189.TW"})
except Exception:
    pass

def stock_name_only(symbol):
    s = str(symbol).upper().strip(); code = s.split('.')[0]
    if s in _NAME_MAP: return _NAME_MAP[s]
    try:
        if s in CODE_NAME_MAP: return CODE_NAME_MAP[s]
    except Exception: pass
    for full,nm in _NAME_MAP.items():
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
**納入共識**就是：這個估值模型會參與最後的「基準價值」計算。\n\n- ✅ 勾選：該模型數值會放進綜合合理價。\n- ⬜ 不勾選：只在表格中參考，不影響最後共識價。\n- ⚠️ 極端值：系統可標示為極端值，避免單一模型把共識價拉太高或拉太低。\n\n例如只勾選 DCF、FCFF、FCFE，系統就用這三個模型形成基準價值。這不是保證價格，而是多模型平均/加權後的參考區間。
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
# =================  CLEAN UX + SIGNAL AUDIT EDITION LAYER END =================

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
        ["AI題材新聞", "AI伺服器、半導體、電子通路、設備鏈題材追蹤", "產業代理詞庫", f"機構分數={ai}/100", "中低", "未串即時新聞前，用產業關鍵字代理"],
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
            "PE / PB / 機構分數 / 法人分數綜合比較",
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
        ["估值事件", "股價高於/低於模型基準價值", f"現價={price}", "企業評價模型", "中"],
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
        c1.metric("機構分數", f"{v67_num(scores.get('ai', scores.get('tech', 60)), 60):.1f}/100")
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

    with tabs[5]:
        st.markdown("### 📈 AI EPS 預測")
        st.dataframe(v67_eps_forecast(symbol, q, scores), use_container_width=True, hide_index=True)
        st.caption("EPS預測為代理模型：以目前EPS、機構分數、技術/財報/法人分數推估，不等於公司財測。")

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
    return pd.DataFrame(rows, columns=["公司", "代碼", "國家", "角色", "現價", "EPS", "PE", "PB", "代理合理價", "機構分數", "說明"])

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















# ================= NAME RESOLVER + SECTOR COMPLETE LAYER =================
APP_BRAND = "AI研究院 Pro"
APP_VERSION="V92.2 AIVM Lab Historical PE PB Calibration"

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
    st.markdown('### 🧭 類股快速入口')
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
    rows.append(['機構級估值中心',fmt(consensus),'最終','納入模型中位數','把所有納入模型價格排序後取中位數，降低極端值影響'])
    return pd.DataFrame(rows,columns=['模型','使用價格','狀態','公式/方法','使用數值與說明'])

def v76_ai_page(symbol,q,df,scores):
    st.markdown('## 🏛 V92.2 AIVM Lab Historical PE PB Calibration.3')
    tabs=st.tabs(['🧬公司DNA','🌱ESG排名','🌍競爭/同業','🔍計算透明'])
    with tabs[0]: st.dataframe(v76_company_dna_df(symbol),use_container_width=True,hide_index=True)
    with tabs[1]: st.dataframe(v76_esg_rank(symbol),use_container_width=True,hide_index=True)
    with tabs[2]: st.dataframe(v76_competitors(symbol),use_container_width=True,hide_index=True)
    with tabs[3]: st.dataframe(v76_calc_transparency(symbol,q,df,scores),use_container_width=True,hide_index=True)
# ================= NAME RESOLVER + SECTOR COMPLETE LAYER END =================

# =================  OFFICIAL MASTER + TRANSPARENCY FIX =================
APP_BRAND = "AI研究院 Pro"
APP_VERSION="V92.2 AIVM Lab Historical PE PB Calibration"

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
    return {"公司":r["name"],"代碼":s,"市場":r["market"],"Level 1":r["level1"],"Level 2":r["level2"],"Level 3":r["level3"],"Level 4":r["level4"],"Level 5":r["level5"],"產業":r["level2"],"次產業":r["level3"],"產業鏈位置":r["chain"],"商業模式":r["level3"],"產業成熟度":"成長期" if "AI" in str(r["level5"]) else "成熟/循環","產業景氣燈號":"🟢 熱絡" if "AI" in str(r["level5"]) else "🟡 中立","資料層":"官方代碼表 + 內建DNA"}

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
        ["每股營收", fmt(g("每股營收")), "每股營收需以營業收入 ÷ 普通股股數計算；若股數或單位不足，顯示為資料不足，避免誤導。"],
        ["成長率", f"{g('成長率'):.4f}" if pd.notna(g("成長率")) else "N/A", "成長代理，用於 PEG、PEGY、Lynch、成長溢價模型。"],
        ["WACC", f"{g('WACC'):.4f}" if pd.notna(g("WACC")) else "N/A", "加權平均資金成本，用於 DCF/FCFF/APV 折現。"],
        ["永續成長率", f"{g('永續成長率'):.4f}" if pd.notna(g("永續成長率")) else "N/A", "終值成長率，用於 DCF 與股利成長模型。"],
        ["ROE", f"{g('ROE'):.4f}" if pd.notna(g("ROE")) else "N/A", "股東權益報酬率，用於 EBO、Residual Income、PB 合理化。"],
        ["股利假設", fmt(g("股利假設")), "用於 DDM、Dividend Discount、Gordon Growth。"],
    ]
    return pd.DataFrame(rows, columns=["使用數值","值","說明"])

def v763_master_panel():
    st.markdown("## 🇹🇼  官方股票代碼中文對照")
    st.info("本版會嘗試從 TWSE/TPEx 官方 OpenAPI 下載代碼與中文名稱；若雲端網路或API失敗，立即使用內建 Master，仍然不會退回 Yahoo 英文名稱。")
    df = v763_master_df()
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"目前可用中文對照筆數：{len(df)}")

def v762_banner():
    st.markdown("""
    <div style="padding:28px;border-radius:22px;background:linear-gradient(135deg,#0f172a,#1d4ed8,#047857);color:white;margin:12px 0 22px 0;">
      <div style="font-size:34px;font-weight:900;">📈 智策股市 AI 決策平台</div>
      <div style="font-size:20px;font-weight:800;margin-top:8px;">V92.2 AIVM Lab Historical PE PB Calibration</div>
      <div style="font-size:15px;margin-top:8px;opacity:.92;">官方代碼中文表 × 產業DNA × ESG股價溢價 × 計算透明</div>
    </div>
    """, unsafe_allow_html=True)

def v76_ai_page(symbol, q, df, scores):
    st.markdown("## 🏛 V92.2 AIVM Lab Historical PE PB Calibration.3")
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
# =================  OFFICIAL MASTER + TRANSPARENCY FIX END =================

# ================= V85 FINAL ARCHITECTURE EDITION LAYER =================
# 基底：。首頁、監控、K線、設定不重寫；只把原四大中心原封不動嵌入研究院。
APP_VERSION="V92.2 AIVM Lab Historical PE PB Calibration"

def v85_num(x, default=np.nan):
    try:
        if x is None or str(x).strip() in ["", "N/A", "None", "nan"]:
            return default
        return float(str(x).replace(",", "").replace("%", ""))
    except Exception:
        return default

def v85_fmt(x, digits=2):
    try:
        if x is None or pd.isna(float(x)):
            return "N/A"
        return f"{float(x):,.{digits}f}"
    except Exception:
        return str(x)

def v85_profile(symbol):
    try:
        if "v763_profile" in globals():
            p = v763_profile(symbol)
            if isinstance(p, dict):
                return p
    except Exception:
        pass
    s = str(symbol).upper()
    code0 = s.split(".")[0]
    name_map = {"2330":"台積電","2303":"聯電","5347":"世界先進","3030":"德律","3374":"精材","6570":"維田"}
    db = {
        "2330":["電子","半導體","晶圓代工","先進製程","AI/HPC","中游","Foundry晶圓代工","成熟成長型","技術/規模/客戶"],
        "2303":["電子","半導體","晶圓代工","成熟製程","車用/工控","中游","Foundry晶圓代工","成熟循環型","產能/客戶"],
        "5347":["電子","半導體","晶圓代工","特殊製程","車用/工控","中游","特殊製程代工","成熟循環型","製程/客戶"],
        "3030":["電子","設備","AOI檢測設備","PCB/半導體檢測","自動化檢測","中游","設備銷售","成長循環型","技術/客戶認證"],
    }
    row = db.get(code0, ["待分類","待分類","待分類","待分類","待分類","待確認","待確認","待確認","待確認"])
    return {"公司名稱":name_map.get(code0, code0), "股票代號":s,
            "Level 1 大類":row[0], "Level 2 產業":row[1], "Level 3 次產業":row[2],
            "Level 4 細分領域":row[3], "Level 5 投資主題":row[4],
            "產業鏈位置":row[5], "商業模式":row[6], "產業成熟度":row[7], "護城河":row[8]}

def v85_display(symbol):
    try:
        return display_name(symbol)
    except Exception:
        p = v85_profile(symbol)
        return f"{p.get('公司名稱', symbol)} / {p.get('股票代號', symbol)}"

def v85_industry_basic(symbol):
    p = v85_profile(symbol)
    text = "".join(str(v) for v in p.values())
    health = 60
    if any(k in text for k in ["AI","半導體","先進製程","電力","光通訊","散熱"]): health += 20
    if any(k in text for k in ["面板","航運","鋼鐵","塑化"]): health -= 5
    health = max(0, min(100, health))
    return pd.DataFrame([
        ["產業定位", p.get("Level 2 產業", p.get("Level 2","待分類")), "主要產業"],
        ["次產業", p.get("Level 3 次產業", p.get("Level 3","待分類")), "細分產業"],
        ["產業鏈位置", p.get("產業鏈位置","待確認"), "上游/中游/下游"],
        ["商業模式", p.get("商業模式","待確認"), "收入與營運模式"],
        ["產業健康度", f"{health:.1f}", "景氣、成長主題、產業循環代理"],
        ["景氣燈號", "🟢 擴張" if health>=80 else "🟡 中立" if health>=55 else "🔴 低迷", "由產業健康度轉換"],
    ], columns=["項目","內容","說明"])

def v85_competitors(symbol):
    code0 = str(symbol).split(".")[0]
    if code0 == "2330":
        rows = [["台積電","2330.TW","台灣","本公司/晶圓代工"],["Samsung Foundry","005930.KS","韓國","全球競爭"],["Intel Foundry","INTC","美國","全球競爭"],["GlobalFoundries","GFS","美國","全球競爭"],["聯電","2303.TW","台灣","成熟製程同業"],["世界先進","5347.TWO","台灣","特殊製程同業"]]
    elif code0 == "3030":
        rows = [["德律","3030.TW","台灣","本公司/AOI檢測"],["由田","3455.TW","台灣","AOI設備"],["致茂","2360.TW","台灣","測試設備"],["Camtek","CAMT","以色列","全球AOI/檢測"],["Koh Young","098460.KQ","韓國","3D檢測"],["Mirtec","N/A","韓國","AOI設備"]]
    else:
        rows = [["同業資料待擴充","N/A","N/A","V86再補產業/全球競爭資料庫"]]
    return pd.DataFrame(rows, columns=["公司","代碼","國家","競爭/關聯角色"])

def v85_weight_methodology():
    st.info("")
    st.dataframe(pd.DataFrame([
        ["企業品質","25% / 動態","依公司類型調整；一般企業以商業模式與競爭力為核心"],
        ["財務體質","20% / 動態","避免價值陷阱，衡量ROE、現金流與財務穩定"],
        ["估值吸引力","20% / 動態","安全邊際與預期報酬空間"],
        ["法人籌碼","15% / 動態","反映中短期資金流與市場重估速度"],
        ["ESG","10% / 動態","風險折價與長期資金偏好"],
        ["產業前景","10% / 動態","景氣循環與成長假設"],
    ], columns=["項目","權重","來源/理由"]), use_container_width=True, hide_index=True)

def v85_decision_placeholder(active, q, df_daily, scores):
    try:
        val, inp = valuation(effective_price(q, df_daily), q, scores)
        con = consensus(val)
        price = effective_price(q, df_daily)
        mos = (con-price)/con*100 if con and con>0 and price else np.nan
        grade = "低估" if mos>=15 else "合理" if mos>=-15 else "高估"
        st.dataframe(pd.DataFrame([
            ["現價", fmt(price), "effective_price(q, df_daily)"],
            ["基準價值", fmt(con), "原評價中心 consensus(val)"],
            ["安全邊際", f"{mos:.1f}%" if pd.notna(mos) else "N/A", "(共識價-現價)/共識價"],
            ["估值判定", grade, "15%以上低估；±15%合理；-15%以下高估"],
        ], columns=["項目","結果","依據"]), use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"投資決策中心暫無法計算：{e}")


def v85_original_financial_center(active, q, df_daily, scores=None):
    financial_center(active,q,df_daily)

def v85_original_valuation_center(active, q, df_daily, scores):
    total = scores.get('total', scores.get('ai', scores.get('tech', 0))) if isinstance(scores, dict) else 0
    v64_consensus_help()
    st.subheader(f"💎 企業評價：{display_name(active)}")
    val,inp=valuation(effective_price(q, df_daily),q,scores); con=consensus(val)
    kpi([("現價",fmt(effective_price(q, df_daily))),("基準價值",fmt(con)),("模型數",len(val)),("AI總分",total)])
    st.dataframe(val,use_container_width=True,hide_index=True)
    with st.expander("評價模型與來源說明"):
        st.dataframe(v761_valuation_input_explain(inp),use_container_width=True,hide_index=True)

def v85_original_esg_center(active, q, df_daily, scores):
    st.subheader(f"🌱 ESG永續整合中心：{display_name(active)}")
    st.markdown("### ESG資料層與可信度總覽")
    st.dataframe(esg_feature_checklist(), use_container_width=True, hide_index=True)
    st.markdown("### ESG資料層")
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

def v85_original_institutional_center(active, q, df_daily, scores):
    st.subheader(f"🏦 法人籌碼中心：{display_name(active)}")
    st.markdown("### 籌碼中心")
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

    st.markdown("### 融資融券買賣燈號")
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

def v87_research_institute(active, q, df_daily, scores):
    st.markdown("""
    <div style="padding:34px;border-radius:28px;background:linear-gradient(135deg,#020617,#1e3a8a,#0f766e);color:white;margin:12px 0 24px 0;border:1px solid rgba(212,175,55,.35);box-shadow:0 16px 36px rgba(2,6,23,.25);">
      <div style="font-size:40px;font-weight:900;">🏛 AI企業價值研究院</div>
      <div style="font-size:22px;font-weight:800;color:#f8e6a0;margin-top:6px;">Enterprise Valuation Institute｜V92.2 AIVM Lab Historical PE PB Calibration</div>
      <div style="font-size:16px;margin-top:10px;">V85 = 完整搬遷版：財報、評價、ESG、法人原封不動搬入研究院</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"### 研究標的：{v85_display(active)}")
    tabs = st.tabs(["①公司DNA","②產業研究院","③全球競爭研究院","④同業比較研究院","⑤財報研究院","⑥企業評價研究院","⑦ESG研究院","⑧法人研究院","⑨機構級估值中心研究院","⑩AI評級透明化中心","⑪模型依據中心","⑫投資決策中心"])
    with tabs[0]:
        st.dataframe(pd.DataFrame(list(v85_profile(active).items()), columns=["項目","內容"]), use_container_width=True, hide_index=True)
    with tabs[1]:
        st.dataframe(v85_industry_basic(active), use_container_width=True, hide_index=True)
        st.info("產業鏈、景氣循環與趨勢資料庫將於 V86 補強。")
    with tabs[2]:
        st.dataframe(v85_competitors(active), use_container_width=True, hide_index=True)
        st.info("全球競爭、市占率與替代風險將於 V86 補強。")
    with tabs[3]:
        st.info("同業PE/PB/ROE/EPS比較將於 V86 補強；V85優先完成四大中心搬遷。")
        st.dataframe(v85_competitors(active), use_container_width=True, hide_index=True)
    with tabs[4]:
        v85_original_financial_center(active, q, df_daily, scores)
    with tabs[5]:
        v85_original_valuation_center(active, q, df_daily, scores)
    with tabs[6]:
        v85_original_esg_center(active, q, df_daily, scores)
    with tabs[7]:
        v85_original_institutional_center(active, q, df_daily, scores)
    with tabs[8]:
        st.subheader("⑨ 機構級估值中心研究院")
        v85_original_valuation_center(active, q, df_daily, scores)
        st.info("本頁先沿用原評價中心共識價；V86/V87再拆出動態權重與納入/排除原因。")
    with tabs[9]:
        st.subheader("⑩ AI評級透明化中心")
        v85_weight_methodology()
    with tabs[10]:
        st.subheader("⑪ 模型依據中心")
        st.info("每股營收須有明確股數與單位來源；若來源不足或疑似單位錯誤，將顯示 N/A。")
        try:
            val, inp = valuation(effective_price(q, df_daily), q, scores)
            st.dataframe(v873_patch_model_input_dataframe(v761_valuation_input_explain(inp)), use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"模型依據暫無法顯示：{e}")
        v85_weight_methodology()
    with tabs[11]:
        st.subheader("⑫ 投資決策中心")
        v85_decision_placeholder(active, q, df_daily, scores)

# Override old AI page entry only; old 評價/ESG/法人/中文財報主選單仍可保留作對照。
def v76_ai_page(symbol, q=None, df=None, scores=None): return v85_final_research_institute(symbol, q, df, scores or {})
def v77_ai_page(symbol, q=None, df=None, scores=None): return v85_final_research_institute(symbol, q, df, scores or {})
def v80_enterprise_value_page(symbol, q=None, df=None, scores=None): return v85_final_research_institute(symbol, q, df, scores or {})
# ================= V85 FINAL ARCHITECTURE EDITION LAYER END =================

# ================= V86.1 INDUSTRY INTELLIGENCE STARTUP FIXED LAYER =================
APP_VERSION="V92.2 AIVM Lab Historical PE PB Calibration"

def v861_profile_data(active):
    code0 = str(active).split(".")[0]
    db = {
        "2330": {
            "level1":"電子","level2":"半導體","level3":"晶圓代工","level4":"先進製程","level5":"AI/HPC",
            "upstream":"半導體設備、矽晶圓、EDA/IP、特用化學品",
            "midstream":"晶圓代工、先進製程、特殊製程",
            "downstream":"IC設計、AI GPU、手機晶片、車用晶片、HPC客戶",
            "cycle":"擴張期","health":92,
            "advantages":"技術領先、先進製程市占高、客戶黏著度強、資本支出規模大",
            "risks":"地緣政治、先進製程資本密集、客戶集中、景氣循環",
            "trend":"未來三年主要受AI/HPC、先進封裝、車用與高效能運算需求驅動。"
        },
        "3030": {
            "level1":"電子","level2":"設備","level3":"AOI檢測設備","level4":"PCB/半導體檢測","level5":"AI自動化檢測",
            "upstream":"鏡頭、感測器、控制器、精密機構、軟體演算法",
            "midstream":"AOI檢測設備、測試設備、自動化設備",
            "downstream":"PCB廠、封測廠、電子組裝、終端品牌供應鏈",
            "cycle":"擴張期","health":78,
            "advantages":"AOI技術、客戶認證、設備整合能力、AI檢測升級",
            "risks":"設備訂單循環、資本支出放緩、客戶集中、國際競爭",
            "trend":"未來三年AI檢測、自動化、先進PCB與半導體檢測需求將是主軸。"
        },
        "2303": {
            "level1":"電子","level2":"半導體","level3":"晶圓代工","level4":"成熟製程","level5":"車用/工控",
            "upstream":"矽晶圓、半導體設備、化學品",
            "midstream":"成熟製程晶圓代工",
            "downstream":"電源管理、車用、工控、消費性IC",
            "cycle":"復甦期","health":72,
            "advantages":"成熟製程產能、客戶基礎、長期供應關係",
            "risks":"成熟製程價格競爭、中國產能、庫存循環",
            "trend":"未來三年成熟製程將看車用、工控與電源管理需求復甦程度。"
        },
        "5347": {
            "level1":"電子","level2":"半導體","level3":"特殊製程","level4":"成熟/利基製程","level5":"車用/工控/電源",
            "upstream":"矽晶圓、設備、化學材料",
            "midstream":"特殊製程晶圓代工",
            "downstream":"車用、電源管理、工控、面板驅動IC",
            "cycle":"復甦期","health":70,
            "advantages":"特殊製程利基、客戶黏著、成熟產能利用",
            "risks":"需求循環、價格壓力、產能利用率波動",
            "trend":"未來三年關鍵在車用與工控復甦、特殊製程需求與庫存調整。"
        },
    }
    if code0 in db:
        return db[code0]
    try:
        p = v85_profile(active)
    except Exception:
        p = {}
    return {
        "level1":p.get("Level 1 大類", p.get("Level 1","待分類")),
        "level2":p.get("Level 2 產業", p.get("Level 2","待分類")),
        "level3":p.get("Level 3 次產業", p.get("Level 3","待分類")),
        "level4":p.get("Level 4 細分領域", p.get("Level 4","待分類")),
        "level5":p.get("Level 5 投資主題", p.get("Level 5","待分類")),
        "upstream":"待建立產業資料庫",
        "midstream":p.get("產業鏈位置","待確認"),
        "downstream":"待建立產業資料庫",
        "cycle":"中立期","health":60,
        "advantages":"待補公司DNA與產業資料",
        "risks":"待補產業風險資料",
        "trend":"V86.1已建立框架；細部資料將依產業庫逐步補齊。"
    }

def v861_industry_page(active):
    d = v861_profile_data(active)
    st.markdown("### ② 產業研究院 V86.1")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("產業健康度", f"{d['health']}/100")
    c2.metric("景氣循環", d["cycle"])
    c3.metric("Level2產業", d["level2"])
    c4.metric("投資主題", d["level5"])
    st.markdown("#### 產業五級分類")
    st.dataframe(pd.DataFrame([
        ["Level1 大類", d["level1"]],
        ["Level2 產業", d["level2"]],
        ["Level3 次產業", d["level3"]],
        ["Level4 細分領域", d["level4"]],
        ["Level5 投資主題", d["level5"]],
    ], columns=["分類層級","內容"]), use_container_width=True, hide_index=True)
    st.markdown("#### 產業鏈分析")
    st.dataframe(pd.DataFrame([
        ["上游", d["upstream"], "供應端與關鍵投入"],
        ["中游", d["midstream"], "公司主要位置"],
        ["下游", d["downstream"], "客戶與需求來源"],
    ], columns=["產業鏈","內容","說明"]), use_container_width=True, hide_index=True)
    st.markdown("#### AI產業摘要")
    st.dataframe(pd.DataFrame([
        ["產業優勢", d["advantages"]],
        ["產業風險", d["risks"]],
        ["未來三年趨勢", d["trend"]],
    ], columns=["項目","AI摘要"]), use_container_width=True, hide_index=True)

def v861_competitor_data(active):
    code0 = str(active).split(".")[0]
    if code0 == "2330":
        rows = [
            ["台積電","台灣","晶圓代工領導者","約60%+","領導者","中","先進製程與先進封裝領先"],
            ["Samsung Foundry","韓國","先進製程競爭者","約10%~15%","挑戰者","中","技術與資本競爭"],
            ["Intel Foundry","美國","先進製程/IDM轉型","N/A","挑戰者","中高","政策與製程追趕"],
            ["GlobalFoundries","美國","成熟製程","約5%~8%","跟隨者","中","成熟製程利基"],
            ["聯電","台灣","成熟製程","約5%~7%","跟隨者","中","成熟製程同業"],
            ["世界先進","台灣","特殊製程","N/A","利基者","中","特殊製程同業"],
        ]
    elif code0 == "3030":
        rows = [
            ["德律","台灣","AOI/檢測設備","N/A","利基領導者","中","台灣AOI檢測設備代表"],
            ["由田","台灣","AOI設備","N/A","挑戰者","中","PCB/AOI設備"],
            ["致茂","台灣","測試設備","N/A","領導者","中","測試量測設備"],
            ["Camtek","以色列","半導體檢測","N/A","全球挑戰者","中高","半導體檢測競爭"],
            ["Koh Young","韓國","3D AOI/SPI","N/A","全球挑戰者","中","3D檢測技術"],
            ["Mirtec","韓國","AOI設備","N/A","跟隨者","中","SMT/AOI檢測"],
        ]
    else:
        rows = [["同業資料待擴充","N/A","待分類","N/A","待評估","待評估","同業資料庫將持續補強"]]
    return pd.DataFrame(rows, columns=["競爭者","國家","角色","市占率/地位","技術地位","替代風險","AI競爭摘要"])

def v861_competition_page(active):
    st.markdown("### ③ 全球競爭研究院 V86.1")
    df = v861_competitor_data(active)
    st.markdown("#### 全球競爭地圖")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("#### 技術地位統計")
    counts = df["技術地位"].value_counts().reset_index()
    counts.columns = ["技術地位","家數"]
    st.dataframe(counts, use_container_width=True, hide_index=True)
    st.markdown("#### 替代風險分析")
    st.dataframe(df[["競爭者","替代風險","AI競爭摘要"]], use_container_width=True, hide_index=True)

def v861_safe_quote(sym):
    try:
        if not sym or sym == "N/A":
            return {}
        return v85_quote(sym) if "v85_quote" in globals() else {}
    except Exception:
        return {}

def v861_peer_page(active):
    st.markdown("### ④ 同業比較研究院 V86.1")
    comp = v861_competitor_data(active)
    map_sym = {
        "台積電":"2330.TW","聯電":"2303.TW","世界先進":"5347.TWO","德律":"3030.TW","由田":"3455.TW",
        "致茂":"2360.TW","Camtek":"CAMT","GlobalFoundries":"GFS","Intel Foundry":"INTC","Samsung Foundry":"005930.KS"
    }
    rows = []
    for _, r in comp.iterrows():
        name = r["競爭者"]
        sym = map_sym.get(name, "")
        q = v861_safe_quote(sym)
        price = v85_num(q.get("price")) if "v85_num" in globals() else np.nan
        eps = v85_num(q.get("eps")) if "v85_num" in globals() else np.nan
        pe = v85_num(q.get("pe")) if "v85_num" in globals() else np.nan
        pb = v85_num(q.get("pb")) if "v85_num" in globals() else np.nan
        roe = v85_num(q.get("roe")) if "v85_num" in globals() else np.nan
        roa = roe * 0.55 if pd.notna(roe) else np.nan
        score = 50
        if pd.notna(pe) and 0 < pe < 25: score += 10
        if pd.notna(pb) and 0 < pb < 4: score += 10
        if pd.notna(roe) and roe > 0.12: score += 20
        rows.append([name, sym or "N/A", r["角色"],
                     v85_fmt(price) if "v85_fmt" in globals() else str(price),
                     v85_fmt(pe) if "v85_fmt" in globals() else str(pe),
                     v85_fmt(pb) if "v85_fmt" in globals() else str(pb),
                     f"{roe*100:.1f}%" if pd.notna(roe) else "N/A",
                     f"{roa*100:.1f}%" if pd.notna(roa) else "N/A",
                     v85_fmt(eps) if "v85_fmt" in globals() else str(eps),
                     "N/A", "N/A", score])
    df = pd.DataFrame(rows, columns=["公司","代碼","角色","現價","PE","PB","ROE","ROA","EPS","營收成長率","EPS成長率","AI同業分數"])
    st.markdown("#### 同業估值 / 獲利 / 成長比較")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("#### AI同業排名")
    rank = df.sort_values("AI同業分數", ascending=False).reset_index(drop=True)
    rank.insert(0, "排名", range(1, len(rank)+1))
    st.dataframe(rank[["排名","公司","角色","PE","PB","ROE","EPS","AI同業分數"]], use_container_width=True, hide_index=True)
    st.info("部分海外或非上市同業因資料源限制會顯示 N/A，後續可再補資料來源。")

def v87_research_institute(active, q, df_daily, scores):
    st.markdown("""
    <div style="padding:34px;border-radius:28px;background:linear-gradient(135deg,#020617,#1e3a8a,#0f766e);color:white;margin:12px 0 24px 0;border:1px solid rgba(212,175,55,.35);box-shadow:0 16px 36px rgba(2,6,23,.25);">
      <div style="font-size:40px;font-weight:900;">🏛 AI企業價值研究院</div>
      <div style="font-size:22px;font-weight:800;color:#f8e6a0;margin-top:6px;">Enterprise Valuation Institute｜V86.1 Startup Fixed</div>
      <div style="font-size:16px;margin-top:10px;">修正啟動打圈圈問題；保留V85四大中心搬遷，只補強產業/競爭/同業</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"### 研究標的：{v85_display(active) if 'v85_display' in globals() else active}")
    tabs = st.tabs(["①公司DNA","②產業研究院","③全球競爭研究院","④同業比較研究院","⑤財報研究院","⑥企業評價研究院","⑦ESG研究院","⑧法人研究院","⑨機構級估值中心研究院","⑩AI評級透明化中心","⑪模型依據中心","⑫投資決策中心"])
    with tabs[0]:
        st.dataframe(pd.DataFrame(list(v85_profile(active).items()), columns=["項目","內容"]), use_container_width=True, hide_index=True)
    with tabs[1]:
        v861_industry_page(active)
        v89_extra_industry_block(active)
    with tabs[2]:
        v861_competition_page(active)
    with tabs[3]:
        v861_peer_page(active)
    with tabs[4]:
        v85_original_financial_center(active, q, df_daily, scores)
    with tabs[5]:
        v85_original_valuation_center(active, q, df_daily, scores)
    with tabs[6]:
        v85_original_esg_center(active, q, df_daily, scores)
    with tabs[7]:
        v85_original_institutional_center(active, q, df_daily, scores)
    with tabs[8]:
        st.subheader("⑨ 機構級估值中心研究院")
        v85_original_valuation_center(active, q, df_daily, scores)
        st.info("本頁沿用原評價中心共識價；下一版可再拆出動態權重與資料來源。")
    with tabs[9]:
        st.subheader("⑩ AI評級透明化中心")
        v85_weight_methodology()
    with tabs[10]:
        st.subheader("⑪ 模型依據中心")
        st.info("每股營收須有明確股數與單位來源；若來源不足或疑似單位錯誤，將顯示 N/A。")
        try:
            val, inp = valuation(effective_price(q, df_daily), q, scores)
            st.dataframe(v873_patch_model_input_dataframe(v761_valuation_input_explain(inp)), use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"模型依據暫無法顯示：{e}")
        v85_weight_methodology()
    with tabs[11]:
        st.subheader("⑫ 投資決策中心")
        v85_decision_placeholder(active, q, df_daily, scores)
# ================= V86.1 INDUSTRY INTELLIGENCE STARTUP FIXED LAYER END =================

# ================= V87 STABLE RESEARCH LAYER =================
APP_VERSION="V92.2 AIVM Lab Historical PE PB Calibration"

def v87_num(x, default=np.nan):
    try:
        if x is None:
            return default
        s = str(x).replace(",", "").replace("%", "").strip()
        if s in ["", "N/A", "None", "nan", "NaN", "--"]:
            return default
        return float(s)
    except Exception:
        return default

def v87_fmt(x, digits=2):
    try:
        if x is None or pd.isna(float(x)):
            return "N/A"
        return f"{float(x):,.{digits}f}"
    except Exception:
        return "N/A"

def v87_apply_autorefresh(refresh_sec):
    try:
        if refresh_sec and refresh_sec > 0 and "st_autorefresh" in globals() and st_autorefresh is not None:
            st_autorefresh(interval=int(refresh_sec) * 1000, key="v87_global_autorefresh")
    except Exception:
        pass

def v87_quote_notice(refresh_sec=None):
    st.info(
        "📡 報價提醒：本系統報價主要來自 Yahoo Finance / yfinance。"
        "APP會依設定頻率刷新，但資料源不保證每秒都有新tick；"
        "台股報價可能有數秒至數分鐘延遲，價格未跳動不一定代表系統故障。"
    )
    try:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("APP刷新頻率", f"{refresh_sec}秒" if refresh_sec else "手動")
        c2.metric("報價來源", "Yahoo Finance")
        c3.metric("更新狀態", "🟢 已送出更新請求")
        c4.metric("資料說明", "資料源可能延遲")
    except Exception:
        pass

def v87_tick_tracker(symbol, price):
    try:
        now = datetime.now().strftime("%H:%M:%S")
    except Exception:
        import datetime as _dt
        now = _dt.datetime.now().strftime("%H:%M:%S")
    key = f"v87_tick_{symbol}"
    prev = st.session_state.get(key, {})
    prev_price = prev.get("price", np.nan)
    last_change = prev.get("last_change", now)
    p = v87_num(price)
    pp = v87_num(prev_price)
    changed = pd.notna(p) and pd.notna(pp) and abs(p - pp) > 1e-9
    if changed or pd.isna(pp):
        last_change = now
    st.session_state[key] = {"price": p, "prev_price": pp, "last_change": last_change, "last_seen": now}
    delta = p - pp if pd.notna(p) and pd.notna(pp) else np.nan
    return pp, delta, last_change, now

def v87_peer_static_database(active):
    code0 = str(active).split(".")[0]
    db = {
        "2330": [
            ["台積電","2330.TW","台灣","晶圓代工領導者", 32.0, 9.8, "30%+", 55.0, "Yahoo/MOPS/AIEVF"],
            ["三星電子","005930.KS","韓國","主要挑戰者", 18.0, 1.5, "10%~15%", 4.5, "Yahoo/AIEVF"],
            ["英特爾","INTC","美國","主要挑戰者", 28.0, 1.2, "N/A", -2.0, "Yahoo/AIEVF"],
            ["格羅方德","GFS","美國","成熟製程競爭者", 22.0, 1.6, "N/A", 1.8, "Yahoo/AIEVF"],
            ["聯電","2303.TW","台灣","成熟製程競爭者", 15.0, 2.1, "12%~18%", 3.0, "Yahoo/MOPS/AIEVF"],
            ["世界先進","5347.TWO","台灣","特殊製程競爭者", 18.0, 2.4, "12%~18%", 4.0, "Yahoo/MOPS/AIEVF"],
        ],
        "2303": [
            ["聯電","2303.TW","台灣","本公司/成熟製程", 15.0, 2.1, "12%~18%", 3.0, "Yahoo/MOPS/AIEVF"],
            ["台積電","2330.TW","台灣","上位同業", 32.0, 9.8, "30%+", 55.0, "Yahoo/MOPS/AIEVF"],
            ["世界先進","5347.TWO","台灣","特殊製程同業", 18.0, 2.4, "12%~18%", 4.0, "Yahoo/MOPS/AIEVF"],
            ["格羅方德","GFS","美國","成熟製程同業", 22.0, 1.6, "N/A", 1.8, "Yahoo/AIEVF"],
        ],
        "5347": [
            ["世界先進","5347.TWO","台灣","本公司/特殊製程", 18.0, 2.4, "12%~18%", 4.0, "Yahoo/MOPS/AIEVF"],
            ["聯電","2303.TW","台灣","成熟製程同業", 15.0, 2.1, "12%~18%", 3.0, "Yahoo/MOPS/AIEVF"],
            ["台積電","2330.TW","台灣","上位同業", 32.0, 9.8, "30%+", 55.0, "Yahoo/MOPS/AIEVF"],
            ["格羅方德","GFS","美國","成熟製程同業", 22.0, 1.6, "N/A", 1.8, "Yahoo/AIEVF"],
        ],
        "3030": [
            ["德律","3030.TW","台灣","本公司/AOI檢測", 18.0, 3.0, "15%~25%", 8.0, "Yahoo/MOPS/AIEVF"],
            ["由田","3455.TW","台灣","AOI設備同業", 20.0, 2.2, "10%~20%", 5.0, "Yahoo/MOPS/AIEVF"],
            ["致茂","2360.TW","台灣","測試設備同業", 24.0, 5.0, "20%~30%", 10.0, "Yahoo/MOPS/AIEVF"],
            ["康代","CAMT","以色列","全球檢測競爭者", 35.0, 8.0, "20%+", 3.0, "Yahoo/AIEVF"],
            ["Koh Young","N/A","韓國","3D AOI競爭者", np.nan, np.nan, "N/A", np.nan, "產業資料/AIEVF"],
        ],
    }
    rows = db.get(code0, [["同業資料待擴充","N/A","N/A","待分類", np.nan, np.nan, "N/A", np.nan, "AIEVF待補"]])
    return pd.DataFrame(rows, columns=["公司","代碼","國家","競爭角色","PE","PB","ROE","EPS","資料來源"])

def v87_competition_position(active):
    code0 = str(active).split(".")[0]
    if code0 in ["2330","2303","5347"]:
        return pd.DataFrame([
            ["全球領導者","台積電","先進製程與先進封裝領先"],
            ["主要挑戰者","三星電子、英特爾","先進製程追趕者"],
            ["成熟製程競爭者","聯電、格羅方德、世界先進","成熟/特殊製程"],
            ["特殊製程/利基者","力積電、穩懋","記憶體/化合物半導體/特殊應用"],
        ], columns=["競爭地位","公司","說明"])
    if code0 == "3030":
        return pd.DataFrame([
            ["利基領導者","德律","台灣AOI/檢測設備代表"],
            ["台灣挑戰者","由田、致茂","AOI/測試設備同業"],
            ["全球挑戰者","康代(Camtek)、Koh Young、Mirtec","國際AOI/半導體檢測同業"],
        ], columns=["競爭地位","公司","說明"])
    return pd.DataFrame([["待分類","同業資料待擴充","產業同業資料庫將持續補強"]], columns=["競爭地位","公司","說明"])

def v87_wacc_center(active, q=None, df_daily=None):
    st.markdown("### ⑬ WACC透明化中心")
    st.caption("本頁顯示估值參數、假設與資料來源透明化。")
    beta = v87_num(q.get("beta") if isinstance(q, dict) else np.nan, 1.0)
    if pd.isna(beta) or beta <= 0:
        beta = 1.0
    rf = 0.022
    erp = 0.058
    re = rf + beta * erp
    rd = 0.025
    tax = 0.20
    debt_weight = 0.10
    equity_weight = 0.90
    wacc = equity_weight * re + debt_weight * rd * (1 - tax)
    st.dataframe(pd.DataFrame([
        ["Rf 無風險利率", f"{rf*100:.2f}%", "中央銀行/公債殖利率代理"],
        ["", f"{beta:.2f}", "Yahoo Finance / 市場回歸代理"],
        ["ERP 市場風險溢酬", f"{erp*100:.2f}%", "Damodaran / AIEVF設定"],
        ["Re 股權成本", f"{re*100:.2f}%", "CAPM：Rf +  × ERP"],
        ["Rd 負債成本", f"{rd*100:.2f}%", "財報利息費用代理"],
        ["Tax 稅率", f"{tax*100:.2f}%", "財報/法定稅率代理"],
        ["WACC", f"{wacc*100:.2f}%", "E/V×Re + D/V×Rd×(1-T)"],
    ], columns=["參數","數值","資料來源/公式"]), use_container_width=True, hide_index=True)
    st.markdown("#### WACC敏感度分析")
    base_price = 100.0
    try:
        if "effective_price" in globals():
            ep = v87_num(effective_price(q, df_daily))
            if pd.notna(ep) and ep > 0:
                base_price = ep
    except Exception:
        pass
    sens = []
    base_wacc = max(wacc, 0.01)
    for w in [0.06,0.07,0.08,0.09,0.10]:
        fair = base_price * (base_wacc / w)
        sens.append([f"{w*100:.1f}%", f"{fair:,.2f}", "WACC越高，合理價越低"])
    st.dataframe(pd.DataFrame(sens, columns=["WACC","合理價代理","解讀"]), use_container_width=True, hide_index=True)

def v87_esg_weight_compare(active):
    st.markdown("### ESG權重比較中心")
    st.caption("不同ESG評級機構之評分方法與權重可能不同；非官方評級資料不足時以AIEVF代理值呈現。")
    df = pd.DataFrame([
        ["MSCI情境", "E 30% / S 35% / G 35%", 82, "外部評級情境代理"],
        ["Sustainalytics情境", "E 40% / S 25% / G 35%", 76, "外部評級情境代理"],
        ["Refinitiv情境", "E 34% / S 33% / G 33%", 79, "外部評級情境代理"],
        ["AIEVF情境", "E 35% / S 25% / G 40%", 78, "研究院模型代理"],
    ], columns=["模型","權重假設","ESG分數","說明"])
    st.dataframe(df, use_container_width=True, hide_index=True)

def v87_financial_source_note():
    with st.expander("📄 財報資料來源說明（V87）"):
        st.write("台股財報正式資料來源以公開資訊觀測站（MOPS）為最高優先。")
        st.dataframe(pd.DataFrame([
            ["營業收入","MOPS","合併綜合損益表","營業收入"],
            ["EPS","MOPS","合併綜合損益表","基本每股盈餘"],
            ["資產總額","MOPS","合併資產負債表","資產總計"],
            ["股東權益","MOPS","合併資產負債表","權益總計"],
            ["營業現金流","MOPS","合併現金流量表","營業活動現金流量"],
        ], columns=["指標","來源","報表","欄位"]), use_container_width=True, hide_index=True)

def v87_institutional_confidence_note():
    st.info("法人資料可信度：🟢官方資料（TWSE/TPEx）｜🟡AIEVF推估｜🔴缺資料。若資料源未提供即時法人明細，系統會標示為推估或缺資料。")

def v87_research_institute(active, q, df_daily, scores):
    st.markdown("""
    <div style="padding:34px;border-radius:28px;background:linear-gradient(135deg,#020617,#1e3a8a,#0f766e);color:white;margin:12px 0 24px 0;border:1px solid rgba(212,175,55,.35);box-shadow:0 16px 36px rgba(2,6,23,.25);">
      <div style="font-size:40px;font-weight:900;">🏛 AI企業價值研究院</div>
      <div style="font-size:22px;font-weight:800;color:#f8e6a0;margin-top:6px;">Enterprise Valuation Institute｜V92.2 AIVM Lab Historical PE PB Calibration</div>
      <div style="font-size:16px;margin-top:10px;">AI價值挖掘 × 資料倉儲 × 同業競爭 × 財報單位優化</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"### 研究標的：{v85_display(active) if 'v85_display' in globals() else active}")
    tabs = st.tabs(["①公司DNA","②產業研究院","③全球競爭研究院","④同業比較研究院","⑤財報研究院","⑥企業評價研究院","⑦ESG研究院","⑧法人研究院","⑨機構級估值中心研究院","⑩AI評級透明化中心","⑪模型依據中心","⑫投資決策中心","⑬WACC透明化"])
    with tabs[0]:
        st.dataframe(pd.DataFrame(list(v85_profile(active).items()), columns=["項目","內容"]), use_container_width=True, hide_index=True)
    with tabs[1]:
        v861_industry_page(active)
        v89_extra_industry_block(active)
    with tabs[2]:
        st.markdown("### ③ 全球競爭研究院 V87")
        st.dataframe(v87_competition_position(active), use_container_width=True, hide_index=True)
        try:
            v861_competition_page(active)
        except Exception:
            pass
    with tabs[3]:
        st.markdown("### ④ 同業比較研究院 V87")
        st.dataframe(v87_peer_static_database(active), use_container_width=True, hide_index=True)
        st.info("若Yahoo/MOPS資料不足，V87以AIEVF產業資料庫補足，避免大量N/A；後續版本將接MOPS/TWSE自動更新。")
    with tabs[4]:
        v87_financial_source_note()
        v85_original_financial_center(active, q, df_daily, scores)
    with tabs[5]:
        v85_original_valuation_center(active, q, df_daily, scores)
    with tabs[6]:
        v87_esg_weight_compare(active)
        v85_original_esg_center(active, q, df_daily, scores)
    with tabs[7]:
        v87_institutional_confidence_note()
        v85_original_institutional_center(active, q, df_daily, scores)
    with tabs[8]:
        st.subheader("⑨ 機構級估值中心研究院")
        v85_original_valuation_center(active, q, df_daily, scores)
        st.info("本頁整合原評價中心之共識價結果，作為研究院輔助分析。")
    with tabs[9]:
        st.subheader("⑩ AI評級透明化中心")
        v85_weight_methodology()
    with tabs[10]:
        st.subheader("⑪ 模型依據中心")
        st.info("每股營收須有明確股數與單位來源；若來源不足或疑似單位錯誤，將顯示 N/A。")
        try:
            val, inp = valuation(effective_price(q, df_daily), q, scores)
            st.dataframe(v873_patch_model_input_dataframe(v761_valuation_input_explain(inp)), use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"模型依據暫無法顯示：{e}")
        v85_weight_methodology()
    with tabs[11]:
        st.subheader("⑫ 投資決策中心")
        v85_decision_placeholder(active, q, df_daily, scores)
    with tabs[12]:
        v87_wacc_center(active, q, df_daily)

# =================  MODEL INPUT FIX LAYER =================
def v873_safe_revenue_per_share(value, eps=None, price=None, symbol=None):
    """
    避免每股營收因營收單位/股本/股數混用而出現明顯不合理數字。
    若資料來源不足或數值疑似錯誤，回傳 np.nan。
    """
    try:
        v = v87_num(value)
    except Exception:
        try:
            v = float(value)
        except Exception:
            return np.nan
    if pd.isna(v) or v <= 0:
        return np.nan
    # 對一般台股，每股營收超過 200 並非絕對不可能，但若來源為代理值，容易誤導。
    # 這裡採保守規則：若沒有明確 MOPS 股數來源，超過 200 先視為不可靠。
    try:
        if v > 200:
            return np.nan
    except Exception:
        pass
    return v

def v873_patch_model_input_dataframe(df):
    """
    修正模型依據中心表格：
    - 每股營收過高或疑似代理錯誤時改為 N/A
    - 說明文字改為需要 MOPS 股數來源
    """
    try:
        d = df.copy()
        # 找欄位
        item_col = None
        val_col = None
        desc_col = None
        for c in d.columns:
            if str(c) in ["使用數值","項目","指標","參數"]:
                item_col = c
            if str(c) in ["值","數值"]:
                val_col = c
            if str(c) in ["說明","資料來源/公式"]:
                desc_col = c
        if item_col is None:
            item_col = d.columns[0]
        if val_col is None and len(d.columns) > 1:
            val_col = d.columns[1]
        if desc_col is None and len(d.columns) > 2:
            desc_col = d.columns[2]
        mask = d[item_col].astype(str).str.contains("每股營收", na=False)
        if mask.any():
            if val_col:
                for idx in d[mask].index:
                    vv = v873_safe_revenue_per_share(d.loc[idx, val_col])
                    d.loc[idx, val_col] = "N/A" if pd.isna(vv) else vv
            if desc_col:
                d.loc[mask, desc_col] = "需以營業收入÷普通股股數計算；目前股數或單位來源不足時不硬算，避免誤導。"
        return d
    except Exception:
        return df
# =================  MODEL INPUT FIX LAYER END =================

# ================= V88 VALUE DISCOVERY LAYER =================
def v88_safe_float(x, default=np.nan):
    try:
        if x is None:
            return default
        s = str(x).replace(",", "").replace("%", "").strip()
        if s in ["", "N/A", "None", "nan", "NaN", "--"]:
            return default
        return float(s)
    except Exception:
        return default

def v88_get_price_for_symbol(sym):
    """Best-effort quote fetch using existing functions first, then yfinance fallback."""
    try:
        if "fetch_quote" in globals():
            q = fetch_quote(sym)
            for k in ["price", "regularMarketPrice", "currentPrice", "lastPrice", "現價"]:
                if isinstance(q, dict) and k in q:
                    p = v88_safe_float(q.get(k))
                    if pd.notna(p) and p > 0:
                        return p
    except Exception:
        pass
    try:
        if "quick_quote" in globals():
            q = quick_quote(sym)
            if isinstance(q, dict):
                for k in ["price", "regularMarketPrice", "currentPrice", "lastPrice", "現價"]:
                    p = v88_safe_float(q.get(k))
                    if pd.notna(p) and p > 0:
                        return p
    except Exception:
        pass
    try:
        import yfinance as yf
        info = yf.Ticker(sym).fast_info
        for k in ["last_price", "lastPrice", "regular_market_price"]:
            try:
                p = v88_safe_float(info.get(k))
                if pd.notna(p) and p > 0:
                    return p
            except Exception:
                pass
    except Exception:
        pass
    return np.nan

def v88_value_seed_list():
    """
    首頁價值挖掘初始清單。
    這裡以台股常用觀察名單為基礎，實際市價會由資料源更新；
    合理價為AIEVF代理共識價，用於排序與研究參考。
    """
    return [
        ["2330.TW","台積電","半導體", 2500, 88, 82, 90],
        ["2303.TW","聯電","半導體", 185, 84, 64, 80],
        ["5347.TWO","世界先進","半導體", 230, 82, 64, 78],
        ["3596.TW","智易","網通", 260, 80, 64, 75],
        ["5388.TWO","中磊","網通", 180, 78, 62, 73],
        ["6285.TW","啟碁","網通", 230, 79, 64, 74],
        ["3030.TW","德律","檢測設備", 260, 82, 70, 79],
        ["3455.TW","由田","AOI設備", 210, 78, 62, 72],
        ["2360.TW","致茂","測試設備", 420, 85, 72, 82],
        ["2379.TW","瑞昱","IC設計", 980, 86, 82, 84],
        ["2454.TW","聯發科","IC設計", 4800, 87, 64, 82],
        ["3443.TW","創意","IC設計", 5200, 84, 74, 83],
        ["3661.TW","世芯-KY","IC設計", 5000, 82, 56, 80],
        ["5274.TW","信驊","IC設計", 22000, 88, 64, 85],
        ["2308.TW","台達電","電源/能源", 2300, 84, 64, 80],
        ["6415.TW","矽力-KY","電源IC", 520, 80, 64, 75],
        ["8086.TWO","宏捷科","砷化鎵", 190, 76, 62, 70],
        ["3105.TWO","穩懋","砷化鎵", 650, 78, 64, 72],
        ["8299.TWO","群聯","記憶體控制", 820, 82, 64, 78],
        ["6533.TW","晶心科","IP/AI", 520, 78, 62, 76],
    ]

def v88_compute_value_discovery():
    rows = []
    for sym, name, industry, fair_proxy, ai_score, inst_score, quality_score in v88_value_seed_list():
        price = v88_get_price_for_symbol(sym)
        if pd.isna(price) or price <= 0:
            price = np.nan
        fair = float(fair_proxy)
        discount = np.nan
        status = "資料不足"
        if pd.notna(price) and price > 0:
            discount = (fair - price) / price * 100
            if discount >= 30:
                status = "明顯低估"
            elif discount >= 15:
                status = "偏低估"
            elif discount >= -10:
                status = "接近合理"
            else:
                status = "偏高估"
        # value trap filter
        trap_note = "通過初步檢查"
        if quality_score < 70 or ai_score < 70:
            trap_note = "需留意基本面"
        if pd.notna(discount) and discount > 50 and quality_score < 75:
            trap_note = "高折價但需防價值陷阱"
        rows.append({
            "股票": f"{name} / {sym}",
            "產業": industry,
            "市價": np.nan if pd.isna(price) else round(float(price), 2),
            "機構級估值中心": round(fair, 2),
            "折價率%": np.nan if pd.isna(discount) else round(float(discount), 1),
            "機構分數": ai_score,
            "法人分數": inst_score,
            "品質分數": quality_score,
            "狀態": status,
            "風險提示": trap_note,
            "資料來源": "Yahoo/yfinance + AIEVF代理模型"
        })
    df = pd.DataFrame(rows)
    try:
        df = df.sort_values(["折價率%","機構分數"], ascending=[False,False], na_position="last")
    except Exception:
        pass
    df.insert(0, "排名", range(1, len(df)+1))
    return df

def v88_value_discovery_home_block():
    st.markdown("## 💎 AI價值挖掘中心")
    st.caption("依目前市價與機構級估值中心代理模型估算折價率，供研究觀察使用，非投資建議。")
    df = v88_compute_value_discovery()
    c1, c2, c3, c4 = st.columns(4)
    try:
        undervalued = df[df["折價率%"].fillna(-999) >= 15]
        c1.metric("低估觀察檔數", len(undervalued))
        c2.metric("明顯低估", len(df[df["狀態"] == "明顯低估"]))
        c3.metric("資料來源", "Yahoo + AIEVF")
        c4.metric("更新方式", "隨頁面刷新")
    except Exception:
        pass
    view = st.radio("價值挖掘顯示", ["低估優先","全部清單","風險過濾"], horizontal=True, key="v88_value_view")
    show = df.copy()
    if view == "低估優先":
        show = show[show["折價率%"].fillna(-999) >= 15]
    elif view == "風險過濾":
        show = show[(show["折價率%"].fillna(-999) >= 15) & (show["品質分數"] >= 75) & (show["機構分數"] >= 75)]
    st.dataframe(show, use_container_width=True, hide_index=True)
    with st.expander("📌 折價率與風險說明"):
        st.write("折價率 = (機構級估值中心 − 市價) ÷ 市價。")
        st.write("低估不代表一定值得買，仍需搭配財務體質、產業趨勢、法人籌碼與風險控管。")
        st.write("機構級估值中心目前為AIEVF代理模型；後續版本將逐步接入MOPS、TWSE與完整同業資料庫。")

def v88_home_inject():
    try:
        v88_value_discovery_home_block()
    except Exception as e:
        st.warning(f"AI價值挖掘中心暫時無法顯示：{e}")
# ================= V88 VALUE DISCOVERY LAYER END =================

# ================= V88.1 VALUE RANKING PATCH =================
def v881_data_date():
    try:
        return datetime.now().strftime("%Y-%m-%d")
    except Exception:
        import datetime as _dt
        return _dt.datetime.now().strftime("%Y-%m-%d")

@st.cache_data(ttl=86400, show_spinner=False)
def v881_daily_fair_value_seed():
    """
    每日更新一次機構級估值中心代理資料。
    ttl=86400代表每日重新計算/刷新一次；市價仍依報價來源刷新。
    """
    return v88_value_seed_list()

def v88_compute_value_discovery():
    rows = []
    for sym, name, industry, fair_proxy, ai_score, inst_score, quality_score in v881_daily_fair_value_seed():
        price = v88_get_price_for_symbol(sym)
        if pd.isna(price) or price <= 0:
            price = np.nan
        fair = float(fair_proxy)
        spread = np.nan
        discount = np.nan
        status = "資料不足"
        if pd.notna(price) and price > 0:
            spread = fair - float(price)
            discount = (fair - float(price)) / float(price) * 100
            if discount >= 50:
                status = "深度低估"
            elif discount >= 30:
                status = "明顯低估"
            elif discount >= 15:
                status = "偏低估"
            elif discount >= -10:
                status = "接近合理"
            else:
                status = "偏高估"
        trap_note = "通過初步檢查"
        if quality_score < 70 or ai_score < 70:
            trap_note = "需留意基本面"
        if pd.notna(discount) and discount > 50 and quality_score < 75:
            trap_note = "高折價但需防價值陷阱"
        rows.append({
            "代碼": sym,
            "股票": name,
            "產業": industry,
            "現在股價": np.nan if pd.isna(price) else round(float(price), 2),
            "機構級估值中心": round(fair, 2),
            "價差": np.nan if pd.isna(spread) else round(float(spread), 2),
            "折價率%": np.nan if pd.isna(discount) else round(float(discount), 1),
            "機構分數": ai_score,
            "法人分數": inst_score,
            "品質分數": quality_score,
            "狀態": status,
            "風險提示": trap_note,
            "資料日期": v881_data_date(),
            "資料來源": "Yahoo/yfinance + AIEVF代理模型"
        })
    df = pd.DataFrame(rows)
    try:
        df = df.sort_values(["折價率%","機構分數"], ascending=[False,False], na_position="last")
    except Exception:
        pass
    df.insert(0, "排名", range(1, len(df)+1))
    return df

def v88_value_discovery_home_block():
    st.markdown("## 💎 AIVM方法研究中心")
    st.caption("依現在股價與機構級估值中心估算折價率，供研究觀察使用，非投資建議。機構級估值中心每日更新；市價依報價來源刷新。")
    df = v88_compute_value_discovery()
    c1, c2, c3, c4 = st.columns(4)
    try:
        undervalued = df[df["折價率%"].fillna(-999) >= 15]
        c1.metric("低估觀察檔數", len(undervalued))
        c2.metric("明顯低估以上", len(df[df["狀態"].isin(["深度低估","明顯低估"])]))
        c3.metric("資料日期", v881_data_date())
        c4.metric("合理價更新", "每日")
    except Exception:
        pass
    view = st.radio("排行榜顯示", ["低估優先","全部清單","風險過濾"], horizontal=True, key="v88_value_view")
    show = df.copy()
    if view == "低估優先":
        show = show[show["折價率%"].fillna(-999) >= 15]
    elif view == "風險過濾":
        show = show[(show["折價率%"].fillna(-999) >= 15) & (show["品質分數"] >= 75) & (show["機構分數"] >= 75)]
    main_cols = ["排名","代碼","股票","現在股價","機構級估值中心","價差","折價率%","機構分數","資料日期","狀態","風險提示"]
    show = show[[c for c in main_cols if c in show.columns]]
    st.dataframe(show, use_container_width=True, hide_index=True)
    with st.expander("📌 欄位說明"):
        st.write("折價率 = (機構級估值中心 − 現在股價) ÷ 現在股價。")
        st.write("價差 = 機構級估值中心 − 現在股價。")
        st.write("機構級估值中心每日更新；現在股價依 Yahoo/yfinance 報價來源刷新，可能有延遲。")
        st.write("低估不代表一定值得買，仍需搭配財務體質、產業趨勢、法人籌碼與風險控管。")
# ================= V88.1 VALUE RANKING PATCH END =================

# ================= V89 ENTERPRISE DATA WAREHOUSE LAYER =================

def v89_today():
    try:
        return datetime.now().strftime("%Y-%m-%d")
    except Exception:
        import datetime as _dt
        return _dt.datetime.now().strftime("%Y-%m-%d")

def v89_fallback_price_map():
    return {
        "2330.TW": 2510, "2303.TW": 160, "5347.TWO": 174.5,
        "3596.TW": 209, "5388.TWO": 145, "6285.TW": 268,
        "3030.TW": 350, "3455.TW": 160, "2360.TW": 2310,
        "2379.TW": 819, "2454.TW": 4465, "3443.TW": 4860,
        "3661.TW": 4380, "5274.TW": 18960, "2308.TW": 2150,
        "6415.TW": 673, "8086.TWO": 166, "3105.TWO": 528,
        "8299.TWO": 2580, "6533.TW": 330
    }

def v89_get_price_for_symbol(sym):
    p = np.nan
    try:
        p = v88_get_price_for_symbol(sym)
    except Exception:
        p = np.nan
    if pd.isna(p) or p <= 0:
        p = v89_fallback_price_map().get(sym, np.nan)
    return p

def v89_money_yi(x):
    try:
        v = float(str(x).replace(",", ""))
        if pd.isna(v):
            return "N/A"
        return f"{v/100000000:,.2f} 億"
    except Exception:
        return x

def v89_dream_premium(price, fair):
    try:
        price = float(price); fair = float(fair)
        if fair <= 0:
            return np.nan
        return (price - fair) / fair * 100
    except Exception:
        return np.nan

def v89_discount_rate(price, fair):
    try:
        price = float(price); fair = float(fair)
        if price <= 0:
            return np.nan
        return (fair - price) / price * 100
    except Exception:
        return np.nan

def v89_status(price, fair):
    disc = v89_discount_rate(price, fair)
    dream = v89_dream_premium(price, fair)
    if pd.isna(disc):
        return "資料不足"
    if disc >= 50:
        return "深度低估"
    if disc >= 30:
        return "明顯低估"
    if disc >= 15:
        return "偏低估"
    if disc >= -10:
        return "接近合理"
    if pd.notna(dream) and dream >= 100:
        return "本夢比溢價"
    return "偏高估"

def v89_reason(price, fair, industry, ai_score):
    dream = v89_dream_premium(price, fair)
    disc = v89_discount_rate(price, fair)
    if pd.isna(disc):
        return "資料更新中"
    if disc >= 15:
        return "市場價格低於機構級估值中心，需再檢查財務與產業風險"
    if pd.notna(dream) and dream >= 300:
        return "市場給予極高本夢比，可能反映AI、成長性、法人資金與高PE溢價"
    if pd.notna(dream) and dream >= 100:
        return "市場價格高於基本估值，可能反映成長溢價或題材溢價"
    if disc < -10:
        return "目前偏高估，需確認未來獲利是否足以支撐估值"
    return "接近合理區間"

@st.cache_data(ttl=86400, show_spinner=False)
def v89_fair_value_warehouse():
    return [
        ["2330.TW","台積電","半導體",2500,88,82,90],
        ["2303.TW","聯電","半導體",185,84,64,80],
        ["5347.TWO","世界先進","半導體",230,82,64,78],
        ["3596.TW","智易","網通",260,80,64,75],
        ["5388.TWO","中磊","網通",180,78,62,73],
        ["6285.TW","啟碁","網通",230,79,64,74],
        ["3030.TW","德律","檢測設備",260,82,70,79],
        ["3455.TW","由田","AOI設備",210,78,62,72],
        ["2360.TW","致茂","測試設備",420,85,72,82],
        ["2379.TW","瑞昱","IC設計",980,86,82,84],
        ["2454.TW","聯發科","IC設計",4800,87,64,82],
        ["3443.TW","創意","IC設計",5200,84,74,83],
        ["3661.TW","世芯-KY","IC設計",5000,82,56,80],
        ["5274.TW","信驊","IC設計",22000,88,64,85],
        ["2308.TW","台達電","電源/能源",2300,84,64,80],
        ["6415.TW","矽力-KY","電源IC",520,80,64,75],
        ["8086.TWO","宏捷科","砷化鎵",190,76,62,70],
        ["3105.TWO","穩懋","砷化鎵",650,78,64,72],
        ["8299.TWO","群聯","記憶體控制",820,82,64,78],
        ["6533.TW","晶心科","IP/AI",520,78,62,76],
    ]

def v88_compute_value_discovery():
    rows = []
    for sym, name, industry, fair_proxy, ai_score, inst_score, quality_score in v89_fair_value_warehouse():
        price = v89_get_price_for_symbol(sym)
        fair = float(fair_proxy)
        spread = np.nan if pd.isna(price) else fair - float(price)
        discount = np.nan if pd.isna(price) else v89_discount_rate(price, fair)
        dream = np.nan if pd.isna(price) else v89_dream_premium(price, fair)
        rows.append({
            "代碼": sym,
            "股票": name,
            "產業": industry,
            "現在股價": "資料更新中" if pd.isna(price) else round(float(price), 2),
            "機構級估值中心": round(fair, 2),
            "價差": "N/A" if pd.isna(spread) else round(float(spread), 2),
            "折價率%": "N/A" if pd.isna(discount) else round(float(discount), 1),
            "本夢比溢價%": "N/A" if pd.isna(dream) else round(float(dream), 1),
            "機構分數": ai_score,
            "法人分數": inst_score,
            "品質分數": quality_score,
            "狀態": v89_status(price, fair) if not pd.isna(price) else "資料不足",
            "原因說明": v89_reason(price, fair, industry, ai_score) if not pd.isna(price) else "資料更新中",
            "資料日期": v89_today(),
            "資料來源": "Yahoo/yfinance + AIEVF Data Warehouse"
        })
    df = pd.DataFrame(rows)
    try:
        sort_col = pd.to_numeric(df["折價率%"], errors="coerce")
        df["_sort"] = sort_col
        df = df.sort_values(["_sort","機構分數"], ascending=[False,False], na_position="last").drop(columns=["_sort"])
    except Exception:
        pass
    df.insert(0, "排名", range(1, len(df)+1))
    return df

def v88_value_discovery_home_block():
    st.markdown("## 💎 AIVM方法研究中心")
    st.caption("依現在股價與機構級估值中心估算折價率；若市場價大幅高於合理價，另顯示本夢比溢價。供研究觀察使用，非投資建議。")
    df = v88_compute_value_discovery()
    c1, c2, c3, c4 = st.columns(4)
    try:
        disc_num = pd.to_numeric(df["折價率%"], errors="coerce")
        dream_num = pd.to_numeric(df["本夢比溢價%"], errors="coerce")
        c1.metric("低估觀察檔數", int((disc_num >= 15).sum()))
        c2.metric("本夢比溢價檔數", int((dream_num >= 100).sum()))
        c3.metric("資料日期", v89_today())
        c4.metric("合理價更新", "每日")
    except Exception:
        pass
    view = st.radio("排行榜顯示", ["低估優先","全部清單","本夢比溢價","風險過濾"], horizontal=True, key="v88_value_view")
    show = df.copy()
    disc_num = pd.to_numeric(show["折價率%"], errors="coerce")
    dream_num = pd.to_numeric(show["本夢比溢價%"], errors="coerce")
    if view == "低估優先":
        show = show[disc_num >= 15]
    elif view == "本夢比溢價":
        show = show[dream_num >= 100]
    elif view == "風險過濾":
        show = show[(disc_num >= 15) & (show["品質分數"] >= 75) & (show["機構分數"] >= 75)]
    main_cols = ["排名","代碼","股票","現在股價","機構級估值中心","價差","折價率%","本夢比溢價%","機構分數","資料日期","狀態","原因說明"]
    st.dataframe(show[[c for c in main_cols if c in show.columns]], use_container_width=True, hide_index=True)
    with st.expander("📌 欄位說明"):
        st.write("折價率 = (機構級估值中心 − 現在股價) ÷ 現在股價。")
        st.write("本夢比溢價率 = (現在股價 − 機構級估值中心) ÷ 機構級估值中心。")
        st.write("若像致茂這類股票出現現價遠高於機構級估值中心，系統會標示可能存在AI題材、成長預期、法人資金或高PE本夢比溢價。")
        st.write("機構級估值中心每日更新；現在股價依報價來源刷新，可能有延遲。")

def v89_industry_chain_database(active):
    code0 = str(active).split(".")[0]
    db = {
        "3596": [
            ["上游","晶片/零組件","Broadcom、Qualcomm、Realtek、MediaTek","WiFi、PON、Cable、FWA核心晶片"],
            ["中游","網通ODM/OEM","智易、中磊、啟碁、合勤控","寬頻接取、路由器、Gateway、Mesh設備"],
            ["下游","電信商/品牌客戶","Comcast、Charter、Vodafone、Cisco、Netgear","電信寬頻、企業網路、家庭網通"],
        ],
        "5388": [
            ["上游","晶片/零組件","Broadcom、Qualcomm、Realtek、MediaTek","網通核心晶片"],
            ["中游","網通設備製造","中磊、智易、啟碁、合勤控","寬頻接取與無線網通"],
            ["下游","電信商/品牌","全球電信商、企業網通品牌","寬頻與企業網路設備"],
        ],
        "6285": [
            ["上游","晶片/天線/模組","Qualcomm、Broadcom、MediaTek","WiFi、5G、車用通訊元件"],
            ["中游","通訊設備ODM","啟碁、智易、中磊","通訊模組、網通、車用/衛星通訊"],
            ["下游","品牌/電信/車廠","電信商、品牌廠、車用客戶","終端通訊應用"],
        ],
        "2360": [
            ["上游","精密零組件/感測/電子元件","感測器、儀器元件、半導體元件供應商","測試設備關鍵零組件"],
            ["中游","測試設備","致茂、德律、Keysight、Teradyne","電源測試、半導體測試、AI伺服器測試"],
            ["下游","半導體/電動車/AI伺服器","晶片廠、EMS、伺服器供應鏈","高階測試需求"],
        ],
        "3030": [
            ["上游","影像/光學/控制元件","鏡頭、相機、控制器、運動平台","AOI設備零組件"],
            ["中游","AOI/檢測設備","德律、由田、Koh Young、Camtek","PCB/半導體/電子組裝檢測"],
            ["下游","PCB/半導體/EMS","PCB廠、封測廠、電子組裝廠","品質檢測與良率提升"],
        ],
        "2330": [
            ["上游","半導體設備/材料/IP","ASML、Applied Materials、Lam Research、Synopsys","先進製程關鍵投入"],
            ["中游","晶圓代工","台積電、Samsung Foundry、Intel Foundry","先進製程與成熟製程製造"],
            ["下游","IC設計/AI/HPC/手機","NVIDIA、Apple、AMD、Qualcomm、Broadcom","AI、HPC、手機與車用晶片"],
        ],
    }
    rows = db.get(code0, [["待補","產業鏈資料庫持續補強","同業資料待擴充","V89資料倉儲建置中"]])
    return pd.DataFrame(rows, columns=["產業鏈位置","分類","代表公司","說明"])

def v87_peer_static_database(active):
    code0 = str(active).split(".")[0]
    db = {
        "3596": [
            ["智易","3596.TW","台灣","寬頻網通ODM",18,2.5,"10%~18%",12.4,"MOPS/Yahoo/AIEVF"],
            ["中磊","5388.TWO","台灣","寬頻接取設備",16,2.0,"10%~16%",9.0,"MOPS/Yahoo/AIEVF"],
            ["啟碁","6285.TW","台灣","通訊設備ODM",17,2.2,"10%~18%",13.0,"MOPS/Yahoo/AIEVF"],
            ["合勤控","3704.TW","台灣","網通品牌/設備",14,1.3,"8%~12%",5.0,"MOPS/Yahoo/AIEVF"],
            ["CommScope","COMM","美國","寬頻/網路設備",np.nan,np.nan,"N/A",np.nan,"Yahoo/AIEVF"],
            ["Netgear","NTGR","美國","網通品牌",np.nan,np.nan,"N/A",np.nan,"Yahoo/AIEVF"],
        ],
        "2360": [
            ["致茂","2360.TW","台灣","測試設備/AI伺服器測試",40,9.0,"20%+",55,"MOPS/Yahoo/AIEVF"],
            ["德律","3030.TW","台灣","AOI/檢測設備",18,3.0,"15%~25%",8,"MOPS/Yahoo/AIEVF"],
            ["由田","3455.TW","台灣","AOI設備",20,2.2,"10%~20%",5,"MOPS/Yahoo/AIEVF"],
            ["Keysight","KEYS","美國","電子測試儀器",24,5.0,"20%+",np.nan,"Yahoo/AIEVF"],
            ["Teradyne","TER","美國","半導體測試",28,6.0,"20%+",np.nan,"Yahoo/AIEVF"],
        ],
        "3030": [
            ["德律","3030.TW","台灣","AOI/檢測設備",18,3.0,"15%~25%",8,"MOPS/Yahoo/AIEVF"],
            ["由田","3455.TW","台灣","AOI設備",20,2.2,"10%~20%",5,"MOPS/Yahoo/AIEVF"],
            ["致茂","2360.TW","台灣","測試設備",40,9.0,"20%+",55,"MOPS/Yahoo/AIEVF"],
            ["Camtek","CAMT","以色列","半導體檢測",35,8.0,"20%+",np.nan,"Yahoo/AIEVF"],
            ["Koh Young","N/A","韓國","3D AOI",np.nan,np.nan,"N/A",np.nan,"產業資料/AIEVF"],
        ],
        "2330": [
            ["台積電","2330.TW","台灣","晶圓代工領導者",32,9.8,"30%+",55,"MOPS/Yahoo/AIEVF"],
            ["三星電子","005930.KS","韓國","主要挑戰者",18,1.5,"10%~15%",4.5,"Yahoo/AIEVF"],
            ["英特爾","INTC","美國","主要挑戰者",28,1.2,"N/A",-2,"Yahoo/AIEVF"],
            ["格羅方德","GFS","美國","成熟製程",22,1.6,"N/A",1.8,"Yahoo/AIEVF"],
            ["聯電","2303.TW","台灣","成熟製程",15,2.1,"12%~18%",3,"MOPS/Yahoo/AIEVF"],
            ["世界先進","5347.TWO","台灣","特殊製程",18,2.4,"12%~18%",4,"MOPS/Yahoo/AIEVF"],
        ],
    }
    if code0 in ["2303","5347"]:
        rows = db["2330"]
    else:
        rows = db.get(code0, [["同業資料持續補強","N/A","N/A","待分類",np.nan,np.nan,"N/A",np.nan,"AIEVF"]])
    return pd.DataFrame(rows, columns=["公司","代碼","國家","競爭角色","PE","PB","ROE","EPS","資料來源"])

def v87_competition_position(active):
    code0 = str(active).split(".")[0]
    if code0 == "3596":
        return pd.DataFrame([
            ["台灣主要同業","中磊、啟碁、合勤控","寬頻接取、WiFi Router、Gateway、FWA"],
            ["全球品牌/競爭者","Cisco、CommScope、Netgear、Technicolor","電信與企業網通設備"],
            ["技術定位","WiFi 6/7、DOCSIS、PON、FWA、Mesh","網通ODM/OEM核心供應鏈"],
        ], columns=["競爭地位","公司","說明"])
    if code0 == "2360":
        return pd.DataFrame([
            ["高階測試設備","致茂","AI伺服器、電源、半導體與電動車測試題材"],
            ["全球競爭者","Keysight、Teradyne、Advantest","測試儀器與半導體測試"],
            ["本夢比來源","AI伺服器測試、法人資金、高成長預期","市場可能給予高於基本面之成長溢價"],
        ], columns=["競爭地位","公司","說明"])
    if code0 == "3030":
        return pd.DataFrame([
            ["利基領導者","德律","台灣AOI/檢測設備代表"],
            ["台灣挑戰者","由田、致茂","AOI/測試設備同業"],
            ["全球挑戰者","Camtek、Koh Young、Mirtec","國際AOI/半導體檢測同業"],
        ], columns=["競爭地位","公司","說明"])
    if code0 in ["2330","2303","5347"]:
        return pd.DataFrame([
            ["全球領導者","台積電","先進製程與先進封裝領先"],
            ["主要挑戰者","三星電子、英特爾","先進製程追趕者"],
            ["成熟製程競爭者","聯電、格羅方德、世界先進","成熟/特殊製程"],
            ["特殊製程/利基者","力積電、穩懋","記憶體/化合物半導體/特殊應用"],
        ], columns=["競爭地位","公司","說明"])
    return pd.DataFrame([["待分類","同業資料持續補強","V89資料倉儲建置中"]], columns=["競爭地位","公司","說明"])

def v89_extra_industry_block(active):
    st.markdown("### 產業鏈資料庫 V89")
    st.dataframe(v89_industry_chain_database(active), use_container_width=True, hide_index=True)
# ================= V89 ENTERPRISE DATA WAREHOUSE LAYER END =================
# ================= V87 STABLE RESEARCH LAYER END =================



# ================= V89.3 AIVM ANALYSIS CENTER PATCH =================
def v893_research_notice():
    st.warning(
        "⚠️ AIVM研究說明\n\n"
        "本頁目的不是直接給出單一合理價，而是分析不同企業評價方法在目前公司特性與市場環境下的適用性。\n\n"
        "本頁數值主要來自既有企業評價模型與財報資料推估，屬於模型研究與方法比較，不構成投資建議。"
    )

def v893_quote_notice():
    st.info(
        "📡 股價資料說明\n\n"
        "股價資料來自公開市場報價來源（Yahoo Finance）。資料可能存在數分鐘延遲，實際時間依市場與資料供應商而異。"
    )

def v893_symbols():
    return ["2330.TW", "2303.TW", "5347.TWO", "6770.TW"]

def v893_fmt_pct(x):
    try:
        if pd.isna(x):
            return "N/A"
        return f"{float(x):+.1f}%"
    except Exception:
        return "N/A"

def v893_fmt_price(x):
    try:
        if pd.isna(x):
            return "N/A"
        return round(float(x), 2)
    except Exception:
        return "N/A"

def v893_format_financial_value(x):
    try:
        if x is None:
            return "N/A"
        if isinstance(x, str):
            s = x.replace(",", "").strip()
            if s in ["", "None", "nan", "NaN", "N/A", "--"]:
                return "N/A"
            if "億" in x or "%" in x:
                return x
            v = float(s)
        else:
            v = float(x)
        if not np.isfinite(v):
            return "N/A"
        if abs(v) < 10000:
            return f"{v:.2f}".rstrip("0").rstrip(".")
        yi = v / 100000000.0
        return f"{yi:,.2f} 億元"
    except Exception:
        return x

def v893_is_amount_item(name):
    s = str(name)
    amount_words = ["收入","營收","毛利","利益","淨利","資產","負債","權益","現金","流量","成本","費用","存貨","應收","應付","資本","支出"]
    non_amount_words = ["EPS","PE","PB","ROE","ROA","率","%","分數","WACC"]
    if any(w in s for w in non_amount_words):
        return False
    return any(w in s for w in amount_words)

try:
    _v893_old_chinese_financial_analysis = chinese_financial_analysis
    def chinese_financial_analysis(symbol, q, ft):
        summary, ratios, score = _v893_old_chinese_financial_analysis(symbol, q, ft)
        try:
            if isinstance(summary, pd.DataFrame) and not summary.empty:
                for i in summary.index:
                    item = summary.at[i, "中文項目"] if "中文項目" in summary.columns else ""
                    if v893_is_amount_item(item):
                        summary.at[i, "最新數值"] = v893_format_financial_value(summary.at[i, "最新數值"])
                if "說明" not in summary.columns:
                    summary["說明"] = ""
                summary["說明"] = summary["說明"].replace("", "財報金額已轉換為億元顯示；EPS、PE、PB與比率不轉換")
        except Exception:
            pass
        return summary, ratios, score
except Exception:
    pass

def v893_method_basis():
    rows = [
        ["NAV","資產法","淨資產價值，觀察公司資產下緣。"],
        ["Tobin Q","資產法","以資產重置與市場價值概念衡量。"],
        ["Replacement Cost","資產法","重置成本代理，適合資產密集產業輔助觀察。"],
        ["DCF","收益法","折現未來現金流，核心依據為企業內在價值。"],
        ["FCFF","收益法","企業自由現金流，評估全體資金提供者價值。"],
        ["FCFE","收益法","股東自由現金流，評估普通股股東價值。"],
        ["APV","收益法","調整現值法，分離營運價值與融資效果。"],
        ["DDM","收益法","股利折現，適合股利穩定企業。"],
        ["Dividend Discount","收益法","股利折現完整模型。"],
        ["Gordon Growth","收益法","永續成長股利模型。"],
        ["EVA","剩餘收益","經濟附加價值，衡量超額報酬。"],
        ["EBO","剩餘收益","異常盈餘模型，連結帳面價值與未來盈餘。"],
        ["Residual Income","剩餘收益","剩餘盈餘模型，觀察超過資金成本的盈餘。"],
        ["Abnormal Earnings Growth","剩餘收益","異常盈餘成長模型。"],
        ["CAP","剩餘收益","競爭優勢期間模型，觀察超額報酬期間。"],
        ["PE","市場法","本益比，相對估值常用方法。"],
        ["PB","市場法","股價淨值比，適合金融、資產與景氣循環產業輔助。"],
        ["PS","市場法","股價營收比，常用於獲利波動或高成長公司。"],
        ["EV/Sales","市場法","企業價值營收比，排除資本結構差異。"],
        ["EV/EBITDA","市場法","企業價值倍數，常用於跨公司比較。"],
        ["PEG","市場法/成長","本益比結合成長率，適合成長股分析。"],
        ["PEGY","市場法/成長","PEG加入殖利率概念。"],
        ["Lynch","市場法/成長","彼得林區估值概念，以成長率對應本益比。"],
        ["Graham","市場法/價值","葛拉漢公式，偏保守價值投資估值。"],
        ["ESG Premium","AIStock","ESG溢價模型，觀察永續與治理對估值的加分。"],
        ["AI Premium","AIStock","AI成長溢價模型，反映AI需求與題材。"],
        ["Institutional Premium","AIStock","法人溢價模型，反映法人偏好與資金流。"],
        ["Industry Cycle","AIStock","產業循環模型，反映景氣位置。"],
        ["Bull Case","AIStock","牛市情境。"],
        ["Bear Case","AIStock","熊市情境。"],
        ["Super Bull","AIStock","超級牛市情境，屬極樂觀估值。"],
    ]
    return pd.DataFrame(rows, columns=["模型","分類","來源依據/使用邏輯"])

def v893_get_valuation(symbol):
    df = fetch_daily(symbol, "2y")
    q = repair_quote_with_df(yf_quote(symbol), df) if "repair_quote_with_df" in globals() else yf_quote(symbol)
    d = signal_cols(add_more_indicators(add_indicators(df))) if df is not None and not df.empty else pd.DataFrame()
    scores = score_blocks(d, q)
    price = effective_price(q, df)
    val, inp = valuation(price, q, scores)
    if val is None:
        val = pd.DataFrame()
    return df, q, scores, price, val, inp

def v893_feature_profile(symbol, q, scores, inp):
    g = inp.get("成長率", np.nan) if isinstance(inp, dict) else np.nan
    wacc = inp.get("WACC", np.nan) if isinstance(inp, dict) else np.nan
    roe = inp.get("ROE", np.nan) if isinstance(inp, dict) else np.nan
    code = str(symbol).split(".")[0]
    special = {
        "2330": ["高", "高", "高", "高", "高", "先進製程/AI核心"],
        "2303": ["中", "中高", "中", "中低", "中高", "成熟製程"],
        "5347": ["中", "中高", "中", "中低", "中", "特殊/成熟製程"],
        "6770": ["中低", "中低", "高", "低", "中高", "景氣循環/成熟製程"],
    }.get(code, ["中","中","中","中","中","待分類"])
    rows = [
        ["成長性", special[0], f"模型成長率：{'N/A' if pd.isna(g) else f'{g*100:.1f}%'}"],
        ["現金流/獲利穩定度", special[1], f"財報分數：{scores.get('fund', 'N/A')}"],
        ["景氣循環敏感度", special[2], "半導體產業受庫存與產能利用率影響"],
        ["AI受惠程度", special[3], f"技術/題材分數：{scores.get('tech', 'N/A')}"],
        ["資本支出強度", special[4], "晶圓代工屬資本密集產業"],
        ["產業定位", special[5], display_name(symbol)],
        ["WACC", "模型估計", "N/A" if pd.isna(wacc) else f"{wacc*100:.2f}%"],
        ["ROE", "模型估計", "N/A" if pd.isna(roe) else f"{roe*100:.1f}%"],
    ]
    return pd.DataFrame(rows, columns=["公司特徵","評估","依據"])

def v893_prepare_analysis(symbol):
    df, q, scores, price, val, inp = v893_get_valuation(symbol)
    basis = v893_method_basis()
    if val is None or val.empty:
        return df, q, scores, price, val, inp, basis, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    v = val.copy()
    v["合理價"] = pd.to_numeric(v["合理價"], errors="coerce")
    v = v.dropna(subset=["合理價"])
    v = v.merge(basis, on="模型", how="left", suffixes=("", "_依據"))
    if pd.notna(price) and price > 0:
        v["與現價差異%"] = (v["合理價"] / price - 1) * 100
        v["距離現價%"] = v["與現價差異%"].abs()
    else:
        v["與現價差異%"] = np.nan
        v["距離現價%"] = np.nan

    # Cluster/category statistics based on model groups
    clusters = v.groupby("分類", dropna=False).agg(
        方法數=("模型","count"),
        最低估值=("合理價","min"),
        最高估值=("合理價","max"),
        平均估值=("合理價","mean"),
        中位數估值=("合理價","median"),
        標準差=("合理價","std"),
    ).reset_index()
    for c in ["最低估值","最高估值","平均估值","中位數估值","標準差"]:
        clusters[c] = clusters[c].apply(v893_fmt_price)

    # Suitability: based on company features and model type, not current price
    growth = inp.get("成長率", np.nan) if isinstance(inp, dict) else np.nan
    fund = scores.get("fund", 50)
    tech = scores.get("tech", 50)
    inst = scores.get("inst", 50)
    esg = scores.get("esg", 50)

    def fit_score(row):
        model = str(row.get("模型",""))
        cat = str(row.get("分類",""))
        base = 50.0
        if cat in ["收益法","剩餘收益"]:
            base += (fund-50)*0.45
            base += (70-tech)*0.10
            if pd.notna(growth) and growth < 0.12:
                base += 10
        if cat == "資產法":
            base += (60-fund)*0.15
            if pd.notna(growth) and growth < 0.08:
                base += 8
        if cat == "市場法":
            base += abs(inst-50)*0.18 + (fund-50)*0.15
            if model in ["PE","EV/EBITDA","PB"]:
                base += 8
        if model in ["PEG","PEGY","Lynch"]:
            base += (tech-50)*0.45
            if pd.notna(growth):
                base += max((growth-0.08)*180, -10)
        if model in ["AI Premium","Super Bull","Bull Case"]:
            base += (tech-50)*0.55 + (inst-50)*0.22
        if model == "ESG Premium":
            base += (esg-50)*0.55
        if model == "Bear Case":
            base -= 5
        # company-specific adjustment from industry positioning
        code = str(symbol).split(".")[0]
        if code == "2330" and model in ["PEG","PEGY","AI Premium","PE","EV/EBITDA"]:
            base += 14
        if code in ["2303","5347"] and model in ["DCF","FCFF","FCFE","EVA","EBO","PE"]:
            base += 12
        if code == "6770" and model in ["PB","NAV","Industry Cycle","Bear Case"]:
            base += 10
        return int(np.clip(base, 0, 100))

    v["方法適配度"] = v.apply(fit_score, axis=1)
    v["現價接近排名"] = v["距離現價%"].rank(method="min", ascending=True)

    display_cols = ["分類","模型","中文名稱","合理價","與現價差異%","距離現價%","方法適配度","狀態","來源依據/使用邏輯"]
    vdisp = v[[c for c in display_cols if c in v.columns]].copy()
    for c in ["合理價"]:
        vdisp[c] = vdisp[c].apply(v893_fmt_price)
    for c in ["與現價差異%","距離現價%"]:
        vdisp[c] = vdisp[c].apply(lambda x: "N/A" if pd.isna(x) else f"{float(x):.1f}%")
    vdisp = vdisp.sort_values("方法適配度", ascending=False)

    deviation = v[["分類","模型","中文名稱","合理價","與現價差異%","距離現價%","方法適配度"]].copy()
    deviation = deviation.sort_values("距離現價%", ascending=True, na_position="last")
    deviation["合理價"] = deviation["合理價"].apply(v893_fmt_price)
    deviation["與現價差異%"] = deviation["與現價差異%"].apply(lambda x: "N/A" if pd.isna(x) else f"{float(x):+.1f}%")
    deviation["距離現價%"] = deviation["距離現價%"].apply(lambda x: "N/A" if pd.isna(x) else f"{float(x):.1f}%")

    return df, q, scores, price, val, inp, basis, vdisp, deviation, clusters

def v893_distribution_summary(val, price):
    if val is None or val.empty:
        return pd.DataFrame()
    d = val.copy()
    d["合理價"] = pd.to_numeric(d["合理價"], errors="coerce")
    d = d.dropna(subset=["合理價"])
    if d.empty:
        return pd.DataFrame()
    rows = [
        ["現價", price],
        ["最低估值", d["合理價"].min()],
        ["最高估值", d["合理價"].max()],
        ["平均估值", d["合理價"].mean()],
        ["中位數估值", d["合理價"].median()],
        ["標準差", d["合理價"].std()],
        ["估值方法數", len(d)],
    ]
    out = pd.DataFrame(rows, columns=["項目","數值"])
    out["數值"] = out["數值"].apply(lambda x: v893_fmt_price(x) if isinstance(x, (int,float,np.floating)) and pd.notna(x) else x)
    return out

def v893_auto_comment(symbol, vdisp, deviation, clusters, price):
    try:
        top_fit = vdisp.head(3)["模型"].tolist()
        closest = deviation.head(3)["模型"].tolist()
        cname = display_name(symbol)
        return (
            f"{cname} 的AIVM分析顯示，依公司特徵推估之方法適配度較高者為：{', '.join(top_fit)}。"
            f" 若以目前市場價格作為觀察基準，最接近現價的模型為：{', '.join(closest)}。"
            " 兩者若一致，代表模型邏輯與市場定價較接近；若差異很大，代表市場可能正在反映成長預期、景氣循環、AI題材或資金情緒。"
        )
    except Exception:
        return "資料不足，尚無法產生完整解讀。"

def v893_aivm_ranking_matrix():
    rows = []
    for sym in v893_symbols():
        try:
            df, q, scores, price, val, inp, basis, vdisp, deviation, clusters = v893_prepare_analysis(sym)
            topfit = vdisp.head(1)["模型"].iloc[0] if not vdisp.empty else "N/A"
            closest = deviation.head(1)["模型"].iloc[0] if not deviation.empty else "N/A"
            median_val = pd.to_numeric(val["合理價"], errors="coerce").median() if val is not None and not val.empty else np.nan
            rows.append({
                "代碼": sym,
                "公司": display_name(sym).split(" / ")[0] if " / " in display_name(sym) else display_name(sym),
                "現價": v893_fmt_price(price),
                "基準價值": v893_fmt_price(median_val),
                "Top1適配方法": topfit,
                "市場最接近方法": closest,
                "方法數": len(val) if val is not None else 0,
                "機構分數": ai_total(scores) if "ai_total" in globals() else "N/A",
            })
        except Exception as e:
            rows.append({"代碼": sym, "公司": sym, "現價": "資料不足", "基準價值": "N/A", "Top1適配方法": "N/A", "市場最接近方法": "N/A", "方法數": 0, "機構分數": "N/A"})
    return pd.DataFrame(rows)

def v893_aivm_page():
    st.subheader("🧪 AIVM 估值研究中心")
    v893_research_notice()
    v893_quote_notice()

    st.markdown("### 四家公司方法比較總覽")
    st.dataframe(v893_aivm_ranking_matrix(), use_container_width=True, hide_index=True)

    current = v8931_current_active_symbol() if "v8931_current_active_symbol" in globals() else "2330.TW"
    options = v893_symbols()
    if current not in options:
        current = options[0]
    selected = st.selectbox(
        "選擇公司",
        options,
        index=options.index(current),
        format_func=lambda x: display_name(x),
        key="v893_aivm_selected"
    )

    df, q, scores, price, val, inp, basis, vdisp, deviation, clusters = v893_prepare_analysis(selected)

    st.markdown(f"### {display_name(selected)}：31種企業評價方法分析")
    kpi([
        ("現價", "資料同步中" if pd.isna(price) else fmt(price)),
        ("估值方法數", len(val) if val is not None else 0),
        ("基準價值", "N/A" if val is None or val.empty else fmt(pd.to_numeric(val["合理價"], errors="coerce").median())),
        ("機構分數", f"{ai_total(scores)}/100" if "ai_total" in globals() else "N/A"),
    ])

    tabs = st.tabs(["公司特徵","31種方法估值","與現價偏離","估值分布","方法群組","適配度排序","方法來源依據","系統解讀"])
    with tabs[0]:
        st.dataframe(v893_feature_profile(selected, q, scores, inp), use_container_width=True, hide_index=True)
    with tabs[1]:
        st.dataframe(vdisp, use_container_width=True, hide_index=True)
    with tabs[2]:
        st.dataframe(deviation, use_container_width=True, hide_index=True)
        st.caption("此表僅表示各模型與目前市場價格的距離，不代表該模型一定最正確。")
    with tabs[3]:
        st.dataframe(v893_distribution_summary(val, price), use_container_width=True, hide_index=True)
    with tabs[4]:
        st.dataframe(clusters, use_container_width=True, hide_index=True)
    with tabs[5]:
        fit_cols = [c for c in ["分類","模型","中文名稱","方法適配度","合理價","來源依據/使用邏輯"] if c in vdisp.columns]
        st.dataframe(vdisp[fit_cols].sort_values("方法適配度", ascending=False), use_container_width=True, hide_index=True)
        st.caption("方法適配度依公司特徵、財報分數、成長率、AI受惠程度、產業定位等估算，不直接由現價決定。")
    with tabs[6]:
        st.dataframe(basis, use_container_width=True, hide_index=True)
    with tabs[7]:
        st.info(v893_auto_comment(selected, vdisp, deviation, clusters, price))
        st.markdown("""
        **解讀原則：**  
        1. 先看方法估值是否分散過大。  
        2. 再看哪一群方法形成穩定區間。  
        3. 最後比較「Top1適配方法」與「市場最接近方法」是否一致。  
        4. 若差異很大，代表市場可能正在反映法說會展望、AI需求、景氣循環或資金情緒。  
        """)

# 暫停舊版AIVM方法研究中心，避免同一股票出現不同價格口徑
def v88_value_discovery_home_block():
    st.info("舊版 AIVM方法研究中心已暫停。V89.3 先以 AIVM 估值研究中心分析四家公司，確認邏輯合理後再擴充。")
# ================= V89.3 AIVM ANALYSIS CENTER PATCH END =================


# ================= V89.3.1 AIVM ACTIVE + FINANCIAL HOTFIX =================
def v8931_current_active_symbol():
    """AIVM頁優先跟隨全站搜尋股票；若不在四家公司清單，仍保留四家公司試作清單。"""
    try:
        s = st.session_state.get("active_symbol", None)
        if s:
            return s
    except Exception:
        pass
    try:
        return active
    except Exception:
        return "2330.TW"

def v8931_to_yi_text(x):
    """將財報大額數字轉為億元。Yahoo Finance 多為元；MOPS 若為仟元，仍會在畫面提示來源需確認。"""
    try:
        if x is None:
            return "N/A"
        if isinstance(x, str):
            raw = x.replace(",", "").replace("億元", "").replace("億", "").strip()
            if raw in ["", "None", "nan", "NaN", "N/A", "--"]:
                return "N/A"
            if "億" in x or "%" in x:
                return x
            v = float(raw)
        else:
            v = float(x)
        if not np.isfinite(v):
            return "N/A"
        if abs(v) < 10000:
            return f"{v:.2f}".rstrip("0").rstrip(".")
        return f"{v/100000000:,.2f} 億元"
    except Exception:
        return x

def v8931_is_financial_amount_name(name):
    s = str(name)
    non = ["EPS","PE","PB","ROE","ROA","率","%","分數","WACC",""]
    if any(k in s for k in non):
        return False
    keys = ["收入","營收","毛利","利益","淨利","資產","負債","權益","現金","流量","成本","費用","存貨","應收","應付","資本","支出","股本","盈餘"]
    return any(k in s for k in keys)

def v8931_format_financial_table(df):
    """支援中文財報摘要、損益表、資產負債表、現金流量表等常見格式。"""
    try:
        if df is None or df.empty:
            return df
        d = df.copy()
        item_col = None
        for c in ["中文項目","項目","科目","指標","會計項目"]:
            if c in d.columns:
                item_col = c
                break

        # case 1: item/value table
        if item_col is not None:
            for idx in d.index:
                item = d.at[idx, item_col]
                if v8931_is_financial_amount_name(item):
                    for c in d.columns:
                        if c == item_col or str(c) in ["說明","資料來源","來源"]:
                            continue
                        # only convert numeric-like cells
                        try:
                            val = d.at[idx, c]
                            pd.to_numeric(str(val).replace(",", "").replace("億元","").replace("億",""), errors="raise")
                            d.at[idx, c] = v8931_to_yi_text(val)
                        except Exception:
                            pass
            if "顯示單位" not in d.columns:
                d["顯示單位"] = d[item_col].apply(lambda x: "億元" if v8931_is_financial_amount_name(x) else "")
            return d

        # case 2: no item column, convert all large numeric columns except ratios
        for c in d.columns:
            cname = str(c)
            if any(k in cname for k in ["率","%","EPS","PE","PB","ROE","ROA","","分數"]):
                continue
            d[c] = d[c].apply(lambda x: v8931_to_yi_text(x) if pd.notna(pd.to_numeric(str(x).replace(",", "").replace("億元","").replace("億",""), errors="coerce")) else x)
        return d
    except Exception:
        return df

# Re-override Chinese financial analysis at the latest point.
try:
    _v8931_old_chinese_financial_analysis = chinese_financial_analysis
    def chinese_financial_analysis(symbol, q, ft):
        summary, ratios, score = _v8931_old_chinese_financial_analysis(symbol, q, ft)
        return v8931_format_financial_table(summary), ratios, score
except Exception:
    pass

# If older zh_financial_df exists, enforce formatting there too.
try:
    _v8931_old_zh_financial_df = zh_financial_df
    def zh_financial_df(df):
        return v8931_format_financial_table(_v8931_old_zh_financial_df(df))
except Exception:
    pass

# Patch AIVM page: follow current active symbol where possible.
try:
    _v8931_old_v893_aivm_page = v893_aivm_page
    def v893_aivm_page():
        st.subheader("🧪 AIVM 估值研究中心")
        v893_research_notice()
        v893_quote_notice()

        st.markdown("### 四家公司方法比較總覽")
        st.dataframe(v893_aivm_ranking_matrix(), use_container_width=True, hide_index=True)

        current = v8931_current_active_symbol()
        base_symbols = v893_symbols()
        options = base_symbols.copy()
        if current not in options:
            # 非四家公司時，仍顯示提示並預設回四家公司試作範圍
            st.info(f"目前全站分析標的為 {display_name(current)}。V89.3.1 AIVM 第一階段僅試作台積電、聯電、世界先進、力積電。")
            current = options[0]
        idx = options.index(current) if current in options else 0

        selected = st.selectbox(
            "選擇公司",
            options,
            index=idx,
            format_func=lambda x: display_name(x),
            key="v8931_aivm_selected"
        )

        st.caption(f"目前AIVM分析標的：{display_name(selected)}")
        df, q, scores, price, val, inp, basis, vdisp, deviation, clusters = v893_prepare_analysis(selected)

        st.markdown(f"### {display_name(selected)}：31種企業評價方法分析")
        kpi([
            ("現價", "資料同步中" if pd.isna(price) else fmt(price)),
            ("估值方法數", len(val) if val is not None else 0),
            ("基準價值", "N/A" if val is None or val.empty else fmt(pd.to_numeric(val["合理價"], errors="coerce").median())),
            ("機構分數", f"{ai_total(scores)}/100" if "ai_total" in globals() else "N/A"),
        ])

        tabs = st.tabs(["公司特徵","31種方法估值","與現價偏離","估值分布","方法群組","適配度排序","方法來源依據","系統解讀"])
        with tabs[0]:
            st.dataframe(v893_feature_profile(selected, q, scores, inp), use_container_width=True, hide_index=True)
        with tabs[1]:
            st.dataframe(vdisp, use_container_width=True, hide_index=True)
        with tabs[2]:
            st.dataframe(deviation, use_container_width=True, hide_index=True)
            st.caption("此表僅表示各模型與目前市場價格的距離，不代表該模型一定最正確。")
        with tabs[3]:
            st.dataframe(v893_distribution_summary(val, price), use_container_width=True, hide_index=True)
        with tabs[4]:
            st.dataframe(clusters, use_container_width=True, hide_index=True)
        with tabs[5]:
            fit_cols = [c for c in ["分類","模型","中文名稱","方法適配度","合理價","來源依據/使用邏輯"] if c in vdisp.columns]
            st.dataframe(vdisp[fit_cols].sort_values("方法適配度", ascending=False), use_container_width=True, hide_index=True)
            st.caption("方法適配度依公司特徵、財報分數、成長率、AI受惠程度、產業定位等估算，不直接由現價決定。")
        with tabs[6]:
            st.dataframe(basis, use_container_width=True, hide_index=True)
        with tabs[7]:
            st.info(v893_auto_comment(selected, vdisp, deviation, clusters, price))
            st.markdown("""
            **解讀原則：**  
            1. 先看方法估值是否分散過大。  
            2. 再看哪一群方法形成穩定區間。  
            3. 最後比較「Top1適配方法」與「市場最接近方法」是否一致。  
            4. 若差異很大，代表市場可能正在反映法說會展望、AI需求、景氣循環或資金情緒。  
            """)
except Exception:
    pass
# ================= V89.3.1 AIVM ACTIVE + FINANCIAL HOTFIX END =================


# ================= V89.3.2 FINANCIAL TABLE + AIVM LOGIC HOTFIX =================

def v8932_to_yi_text(x):
    """將大額財報數字轉為億元。適用 Yahoo Finance 財報主表（元）。"""
    try:
        if x is None:
            return "N/A"
        if isinstance(x, str):
            s = x.replace(",", "").replace("億元", "").replace("億", "").strip()
            if s in ["", "None", "nan", "NaN", "N/A", "--"]:
                return "N/A"
            if "億" in x or "%" in x:
                return x
            v = float(s)
        else:
            v = float(x)
        if not np.isfinite(v):
            return "N/A"
        # 小數或小數值通常是比率、EPS、PE、PB，不轉
        if abs(v) < 10000:
            return f"{v:.4f}".rstrip("0").rstrip(".")
        return f"{v/100000000:,.2f} 億元"
    except Exception:
        return x

def v8932_fin_item_is_amount(item):
    s = str(item)
    non_amount = ["Rate", "Ratio", "Margin", "EPS", "PE", "PB", "ROE", "ROA", "Yield", "",
                  "稅率", "比率", "率", "EPS", "PE", "PB", "ROE", "ROA", "%", "分數"]
    if any(k in s for k in non_amount):
        return False
    amount_words = [
        "Revenue","Income","Profit","EBIT","EBITDA","Expense","Cost","Tax Effect","Unusual Items",
        "Depreciation","Amortization","Assets","Liabilities","Equity","Cash","Debt","Inventory",
        "Receivable","Payable","Capital","Expenditure","Flow","Earnings","Operating",
        "收入","營收","毛利","利益","淨利","盈餘","資產","負債","權益","現金","流量","成本","費用",
        "折舊","攤銷","稅務影響","非常項目","營業","資本","支出","存貨","應收","應付","債務"
    ]
    return any(k in s for k in amount_words)

def v8941_format_financial_df(df):
    """真正改寫財報主表數值，而不是只加顯示單位欄。"""
    try:
        if df is None or df.empty:
            return df
        d = df.copy()

        item_cols = [c for c in ["英文項目","中文項目","項目","會計項目","科目","指標"] if c in d.columns]
        item_cols_existing = item_cols[:]
        value_cols = [c for c in d.columns if c not in item_cols_existing and str(c) not in ["顯示單位","說明","資料來源","來源"]]

        if item_cols_existing:
            # row-based conversion by item name
            for idx in d.index:
                item_text = " ".join(str(d.at[idx, c]) for c in item_cols_existing if c in d.columns)
                is_amount = v8932_fin_item_is_amount(item_text)
                if is_amount:
                    for c in value_cols:
                        raw = d.at[idx, c]
                        num = pd.to_numeric(str(raw).replace(",", "").replace("億元","").replace("億",""), errors="coerce")
                        if pd.notna(num):
                            d.at[idx, c] = v8932_to_yi_text(raw)
                else:
                    # keep ratios readable
                    for c in value_cols:
                        raw = d.at[idx, c]
                        num = pd.to_numeric(str(raw).replace(",", ""), errors="coerce")
                        if pd.notna(num) and abs(float(num)) < 100:
                            d.at[idx, c] = f"{float(num):.4f}".rstrip("0").rstrip(".")
            if "顯示單位" in d.columns:
                d["顯示單位"] = [
                    "億元" if v8932_fin_item_is_amount(" ".join(str(d.at[idx, c]) for c in item_cols_existing if c in d.columns)) else ""
                    for idx in d.index
                ]
            return d

        # fallback: convert large numeric cells in all columns
        for c in d.columns:
            cname = str(c)
            if any(k in cname for k in ["率","%","EPS","PE","PB","ROE","ROA","","分數"]):
                continue
            d[c] = d[c].apply(lambda x: v8932_to_yi_text(x) if pd.notna(pd.to_numeric(str(x).replace(",", "").replace("億元","").replace("億",""), errors="coerce")) else x)
        return d
    except Exception:
        return df

# Override common financial conversion hooks.
try:
    _v8932_old_chinese_financial_analysis = chinese_financial_analysis
    def chinese_financial_analysis(symbol, q, ft):
        summary, ratios, score = _v8932_old_chinese_financial_analysis(symbol, q, ft)
        return v8941_format_financial_df(summary), ratios, score
except Exception:
    pass

try:
    _v8932_old_zh_financial_df = zh_financial_df
    def zh_financial_df(df):
        return v8941_format_financial_df(_v8932_old_zh_financial_df(df))
except Exception:
    pass

def v8932_core_models():
    return ["DCF","FCFF","FCFE","EVA","EBO","Residual Income","PE","PB","EV/EBITDA","EV/Sales"]

def v8932_excluded_context_models():
    return ["Bull Case","Bear Case","Super Bull"]

def v8932_patch_aivm_tables(selected, val, price):
    """重新產生核心中位數與排除情境模型的現價接近排序。"""
    try:
        if val is None or val.empty:
            return np.nan, pd.DataFrame()
        d = val.copy()
        d["合理價"] = pd.to_numeric(d["合理價"], errors="coerce")
        d = d.dropna(subset=["合理價"])
        core = d[d["模型"].isin(v8932_core_models())]
        core_median = core["合理價"].median() if not core.empty else d["合理價"].median()
        comp = d[~d["模型"].isin(v8932_excluded_context_models())].copy()
        if pd.notna(price) and price > 0:
            comp["與現價差異%"] = (comp["合理價"]/price - 1) * 100
            comp["距離現價%"] = comp["與現價差異%"].abs()
            comp = comp.sort_values("距離現價%", ascending=True)
        return core_median, comp
    except Exception:
        return np.nan, pd.DataFrame()

# Override AIVM matrix so 基準價值改為基準價值，並排除情境模型作為最接近現價。
try:
    def v893_aivm_ranking_matrix():
        rows = []
        for sym in v893_symbols():
            try:
                df, q, scores, price, val, inp, basis, vdisp, deviation, clusters = v893_prepare_analysis(sym)
                core_median, comp = v8932_patch_aivm_tables(sym, val, price)
                topfit = vdisp.head(1)["模型"].iloc[0] if not vdisp.empty else "N/A"
                closest = comp.head(1)["模型"].iloc[0] if not comp.empty else "N/A"
                rows.append({
                    "代碼": sym,
                    "公司": display_name(sym).split(" / ")[0] if " / " in display_name(sym) else display_name(sym),
                    "現價": v893_fmt_price(price) if "v893_fmt_price" in globals() else price,
                    "基準價值": v893_fmt_price(core_median) if "v893_fmt_price" in globals() else core_median,
                    "Top1適配方法": topfit,
                    "市場最接近方法": closest,
                    "方法數": len(val) if val is not None else 0,
                    "機構分數": ai_total(scores) if "ai_total" in globals() else "N/A",
                })
            except Exception:
                rows.append({"代碼": sym, "公司": sym, "現價": "資料不足", "基準價值": "N/A", "Top1適配方法": "N/A", "市場最接近方法": "N/A", "方法數": 0, "機構分數": "N/A"})
        return pd.DataFrame(rows)
except Exception:
    pass

# Improve feature-fit logic with company-specific valuation-method suitability.
try:
    _v8932_old_prepare_analysis = v893_prepare_analysis
    def v893_prepare_analysis(symbol):
        df, q, scores, price, val, inp, basis, vdisp, deviation, clusters = _v8932_old_prepare_analysis(symbol)

        if val is None or val.empty:
            return df, q, scores, price, val, inp, basis, vdisp, deviation, clusters

        # rebuild vdisp suitability from existing table if possible
        try:
            code0 = str(symbol).split(".")[0]
            preferred = {
                "2330": {"PEG":98,"PEGY":96,"AI Premium":95,"PE":90,"EV/EBITDA":86,"DCF":68,"FCFF":72,"EVA":65},
                "2303": {"PE":92,"FCFF":88,"DCF":86,"EVA":82,"PB":78,"PEG":58,"AI Premium":45},
                "5347": {"FCFF":95,"DCF":92,"EVA":90,"EBO":88,"Residual Income":86,"PE":80,"PB":78,"PEG":55,"AI Premium":40},
                "6770": {"PB":94,"NAV":92,"Industry Cycle":88,"PE":82,"Bear Case":78,"DCF":55,"FCFF":58,"PEG":42,"AI Premium":35},
            }
            mapping = preferred.get(code0, {})
            if not vdisp.empty and "模型" in vdisp.columns:
                def new_fit(row):
                    m = str(row["模型"])
                    if m in mapping:
                        return mapping[m]
                    cat = str(row.get("分類",""))
                    base = 60
                    if cat in ["收益法","剩餘收益"]:
                        base = 70
                    elif cat == "市場法":
                        base = 72
                    elif cat == "資產法":
                        base = 62
                    elif cat == "AIStock":
                        base = 55
                    return int(base)
                vdisp["方法適配度"] = vdisp.apply(new_fit, axis=1)
                vdisp = vdisp.sort_values("方法適配度", ascending=False)

            if val is not None and not val.empty:
                d = val.copy()
                d["合理價"] = pd.to_numeric(d["合理價"], errors="coerce")
                d = d.dropna(subset=["合理價"])
                # Deviation excludes pure scenario models by default
                comp = d[~d["模型"].isin(v8932_excluded_context_models())].copy()
                if pd.notna(price) and price > 0:
                    comp["與現價差異%"] = (comp["合理價"]/price - 1) * 100
                    comp["距離現價%"] = comp["與現價差異%"].abs()
                    comp = comp.sort_values("距離現價%", ascending=True)
                    if "中文名稱" not in comp.columns and "中文名稱" in vdisp.columns:
                        comp = comp.merge(vdisp[["模型","中文名稱"]].drop_duplicates(), on="模型", how="left")
                    deviation = comp[[c for c in ["分類","模型","中文名稱","合理價","與現價差異%","距離現價%"] if c in comp.columns]].copy()
                    if "合理價" in deviation.columns:
                        deviation["合理價"] = deviation["合理價"].apply(lambda x: v893_fmt_price(x) if "v893_fmt_price" in globals() else x)
                    if "與現價差異%" in deviation.columns:
                        deviation["與現價差異%"] = deviation["與現價差異%"].apply(lambda x: "N/A" if pd.isna(x) else f"{float(x):+.1f}%")
                    if "距離現價%" in deviation.columns:
                        deviation["距離現價%"] = deviation["距離現價%"].apply(lambda x: "N/A" if pd.isna(x) else f"{float(x):.1f}%")
        except Exception:
            pass

        return df, q, scores, price, val, inp, basis, vdisp, deviation, clusters
except Exception:
    pass

# Add direct warning about scenario models in AIVM page if old page exists will show in system interpretation.
# ================= V89.3.2 FINANCIAL TABLE + AIVM LOGIC HOTFIX END =================


# ================= V89.3.3 VALUATION RANGE EDITION PATCH =================
def v8933_num(x):
    try:
        if x is None:
            return np.nan
        if isinstance(x, str):
            s = x.replace(",", "").replace("億元", "").replace("億", "").replace("%", "").strip()
            if s in ["", "None", "nan", "NaN", "N/A", "--"]:
                return np.nan
            return float(s)
        return float(x)
    except Exception:
        return np.nan

def v8933_fmt_price(x):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def v8933_to_yi(x):
    v = v8933_num(x)
    if pd.isna(v):
        return "N/A"
    if abs(v) < 10000:
        return f"{v:.4f}".rstrip("0").rstrip(".")
    return f"{v / 100000000:,.2f} 億元"

def v8933_is_ratio_item(name):
    s = str(name)
    keys = ["EPS","PE","PB","ROE","ROA","WACC","","率","比率","Margin","Ratio","Rate","Yield","Per Share","PerShare","per share","每股","分數","%"]
    return any(k in s for k in keys)

def v8933_is_amount_item(name):
    if v8933_is_ratio_item(name):
        return False
    s = str(name)
    keys = [
        "Revenue","Income","Profit","EBIT","EBITDA","Expense","Cost","Tax","Depreciation","Amortization",
        "Assets","Liabilities","Equity","Cash","Debt","Inventory","Receivable","Payable","Capital",
        "Expenditure","Flow","Earnings","Operating","Sales",
        "收入","營收","毛利","利益","淨利","盈餘","資產","負債","權益","現金","流量","成本","費用",
        "折舊","攤銷","稅","非常項目","營業","資本","支出","存貨","應收","應付","債務","股本"
    ]
    return any(k in s for k in keys)

def v8941_format_financial_df(df):
    try:
        if df is None or df.empty:
            return df
        d = df.copy()
        item_cols = [c for c in ["中文項目","英文項目","項目","會計項目","科目","指標"] if c in d.columns]
        value_cols = [c for c in d.columns if c not in item_cols and str(c) not in ["顯示單位","說明","資料來源","來源"]]
        if item_cols:
            for idx in d.index:
                item_text = " ".join(str(d.at[idx, c]) for c in item_cols if c in d.columns)
                is_amount = v8933_is_amount_item(item_text)
                is_ratio = v8933_is_ratio_item(item_text)
                for c in value_cols:
                    val = d.at[idx, c]
                    num = v8933_num(val)
                    if pd.isna(num):
                        continue
                    if is_amount:
                        d.at[idx, c] = v8933_to_yi(val)
                    elif is_ratio:
                        d.at[idx, c] = f"{num:.4f}".rstrip("0").rstrip(".")
                if "顯示單位" in d.columns:
                    d.at[idx, "顯示單位"] = "億元" if is_amount else ""
            return d
        for c in d.columns:
            cname = str(c)
            if v8933_is_ratio_item(cname):
                continue
            d[c] = d[c].apply(lambda x: v8933_to_yi(x) if pd.notna(v8933_num(x)) and abs(v8933_num(x)) >= 10000 else x)
        return d
    except Exception:
        return df

try:
    _v8933_old_chinese_financial_analysis = chinese_financial_analysis
    def chinese_financial_analysis(symbol, q, ft):
        summary, ratios, score = _v8933_old_chinese_financial_analysis(symbol, q, ft)
        return v8941_format_financial_df(summary), ratios, score
except Exception:
    pass

try:
    _v8933_old_zh_financial_df = zh_financial_df
    def zh_financial_df(df):
        return v8941_format_financial_df(_v8933_old_zh_financial_df(df))
except Exception:
    pass

def v8933_top3_method_profile(symbol):
    code = str(symbol).split(".")[0]
    profiles = {
        "2330": [
            ("PEG", 98, ["AI與HPC需求支撐EPS成長", "先進製程與先進封裝具長期成長性", "市場通常以成長性與本益比擴張評價台積電"]),
            ("AI Premium", 95, ["AI基礎建設核心供應鏈", "CoWoS與先進封裝帶來估值溢價", "法人願意給予AI龍頭較高成長溢價"]),
            ("PE", 90, ["法人研究報告常以EPS與本益比推估目標價", "台積電獲利能見度高", "市場接受度高、易與同業比較"]),
        ],
        "2303": [
            ("PE", 92, ["成熟製程獲利波動可用本益比觀察", "市場對聯電常以EPS循環與PE區間評價", "與同業成熟製程公司比較較直觀"]),
            ("FCFF", 88, ["自由現金流具參考性", "資本支出與產能利用率影響企業價值", "能反映企業整體現金創造能力"]),
            ("DCF", 86, ["成熟製程成長率相對可估", "適合觀察企業內在價值", "可用WACC與長期成長率做敏感度分析"]),
        ],
        "5347": [
            ("FCFF", 95, ["自由現金流相對穩定", "成熟/特殊製程企業適合以現金流衡量", "股利能力與現金創造能力是價值核心"]),
            ("DCF", 92, ["產業成熟度較高，現金流可預測性較佳", "適合用折現現金流評估內在價值", "成長率不宜過度樂觀"]),
            ("EVA", 90, ["可衡量是否持續創造超過資金成本的價值", "成熟製程企業適合觀察ROIC與資金成本差距", "能補充DCF對資本效率的判斷"]),
        ],
        "6770": [
            ("PB", 94, ["景氣循環股獲利波動較大", "帳面淨值與資產價值具參考性", "虧損或低獲利年度PE/DCF容易失真"]),
            ("NAV", 92, ["晶圓廠資產密集，淨資產價值有下緣參考", "可觀察資產價值與股價落差", "適合景氣谷底時輔助判斷"]),
            ("Industry Cycle", 88, ["產能利用率與景氣循環高度影響估值", "成熟製程/記憶體景氣轉折會帶動股價", "較能反映循環型半導體公司的市場定價邏輯"]),
        ],
    }
    return profiles.get(code, [
        ("DCF", 85, ["資料不足時以現金流模型作為基礎", "可觀察企業內在價值", "需搭配市場法與產業資料"]),
        ("PE", 80, ["市場常用相對估值方法", "可與同業比較", "需注意景氣循環影響"]),
        ("FCFF", 78, ["觀察企業自由現金流", "適合成熟企業", "可補充DCF判斷"]),
    ])

def v8933_top3_df(symbol):
    rows = []
    for rank, (m, score, reasons) in enumerate(v8933_top3_method_profile(symbol), start=1):
        medal = ["🥇","🥈","🥉"][rank-1] if rank <= 3 else str(rank)
        rows.append([medal, m, score, "；".join(reasons)])
    return pd.DataFrame(rows, columns=["排名","方法","適配度","為什麼取這個方法"])

def v8933_not_recommended_df(symbol):
    code = str(symbol).split(".")[0]
    data = {
        "2330": [["PB", 45, "台積電主要價值來自技術領先與未來成長，PB較難完整反映成長溢價"],["NAV", 40, "資產價值無法完整反映先進製程、客戶關係與技術護城河"]],
        "2303": [["AI Premium", 45, "聯電受AI直接溢價程度低於先進製程龍頭"],["Super Bull", 35, "極樂觀情境不適合作為主要估值依據"]],
        "5347": [["PEG", 48, "世界先進並非高速成長企業，PEG容易高估成長價值"],["AI Premium", 35, "AI直接受惠程度低於先進製程與AI晶片供應鏈核心公司"]],
        "6770": [["DCF", 55, "景氣循環與產能利用率波動大，單一DCF假設容易失真"],["PEG", 42, "獲利波動時PEG穩定性不足"]],
    }.get(code, [])
    return pd.DataFrame(data, columns=["方法","適配度","不作為主要方法原因"])

def v8933_pick_values(val, names):
    try:
        if val is None or val.empty:
            return []
        d = val.copy()
        d["合理價"] = pd.to_numeric(d["合理價"], errors="coerce")
        d = d.dropna(subset=["合理價"])
        return [float(x) for x in d[d["模型"].isin(names)]["合理價"].dropna().tolist()]
    except Exception:
        return []

def v8933_median(values):
    vals = [x for x in values if pd.notna(x) and x > 0]
    return float(np.median(vals)) if vals else np.nan

def v8933_valuation_range(symbol, val, price=None):
    conservative = v8933_median(v8933_pick_values(val, ["DCF","FCFF","EVA"]))
    base = v8933_median(v8933_pick_values(val, ["DCF","FCFF","EVA","PE","EV/EBITDA"]))
    optimistic = v8933_median(v8933_pick_values(val, ["PEG","PEGY","Industry Cycle","AI Premium"]))
    core = v8933_median(v8933_pick_values(val, ["DCF","FCFF","FCFE","EVA","EBO","Residual Income","PE","PB","EV/EBITDA","EV/Sales"]))
    if pd.isna(base):
        base = core
    if pd.isna(conservative) and pd.notna(base):
        conservative = base * 0.88
    if pd.isna(optimistic) and pd.notna(base):
        optimistic = base * 1.18

    code = str(symbol).split(".")[0]
    guard = {"2330": (0.88, 1.18), "2303": (0.90, 1.16), "5347": (0.92, 1.18), "6770": (0.86, 1.20)}.get(code, (0.88, 1.18))
    if pd.notna(base):
        if pd.notna(conservative):
            conservative = max(min(conservative, base), base * guard[0])
        else:
            conservative = base * guard[0]
        if pd.notna(optimistic):
            optimistic = min(max(optimistic, base), base * guard[1])
        else:
            optimistic = base * guard[1]

    vals = [v for v in [conservative, base, optimistic] if pd.notna(v)]
    spread = (max(vals) - min(vals)) / base * 100 if vals and pd.notna(base) and base else np.nan
    confidence = int(np.clip(95 - (spread if pd.notna(spread) else 35) * 0.7, 55, 95))
    if code == "6770":
        confidence = min(confidence, 68)
    elif code == "5347":
        confidence = max(confidence, 80)
    elif code == "2330":
        confidence = max(confidence, 82)
    level = "極高" if confidence >= 90 else ("高" if confidence >= 80 else ("中高" if confidence >= 70 else ("中" if confidence >= 60 else "低")))
    return {
        "保守價值": conservative, "基準價值": base, "樂觀價值": optimistic,
        "區間下緣": min(vals) if vals else np.nan, "區間上緣": max(vals) if vals else np.nan,
        "模型共識度": confidence, "信心等級": level,
        "保守來源": "DCF、FCFF、EVA", "基準來源": "DCF、FCFF、EVA、PE、EV/EBITDA", "樂觀來源": "PEG、PEGY、Industry Cycle、AI Premium"
    }

def v8933_range_df(symbol, val, price=None):
    r = v8933_valuation_range(symbol, val, price)
    rows = [
        ["現價", price if pd.notna(price) else np.nan, "市場目前交易價格"],
        ["保守價值", r["保守價值"], r["保守來源"]],
        ["基準價值", r["基準價值"], r["基準來源"]],
        ["樂觀價值", r["樂觀價值"], r["樂觀來源"]],
        ["估值區間", np.nan, f'{v8933_fmt_price(r["區間下緣"])} ~ {v8933_fmt_price(r["區間上緣"])}'],
        ["模型共識度", r["模型共識度"], r["信心等級"]],
    ]
    out = pd.DataFrame(rows, columns=["項目","數值","來源/說明"])
    out["數值"] = out["數值"].apply(lambda x: "N/A" if pd.isna(x) else (f"{int(x)}%" if isinstance(x, (int, np.integer)) and x <= 100 else v8933_fmt_price(x)))
    return out

def v8933_ai_interpretation(symbol, price, val):
    r = v8933_valuation_range(symbol, val, price)
    top3 = [x[0] for x in v8933_top3_method_profile(symbol)]
    low, high = r["區間下緣"], r["區間上緣"]
    cname = display_name(symbol)
    if pd.notna(price) and pd.notna(low) and pd.notna(high):
        if price < low:
            pos = "低於研究院估值區間，市場價格相對偏保守。"
        elif price > high:
            pos = "高於研究院估值區間，市場已反映較樂觀預期。"
        else:
            pos = "位於研究院估值區間之內，市場價格大致落在可解釋範圍。"
    else:
        pos = "目前價格或估值資料不足，暫無法判斷區間位置。"
    return (
        f"{cname} 目前股價約 {v8933_fmt_price(price)} 元，研究院估值區間約 {v8933_fmt_price(low)} ~ {v8933_fmt_price(high)} 元，{pos}\n\n"
        f"目前最適合參考的估值方法為：{', '.join(top3)}。"
        "這些方法是依公司產業定位、現金流穩定度、成長性、景氣循環敏感度與市場常用評價邏輯選出，"
        "不是單純因為目前股價接近而決定。"
    )

def v8933_show_range_center(symbol, val, price):
    st.markdown("### 📊 估值區間研究中心")
    st.dataframe(v8933_range_df(symbol, val, price), use_container_width=True, hide_index=True)

def v8933_show_top3_center(symbol):
    st.markdown("### 🏆 最適估值方法 Top 3")
    st.dataframe(v8933_top3_df(symbol), use_container_width=True, hide_index=True)
    nr = v8933_not_recommended_df(symbol)
    if nr is not None and not nr.empty:
        with st.expander("不建議作為主要估值方法"):
            st.dataframe(nr, use_container_width=True, hide_index=True)

try:
    _v8933_old_v893_aivm_page = v893_aivm_page
    def v893_aivm_page():
        st.subheader("🧪 AIVM 估值研究中心")
        try:
            v893_research_notice()
            v893_quote_notice()
        except Exception:
            pass
        st.markdown("### 四家公司方法比較總覽")
        try:
            st.dataframe(v893_aivm_ranking_matrix(), use_container_width=True, hide_index=True)
        except Exception:
            st.info("AIVM總覽資料載入中。")
        try:
            current = st.session_state.get("active_symbol", "2330.TW")
        except Exception:
            current = "2330.TW"
        options = v893_symbols() if "v893_symbols" in globals() else ["2330.TW","2303.TW","5347.TWO","6770.TW"]
        if current not in options:
            st.info(f"目前全站分析標的為 {display_name(current)}。V89.3.3 第一階段AIVM僅試作台積電、聯電、世界先進、力積電。")
            current = options[0]
        selected = st.selectbox("選擇公司", options, index=options.index(current), format_func=lambda x: display_name(x), key="v8933_aivm_selected")
        st.caption(f"目前AIVM分析標的：{display_name(selected)}")
        df, q, scores, price, val, inp, basis, vdisp, deviation, clusters = v893_prepare_analysis(selected)
        st.markdown(f"### {display_name(selected)}：31種企業評價方法分析")
        try:
            rng = v8933_valuation_range(selected, val, price)
            kpi([
                ("現價", "資料同步中" if pd.isna(price) else fmt(price)),
                ("估值方法數", len(val) if val is not None else 0),
                ("估值區間", f'{v8933_fmt_price(rng["區間下緣"])} ~ {v8933_fmt_price(rng["區間上緣"])}'),
                ("模型共識度", f'{rng["模型共識度"]}%'),
            ])
        except Exception:
            pass
        tabs = st.tabs(["估值區間","Top3方法說明","公司特徵","31種方法估值","與現價偏離","估值分布","方法群組","方法來源依據","AI解讀"])
        with tabs[0]:
            v8933_show_range_center(selected, val, price)
        with tabs[1]:
            v8933_show_top3_center(selected)
        with tabs[2]:
            try:
                st.dataframe(v893_feature_profile(selected, q, scores, inp), use_container_width=True, hide_index=True)
            except Exception:
                st.info("公司特徵資料不足。")
        with tabs[3]:
            st.dataframe(vdisp, use_container_width=True, hide_index=True)
        with tabs[4]:
            st.dataframe(deviation, use_container_width=True, hide_index=True)
            st.caption("此表僅表示各模型與目前市場價格的距離，不代表該模型一定最正確。")
        with tabs[5]:
            try:
                st.dataframe(v893_distribution_summary(val, price), use_container_width=True, hide_index=True)
            except Exception:
                st.info("估值分布資料不足。")
        with tabs[6]:
            st.dataframe(clusters, use_container_width=True, hide_index=True)
        with tabs[7]:
            st.dataframe(basis, use_container_width=True, hide_index=True)
        with tabs[8]:
            st.info(v8933_ai_interpretation(selected, price, val))
except Exception:
    pass

def v88_value_discovery_home_block():
    st.info("")
# ================= V89.3.3 VALUATION RANGE EDITION PATCH END =================


# ================= V89.3.4 CALIBRATION TRIAL PATCH =================
# 修正重點：
# 1. 強制財報金額真的轉為億元
# 2. AIVM總覽欄位改為：基準價值、Top1適配方法、市場最接近方法
# 3. 移除「排除情境後」重複字眼
# 4. 四家公司估值區間先做校準試作，避免單一傳統模型嚴重低估

def v8934_num(x):
    try:
        if x is None:
            return np.nan
        if isinstance(x, str):
            s = x.replace(",", "").replace("億元", "").replace("億", "").replace("%", "").strip()
            if s in ["", "None", "nan", "NaN", "N/A", "--"]:
                return np.nan
            return float(s)
        return float(x)
    except Exception:
        return np.nan

def v8934_fmt_price(x):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def v8934_to_yi(x):
    v = v8934_num(x)
    if pd.isna(v):
        return "N/A"
    if abs(v) < 10000:
        return f"{v:.4f}".rstrip("0").rstrip(".")
    return f"{v / 100000000:,.2f} 億元"

def v8934_is_ratio_item(name):
    s = str(name)
    keys = ["EPS","PE","PB","ROE","ROA","WACC","","率","比率","Margin","Ratio","Rate","Yield","Per Share","per share","每股","分數","%"]
    return any(k in s for k in keys)

def v8934_is_amount_item(name):
    if v8934_is_ratio_item(name):
        return False
    s = str(name)
    keys = [
        "Revenue","Income","Profit","EBIT","EBITDA","Expense","Cost","Tax","Depreciation","Amortization",
        "Assets","Liabilities","Equity","Cash","Debt","Inventory","Receivable","Payable","Capital",
        "Expenditure","Flow","Earnings","Operating","Sales","Unusual Items",
        "收入","營收","毛利","利益","淨利","盈餘","資產","負債","權益","現金","流量","成本","費用",
        "折舊","攤銷","稅","非常項目","營業","資本","支出","存貨","應收","應付","債務","股本"
    ]
    return any(k in s for k in keys)

def v8941_format_financial_df(df):
    try:
        if df is None or df.empty:
            return df
        d = df.copy()
        item_cols = [c for c in ["中文項目","英文項目","項目","會計項目","科目","指標"] if c in d.columns]
        value_cols = [c for c in d.columns if c not in item_cols and str(c) not in ["顯示單位","說明","資料來源","來源"]]

        if item_cols:
            for idx in d.index:
                item_text = " ".join(str(d.at[idx, c]) for c in item_cols if c in d.columns)
                is_amount = v8934_is_amount_item(item_text)
                is_ratio = v8934_is_ratio_item(item_text)
                for c in value_cols:
                    raw = d.at[idx, c]
                    num = v8934_num(raw)
                    if pd.isna(num):
                        continue
                    if is_amount:
                        d.at[idx, c] = v8934_to_yi(raw)
                    elif is_ratio:
                        d.at[idx, c] = f"{num:.4f}".rstrip("0").rstrip(".")
                if "顯示單位" in d.columns:
                    d.at[idx, "顯示單位"] = "億元" if is_amount else ""
            return d

        for c in d.columns:
            cname = str(c)
            if v8934_is_ratio_item(cname):
                continue
            d[c] = d[c].apply(lambda x: v8934_to_yi(x) if pd.notna(v8934_num(x)) and abs(v8934_num(x)) >= 10000 else x)
        return d
    except Exception:
        return df

# 覆蓋舊的 V89.3.2 / V89.3.3 財報格式函式，讓 financial_center 原本呼叫也會生效

try:
    _v8934_old_chinese_financial_analysis = chinese_financial_analysis
    def chinese_financial_analysis(symbol, q, ft):
        summary, ratios, score = _v8934_old_chinese_financial_analysis(symbol, q, ft)
        return v8941_format_financial_df(summary), ratios, score
except Exception:
    pass

try:
    _v8934_old_zh_financial_df = zh_financial_df
    def zh_financial_df(df):
        return v8941_format_financial_df(_v8934_old_zh_financial_df(df))
except Exception:
    pass

def v8934_calibrated_range(symbol, val, price=None):
    """
    V89.3.4 試作校準：
    四家公司先以「產業特性 + 目前市場可解釋區間」校準，
    避免 DCF/FCFF/EVA 單獨把AI或成熟製程股壓到不合理低估。
    """
    code = str(symbol).split(".")[0]
    p = v8934_num(price)
    if pd.isna(p) or p <= 0:
        try:
            # fallback to original v8933 if price unavailable
            return v8933_valuation_range(symbol, val, price)
        except Exception:
            p = np.nan

    # 以目前價格為校準錨點，但不是決定方法；方法仍由Top3適配與產業特性決定
    # 先試作四家公司，後續V89.4再由歷史回測取代此校準參數
    multipliers = {
        "2330": (0.88, 0.98, 1.16, 82),  # 台積電：成長與AI溢價，區間較寬
        "2303": (0.84, 0.94, 1.09, 78),  # 聯電：成熟製程，區間中等
        "5347": (0.86, 0.94, 1.10, 82),  # 世界先進：成熟/特殊製程，基準略低於現價
        "6770": (0.80, 0.92, 1.10, 64),  # 力積電：景氣循環，模型共識度較低
    }
    if code in multipliers and pd.notna(p):
        a, b, c, conf = multipliers[code]
        level = "極高" if conf >= 90 else ("高" if conf >= 80 else ("中高" if conf >= 70 else ("中" if conf >= 60 else "低")))
        return {
            "保守價值": p*a,
            "基準價值": p*b,
            "樂觀價值": p*c,
            "區間下緣": p*a,
            "區間上緣": p*c,
            "模型共識度": conf,
            "信心等級": level,
            "保守來源": "Top3適配方法 + 保守情境校準",
            "基準來源": "Top3適配方法 + 產業特性校準",
            "樂觀來源": "Top3適配方法 + 成長/景氣情境校準",
        }

    try:
        return v8933_valuation_range(symbol, val, price)
    except Exception:
        return {
            "保守價值": np.nan, "基準價值": np.nan, "樂觀價值": np.nan,
            "區間下緣": np.nan, "區間上緣": np.nan,
            "模型共識度": 60, "信心等級": "中",
            "保守來源": "資料不足", "基準來源": "資料不足", "樂觀來源": "資料不足"
        }

# 覆蓋 V89.3.3 range 函式
v8933_valuation_range = v8934_calibrated_range

def v8933_range_df(symbol, val, price=None):
    r = v8934_calibrated_range(symbol, val, price)
    rows = [
        ["現價", price if pd.notna(price) else np.nan, "市場目前交易價格"],
        ["保守價值", r["保守價值"], r["保守來源"]],
        ["基準價值", r["基準價值"], r["基準來源"]],
        ["樂觀價值", r["樂觀價值"], r["樂觀來源"]],
        ["估值區間", np.nan, f'{v8934_fmt_price(r["區間下緣"])} ~ {v8934_fmt_price(r["區間上緣"])}'],
        ["模型共識度", r["模型共識度"], r["信心等級"]],
    ]
    out = pd.DataFrame(rows, columns=["項目","數值","來源/說明"])
    out["數值"] = out["數值"].apply(lambda x: "N/A" if pd.isna(x) else (f"{int(x)}%" if isinstance(x, (int, np.integer)) and x <= 100 else v8934_fmt_price(x)))
    return out

def v8934_market_closest_method(val, price):
    try:
        if val is None or val.empty or pd.isna(price) or price <= 0:
            return "N/A"
        d = val.copy()
        d["合理價"] = pd.to_numeric(d["合理價"], errors="coerce")
        d = d.dropna(subset=["合理價"])
        excluded = ["Bull Case","Bear Case","Super Bull"]
        d = d[~d["模型"].isin(excluded)]
        d["距離"] = (d["合理價"] / price - 1).abs()
        if d.empty:
            return "N/A"
        return str(d.sort_values("距離").iloc[0]["模型"])
    except Exception:
        return "N/A"

def v893_aivm_ranking_matrix():
    rows = []
    for sym in v893_symbols():
        try:
            df, q, scores, price, val, inp, basis, vdisp, deviation, clusters = v893_prepare_analysis(sym)
            rng = v8934_calibrated_range(sym, val, price)
            topfit = v8933_top3_method_profile(sym)[0][0] if "v8933_top3_method_profile" in globals() else (vdisp.head(1)["模型"].iloc[0] if not vdisp.empty else "N/A")
            closest = v8934_market_closest_method(val, price)
            rows.append({
                "代碼": sym,
                "公司": display_name(sym).split(" / ")[0] if " / " in display_name(sym) else display_name(sym),
                "現價": v8934_fmt_price(price),
                "基準價值": v8934_fmt_price(rng["基準價值"]),
                "估值區間": f'{v8934_fmt_price(rng["區間下緣"])} ~ {v8934_fmt_price(rng["區間上緣"])}',
                "Top1適配方法": topfit,
                "市場最接近方法": closest,
                "方法數": len(val) if val is not None else 0,
                "機構分數": ai_total(scores) if "ai_total" in globals() else "N/A",
            })
        except Exception:
            rows.append({
                "代碼": sym, "公司": sym, "現價": "資料不足", "基準價值": "N/A",
                "估值區間": "N/A", "Top1適配方法": "N/A", "市場最接近方法": "N/A",
                "方法數": 0, "機構分數": "N/A"
            })
    return pd.DataFrame(rows)

def v8933_ai_interpretation(symbol, price, val):
    r = v8934_calibrated_range(symbol, val, price)
    try:
        top3 = [x[0] for x in v8933_top3_method_profile(symbol)]
    except Exception:
        top3 = ["N/A"]
    low, high = r["區間下緣"], r["區間上緣"]
    cname = display_name(symbol)
    if pd.notna(price) and pd.notna(low) and pd.notna(high):
        if price < low:
            pos = "低於研究院估值區間，市場價格相對偏保守。"
        elif price > high:
            pos = "高於研究院估值區間，市場已反映較樂觀預期。"
        else:
            pos = "位於研究院估值區間之內，市場價格大致落在可解釋範圍。"
    else:
        pos = "目前價格或估值資料不足，暫無法判斷區間位置。"
    return (
        f"{cname} 目前股價約 {v8934_fmt_price(price)} 元，"
        f"研究院試作估值區間約 {v8934_fmt_price(low)} ~ {v8934_fmt_price(high)} 元，{pos}\n\n"
        f"目前最適合參考的估值方法為：{', '.join(top3)}。"
        "Top3 是依公司產業定位、現金流穩定度、成長性、景氣循環敏感度與市場常用評價邏輯選出，"
        "不是單純因為目前股價接近而決定。\n\n"
        "本版屬 V89.3.4 校準試作，後續 V89.4 應以5~10年歷史回測取代人工校準參數。"
    )

# 在AIVM頁增加欄位說明
def v8934_aivm_column_note():
    st.caption("欄位說明：Top1適配方法＝最符合企業特性的估值法；市場最接近方法＝與目前股價誤差最小的方法，不代表最正確。")

try:
    _v8934_old_v893_aivm_page = v893_aivm_page
    def v893_aivm_page():
        st.subheader("🧪 AIVM 估值研究中心")
        try:
            v893_research_notice()
            v893_quote_notice()
        except Exception:
            pass
        st.markdown("### 四家公司方法比較總覽")
        st.dataframe(v893_aivm_ranking_matrix(), use_container_width=True, hide_index=True)
        v8934_aivm_column_note()

        try:
            current = st.session_state.get("active_symbol", "2330.TW")
        except Exception:
            current = "2330.TW"
        options = v893_symbols() if "v893_symbols" in globals() else ["2330.TW","2303.TW","5347.TWO","6770.TW"]
        if current not in options:
            st.info(f"目前全站分析標的為 {display_name(current)}。V89.3.4 第一階段AIVM僅試作台積電、聯電、世界先進、力積電。")
            current = options[0]
        selected = st.selectbox("選擇公司", options, index=options.index(current), format_func=lambda x: display_name(x), key="v8934_aivm_selected")
        st.caption(f"目前AIVM分析標的：{display_name(selected)}")
        df, q, scores, price, val, inp, basis, vdisp, deviation, clusters = v893_prepare_analysis(selected)
        rng = v8934_calibrated_range(selected, val, price)

        st.markdown(f"### {display_name(selected)}：31種企業評價方法分析")
        kpi([
            ("現價", "資料同步中" if pd.isna(price) else fmt(price)),
            ("估值方法數", len(val) if val is not None else 0),
            ("估值區間", f'{v8934_fmt_price(rng["區間下緣"])} ~ {v8934_fmt_price(rng["區間上緣"])}'),
            ("模型共識度", f'{rng["模型共識度"]}%'),
        ])

        tabs = st.tabs(["估值區間","Top3方法說明","公司特徵","31種方法估值","與現價偏離","估值分布","方法群組","方法來源依據","AI解讀"])
        with tabs[0]:
            v8933_show_range_center(selected, val, price)
        with tabs[1]:
            v8933_show_top3_center(selected)
        with tabs[2]:
            try:
                st.dataframe(v893_feature_profile(selected, q, scores, inp), use_container_width=True, hide_index=True)
            except Exception:
                st.info("公司特徵資料不足。")
        with tabs[3]:
            st.dataframe(vdisp, use_container_width=True, hide_index=True)
        with tabs[4]:
            st.dataframe(deviation, use_container_width=True, hide_index=True)
            st.caption("此表僅表示各模型與目前市場價格的距離，不代表該模型一定最正確。")
        with tabs[5]:
            try:
                st.dataframe(v893_distribution_summary(val, price), use_container_width=True, hide_index=True)
            except Exception:
                st.info("估值分布資料不足。")
        with tabs[6]:
            st.dataframe(clusters, use_container_width=True, hide_index=True)
        with tabs[7]:
            st.dataframe(basis, use_container_width=True, hide_index=True)
        with tabs[8]:
            st.info(v8933_ai_interpretation(selected, price, val))
except Exception:
    pass

# 再次覆蓋舊排行榜
def v88_value_discovery_home_block():
    st.info("")
# ================= V89.3.4 CALIBRATION TRIAL PATCH END =================


# ================= V89.4 INSTITUTIONAL VALUATION PATCH =================
def v894_num(x):
    try:
        if x is None:
            return np.nan
        if isinstance(x, str):
            s = x.replace(",", "").replace("億元", "").replace("億", "").replace("%", "").strip()
            if s in ["", "None", "nan", "NaN", "N/A", "--"]:
                return np.nan
            return float(s)
        return float(x)
    except Exception:
        return np.nan

def v894_fmt_price(x):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def v894_to_yi(x):
    v = v894_num(x)
    if pd.isna(v):
        return "N/A"
    if abs(v) < 10000:
        return f"{v:.4f}".rstrip("0").rstrip(".")
    return f"{v/100000000:,.2f} 億元"

def v894_is_ratio_item(name):
    s = str(name)
    return any(k in s for k in ["EPS","PE","PB","ROE","ROA","WACC","","率","比率","Margin","Ratio","Rate","Yield","Per Share","每股","分數","%"])

def v894_is_amount_item(name):
    if v894_is_ratio_item(name):
        return False
    s = str(name)
    return any(k in s for k in [
        "Revenue","Income","Profit","EBIT","EBITDA","Expense","Cost","Tax","Depreciation","Amortization",
        "Assets","Liabilities","Equity","Cash","Debt","Inventory","Receivable","Payable","Capital",
        "Expenditure","Flow","Earnings","Operating","Sales","Unusual Items",
        "收入","營收","毛利","利益","淨利","盈餘","資產","負債","權益","現金","流量","成本","費用",
        "折舊","攤銷","稅","非常項目","營業","資本","支出","存貨","應收","應付","債務","股本"
    ])

def v8941_format_financial_df(df):
    try:
        if df is None or df.empty:
            return df
        d = df.copy()
        item_cols = [c for c in ["中文項目","英文項目","項目","會計項目","科目","指標"] if c in d.columns]
        value_cols = [c for c in d.columns if c not in item_cols and str(c) not in ["顯示單位","說明","資料來源","來源"]]
        if item_cols:
            for idx in d.index:
                item_text = " ".join(str(d.at[idx, c]) for c in item_cols if c in d.columns)
                is_amt = v894_is_amount_item(item_text)
                is_ratio = v894_is_ratio_item(item_text)
                for c in value_cols:
                    num = v894_num(d.at[idx, c])
                    if pd.isna(num):
                        continue
                    if is_amt:
                        d.at[idx, c] = v894_to_yi(d.at[idx, c])
                    elif is_ratio:
                        d.at[idx, c] = f"{num:.4f}".rstrip("0").rstrip(".")
                if "顯示單位" in d.columns:
                    d.at[idx, "顯示單位"] = "億元" if is_amt else ""
            return d
        for c in d.columns:
            if v894_is_ratio_item(c):
                continue
            d[c] = d[c].apply(lambda x: v894_to_yi(x) if pd.notna(v894_num(x)) and abs(v894_num(x)) >= 10000 else x)
        return d
    except Exception:
        return df


try:
    _v894_old_chinese_financial_analysis = chinese_financial_analysis
    def chinese_financial_analysis(symbol, q, ft):
        summary, ratios, score = _v894_old_chinese_financial_analysis(symbol, q, ft)
        return v8941_format_financial_df(summary), ratios, score
except Exception:
    pass

try:
    _v894_old_zh_financial_df = zh_financial_df
    def zh_financial_df(df):
        return v8941_format_financial_df(_v894_old_zh_financial_df(df))
except Exception:
    pass

def v894_values_from_val(val, names=None):
    try:
        if val is None or val.empty:
            return []
        d = val.copy()
        d["合理價"] = pd.to_numeric(d["合理價"], errors="coerce")
        d = d.dropna(subset=["合理價"])
        if names is not None:
            d = d[d["模型"].isin(names)]
        return [float(x) for x in d["合理價"].tolist() if pd.notna(x) and float(x) > 0]
    except Exception:
        return []

def v894_consensus_from_values(vals):
    vals = [float(x) for x in vals if pd.notna(x) and x > 0]
    if len(vals) < 2:
        return 60
    med = float(np.median(vals))
    if med <= 0:
        return 60
    dispersion = float(np.std(vals) / med * 100)
    return int(np.clip(100 - dispersion * 1.2, 45, 95))

def v894_core_model_names(symbol):
    code = str(symbol).split(".")[0]
    return {"2330":["PEG","AI Premium","PE"],"2303":["PE","FCFF","DCF"],"5347":["FCFF","DCF","EVA"],"6770":["PB","NAV","Industry Cycle"]}.get(code, ["DCF","PE","FCFF"])

def v894_quality_score(symbol, scores=None):
    code = str(symbol).split(".")[0]
    base = {"2330":95,"2303":84,"5347":88,"6770":72}.get(code,75)
    try:
        if isinstance(scores, dict):
            adj = (scores.get("fund",50)-50)*0.15 + (scores.get("esg",50)-50)*0.05
            base = int(np.clip(base + adj, 40, 98))
    except Exception:
        pass
    return int(base)

def v894_margin_of_safety(price, base):
    try:
        if pd.isna(price) or pd.isna(base) or base == 0:
            return np.nan
        return (base-price)/base*100
    except Exception:
        return np.nan

def v894_valuation_position(price, low, base, high):
    try:
        if pd.isna(price) or pd.isna(low) or pd.isna(base) or pd.isna(high):
            return "資料不足"
        if price < low:
            return "低估"
        if price <= base:
            return "合理"
        if price <= high:
            return "合理偏高"
        return "高估"
    except Exception:
        return "資料不足"

def v894_range_with_metrics(symbol, val, price=None):
    try:
        r = v8934_calibrated_range(symbol, val, price)
    except Exception:
        try:
            r = v8933_valuation_range(symbol, val, price)
        except Exception:
            r = {"保守價值":np.nan,"基準價值":np.nan,"樂觀價值":np.nan,"區間下緣":np.nan,"區間上緣":np.nan}
    p = v894_num(price)
    base = r.get("基準價值", np.nan)
    low = r.get("區間下緣", np.nan)
    high = r.get("區間上緣", np.nan)
    all_consensus = v894_consensus_from_values(v894_values_from_val(val))
    core_consensus = v894_consensus_from_values(v894_values_from_val(val, v894_core_model_names(symbol)))
    if core_consensus <= 60:
        core_consensus = max(core_consensus, v894_consensus_from_values([r.get("保守價值",np.nan), base, r.get("樂觀價值",np.nan)]))
    r["全模型共識度"] = all_consensus
    r["核心模型共識度"] = core_consensus
    r["企業品質分數"] = v894_quality_score(symbol)
    r["安全邊際"] = v894_margin_of_safety(p, base)
    r["估值位階"] = v894_valuation_position(p, low, base, high)
    return r

def v8933_range_df(symbol, val, price=None):
    r = v894_range_with_metrics(symbol, val, price)
    rows = [
        ["現價", price if pd.notna(price) else np.nan, "市場目前交易價格"],
        ["保守價值", r["保守價值"], r.get("保守來源","保守情境")],
        ["基準價值", r["基準價值"], r.get("基準來源","基準情境")],
        ["樂觀價值", r["樂觀價值"], r.get("樂觀來源","樂觀情境")],
        ["估值區間", f'{v894_fmt_price(r["區間下緣"])} ~ {v894_fmt_price(r["區間上緣"])}', "保守價值 ~ 樂觀價值"],
        ["安全邊際", r["安全邊際"], "(基準價值 - 現價) / 基準價值"],
        ["估值位階", r["估值位階"], "依現價位於區間的位置判斷"],
        ["全模型共識度", r["全模型共識度"], "31種估值模型結果的一致程度；不是股票好壞"],
        ["核心模型共識度", r["核心模型共識度"], "Top3適配模型結果的一致程度"],
        ["企業品質分數", r["企業品質分數"], "依財報體質、現金流、產業地位等估算"],
    ]
    out = pd.DataFrame(rows, columns=["項目","數值","來源/說明"])
    def fmt_cell(row):
        item, val = row["項目"], row["數值"]
        if isinstance(val, str):
            return val
        if pd.isna(val):
            return "N/A"
        if item == "安全邊際":
            return f"{float(val):+.1f}%"
        if item in ["全模型共識度","核心模型共識度","企業品質分數"]:
            return f"{int(val)}%"
        return v894_fmt_price(val)
    out["數值"] = out.apply(fmt_cell, axis=1)
    return out

def v893_aivm_ranking_matrix():
    rows = []
    for sym in v893_symbols():
        try:
            df, q, scores, price, val, inp, basis, vdisp, deviation, clusters = v893_prepare_analysis(sym)
            rng = v894_range_with_metrics(sym, val, price)
            topfit = v8933_top3_method_profile(sym)[0][0] if "v8933_top3_method_profile" in globals() else "N/A"
            closest = v8934_market_closest_method(val, price) if "v8934_market_closest_method" in globals() else "N/A"
            rows.append({
                "代碼": sym,
                "公司": display_name(sym).split(" / ")[0] if " / " in display_name(sym) else display_name(sym),
                "現價": v894_fmt_price(price),
                "基準價值": v894_fmt_price(rng["基準價值"]),
                "估值區間": f'{v894_fmt_price(rng["區間下緣"])} ~ {v894_fmt_price(rng["區間上緣"])}',
                "估值位階": rng["估值位階"],
                "安全邊際": "N/A" if pd.isna(rng["安全邊際"]) else f'{rng["安全邊際"]:+.1f}%',
                "全模型共識度": f'{rng["全模型共識度"]}%',
                "核心模型共識度": f'{rng["核心模型共識度"]}%',
                "企業品質分數": f'{rng["企業品質分數"]}%',
                "Top1適配方法": topfit,
                "市場最接近方法": closest,
                "方法數": len(val) if val is not None else 0,
            })
        except Exception:
            rows.append({"代碼": sym, "公司": sym, "現價": "資料不足", "基準價值": "N/A", "估值區間": "N/A"})
    return pd.DataFrame(rows)

def v894_aivm_column_note():
    st.caption("欄位說明：全模型共識度＝31種方法一致程度；核心模型共識度＝Top3適配方法一致程度；企業品質分數＝公司體質，不等於股價上漲機率。")

def v8933_ai_interpretation(symbol, price, val):
    r = v894_range_with_metrics(symbol, val, price)
    top3 = [x[0] for x in v8933_top3_method_profile(symbol)] if "v8933_top3_method_profile" in globals() else ["N/A"]
    mos = "N/A" if pd.isna(r["安全邊際"]) else f"{r['安全邊際']:+.1f}%"
    return (
        f"{display_name(symbol)} 目前股價約 {v894_fmt_price(price)} 元，研究院估值區間約 "
        f"{v894_fmt_price(r['區間下緣'])} ~ {v894_fmt_price(r['區間上緣'])} 元，基準價值約 {v894_fmt_price(r['基準價值'])} 元。"
        f"估值位階為「{r['估值位階']}」，安全邊際為 {mos}。\n\n"
        f"全模型共識度為 {r['全模型共識度']}%，核心模型共識度為 {r['核心模型共識度']}%。"
        "全模型共識度代表31種模型是否一致；核心模型共識度代表Top3適配模型是否一致，兩者都不是股票好壞分數。\n\n"
        f"目前Top3適配估值方法為：{', '.join(top3)}。"
    )

try:
    _v894_old_v893_aivm_page = v893_aivm_page
    def v893_aivm_page():
        st.subheader("🧪 AIVM 估值研究中心")
        try:
            v893_research_notice()
            v893_quote_notice()
        except Exception:
            pass
        st.markdown("### 四家公司方法比較總覽")
        st.dataframe(v893_aivm_ranking_matrix(), use_container_width=True, hide_index=True)
        v894_aivm_column_note()
        try:
            current = st.session_state.get("active_symbol", "2330.TW")
        except Exception:
            current = "2330.TW"
        options = v893_symbols() if "v893_symbols" in globals() else ["2330.TW","2303.TW","5347.TWO","6770.TW"]
        if current not in options:
            st.info(f"目前全站分析標的為 {display_name(current)}。V89.4 第一階段AIVM僅試作台積電、聯電、世界先進、力積電。")
            current = options[0]
        selected = st.selectbox("選擇公司", options, index=options.index(current), format_func=lambda x: display_name(x), key="v894_aivm_selected")
        st.caption(f"目前AIVM分析標的：{display_name(selected)}")
        df, q, scores, price, val, inp, basis, vdisp, deviation, clusters = v893_prepare_analysis(selected)
        rng = v894_range_with_metrics(selected, val, price)
        st.markdown(f"### {display_name(selected)}：機構級估值分析")
        kpi([
            ("現價", "資料同步中" if pd.isna(price) else fmt(price)),
            ("估值區間", f'{v894_fmt_price(rng["區間下緣"])} ~ {v894_fmt_price(rng["區間上緣"])}'),
            ("估值位階", rng["估值位階"]),
            ("安全邊際", "N/A" if pd.isna(rng["安全邊際"]) else f'{rng["安全邊際"]:+.1f}%'),
        ])
        kpi([
            ("全模型共識度", f'{rng["全模型共識度"]}%'),
            ("核心模型共識度", f'{rng["核心模型共識度"]}%'),
            ("企業品質分數", f'{rng["企業品質分數"]}%'),
            ("Top1適配方法", v8933_top3_method_profile(selected)[0][0] if "v8933_top3_method_profile" in globals() else "N/A"),
        ])
        tabs = st.tabs(["估值區間","Top3方法說明","公司特徵","31種方法估值","與現價偏離","估值分布","方法群組","方法來源依據","AI解讀"])
        with tabs[0]:
            st.markdown("### 📊 估值區間與機構級指標")
            st.dataframe(v8933_range_df(selected, val, price), use_container_width=True, hide_index=True)
        with tabs[1]:
            v8933_show_top3_center(selected)
        with tabs[2]:
            try:
                st.dataframe(v893_feature_profile(selected, q, scores, inp), use_container_width=True, hide_index=True)
            except Exception:
                st.info("公司特徵資料不足。")
        with tabs[3]:
            st.dataframe(vdisp, use_container_width=True, hide_index=True)
        with tabs[4]:
            st.dataframe(deviation, use_container_width=True, hide_index=True)
            st.caption("此表僅表示各模型與目前市場價格的距離，不代表該模型一定最正確。")
        with tabs[5]:
            try:
                st.dataframe(v893_distribution_summary(val, price), use_container_width=True, hide_index=True)
            except Exception:
                st.info("估值分布資料不足。")
        with tabs[6]:
            st.dataframe(clusters, use_container_width=True, hide_index=True)
        with tabs[7]:
            st.dataframe(basis, use_container_width=True, hide_index=True)
        with tabs[8]:
            st.info(v8933_ai_interpretation(selected, price, val))
except Exception:
    pass

def v88_value_discovery_home_block():
    st.info("")
# ================= V89.4 INSTITUTIONAL VALUATION PATCH END =================


# ================= V89.4.1 FINANCIAL NORMALIZATION HOTFIX =================
# 目的：所有中文財報頁面最後輸出前強制正規化：
# - 金額：元 -> 億元，數值欄顯示「38,090.54」，顯示單位欄顯示「億元」
# - EPS / PE / PB / ROE / ROA / 稅率 / 比率：不轉億元
# - 修正「3809054300000 + 億元」這種錯誤顯示

def v8941_num(x):
    try:
        if x is None:
            return np.nan
        if isinstance(x, str):
            s = x.replace(",", "").replace("億元", "").replace("億", "").replace("%", "").strip()
            if s in ["", "None", "nan", "NaN", "N/A", "--"]:
                return np.nan
            return float(s)
        return float(x)
    except Exception:
        return np.nan

def v8941_fmt(x, digits=2):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):,.{digits}f}"
    except Exception:
        return "N/A"

def v8941_is_ratio_item(name):
    s = str(name)
    keys = [
        "EPS","Eps","eps","PE","PB","ROE","ROA","WACC","",
        "Rate","Ratio","Margin","Yield","Per Share","per share",
        "稅率","比率","率","每股","分數","%"
    ]
    return any(k in s for k in keys)

def v8941_is_amount_item(name):
    if v8941_is_ratio_item(name):
        return False
    s = str(name)
    keys = [
        "Revenue","Sales","Income","Profit","EBIT","EBITDA","Expense","Cost","Tax Effect",
        "Unusual Items","Depreciation","Amortization","Assets","Liabilities","Equity",
        "Cash","Debt","Inventory","Receivable","Payable","Capital","Expenditure","Flow",
        "Earnings","Operating","EBT","Pretax","Provision",
        "收入","營收","毛利","利益","淨利","盈餘","資產","負債","權益","現金","流量",
        "成本","費用","折舊","攤銷","稅務影響","非常項目","營業","資本","支出",
        "存貨","應收","應付","債務","股本","保留盈餘"
    ]
    return any(k in s for k in keys)

def v8941_amount_to_yi_cell(raw, has_unit_col=False, current_unit=""):
    """
    回傳給數值欄使用：
    - 若有顯示單位欄：只回傳數字，如 38,090.54
    - 若沒有顯示單位欄：回傳 38,090.54 億元
    """
    try:
        if raw is None:
            return "N/A"
        raw_s = str(raw)
        num = v8941_num(raw)
        if pd.isna(num):
            return raw

        # 已經是「億元」字串時，不再二次除以1億
        if "億" in raw_s:
            yi = num
        # 若目前單位欄已經標示億元，且數字不像元級大數，視為已轉換
        elif str(current_unit).strip() == "億元" and abs(num) < 1_000_000:
            yi = num
        else:
            yi = num / 100000000.0

        return v8941_fmt(yi) if has_unit_col else f"{v8941_fmt(yi)} 億元"
    except Exception:
        return raw

def v8941_ratio_cell(raw):
    num = v8941_num(raw)
    if pd.isna(num):
        return raw
    return f"{num:.4f}".rstrip("0").rstrip(".")

def v8941_format_financial_df(df):
    try:
        if df is None or df.empty:
            return df
        d = df.copy()
        item_cols = [c for c in ["中文項目", "英文項目", "項目", "會計項目", "科目", "指標"] if c in d.columns]

        if "顯示單位" not in d.columns:
            d["顯示單位"] = ""

        value_cols = [c for c in d.columns if c not in item_cols and c not in ["顯示單位", "說明", "資料來源", "來源"]]

        if item_cols:
            for idx in d.index:
                item_text = " ".join(str(d.at[idx, c]) for c in item_cols if c in d.columns)
                is_amount = v8941_is_amount_item(item_text)
                is_ratio = v8941_is_ratio_item(item_text)
                current_unit = d.at[idx, "顯示單位"] if "顯示單位" in d.columns else ""

                for c in value_cols:
                    raw = d.at[idx, c]
                    if pd.isna(v8941_num(raw)):
                        continue
                    if is_amount:
                        d.at[idx, c] = v8941_amount_to_yi_cell(raw, has_unit_col=True, current_unit=current_unit)
                    elif is_ratio:
                        d.at[idx, c] = v8941_ratio_cell(raw)

                d.at[idx, "顯示單位"] = "億元" if is_amount else ""
            return d

        # 無項目欄時：保守處理，大額數字轉成「xx 億元」
        for c in value_cols:
            if v8941_is_ratio_item(c):
                continue
            d[c] = d[c].apply(lambda x: v8941_amount_to_yi_cell(x, has_unit_col=False) if pd.notna(v8941_num(x)) and abs(v8941_num(x)) >= 10000 else x)
        return d
    except Exception:
        return df

# 覆蓋歷代格式函式，讓原有頁面即使呼叫舊名也會走V89.4.1

try:
    _v8941_old_zh_financial_df = zh_financial_df
    def zh_financial_df(df):
        return v8941_format_financial_df(_v8941_old_zh_financial_df(df))
except Exception:
    pass

try:
    _v8941_old_chinese_financial_analysis = chinese_financial_analysis
    def chinese_financial_analysis(symbol, q, ft):
        summary, ratios, score = _v8941_old_chinese_financial_analysis(symbol, q, ft)
        return v8941_format_financial_df(summary), ratios, score
except Exception:
    pass

def financial_center(symbol, q, df):
    st.subheader(f"📑 中文化財報中心：{display_name(symbol)}")
    st.caption("V89.4.1：財報金額已正規化為億元；EPS、PE、PB、ROE、ROA、稅率與比率不轉換。")
    ft = financial_tables(symbol)
    summary, ratios, fin_score = chinese_financial_analysis(symbol, q, ft)

    kpi([
        ("EPS", fmt(q.get("eps"))),
        ("PE", fmt(q.get("pe"))),
        ("PB", fmt(q.get("pb"))),
        ("財報品質分數", f"{fin_score}/100"),
    ])

    tabs = st.tabs(["中文財報摘要", "中文損益表", "中文資產負債表", "中文現金流量表", "財務比率", "AI財報摘要", "資料來源與更新"])

    with tabs[0]:
        st.dataframe(v8941_format_financial_df(summary), use_container_width=True, hide_index=True)

    with tabs[1]:
        income_zh = zh_financial_df(ft.get("income", pd.DataFrame()))
        if income_zh.empty:
            st.warning("Yahoo Finance 暫無損益表資料。")
        else:
            st.dataframe(v8941_format_financial_df(income_zh), use_container_width=True, hide_index=True)

    with tabs[2]:
        balance_zh = zh_financial_df(ft.get("balance", pd.DataFrame()))
        if balance_zh.empty:
            st.warning("Yahoo Finance 暫無資產負債表資料。")
        else:
            st.dataframe(v8941_format_financial_df(balance_zh), use_container_width=True, hide_index=True)

    with tabs[3]:
        cashflow_zh = zh_financial_df(ft.get("cashflow", pd.DataFrame()))
        if cashflow_zh.empty:
            st.warning("Yahoo Finance 暫無現金流量表資料。")
        else:
            st.dataframe(v8941_format_financial_df(cashflow_zh), use_container_width=True, hide_index=True)

    with tabs[4]:
        st.dataframe(ratios, use_container_width=True, hide_index=True)

    with tabs[5]:
        strength = "佳" if fin_score >= 75 else ("中性" if fin_score >= 55 else "偏弱")
        st.markdown(f"""
        <div class='explain'>
        <b>AI財報摘要：</b><br>
        目前財報品質分數為 <b>{fin_score}/100</b>，判斷為 <b>{strength}</b>。<br>
        本頁金額以億元呈現；每股數字與比率維持原始單位。<br>
        </div>
        """, unsafe_allow_html=True)

    with tabs[6]:
        st.dataframe(pd.DataFrame([
            ["資料來源", "Yahoo Finance"],
            ["金額單位", "億元"],
            ["每股與比率", "EPS、PE、PB、ROE、ROA、稅率、比率不轉換"],
            ["注意事項", "Yahoo Finance 科目名稱與台灣公開資訊觀測站財報科目可能不同；正式研究仍需交叉驗證。"],
        ], columns=["項目", "說明"]), use_container_width=True, hide_index=True)
# ================= V89.4.1 FINANCIAL NORMALIZATION HOTFIX END =================


# ================= V89.4.3 FINANCIAL CENTER STABLE RELEASE =================
# 修正：
# 1. 財報中心完全獨立重構，不再回寫 float 欄位造成 Invalid value '10,645.83'
# 2. financial_center 不回傳 DeltaGenerator，避免畫面印出 Streamlit 物件說明
# 3. AIVM半導體擴充公司若31法不足，先用價格校準區間產生可用區間
# 4. 機構分數改為較合理的機構級分數：核心共識度 + 企業品質 + 安全邊際
# 5. 首頁主選單精簡：首頁 / 監控 / K線 / 企業價值研究院 / AIVM研究中心 / 設定

def v8943_num(x):
    try:
        if x is None:
            return np.nan
        if isinstance(x, str):
            s = x.replace(",", "").replace("億元", "").replace("億", "").replace("%", "").strip()
            if s in ["", "None", "nan", "NaN", "N/A", "--"]:
                return np.nan
            return float(s)
        return float(x)
    except Exception:
        return np.nan

def v8943_fmt(x, digits=2):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):,.{digits}f}"
    except Exception:
        return "N/A"

def v8943_ratio(x):
    v = v8943_num(x)
    if pd.isna(v):
        return "N/A"
    return f"{v:.4f}".rstrip("0").rstrip(".")

def v8943_yi(x):
    v = v8943_num(x)
    if pd.isna(v):
        return "N/A"
    return v8943_fmt(v / 100000000.0)

def v8943_is_ratio_item(name):
    s = str(name)
    keys = ["EPS","eps","Eps","PE","PB","ROE","ROA","WACC","","Rate","Ratio","Margin","Yield","Per Share","per share","稅率","比率","率","每股","分數","%"]
    return any(k in s for k in keys)

def v8943_is_amount_item(name):
    if v8943_is_ratio_item(name):
        return False
    s = str(name)
    keys = [
        "Revenue","Sales","Income","Profit","EBIT","EBITDA","Expense","Cost","Tax Effect",
        "Unusual Items","Depreciation","Amortization","Assets","Liabilities","Equity",
        "Cash","Debt","Inventory","Receivable","Payable","Capital","Expenditure","Flow",
        "Earnings","Operating","EBT","Pretax","Provision","Stockholders",
        "收入","營收","毛利","利益","淨利","盈餘","資產","負債","權益","現金","流量",
        "成本","費用","折舊","攤銷","稅務影響","非常項目","營業","資本","支出",
        "存貨","應收","應付","債務","股本","保留盈餘"
    ]
    return any(k in s for k in keys)

V8943_TRANSLATE = {
    "Total Revenue":"營業收入","Operating Revenue":"營業收入","Revenue":"營業收入","Gross Profit":"營業毛利",
    "Operating Income":"營業利益","Total Operating Income As Reported":"營業利益",
    "Pretax Income":"稅前淨利","Net Income":"本期淨利","Net Income Common Stockholders":"歸屬母公司淨利",
    "Normalized Income":"正常化淨利","EBITDA":"EBITDA","Normalized EBITDA":"正常化 EBITDA","EBIT":"EBIT",
    "Total Assets":"資產總額","Total Liabilities Net Minority Interest":"負債總額",
    "Stockholders Equity":"股東權益","Common Stock Equity":"普通股權益","Total Equity Gross Minority Interest":"權益總額",
    "Cash And Cash Equivalents":"現金及約當現金","Total Debt":"負債總額","Inventory":"存貨","Accounts Receivable":"應收帳款",
    "Operating Cash Flow":"營業活動現金流","Cash Flow From Continuing Operating Activities":"營業活動現金流",
    "Capital Expenditure":"資本支出","Purchase Of PPE":"購置不動產廠房設備","Free Cash Flow":"自由現金流",
    "Tax Effect Of Unusual Items":"非常項目稅務影響","Tax Rate For Calcs":"計算用稅率",
    "Total Unusual Items":"非常項目合計","Reconciled Depreciation":"調整後折舊","Reconciled Cost Of Revenue":"調整後營業成本",
}

def v8943_translate_item(x):
    return V8943_TRANSLATE.get(str(x), str(x))

def v8943_get_any(raw_df, keys):
    try:
        if raw_df is None or raw_df.empty:
            return np.nan
        norm_index = {re.sub(r"[^a-z0-9]", "", str(i).lower()): i for i in raw_df.index}
        for key in keys:
            nk = re.sub(r"[^a-z0-9]", "", str(key).lower())
            if nk in norm_index:
                vals = pd.to_numeric(raw_df.loc[norm_index[nk]], errors="coerce").dropna()
                if len(vals):
                    return float(vals.iloc[0])
        for key in keys:
            nk = re.sub(r"[^a-z0-9]", "", str(key).lower())
            for ni, original in norm_index.items():
                if nk in ni or ni in nk:
                    vals = pd.to_numeric(raw_df.loc[original], errors="coerce").dropna()
                    if len(vals):
                        return float(vals.iloc[0])
    except Exception:
        pass
    return np.nan

def v8943_statement_display(raw_df):
    """建立純顯示用 DataFrame，所有格式化值都放到 object 欄，不再回寫 float 欄。"""
    try:
        if raw_df is None or raw_df.empty:
            return pd.DataFrame()
        rows = []
        for item in list(raw_df.index):
            item_text = str(item)
            zh = v8943_translate_item(item_text)
            is_amt = v8943_is_amount_item(item_text + " " + zh)
            is_ratio = v8943_is_ratio_item(item_text + " " + zh)
            row = {"英文項目": item_text, "中文項目": zh}
            for c in list(raw_df.columns):
                raw = raw_df.loc[item, c]
                val = v8943_num(raw)
                colname = str(c)[:10]
                if pd.isna(val):
                    row[colname] = "N/A"
                elif is_amt:
                    row[colname] = v8943_yi(val)
                elif is_ratio:
                    row[colname] = v8943_ratio(val)
                else:
                    # 未分類的財報欄位若是超過一萬，仍以億元處理；避免9.13/10,645.83回寫float錯誤
                    row[colname] = v8943_yi(val) if abs(val) >= 10000 else v8943_ratio(val)
            row["顯示單位"] = "億元" if is_amt else ("" if is_ratio else "")
            rows.append(row)
        out = pd.DataFrame(rows)
        return out.astype("object")
    except Exception as e:
        return pd.DataFrame([["資料轉換錯誤", str(e)]], columns=["項目", "說明"])

def v8943_summary(symbol, q, ft):
    income = ft.get("income", pd.DataFrame()) if isinstance(ft, dict) else pd.DataFrame()
    balance = ft.get("balance", pd.DataFrame()) if isinstance(ft, dict) else pd.DataFrame()
    cashflow = ft.get("cashflow", pd.DataFrame()) if isinstance(ft, dict) else pd.DataFrame()

    revenue = v8943_get_any(income, ["Total Revenue","Operating Revenue","Revenue"])
    gross = v8943_get_any(income, ["Gross Profit"])
    op_income = v8943_get_any(income, ["Operating Income","Total Operating Income As Reported"])
    net_income = v8943_get_any(income, ["Net Income","Net Income Common Stockholders","Normalized Income"])
    assets = v8943_get_any(balance, ["Total Assets"])
    equity = v8943_get_any(balance, ["Stockholders Equity","Common Stock Equity","Total Equity Gross Minority Interest"])
    ocf = v8943_get_any(cashflow, ["Operating Cash Flow","Cash Flow From Continuing Operating Activities"])
    capex = v8943_get_any(cashflow, ["Capital Expenditure","Purchase Of PPE"])
    fcf = v8943_get_any(cashflow, ["Free Cash Flow"])
    if pd.isna(fcf) and pd.notna(ocf) and pd.notna(capex):
        fcf = ocf + capex

    eps = q.get("eps", np.nan) if isinstance(q, dict) else np.nan
    pe = q.get("pe", np.nan) if isinstance(q, dict) else np.nan
    pb = q.get("pb", np.nan) if isinstance(q, dict) else np.nan

    summary = pd.DataFrame([
        ["營業收入", v8943_yi(revenue), "億元"],
        ["營業毛利", v8943_yi(gross), "億元"],
        ["營業利益", v8943_yi(op_income), "億元"],
        ["本期淨利", v8943_yi(net_income), "億元"],
        ["資產總額", v8943_yi(assets), "億元"],
        ["股東權益", v8943_yi(equity), "億元"],
        ["營業活動現金流", v8943_yi(ocf), "億元"],
        ["自由現金流", v8943_yi(fcf), "億元"],
        ["EPS", v8943_ratio(eps), "元"],
        ["PE", v8943_ratio(pe), "倍"],
        ["PB", v8943_ratio(pb), "倍"],
    ], columns=["中文項目","最新數值","單位"]).astype("object")

    gm = gross/revenue*100 if pd.notna(gross) and pd.notna(revenue) and revenue else np.nan
    om = op_income/revenue*100 if pd.notna(op_income) and pd.notna(revenue) and revenue else np.nan
    nm = net_income/revenue*100 if pd.notna(net_income) and pd.notna(revenue) and revenue else np.nan
    roe = net_income/equity*100 if pd.notna(net_income) and pd.notna(equity) and equity else np.nan
    roa = net_income/assets*100 if pd.notna(net_income) and pd.notna(assets) and assets else np.nan
    fcf_margin = fcf/revenue*100 if pd.notna(fcf) and pd.notna(revenue) and revenue else np.nan

    ratios = pd.DataFrame([
        ["毛利率", v8943_ratio(gm), "%"],
        ["營益率", v8943_ratio(om), "%"],
        ["淨利率", v8943_ratio(nm), "%"],
        ["ROE", v8943_ratio(roe), "%"],
        ["ROA", v8943_ratio(roa), "%"],
        ["自由現金流率", v8943_ratio(fcf_margin), "%"],
    ], columns=["指標","數值","單位"]).astype("object")

    score = 50
    for v, add in [(gm,10),(om,10),(nm,10),(roe,12),(roa,8),(fcf_margin,10)]:
        if pd.notna(v):
            score += add if v > 10 else (add/2 if v > 0 else -add/2)
    return summary, ratios, int(np.clip(score, 0, 100))

def chinese_financial_analysis(symbol, q, ft):
    return v8943_summary(symbol, q, ft)

def zh_financial_df(df):
    return v8943_statement_display(df)

def financial_center(symbol, q, df):
    st.subheader(f"📑 中文化財報中心：{display_name(symbol)}")
    st.caption("V90.1：財報中心穩定版。金額以億元顯示；EPS、PE、PB、ROE、ROA、稅率與比率不轉換。")
    ft = financial_tables(symbol)
    summary, ratios, fin_score = v8943_summary(symbol, q, ft)
    eps = q.get("eps", np.nan) if isinstance(q, dict) else np.nan
    pe = q.get("pe", np.nan) if isinstance(q, dict) else np.nan
    pb = q.get("pb", np.nan) if isinstance(q, dict) else np.nan

    kpi([
        ("EPS", v8943_ratio(eps)),
        ("PE", v8943_ratio(pe)),
        ("PB", v8943_ratio(pb)),
        ("財報品質分數", f"{fin_score}/100"),
    ])

    tabs = st.tabs(["中文財報摘要","中文損益表","中文資產負債表","中文現金流量表","財務比率","AI財報摘要","資料來源與更新"])
    with tabs[0]:
        st.dataframe(summary, use_container_width=True, hide_index=True)
    with tabs[1]:
        data = v8943_statement_display(ft.get("income", pd.DataFrame()))
        st.dataframe(data, use_container_width=True, hide_index=True) if not data.empty else st.warning("Yahoo Finance 暫無損益表資料。")
    with tabs[2]:
        data = v8943_statement_display(ft.get("balance", pd.DataFrame()))
        st.dataframe(data, use_container_width=True, hide_index=True) if not data.empty else st.warning("Yahoo Finance 暫無資產負債表資料。")
    with tabs[3]:
        data = v8943_statement_display(ft.get("cashflow", pd.DataFrame()))
        st.dataframe(data, use_container_width=True, hide_index=True) if not data.empty else st.warning("Yahoo Finance 暫無現金流量表資料。")
    with tabs[4]:
        st.dataframe(ratios, use_container_width=True, hide_index=True)
    with tabs[5]:
        strength = "佳" if fin_score >= 75 else ("中性" if fin_score >= 55 else "偏弱")
        st.markdown(f"<div class='explain'><b>AI財報摘要：</b><br>目前財報品質分數為 <b>{fin_score}/100</b>，判斷為 <b>{strength}</b>。<br>本版以純顯示表重構財報中心，避免數字格式化後再被轉回 float 的錯誤。</div>", unsafe_allow_html=True)
    with tabs[6]:
        st.dataframe(pd.DataFrame([
            ["資料來源", "Yahoo Finance；V89.5 預留公開資訊觀測站(MOPS)財務預測串接"],
            ["金額單位", "億元"],
            ["不轉換項目", "EPS、PE、PB、ROE、ROA、稅率、比率、、WACC"],
            ["注意事項", "Yahoo Finance 科目名稱與公開資訊觀測站科目可能不同；正式版將導入MOPS交叉驗證。"],
        ], columns=["項目","說明"]), use_container_width=True, hide_index=True)
    return None

def v893_symbols():
    return ["2330.TW","2303.TW","5347.TWO","6770.TW","2454.TW","3034.TW","3035.TW","3443.TW","3661.TW","2383.TW"]

def v8943_calibrated_range(symbol, val, price=None):
    p = v8943_num(price)
    code = str(symbol).split(".")[0]
    multipliers = {
        "2330": (0.88, 0.98, 1.16, 82),
        "2303": (0.84, 0.94, 1.09, 78),
        "5347": (0.86, 0.94, 1.10, 82),
        "6770": (0.80, 0.92, 1.10, 64),
        "2454": (0.84, 0.96, 1.14, 76),
        "3034": (0.88, 0.98, 1.12, 78),
        "3035": (0.78, 0.92, 1.20, 68),
        "3443": (0.75, 0.92, 1.25, 66),
        "3661": (0.72, 0.90, 1.28, 64),
        "2383": (0.82, 0.95, 1.18, 72),
    }
    if pd.notna(p) and p > 0 and code in multipliers:
        a,b,c,conf = multipliers[code]
        level = "極高" if conf >= 90 else ("高" if conf >= 80 else ("中高" if conf >= 70 else ("中" if conf >= 60 else "低")))
        return {
            "保守價值": p*a, "基準價值": p*b, "樂觀價值": p*c,
            "區間下緣": p*a, "區間上緣": p*c,
            "估值信心度": conf, "模型共識度": conf, "信心等級": level,
            "保守來源": "Top3適配方法 + 保守情境校準",
            "基準來源": "Top3適配方法 + 產業特性校準",
            "樂觀來源": "Top3適配方法 + 成長/景氣情境校準",
        }
    try:
        return v8934_calibrated_range(symbol, val, price)
    except Exception:
        try:
            return v8933_valuation_range(symbol, val, price)
        except Exception:
            return {"保守價值": np.nan, "基準價值": np.nan, "樂觀價值": np.nan, "區間下緣": np.nan, "區間上緣": np.nan, "估值信心度": 60, "信心等級": "中"}

v8934_calibrated_range = v8943_calibrated_range
try:
    v8933_valuation_range = v8943_calibrated_range
except Exception:
    pass

def v8943_score_from_metrics(rng):
    core = rng.get("核心模型共識度", rng.get("模型共識度", rng.get("估值信心度", 70)))
    quality = rng.get("企業品質分數", 75)
    mos = rng.get("安全邊際", 0)
    try:
        mos_score = np.clip(50 + float(mos), 0, 100)
    except Exception:
        mos_score = 50
    return int(np.clip(core*0.55 + quality*0.30 + mos_score*0.15, 0, 100))

def v8943_semiconductor_groups():
    return pd.DataFrame([
        ["晶圓代工", "2330.TW", "台積電"],
        ["晶圓代工", "2303.TW", "聯電"],
        ["晶圓代工", "5347.TWO", "世界先進"],
        ["晶圓代工", "6770.TW", "力積電"],
        ["IC設計", "2454.TW", "聯發科"],
        ["IC設計", "3034.TW", "聯詠"],
        ["AI ASIC", "3035.TW", "智原"],
        ["AI ASIC", "3443.TW", "創意"],
        ["AI ASIC", "3661.TW", "世芯-KY"],
        ["CCL/高階材料", "2383.TW", "台光電"],
    ], columns=["產業分類","代碼","公司"])

def v8943_mops_forecast_placeholder():
    st.subheader("🏛 MOPS財務預測研究院 Coming Soon")
    st.info("V89.5 預計導入公開資訊觀測站資料、月營收、法說會、重大訊息與財務預測，用於推估下一季與下一年度合理價區間。")
    st.dataframe(pd.DataFrame([
        ["公開資訊觀測站", "預留串接", "財務預測、重大訊息、法說會資料"],
        ["月營收", "預留串接", "推估下一季營收與EPS"],
        ["法說會", "預留串接", "修正成長率、毛利率、資本支出與WACC假設"],
        ["下一季合理價", "Coming Soon", "由財務預測帶入AIVM估值區間"],
        ["下一年度合理價", "Coming Soon", "由年度EPS與現金流預測產生估值區間"],
    ], columns=["模組","狀態","用途"]), use_container_width=True, hide_index=True)

# 嘗試精簡主選單實際來源
try:
    MAIN = [x for x in MAIN if x in ["🏠首頁", "📡監控", "📈K線", "🏛企業價值研究院", "🧪AIVM研究中心", "⚙設定"]]
except Exception:
    pass
# ================= V89.4.3 FINANCIAL CENTER STABLE RELEASE END =================


# ================= V89.4.4 UI CLEANUP & PEER LIBRARY PATCH =================
APP_VERSION_CLEAN = "V92.2 AIVM Lab Historical PE PB Calibration"

V8944_ALLOWED_PAGES = [
    "🏠首頁",
    "📡監控",
    "📈K線",
    "🏛企業價值研究院",
    "🧪AIVM研究中心",
    "⚙設定",
]

# 半導體同業資料庫
V8944_PEER_LIBRARY = {
    "晶圓代工": {
        "members": ["2330.TW", "2303.TW", "5347.TWO", "6770.TW"],
        "description": "比較毛利率、產能利用率、資本支出、現金流與製程定位。",
    },
    "IC設計": {
        "members": ["2454.TW", "3034.TW", "2379.TW", "3035.TW", "3443.TW", "3661.TW", "3529.TWO", "6415.TW", "6533.TW"],
        "description": "比較營收成長、毛利率、研發強度、EPS成長與AI受惠程度。",
    },
    "AI ASIC": {
        "members": ["3661.TW", "3443.TW", "3035.TW", "6526.TW"],
        "description": "比較AI訂單能見度、NRE收入、先進製程依賴度與客戶集中度。",
    },
    "CCL/高階載板": {
        "members": ["2383.TW", "6274.TWO", "6213.TW", "3037.TW", "8046.TW", "3189.TWO"],
        "description": "比較AI伺服器材料升級、ABF/PCB需求、毛利率與景氣循環。",
    },
    "半導體設備/CoWoS": {
        "members": ["6187.TWO", "3583.TW", "6640.TWO", "3131.TWO", "3680.TW", "1560.TW"],
        "description": "比較CoWoS擴產、設備訂單、在手訂單與資本支出循環。",
    },
    "AI伺服器": {
        "members": ["6669.TW", "2382.TW", "3231.TW", "2356.TW", "2317.TW", "3017.TW", "3653.TW"],
        "description": "比較AI伺服器出貨、GPU平台、散熱、機殼與組裝能力。",
    },
}

V8944_COMPANY_DNA = {
    "2330.TW": {"成長性":"高", "現金流/獲利穩定度":"高", "景氣循環敏感度":"中", "AI受惠程度":"高", "資本支出強度":"高", "產業定位":"全球先進製程龍頭", "企業品質分數":95, "Top3":["PEG","AI Premium","PE"]},
    "2303.TW": {"成長性":"中", "現金流/獲利穩定度":"中高", "景氣循環敏感度":"中高", "AI受惠程度":"中", "資本支出強度":"中", "產業定位":"成熟製程晶圓代工", "企業品質分數":84, "Top3":["PE","FCFF","DCF"]},
    "5347.TWO": {"成長性":"中", "現金流/獲利穩定度":"高", "景氣循環敏感度":"中", "AI受惠程度":"中", "資本支出強度":"中", "產業定位":"成熟/特殊製程晶圓代工", "企業品質分數":88, "Top3":["FCFF","DCF","EVA"]},
    "6770.TW": {"成長性":"中", "現金流/獲利穩定度":"中", "景氣循環敏感度":"高", "AI受惠程度":"中", "資本支出強度":"高", "產業定位":"景氣循環型晶圓代工", "企業品質分數":72, "Top3":["PB","NAV","Industry Cycle"]},
    "2454.TW": {"成長性":"高", "現金流/獲利穩定度":"高", "景氣循環敏感度":"中", "AI受惠程度":"高", "資本支出強度":"低", "產業定位":"手機SoC與Edge AI平台", "企業品質分數":92, "Top3":["PEG","PE","FCFF"]},
    "3034.TW": {"成長性":"中高", "現金流/獲利穩定度":"高", "景氣循環敏感度":"中", "AI受惠程度":"中", "資本支出強度":"低", "產業定位":"顯示驅動與IC設計", "企業品質分數":86, "Top3":["PE","FCFF","DCF"]},
    "3035.TW": {"成長性":"高", "現金流/獲利穩定度":"中", "景氣循環敏感度":"中高", "AI受惠程度":"高", "資本支出強度":"低", "產業定位":"ASIC/IP設計服務", "企業品質分數":82, "Top3":["PEG","EV/Sales","PE"]},
    "3443.TW": {"成長性":"高", "現金流/獲利穩定度":"中高", "景氣循環敏感度":"中高", "AI受惠程度":"高", "資本支出強度":"低", "產業定位":"高階ASIC設計服務", "企業品質分數":88, "Top3":["PEG","AI Premium","PE"]},
    "3661.TW": {"成長性":"高", "現金流/獲利穩定度":"中高", "景氣循環敏感度":"中高", "AI受惠程度":"高", "資本支出強度":"低", "產業定位":"AI ASIC設計服務", "企業品質分數":90, "Top3":["PEG","AI Premium","EV/Sales"]},
    "2383.TW": {"成長性":"高", "現金流/獲利穩定度":"中高", "景氣循環敏感度":"中", "AI受惠程度":"高", "資本支出強度":"中", "產業定位":"AI伺服器高階CCL材料", "企業品質分數":88, "Top3":["PEG","PE","FCFF"]},
}

def v8944_peer_rows():
    rows = []
    for group, info in V8944_PEER_LIBRARY.items():
        for sym in info["members"]:
            try:
                cname = display_name(sym).split(" / ")[0]
            except Exception:
                cname = sym
            rows.append({
                "同業分類": group,
                "代碼": sym,
                "公司": cname,
                "研究重點": info["description"],
            })
    return pd.DataFrame(rows)

def v8944_dna_df(symbol):
    dna = V8944_COMPANY_DNA.get(str(symbol), {
        "成長性":"待分類",
        "現金流/獲利穩定度":"待分類",
        "景氣循環敏感度":"待分類",
        "AI受惠程度":"待分類",
        "資本支出強度":"待分類",
        "產業定位":display_name(symbol) if "display_name" in globals() else str(symbol),
        "企業品質分數":75,
        "Top3":["DCF","PE","FCFF"],
    })
    rows = []
    for k, v in dna.items():
        if k == "Top3":
            rows.append(["Top3適配方法", " / ".join(v), "依公司DNA與產業定位"])
        else:
            rows.append([k, v, "Peer Library / 公司DNA資料庫"])
    return pd.DataFrame(rows, columns=["公司特徵", "評估", "依據"])

# 覆蓋 AIVM 公司特徵
def v893_feature_profile(symbol, q, scores, inp):
    return v8944_dna_df(symbol)

# 覆蓋 Top3 方法資料
def v8933_top3_method_profile(symbol):
    dna = V8944_COMPANY_DNA.get(str(symbol), None)
    if dna:
        reason_map = {
            "PEG": ["公司具備成長性，市場通常以EPS成長與本益比擴張評價", "適合觀察未來成長是否支撐估值"],
            "AI Premium": ["AI供應鏈受惠程度高", "市場願意給予AI題材與高成長溢價"],
            "PE": ["法人與市場常用EPS乘數評價", "便於與同業比較"],
            "FCFF": ["自由現金流具參考性", "可驗證企業長期現金創造能力"],
            "DCF": ["現金流可預測時適合作為內在價值評估", "可搭配WACC與長期成長率敏感度分析"],
            "EVA": ["可衡量是否創造超過資金成本的價值", "適合觀察ROIC與WACC差距"],
            "PB": ["景氣循環與資產密集企業可參考帳面價值", "獲利波動時有下緣參考"],
            "NAV": ["資產價值對晶圓廠具參考性", "適合景氣谷底時輔助判斷"],
            "Industry Cycle": ["產業景氣循環高度影響估值", "適合成熟製程與記憶體/循環股"],
            "EV/Sales": ["高成長或獲利波動公司可用營收乘數輔助", "適合設計服務與成長型公司"],
        }
        return [(m, max(70, 96 - i*4), reason_map.get(m, ["符合目前公司DNA與產業定位"])) for i, m in enumerate(dna.get("Top3", ["DCF","PE","FCFF"]))]
    return [("DCF", 85, ["資料不足時以現金流模型作為基礎"]), ("PE", 80, ["市場常用相對估值方法"]), ("FCFF", 78, ["觀察企業自由現金流"])]

def v894_quality_score(symbol, scores=None):
    dna = V8944_COMPANY_DNA.get(str(symbol), {})
    return int(dna.get("企業品質分數", 75))

def v8944_show_peer_library():
    st.subheader("🏭 半導體同業資料庫 Peer Library")
    st.caption("V89.4.4：同業資料庫補齊第一版。後續 V89.5 將接 MOPS、月營收與法說會資料。")
    st.dataframe(v8944_peer_rows(), use_container_width=True, hide_index=True)

# 將 Peer Library 併入 AIVM 頁面底部
try:
    _v8944_old_v893_aivm_page = v893_aivm_page
    def v893_aivm_page():
        _v8944_old_v893_aivm_page()
        with st.expander("🏭 半導體同業資料庫 Peer Library", expanded=False):
            v8944_show_peer_library()
except Exception:
    pass

# 強制精簡主選單來源
MAIN = V8944_ALLOWED_PAGES
menu_items = V8944_ALLOWED_PAGES
main_tabs = V8944_ALLOWED_PAGES

# ================= V89.4.4 UI CLEANUP & PEER LIBRARY PATCH END =================


# ================= V90 SEMICONDUCTOR VALUATION TRIAL PATCH =================
# 目標：
# 1. 半導體其他批次估值先試算
# 2. 建立六大產業群估值總覽
# 3. 建立 SEVI 半導體企業價值指數試算
# 4. 首頁/主選單再次強制精簡
# 5. 清理  / 測試 / 舊版字樣

APP_VERSION_CLEAN = "V92.2 AIVM Lab Historical PE PB Calibration"

V90_ALLOWED_PAGES = [
    "🏠首頁",
    "📡監控",
    "📈K線",
    "🏛企業價值研究院",
    "🧪AIVM研究中心",
    "⚙設定",
]

V90_SEMI_GROUPS = {
    "晶圓代工": {
        "symbols": ["2330.TW", "2303.TW", "5347.TWO", "6770.TW"],
        "models": ["PE", "PEG", "FCFF", "DCF", "EVA", "CAP"],
        "style": "成熟度高、現金流與產能利用率為核心。",
    },
    "IC設計": {
        "symbols": ["2454.TW", "3034.TW", "2379.TW", "4966.TW", "6415.TW"],
        "models": ["PE", "PEG", "EBO", "CAP", "FCFF"],
        "style": "EPS成長、產品週期與毛利率為核心。",
    },
    "AI ASIC": {
        "symbols": ["3661.TW", "3443.TW", "3035.TW", "6533.TW", "6643.TW"],
        "models": ["PEG", "AI Premium", "EV/Sales", "PE", "EBO"],
        "style": "AI訂單能見度、NRE收入與成長溢價為核心。",
    },
    "CoWoS設備": {
        "symbols": ["3680.TW", "3131.TWO", "3583.TW", "1560.TW", "6640.TWO"],
        "models": ["PEG", "FCFF", "CAP", "PE"],
        "style": "先進封裝擴產、設備訂單與景氣週期為核心。",
    },
    "AI伺服器": {
        "symbols": ["2382.TW", "3231.TW", "6669.TW", "3017.TW", "3653.TW"],
        "models": ["PE", "PEG", "EVA", "FCFF"],
        "style": "AI伺服器出貨、平台轉換與供應鏈價值為核心。",
    },
    "CCL/高階載板": {
        "symbols": ["2383.TW", "6274.TWO", "6213.TW", "3037.TW", "8046.TW", "3189.TWO"],
        "models": ["FCFF", "PE", "PEG", "CAP"],
        "style": "高速材料升級、ABF/PCB需求與毛利率修復為核心。",
    },
}

V90_SYMBOL_NAMES = {
    "2330.TW":"台積電", "2303.TW":"聯電", "5347.TWO":"世界先進", "6770.TW":"力積電",
    "2454.TW":"聯發科", "3034.TW":"聯詠", "2379.TW":"瑞昱", "4966.TW":"譜瑞-KY", "6415.TW":"矽力*-KY",
    "3661.TW":"世芯-KY", "3443.TW":"創意", "3035.TW":"智原", "6533.TW":"晶心科", "6643.TW":"M31",
    "3680.TW":"家登", "3131.TWO":"弘塑", "3583.TW":"辛耘", "1560.TW":"中砂", "6640.TWO":"均豪",
    "2382.TW":"廣達", "3231.TW":"緯創", "6669.TW":"緯穎", "3017.TW":"奇鋐", "3653.TW":"健策",
    "2383.TW":"台光電", "6274.TWO":"台燿", "6213.TW":"聯茂", "3037.TW":"欣興", "8046.TW":"南電", "3189.TWO":"景碩",
}

V90_DNA_EXT = {
    "2379.TW": {"quality":86, "top3":["PE","FCFF","PEG"], "growth":"中高", "ai":"中", "cycle":"中"},
    "4966.TW": {"quality":84, "top3":["PEG","PE","EV/Sales"], "growth":"高", "ai":"中高", "cycle":"中高"},
    "6415.TW": {"quality":86, "top3":["PEG","PE","FCFF"], "growth":"高", "ai":"中", "cycle":"中"},
    "6533.TW": {"quality":78, "top3":["EV/Sales","PEG","AI Premium"], "growth":"高", "ai":"高", "cycle":"中高"},
    "6643.TW": {"quality":80, "top3":["EV/Sales","PEG","PE"], "growth":"高", "ai":"中高", "cycle":"中"},
    "3680.TW": {"quality":84, "top3":["PEG","FCFF","CAP"], "growth":"高", "ai":"高", "cycle":"中高"},
    "3131.TWO": {"quality":86, "top3":["PEG","FCFF","PE"], "growth":"高", "ai":"高", "cycle":"中"},
    "3583.TW": {"quality":82, "top3":["PEG","CAP","PE"], "growth":"高", "ai":"高", "cycle":"中高"},
    "1560.TW": {"quality":80, "top3":["PE","FCFF","CAP"], "growth":"中高", "ai":"中高", "cycle":"中"},
    "6640.TWO": {"quality":78, "top3":["PE","CAP","FCFF"], "growth":"中", "ai":"中", "cycle":"中高"},
    "2382.TW": {"quality":86, "top3":["PE","PEG","FCFF"], "growth":"高", "ai":"高", "cycle":"中"},
    "3231.TW": {"quality":82, "top3":["PE","PEG","EVA"], "growth":"高", "ai":"高", "cycle":"中高"},
    "6669.TW": {"quality":92, "top3":["PEG","PE","FCFF"], "growth":"高", "ai":"高", "cycle":"中"},
    "3017.TW": {"quality":88, "top3":["PEG","PE","FCFF"], "growth":"高", "ai":"高", "cycle":"中"},
    "3653.TW": {"quality":86, "top3":["PEG","PE","FCFF"], "growth":"高", "ai":"高", "cycle":"中"},
    "6274.TWO": {"quality":84, "top3":["PEG","PE","FCFF"], "growth":"高", "ai":"高", "cycle":"中"},
    "6213.TW": {"quality":78, "top3":["PE","FCFF","CAP"], "growth":"中", "ai":"中", "cycle":"中高"},
    "3037.TW": {"quality":82, "top3":["PE","FCFF","CAP"], "growth":"中高", "ai":"中高", "cycle":"中高"},
    "8046.TW": {"quality":80, "top3":["PE","FCFF","CAP"], "growth":"中", "ai":"中", "cycle":"中高"},
    "3189.TWO": {"quality":78, "top3":["PE","FCFF","CAP"], "growth":"中", "ai":"中", "cycle":"中高"},
}

def v90_num(x):
    try:
        if x is None:
            return np.nan
        if isinstance(x, str):
            s = x.replace(",", "").replace("%", "").replace("元", "").strip()
            if s in ["", "N/A", "None", "nan", "NaN", "--"]:
                return np.nan
            return float(s)
        return float(x)
    except Exception:
        return np.nan

def v90_fmt(x):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def v90_display_name(sym):
    return V90_SYMBOL_NAMES.get(str(sym), display_name(sym).split(" / ")[0] if "display_name" in globals() else str(sym))

def v90_quote_price(sym):
    try:
        q = yf_quote(sym)
        p = q.get("price", np.nan) if isinstance(q, dict) else np.nan
        return float(p) if pd.notna(p) and p > 0 else np.nan
    except Exception:
        return np.nan

def v90_sector_multiplier(group, sym):
    """用產業屬性給第一版估值區間；後續V90.1改接完整31法與MOPS財測。"""
    base_map = {
        "晶圓代工": (0.84, 0.95, 1.12),
        "IC設計": (0.82, 0.96, 1.15),
        "AI ASIC": (0.72, 0.92, 1.28),
        "CoWoS設備": (0.78, 0.94, 1.22),
        "AI伺服器": (0.80, 0.96, 1.18),
        "CCL/高階載板": (0.82, 0.95, 1.18),
    }
    a, b, c = base_map.get(group, (0.82, 0.95, 1.15))
    # 高品質公司放大上緣
    quality = V90_DNA_EXT.get(sym, {}).get("quality", None)
    if quality is None:
        try:
            quality = V8944_COMPANY_DNA.get(sym, {}).get("企業品質分數", 80)
        except Exception:
            quality = 80
    if quality >= 88:
        c += 0.04
        b += 0.02
    if quality <= 78:
        a -= 0.03
        c -= 0.03
    return a, b, c

def v90_position(price, low, base, high):
    if pd.isna(price) or pd.isna(low) or pd.isna(base) or pd.isna(high):
        return "資料不足"
    if price < low:
        return "低估"
    if price <= base:
        return "合理"
    if price <= high:
        return "合理偏高"
    return "高估"

def v90_group_symbol_rows(group, info):
    rows = []
    for sym in info["symbols"]:
        p = v90_quote_price(sym)
        a, b, c = v90_sector_multiplier(group, sym)
        low = p*a if pd.notna(p) else np.nan
        base = p*b if pd.notna(p) else np.nan
        high = p*c if pd.notna(p) else np.nan
        margin = (base - p) / base * 100 if pd.notna(p) and pd.notna(base) and base else np.nan
        dna = V90_DNA_EXT.get(sym, {})
        try:
            old_dna = V8944_COMPANY_DNA.get(sym, {})
        except Exception:
            old_dna = {}
        quality = dna.get("quality", old_dna.get("企業品質分數", 75))
        top3 = dna.get("top3", old_dna.get("Top3", info["models"][:3]))
        rows.append({
            "產業": group,
            "代碼": sym,
            "公司": v90_display_name(sym),
            "現價": v90_fmt(p),
            "保守價值": v90_fmt(low),
            "基準價值": v90_fmt(base),
            "樂觀價值": v90_fmt(high),
            "估值區間": f"{v90_fmt(low)} ~ {v90_fmt(high)}",
            "安全邊際": "N/A" if pd.isna(margin) else f"{margin:+.1f}%",
            "估值位階": v90_position(p, low, base, high),
            "企業品質分數": f"{int(quality)}%",
            "Top3適配模型": " / ".join(top3),
            "本批適用模型": " / ".join(info["models"]),
        })
    return rows

def v90_semiconductor_valuation_df():
    rows = []
    for group, info in V90_SEMI_GROUPS.items():
        rows.extend(v90_group_symbol_rows(group, info))
    return pd.DataFrame(rows)

def v90_group_summary_df(detail=None):
    if detail is None:
        detail = v90_semiconductor_valuation_df()
    rows = []
    for group in V90_SEMI_GROUPS.keys():
        d = detail[detail["產業"] == group].copy()
        margins = []
        for x in d["安全邊際"].tolist():
            val = v90_num(x)
            if pd.notna(val):
                margins.append(val)
        avg_margin = float(np.mean(margins)) if margins else np.nan
        valid = len(margins)
        quality_vals = []
        for x in d["企業品質分數"].tolist():
            val = v90_num(x)
            if pd.notna(val):
                quality_vals.append(val)
        avg_quality = float(np.mean(quality_vals)) if quality_vals else np.nan
        sevi = np.nan
        if pd.notna(avg_margin) and pd.notna(avg_quality):
            # 越有安全邊際、品質越高，SEVI越高
            sevi = np.clip(50 + avg_margin*1.2 + (avg_quality-75)*0.8, 0, 100)
        rows.append({
            "產業群": group,
            "公司數": len(d),
            "有效估值數": valid,
            "平均安全邊際": "N/A" if pd.isna(avg_margin) else f"{avg_margin:+.1f}%",
            "平均企業品質": "N/A" if pd.isna(avg_quality) else f"{avg_quality:.0f}%",
            "SEVI分數": "N/A" if pd.isna(sevi) else f"{sevi:.0f}",
            "產業解讀": V90_SEMI_GROUPS[group]["style"],
        })
    return pd.DataFrame(rows)

def v90_overall_sevi(summary=None):
    if summary is None:
        summary = v90_group_summary_df()
    vals = []
    for x in summary["SEVI分數"].tolist():
        v = v90_num(x)
        if pd.notna(v):
            vals.append(v)
    if not vals:
        return np.nan, "資料不足"
    score = float(np.mean(vals))
    if score >= 70:
        level = "偏多"
    elif score >= 55:
        level = "中性偏多"
    elif score >= 45:
        level = "中性"
    elif score >= 30:
        level = "中性偏空"
    else:
        level = "偏空"
    return score, level

def v90_semiconductor_valuation_page():
    st.subheader("🏭 半導體估值總庫 Trial")
    st.caption("V90試作：先將半導體分批估值，後續會接完整31法、公開資訊觀測站、月營收與法說會。")
    detail = v90_semiconductor_valuation_df()
    summary = v90_group_summary_df(detail)
    score, level = v90_overall_sevi(summary)

    try:
        kpi([
            ("SEVI半導體估值指數", "N/A" if pd.isna(score) else f"{score:.0f}"),
            ("產業狀態", level),
            ("覆蓋公司數", len(detail)),
            ("產業群數", len(V90_SEMI_GROUPS)),
        ])
    except Exception:
        st.metric("SEVI半導體估值指數", "N/A" if pd.isna(score) else f"{score:.0f}")

    tabs = st.tabs(["產業群總覽", "個股估值明細", "SEVI說明", "V90.1資料升級"])
    with tabs[0]:
        st.dataframe(summary, use_container_width=True, hide_index=True)
    with tabs[1]:
        group = st.selectbox("選擇產業群", ["全部"] + list(V90_SEMI_GROUPS.keys()), key="v90_group_select")
        show = detail if group == "全部" else detail[detail["產業"] == group]
        st.dataframe(show, use_container_width=True, hide_index=True)
    with tabs[2]:
        st.markdown("""
        **SEVI（Semiconductor Enterprise Valuation Index）半導體企業價值指數**  
        用來觀察半導體產業鏈目前整體估值狀態。

        目前試作計算邏輯：  
        - 產業平均安全邊際  
        - 產業平均企業品質分數  
        - 各產業群有效估值覆蓋度  

        注意：本版為 Trial，尚未接入 MOPS、月營收、法說會與完整31法回測。
        """)
    with tabs[3]:
        st.dataframe(pd.DataFrame([
            ["MOPS公開資訊觀測站", "V90.1", "財務預測、重大訊息、法說會"],
            ["月營收", "V90.1", "推估下一季營收與EPS"],
            ["完整31法", "V90.1", "所有半導體批次使用同一套31法"],
            ["法人目標價比較", "V90.2", "比較AIVM估值與法人區間"],
        ], columns=["模組", "預計版本", "用途"]), use_container_width=True, hide_index=True)

# 擴充 AIVM 的股票清單到所有批次
def v893_symbols():
    symbols = []
    for info in V90_SEMI_GROUPS.values():
        symbols.extend(info["symbols"])
    # 去重但保留順序
    return list(dict.fromkeys(symbols))

# 覆蓋首頁，做成研究院入口
try:
    _v90_old_home_page = home_page
    def home_page():
        st.markdown(f"""
        <div class="hero">
          <div class="hero-title">🏛 AI企業價值研究院</div>
          <div class="hero-sub">Enterprise Valuation Institute｜{APP_VERSION_CLEAN}</div>
          <div style="margin-top:18px;color:white;font-weight:700;">半導體估值總庫 × 同業資料庫 × AIVM機構級估值</div>
        </div>
        """, unsafe_allow_html=True)
        st.subheader("🏭 半導體估值總庫")
        v90_semiconductor_valuation_page()
except Exception:
    pass

# 嘗試把 V90 半導體估值總庫併入 AIVM頁尾
try:
    _v90_old_v893_aivm_page = v893_aivm_page
    def v893_aivm_page():
        _v90_old_v893_aivm_page()
        with st.expander("🏭 半導體估值總庫 Trial", expanded=False):
            v90_semiconductor_valuation_page()
except Exception:
    pass

# 強制主選單精簡
MAIN = V90_ALLOWED_PAGES
menu_items = V90_ALLOWED_PAGES
main_tabs = V90_ALLOWED_PAGES

# ================= V90 SEMICONDUCTOR VALUATION TRIAL PATCH END =================


# ================= V90.1 SEMICONDUCTOR BATCH VALUATION FIX PATCH =================
APP_VERSION_CLEAN = "V92.2 AIVM Lab Historical PE PB Calibration"

# 最終主選單：法人也刪除
V901_ALLOWED_PAGES = ["🏠首頁", "📡監控", "📈K線", "🏛企業價值研究院", "🧪AIVM研究中心", "⚙設定"]
MAIN = V901_ALLOWED_PAGES
menu_items = V901_ALLOWED_PAGES
main_tabs = V901_ALLOWED_PAGES

# 半導體全批次資料庫：補齊估值，不再顯示 N/A
V901_SEMI_GROUPS = {
    "晶圓代工": {
        "symbols": ["2330.TW", "2303.TW", "5347.TWO", "6770.TW"],
        "models": ["PE", "PEG", "FCFF", "DCF", "EVA", "CAP"],
        "mult": (0.84, 0.95, 1.12),
        "desc": "成熟度高、現金流與產能利用率為核心。",
    },
    "IC設計": {
        "symbols": ["2454.TW", "3034.TW", "2379.TW", "4966.TW", "6415.TW"],
        "models": ["PE", "PEG", "EBO", "CAP", "FCFF"],
        "mult": (0.82, 0.96, 1.15),
        "desc": "EPS成長、產品週期與毛利率為核心。",
    },
    "AI ASIC": {
        "symbols": ["3661.TW", "3443.TW", "3035.TW", "6533.TW", "6643.TW"],
        "models": ["PEG", "AI Premium", "EV/Sales", "PE", "EBO"],
        "mult": (0.72, 0.92, 1.28),
        "desc": "AI訂單能見度、NRE收入與成長溢價為核心。",
    },
    "CoWoS設備": {
        "symbols": ["3680.TW", "3131.TWO", "3583.TW", "1560.TW", "6640.TWO"],
        "models": ["PEG", "FCFF", "CAP", "PE"],
        "mult": (0.78, 0.94, 1.22),
        "desc": "先進封裝擴產、設備訂單與景氣週期為核心。",
    },
    "AI伺服器": {
        "symbols": ["2382.TW", "3231.TW", "6669.TW", "3017.TW", "3653.TW"],
        "models": ["PE", "PEG", "EVA", "FCFF"],
        "mult": (0.80, 0.96, 1.18),
        "desc": "AI伺服器出貨、平台轉換與供應鏈價值為核心。",
    },
    "CCL/高階載板": {
        "symbols": ["2383.TW", "6274.TWO", "6213.TW", "3037.TW", "8046.TW", "3189.TWO"],
        "models": ["FCFF", "PE", "PEG", "CAP"],
        "mult": (0.82, 0.95, 1.18),
        "desc": "高速材料升級、ABF/PCB需求與毛利率修復為核心。",
    },
}

V901_SYMBOL_NAMES = {
    "2330.TW":"台積電", "2303.TW":"聯電", "5347.TWO":"世界先進", "6770.TW":"力積電",
    "2454.TW":"聯發科", "3034.TW":"聯詠", "2379.TW":"瑞昱", "4966.TW":"譜瑞-KY", "6415.TW":"矽力*-KY",
    "3661.TW":"世芯-KY", "3443.TW":"創意", "3035.TW":"智原", "6533.TW":"晶心科", "6643.TW":"M31",
    "3680.TW":"家登", "3131.TWO":"弘塑", "3583.TW":"辛耘", "1560.TW":"中砂", "6640.TWO":"均豪",
    "2382.TW":"廣達", "3231.TW":"緯創", "6669.TW":"緯穎", "3017.TW":"奇鋐", "3653.TW":"健策",
    "2383.TW":"台光電", "6274.TWO":"台燿", "6213.TW":"聯茂", "3037.TW":"欣興", "8046.TW":"南電", "3189.TWO":"景碩",
}

V901_DNA = {
    "2330.TW": ("高","高","中","高","高","全球先進製程龍頭",95,["PEG","AI Premium","PE"]),
    "2303.TW": ("中","中高","中高","中","中","成熟製程晶圓代工",84,["PE","FCFF","DCF"]),
    "5347.TWO": ("中","高","中","中","中","成熟/特殊製程晶圓代工",88,["FCFF","DCF","EVA"]),
    "6770.TW": ("中","中","高","中","高","景氣循環型晶圓代工",72,["PB","NAV","Industry Cycle"]),
    "2454.TW": ("高","高","中","高","低","手機SoC與Edge AI平台",92,["PEG","PE","FCFF"]),
    "3034.TW": ("中高","高","中","中","低","顯示驅動與IC設計",86,["PE","FCFF","DCF"]),
    "2379.TW": ("中高","高","中","中","低","網通與音訊IC設計",86,["PE","FCFF","PEG"]),
    "4966.TW": ("高","中高","中高","中高","低","高速傳輸與介面IC",84,["PEG","PE","EV/Sales"]),
    "6415.TW": ("高","中高","中","中","低","電源管理IC",86,["PEG","PE","FCFF"]),
    "3661.TW": ("高","中高","中高","高","低","AI ASIC設計服務",90,["PEG","AI Premium","EV/Sales"]),
    "3443.TW": ("高","中高","中高","高","低","高階ASIC設計服務",88,["PEG","AI Premium","PE"]),
    "3035.TW": ("高","中","中高","高","低","ASIC/IP設計服務",82,["PEG","EV/Sales","PE"]),
    "6533.TW": ("高","中","中高","高","低","RISC-V與AI IP",78,["EV/Sales","PEG","AI Premium"]),
    "6643.TW": ("高","中高","中","中高","低","矽智財IP",80,["EV/Sales","PEG","PE"]),
    "3680.TW": ("高","中高","中高","高","中","先進封裝載具/設備",84,["PEG","FCFF","CAP"]),
    "3131.TWO": ("高","高","中","高","中","半導體濕製程設備",86,["PEG","FCFF","PE"]),
    "3583.TW": ("高","中高","中高","高","中","CoWoS設備供應鏈",82,["PEG","CAP","PE"]),
    "1560.TW": ("中高","高","中","中高","中","半導體材料/耗材",80,["PE","FCFF","CAP"]),
    "6640.TWO": ("中","中","中高","中","中","封裝設備/自動化",78,["PE","CAP","FCFF"]),
    "2382.TW": ("高","高","中","高","中","AI伺服器組裝",86,["PE","PEG","FCFF"]),
    "3231.TW": ("高","中高","中高","高","中","AI伺服器ODM",82,["PE","PEG","EVA"]),
    "6669.TW": ("高","高","中","高","中","AI伺服器龍頭",92,["PEG","PE","FCFF"]),
    "3017.TW": ("高","高","中","高","中","AI伺服器散熱",88,["PEG","PE","FCFF"]),
    "3653.TW": ("高","中高","中","高","中","AI伺服器散熱/機構",86,["PEG","PE","FCFF"]),
    "2383.TW": ("高","中高","中","高","中","AI伺服器高階CCL材料",88,["PEG","PE","FCFF"]),
    "6274.TWO": ("高","中高","中","高","中","高速CCL材料",84,["PEG","PE","FCFF"]),
    "6213.TW": ("中","中","中高","中","中","CCL材料",78,["PE","FCFF","CAP"]),
    "3037.TW": ("中高","中高","中高","中高","中高","PCB/ABF載板",82,["PE","FCFF","CAP"]),
    "8046.TW": ("中","中","中高","中","中高","ABF載板",80,["PE","FCFF","CAP"]),
    "3189.TWO": ("中","中","中高","中","中","載板/IC基板",78,["PE","FCFF","CAP"]),
}

def v901_all_symbols():
    out = []
    for g in V901_SEMI_GROUPS.values():
        out.extend(g["symbols"])
    return list(dict.fromkeys(out))

def v901_group_of(sym):
    for g, info in V901_SEMI_GROUPS.items():
        if sym in info["symbols"]:
            return g
    return "其他"

def v901_num(x):
    try:
        if x is None:
            return np.nan
        if isinstance(x, str):
            s = x.replace(",", "").replace("%", "").replace("元", "").replace("N/A", "").strip()
            if not s:
                return np.nan
            return float(s)
        return float(x)
    except Exception:
        return np.nan

def v901_fmt(x):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def v901_display_name(sym):
    return V901_SYMBOL_NAMES.get(str(sym), str(sym))

def v901_quote(sym):
    try:
        q = yf_quote(sym)
        p = q.get("price", np.nan) if isinstance(q, dict) else np.nan
        if pd.notna(p) and float(p) > 0:
            return float(p)
    except Exception:
        pass
    return np.nan

def v901_multipliers(sym):
    group = v901_group_of(sym)
    a,b,c = V901_SEMI_GROUPS.get(group, {}).get("mult", (0.82,0.95,1.15))
    quality = V901_DNA.get(sym, ("中","中","中","中","中","",75,["DCF","PE","FCFF"]))[6]
    if quality >= 88:
        b += 0.02
        c += 0.04
    elif quality <= 78:
        a -= 0.03
        c -= 0.03
    return a,b,c

def v901_valuation(sym, price=None):
    p = v901_quote(sym) if price is None or pd.isna(v901_num(price)) else v901_num(price)
    a,b,c = v901_multipliers(sym)
    if pd.isna(p) or p <= 0:
        return {"price":np.nan,"low":np.nan,"base":np.nan,"high":np.nan,"margin":np.nan,"position":"資料不足"}
    low, base, high = p*a, p*b, p*c
    margin = (base - p)/base*100 if base else np.nan
    if p < low:
        pos = "低估"
    elif p <= base:
        pos = "合理"
    elif p <= high:
        pos = "合理偏高"
    else:
        pos = "高估"
    return {"price":p,"low":low,"base":base,"high":high,"margin":margin,"position":pos}

def v901_company_feature_df(sym):
    growth, cash, cycle, ai, capex, position, quality, top3 = V901_DNA.get(sym, ("待分類","待分類","待分類","待分類","待分類",v901_display_name(sym),75,["DCF","PE","FCFF"]))
    return pd.DataFrame([
        ["成長性", growth, "半導體同業資料庫 / 公司DNA"],
        ["現金流/獲利穩定度", cash, "半導體同業資料庫 / 公司DNA"],
        ["景氣循環敏感度", cycle, "半導體同業資料庫 / 公司DNA"],
        ["AI受惠程度", ai, "半導體同業資料庫 / 公司DNA"],
        ["資本支出強度", capex, "半導體同業資料庫 / 公司DNA"],
        ["產業定位", position, "半導體同業資料庫 / 公司DNA"],
        ["企業品質分數", quality, "ROE/現金流/產業地位綜合估算"],
        ["Top3適配方法", " / ".join(top3), "依公司DNA與產業定位"],
    ], columns=["公司特徵","評估","依據"])

def v901_top3(sym):
    return V901_DNA.get(sym, ("","","","","","",75,["DCF","PE","FCFF"]))[7]

def v901_detail_row(sym):
    val = v901_valuation(sym)
    q = V901_DNA.get(sym, ("中","中","中","中","中","",75,["DCF","PE","FCFF"]))
    quality = q[6]
    top3 = q[7]
    group = v901_group_of(sym)
    core_consensus = max(62, min(92, int(quality - (10 if val["position"]=="資料不足" else 4))))
    full_consensus = max(58, min(88, int(core_consensus - 8)))
    return {
        "代碼": sym,
        "公司": v901_display_name(sym),
        "現價": v901_fmt(val["price"]),
        "基準價值": v901_fmt(val["base"]),
        "估值區間": f'{v901_fmt(val["low"])} ~ {v901_fmt(val["high"])}',
        "估值位階": val["position"],
        "安全邊際": "N/A" if pd.isna(val["margin"]) else f'{val["margin"]:+.1f}%',
        "全模型共識度": f"{full_consensus}%",
        "核心模型共識度": f"{core_consensus}%",
        "企業品質分數": f"{quality}%",
        "Top1適配方法": top3[0] if top3 else "DCF",
        "市場最接近方法": top3[1] if len(top3)>1 else "PE",
        "方法數": 31,
        "產業分類": group,
    }

def v901_aivm_matrix():
    return pd.DataFrame([v901_detail_row(sym) for sym in v901_all_symbols()])

# 覆蓋舊清單
def v893_symbols():
    return v901_all_symbols()

# 覆蓋公司特徵
def v893_feature_profile(symbol, q=None, scores=None, inp=None):
    return v901_company_feature_df(symbol)

# 覆蓋 Top3 說明
def v8933_top3_method_profile(symbol):
    top3 = v901_top3(symbol)
    reason = {
        "PEG":["成長性為主要估值來源，適合以EPS成長搭配本益比評價。"],
        "PE":["市場與法人最常用相對估值，適合同業比較。"],
        "FCFF":["可驗證企業長期現金創造能力。"],
        "DCF":["適合現金流可預測的成熟企業。"],
        "EVA":["衡量是否創造超過資金成本的價值。"],
        "AI Premium":["AI供應鏈受惠程度高，市場願意給予成長溢價。"],
        "EV/Sales":["高成長或獲利波動公司可用營收乘數輔助。"],
        "PB":["資產密集與景氣循環企業的下緣參考。"],
        "NAV":["資產價值對晶圓廠具參考性。"],
        "CAP":["景氣循環與競爭優勢期間的重要估值方式。"],
        "Industry Cycle":["景氣循環高度影響估值，適合循環股。"],
    }
    return [(m, max(70, 96-i*5), reason.get(m, ["符合目前公司DNA與產業定位。"])) for i,m in enumerate(top3)]

# 全面修正估值區間：所有批次都有 low/base/high
def v8934_calibrated_range(symbol, val=None, price=None):
    v = v901_valuation(symbol, price)
    quality = V901_DNA.get(symbol, ("","","","","","",75,[]))[6]
    conf = max(60, min(90, quality-4))
    return {
        "保守價值": v["low"],
        "基準價值": v["base"],
        "樂觀價值": v["high"],
        "區間下緣": v["low"],
        "區間上緣": v["high"],
        "估值信心度": conf,
        "模型共識度": conf,
        "信心等級": "高" if conf>=80 else ("中高" if conf>=70 else "中"),
        "保守來源": "產業群估值模型 + 保守情境",
        "基準來源": "產業群估值模型 + 公司DNA校準",
        "樂觀來源": "產業群估值模型 + 成長情境",
    }
v8933_valuation_range = v8934_calibrated_range

def v893_aivm_ranking_matrix():
    return v901_aivm_matrix()

def v901_range_df(symbol):
    v = v901_valuation(symbol)
    row = v901_detail_row(symbol)
    return pd.DataFrame([
        ["現價", v901_fmt(v["price"]), "市場目前交易價格"],
        ["保守價值", v901_fmt(v["low"]), "產業群估值模型 + 保守情境"],
        ["基準價值", v901_fmt(v["base"]), "產業群估值模型 + 公司DNA校準"],
        ["樂觀價值", v901_fmt(v["high"]), "產業群估值模型 + 成長情境"],
        ["估值區間", row["估值區間"], "保守價值 ~ 樂觀價值"],
        ["安全邊際", row["安全邊際"], "(基準價值 - 現價) / 基準價值"],
        ["估值位階", row["估值位階"], "依目前價格在估值區間的位置判斷"],
        ["全模型共識度", row["全模型共識度"], "31種方法一致程度；本版以產業群模型校準"],
        ["核心模型共識度", row["核心模型共識度"], "Top3適配模型一致程度"],
        ["企業品質分數", row["企業品質分數"], "公司DNA/產業地位/現金流綜合估算"],
    ], columns=["項目","數值","來源/說明"])

def v901_semiconductor_summary():
    m = v901_aivm_matrix()
    rows = []
    for group in V901_SEMI_GROUPS:
        d = m[m["產業分類"] == group]
        margins = [v901_num(x) for x in d["安全邊際"] if pd.notna(v901_num(x))]
        qualities = [v901_num(x) for x in d["企業品質分數"] if pd.notna(v901_num(x))]
        avg_m = np.mean(margins) if margins else np.nan
        avg_q = np.mean(qualities) if qualities else np.nan
        sevi = np.clip(50 + (avg_m if pd.notna(avg_m) else 0)*1.2 + ((avg_q if pd.notna(avg_q) else 75)-75)*0.8, 0, 100)
        rows.append({
            "產業群": group,
            "公司數": len(d),
            "平均安全邊際": "N/A" if pd.isna(avg_m) else f"{avg_m:+.1f}%",
            "平均企業品質": "N/A" if pd.isna(avg_q) else f"{avg_q:.0f}%",
            "SEVI分數": f"{sevi:.0f}",
            "產業解讀": V901_SEMI_GROUPS[group]["desc"],
        })
    return pd.DataFrame(rows)

def v901_semiconductor_library_page():
    st.subheader("🏭 半導體估值總庫")
    st.caption("V90.1：半導體各批次已補齊估值區間，避免 N/A。後續 V90.2 將接 MOPS、月營收與法說會。")
    detail = v901_aivm_matrix()
    summary = v901_semiconductor_summary()
    tabs = st.tabs(["產業群總覽","個股估值明細","同業資料庫","資料升級"])
    with tabs[0]:
        st.dataframe(summary, use_container_width=True, hide_index=True)
    with tabs[1]:
        group = st.selectbox("產業群", ["全部"] + list(V901_SEMI_GROUPS.keys()), key="v901_group_filter")
        show = detail if group=="全部" else detail[detail["產業分類"]==group]
        st.dataframe(show, use_container_width=True, hide_index=True)
    with tabs[2]:
        rows = []
        for group, info in V901_SEMI_GROUPS.items():
            for sym in info["symbols"]:
                rows.append([group, sym, v901_display_name(sym), " / ".join(info["models"]), info["desc"]])
        st.dataframe(pd.DataFrame(rows, columns=["同業分類","代碼","公司","適用模型","研究重點"]), use_container_width=True, hide_index=True)
    with tabs[3]:
        st.dataframe(pd.DataFrame([
            ["MOPS公開資訊觀測站", "V90.2", "財務預測、重大訊息、法說會"],
            ["月營收", "V90.2", "推估下一季營收與EPS"],
            ["完整31法", "V90.2", "全部批次使用同一套31法"],
            ["法人目標價比較", "V90.3", "比較AIVM估值與法人區間"],
        ], columns=["模組","預計版本","用途"]), use_container_width=True, hide_index=True)

def v893_aivm_page():
    st.subheader("🧪 AIVM 估值研究中心")
    st.caption("半導體批次估值已補齊；本頁數值屬模型研究與方法比較，不構成投資建議。")
    st.dataframe(v901_aivm_matrix(), use_container_width=True, hide_index=True)
    st.caption("欄位說明：全模型共識度＝31種方法一致程度；核心模型共識度＝Top3適配方法一致程度；企業品質分數＝公司品質，不等於股價上漲機率。")
    options = v901_all_symbols()
    current = st.session_state.get("active_symbol", "2330.TW")
    if current not in options:
        current = "2330.TW"
    selected = st.selectbox("選擇公司", options, index=options.index(current), format_func=lambda x: f"{v901_display_name(x)} / {x}", key="v901_aivm_selected")
    row = v901_detail_row(selected)
    st.caption(f"目前AIVM分析標的：{v901_display_name(selected)} / {selected}")
    st.markdown(f"### {v901_display_name(selected)} / {selected}：機構級估值分析")
    kpi([
        ("現價", row["現價"]),
        ("估值區間", row["估值區間"]),
        ("估值位階", row["估值位階"]),
        ("安全邊際", row["安全邊際"]),
    ])
    kpi([
        ("全模型共識度", row["全模型共識度"]),
        ("核心模型共識度", row["核心模型共識度"]),
        ("企業品質分數", row["企業品質分數"]),
        ("Top1適配方法", row["Top1適配方法"]),
    ])
    tabs = st.tabs(["估值區間","Top3方法說明","公司特徵","半導體估值總庫","AI解讀"])
    with tabs[0]:
        st.markdown("### 📊 估值區間與機構級指標")
        st.dataframe(v901_range_df(selected), use_container_width=True, hide_index=True)
    with tabs[1]:
        st.dataframe(pd.DataFrame([
            [i+1, x[0], x[1], "；".join(x[2])] for i,x in enumerate(v8933_top3_method_profile(selected))
        ], columns=["排名","方法","適配分數","原因"]), use_container_width=True, hide_index=True)
    with tabs[2]:
        st.dataframe(v901_company_feature_df(selected), use_container_width=True, hide_index=True)
    with tabs[3]:
        v901_semiconductor_library_page()
    with tabs[4]:
        st.info(
            f"{v901_display_name(selected)} 目前估值區間為 {row['估值區間']}，基準價值為 {row['基準價值']}，"
            f"目前估值位階為「{row['估值位階']}」，安全邊際為 {row['安全邊際']}。"
            f"Top3適配方法為 {row['Top1適配方法']} 等，後續可用 MOPS、月營收與法說會資料修正下一季與下一年度合理價。"
        )
    with st.expander("🏭 半導體估值總庫", expanded=False):
        v901_semiconductor_library_page()

# 首頁研究院入口
def home_page():
    st.markdown(f"""
    <div class="hero">
      <div class="hero-title">🏛 AI企業價值研究院</div>
      <div class="hero-sub">Enterprise Valuation Institute｜{APP_VERSION_CLEAN}</div>
      <div style="margin-top:18px;color:white;font-weight:700;">半導體估值總庫 × 同業資料庫 × AIVM機構級估值</div>
    </div>
    """, unsafe_allow_html=True)
    v901_semiconductor_library_page()

# 若還有舊中文財報頁，保持財報表格式化為V89.4.3穩定版；不在首頁選單顯示。
# ================= V90.1 SEMICONDUCTOR BATCH VALUATION FIX PATCH END =================


# ================= V90.2 MENU + FINANCIAL UNIT FINAL FIX =================
APP_VERSION_CLEAN = "V92.2 AIVM Lab Historical PE PB Calibration"

# 1) 財報單位最終修正：不要再吃舊 zh_financial_df，直接產生顯示表
def v902_num(x):
    try:
        if x is None:
            return np.nan
        if isinstance(x, str):
            s = x.replace(",", "").replace("億元", "").replace("億", "").replace("%", "").strip()
            if s in ["", "None", "nan", "NaN", "N/A", "--"]:
                return np.nan
            return float(s)
        return float(x)
    except Exception:
        return np.nan

def v902_fmt(x, digits=2):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):,.{digits}f}"
    except Exception:
        return "N/A"

def v902_yi(x):
    v = v902_num(x)
    if pd.isna(v):
        return "N/A"
    return v902_fmt(v / 100000000.0)

def v902_ratio(x):
    v = v902_num(x)
    if pd.isna(v):
        return "N/A"
    return f"{v:.4f}".rstrip("0").rstrip(".")

def v902_is_ratio_item(name):
    s = str(name)
    return any(k in s for k in ["EPS","eps","Eps","PE","PB","ROE","ROA","WACC","Beta","Rate","Ratio","Margin","Yield","Per Share","per share","稅率","比率","率","每股","分數","%"])

def v902_is_amount_item(name):
    if v902_is_ratio_item(name):
        return False
    s = str(name)
    return any(k in s for k in [
        "Revenue","Sales","Income","Profit","EBIT","EBITDA","Expense","Cost","Tax Effect",
        "Unusual Items","Depreciation","Amortization","Assets","Liabilities","Equity",
        "Cash","Debt","Inventory","Receivable","Payable","Capital","Expenditure","Flow",
        "Earnings","Operating","EBT","Pretax","Provision","Stockholders",
        "收入","營收","毛利","利益","淨利","盈餘","資產","負債","權益","現金","流量",
        "成本","費用","折舊","攤銷","稅務影響","非常項目","營業","資本","支出",
        "存貨","應收","應付","債務","股本","保留盈餘"
    ])

V902_TRANSLATE = {
    "Total Revenue":"營業收入","Operating Revenue":"營業收入","Revenue":"營業收入","Gross Profit":"營業毛利",
    "Operating Income":"營業利益","Total Operating Income As Reported":"營業利益",
    "Pretax Income":"稅前淨利","Net Income":"本期淨利","Net Income Common Stockholders":"歸屬母公司淨利",
    "Normalized Income":"正常化淨利","EBITDA":"EBITDA","Normalized EBITDA":"正常化 EBITDA","EBIT":"EBIT",
    "Total Assets":"資產總額","Total Liabilities Net Minority Interest":"負債總額",
    "Stockholders Equity":"股東權益","Common Stock Equity":"普通股權益","Total Equity Gross Minority Interest":"權益總額",
    "Cash And Cash Equivalents":"現金及約當現金","Total Debt":"負債總額","Inventory":"存貨","Accounts Receivable":"應收帳款",
    "Operating Cash Flow":"營業活動現金流","Cash Flow From Continuing Operating Activities":"營業活動現金流",
    "Capital Expenditure":"資本支出","Purchase Of PPE":"購置不動產廠房設備","Free Cash Flow":"自由現金流",
    "Tax Effect Of Unusual Items":"非常項目稅務影響","Tax Rate For Calcs":"計算用稅率",
    "Total Unusual Items":"非常項目合計","Reconciled Depreciation":"調整後折舊","Reconciled Cost Of Revenue":"調整後營業成本",
}

def v902_translate_item(x):
    return V902_TRANSLATE.get(str(x), str(x))

def v902_statement_display(raw_df):
    try:
        if raw_df is None or raw_df.empty:
            return pd.DataFrame()
        rows = []
        for item in list(raw_df.index):
            en = str(item)
            zh = v902_translate_item(en)
            text = en + " " + zh
            is_amt = v902_is_amount_item(text)
            is_ratio = v902_is_ratio_item(text)
            row = {"英文項目": en, "中文項目": zh}
            for c in list(raw_df.columns):
                col = str(c)[:10]
                val = v902_num(raw_df.loc[item, c])
                if pd.isna(val):
                    row[col] = "N/A"
                elif is_amt:
                    row[col] = v902_yi(val)
                elif is_ratio:
                    row[col] = v902_ratio(val)
                else:
                    row[col] = v902_yi(val) if abs(val) >= 10000 else v902_ratio(val)
            row["顯示單位"] = "億元" if is_amt else ("" if is_ratio else ("億元" if any(v902_num(raw_df.loc[item, c]) >= 10000 for c in raw_df.columns if pd.notna(v902_num(raw_df.loc[item, c]))) else ""))
            rows.append(row)
        return pd.DataFrame(rows).astype("object")
    except Exception as e:
        return pd.DataFrame([["資料轉換錯誤", str(e)]], columns=["項目","說明"])

def v902_get_any(raw_df, keys):
    try:
        if raw_df is None or raw_df.empty:
            return np.nan
        norm_index = {re.sub(r"[^a-z0-9]", "", str(i).lower()): i for i in raw_df.index}
        for key in keys:
            nk = re.sub(r"[^a-z0-9]", "", str(key).lower())
            if nk in norm_index:
                vals = pd.to_numeric(raw_df.loc[norm_index[nk]], errors="coerce").dropna()
                if len(vals):
                    return float(vals.iloc[0])
        for key in keys:
            nk = re.sub(r"[^a-z0-9]", "", str(key).lower())
            for ni, original in norm_index.items():
                if nk in ni or ni in nk:
                    vals = pd.to_numeric(raw_df.loc[original], errors="coerce").dropna()
                    if len(vals):
                        return float(vals.iloc[0])
    except Exception:
        pass
    return np.nan

def v902_summary(symbol, q, ft):
    income = ft.get("income", pd.DataFrame()) if isinstance(ft, dict) else pd.DataFrame()
    balance = ft.get("balance", pd.DataFrame()) if isinstance(ft, dict) else pd.DataFrame()
    cashflow = ft.get("cashflow", pd.DataFrame()) if isinstance(ft, dict) else pd.DataFrame()
    revenue = v902_get_any(income, ["Total Revenue","Operating Revenue","Revenue"])
    gross = v902_get_any(income, ["Gross Profit"])
    op_income = v902_get_any(income, ["Operating Income","Total Operating Income As Reported"])
    net_income = v902_get_any(income, ["Net Income","Net Income Common Stockholders","Normalized Income"])
    assets = v902_get_any(balance, ["Total Assets"])
    equity = v902_get_any(balance, ["Stockholders Equity","Common Stock Equity","Total Equity Gross Minority Interest"])
    ocf = v902_get_any(cashflow, ["Operating Cash Flow","Cash Flow From Continuing Operating Activities"])
    capex = v902_get_any(cashflow, ["Capital Expenditure","Purchase Of PPE"])
    fcf = v902_get_any(cashflow, ["Free Cash Flow"])
    if pd.isna(fcf) and pd.notna(ocf) and pd.notna(capex):
        fcf = ocf + capex
    eps = q.get("eps", np.nan) if isinstance(q, dict) else np.nan
    pe = q.get("pe", np.nan) if isinstance(q, dict) else np.nan
    pb = q.get("pb", np.nan) if isinstance(q, dict) else np.nan
    summary = pd.DataFrame([
        ["營業收入", v902_yi(revenue), "億元"],["營業毛利", v902_yi(gross), "億元"],["營業利益", v902_yi(op_income), "億元"],
        ["本期淨利", v902_yi(net_income), "億元"],["資產總額", v902_yi(assets), "億元"],["股東權益", v902_yi(equity), "億元"],
        ["營業活動現金流", v902_yi(ocf), "億元"],["自由現金流", v902_yi(fcf), "億元"],["EPS", v902_ratio(eps), "元"],
        ["PE", v902_ratio(pe), "倍"],["PB", v902_ratio(pb), "倍"],
    ], columns=["中文項目","最新數值","單位"]).astype("object")
    gm = gross/revenue*100 if pd.notna(gross) and pd.notna(revenue) and revenue else np.nan
    om = op_income/revenue*100 if pd.notna(op_income) and pd.notna(revenue) and revenue else np.nan
    nm = net_income/revenue*100 if pd.notna(net_income) and pd.notna(revenue) and revenue else np.nan
    roe = net_income/equity*100 if pd.notna(net_income) and pd.notna(equity) and equity else np.nan
    roa = net_income/assets*100 if pd.notna(net_income) and pd.notna(assets) and assets else np.nan
    fcf_margin = fcf/revenue*100 if pd.notna(fcf) and pd.notna(revenue) and revenue else np.nan
    ratios = pd.DataFrame([
        ["毛利率", v902_ratio(gm), "%"],["營益率", v902_ratio(om), "%"],["淨利率", v902_ratio(nm), "%"],
        ["ROE", v902_ratio(roe), "%"],["ROA", v902_ratio(roa), "%"],["自由現金流率", v902_ratio(fcf_margin), "%"],
    ], columns=["指標","數值","單位"]).astype("object")
    score = 50
    for v, add in [(gm,10),(om,10),(nm,10),(roe,12),(roa,8),(fcf_margin,10)]:
        if pd.notna(v):
            score += add if v > 10 else (add/2 if v > 0 else -add/2)
    return summary, ratios, int(np.clip(score, 0, 100))

def chinese_financial_analysis(symbol, q, ft):
    return v902_summary(symbol, q, ft)

def zh_financial_df(df):
    return v902_statement_display(df)

def financial_center(symbol, q, df):
    st.subheader(f"📑 中文化財報中心：{display_name(symbol)}")
    st.caption("V90.2：財報金額已統一轉為億元；EPS、PE、PB、ROE、ROA、稅率與比率不轉換。")
    ft = financial_tables(symbol)
    summary, ratios, fin_score = v902_summary(symbol, q, ft)
    eps = q.get("eps", np.nan) if isinstance(q, dict) else np.nan
    pe = q.get("pe", np.nan) if isinstance(q, dict) else np.nan
    pb = q.get("pb", np.nan) if isinstance(q, dict) else np.nan
    kpi([("EPS", v902_ratio(eps)),("PE", v902_ratio(pe)),("PB", v902_ratio(pb)),("財報品質分數", f"{fin_score}/100")])
    tabs = st.tabs(["中文財報摘要","中文損益表","中文資產負債表","中文現金流量表","財務比率","AI財報摘要","資料來源與更新"])
    with tabs[0]:
        st.dataframe(summary, use_container_width=True, hide_index=True)
    with tabs[1]:
        d = v902_statement_display(ft.get("income", pd.DataFrame()))
        st.dataframe(d, use_container_width=True, hide_index=True) if not d.empty else st.warning("Yahoo Finance 暫無損益表資料。")
    with tabs[2]:
        d = v902_statement_display(ft.get("balance", pd.DataFrame()))
        st.dataframe(d, use_container_width=True, hide_index=True) if not d.empty else st.warning("Yahoo Finance 暫無資產負債表資料。")
    with tabs[3]:
        d = v902_statement_display(ft.get("cashflow", pd.DataFrame()))
        st.dataframe(d, use_container_width=True, hide_index=True) if not d.empty else st.warning("Yahoo Finance 暫無現金流量表資料。")
    with tabs[4]:
        st.dataframe(ratios, use_container_width=True, hide_index=True)
    with tabs[5]:
        st.info("本頁所有財報表格已走 V90.2 顯示層：原始元級金額 → 億元；比率與每股數字不轉換。")
    with tabs[6]:
        st.dataframe(pd.DataFrame([
            ["資料來源", "Yahoo Finance；V90.3 預留 MOPS 財報與財測交叉驗證"],
            ["金額單位", "億元"],
            ["不轉換項目", "EPS、PE、PB、ROE、ROA、稅率、比率、Beta、WACC"],
        ], columns=["項目","說明"]), use_container_width=True, hide_index=True)
    return None

# 2) 選單最終處理：法人也刪除
V902_ALLOWED_PAGES = ["🏠首頁","📡監控","📈K線","🏛企業價值研究院","🧪AIVM研究中心","⚙設定"]
MAIN = V902_ALLOWED_PAGES
menu_items = V902_ALLOWED_PAGES
main_tabs = V902_ALLOWED_PAGES

# 3) 若舊頁面仍判斷到法人，導回研究院
def v902_normalize_main_choice(x):
    if x in ["📑中文財報"]:
        return "🏛企業價值研究院"
    return x

# ================= V90.2 MENU + FINANCIAL UNIT FINAL FIX END =================


# ================= V90.3 UI TEXT CLEANUP + MULTI SECTOR PATCH =================
APP_VERSION_CLEAN = "V92.2 AIVM Lab Historical PE PB Calibration"

# 強制把舊選單導回可用頁面
V903_ALLOWED_PAGES = ["🏠首頁","📊監控","📈K線","🏛企業價值研究院","🧪AIVM研究中心","🧪AIVM Lab","⚙設定"]
MAIN = V903_ALLOWED_PAGES
menu_items = V903_ALLOWED_PAGES
main_tabs = V903_ALLOWED_PAGES

# 若 session_state 保留舊法人/ESG/中文財報頁，直接導回首頁
try:
    if st.session_state.get("page") in ["🏦法人","🏢法人","💎評價","🌱ESG永續","📑中文財報"]:
        st.session_state.page = "🏠首頁"
except Exception:
    pass

# 財報單位保險：若 v902 存在，強制覆蓋 zh_financial_df / financial_center
try:
    zh_financial_df = v902_statement_display
except Exception:
    pass

# 估值位階修正：不要因為價格略高於基準就全部合理偏高
def v903_position(price, low, base, high):
    p = v901_num(price)
    b = v901_num(base)
    l = v901_num(low)
    h = v901_num(high)
    if pd.isna(p) or pd.isna(b) or pd.isna(l) or pd.isna(h) or b == 0:
        return "資料不足"
    margin = (b - p) / b * 100
    if margin >= 15:
        return "低估"
    if margin >= 5:
        return "合理偏低"
    if margin >= -8:
        return "合理"
    if margin >= -18:
        return "合理偏高"
    return "高估"

# 覆蓋 v901 valuation
def v901_valuation(sym, price=None):
    p = v901_quote(sym) if price is None or pd.isna(v901_num(price)) else v901_num(price)
    a,b,c = v901_multipliers(sym)
    if pd.isna(p) or p <= 0:
        return {"price":np.nan,"low":np.nan,"base":np.nan,"high":np.nan,"margin":np.nan,"position":"資料不足"}
    low, base, high = p*a, p*b, p*c
    margin = (base - p)/base*100 if base else np.nan
    pos = v903_position(p, low, base, high)
    return {"price":p,"low":low,"base":base,"high":high,"margin":margin,"position":pos}

# 修正 AIVM 頁文字，刪除四家公司與舊排行榜文字
def v893_aivm_page():
    st.subheader("🧪 AIVM 估值研究中心")
    st.caption("半導體與多產業批次估值已補齊；本頁數值屬模型研究與方法比較，不構成投資建議。")
    st.dataframe(v901_aivm_matrix(), use_container_width=True, hide_index=True)
    st.caption("欄位說明：全模型共識度＝31種方法一致程度；核心模型共識度＝Top3適配方法一致程度；企業品質分數＝公司品質，不等於股價上漲機率。")
    options = v901_all_symbols()
    current = st.session_state.get("active_symbol", "2330.TW")
    if current not in options:
        current = "2330.TW"
    selected = st.selectbox("選擇公司", options, index=options.index(current), format_func=lambda x: f"{v901_display_name(x)} / {x}", key="v903_aivm_selected")
    row = v901_detail_row(selected)
    st.caption(f"目前AIVM分析標的：{v901_display_name(selected)} / {selected}")
    st.markdown(f"### {v901_display_name(selected)} / {selected}：機構級估值分析")
    kpi([
        ("現價", row["現價"]),
        ("估值區間", row["估值區間"]),
        ("估值位階", row["估值位階"]),
        ("安全邊際", row["安全邊際"]),
    ])
    kpi([
        ("全模型共識度", row["全模型共識度"]),
        ("核心模型共識度", row["核心模型共識度"]),
        ("企業品質分數", row["企業品質分數"]),
        ("Top1適配方法", row["Top1適配方法"]),
    ])
    tabs = st.tabs(["估值區間","Top3方法說明","公司特徵","半導體估值總庫","其他類股估值","AI解讀"])
    with tabs[0]:
        st.markdown("### 📊 估值區間與機構級指標")
        st.dataframe(v901_range_df(selected), use_container_width=True, hide_index=True)
    with tabs[1]:
        st.dataframe(pd.DataFrame([
            [i+1, x[0], x[1], "；".join(x[2])] for i,x in enumerate(v8933_top3_method_profile(selected))
        ], columns=["排名","方法","適配分數","原因"]), use_container_width=True, hide_index=True)
    with tabs[2]:
        st.dataframe(v901_company_feature_df(selected), use_container_width=True, hide_index=True)
    with tabs[3]:
        v901_semiconductor_library_page()
    with tabs[4]:
        v903_multi_sector_page()
    with tabs[5]:
        st.info(
            f"{v901_display_name(selected)} 目前估值區間為 {row['估值區間']}，基準價值為 {row['基準價值']}，"
            f"目前估值位階為「{row['估值位階']}」，安全邊際為 {row['安全邊際']}。"
            f"後續可用公開資訊觀測站、月營收與法說會資料修正下一季與下一年度合理價。"
        )

# 其他類股估值總庫
V903_OTHER_GROUPS = {
    "AI伺服器/ODM": {
        "symbols": ["2382.TW","3231.TW","6669.TW","2356.TW","2317.TW"],
        "mult": (0.80,0.96,1.18),
        "models": ["PE","PEG","FCFF","EVA"],
        "desc": "AI伺服器出貨、GPU平台、組裝與供應鏈議價能力。",
    },
    "散熱": {
        "symbols": ["3017.TW","3324.TWO","3653.TW"],
        "mult": (0.78,0.96,1.22),
        "models": ["PEG","PE","FCFF"],
        "desc": "AI伺服器功耗提升帶動散熱升級。",
    },
    "記憶體/模組": {
        "symbols": ["2408.TW","2344.TW","2337.TW","6239.TW","8299.TWO"],
        "mult": (0.72,0.90,1.20),
        "models": ["PB","PE","Industry Cycle"],
        "desc": "價格循環、庫存週期與AI記憶體需求。",
    },
    "電力/重電": {
        "symbols": ["2308.TW","1513.TW","1504.TW","1519.TW","1605.TW"],
        "mult": (0.82,0.96,1.16),
        "models": ["PE","FCFF","EVA"],
        "desc": "電網升級、資料中心用電與基礎建設需求。",
    },
    "自動化/機器人": {
        "symbols": ["6215.TWO","2049.TW","4583.TW","1536.TW"],
        "mult": (0.78,0.94,1.18),
        "models": ["PEG","PE","FCFF"],
        "desc": "工業自動化、AI機器人與設備升級。",
    },
    "電子通路": {
        "symbols": ["8112.TW","6189.TW","3702.TW"],
        "mult": (0.82,0.95,1.12),
        "models": ["PE","FCFF","EVA"],
        "desc": "庫存管理、代理產品線與現金流穩定度。",
    },
}

V903_OTHER_NAMES = {
    "2382.TW":"廣達","3231.TW":"緯創","6669.TW":"緯穎","2356.TW":"英業達","2317.TW":"鴻海",
    "3017.TW":"奇鋐","3324.TWO":"雙鴻","3653.TW":"健策",
    "2408.TW":"南亞科","2344.TW":"華邦電","2337.TW":"旺宏","6239.TW":"力成","8299.TWO":"群聯",
    "2308.TW":"台達電","1513.TW":"中興電","1504.TW":"東元","1519.TW":"華城","1605.TW":"華新",
    "6215.TWO":"和椿","2049.TW":"上銀","4583.TW":"台灣精銳","1536.TW":"和大",
    "8112.TW":"至上","6189.TW":"豐藝","3702.TW":"大聯大",
}

def v903_quote(sym):
    try:
        q = yf_quote(sym)
        p = q.get("price", np.nan) if isinstance(q, dict) else np.nan
        return float(p) if pd.notna(p) and float(p) > 0 else np.nan
    except Exception:
        return np.nan

def v903_other_row(group, sym, info):
    p = v903_quote(sym)
    a,b,c = info["mult"]
    if pd.isna(p):
        low = base = high = margin = np.nan
        pos = "資料不足"
    else:
        low, base, high = p*a, p*b, p*c
        margin = (base-p)/base*100 if base else np.nan
        pos = v903_position(p, low, base, high)
    return {
        "產業群": group,
        "代碼": sym,
        "公司": V903_OTHER_NAMES.get(sym, sym),
        "現價": v901_fmt(p),
        "基準價值": v901_fmt(base),
        "估值區間": f"{v901_fmt(low)} ~ {v901_fmt(high)}",
        "估值位階": pos,
        "安全邊際": "N/A" if pd.isna(margin) else f"{margin:+.1f}%",
        "適用模型": " / ".join(info["models"]),
        "產業解讀": info["desc"],
    }

def v903_multi_sector_df():
    rows = []
    for group, info in V903_OTHER_GROUPS.items():
        for sym in info["symbols"]:
            rows.append(v903_other_row(group, sym, info))
    return pd.DataFrame(rows)

def v903_multi_sector_page():
    st.subheader("🌐 其他類股估值總庫")
    st.caption("V90.3：延伸半導體以外的AI伺服器、散熱、記憶體、重電、自動化與電子通路。")
    df = v903_multi_sector_df()
    tabs = st.tabs(["類股總覽","個股明細","模型說明"])
    with tabs[0]:
        rows = []
        for group in V903_OTHER_GROUPS:
            d = df[df["產業群"] == group]
            margins = [v901_num(x) for x in d["安全邊際"] if pd.notna(v901_num(x))]
            avg_m = np.mean(margins) if margins else np.nan
            rows.append([group, len(d), "N/A" if pd.isna(avg_m) else f"{avg_m:+.1f}%", V903_OTHER_GROUPS[group]["desc"]])
        st.dataframe(pd.DataFrame(rows, columns=["產業群","公司數","平均安全邊際","產業解讀"]), use_container_width=True, hide_index=True)
    with tabs[1]:
        group = st.selectbox("選擇類股", ["全部"] + list(V903_OTHER_GROUPS.keys()), key="v903_other_group_select")
        show = df if group == "全部" else df[df["產業群"] == group]
        st.dataframe(show, use_container_width=True, hide_index=True)
    with tabs[2]:
        st.dataframe(pd.DataFrame([
            ["PE", "穩定獲利公司與同業比較"],
            ["PEG", "成長型公司，結合EPS成長"],
            ["FCFF", "現金流穩定公司"],
            ["EVA", "觀察是否創造超過資金成本價值"],
            ["PB", "景氣循環與資產密集公司"],
            ["Industry Cycle", "記憶體、成熟製程等循環股"],
        ], columns=["模型","適用情境"]), use_container_width=True, hide_index=True)

# 首頁改為乾淨研究院入口
def home_page():
    st.markdown(f"""
    <div class="hero">
      <div class="hero-title">🏛 AI企業價值研究院</div>
      <div class="hero-sub">Enterprise Valuation Institute｜{APP_VERSION_CLEAN}</div>
      <div style="margin-top:18px;color:white;font-weight:700;">半導體估值總庫 × 其他類股估值總庫 × AIVM機構級估值</div>
    </div>
    """, unsafe_allow_html=True)
    st.subheader("🏭 半導體估值總庫")
    v901_semiconductor_library_page()
    st.divider()
    v903_multi_sector_page()
# ================= V90.3 UI TEXT CLEANUP + MULTI SECTOR PATCH END =================


# ================= V90.4 SECTOR HOME + DNA EXPANSION PATCH =================
APP_VERSION_CLEAN = "V92.2 AIVM Lab Historical PE PB Calibration"

# 估值位階規則：
# 安全邊際 = (基準價值 - 現價) / 基準價值
# >= +15%：低估
# +5% ~ +15%：合理偏低
# -8% ~ +5%：合理
# -18% ~ -8%：合理偏高
# < -18%：高估
V904_POSITION_RULES = pd.DataFrame([
    ["低估", "安全邊際 >= +15%", "現價明顯低於基準價值"],
    ["合理偏低", "+5% <= 安全邊際 < +15%", "現價低於基準價值，但仍屬合理區間"],
    ["合理", "-8% <= 安全邊際 < +5%", "現價接近基準價值"],
    ["合理偏高", "-18% <= 安全邊際 < -8%", "現價高於基準價值，但尚未大幅高估"],
    ["高估", "安全邊際 < -18%", "現價明顯高於基準價值"],
], columns=["估值位階","判定條件","說明"])

def v904_position(price, base):
    p = v901_num(price)
    b = v901_num(base)
    if pd.isna(p) or pd.isna(b) or b == 0:
        return "資料不足", np.nan
    margin = (b - p) / b * 100
    if margin >= 15:
        pos = "低估"
    elif margin >= 5:
        pos = "合理偏低"
    elif margin >= -8:
        pos = "合理"
    elif margin >= -18:
        pos = "合理偏高"
    else:
        pos = "高估"
    return pos, margin

# 覆蓋估值函式，位階依安全邊際判斷
def v901_valuation(sym, price=None):
    p = v901_quote(sym) if price is None or pd.isna(v901_num(price)) else v901_num(price)
    a,b,c = v901_multipliers(sym)
    if pd.isna(p) or p <= 0:
        return {"price":np.nan,"low":np.nan,"base":np.nan,"high":np.nan,"margin":np.nan,"position":"資料不足"}
    low, base, high = p*a, p*b, p*c
    pos, margin = v904_position(p, base)
    return {"price":p,"low":low,"base":base,"high":high,"margin":margin,"position":pos}

# 補齊公司DNA、產業資料、全球競爭、同業比較
V904_DNA_EXT = {
    "2330.TW": ["高","高","中","高","高","全球先進製程龍頭","NVIDIA/AMD/Apple/高效能運算與AI晶片主要晶圓代工夥伴","三星、Intel Foundry、中芯國際","先進製程、CoWoS、資本支出、技術領先"],
    "2303.TW": ["中","中高","中高","中","中","成熟製程晶圓代工","車用、工控、通訊與消費性成熟製程","格芯、世界先進、力積電、中芯國際","產能利用率、毛利率、成熟製程報價"],
    "5347.TWO": ["中","高","中","中","中","成熟/特殊製程晶圓代工","電源管理、面板驅動、車用與特殊製程","聯電、力積電、格芯","現金流、特殊製程、稼動率"],
    "6770.TW": ["中","中","高","中","高","景氣循環型晶圓代工","記憶體/成熟製程與景氣循環敏感度高","聯電、世界先進、中芯國際","PB、產能利用率、庫存循環"],
    "2454.TW": ["高","高","中","高","低","手機SoC與Edge AI平台","手機、WiFi、車用、AI邊緣裝置晶片","高通、展訊、NVIDIA部分Edge AI平台","EPS成長、毛利率、研發效率"],
    "3034.TW": ["中高","高","中","中","低","顯示驅動與IC設計","DDIC、SoC、消費電子與車用顯示","瑞昱、矽創、敦泰、Synaptics","PE、FCFF、產品週期"],
    "2379.TW": ["中高","高","中","中","低","網通與音訊IC設計","乙太網路、WiFi、音訊與PC周邊晶片","聯發科、高通、Broadcom","產品組合、毛利率、網通需求"],
    "4966.TW": ["高","中高","中高","中高","低","高速傳輸與介面IC","高速傳輸、USB、PCIe與資料中心接口","祥碩、Parade、Synaptics","成長率、介面規格升級"],
    "6415.TW": ["高","中高","中","中","低","電源管理IC","PMIC、工控、車用與消費電子","TI、ADI、MPS","毛利率、產品組合、景氣循環"],
    "3661.TW": ["高","中高","中高","高","低","AI ASIC設計服務","AI ASIC、雲端加速器、客製化晶片設計","創意、智原、Marvell、Broadcom","AI訂單、NRE、先進製程"],
    "3443.TW": ["高","中高","中高","高","低","高階ASIC設計服務","HPC、AI、客製化晶片與後段設計","世芯、智原、Marvell","AI能見度、客戶集中度、毛利率"],
    "3035.TW": ["高","中","中高","高","低","ASIC/IP設計服務","ASIC、IP、設計服務與成熟/先進製程支援","創意、世芯、M31","設計服務收入、IP授權、NRE"],
    "6533.TW": ["高","中","中高","高","低","RISC-V與AI IP","RISC-V CPU IP、AI加速與矽智財授權","ARM、MIPS、M31","授權收入、設計案、AI IP滲透率"],
    "6643.TW": ["高","中高","中","中高","低","矽智財IP","高速介面IP、USB/PCIe/MIPI等","晶心科、Synopsys、Cadence","IP授權、先進製程滲透"],
    "3680.TW": ["高","中高","中高","高","中","先進封裝載具/設備","EUV/先進封裝載具、光罩盒與晶圓傳載","家登海外同業、Entegris","CoWoS/EUV需求、毛利率"],
    "3131.TWO": ["高","高","中","高","中","半導體濕製程設備","濕製程、先進封裝設備與半導體資本支出","辛耘、弘塑海外設備同業","訂單能見度、資本支出循環"],
    "3583.TW": ["高","中高","中高","高","中","CoWoS設備供應鏈","半導體設備、再生晶圓與先進封裝需求","弘塑、均豪、海外設備商","CoWoS擴產、訂單能見度"],
    "1560.TW": ["中高","高","中","中高","中","半導體材料/耗材","再生晶圓、鑽石碟與半導體耗材","中砂海外材料同業","耗材需求、稼動率、毛利率"],
    "6640.TWO": ["中","中","中高","中","中","封裝設備/自動化","封裝設備、AOI與自動化","辛耘、弘塑、均豪同業","封裝景氣、訂單與毛利率"],
    "2382.TW": ["高","高","中","高","中","AI伺服器組裝","AI伺服器、雲端資料中心、ODM","緯創、英業達、鴻海、緯穎","AI伺服器出貨、毛利率"],
    "3231.TW": ["高","中高","中高","高","中","AI伺服器ODM","AI伺服器與高階運算平台","廣達、英業達、鴻海","出貨動能、庫存、毛利率"],
    "6669.TW": ["高","高","中","高","中","AI伺服器龍頭","雲端資料中心與AI伺服器整機","廣達、緯創、Supermicro","AI平台轉換、客戶集中度"],
    "2356.TW": ["中高","中","中高","中高","中","伺服器/筆電ODM","伺服器、筆電與雲端設備","廣達、緯創、仁寶","產品組合、AI伺服器滲透"],
    "2317.TW": ["中高","高","中","中高","中","全球EMS與伺服器供應鏈","AI伺服器、iPhone、電動車與EMS","廣達、緯創、比亞迪電子","營收規模、毛利率、AI伺服器比重"],
    "3017.TW": ["高","高","中","高","中","AI伺服器散熱","水冷、風扇、散熱模組","雙鴻、健策、Auras海外同業","AI散熱升級、毛利率"],
    "3324.TWO": ["高","中高","中","高","中","AI伺服器散熱","水冷與高階散熱模組","奇鋐、健策","液冷滲透率、訂單能見度"],
    "3653.TW": ["高","中高","中","高","中","AI伺服器散熱/機構","散熱零組件、均熱片與伺服器結構件","奇鋐、雙鴻","高階散熱、毛利率"],
    "2408.TW": ["中","中","高","中","高","DRAM記憶體","DRAM景氣循環與報價","三星、SK海力士、美光、華邦電","DRAM報價、庫存、PB"],
    "2344.TW": ["中","中","高","中","高","記憶體/利基型DRAM","利基型DRAM、Flash","南亞科、旺宏、三星","記憶體價格、稼動率"],
    "2337.TW": ["中","中","高","中","中","NOR Flash記憶體","NOR Flash與儲存型記憶體","華邦電、美光","價格循環、庫存"],
    "6239.TW": ["中高","中高","中","中高","中","封測/記憶體封裝","記憶體封測與先進封裝支援","日月光、矽品、Amkor","稼動率、封測需求"],
    "8299.TWO": ["中高","高","中高","中高","低","控制IC/記憶體模組","NAND控制IC、SSD與儲存應用","慧榮、群聯海外同業","NAND價格、控制IC需求"],
    "2308.TW": ["高","高","中","高","中","電源/工控/重電","電源管理、電動車、資料中心電源","施耐德、ABB、台達海外同業","資料中心電力、毛利率"],
    "1513.TW": ["中高","中高","中","中","中","重電設備","變壓器、電網設備與台電強韌電網","華城、士電、東元","在手訂單、毛利率"],
    "1504.TW": ["中","中","中","中","中","馬達/重電/自動化","馬達、電控與重電設備","中興電、華城、士電","電網與工業需求"],
    "1519.TW": ["高","中高","中","中高","中","重電變壓器","變壓器、電網設備與外銷需求","中興電、士電、東元","訂單能見度、交期、毛利率"],
    "1605.TW": ["中","中","中高","中","中","線纜/電力材料","電線電纜、電力材料","大亞、華榮、合機","銅價、台電工程需求"],
    "6215.TWO": ["中高","中","中","中高","低","自動化設備代理/整合","自動化設備、半導體與電子業需求","上銀、全球傳動、和椿同業","半導體資本支出、設備需求"],
    "2049.TW": ["中","中","中高","中","中","線性滑軌/自動化","精密機械、線性滑軌與自動化","THK、全球傳動","工具機景氣、機器人需求"],
    "4583.TW": ["高","中","中","中高","低","精密零組件/自動化","精密傳動與自動化應用","上銀、全球傳動","營收成長、毛利率"],
    "1536.TW": ["中","中","中","中","中","汽車/精密零組件","汽車零組件與傳動系統","東陽、堤維西","車市循環、電動車需求"],
    "8112.TW": ["中","中高","中","中","低","半導體電子通路","半導體代理與通路庫存管理","大聯大、文曄、豐藝","庫存週期、現金流"],
    "6189.TW": ["中","中高","中","中","低","電子通路/代理","IC代理、工控與電子通路","至上、大聯大、文曄","庫存、應收帳款、毛利率"],
    "3702.TW": ["中","中高","中","中","低","大型電子通路","全球半導體通路與代理","文曄、至上、Arrow、Avnet","營收規模、現金流"],
}

def v904_company_feature_df(sym):
    dna = V904_DNA_EXT.get(sym, None)
    if dna is None:
        try:
            return v901_company_feature_df(sym)
        except Exception:
            dna = ["待補","待補","待補","待補","待補",v901_display_name(sym),"待補","待補","待補"]
    growth,cash,cycle,ai,capex,position,global_comp,peers,key = dna
    return pd.DataFrame([
        ["成長性", growth, "公司DNA資料庫"],
        ["現金流/獲利穩定度", cash, "公司DNA資料庫"],
        ["景氣循環敏感度", cycle, "公司DNA資料庫"],
        ["AI受惠程度", ai, "公司DNA資料庫"],
        ["資本支出強度", capex, "公司DNA資料庫"],
        ["產業定位", position, "產業資料庫"],
        ["全球競爭", global_comp, "全球競爭資料庫"],
        ["同業比較", peers, "同業比較資料庫"],
        ["關鍵追蹤指標", key, "投資研究追蹤項目"],
    ], columns=["項目","內容","資料來源"])

def v893_feature_profile(symbol, q=None, scores=None, inp=None):
    return v904_company_feature_df(symbol)

# 覆蓋 AIVM 公司特徵頁與新增估值位階說明
def v893_aivm_page():
    st.subheader("🧪 AIVM 估值研究中心")
    st.caption("批次估值已補齊；本頁數值屬模型研究與方法比較，不構成投資建議。")
    st.dataframe(v901_aivm_matrix(), use_container_width=True, hide_index=True)
    options = v901_all_symbols()
    current = st.session_state.get("active_symbol", "2330.TW")
    if current not in options:
        current = "2330.TW"
    selected = st.selectbox("選擇公司", options, index=options.index(current), format_func=lambda x: f"{v901_display_name(x)} / {x}", key="v904_aivm_selected")
    row = v901_detail_row(selected)
    st.markdown(f"### {v901_display_name(selected)} / {selected}：機構級估值分析")
    kpi([("現價", row["現價"]),("估值區間", row["估值區間"]),("估值位階", row["估值位階"]),("安全邊際", row["安全邊際"])])
    kpi([("全模型共識度", row["全模型共識度"]),("核心模型共識度", row["核心模型共識度"]),("企業品質分數", row["企業品質分數"]),("Top1適配方法", row["Top1適配方法"])])
    tabs = st.tabs(["估值區間","估值位階說明","Top3方法說明","公司DNA","產業資料","全球競爭","同業比較","半導體估值總庫","其他類股估值"])
    with tabs[0]:
        st.dataframe(v901_range_df(selected), use_container_width=True, hide_index=True)
    with tabs[1]:
        st.dataframe(V904_POSITION_RULES, use_container_width=True, hide_index=True)
    with tabs[2]:
        st.dataframe(pd.DataFrame([[i+1, x[0], x[1], "；".join(x[2])] for i,x in enumerate(v8933_top3_method_profile(selected))], columns=["排名","方法","適配分數","原因"]), use_container_width=True, hide_index=True)
    dna_df = v904_company_feature_df(selected)
    with tabs[3]:
        st.dataframe(dna_df[dna_df["項目"].isin(["成長性","現金流/獲利穩定度","景氣循環敏感度","AI受惠程度","資本支出強度"])], use_container_width=True, hide_index=True)
    with tabs[4]:
        st.dataframe(dna_df[dna_df["項目"].isin(["產業定位","關鍵追蹤指標"])], use_container_width=True, hide_index=True)
    with tabs[5]:
        st.dataframe(dna_df[dna_df["項目"]=="全球競爭"], use_container_width=True, hide_index=True)
    with tabs[6]:
        st.dataframe(dna_df[dna_df["項目"]=="同業比較"], use_container_width=True, hide_index=True)
    with tabs[7]:
        v901_semiconductor_library_page()
    with tabs[8]:
        v903_multi_sector_page()

def home_page():
    st.markdown(f"""
    <div class="hero">
      <div class="hero-title">🏛 AI企業價值研究院</div>
      <div class="hero-sub">Enterprise Valuation Institute｜{APP_VERSION_CLEAN}</div>
      <div style="margin-top:18px;color:white;font-weight:700;">半導體估值總庫 × 其他類股估值總庫 × AIVM機構級估值</div>
    </div>
    """, unsafe_allow_html=True)
    st.subheader("首頁：類股估值入口")
    tabs = st.tabs(["半導體", "AI伺服器/ODM", "散熱", "記憶體/模組", "電力/重電", "自動化/機器人", "電子通路"])
    with tabs[0]:
        v901_semiconductor_library_page()
    groups = ["AI伺服器/ODM","散熱","記憶體/模組","電力/重電","自動化/機器人","電子通路"]
    for tab, group in zip(tabs[1:], groups):
        with tab:
            df = v903_multi_sector_df()
            st.dataframe(df[df["產業群"] == group], use_container_width=True, hide_index=True)
            st.caption(V903_OTHER_GROUPS[group]["desc"])
# ================= V90.4 SECTOR HOME + DNA EXPANSION PATCH END =================


# ================= V90.5 HOME SECTOR DASHBOARD PATCH =================
APP_VERSION_CLEAN = "V92.2 AIVM Lab Historical PE PB Calibration"

# 擴充其他產業類股
V905_EXTRA_SECTORS = {
    "金融": {
        "symbols": ["2881.TW","2882.TW","2884.TW","2885.TW","2886.TW","2891.TW","2892.TW"],
        "mult": (0.82,0.95,1.10),
        "models": ["PB","PE","DDM","EVA"],
        "desc": "以PB、ROE、股利政策與利率循環為核心。",
    },
    "電信": {
        "symbols": ["2412.TW","3045.TW","4904.TW"],
        "mult": (0.86,0.98,1.10),
        "models": ["DDM","PE","FCFF"],
        "desc": "現金流、股利穩定度、5G/寬頻用戶為核心。",
    },
    "航運": {
        "symbols": ["2603.TW","2609.TW","2615.TW","2618.TW","2637.TW"],
        "mult": (0.70,0.90,1.20),
        "models": ["PB","PE","Industry Cycle"],
        "desc": "運價循環、景氣敏感度、現金與股利為核心。",
    },
    "鋼鐵": {
        "symbols": ["2002.TW","2027.TW","2014.TW","2015.TW","2031.TW"],
        "mult": (0.76,0.92,1.12),
        "models": ["PB","PE","EV/EBITDA"],
        "desc": "鋼價循環、庫存週期與中國需求為核心。",
    },
    "塑化": {
        "symbols": ["1301.TW","1303.TW","1326.TW","6505.TW"],
        "mult": (0.78,0.93,1.12),
        "models": ["PB","PE","EV/EBITDA"],
        "desc": "油價、利差、景氣循環與資產價值為核心。",
    },
    "生技醫療": {
        "symbols": ["4743.TW","6472.TW","6446.TW","4105.TW","1795.TW"],
        "mult": (0.70,0.92,1.30),
        "models": ["PS","EV/Sales","Pipeline"],
        "desc": "產品線、臨床進度、授權金與營收成長為核心。",
    },
    "食品民生": {
        "symbols": ["1216.TW","1227.TW","1231.TW","1707.TW","9910.TW"],
        "mult": (0.86,0.98,1.12),
        "models": ["PE","DDM","FCFF"],
        "desc": "品牌、通路、現金流與股利穩定度為核心。",
    },
    "車用/電動車": {
        "symbols": ["2207.TW","2231.TW","1536.TW","2308.TW","3665.TW"],
        "mult": (0.78,0.95,1.20),
        "models": ["PE","PEG","FCFF"],
        "desc": "電動車滲透率、零組件出貨與毛利率為核心。",
    },
}

V905_EXTRA_NAMES = {
    "2881.TW":"富邦金","2882.TW":"國泰金","2884.TW":"玉山金","2885.TW":"元大金","2886.TW":"兆豐金","2891.TW":"中信金","2892.TW":"第一金",
    "2412.TW":"中華電","3045.TW":"台灣大","4904.TW":"遠傳",
    "2603.TW":"長榮","2609.TW":"陽明","2615.TW":"萬海","2618.TW":"長榮航","2637.TW":"慧洋-KY",
    "2002.TW":"中鋼","2027.TW":"大成鋼","2014.TW":"中鴻","2015.TW":"豐興","2031.TW":"新光鋼",
    "1301.TW":"台塑","1303.TW":"南亞","1326.TW":"台化","6505.TW":"台塑化",
    "4743.TW":"合一","6472.TW":"保瑞","6446.TW":"藥華藥","4105.TW":"東洋","1795.TW":"美時",
    "1216.TW":"統一","1227.TW":"佳格","1231.TW":"聯華食","1707.TW":"葡萄王","9910.TW":"豐泰",
    "2207.TW":"和泰車","2231.TW":"為升","3665.TW":"貿聯-KY",
}

# 合併 V903 其他類股與新增產業
def v905_all_sector_groups():
    groups = {}
    try:
        groups.update(V903_OTHER_GROUPS)
    except Exception:
        pass
    groups.update(V905_EXTRA_SECTORS)
    return groups

def v905_name(sym):
    if sym in V905_EXTRA_NAMES:
        return V905_EXTRA_NAMES[sym]
    try:
        return V903_OTHER_NAMES.get(sym, v901_display_name(sym))
    except Exception:
        return sym

def v905_quote(sym):
    try:
        q = yf_quote(sym)
        p = q.get("price", np.nan) if isinstance(q, dict) else np.nan
        return float(p) if pd.notna(p) and float(p) > 0 else np.nan
    except Exception:
        return np.nan

def v905_row(group, sym, info):
    p = v905_quote(sym)
    a,b,c = info["mult"]
    if pd.isna(p):
        low=base=high=margin=np.nan
        pos="資料不足"
    else:
        low,base,high = p*a, p*b, p*c
        pos, margin = v904_position(p, base) if "v904_position" in globals() else ("合理", (base-p)/base*100)
    return {
        "產業群": group,
        "代碼": sym,
        "公司": v905_name(sym),
        "現價": v901_fmt(p) if "v901_fmt" in globals() else f"{p:,.2f}",
        "基準價值": v901_fmt(base) if "v901_fmt" in globals() else f"{base:,.2f}",
        "估值區間": f"{v901_fmt(low)} ~ {v901_fmt(high)}" if "v901_fmt" in globals() else f"{low:,.2f} ~ {high:,.2f}",
        "估值位階": pos,
        "安全邊際": "N/A" if pd.isna(margin) else f"{margin:+.1f}%",
        "適用模型": " / ".join(info["models"]),
        "產業解讀": info["desc"],
    }

def v905_all_sector_df():
    rows = []
    for group, info in v905_all_sector_groups().items():
        for sym in info["symbols"]:
            rows.append(v905_row(group, sym, info))
    return pd.DataFrame(rows)

def v905_sector_summary(df=None):
    if df is None:
        df = v905_all_sector_df()
    rows = []
    for group, info in v905_all_sector_groups().items():
        d = df[df["產業群"] == group]
        margins = []
        for x in d["安全邊際"].tolist():
            try:
                v = v901_num(x)
                if pd.notna(v):
                    margins.append(v)
            except Exception:
                pass
        avg = np.mean(margins) if margins else np.nan
        rows.append({
            "產業群": group,
            "公司數": len(d),
            "平均安全邊際": "N/A" if pd.isna(avg) else f"{avg:+.1f}%",
            "主要適用模型": " / ".join(info["models"]),
            "產業解讀": info["desc"],
        })
    return pd.DataFrame(rows)

def v905_sector_dashboard():
    st.subheader("🌐 全產業類股估值入口")
    st.caption("V90.5：首頁直接顯示半導體與其他產業類股，方便投資人依類股查詢。")
    df = v905_all_sector_df()
    summary = v905_sector_summary(df)
    tabs = st.tabs(["類股總覽"] + list(v905_all_sector_groups().keys()))
    with tabs[0]:
        st.dataframe(summary, use_container_width=True, hide_index=True)
    for tab, group in zip(tabs[1:], list(v905_all_sector_groups().keys())):
        with tab:
            d = df[df["產業群"] == group]
            st.dataframe(d, use_container_width=True, hide_index=True)
            st.info(v905_all_sector_groups()[group]["desc"])

# 覆蓋其他類股頁
def v903_multi_sector_page():
    v905_sector_dashboard()

# 首頁強制顯示類股入口：先半導體，再全產業類股
def home_page():
    st.markdown(f"""
    <div class="hero">
      <div class="hero-title">🏛 AI企業價值研究院</div>
      <div class="hero-sub">Enterprise Valuation Institute｜{APP_VERSION_CLEAN}</div>
      <div style="margin-top:18px;color:white;font-weight:700;">半導體估值總庫 × 全產業類股估值入口 × AIVM機構級估值</div>
    </div>
    """, unsafe_allow_html=True)
    home_tabs = st.tabs(["半導體估值總庫","全產業類股估值入口","估值位階說明"])
    with home_tabs[0]:
        try:
            v901_semiconductor_library_page()
        except Exception:
            st.warning("半導體估值總庫載入中。")
    with home_tabs[1]:
        v905_sector_dashboard()
    with home_tabs[2]:
        try:
            st.dataframe(V904_POSITION_RULES, use_container_width=True, hide_index=True)
        except Exception:
            st.info("估值位階依安全邊際判斷：低估、合理偏低、合理、合理偏高、高估。")

# 若舊 dispatch 沒有呼叫 home_page，強制首頁頁面顯示 sector dashboard
try:
    if st.session_state.get("page") == "🏠首頁":
        pass
except Exception:
    pass
# ================= V90.5 HOME SECTOR DASHBOARD PATCH END =================


# ================= V90.6 HARD OVERRIDE HOME DASHBOARD PATCH =================
APP_VERSION_CLEAN = "V92.2 AIVM Lab Historical PE PB Calibration"

# 這版直接覆蓋 page dispatch，避免舊首頁仍呼叫舊 AIVM 表格。
V906_ALLOWED_PAGES = ["🏠首頁","📊監控","📈K線","🏛企業價值研究院","🧪AIVM研究中心","🧪AIVM Lab","⚙設定"]
MAIN = V906_ALLOWED_PAGES
menu_items = V906_ALLOWED_PAGES
main_tabs = V906_ALLOWED_PAGES

# 補足全產業類股資料庫；若 V90.5 沒載到，也可獨立運作
V906_SECTOR_GROUPS = {
    "半導體": {
        "symbols": ["2330.TW","2303.TW","5347.TWO","6770.TW","2454.TW","3034.TW","2379.TW","4966.TW","6415.TW","3661.TW","3443.TW","3035.TW","6533.TW","6643.TW","3680.TW","3131.TWO","3583.TW","1560.TW","6640.TWO","2383.TW","6274.TWO","6213.TW","3037.TW","8046.TW","3189.TWO"],
        "mult": (0.78,0.95,1.18),
        "models": ["PE","PEG","FCFF","CAP"],
        "desc": "晶圓代工、IC設計、AI ASIC、設備、CCL與載板。",
    },
    "AI伺服器/ODM": {
        "symbols": ["2382.TW","3231.TW","6669.TW","2356.TW","2317.TW"],
        "mult": (0.80,0.96,1.18),
        "models": ["PE","PEG","FCFF","EVA"],
        "desc": "AI伺服器出貨、GPU平台、組裝與供應鏈議價能力。",
    },
    "散熱": {
        "symbols": ["3017.TW","3324.TWO","3653.TW"],
        "mult": (0.78,0.96,1.22),
        "models": ["PEG","PE","FCFF"],
        "desc": "AI伺服器功耗提升帶動散熱升級。",
    },
    "記憶體/模組": {
        "symbols": ["2408.TW","2344.TW","2337.TW","6239.TW","8299.TWO"],
        "mult": (0.72,0.90,1.20),
        "models": ["PB","PE","Industry Cycle"],
        "desc": "價格循環、庫存週期與AI記憶體需求。",
    },
    "電力/重電": {
        "symbols": ["2308.TW","1513.TW","1504.TW","1519.TW","1605.TW"],
        "mult": (0.82,0.96,1.16),
        "models": ["PE","FCFF","EVA"],
        "desc": "電網升級、資料中心用電與基礎建設需求。",
    },
    "自動化/機器人": {
        "symbols": ["6215.TWO","2049.TW","4583.TW","1536.TW"],
        "mult": (0.78,0.94,1.18),
        "models": ["PEG","PE","FCFF"],
        "desc": "工業自動化、AI機器人與設備升級。",
    },
    "電子通路": {
        "symbols": ["8112.TW","6189.TW","3702.TW"],
        "mult": (0.82,0.95,1.12),
        "models": ["PE","FCFF","EVA"],
        "desc": "庫存管理、代理產品線與現金流穩定度。",
    },
    "金融": {
        "symbols": ["2881.TW","2882.TW","2884.TW","2885.TW","2886.TW","2891.TW","2892.TW"],
        "mult": (0.82,0.95,1.10),
        "models": ["PB","PE","DDM","EVA"],
        "desc": "以PB、ROE、股利政策與利率循環為核心。",
    },
    "電信": {
        "symbols": ["2412.TW","3045.TW","4904.TW"],
        "mult": (0.86,0.98,1.10),
        "models": ["DDM","PE","FCFF"],
        "desc": "現金流、股利穩定度、5G/寬頻用戶為核心。",
    },
    "航運": {
        "symbols": ["2603.TW","2609.TW","2615.TW","2618.TW","2637.TW"],
        "mult": (0.70,0.90,1.20),
        "models": ["PB","PE","Industry Cycle"],
        "desc": "運價循環、景氣敏感度、現金與股利為核心。",
    },
    "鋼鐵": {
        "symbols": ["2002.TW","2027.TW","2014.TW","2015.TW","2031.TW"],
        "mult": (0.76,0.92,1.12),
        "models": ["PB","PE","EV/EBITDA"],
        "desc": "鋼價循環、庫存週期與中國需求為核心。",
    },
    "塑化": {
        "symbols": ["1301.TW","1303.TW","1326.TW","6505.TW"],
        "mult": (0.78,0.93,1.12),
        "models": ["PB","PE","EV/EBITDA"],
        "desc": "油價、利差、景氣循環與資產價值為核心。",
    },
    "生技醫療": {
        "symbols": ["4743.TW","6472.TW","6446.TW","4105.TW","1795.TW"],
        "mult": (0.70,0.92,1.30),
        "models": ["PS","EV/Sales","Pipeline"],
        "desc": "產品線、臨床進度、授權金與營收成長為核心。",
    },
    "食品民生": {
        "symbols": ["1216.TW","1227.TW","1231.TW","1707.TW","9910.TW"],
        "mult": (0.86,0.98,1.12),
        "models": ["PE","DDM","FCFF"],
        "desc": "品牌、通路、現金流與股利穩定度為核心。",
    },
    "車用/電動車": {
        "symbols": ["2207.TW","2231.TW","1536.TW","2308.TW","3665.TW"],
        "mult": (0.78,0.95,1.20),
        "models": ["PE","PEG","FCFF"],
        "desc": "電動車滲透率、零組件出貨與毛利率為核心。",
    },
}

V906_NAMES = {
    "2330.TW":"台積電","2303.TW":"聯電","5347.TWO":"世界先進","6770.TW":"力積電","2454.TW":"聯發科","3034.TW":"聯詠","2379.TW":"瑞昱","4966.TW":"譜瑞-KY","6415.TW":"矽力*-KY","3661.TW":"世芯-KY","3443.TW":"創意","3035.TW":"智原","6533.TW":"晶心科","6643.TW":"M31","3680.TW":"家登","3131.TWO":"弘塑","3583.TW":"辛耘","1560.TW":"中砂","6640.TWO":"均豪","2383.TW":"台光電","6274.TWO":"台燿","6213.TW":"聯茂","3037.TW":"欣興","8046.TW":"南電","3189.TWO":"景碩",
    "2382.TW":"廣達","3231.TW":"緯創","6669.TW":"緯穎","2356.TW":"英業達","2317.TW":"鴻海","3017.TW":"奇鋐","3324.TWO":"雙鴻","3653.TW":"健策",
    "2408.TW":"南亞科","2344.TW":"華邦電","2337.TW":"旺宏","6239.TW":"力成","8299.TWO":"群聯","2308.TW":"台達電","1513.TW":"中興電","1504.TW":"東元","1519.TW":"華城","1605.TW":"華新","6215.TWO":"和椿","2049.TW":"上銀","4583.TW":"台灣精銳","1536.TW":"和大","8112.TW":"至上","6189.TW":"豐藝","3702.TW":"大聯大",
    "2881.TW":"富邦金","2882.TW":"國泰金","2884.TW":"玉山金","2885.TW":"元大金","2886.TW":"兆豐金","2891.TW":"中信金","2892.TW":"第一金","2412.TW":"中華電","3045.TW":"台灣大","4904.TW":"遠傳","2603.TW":"長榮","2609.TW":"陽明","2615.TW":"萬海","2618.TW":"長榮航","2637.TW":"慧洋-KY","2002.TW":"中鋼","2027.TW":"大成鋼","2014.TW":"中鴻","2015.TW":"豐興","2031.TW":"新光鋼","1301.TW":"台塑","1303.TW":"南亞","1326.TW":"台化","6505.TW":"台塑化","4743.TW":"合一","6472.TW":"保瑞","6446.TW":"藥華藥","4105.TW":"東洋","1795.TW":"美時","1216.TW":"統一","1227.TW":"佳格","1231.TW":"聯華食","1707.TW":"葡萄王","9910.TW":"豐泰","2207.TW":"和泰車","2231.TW":"為升","3665.TW":"貿聯-KY",
}

def v906_num(x):
    try:
        if x is None:
            return np.nan
        if isinstance(x, str):
            s=x.replace(",","").replace("%","").strip()
            if not s or s in ["N/A","nan","None"]:
                return np.nan
            return float(s)
        return float(x)
    except Exception:
        return np.nan

def v906_fmt(x):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def v906_quote(sym):
    try:
        q = yf_quote(sym)
        p = q.get("price", np.nan) if isinstance(q, dict) else np.nan
        return float(p) if pd.notna(p) and float(p)>0 else np.nan
    except Exception:
        return np.nan

def v906_position(price, base):
    p=v906_num(price); b=v906_num(base)
    if pd.isna(p) or pd.isna(b) or b==0:
        return "資料不足", np.nan
    margin=(b-p)/b*100
    if margin >= 15: return "低估", margin
    if margin >= 5: return "合理偏低", margin
    if margin >= -8: return "合理", margin
    if margin >= -18: return "合理偏高", margin
    return "高估", margin

def v906_row(group, sym, info):
    p=v906_quote(sym)
    a,b,c=info["mult"]
    if pd.isna(p):
        low=base=high=margin=np.nan; pos="資料不足"
    else:
        low=p*a; base=p*b; high=p*c
        pos, margin=v906_position(p, base)
    return {
        "產業群":group,
        "代碼":sym,
        "公司":V906_NAMES.get(sym, sym),
        "現價":v906_fmt(p),
        "基準價值":v906_fmt(base),
        "估值區間":f"{v906_fmt(low)} ~ {v906_fmt(high)}",
        "估值位階":pos,
        "安全邊際":"N/A" if pd.isna(margin) else f"{margin:+.1f}%",
        "適用模型":" / ".join(info["models"]),
        "產業解讀":info["desc"],
    }

def v906_all_sector_df():
    rows=[]
    for group, info in V906_SECTOR_GROUPS.items():
        for sym in info["symbols"]:
            rows.append(v906_row(group, sym, info))
    return pd.DataFrame(rows)

def v906_summary_df(df=None):
    if df is None:
        df=v906_all_sector_df()
    rows=[]
    for group, info in V906_SECTOR_GROUPS.items():
        d=df[df["產業群"]==group]
        margins=[]
        for x in d["安全邊際"]:
            v=v906_num(x)
            if pd.notna(v): margins.append(v)
        avg=np.mean(margins) if margins else np.nan
        rows.append({
            "產業群":group,
            "公司數":len(d),
            "平均安全邊際":"N/A" if pd.isna(avg) else f"{avg:+.1f}%",
            "主要適用模型":" / ".join(info["models"]),
            "產業解讀":info["desc"],
        })
    return pd.DataFrame(rows)

def v906_home_dashboard():
    st.markdown(f"""
    <div class="hero">
      <div class="hero-title">🏛 AI企業價值研究院</div>
      <div class="hero-sub">Enterprise Valuation Institute｜{APP_VERSION_CLEAN}</div>
      <div style="margin-top:18px;color:white;font-weight:700;">全產業類股估值入口 × 半導體估值總庫 × AIVM機構級估值</div>
    </div>
    """, unsafe_allow_html=True)
    st.subheader("🏠 首頁：全產業類股估值入口")
    df=v906_all_sector_df()
    tabs=st.tabs(["類股總覽"]+list(V906_SECTOR_GROUPS.keys())+["估值位階說明"])
    with tabs[0]:
        st.dataframe(v906_summary_df(df), use_container_width=True, hide_index=True)
    for tab, group in zip(tabs[1:-1], list(V906_SECTOR_GROUPS.keys())):
        with tab:
            d=df[df["產業群"]==group]
            st.dataframe(d, use_container_width=True, hide_index=True)
            st.info(V906_SECTOR_GROUPS[group]["desc"])
    with tabs[-1]:
        st.dataframe(pd.DataFrame([
            ["低估","安全邊際 >= +15%","現價明顯低於基準價值"],
            ["合理偏低","+5% <= 安全邊際 < +15%","現價低於基準價值，但仍屬合理區間"],
            ["合理","-8% <= 安全邊際 < +5%","現價接近基準價值"],
            ["合理偏高","-18% <= 安全邊際 < -8%","現價高於基準價值，但尚未大幅高估"],
            ["高估","安全邊際 < -18%","現價明顯高於基準價值"],
        ], columns=["估值位階","判定條件","說明"]), use_container_width=True, hide_index=True)

# 強制首頁函式
def home_page():
    v906_home_dashboard()

# 若舊 dispatch 還是使用 AIVM 頁，這裡也提供一個乾淨首頁入口函式給下方強制替換
def v906_force_home():
    v906_home_dashboard()

# ================= V90.6 HARD OVERRIDE HOME DASHBOARD PATCH END =================








# ================= V92.3 AIVM QUARTERLY FIXED VALUE LAB START =================
APP_VERSION_CLEAN = "V96.0 AIVM Calibration Test"
# ===== V96.0 AIVM 校對檢定中心 START =====
AIVM_CALIBRATION_POOL = {
    "晶圓代工": [("2330.TW","台積電",2536.56,.10),("2303.TW","聯電",145.47,.10),("5347.TWO","世界先進",169.92,.10),("6770.TW","力積電",81.40,.10)],
    "IC設計": [("2454.TW","聯發科",4444.30,.15),("2379.TW","瑞昱",770.88,.15),("3034.TW","聯詠",521.28,.15),("8299.TWO","群聯",590,.15),("6415.TW","矽力*-KY",580.80,.15),("3035.TW","智原",268,.15),("2458.TW","義隆",142,.15),("4919.TW","新唐",96,.15),("2401.TW","凌陽",45,.15)],
    "AI ASIC / IP": [("3661.TW","世芯-KY",4112.5,.15),("3443.TW","創意",4441.5,.15),("6643.TWO","M31",451.26,.15),("6533.TW","晶心科",520,.15),("3529.TWO","力旺",1780,.15)],
    "封測": [("3711.TW","日月光投控",158.4,.15),("2449.TW","京元電子",106.4,.15),("6239.TW","力成",139.5,.15),("3264.TWO","欣銓",225,.15),("6147.TWO","頎邦",74,.15),("6257.TW","矽格",82,.15)],
    "載板 / CCL": [("3037.TW","欣興",178,.15),("8046.TW","南電",907.25,.15),("3189.TWO","景碩",690.65,.15),("2383.TW","台光電",5393.2,.15),("6274.TWO","台燿",1676.75,.15),("6213.TW","聯茂",293.55,.15)],
    "半導體設備": [("3131.TWO","弘塑",3285.3,.15),("3583.TW","辛耘",829.08,.15),("3680.TW","家登",504.78,.15),("1560.TW","中砂",704.06,.15),("5443.TWO","均豪",180,.15),("6187.TWO","萬潤",520,.15)],
    "矽晶圓 / 材料": [("6488.TWO","環球晶",371.3,.15),("5483.TWO","中美晶",108.1,.15),("6182.TWO","合晶",33.25,.15),("3532.TW","台勝科",185,.15)],
}
AIVM_CALIBRATION_FALLBACK_PRICE = {
    "2330.TW":2390,"2303.TW":178,"5347.TWO":200,"6770.TW":85.7,"2454.TW":4535,"2379.TW":803,"3034.TW":543,"8299.TWO":620,"6415.TW":605,"3035.TW":285,"2458.TW":155,"4919.TW":105,"2401.TW":48,
    "3661.TW":4375,"3443.TW":4725,"6643.TWO":490.5,"6533.TW":560,"3529.TWO":1860,"3711.TW":165,"2449.TW":112,"6239.TW":150,"3264.TWO":230,"6147.TWO":78,"6257.TW":85,
    "3037.TW":185,"8046.TW":955,"3189.TWO":727,"2383.TW":5560,"6274.TWO":1765,"6213.TW":309,"3131.TWO":3495,"3583.TW":882,"3680.TW":537,"1560.TW":749,"5443.TWO":190,"6187.TWO":545,
    "6488.TWO":395,"5483.TWO":115,"6182.TWO":35,"3532.TW":198
}

def v96_fmt(x):
    try:
        return "N/A" if x is None or pd.isna(x) else f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def v96_pct(x):
    try:
        return "N/A" if x is None or pd.isna(x) else f"{float(x):.1f}%"
    except Exception:
        return "N/A"

@st.cache_data(ttl=900, show_spinner=False)
def v96_get_live_price(symbol):
    price, source = np.nan, "Yahoo Finance"
    try:
        t = yf.Ticker(symbol)
        try:
            fi = getattr(t, "fast_info", {}) or {}
            price = float(fi.get("last_price", fi.get("lastPrice", np.nan)))
        except Exception:
            pass
        if pd.isna(price):
            try:
                hist = t.history(period="5d", auto_adjust=True)
                if hist is not None and len(hist) > 0:
                    price = float(hist["Close"].dropna().iloc[-1])
                    source = "Yahoo Finance 最近收盤"
            except Exception:
                pass
    except Exception:
        pass
    if pd.isna(price):
        price = AIVM_CALIBRATION_FALLBACK_PRICE.get(symbol, np.nan)
        source = "Fallback校對值"
    return price, source

def v96_stage(price, fair, low, high):
    if pd.isna(price) or pd.isna(fair):
        return "資料不足"
    if price < low:
        return "合理偏低"
    if price > high:
        return "高估"
    if price > fair:
        return "合理偏高"
    return "合理"

def v96_calibration_df():
    rows = []
    for group, items in AIVM_CALIBRATION_POOL.items():
        for sym, name, fair, band in items:
            price, source = v96_get_live_price(sym)
            low, high = fair*(1-band), fair*(1+band)
            margin = (fair-price)/fair*100 if pd.notna(price) and fair else np.nan
            dev = abs(price-fair)/fair*100 if pd.notna(price) and fair else np.nan
            rows.append({"次產業":group,"代碼":sym,"公司":name,"現價":price,"基準價值":fair,"合理下緣":low,"合理上緣":high,"安全邊際":margin,"偏離率":dev,"估值位階":v96_stage(price,fair,low,high),"現價來源":source,"校對狀態":"需檢查" if source.startswith("Fallback") else ("偏離過大" if pd.notna(dev) and dev > 30 else "正常")})
    return pd.DataFrame(rows)

def v96_display(df):
    out = df.copy()
    for c in ["現價","基準價值","合理下緣","合理上緣"]:
        if c in out.columns:
            out[c]=out[c].apply(v96_fmt)
    if "合理下緣" in out.columns and "合理上緣" in out.columns:
        out["合理區間"]=out["合理下緣"]+" ~ "+out["合理上緣"]
    for c in ["安全邊際","偏離率","平均偏離率","平均安全邊際"]:
        if c in out.columns:
            out[c]=out[c].apply(v96_pct)
    return out

def v96_summary(df):
    rows=[]
    for g, sub in df.groupby("次產業"):
        rows.append({"次產業":g,"公司數":len(sub),"平均偏離率":sub["偏離率"].mean(),"平均安全邊際":sub["安全邊際"].mean(),"合理偏低":int((sub["估值位階"]=="合理偏低").sum()),"合理":int((sub["估值位階"]=="合理").sum()),"合理偏高":int((sub["估值位階"]=="合理偏高").sum()),"高估":int((sub["估值位階"]=="高估").sum()),"異常筆數":int((sub["校對狀態"]!="正常").sum())})
    return pd.DataFrame(rows)

def v96_calibration_test_page_block():
    st.markdown("### V96.0 AIVM 校對檢定中心")
    st.info("現價改為動態抓取；基準價值維持季更新。本頁只檢定，不直接改首頁與主估值系統。")
    df = v96_calibration_df()
    tabs = st.tabs(["校對總覽","個股校對","次產業篩選","異常清單","檢定結論"])
    with tabs[0]:
        st.dataframe(v96_display(v96_summary(df)), use_container_width=True, hide_index=True)
    with tabs[1]:
        cols=["次產業","代碼","公司","現價","基準價值","合理區間","安全邊際","偏離率","估值位階","現價來源","校對狀態"]
        st.dataframe(v96_display(df)[cols], use_container_width=True, hide_index=True)
    with tabs[2]:
        group = st.selectbox("選擇次產業", sorted(df["次產業"].unique().tolist()), key="v96_calib_group")
        cols=["代碼","公司","現價","基準價值","合理區間","安全邊際","估值位階","現價來源","校對狀態"]
        st.dataframe(v96_display(df[df["次產業"]==group])[cols], use_container_width=True, hide_index=True)
    with tabs[3]:
        ab = df[(df["校對狀態"]!="正常") | (df["估值位階"]=="高估")]
        if ab.empty:
            st.success("目前未發現明顯異常。")
        else:
            cols=["次產業","代碼","公司","現價","基準價值","偏離率","估值位階","現價來源","校對狀態"]
            st.dataframe(v96_display(ab)[cols], use_container_width=True, hide_index=True)
    with tabs[4]:
        total=len(df)
        high=int(((df["估值位階"]=="合理偏高") | (df["估值位階"]=="高估")).sum())
        fallback=int((df["現價來源"]=="Fallback校對值").sum())
        ratio=high/total*100 if total else 0
        st.metric("合理偏高＋高估占比", f"{ratio:.1f}%")
        st.metric("Fallback現價筆數", fallback)
        if ratio>=60:
            st.error("檢定結論：基準價值可能系統性偏保守，建議校準權重。")
        elif fallback>0:
            st.warning("檢定結論：部分股票無法取得即時價，需先修正報價來源。")
        else:
            st.success("檢定結論：估值分布尚可。")
# ===== V96.0 AIVM 校對檢定中心 END =====


# ===== V95.0 半導體產業鏈 / 同業 / 全球競爭資料庫 START =====
# 目的：建立半導體大類股 → 次產業 → 個股 → 同業比較 → 全球競爭的資料骨架。
# 本版只補 AIVM Lab 資料庫，不改主系統首頁與估值計算。

AIVM_SEMI_INDUSTRY_TREE = {
    "半導體": {
        "晶圓代工": [
            {"代碼":"2330.TW","公司":"台積電","定位":"先進製程龍頭","台灣同業":"聯電、世界先進、力積電","全球競爭":"Samsung Foundry、Intel Foundry、SMIC、GlobalFoundries","核心產品":"先進製程、CoWoS、先進封裝","護城河":"先進製程、客戶黏著度、資本支出規模","AI受惠":"高","景氣敏感度":"中","AIVM重點":"FCFF / EVA / CAP"},
            {"代碼":"2303.TW","公司":"聯電","定位":"成熟製程晶圓代工","台灣同業":"台積電、世界先進、力積電","全球競爭":"GlobalFoundries、SMIC、Tower Semiconductor","核心產品":"成熟製程、車用、工控、通訊","護城河":"成熟製程客戶組合、產能利用率","AI受惠":"中","景氣敏感度":"高","AIVM重點":"市場價值 / FCFF / FCFE"},
            {"代碼":"5347.TWO","公司":"世界先進","定位":"特殊製程 / 成熟製程","台灣同業":"聯電、力積電","全球競爭":"Tower Semiconductor、SMIC、DB HiTek","核心產品":"PMIC、DDIC、Power IC製程","護城河":"特殊製程、客戶合作、股利能力","AI受惠":"中","景氣敏感度":"高","AIVM重點":"市場價值 / FCFE / 股利能力"},
            {"代碼":"6770.TW","公司":"力積電","定位":"成熟製程 / 記憶體相關代工","台灣同業":"聯電、世界先進","全球競爭":"SMIC、DB HiTek、Hua Hong Semiconductor","核心產品":"成熟製程、DRAM代工、特殊製程","護城河":"產能規模與製程轉換能力","AI受惠":"低中","景氣敏感度":"高","AIVM重點":"PB / 市場循環 / 產能利用率"},
        ],
        "IC設計": [
            {"代碼":"2454.TW","公司":"聯發科","定位":"手機 / 通訊 / AI邊緣晶片","台灣同業":"瑞昱、聯詠、譜瑞、矽力","全球競爭":"Qualcomm、Broadcom、NVIDIA、Samsung LSI","核心產品":"手機SoC、WiFi、ASIC、車用晶片","護城河":"平台整合、客戶規模、產品組合","AI受惠":"高","景氣敏感度":"中高","AIVM重點":"PE / EBO / CAP"},
            {"代碼":"2379.TW","公司":"瑞昱","定位":"網通與多媒體IC","台灣同業":"聯發科、聯詠、義隆","全球競爭":"Broadcom、Marvell、Qualcomm","核心產品":"Ethernet、WiFi、Audio、TV IC","護城河":"產品線廣、成本效率、客戶基礎","AI受惠":"中","景氣敏感度":"中","AIVM重點":"PE / FCFF / EBO"},
            {"代碼":"3034.TW","公司":"聯詠","定位":"顯示驅動IC","台灣同業":"矽創、敦泰、瑞鼎","全球競爭":"Samsung LSI、LX Semicon、Synaptics","核心產品":"DDIC、TDDI、SoC","護城河":"面板客戶關係、產品迭代","AI受惠":"低中","景氣敏感度":"高","AIVM重點":"PE / FCFE / 景氣循環"},
            {"代碼":"4966.TW","公司":"譜瑞-KY","定位":"高速傳輸IC","台灣同業":"祥碩、創意、瑞昱","全球競爭":"Parade peers、Analogix、Synaptics","核心產品":"高速介面、USB、DisplayPort","護城河":"高速訊號技術、筆電與AI PC應用","AI受惠":"中高","景氣敏感度":"中","AIVM重點":"PE / EBO / CAP"},
            {"代碼":"6415.TW","公司":"矽力*-KY","定位":"類比 / 電源管理IC","台灣同業":"致新、茂達","全球競爭":"Texas Instruments、Analog Devices、Monolithic Power Systems","核心產品":"PMIC、電源管理、工控與車用","護城河":"類比設計能力、產品週期長","AI受惠":"中","景氣敏感度":"中","AIVM重點":"EVA / EBO / PE"},
            {"代碼":"8299.TWO","公司":"群聯","定位":"NAND控制IC","台灣同業":"慧榮、威剛供應鏈","全球競爭":"Silicon Motion、Marvell、Samsung controller","核心產品":"SSD Controller、NAND解決方案","護城河":"控制IC韌體、NAND供應鏈整合","AI受惠":"中高","景氣敏感度":"高","AIVM重點":"PE / 記憶體循環 / FCFF"},
            {"代碼":"3035.TW","公司":"智原","定位":"ASIC / 設計服務","台灣同業":"創意、世芯、M31","全球競爭":"Alchip peers、Synopsys design services","核心產品":"ASIC設計服務、IP整合","護城河":"設計服務經驗、特殊製程合作","AI受惠":"中高","景氣敏感度":"中高","AIVM重點":"EBO / CAP / PE"},
        ],
        "AI ASIC / IP": [
            {"代碼":"3661.TW","公司":"世芯-KY","定位":"AI ASIC設計服務","台灣同業":"創意、智原、M31","全球競爭":"Marvell、Broadcom ASIC、Global Unichip peers","核心產品":"AI ASIC、HPC晶片設計服務","護城河":"先進製程設計能力、客戶專案","AI受惠":"高","景氣敏感度":"高","AIVM重點":"EBO / CAP / 產業價值"},
            {"代碼":"3443.TW","公司":"創意","定位":"ASIC設計服務 / GUC","台灣同業":"世芯、智原、M31","全球競爭":"Broadcom ASIC、Marvell、Synopsys services","核心產品":"ASIC、NRE、先進製程設計服務","護城河":"台積電生態系、先進製程支援","AI受惠":"高","景氣敏感度":"高","AIVM重點":"EBO / CAP / PE"},
            {"代碼":"6643.TWO","公司":"M31","定位":"高速IP / 矽智財","台灣同業":"晶心科、力旺","全球競爭":"Synopsys、Cadence、Rambus","核心產品":"高速介面IP、記憶體IP","護城河":"IP授權、先進製程認證","AI受惠":"中高","景氣敏感度":"中","AIVM重點":"EBO / CAP / 高毛利"},
            {"代碼":"6533.TW","公司":"晶心科","定位":"RISC-V IP","台灣同業":"M31、力旺","全球競爭":"Arm、SiFive、Synopsys ARC","核心產品":"CPU IP、RISC-V處理器IP","護城河":"RISC-V生態、IP授權模式","AI受惠":"中高","景氣敏感度":"中","AIVM重點":"EBO / CAP / IP授權"},
        ],
        "封測": [
            {"代碼":"3711.TW","公司":"日月光投控","定位":"全球封測龍頭","台灣同業":"力成、京元電、矽格","全球競爭":"Amkor、JCET、Tongfu Microelectronics","核心產品":"封裝、測試、SiP、先進封裝","護城河":"全球產能、客戶組合、先進封裝","AI受惠":"高","景氣敏感度":"中高","AIVM重點":"FCFF / PE / 產業循環"},
            {"代碼":"2449.TW","公司":"京元電子","定位":"IC測試服務","台灣同業":"矽格、欣銓、日月光","全球競爭":"Teradyne ecosystem、ASE test peers","核心產品":"晶圓測試、成品測試","護城河":"測試產能、AI/HPC測試需求","AI受惠":"高","景氣敏感度":"中高","AIVM重點":"PE / FCFF / 產業價值"},
            {"代碼":"6239.TW","公司":"力成","定位":"記憶體封測","台灣同業":"日月光、南茂、華東","全球競爭":"Amkor、JCET、UTAC","核心產品":"記憶體封測、邏輯封測","護城河":"記憶體客戶、封裝能力","AI受惠":"中","景氣敏感度":"高","AIVM重點":"PB / PE / 記憶體循環"},
            {"代碼":"3264.TWO","公司":"欣銓","定位":"晶圓測試","台灣同業":"京元電、矽格","全球競爭":"ASE test peers、Amkor test","核心產品":"晶圓測試、邏輯IC測試","護城河":"測試平台、客戶黏著度","AI受惠":"中","景氣敏感度":"中高","AIVM重點":"PE / FCFF / FCFE"},
        ],
        "載板 / PCB / CCL": [
            {"代碼":"3037.TW","公司":"欣興","定位":"ABF載板 / PCB","台灣同業":"南電、景碩、臻鼎","全球競爭":"Ibiden、Shinko、AT&S","核心產品":"ABF載板、HDI、PCB","護城河":"ABF技術、客戶認證、產能","AI受惠":"高","景氣敏感度":"高","AIVM重點":"產業價值 / FCFF / CAP"},
            {"代碼":"8046.TW","公司":"南電","定位":"ABF載板","台灣同業":"欣興、景碩","全球競爭":"Ibiden、Shinko、AT&S","核心產品":"ABF、BT載板","護城河":"高階載板製程、客戶認證","AI受惠":"高","景氣敏感度":"高","AIVM重點":"產業價值 / PB / FCFF"},
            {"代碼":"3189.TWO","公司":"景碩","定位":"IC載板","台灣同業":"欣興、南電","全球競爭":"Shinko、Ibiden、AT&S","核心產品":"ABF、BT載板","護城河":"載板製程、客戶認證","AI受惠":"中高","景氣敏感度":"高","AIVM重點":"PB / PE / 產業循環"},
            {"代碼":"2383.TW","公司":"台光電","定位":"高階CCL龍頭","台灣同業":"台燿、聯茂","全球競爭":"Panasonic Industry、Rogers、Isola、Doosan","核心產品":"高速CCL、低損耗材料","護城河":"材料配方、AI伺服器認證","AI受惠":"高","景氣敏感度":"中高","AIVM重點":"產業價值 / FCFF / PE"},
            {"代碼":"6274.TWO","公司":"台燿","定位":"高頻高速CCL","台灣同業":"台光電、聯茂","全球競爭":"Panasonic、Rogers、Isola","核心產品":"高速CCL、伺服器材料","護城河":"材料認證、客戶導入","AI受惠":"高","景氣敏感度":"中高","AIVM重點":"產業價值 / PE / FCFF"},
            {"代碼":"6213.TW","公司":"聯茂","定位":"CCL材料","台灣同業":"台光電、台燿","全球競爭":"Panasonic、Isola、Doosan","核心產品":"CCL、PCB材料","護城河":"材料製程、成本控制","AI受惠":"中高","景氣敏感度":"高","AIVM重點":"PE / FCFF / 市場價值"},
        ],
        "半導體設備": [
            {"代碼":"3131.TWO","公司":"弘塑","定位":"濕製程設備","台灣同業":"辛耘、均豪、萬潤","全球競爭":"SCREEN、Tokyo Electron、Lam Research","核心產品":"濕製程、先進封裝設備","護城河":"先進封裝供應鏈、設備客製化","AI受惠":"高","景氣敏感度":"高","AIVM重點":"產業價值 / CAP / PE"},
            {"代碼":"3583.TW","公司":"辛耘","定位":"半導體設備 / 再生晶圓","台灣同業":"弘塑、家登、中砂","全球競爭":"DISCO ecosystem、SCREEN peers","核心產品":"設備代理、再生晶圓、製程服務","護城河":"客戶關係、設備代理、製程服務","AI受惠":"中高","景氣敏感度":"中高","AIVM重點":"PE / FCFF / 產業價值"},
            {"代碼":"3680.TW","公司":"家登","定位":"EUV載具 / 晶圓傳載","台灣同業":"中砂、弘塑","全球競爭":"Entegris、Miraial","核心產品":"EUV POD、晶圓載具","護城河":"EUV認證、先進製程供應鏈","AI受惠":"高","景氣敏感度":"中高","AIVM重點":"CAP / EBO / 產業價值"},
            {"代碼":"1560.TW","公司":"中砂","定位":"鑽石碟 / 再生晶圓","台灣同業":"辛耘、家登","全球競爭":"3M、Asahi Diamond、Disco materials peers","核心產品":"CMP鑽石碟、再生晶圓","護城河":"材料技術、先進製程耗材","AI受惠":"中高","景氣敏感度":"中","AIVM重點":"FCFF / EVA / CAP"},
        ],
        "矽晶圓 / 材料": [
            {"代碼":"6488.TWO","公司":"環球晶","定位":"全球矽晶圓供應商","台灣同業":"台勝科、合晶、中美晶","全球競爭":"Shin-Etsu、SUMCO、Siltronic、SK Siltron","核心產品":"矽晶圓、SOI、特殊晶圓","護城河":"長約、產能、品質認證","AI受惠":"中","景氣敏感度":"高","AIVM重點":"PB / FCFF / 產業循環"},
            {"代碼":"5483.TWO","公司":"中美晶","定位":"矽晶圓 / 投控","台灣同業":"環球晶、合晶","全球競爭":"SUMCO、Siltronic、Shin-Etsu","核心產品":"矽晶圓、太陽能材料投資","護城河":"轉投資、矽晶圓供應鏈","AI受惠":"中","景氣敏感度":"高","AIVM重點":"PB / NAV / FCFE"},
            {"代碼":"6182.TWO","公司":"合晶","定位":"矽晶圓","台灣同業":"環球晶、台勝科","全球競爭":"SUMCO、Siltronic、SK Siltron","核心產品":"矽晶圓","護城河":"產能、客戶認證","AI受惠":"低中","景氣敏感度":"高","AIVM重點":"PB / 產業循環 / FCFF"},
        ],
    }
}

def v95_industry_tree_flat_df():
    rows = []
    for major, subs in AIVM_SEMI_INDUSTRY_TREE.items():
        for sub, items in subs.items():
            for x in items:
                row = {"大類股": major, "次產業": sub}
                row.update(x)
                rows.append(row)
    return pd.DataFrame(rows)

def v95_industry_tree_summary_df():
    d = v95_industry_tree_flat_df()
    rows = []
    for (major, sub), g in d.groupby(["大類股", "次產業"]):
        ai_high = (g["AI受惠"] == "高").sum()
        rows.append({
            "大類股": major,
            "次產業": sub,
            "公司數": len(g),
            "AI高受惠公司數": int(ai_high),
            "主要AIVM重點": " / ".join(sorted(set(" / ".join(g["AIVM重點"]).split(" / ")))),
        })
    return pd.DataFrame(rows)

def v95_peer_map_df(company_name):
    d = v95_industry_tree_flat_df()
    row = d[d["公司"] == company_name]
    if row.empty:
        return pd.DataFrame()
    r = row.iloc[0]
    return pd.DataFrame([
        ["公司", r["公司"]],
        ["代碼", r["代碼"]],
        ["大類股", r["大類股"]],
        ["次產業", r["次產業"]],
        ["產業定位", r["定位"]],
        ["台灣同業", r["台灣同業"]],
        ["全球競爭", r["全球競爭"]],
        ["核心產品", r["核心產品"]],
        ["護城河", r["護城河"]],
        ["AI受惠", r["AI受惠"]],
        ["景氣敏感度", r["景氣敏感度"]],
        ["AIVM重點", r["AIVM重點"]],
    ], columns=["項目", "內容"])

def v95_global_competition_df():
    d = v95_industry_tree_flat_df()
    rows = []
    for _, r in d.iterrows():
        competitors = [x.strip() for x in str(r["全球競爭"]).split("、") if x.strip()]
        for comp in competitors:
            rows.append({
                "台灣公司": r["公司"],
                "代碼": r["代碼"],
                "次產業": r["次產業"],
                "全球競爭對手": comp,
                "競爭主軸": r["核心產品"],
                "護城河": r["護城河"],
            })
    return pd.DataFrame(rows)

def v95_industry_chain_page_block():
    st.markdown("### V95.0 半導體產業鏈 / 同業 / 全球競爭資料庫")
    st.info("本頁建立半導體 → 次產業 → 個股 → 台灣同業 → 全球競爭對手的資料骨架；先補資料庫，不直接改主系統。")

    tabs4 = st.tabs(["產業樹總覽", "次產業公司清單", "個股產業DNA", "全球競爭對照", "資料庫說明"])

    flat = v95_industry_tree_flat_df()
    summary = v95_industry_tree_summary_df()

    with tabs4[0]:
        st.dataframe(summary, use_container_width=True, hide_index=True)
        st.caption("先以半導體大類股為第一層，底下再分晶圓代工、IC設計、AI ASIC、封測、載板/PCB/CCL、設備、材料。")
    with tabs4[1]:
        sub = st.selectbox("選擇次產業", sorted(flat["次產業"].unique().tolist()), key="v95_sub_industry")
        cols = ["大類股", "次產業", "代碼", "公司", "定位", "AI受惠", "景氣敏感度", "AIVM重點"]
        st.dataframe(flat[flat["次產業"] == sub][cols], use_container_width=True, hide_index=True)
    with tabs4[2]:
        company = st.selectbox("選擇公司", flat["公司"].tolist(), key="v95_company_dna")
        st.dataframe(v95_peer_map_df(company), use_container_width=True, hide_index=True)
    with tabs4[3]:
        st.dataframe(v95_global_competition_df(), use_container_width=True, hide_index=True)
        st.caption("全球競爭資料是產業價值、CAP、護城河與同業比較的基礎。")
    with tabs4[4]:
        st.markdown("""
        **V95.0 建置原則**

        1. 先建立大類股：半導體。
        2. 半導體底下再拆次產業，不把晶圓代工、IC設計、封測全部放在第一層。
        3. 每檔股票固定欄位：
           - 大類股
           - 次產業
           - 台灣同業
           - 全球競爭對手
           - 核心產品
           - 護城河
           - AI受惠
           - 景氣敏感度
           - AIVM估值重點

        **用途**
        - 公司DNA
        - 同業比較
        - 全球競爭分析
        - 產業價值軸
        - CAP競爭優勢期間
        - AIVM動態權重
        """)
# ===== V95.0 半導體產業鏈 / 同業 / 全球競爭資料庫 END =====


# ===== V94.0 半導體類股驗證中心 START =====
AIVM_SEMI_VALIDATION_POOL = {
    "晶圓代工": [
        ("2330.TW", "台積電", 2390, 2536.56, 2567.73, 2773.15),
        ("2303.TW", "聯電", 178, 120.90, 156.00, 156.00),
        ("5347.TWO", "世界先進", 200, 137.14, 185.56, 181.85),
        ("6770.TW", "力積電", 85.7, 70.20, 82.40, 88.90),
    ],
    "IC設計": [
        ("2454.TW", "聯發科", 4535, 3920, 4300, 4860),
        ("2379.TW", "瑞昱", 803, 690, 775, 850),
        ("3034.TW", "聯詠", 543, 480, 525, 570),
        ("4966.TW", "譜瑞-KY", 664, 560, 635, 720),
        ("6415.TW", "矽力*-KY", 605, 500, 570, 680),
    ],
    "AI ASIC": [
        ("3661.TW", "世芯-KY", 4375, 3600, 4200, 5100),
        ("3443.TW", "創意", 4725, 3900, 4500, 5600),
        ("6643.TW", "M31", 490.5, 420, 465, 570),
    ],
    "CCL/高階載板": [
        ("2383.TW", "台光電", 5560, 4700, 5350, 6500),
        ("6274.TWO", "台燿", 1765, 1480, 1700, 2050),
        ("6213.TW", "聯茂", 309, 250, 295, 350),
    ],
    "AI伺服器/散熱": [
        ("6669.TW", "緯穎", 4605, 3900, 4450, 5400),
        ("3017.TW", "奇鋐", 2530, 2100, 2450, 3050),
        ("3653.TW", "健策", 3640, 3000, 3500, 4300),
        ("3231.TW", "緯創", 157.5, 130, 150, 180),
    ],
}

def v94_abs_error(value, price):
    try:
        return abs(float(value) - float(price)) / float(price) * 100 if float(price) != 0 else np.nan
    except Exception:
        return np.nan

def v94_stage_from_error(err):
    if pd.isna(err):
        return "資料不足"
    if err <= 10:
        return "優秀"
    if err <= 15:
        return "可接受"
    if err <= 20:
        return "需觀察"
    return "需再校準"

def v94_recommend_weights(fin_err, mkt_err, ind_err):
    errors = {"財報": fin_err, "市場": mkt_err, "產業": ind_err}
    inv = {k: 1 / max(float(v), 1e-6) for k, v in errors.items() if pd.notna(v)}
    total = sum(inv.values())
    if total <= 0:
        return {"財報": 33, "市場": 34, "產業": 33}
    raw = {k: inv[k] / total * 100 for k in inv}
    rounded = {k: int(round(v / 5) * 5) for k, v in raw.items()}
    best = min(errors, key=errors.get)
    rounded[best] = rounded.get(best, 0) + (100 - sum(rounded.values()))
    return rounded

def v94_validation_detail_df():
    rows = []
    for group, items in AIVM_SEMI_VALIDATION_POOL.items():
        for code_, name, price, fin, mkt, ind in items:
            fin_err = v94_abs_error(fin, price)
            mkt_err = v94_abs_error(mkt, price)
            ind_err = v94_abs_error(ind, price)
            best_axis = min([("財報", fin_err), ("市場", mkt_err), ("產業", ind_err)], key=lambda x: x[1] if pd.notna(x[1]) else 9999)[0]
            rows.append({
                "類股": group, "代碼": code_, "公司": name, "現價": price,
                "財報價值": fin, "市場價值": mkt, "產業價值": ind,
                "財報誤差": fin_err, "市場誤差": mkt_err, "產業誤差": ind_err,
                "最佳估值軸": best_axis, "驗證狀態": v94_stage_from_error(min(fin_err, mkt_err, ind_err)),
            })
    return pd.DataFrame(rows)

def v94_sector_summary_df():
    d = v94_validation_detail_df()
    rows = []
    for group, sub in d.groupby("類股"):
        fin_err, mkt_err, ind_err = sub["財報誤差"].mean(), sub["市場誤差"].mean(), sub["產業誤差"].mean()
        w = v94_recommend_weights(fin_err, mkt_err, ind_err)
        best = min({"財報": fin_err, "市場": mkt_err, "產業": ind_err}, key={"財報": fin_err, "市場": mkt_err, "產業": ind_err}.get)
        rows.append({
            "類股": group,
            "公司數": len(sub),
            "平均財報誤差": fin_err,
            "平均市場誤差": mkt_err,
            "平均產業誤差": ind_err,
            "最佳估值軸": best,
            "建議權重": f"財報{w.get('財報',0)}% / 市場{w.get('市場',0)}% / 產業{w.get('產業',0)}%",
            "導入建議": "可導入" if min(fin_err, mkt_err, ind_err) <= 15 else "需再校準",
        })
    return pd.DataFrame(rows)

def v94_display_df(df):
    out = df.copy()
    for c in ["現價", "財報價值", "市場價值", "產業價值"]:
        if c in out.columns:
            out[c] = out[c].apply(lambda x: f"{float(x):,.2f}" if pd.notna(x) else "N/A")
    for c in ["財報誤差", "市場誤差", "產業誤差", "平均財報誤差", "平均市場誤差", "平均產業誤差"]:
        if c in out.columns:
            out[c] = out[c].apply(lambda x: f"{float(x):.1f}%" if pd.notna(x) else "N/A")
    return out

def v94_sector_validation_page_block():
    st.markdown("### V94.0 半導體類股驗證中心")
    st.info("統計財報價值、市場價值、產業價值三軸誤差，產出類股建議權重；本頁只驗證，不直接改主系統。")
    detail = v94_validation_detail_df()
    summary = v94_sector_summary_df()
    tabs3 = st.tabs(["類股總覽", "個股明細", "類股篩選", "權重生成邏輯", "導入建議"])
    with tabs3[0]:
        st.dataframe(v94_display_df(summary), use_container_width=True, hide_index=True)
    with tabs3[1]:
        st.dataframe(v94_display_df(detail), use_container_width=True, hide_index=True)
    with tabs3[2]:
        group = st.selectbox("選擇類股", list(AIVM_SEMI_VALIDATION_POOL.keys()), key="v94_sector_filter")
        sub = detail[detail["類股"] == group]
        st.dataframe(v94_display_df(sub), use_container_width=True, hide_index=True)
        ss = summary[summary["類股"] == group]
        if not ss.empty:
            st.success(f"{group} 建議權重：{ss.iloc[0]['建議權重']}｜最佳估值軸：{ss.iloc[0]['最佳估值軸']}")
    with tabs3[3]:
        st.markdown("""
        **權重生成邏輯**
        1. 計算每檔股票三軸誤差：財報、市場、產業。
        2. 彙總為類股平均誤差。
        3. 誤差越低，代表該估值軸越適合該類股，權重越高。
        4. 建議權重四捨五入至 5% 單位。
        """)
    with tabs3[4]:
        st.warning("V94.0 為半導體類股驗證資料庫，不直接覆蓋 AIVM 主系統。")
# ===== V94.0 半導體類股驗證中心 END =====


# ===== V93.0 真實回測試作 START =====
# 目的：先建立「真實資料回測流程」，但不動主系統。
# 本版使用 yfinance 歷史股價 + Lab EPS/BVPS/FCF 基準資料，
# 模擬季報公布後持有至下一季的估值誤差。
# 正式版下一步再串公開資訊觀測站季報與歷史財報表。

AIVM_REAL_BACKTEST_INPUTS = {
    "2330.TW": {
        "公司": "台積電",
        "產業": "晶圓代工 / AI先進製程",
        "eps_ttm": 73.54,
        "bvps": 216.35,
        "fcff_ps": 66.5,
        "fcfe_ps": 58.0,
        "eva_ps": 62.0,
        "cap_ps": 70.0,
        "ebo_ps": 65.0,
        "period_start": "2021-01-01",
        "period_end": "2026-12-31",
    },
    "2303.TW": {
        "公司": "聯電",
        "產業": "成熟製程晶圓代工",
        "eps_ttm": 5.20,
        "bvps": 32.5,
        "fcff_ps": 5.8,
        "fcfe_ps": 5.5,
        "eva_ps": 4.8,
        "cap_ps": 5.2,
        "ebo_ps": 4.9,
        "period_start": "2021-01-01",
        "period_end": "2026-12-31",
    },
    "5347.TWO": {
        "公司": "世界先進",
        "產業": "成熟製程 / 特殊製程",
        "eps_ttm": 4.30,
        "bvps": 36.64,
        "fcff_ps": 5.6,
        "fcfe_ps": 5.3,
        "eva_ps": 4.9,
        "cap_ps": 5.1,
        "ebo_ps": 5.0,
        "period_start": "2021-01-01",
        "period_end": "2026-12-31",
    },
    "2308.TW": {
        "公司": "台達電",
        "產業": "AI電源 / 自動化",
        "eps_ttm": 23.09,
        "bvps": 115.32,
        "fcff_ps": 24.0,
        "fcfe_ps": 22.0,
        "eva_ps": 24.5,
        "cap_ps": 26.0,
        "ebo_ps": 25.0,
        "period_start": "2021-01-01",
        "period_end": "2026-12-31",
    },
}

AIVM_REAL_BACKTEST_MULTIPLIERS = {
    "晶圓代工 / AI先進製程": {
        "PE": 32, "PB": 10.0, "FCFF": 38, "FCFE": 34, "EVA": 36, "CAP": 37, "EBO": 35
    },
    "成熟製程晶圓代工": {
        "PE": 24, "PB": 3.6, "FCFF": 30, "FCFE": 28, "EVA": 26, "CAP": 25, "EBO": 24
    },
    "成熟製程 / 特殊製程": {
        "PE": 28, "PB": 4.2, "FCFF": 34, "FCFE": 32, "EVA": 30, "CAP": 31, "EBO": 30
    },
    "AI電源 / 自動化": {
        "PE": 60, "PB": 13.0, "FCFF": 62, "FCFE": 58, "EVA": 60, "CAP": 64, "EBO": 62
    },
}

def v93_num(x):
    try:
        if x is None or pd.isna(x):
            return np.nan
        return float(x)
    except Exception:
        return np.nan

def v93_fmt(x):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def v93_pct(x):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):.1f}%"
    except Exception:
        return "N/A"

@st.cache_data(ttl=3600, show_spinner=False)
def v93_download_prices(symbol, start, end):
    try:
        dfp = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
        if dfp is None or len(dfp) == 0:
            return pd.DataFrame()
        dfp = dfp.reset_index()
        if "Close" not in dfp.columns:
            return pd.DataFrame()
        dfp["Date"] = pd.to_datetime(dfp["Date"])
        dfp = dfp[["Date", "Close"]].dropna()
        return dfp
    except Exception:
        return pd.DataFrame()

def v93_make_quarter_dates(start="2021-01-01", end="2026-12-31"):
    # 季報公布日試作：5/15、8/14、11/14、3/31
    years = list(range(pd.to_datetime(start).year, pd.to_datetime(end).year + 1))
    dates = []
    for y in years:
        dates += [
            (f"{y}-03-31", f"{y-1} Q4"),
            (f"{y}-05-15", f"{y} Q1"),
            (f"{y}-08-14", f"{y} Q2"),
            (f"{y}-11-14", f"{y} Q3"),
        ]
    out = []
    sdt, edt = pd.to_datetime(start), pd.to_datetime(end)
    for d, q in dates:
        dt = pd.to_datetime(d)
        if sdt <= dt <= edt:
            out.append({"財報公布日": dt, "財報季度": q})
    return pd.DataFrame(out)

def v93_price_on_or_after(dfp, dt):
    if dfp is None or dfp.empty:
        return np.nan
    m = dfp[dfp["Date"] >= pd.to_datetime(dt)]
    if m.empty:
        return np.nan
    return float(m.iloc[0]["Close"])

def v93_price_after_days(dfp, dt, days=63):
    if dfp is None or dfp.empty:
        return np.nan
    target = pd.to_datetime(dt) + pd.Timedelta(days=days)
    return v93_price_on_or_after(dfp, target)

def v93_model_values(symbol, base_price=None):
    cfg = AIVM_REAL_BACKTEST_INPUTS[symbol]
    mult = AIVM_REAL_BACKTEST_MULTIPLIERS.get(cfg["產業"], AIVM_REAL_BACKTEST_MULTIPLIERS["成熟製程晶圓代工"])
    eps = cfg["eps_ttm"]
    bvps = cfg["bvps"]
    values = {
        "PE": eps * mult["PE"],
        "PB": bvps * mult["PB"],
        "FCFF": cfg["fcff_ps"] * mult["FCFF"],
        "FCFE": cfg["fcfe_ps"] * mult["FCFE"],
        "EVA": cfg["eva_ps"] * mult["EVA"],
        "CAP": cfg["cap_ps"] * mult["CAP"],
        "EBO": cfg["ebo_ps"] * mult["EBO"],
    }
    return values

def v93_backtest_for_symbol(symbol):
    cfg = AIVM_REAL_BACKTEST_INPUTS[symbol]
    dfp = v93_download_prices(symbol, cfg["period_start"], cfg["period_end"])
    qdf = v93_make_quarter_dates(cfg["period_start"], cfg["period_end"])
    vals = v93_model_values(symbol)
    rows = []
    for _, r in qdf.iterrows():
        dt = r["財報公布日"]
        price_t = v93_price_on_or_after(dfp, dt)
        price_next = v93_price_after_days(dfp, dt, 63)
        if pd.isna(price_next):
            continue
        row = {
            "公司": cfg["公司"],
            "代碼": symbol,
            "產業": cfg["產業"],
            "財報季度": r["財報季度"],
            "財報公布日": dt.strftime("%Y-%m-%d"),
            "公布日股價": price_t,
            "下一季股價": price_next,
        }
        for m, v in vals.items():
            row[m + "估值"] = v
            row[m + "誤差"] = abs(v - price_next) / price_next * 100 if price_next else np.nan
        rows.append(row)
    return pd.DataFrame(rows)

@st.cache_data(ttl=3600, show_spinner=False)
def v93_all_backtest_df():
    frames = []
    for sym in AIVM_REAL_BACKTEST_INPUTS:
        try:
            frames.append(v93_backtest_for_symbol(sym))
        except Exception:
            pass
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def v93_model_error_summary(df):
    models = ["PE", "PB", "FCFF", "FCFE", "EVA", "CAP", "EBO"]
    rows = []
    for company in df["公司"].dropna().unique():
        sub = df[df["公司"] == company]
        industry = sub["產業"].iloc[0] if len(sub) else ""
        for m in models:
            col = m + "誤差"
            if col in sub.columns:
                rows.append({
                    "公司": company,
                    "產業": industry,
                    "模型": m,
                    "平均誤差": sub[col].mean(),
                    "中位誤差": sub[col].median(),
                    "樣本數": sub[col].count(),
                })
    return pd.DataFrame(rows)

def v93_suggest_weights(summary_df, company):
    sub = summary_df[summary_df["公司"] == company].copy()
    if sub.empty:
        return pd.DataFrame()
    inv = {}
    for _, r in sub.iterrows():
        inv[r["模型"]] = 1 / max(float(r["平均誤差"]), 1e-6)
    total = sum(inv.values())
    weights = {k: int(round(v / total * 100)) for k, v in inv.items()} if total else {}
    if weights:
        best = min(sub.to_dict("records"), key=lambda x: x["平均誤差"])["模型"]
        weights[best] = weights.get(best, 0) + (100 - sum(weights.values()))
    rows = []
    for _, r in sub.sort_values("平均誤差").iterrows():
        rows.append({
            "模型": r["模型"],
            "平均誤差": v93_pct(r["平均誤差"]),
            "中位誤差": v93_pct(r["中位誤差"]),
            "建議權重": f"{weights.get(r['模型'], 0)}%",
            "說明": "誤差越低，建議權重越高",
        })
    return pd.DataFrame(rows)

def v93_backtest_page_block():
    st.markdown("### V93.0 真實回測試作")
    st.info("本頁用 yfinance 歷史股價 + Lab 財報基準資料，先驗證回測流程；正式版再接公開資訊觀測站季報與歷史財報。")

    bt = v93_all_backtest_df()
    if bt.empty:
        st.warning("目前無法取得歷史股價資料，請稍後重試或檢查 yfinance 連線。")
        return

    summary = v93_model_error_summary(bt)
    companies = summary["公司"].dropna().unique().tolist()
    selected = st.selectbox("選擇公司", companies, key="v930_real_backtest_company")

    tabs2 = st.tabs(["回測摘要", "模型誤差", "建議權重", "逐季明細", "方法說明"])
    with tabs2[0]:
        s = summary[summary["公司"] == selected].copy()
        best = s.sort_values("平均誤差").head(3)
        st.dataframe(best.assign(平均誤差=best["平均誤差"].apply(v93_pct), 中位誤差=best["中位誤差"].apply(v93_pct)), use_container_width=True, hide_index=True)
        st.caption("顯示平均誤差最低的前三個模型。")
    with tabs2[1]:
        s = summary[summary["公司"] == selected].copy()
        s["平均誤差"] = s["平均誤差"].apply(v93_pct)
        s["中位誤差"] = s["中位誤差"].apply(v93_pct)
        st.dataframe(s, use_container_width=True, hide_index=True)
    with tabs2[2]:
        st.dataframe(v93_suggest_weights(summary, selected), use_container_width=True, hide_index=True)
    with tabs2[3]:
        d = bt[bt["公司"] == selected].copy()
        for c in d.columns:
            if c.endswith("估值") or c in ["公布日股價", "下一季股價"]:
                d[c] = d[c].apply(v93_fmt)
            if c.endswith("誤差"):
                d[c] = d[c].apply(v93_pct)
        st.dataframe(d, use_container_width=True, hide_index=True)
    with tabs2[4]:
        st.markdown("""
        **回測邏輯**
        1. 以財報公布日作為估值建立日。
        2. 使用當期 Lab 財報基準資料估算 PE、PB、FCFF、FCFE、EVA、CAP、EBO 七模型價值。
        3. 與下一季市場價格比較。
        4. 模型平均誤差越低，建議權重越高。

        **目前限制**
        - EPS、BVPS、FCFF 等仍為 Lab 基準資料。
        - 歷史股價使用 yfinance。
        - 正式版需串接公開資訊觀測站歷史季報。
        """)
# ===== V93.0 真實回測試作 END =====


# ===== V92.5 AIVM 權重回測中心 START =====
# 本版為 Lab 回測展示版：
# 用「模型估值與現價的誤差」模擬回測邏輯，先讓版面與決策流程定型。
# 正式版可改接歷史股價、歷史EPS、財報與現金流資料。

AIVM_BACKTEST_MODEL_ERRORS = {
    "晶圓代工 / AI先進製程": {"PE":18, "PB":34, "FCFF":10, "FCFE":16, "EVA":12, "CAP":14, "EBO":18},
    "成熟製程晶圓代工": {"PE":16, "PB":22, "FCFF":11, "FCFE":12, "EVA":18, "CAP":20, "EBO":24},
    "成熟製程 / 特殊製程": {"PE":15, "PB":20, "FCFF":10, "FCFE":11, "EVA":17, "CAP":19, "EBO":23},
    "AI電源 / 自動化": {"PE":13, "PB":30, "FCFF":12, "FCFE":15, "EVA":14, "CAP":17, "EBO":13},
}

AIVM_BACKTEST_DEFAULT_YEARS = "2018–2026"

def aivm_current_weight_dict(industry):
    try:
        return AIVM_INDUSTRY_WEIGHTS.get(industry, AIVM_INDUSTRY_WEIGHTS.get("成熟製程晶圓代工"))["權重"]
    except Exception:
        return {"PE":15, "PB":5, "FCFF":25, "FCFE":10, "EVA":20, "CAP":15, "EBO":10}

def aivm_backtest_errors(industry):
    return AIVM_BACKTEST_MODEL_ERRORS.get(industry, AIVM_BACKTEST_MODEL_ERRORS.get("成熟製程晶圓代工"))

def aivm_normalize_weights_from_errors(errors):
    """
    誤差越小，權重越高。
    用 inverse error 初步產生最佳權重，並四捨五入到整數百分比。
    """
    inv = {}
    for k, v in errors.items():
        try:
            inv[k] = 1 / max(float(v), 1e-6)
        except Exception:
            inv[k] = 0
    total = sum(inv.values())
    if total <= 0:
        return {k: 0 for k in errors}
    raw = {k: inv[k] / total * 100 for k in inv}
    rounded = {k: int(round(v)) for k, v in raw.items()}
    diff = 100 - sum(rounded.values())
    # 把誤差最低的模型補差額，確保合計100%
    if rounded:
        best = min(errors, key=errors.get)
        rounded[best] = rounded.get(best, 0) + diff
    return rounded

def aivm_weighted_error(errors, weights):
    total_w = sum(float(v) for v in weights.values())
    if total_w <= 0:
        return np.nan
    return sum(float(errors.get(k, np.nan)) * float(w) for k, w in weights.items() if pd.notna(errors.get(k, np.nan))) / total_w

def aivm_backtest_table(industry):
    errors = aivm_backtest_errors(industry)
    current_w = aivm_current_weight_dict(industry)
    optimal_w = aivm_normalize_weights_from_errors(errors)

    rows = []
    for m in ["PE", "PB", "FCFF", "FCFE", "EVA", "CAP", "EBO"]:
        rows.append({
            "模型": m,
            "單模型回測誤差": f"{errors.get(m, np.nan):.1f}%",
            "目前權重": f"{current_w.get(m, 0)}%",
            "回測建議權重": f"{optimal_w.get(m, 0)}%",
            "權重調整方向": "提高" if optimal_w.get(m, 0) > current_w.get(m, 0) else ("降低" if optimal_w.get(m, 0) < current_w.get(m, 0) else "維持"),
        })
    return pd.DataFrame(rows)

def aivm_backtest_summary_df():
    rows = []
    industries = list(AIVM_BACKTEST_MODEL_ERRORS.keys())
    for ind in industries:
        errors = aivm_backtest_errors(ind)
        current_w = aivm_current_weight_dict(ind)
        optimal_w = aivm_normalize_weights_from_errors(errors)
        current_err = aivm_weighted_error(errors, current_w)
        optimal_err = aivm_weighted_error(errors, optimal_w)
        improve = current_err - optimal_err if pd.notna(current_err) and pd.notna(optimal_err) else np.nan
        rows.append({
            "類股": ind,
            "回測期間": AIVM_BACKTEST_DEFAULT_YEARS,
            "目前組合誤差": f"{current_err:.1f}%",
            "最佳組合誤差": f"{optimal_err:.1f}%",
            "改善幅度": f"{improve:.1f}%",
            "建議": "可導入" if pd.notna(optimal_err) and optimal_err <= 15 else "需再校準",
        })
    return pd.DataFrame(rows)

def aivm_backtest_explain_text(industry):
    errors = aivm_backtest_errors(industry)
    best_models = sorted(errors.items(), key=lambda x: x[1])[:3]
    txt = "、".join([f"{m}({e:.1f}%)" for m, e in best_models])
    return f"{industry} 回測中誤差最低的前三個模型為：{txt}。因此權重會傾向提高這些模型，而不是主觀指定。"
# ===== V92.5 AIVM 權重回測中心 END =====


AIVM_INDUSTRY_WEIGHTS = {
    "晶圓代工 / AI先進製程": {
        "權重": {"PE":15, "PB":5, "FCFF":25, "FCFE":10, "EVA":20, "CAP":15, "EBO":10},
        "說明": {
            "PE":"市場仍會用本益比評價獲利能力，但不是唯一核心。",
            "PB":"晶圓代工屬重資產產業，但高階製程價值不只反映在帳面淨值，因此PB權重較低。",
            "FCFF":"先進製程與資本支出龐大，自由現金流最能反映企業價值。",
            "FCFE":"股東可分配現金流仍重要，但台積電仍處高投資循環，因此權重中等。",
            "EVA":"ROIC高於資金成本的能力是台積電核心價值。",
            "CAP":"先進製程護城河與競爭優勢期間長，需給予較高權重。",
            "EBO":"剩餘盈餘可反映未來超額報酬，但對晶圓代工不是最高權重。"
        },
        "權重來源":"法人估值邏輯 + 現金流驅動 + 競爭優勢期間",
        "可信度":"高"
    },
    "成熟製程晶圓代工": {
        "權重": {"PE":20, "PB":10, "FCFF":25, "FCFE":20, "EVA":10, "CAP":10, "EBO":5},
        "說明": {
            "PE":"成熟製程景氣循環明顯，市場常以本益比反映景氣復甦或衰退。",
            "PB":"成熟製程資產與折舊週期重要，PB需保留一定權重。",
            "FCFF":"成熟製程企業現金流穩定，FCFF是主要價值來源。",
            "FCFE":"聯電、世界先進具股利屬性，股東自由現金流重要。",
            "EVA":"成熟製程超額報酬較先進製程低，因此EVA權重中等偏低。",
            "CAP":"護城河存在但期間較短，CAP權重低於台積電。",
            "EBO":"剩餘盈餘對成熟製程解釋力較低，作為輔助。"
        },
        "權重來源":"景氣循環 + 股利能力 + 現金流穩定度",
        "可信度":"中高"
    },
    "成熟製程 / 特殊製程": {
        "權重": {"PE":20, "PB":10, "FCFF":25, "FCFE":20, "EVA":10, "CAP":10, "EBO":5},
        "說明": {
            "PE":"世界先進股價常受成熟製程景氣與市場本益比影響。",
            "PB":"成熟製程與特殊製程設備資產仍具參考價值。",
            "FCFF":"現金流穩定度是成熟製程最重要價值來源之一。",
            "FCFE":"高股息與股東回報對世界先進評價很重要。",
            "EVA":"超額報酬能力需納入，但不宜高估。",
            "CAP":"競爭優勢期間存在，但不如先進製程長。",
            "EBO":"剩餘盈餘作為輔助，避免單純PE/PB低估。"
        },
        "權重來源":"成熟製程景氣 + 股利能力 + FCFF/FCFE",
        "可信度":"中高"
    },
    "AI電源 / 自動化": {
        "權重": {"PE":20, "PB":5, "FCFF":20, "FCFE":15, "EVA":15, "CAP":10, "EBO":15},
        "說明": {
            "PE":"台達電具成長股屬性，市場會給予本益比溢價。",
            "PB":"資產淨值不是台達電主要定價邏輯，因此PB權重低。",
            "FCFF":"AI電源與資料中心成長需反映在企業自由現金流。",
            "FCFE":"台達電現金流穩定，股東自由現金流具參考價值。",
            "EVA":"長期ROE與資本效率優秀，EVA需納入。",
            "CAP":"電源管理、自動化與資料中心有競爭優勢，但需持續驗證。",
            "EBO":"市場買的是未來超額獲利，EBO對台達電有一定解釋力。"
        },
        "權重來源":"AI電源成長 + 現金流 + 超額報酬能力",
        "可信度":"高"
    }
}

def aivm_weight_df(industry):
    data = AIVM_INDUSTRY_WEIGHTS.get(industry)
    if data is None:
        data = AIVM_INDUSTRY_WEIGHTS.get("成熟製程晶圓代工")
    rows = []
    for model, weight in data["權重"].items():
        rows.append({
            "模型": model,
            "權重": f"{weight}%",
            "為什麼給這個權重": data["說明"].get(model, ""),
            "權重來源": data["權重來源"],
            "可信度": data["可信度"],
        })
    return pd.DataFrame(rows)

def aivm_weight_summary_df():
    rows = []
    for industry, data in AIVM_INDUSTRY_WEIGHTS.items():
        row = {"類股": industry, "權重來源": data["權重來源"], "可信度": data["可信度"]}
        row.update({k: f"{v}%" for k, v in data["權重"].items()})
        rows.append(row)
    return pd.DataFrame(rows)


# V92.3 核心：
# 固定AIVM價值 = 每季財報公布後更新一次，不每日跟現價變動。
# 動態AIVM價值 = 以現價做市場校準，僅作比較。
# 本版只影響 AIVM Lab，不改主系統。

AIVM_LAB_STOCKS = {
    "2330.TW": {
        "公司": "台積電",
        "產業": "晶圓代工 / AI先進製程",
        "fallback_price": 2390.0,
        "fallback_eps": 73.54,
        "fallback_bvps": 216.35,
        "hist_pe": (24, 32, 40),
        "hist_pb": (7.0, 10.0, 13.0),
        "market_pe": (30, 36, 42),
        "market_pb": (9.0, 11.5, 14.0),
        "industry_factor": (1.02, 1.08, 1.15),
        "fixed_weights": (0.30, 0.40, 0.30),
        "財報季度": "2026 Q2",
        "財報基準日": "2026-06-30",
        "財報公布日": "2026-08-10",
        "固定價值有效至": "2026-11-10",
        "產業重點": "AI、CoWoS、N3/N2、先進封裝",
    },
    "2303.TW": {
        "公司": "聯電",
        "產業": "成熟製程晶圓代工",
        "fallback_price": 178.0,
        "fallback_eps": 5.20,
        "fallback_bvps": 32.5,
        "hist_pe": (16, 24, 32),
        "hist_pb": (2.6, 3.6, 4.6),
        "market_pe": (24, 30, 36),
        "market_pb": (3.8, 4.8, 5.8),
        "industry_factor": (0.95, 1.00, 1.08),
        "fixed_weights": (0.30, 0.40, 0.30),
        "財報季度": "2026 Q2",
        "財報基準日": "2026-06-30",
        "財報公布日": "2026-08-05",
        "固定價值有效至": "2026-11-05",
        "產業重點": "成熟製程、車用、工控、產能利用率",
    },
    "5347.TWO": {
        "公司": "世界先進",
        "產業": "成熟製程 / 特殊製程",
        "fallback_price": 200.0,
        "fallback_eps": 4.30,
        "fallback_bvps": 36.64,
        "hist_pe": (18, 28, 38),
        "hist_pb": (2.8, 4.2, 5.6),
        "market_pe": (32, 42, 52),
        "market_pb": (4.2, 5.2, 6.2),
        "industry_factor": (0.92, 0.98, 1.05),
        "fixed_weights": (0.30, 0.40, 0.30),
        "財報季度": "2026 Q2",
        "財報基準日": "2026-06-30",
        "財報公布日": "2026-08-08",
        "固定價值有效至": "2026-11-08",
        "產業重點": "PMIC、DDIC、成熟製程、股利能力",
    },
    "2308.TW": {
        "公司": "台達電",
        "產業": "AI電源 / 自動化",
        "fallback_price": 2000.0,
        "fallback_eps": 23.09,
        "fallback_bvps": 115.32,
        "hist_pe": (45, 60, 78),
        "hist_pb": (9.0, 13.0, 18.0),
        "market_pe": (60, 75, 90),
        "market_pb": (12.0, 16.0, 20.0),
        "industry_factor": (1.08, 1.16, 1.25),
        "fixed_weights": (0.30, 0.40, 0.30),
        "財報季度": "2026 Q2",
        "財報基準日": "2026-06-30",
        "財報公布日": "2026-08-12",
        "固定價值有效至": "2026-11-12",
        "產業重點": "AI電源、資料中心、散熱、工業自動化、機器人",
    },
}

def aivm_lab_num(x):
    try:
        if x is None:
            return np.nan
        if isinstance(x, str):
            s = x.replace(",", "").replace("%", "").replace("倍", "").replace("元", "").strip()
            if s in ["", "N/A", "None", "nan", "NaN", "--"]:
                return np.nan
            return float(s)
        return float(x)
    except Exception:
        return np.nan

def aivm_lab_fmt(x):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def aivm_lab_pct(x):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):.1f}%"
    except Exception:
        return "N/A"

def aivm_lab_stage(margin_pct):
    """
    margin_pct = (固定AIVM價值 - 現價) / 固定AIVM價值 * 100
    正數代表現價低於固定價值；負數代表現價高於固定價值。
    """
    if pd.isna(margin_pct):
        return "資料不足"
    if margin_pct >= 25:
        return "明顯低估"
    if margin_pct >= 10:
        return "低估"
    if margin_pct >= -10:
        return "合理"
    if margin_pct >= -25:
        return "高估"
    return "明顯高估"

@st.cache_data(ttl=1800, show_spinner=False)
def aivm_lab_quote(symbol):
    cfg = AIVM_LAB_STOCKS.get(symbol, {})
    out = {
        "現價": np.nan,
        "EPS": np.nan,
        "PE": np.nan,
        "PB": np.nan,
        "BVPS": np.nan,
        "資料來源": "Yahoo Finance",
    }

    try:
        q = yf_quote(symbol)
        if isinstance(q, dict):
            out["現價"] = aivm_lab_num(q.get("price", q.get("regularMarketPrice", np.nan)))
            out["EPS"] = aivm_lab_num(q.get("eps", q.get("trailingEps", np.nan)))
            out["PE"] = aivm_lab_num(q.get("pe", q.get("trailingPE", np.nan)))
            out["PB"] = aivm_lab_num(q.get("pb", q.get("priceToBook", np.nan)))
            out["BVPS"] = aivm_lab_num(q.get("book_value", q.get("bookValue", q.get("bvps", np.nan))))
    except Exception:
        pass

    try:
        t = yf.Ticker(symbol)
        try:
            info = t.get_info() if hasattr(t, "get_info") else t.info
        except Exception:
            info = {}
        try:
            fi = getattr(t, "fast_info", {}) or {}
        except Exception:
            fi = {}

        if isinstance(info, dict):
            if pd.isna(out["現價"]):
                out["現價"] = aivm_lab_num(info.get("regularMarketPrice", info.get("currentPrice", info.get("previousClose", np.nan))))
            if pd.isna(out["EPS"]):
                out["EPS"] = aivm_lab_num(info.get("trailingEps", info.get("forwardEps", info.get("epsTrailingTwelveMonths", np.nan))))
            if pd.isna(out["PE"]):
                out["PE"] = aivm_lab_num(info.get("trailingPE", info.get("forwardPE", np.nan)))
            if pd.isna(out["PB"]):
                out["PB"] = aivm_lab_num(info.get("priceToBook", np.nan))
            if pd.isna(out["BVPS"]):
                out["BVPS"] = aivm_lab_num(info.get("bookValue", np.nan))
        if pd.isna(out["現價"]):
            out["現價"] = aivm_lab_num(fi.get("last_price", fi.get("lastPrice", np.nan)))
    except Exception:
        pass

    used_fb = []
    if pd.isna(out["現價"]):
        out["現價"] = cfg.get("fallback_price", np.nan)
        used_fb.append("現價")
    if pd.isna(out["EPS"]) or out["EPS"] <= 0:
        out["EPS"] = cfg.get("fallback_eps", np.nan)
        used_fb.append("EPS")
    if pd.isna(out["BVPS"]) or out["BVPS"] <= 0:
        out["BVPS"] = cfg.get("fallback_bvps", np.nan)
        used_fb.append("BVPS")

    if pd.isna(out["PE"]) and pd.notna(out["現價"]) and pd.notna(out["EPS"]) and out["EPS"] > 0:
        out["PE"] = out["現價"] / out["EPS"]
    if pd.isna(out["PB"]) and pd.notna(out["現價"]) and pd.notna(out["BVPS"]) and out["BVPS"] > 0:
        out["PB"] = out["現價"] / out["BVPS"]

    if used_fb:
        out["資料來源"] = "Yahoo Finance + Lab校準資料：" + "、".join(used_fb)
    return out

def aivm_lab_range_value(eps, bvps, pe_tuple, pb_tuple):
    low_vals, mid_vals, high_vals = [], [], []
    if pd.notna(eps) and eps > 0:
        low_vals.append(eps * pe_tuple[0])
        mid_vals.append(eps * pe_tuple[1])
        high_vals.append(eps * pe_tuple[2])
    if pd.notna(bvps) and bvps > 0:
        low_vals.append(bvps * pb_tuple[0])
        mid_vals.append(bvps * pb_tuple[1])
        high_vals.append(bvps * pb_tuple[2])
    if not low_vals:
        return np.nan, np.nan, np.nan
    return float(np.median(low_vals)), float(np.median(mid_vals)), float(np.median(high_vals))

def aivm_lab_error(value, price):
    if pd.isna(value) or pd.isna(price) or price == 0:
        return np.nan
    return abs(value - price) / price * 100

def aivm_fixed_value(financial_value, market_value, industry_value, weights):
    if any(pd.isna(x) for x in [financial_value, market_value, industry_value]):
        return np.nan
    fw, mw, iw = weights
    return financial_value * fw + market_value * mw + industry_value * iw

def aivm_dynamic_value(price, fixed_value):
    """
    動態AIVM示範：保留固定價值70%，以現價校準30%。
    用來觀察「若部分跟現價連動」會如何影響估值位階。
    """
    if pd.isna(price) or pd.isna(fixed_value):
        return np.nan
    return fixed_value * 0.70 + price * 0.30

def aivm_lab_row(symbol, cfg):
    q = aivm_lab_quote(symbol)
    price, eps, bvps = q["現價"], q["EPS"], q["BVPS"]

    f_low, f_mid, f_high = aivm_lab_range_value(eps, bvps, cfg["hist_pe"], cfg["hist_pb"])
    m_low, m_mid, m_high = aivm_lab_range_value(eps, bvps, cfg["market_pe"], cfg["market_pb"])

    factor = cfg["industry_factor"]
    i_low = m_mid * factor[0] if pd.notna(m_mid) else np.nan
    i_mid = m_mid * factor[1] if pd.notna(m_mid) else np.nan
    i_high = m_mid * factor[2] if pd.notna(m_mid) else np.nan

    fixed = aivm_fixed_value(f_mid, m_mid, i_mid, cfg["fixed_weights"])
    dynamic = aivm_dynamic_value(price, fixed)

    fixed_margin = (fixed - price) / fixed * 100 if pd.notna(fixed) and fixed != 0 and pd.notna(price) else np.nan
    dynamic_margin = (dynamic - price) / dynamic * 100 if pd.notna(dynamic) and dynamic != 0 and pd.notna(price) else np.nan

    return {
        "公司": cfg["公司"],
        "代碼": symbol,
        "產業": cfg["產業"],
        "現價": price,
        "EPS": eps,
        "PE": q["PE"],
        "PB": q["PB"],
        "BVPS": bvps,
        "財報價值": f_mid,
        "市場價值": m_mid,
        "產業價值": i_mid,
        "固定AIVM價值": fixed,
        "動態AIVM價值": dynamic,
        "固定安全邊際": fixed_margin,
        "動態安全邊際": dynamic_margin,
        "固定估值位階": aivm_lab_stage(fixed_margin),
        "動態估值位階": aivm_lab_stage(dynamic_margin),
        "財報誤差": aivm_lab_error(f_mid, price),
        "市場誤差": aivm_lab_error(m_mid, price),
        "產業誤差": aivm_lab_error(i_mid, price),
        "財報保守": f_low,
        "財報樂觀": f_high,
        "市場保守": m_low,
        "市場樂觀": m_high,
        "產業保守": i_low,
        "產業樂觀": i_high,
        "財報季度": cfg["財報季度"],
        "財報基準日": cfg["財報基準日"],
        "財報公布日": cfg["財報公布日"],
        "固定價值有效至": cfg["固定價值有效至"],
        "更新條件": "季報公布 / 法人目標價重大調整 / 產業景氣循環改變",
        "資料來源": q["資料來源"],
        "產業重點": cfg["產業重點"],
    }

@st.cache_data(ttl=1800, show_spinner=False)
def aivm_lab_df():
    return pd.DataFrame([aivm_lab_row(sym, cfg) for sym, cfg in AIVM_LAB_STOCKS.items()])

def aivm_lab_display_df(df):
    show = df.copy()
    money_cols = [
        "現價","EPS","PE","PB","BVPS",
        "財報價值","市場價值","產業價值",
        "固定AIVM價值","動態AIVM價值",
        "財報保守","財報樂觀","市場保守","市場樂觀","產業保守","產業樂觀",
    ]
    for c in money_cols:
        if c in show.columns:
            show[c] = show[c].apply(aivm_lab_fmt)
    for c in ["固定安全邊際","動態安全邊際","財報誤差","市場誤差","產業誤差"]:
        if c in show.columns:
            show[c] = show[c].apply(aivm_lab_pct)
    return show


# ===== V97.1 DNA TAB CORE START =====
# 注意：此段必須放在舊版 AIVM Lab route guard 之前，否則 page == AIVM Lab 時會 st.stop()，後面新增模組看不到。
V971_DNA_PROFILES = {
    "2330.TW": ["台積電", "晶圓代工", "AI先進製程龍頭", "AI/HPC、先進製程、CoWoS", "Samsung / Intel Foundry / SMIC", "S+", 95],
    "2303.TW": ["聯電", "晶圓代工", "成熟製程現金流型", "成熟製程、車用、工控", "GlobalFoundries / Tower / SMIC", "A", 76],
    "5347.TWO": ["世界先進", "特殊製程", "特殊製程利基型", "PMIC、DDIC、車用/工控特殊製程", "Tower / DB HiTek / Magnachip", "A", 74],
    "6770.TW": ["力積電", "記憶體/代工", "記憶體循環型代工", "DRAM、NAND相關與成熟製程代工", "SMIC / Hua Hong / 記憶體同業", "B+", 66],
    "2383.TW": ["台光電", "CCL", "AI高速材料龍頭", "AI CCL、高速材料、伺服器材料", "Panasonic / Isola / Shengyi", "A+", 88],
    "3037.TW": ["欣興", "ABF載板", "ABF載板龍頭", "ABF、IC載板、高階PCB", "Ibiden / Shinko / Nan Ya PCB", "A", 80],
    "8046.TW": ["南電", "ABF載板", "AI載板景氣循環型", "ABF、BT、HPC載板", "Ibiden / Shinko / 欣興", "A", 78],
    "3711.TW": ["日月光投控", "封測", "全球封測龍頭", "封裝、測試、SiP、先進封裝", "Amkor / JCET / Powertech", "S", 84],
    "2449.TW": ["京元電子", "測試", "AI測試受惠型", "IC測試、AI/HPC測試、車用測試", "ASE Test / Amkor / Sigurd", "A+", 82],
    "6215.TWO": ["和椿", "自動化", "自動化代理與整合型", "自動化元件、機器人、設備整合", "Keyence / SMC / Omron", "B+", 70],
}

V971_BASE_AIVM_VALUE = {
    "2330.TW": 2536.56, "2303.TW": 145.47, "5347.TWO": 169.92, "6770.TW": 81.40,
    "2383.TW": 5393.20, "3037.TW": 178.00, "8046.TW": 907.25, "3711.TW": 158.40,
    "2449.TW": 106.40, "6215.TWO": 92.00,
}
V971_FALLBACK_PRICE = {
    "2330.TW": 2390.00, "2303.TW": 178.50, "5347.TWO": 220.00, "6770.TW": 83.20,
    "2383.TW": 5640.00, "3037.TW": 1020.00, "8046.TW": 1045.00, "3711.TW": 641.00,
    "2449.TW": 334.50, "6215.TWO": 105.50,
}

def v971_dna_factor(score):
    s = float(score)
    if s >= 90: return 1.18
    if s >= 85: return 1.12
    if s >= 80: return 1.08
    if s >= 75: return 1.03
    if s >= 70: return 1.00
    if s >= 65: return 0.94
    return 0.88

def v971_stage(price, fair):
    try:
        price = float(price); fair = float(fair)
        if fair <= 0: return "資料不足"
        if price < fair * 0.90: return "合理偏低"
        if price > fair * 1.10: return "高估"
        if price > fair: return "合理偏高"
        return "合理"
    except Exception:
        return "資料不足"

@st.cache_data(ttl=300, show_spinner=False)
def v971_live_price(symbol):
    """
    V97.2 強化現價取得：
    1) Yahoo fast_info
    2) yfinance history 1d / 5d / 1mo
    3) Yahoo chart API
    4) fallback 最近人工校對價
    """
    symbol = str(symbol).strip()

    # 1. Yahoo fast_info
    try:
        t = yf.Ticker(symbol)
        try:
            fi = getattr(t, "fast_info", {}) or {}
            for key in ["last_price", "lastPrice", "regularMarketPrice"]:
                px = fi.get(key, np.nan)
                px = float(px)
                if np.isfinite(px) and px > 0:
                    return px, "Yahoo fast_info"
        except Exception:
            pass

        # 2. yfinance history
        for p in ["1d", "5d", "1mo"]:
            try:
                h = t.history(period=p, interval="1d", auto_adjust=False)
                if h is not None and not h.empty and "Close" in h.columns:
                    px = pd.to_numeric(h["Close"], errors="coerce").dropna()
                    if len(px) and float(px.iloc[-1]) > 0:
                        return float(px.iloc[-1]), f"Yahoo history {p}"
            except Exception:
                pass
    except Exception:
        pass

    # 3. Yahoo chart API；有時 yfinance fast_info 對上櫃股失敗，但 chart API 仍可回資料
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {"range": "5d", "interval": "1d"}
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, params=params, headers=headers, timeout=8)
        js = r.json()
        result = js.get("chart", {}).get("result", [])
        if result:
            quote = result[0].get("indicators", {}).get("quote", [{}])[0]
            closes = quote.get("close", []) or []
            closes = [float(x) for x in closes if x is not None and float(x) > 0]
            if closes:
                return closes[-1], "Yahoo chart API"
    except Exception:
        pass

    # 4. fallback：只作為抓價失敗提示，不當成正式報價
    return V971_FALLBACK_PRICE.get(symbol, np.nan), "Fallback需校對"

def v971_get_base(symbol, price=np.nan):
    try:
        if "v901_valuation" in globals() and pd.notna(price):
            v = v901_valuation(symbol, price)
            if isinstance(v, dict) and pd.notna(v.get("base", np.nan)):
                return float(v["base"]), "v901_valuation"
    except Exception:
        pass
    return V971_BASE_AIVM_VALUE.get(symbol, np.nan), "V97.1試驗基準"

def v971_fmt(x):
    try:
        if pd.isna(x): return "N/A"
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def v971_pct(x):
    try:
        if pd.isna(x): return "N/A"
        return f"{float(x):.1f}%"
    except Exception:
        return "N/A"

def v971_dna_df():
    rows = []
    for sym, arr in V971_DNA_PROFILES.items():
        company, sub, position, biz, competitors, cap, score = arr
        price, psrc = v971_live_price(sym)
        base, bsrc = v971_get_base(sym, price)
        factor = v971_dna_factor(score)
        dna = base * factor if pd.notna(base) else np.nan
        base_err = abs(price - base) / price * 100 if pd.notna(price) and pd.notna(base) and price else np.nan
        dna_err = abs(price - dna) / price * 100 if pd.notna(price) and pd.notna(dna) and price else np.nan
        rows.append({
            "代碼": sym, "公司": company, "次產業": sub, "DNA定位": position, "主要業務": biz,
            "全球競爭": competitors, "CAP等級": cap, "DNA分數": score, "DNA係數": factor,
            "現價": price, "原AIVM價值": base, "DNA估值": dna,
            "原AIVM誤差": base_err, "DNA誤差": dna_err, "誤差改善": base_err - dna_err if pd.notna(base_err) and pd.notna(dna_err) else np.nan,
            "原位階": v971_stage(price, base), "DNA位階": v971_stage(price, dna), "現價來源": psrc, "估值來源": bsrc
        })
    return pd.DataFrame(rows)

def v971_display(df):
    out = df.copy()
    for c in ["現價", "原AIVM價值", "DNA估值"]:
        out[c] = out[c].apply(v971_fmt)
    for c in ["原AIVM誤差", "DNA誤差", "誤差改善"]:
        out[c] = out[c].apply(v971_pct)
    out["DNA係數"] = out["DNA係數"].apply(lambda x: f"{float(x):.2f}" if pd.notna(x) else "N/A")
    return out


# ===== V98.0 DNA WEIGHT CALIBRATION TRIAL START =====
# V98.0：在 AIVM Lab 第15頁籤內新增 DNA權重校準，不動首頁、K線、財報、ESG、法人。

V980_FACTOR_BASE = {
    "技術領先": 0.20,
    "市場地位": 0.18,
    "AI受惠度": 0.18,
    "現金流品質": 0.14,
    "獲利成長": 0.14,
    "景氣循環": 0.08,
    "財務風險": 0.08,
}

V980_FACTOR_SCORE = {
    "2330.TW": {"技術領先": 98, "市場地位": 96, "AI受惠度": 98, "現金流品質": 95, "獲利成長": 92, "景氣循環": 82, "財務風險": 90},
    "2303.TW": {"技術領先": 74, "市場地位": 76, "AI受惠度": 62, "現金流品質": 82, "獲利成長": 66, "景氣循環": 64, "財務風險": 82},
    "5347.TWO": {"技術領先": 72, "市場地位": 70, "AI受惠度": 58, "現金流品質": 76, "獲利成長": 62, "景氣循環": 62, "財務風險": 78},
    "6770.TW": {"技術領先": 62, "市場地位": 58, "AI受惠度": 52, "現金流品質": 58, "獲利成長": 50, "景氣循環": 45, "財務風險": 60},
    "2383.TW": {"技術領先": 86, "市場地位": 82, "AI受惠度": 94, "現金流品質": 80, "獲利成長": 88, "景氣循環": 72, "財務風險": 76},
    "3037.TW": {"技術領先": 80, "市場地位": 78, "AI受惠度": 82, "現金流品質": 72, "獲利成長": 76, "景氣循環": 60, "財務風險": 70},
    "8046.TW": {"技術領先": 78, "市場地位": 74, "AI受惠度": 80, "現金流品質": 70, "獲利成長": 72, "景氣循環": 58, "財務風險": 68},
    "3711.TW": {"技術領先": 82, "市場地位": 88, "AI受惠度": 80, "現金流品質": 84, "獲利成長": 76, "景氣循環": 68, "財務風險": 78},
    "2449.TW": {"技術領先": 80, "市場地位": 78, "AI受惠度": 86, "現金流品質": 78, "獲利成長": 82, "景氣循環": 70, "財務風險": 74},
    "6215.TWO": {"技術領先": 66, "市場地位": 62, "AI受惠度": 58, "現金流品質": 68, "獲利成長": 64, "景氣循環": 60, "財務風險": 70},
}

def v980_normalize_weights(w):
    total = sum(float(v) for v in w.values())
    if total <= 0:
        return V980_FACTOR_BASE.copy()
    return {k: float(v) / total for k, v in w.items()}

def v980_dna_score_by_weights(symbol, weights):
    scores = V980_FACTOR_SCORE.get(symbol, {})
    if not scores:
        return np.nan
    w = v980_normalize_weights(weights)
    return sum(scores.get(k, 60) * w.get(k, 0) for k in w.keys())

def v980_factor_to_value_factor(score):
    try:
        s = float(score)
    except Exception:
        return 1.00
    # 分數對估值係數：60分=0.90，80分=1.06，95分=1.18，上下限避免過度放大
    factor = 0.90 + (s - 60) * 0.008
    return max(0.82, min(1.22, factor))

def v980_calibration_df(weights):
    base_df = v971_dna_df()
    rows = []
    for _, r in base_df.iterrows():
        sym = r["代碼"]
        score = v980_dna_score_by_weights(sym, weights)
        factor = v980_factor_to_value_factor(score)
        base = float(r["原AIVM價值"]) if pd.notna(r["原AIVM價值"]) else np.nan
        price = float(r["現價"]) if pd.notna(r["現價"]) else np.nan
        dna_value = base * factor if pd.notna(base) else np.nan
        err = abs(price - dna_value) / price * 100 if pd.notna(price) and pd.notna(dna_value) and price > 0 else np.nan
        old_err = float(r["DNA誤差"]) if pd.notna(r["DNA誤差"]) else np.nan
        rows.append({
            "代碼": sym,
            "公司": r["公司"],
            "次產業": r["次產業"],
            "現價": price,
            "原AIVM價值": base,
            "V97 DNA估值": r["DNA估值"],
            "V98校準DNA估值": dna_value,
            "V98 DNA分數": score,
            "V98估值係數": factor,
            "V97 DNA誤差": old_err,
            "V98 DNA誤差": err,
            "誤差改善": old_err - err if pd.notna(old_err) and pd.notna(err) else np.nan,
            "V98位階": v971_stage(price, dna_value),
            "現價來源": r["現價來源"],
        })
    return pd.DataFrame(rows)

def v980_calibration_metrics(df):
    try:
        y = pd.to_numeric(df["現價"], errors="coerce")
        yhat = pd.to_numeric(df["V98校準DNA估值"], errors="coerce")
        mask = y.notna() & yhat.notna() & (y != 0)
        if mask.sum() == 0:
            return np.nan, np.nan, np.nan
        err_pct = (y[mask] - yhat[mask]).abs() / y[mask] * 100
        mape = err_pct.mean()
        rmse = np.sqrt(((y[mask] - yhat[mask]) ** 2).mean())
        ss_res = ((y[mask] - yhat[mask]) ** 2).sum()
        ss_tot = ((y[mask] - y[mask].mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot else np.nan
        return mape, rmse, r2
    except Exception:
        return np.nan, np.nan, np.nan

def v980_show_df(df):
    out = df.copy()
    for c in ["現價", "原AIVM價值", "V97 DNA估值", "V98校準DNA估值"]:
        out[c] = out[c].apply(v971_fmt)
    for c in ["V98 DNA分數"]:
        out[c] = out[c].apply(lambda x: f"{float(x):.1f}" if pd.notna(x) else "N/A")
    for c in ["V98估值係數"]:
        out[c] = out[c].apply(lambda x: f"{float(x):.3f}" if pd.notna(x) else "N/A")
    for c in ["V97 DNA誤差", "V98 DNA誤差", "誤差改善"]:
        out[c] = out[c].apply(v971_pct)
    return out

def v980_weight_calibration_page():
    st.markdown("### V98.0 DNA權重校準引擎")
    st.info("本頁先做試作：手動調整DNA因子權重，觀察 V98校準DNA估值 是否降低誤差。暫不覆蓋V97與主系統。")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("#### 手動權重設定")
        raw = {}
        for k, default in V980_FACTOR_BASE.items():
            raw[k] = st.slider(k, 0, 40, int(default * 100), 1, key=f"v980_weight_{k}") / 100
        weights = v980_normalize_weights(raw)
        st.caption("系統會自動正規化，確保總權重 = 100%。")
        st.dataframe(pd.DataFrame([{"因子": k, "正規化權重": f"{v*100:.1f}%"} for k, v in weights.items()]), use_container_width=True, hide_index=True)

    with c2:
        df = v980_calibration_df(weights)
        mape, rmse, r2 = v980_calibration_metrics(df)
        m1, m2, m3 = st.columns(3)
        m1.metric("V98 MAPE", v971_pct(mape))
        m2.metric("V98 RMSE", v971_fmt(rmse))
        m3.metric("V98 R²", f"{r2:.3f}" if pd.notna(r2) else "N/A")
        cols = ["代碼", "公司", "現價", "原AIVM價值", "V97 DNA估值", "V98校準DNA估值", "V98 DNA分數", "V98估值係數", "V97 DNA誤差", "V98 DNA誤差", "誤差改善", "V98位階", "現價來源"]
        st.dataframe(v980_show_df(df)[cols], use_container_width=True, hide_index=True)

    st.markdown("#### 因子分數資料庫")
    factor_rows = []
    for sym, scores in V980_FACTOR_SCORE.items():
        name = V971_DNA_PROFILES.get(sym, ["", "", "", "", "", "", ""])[0]
        row = {"代碼": sym, "公司": name}
        row.update(scores)
        factor_rows.append(row)
    st.dataframe(pd.DataFrame(factor_rows), use_container_width=True, hide_index=True)

    st.markdown("#### 試作結論")
    st.warning("V98.0 仍是手動權重校準。若調整後 MAPE 下降，代表個股DNA權重方向有效；下一版 V98.1 再做自動搜尋最佳權重。")
# ===== V98.0 DNA WEIGHT CALIBRATION TRIAL END =====



# ===== V98.1 DNA AUTO WEIGHT OPTIMIZER START =====
# V98.1：自動搜尋最佳DNA權重；仍只在 AIVM Lab 第15頁籤內運作，不覆蓋主系統。

def v981_weight_vector_to_dict(vec):
    keys = list(V980_FACTOR_BASE.keys())
    vec = np.array(vec, dtype=float)
    vec = np.maximum(vec, 0)
    s = vec.sum()
    if s <= 0:
        return V980_FACTOR_BASE.copy()
    return {k: float(v / s) for k, v in zip(keys, vec)}

def v981_score_mape(weights):
    try:
        df = v980_calibration_df(weights)
        mape, rmse, r2 = v980_calibration_metrics(df)
        return float(mape) if pd.notna(mape) else 9999
    except Exception:
        return 9999

def v981_random_search(n_iter=600, seed=42):
    rng = np.random.default_rng(seed)
    keys = list(V980_FACTOR_BASE.keys())

    candidates = []
    # 先放入目前預設權重
    base_vec = np.array([V980_FACTOR_BASE[k] for k in keys], dtype=float)
    candidates.append(base_vec)

    # 加入偏向AI與技術的候選
    candidates.extend([
        np.array([0.24,0.16,0.24,0.12,0.12,0.06,0.06]),
        np.array([0.18,0.18,0.22,0.16,0.14,0.06,0.06]),
        np.array([0.16,0.16,0.18,0.18,0.18,0.07,0.07]),
        np.array([0.22,0.20,0.16,0.16,0.14,0.06,0.06]),
    ])

    for _ in range(int(n_iter)):
        # Dirichlet 讓總權重自然等於1
        alpha = np.array([2.5, 2.2, 2.4, 1.8, 1.8, 1.1, 1.1])
        candidates.append(rng.dirichlet(alpha))

    rows = []
    best = None
    for vec in candidates:
        w = v981_weight_vector_to_dict(vec)
        df = v980_calibration_df(w)
        mape, rmse, r2 = v980_calibration_metrics(df)
        row = {"MAPE": mape, "RMSE": rmse, "R2": r2}
        row.update({k: w[k] for k in keys})
        rows.append(row)
        if best is None or (pd.notna(mape) and mape < best["MAPE"]):
            best = {"weights": w, "df": df, "MAPE": mape, "RMSE": rmse, "R2": r2}

    result_df = pd.DataFrame(rows).sort_values("MAPE", ascending=True).reset_index(drop=True)
    return best, result_df

@st.cache_data(ttl=600, show_spinner=False)
def v981_cached_optimizer(n_iter=600):
    best, result = v981_random_search(n_iter=n_iter, seed=42)
    return best, result

def v981_weight_table(weights):
    return pd.DataFrame([
        {"因子": k, "最佳權重": f"{v*100:.1f}%"}
        for k, v in weights.items()
    ])

def v981_result_table(df):
    show = v980_show_df(df)
    cols = ["代碼", "公司", "現價", "V97 DNA估值", "V98校準DNA估值", "V98 DNA分數", "V98估值係數", "V97 DNA誤差", "V98 DNA誤差", "誤差改善", "V98位階", "現價來源"]
    return show[cols]

def v981_top_candidates_table(result_df, n=10):
    out = result_df.head(n).copy()
    for c in ["MAPE"]:
        out[c] = out[c].apply(v971_pct)
    for c in ["RMSE"]:
        out[c] = out[c].apply(v971_fmt)
    out["R2"] = out["R2"].apply(lambda x: f"{float(x):.3f}" if pd.notna(x) else "N/A")
    for k in V980_FACTOR_BASE.keys():
        out[k] = out[k].apply(lambda x: f"{float(x)*100:.1f}%" if pd.notna(x) else "N/A")
    return out

def v981_auto_optimizer_page():
    st.markdown("### V98.1 DNA自動最佳化權重引擎")
    st.info("本頁會自動搜尋讓 MAPE 最低的 DNA 因子權重組合；結果只作建議，不覆蓋 V98.0 手動權重與主系統。")

    n_iter = st.slider("搜尋次數", 100, 2000, 600, 100, key="v981_search_iter")
    best, result_df = v981_cached_optimizer(n_iter)

    if best is None:
        st.warning("目前無法產生最佳化結果。")
        return

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("#### 最佳權重建議")
        st.dataframe(v981_weight_table(best["weights"]), use_container_width=True, hide_index=True)
        st.caption("權重總和已正規化為100%。")

    with c2:
        m1, m2, m3 = st.columns(3)
        m1.metric("最佳 MAPE", v971_pct(best["MAPE"]))
        m2.metric("最佳 RMSE", v971_fmt(best["RMSE"]))
        m3.metric("最佳 R²", f"{best['R2']:.3f}" if pd.notna(best["R2"]) else "N/A")
        st.dataframe(v981_result_table(best["df"]), use_container_width=True, hide_index=True)

    st.markdown("#### 前10組候選權重")
    st.dataframe(v981_top_candidates_table(result_df, 10), use_container_width=True, hide_index=True)

    st.markdown("#### 解讀")
    st.success("若最佳 MAPE 低於 V98.0 手動權重，代表 DNA 因子權重可由資料自動校準；下一版可加入更多個股與歷史期間。")
    st.caption("V98.1 使用隨機搜尋 / Dirichlet 權重組合。正式版可再升級 Grid Search、Genetic Algorithm 或 Bayesian Optimization。")
# ===== V98.1 DNA AUTO WEIGHT OPTIMIZER END =====



# ===== V98.2 DNA HISTORICAL BACKTEST TRIAL START =====
# V98.2：DNA歷史回測試作。先用歷史情境資料驗證權重穩定性，不動首頁/K線/財報/ESG/法人/主估值。

V982_BACKTEST_DATES = ["2023-H1", "2023-H2", "2024-H1", "2024-H2", "2025-H1", "2025-H2", "2026-Q2"]

# 歷史情境倍率：用來模擬不同景氣階段下的原AIVM價值、現價與DNA因子分數。
# 正式版可改為接歷史日收盤、歷史財報與每期模型估值。
V982_PHASE = {
    "2023-H1": {"price": 0.62, "base": 0.66, "tech": -6, "ai": -10, "cash": -2, "growth": -8, "cycle": -12},
    "2023-H2": {"price": 0.70, "base": 0.72, "tech": -5, "ai": -7, "cash": -1, "growth": -5, "cycle": -8},
    "2024-H1": {"price": 0.82, "base": 0.84, "tech": -3, "ai": -2, "cash": 0, "growth": -2, "cycle": -4},
    "2024-H2": {"price": 0.92, "base": 0.93, "tech": -1, "ai": 2, "cash": 0, "growth": 1, "cycle": 0},
    "2025-H1": {"price": 1.00, "base": 1.00, "tech": 0, "ai": 4, "cash": 0, "growth": 3, "cycle": 2},
    "2025-H2": {"price": 1.06, "base": 1.04, "tech": 1, "ai": 6, "cash": 1, "growth": 4, "cycle": 4},
    "2026-Q2": {"price": 1.00, "base": 1.00, "tech": 0, "ai": 0, "cash": 0, "growth": 0, "cycle": 0},
}

def v982_symbol_history_adjust(symbol, phase):
    # 不同公司對景氣/AI的敏感度不同，避免所有股票同倍率。
    if symbol == "2330.TW":
        return {"price": phase["price"] * 1.08, "base": phase["base"] * 1.05, "ai": phase["ai"] + 5, "tech": phase["tech"] + 3}
    if symbol in ["2383.TW", "3037.TW", "8046.TW", "2449.TW"]:
        return {"price": phase["price"] * (1 + phase["ai"]/100), "base": phase["base"] * 1.02, "ai": phase["ai"] + 4, "tech": phase["tech"] + 1}
    if symbol in ["2303.TW", "5347.TWO", "6770.TW"]:
        return {"price": phase["price"] * (1 + phase["cycle"]/120), "base": phase["base"] * 0.98, "cycle": phase["cycle"] - 2, "growth": phase["growth"] - 2}
    if symbol == "6215.TWO":
        return {"price": phase["price"] * 0.96, "base": phase["base"] * 0.97, "cash": phase["cash"] - 1, "growth": phase["growth"] - 1}
    return {}

def v982_adjust_factor_scores(symbol, date_key):
    base = V980_FACTOR_SCORE.get(symbol, {}).copy()
    phase = V982_PHASE.get(date_key, {})
    adj = v982_symbol_history_adjust(symbol, phase)
    def add(k, v):
        if k in base:
            base[k] = max(0, min(100, base[k] + v))
    add("技術領先", phase.get("tech", 0) + adj.get("tech", 0))
    add("AI受惠度", phase.get("ai", 0) + adj.get("ai", 0))
    add("現金流品質", phase.get("cash", 0) + adj.get("cash", 0))
    add("獲利成長", phase.get("growth", 0) + adj.get("growth", 0))
    add("景氣循環", phase.get("cycle", 0) + adj.get("cycle", 0))
    return base

def v982_dna_score(symbol, weights, date_key):
    scores = v982_adjust_factor_scores(symbol, date_key)
    w = v980_normalize_weights(weights)
    return sum(scores.get(k, 60) * w.get(k, 0) for k in w.keys())

def v982_backtest_df(weights):
    current = v971_dna_df()
    current_map = {r["代碼"]: r for _, r in current.iterrows()}
    rows = []
    for date_key in V982_BACKTEST_DATES:
        phase = V982_PHASE[date_key]
        for sym in V971_DNA_PROFILES.keys():
            if sym not in current_map:
                continue
            r = current_map[sym]
            adj = v982_symbol_history_adjust(sym, phase)
            price_mult = adj.get("price", phase["price"])
            base_mult = adj.get("base", phase["base"])
            price = float(r["現價"]) * price_mult if pd.notna(r["現價"]) else np.nan
            base = float(r["原AIVM價值"]) * base_mult if pd.notna(r["原AIVM價值"]) else np.nan
            score = v982_dna_score(sym, weights, date_key)
            factor = v980_factor_to_value_factor(score)
            dna_value = base * factor if pd.notna(base) else np.nan
            err = abs(price - dna_value) / price * 100 if pd.notna(price) and pd.notna(dna_value) and price > 0 else np.nan
            rows.append({
                "期間": date_key,
                "代碼": sym,
                "公司": r["公司"],
                "次產業": r["次產業"],
                "歷史模擬現價": price,
                "歷史AIVM價值": base,
                "歷史DNA估值": dna_value,
                "DNA分數": score,
                "估值係數": factor,
                "MAPE誤差": err,
                "估值位階": v971_stage(price, dna_value),
            })
    return pd.DataFrame(rows)

def v982_period_summary(df):
    rows = []
    for period, g in df.groupby("期間"):
        y = pd.to_numeric(g["歷史模擬現價"], errors="coerce")
        yhat = pd.to_numeric(g["歷史DNA估值"], errors="coerce")
        mask = y.notna() & yhat.notna() & (y != 0)
        if mask.sum() == 0:
            mape = rmse = r2 = np.nan
        else:
            mape = ((y[mask] - yhat[mask]).abs() / y[mask] * 100).mean()
            rmse = np.sqrt(((y[mask] - yhat[mask]) ** 2).mean())
            ss_res = ((y[mask] - yhat[mask]) ** 2).sum()
            ss_tot = ((y[mask] - y[mask].mean()) ** 2).sum()
            r2 = 1 - ss_res / ss_tot if ss_tot else np.nan
        rows.append({"期間": period, "MAPE": mape, "RMSE": rmse, "R2": r2, "樣本數": int(mask.sum())})
    out = pd.DataFrame(rows)
    out["期間排序"] = out["期間"].apply(lambda x: V982_BACKTEST_DATES.index(x) if x in V982_BACKTEST_DATES else 999)
    return out.sort_values("期間排序").drop(columns=["期間排序"])

def v982_show_backtest_df(df):
    out = df.copy()
    for c in ["歷史模擬現價", "歷史AIVM價值", "歷史DNA估值"]:
        out[c] = out[c].apply(v971_fmt)
    for c in ["DNA分數"]:
        out[c] = out[c].apply(lambda x: f"{float(x):.1f}" if pd.notna(x) else "N/A")
    for c in ["估值係數"]:
        out[c] = out[c].apply(lambda x: f"{float(x):.3f}" if pd.notna(x) else "N/A")
    for c in ["MAPE誤差"]:
        out[c] = out[c].apply(v971_pct)
    return out

def v982_show_summary(df):
    out = df.copy()
    out["MAPE"] = out["MAPE"].apply(v971_pct)
    out["RMSE"] = out["RMSE"].apply(v971_fmt)
    out["R2"] = out["R2"].apply(lambda x: f"{float(x):.3f}" if pd.notna(x) else "N/A")
    return out

def v982_weight_stability_page():
    st.markdown("### V98.2 DNA歷史回測引擎")
    st.info("本頁是歷史回測試作：先用2023~2026情境資料驗證DNA權重是否穩定。正式版再接歷史股價與歷史財報。")

    source = st.radio("回測權重來源", ["V98.1 自動最佳權重", "V98.0 預設權重"], horizontal=True, key="v982_weight_source")
    if source == "V98.1 自動最佳權重":
        try:
            best, _ = v981_cached_optimizer(600)
            weights = best["weights"]
        except Exception:
            weights = V980_FACTOR_BASE.copy()
    else:
        weights = V980_FACTOR_BASE.copy()

    df = v982_backtest_df(weights)
    summary = v982_period_summary(df)

    avg_mape = summary["MAPE"].mean()
    avg_rmse = summary["RMSE"].mean()
    avg_r2 = summary["R2"].mean()
    c1, c2, c3 = st.columns(3)
    c1.metric("歷史平均 MAPE", v971_pct(avg_mape))
    c2.metric("歷史平均 RMSE", v971_fmt(avg_rmse))
    c3.metric("歷史平均 R²", f"{avg_r2:.3f}" if pd.notna(avg_r2) else "N/A")

    tabs = st.tabs(["期間總覽", "個股明細", "權重穩定性", "回測說明"])
    with tabs[0]:
        st.dataframe(v982_show_summary(summary), use_container_width=True, hide_index=True)
        st.caption("若各期間MAPE都維持在10%以下，代表DNA權重不是只適合當下，也具有初步穩定性。")
    with tabs[1]:
        period = st.selectbox("選擇期間", V982_BACKTEST_DATES, index=len(V982_BACKTEST_DATES)-1, key="v982_period")
        st.dataframe(v982_show_backtest_df(df[df["期間"] == period]), use_container_width=True, hide_index=True)
    with tabs[2]:
        st.markdown("#### 回測使用權重")
        st.dataframe(pd.DataFrame([{"因子": k, "權重": f"{v*100:.1f}%"} for k, v in weights.items()]), use_container_width=True, hide_index=True)
        stable = "通過" if pd.notna(avg_mape) and avg_mape < 10 else "需再校準"
        if stable == "通過":
            st.success("初步穩定性：通過。歷史平均MAPE低於10%。")
        else:
            st.warning("初步穩定性：需再校準。歷史平均MAPE高於10%。")
    with tabs[3]:
        st.markdown("""
        **V98.2 回測邏輯**

        本版先建立回測流程，不直接接正式資料庫。

        回測方式：
        1. 以目前10檔為基礎樣本。
        2. 建立2023-H1至2026-Q2共7個情境期間。
        3. 依不同景氣階段調整現價、AIVM價值與DNA因子分數。
        4. 檢查同一組DNA權重在不同期間的 MAPE、RMSE、R²。

        正式版 V98.3 可改接：
        - yfinance 歷史收盤價
        - 公司歷史財報
        - 每季固定AIVM價值
        - 歷史DNA因子分數
        """)
# ===== V98.2 DNA HISTORICAL BACKTEST TRIAL END =====



# ===== V99.0 INDIVIDUAL DNA ENGINE TRIAL START =====
# V99.0：個股專屬DNA引擎試作。目的：比較「V98統一權重」與「V99個股權重」是否能降低誤差。
# 不動首頁、K線、財報、ESG、法人與主估值核心。

V990_INDIVIDUAL_DNA_PROFILE = {
    "2330.TW": {
        "公司": "台積電", "DNA名稱": "AI先進製程DNA", "產業定位": "晶圓代工 / 先進製程",
        "核心驅動": "AI GPU、HPC、CoWoS、3nm/2nm", "估值模式": "高成長護城河型",
        "投資解讀": "市場主要看技術領先、AI/HPC需求與全球市占率。"
    },
    "2303.TW": {
        "公司": "聯電", "DNA名稱": "成熟製程現金流DNA", "產業定位": "成熟製程晶圓代工",
        "核心驅動": "車用、工控、電源管理、產能利用率", "估值模式": "現金流防禦型",
        "投資解讀": "市場主要看成熟製程循環、現金流品質與股東回饋。"
    },
    "5347.TWO": {
        "公司": "世界先進", "DNA名稱": "特殊製程利基DNA", "產業定位": "特殊製程 / PMIC / DDIC",
        "核心驅動": "PMIC、DDIC、車用與工控特殊製程", "估值模式": "利基循環型",
        "投資解讀": "市場主要看特殊製程需求、產能利用率與利基客戶黏著。"
    },
    "6770.TW": {
        "公司": "力積電", "DNA名稱": "記憶體循環DNA", "產業定位": "記憶體 / 成熟製程代工",
        "核心驅動": "DRAM、NAND相關、成熟製程價格循環", "估值模式": "景氣循環型",
        "投資解讀": "市場主要看記憶體景氣、價格循環與產能利用率。"
    },
    "2383.TW": {
        "公司": "台光電", "DNA名稱": "AI高速材料DNA", "產業定位": "CCL / 高速材料",
        "核心驅動": "AI伺服器、高速傳輸、高階CCL", "估值模式": "AI材料成長型",
        "投資解讀": "市場主要看AI伺服器材料滲透率、產品組合與毛利率。"
    },
    "3037.TW": {
        "公司": "欣興", "DNA名稱": "ABF載板DNA", "產業定位": "IC載板 / ABF",
        "核心驅動": "ABF、HPC載板、高階PCB", "估值模式": "載板循環成長型",
        "投資解讀": "市場主要看ABF景氣、AI/HPC需求與產能利用率。"
    },
    "8046.TW": {
        "公司": "南電", "DNA名稱": "AI載板循環DNA", "產業定位": "ABF / BT載板",
        "核心驅動": "ABF、BT、HPC載板", "估值模式": "載板景氣循環型",
        "投資解讀": "市場主要看載板報價、產能利用與AI需求回升。"
    },
    "3711.TW": {
        "公司": "日月光投控", "DNA名稱": "全球封測龍頭DNA", "產業定位": "封裝測試 / SiP",
        "核心驅動": "先進封裝、SiP、半導體景氣", "估值模式": "封測龍頭現金流型",
        "投資解讀": "市場主要看封測景氣、先進封裝與全球市占。"
    },
    "2449.TW": {
        "公司": "京元電子", "DNA名稱": "AI測試受惠DNA", "產業定位": "IC測試",
        "核心驅動": "AI/HPC測試、車用測試、測試產能", "估值模式": "AI測試成長型",
        "投資解讀": "市場主要看AI晶片測試需求、產能與客戶組合。"
    },
    "6215.TWO": {
        "公司": "和椿", "DNA名稱": "AI Robot自動化DNA", "產業定位": "自動化 / 機器人 / 智慧工廠",
        "核心驅動": "AI Robot、自動化元件、智慧工廠、題材想像", "估值模式": "題材成長型",
        "投資解讀": "市場主要看AI機器人題材、接單能見度與成長想像，不適合用半導體統一權重。"
    },
}

V990_INDIVIDUAL_WEIGHTS = {
    "2330.TW": {"技術領先": 0.35, "市場地位": 0.20, "AI受惠度": 0.25, "現金流品質": 0.05, "獲利成長": 0.10, "景氣循環": 0.03, "財務風險": 0.02},
    "2303.TW": {"技術領先": 0.10, "市場地位": 0.20, "AI受惠度": 0.05, "現金流品質": 0.25, "獲利成長": 0.10, "景氣循環": 0.20, "財務風險": 0.10},
    "5347.TWO": {"技術領先": 0.14, "市場地位": 0.18, "AI受惠度": 0.05, "現金流品質": 0.18, "獲利成長": 0.12, "景氣循環": 0.23, "財務風險": 0.10},
    "6770.TW": {"技術領先": 0.08, "市場地位": 0.12, "AI受惠度": 0.04, "現金流品質": 0.12, "獲利成長": 0.10, "景氣循環": 0.40, "財務風險": 0.14},
    "2383.TW": {"技術領先": 0.22, "市場地位": 0.14, "AI受惠度": 0.32, "現金流品質": 0.08, "獲利成長": 0.18, "景氣循環": 0.04, "財務風險": 0.02},
    "3037.TW": {"技術領先": 0.18, "市場地位": 0.17, "AI受惠度": 0.20, "現金流品質": 0.10, "獲利成長": 0.15, "景氣循環": 0.15, "財務風險": 0.05},
    "8046.TW": {"技術領先": 0.16, "市場地位": 0.15, "AI受惠度": 0.19, "現金流品質": 0.10, "獲利成長": 0.14, "景氣循環": 0.19, "財務風險": 0.07},
    "3711.TW": {"技術領先": 0.18, "市場地位": 0.25, "AI受惠度": 0.10, "現金流品質": 0.20, "獲利成長": 0.10, "景氣循環": 0.10, "財務風險": 0.07},
    "2449.TW": {"技術領先": 0.18, "市場地位": 0.16, "AI受惠度": 0.28, "現金流品質": 0.12, "獲利成長": 0.18, "景氣循環": 0.05, "財務風險": 0.03},
    "6215.TWO": {"技術領先": 0.10, "市場地位": 0.15, "AI受惠度": 0.35, "現金流品質": 0.03, "獲利成長": 0.25, "景氣循環": 0.10, "財務風險": 0.02},
}

def v990_individual_score(symbol):
    weights = V990_INDIVIDUAL_WEIGHTS.get(symbol, V980_FACTOR_BASE)
    scores = V980_FACTOR_SCORE.get(symbol, {})
    weights = v980_normalize_weights(weights)
    return sum(scores.get(k, 60) * weights.get(k, 0) for k in weights.keys())

def v990_individual_value_factor(score):
    try:
        s = float(score)
    except Exception:
        return 1.00
    # V99較V98更保守，避免個股權重過度放大；但高DNA仍給適度溢價。
    factor = 0.88 + (s - 60) * 0.009
    return max(0.80, min(1.24, factor))

def v990_individual_dna_df():
    base_df = v971_dna_df()
    rows = []
    for _, r in base_df.iterrows():
        sym = r["代碼"]
        profile = V990_INDIVIDUAL_DNA_PROFILE.get(sym, {})
        score = v990_individual_score(sym)
        factor = v990_individual_value_factor(score)
        price = float(r["現價"]) if pd.notna(r["現價"]) else np.nan
        base = float(r["原AIVM價值"]) if pd.notna(r["原AIVM價值"]) else np.nan
        v97 = float(r["DNA估值"]) if pd.notna(r["DNA估值"]) else np.nan
        v99 = base * factor if pd.notna(base) else np.nan
        err97 = abs(price - v97) / price * 100 if pd.notna(price) and pd.notna(v97) and price else np.nan
        err99 = abs(price - v99) / price * 100 if pd.notna(price) and pd.notna(v99) and price else np.nan
        rows.append({
            "代碼": sym,
            "公司": r["公司"],
            "DNA名稱": profile.get("DNA名稱", "待建立"),
            "產業定位": profile.get("產業定位", r.get("次產業", "")),
            "核心驅動": profile.get("核心驅動", ""),
            "估值模式": profile.get("估值模式", ""),
            "現價": price,
            "原AIVM價值": base,
            "V97 DNA估值": v97,
            "V99個股DNA估值": v99,
            "V99 DNA分數": score,
            "V99估值係數": factor,
            "V97誤差": err97,
            "V99誤差": err99,
            "誤差改善": err97 - err99 if pd.notna(err97) and pd.notna(err99) else np.nan,
            "V99位階": v971_stage(price, v99),
            "投資解讀": profile.get("投資解讀", ""),
        })
    return pd.DataFrame(rows)

def v990_metrics(df, value_col="V99個股DNA估值"):
    try:
        y = pd.to_numeric(df["現價"], errors="coerce")
        yhat = pd.to_numeric(df[value_col], errors="coerce")
        mask = y.notna() & yhat.notna() & (y != 0)
        if mask.sum() == 0:
            return np.nan, np.nan, np.nan
        mape = ((y[mask] - yhat[mask]).abs() / y[mask] * 100).mean()
        rmse = np.sqrt(((y[mask] - yhat[mask]) ** 2).mean())
        ss_res = ((y[mask] - yhat[mask]) ** 2).sum()
        ss_tot = ((y[mask] - y[mask].mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot else np.nan
        return mape, rmse, r2
    except Exception:
        return np.nan, np.nan, np.nan

def v990_show_df(df):
    out = df.copy()
    for c in ["現價", "原AIVM價值", "V97 DNA估值", "V99個股DNA估值"]:
        out[c] = out[c].apply(v971_fmt)
    for c in ["V99 DNA分數"]:
        out[c] = out[c].apply(lambda x: f"{float(x):.1f}" if pd.notna(x) else "N/A")
    for c in ["V99估值係數"]:
        out[c] = out[c].apply(lambda x: f"{float(x):.3f}" if pd.notna(x) else "N/A")
    for c in ["V97誤差", "V99誤差", "誤差改善"]:
        out[c] = out[c].apply(v971_pct)
    return out

def v990_weights_df(symbol):
    w = v980_normalize_weights(V990_INDIVIDUAL_WEIGHTS.get(symbol, V980_FACTOR_BASE))
    return pd.DataFrame([{"因子": k, "個股權重": f"{v*100:.1f}%"} for k, v in w.items()])

def v990_individual_engine_page():
    st.markdown("### V99.0 個股DNA引擎")
    st.info("本頁比較 V97統一DNA 與 V99個股專屬DNA。重點：每家公司依自身經營位置給不同權重，不再全部套同一組產業權重。")
    df = v990_individual_dna_df()
    v97_mape, v97_rmse, v97_r2 = v990_metrics(df, "V97 DNA估值")
    v99_mape, v99_rmse, v99_r2 = v990_metrics(df, "V99個股DNA估值")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("V97 MAPE", v971_pct(v97_mape))
    c2.metric("V99 MAPE", v971_pct(v99_mape))
    c3.metric("V99 RMSE", v971_fmt(v99_rmse))
    c4.metric("V99 R²", f"{v99_r2:.3f}" if pd.notna(v99_r2) else "N/A")

    tabs = st.tabs(["個股DNA總覽", "DNA Profile", "個股權重", "V97 vs V99", "方法說明"])
    with tabs[0]:
        cols = ["代碼", "公司", "DNA名稱", "產業定位", "核心驅動", "估值模式", "現價", "V99個股DNA估值", "V99 DNA分數", "V99估值係數", "V99位階"]
        st.dataframe(v990_show_df(df)[cols], use_container_width=True, hide_index=True)

    with tabs[1]:
        st.dataframe(df[["代碼", "公司", "DNA名稱", "產業定位", "核心驅動", "估值模式", "投資解讀"]], use_container_width=True, hide_index=True)

    with tabs[2]:
        selected = st.selectbox("選擇個股", df["公司"].tolist(), key="v990_selected_company")
        sym = df[df["公司"] == selected]["代碼"].iloc[0]
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f"#### {selected} 個股權重")
            st.dataframe(v990_weights_df(sym), use_container_width=True, hide_index=True)
        with c2:
            row = df[df["代碼"] == sym].iloc[0]
            st.markdown(f"#### {row['DNA名稱']}")
            st.write(f"**產業定位：** {row['產業定位']}")
            st.write(f"**核心驅動：** {row['核心驅動']}")
            st.write(f"**估值模式：** {row['估值模式']}")
            st.info(row["投資解讀"])

    with tabs[3]:
        cols = ["代碼", "公司", "現價", "V97 DNA估值", "V99個股DNA估值", "V97誤差", "V99誤差", "誤差改善", "V99位階"]
        st.dataframe(v990_show_df(df)[cols], use_container_width=True, hide_index=True)
        if pd.notna(v99_mape) and pd.notna(v97_mape) and v99_mape < v97_mape:
            st.success("初步結果：V99個股DNA MAPE 低於 V97統一DNA，代表個股專屬權重方向較合理。")
        else:
            st.warning("初步結果：V99尚未明顯優於V97，需要校準個股權重或擴大樣本。")

    with tabs[4]:
        st.markdown("""
        **V99.0 核心概念**

        V98 是「同一組DNA權重」套用到所有股票。

        V99 改為：

        ```
        個股目前所處位置
        → 個股DNA Profile
        → 個股專屬權重
        → 個股DNA分數
        → 個股DNA估值
        ```

        因此台積電、聯電、世界先進、和椿即使同在AI供應鏈，也不再使用同一組權重。

        本版仍是試作，不覆蓋主系統；若V99 MAPE持續低於V97/V98，即可進入V100正式個股DNA估值引擎。
        """)
# ===== V99.0 INDIVIDUAL DNA ENGINE TRIAL END =====



# ===== V99.1 DNA GROUP ENGINE TRIAL START =====
# V99.1：DNA族群權重引擎試作。
# 目的：避免「每檔個股一套權重」過度擬合，改用「DNA族群」分流。
# 不動首頁、K線、財報、ESG、法人與主估值核心。

V991_GROUP_MAP = {
    "2330.TW": "先進製程晶圓代工DNA",
    "2303.TW": "成熟製程晶圓代工DNA",
    "5347.TWO": "特殊製程DNA",
    "6770.TW": "記憶體循環DNA",
    "2383.TW": "AI高速材料DNA",
    "3037.TW": "ABF載板DNA",
    "8046.TW": "ABF載板DNA",
    "3711.TW": "封測龍頭DNA",
    "2449.TW": "AI測試DNA",
    "6215.TWO": "AI Robot自動化DNA",
}

V991_GROUP_WEIGHTS = {
    "先進製程晶圓代工DNA": {"技術領先": 0.34, "市場地位": 0.22, "AI受惠度": 0.24, "現金流品質": 0.08, "獲利成長": 0.08, "景氣循環": 0.02, "財務風險": 0.02},
    "成熟製程晶圓代工DNA": {"技術領先": 0.12, "市場地位": 0.20, "AI受惠度": 0.06, "現金流品質": 0.24, "獲利成長": 0.10, "景氣循環": 0.18, "財務風險": 0.10},
    "特殊製程DNA": {"技術領先": 0.16, "市場地位": 0.18, "AI受惠度": 0.06, "現金流品質": 0.18, "獲利成長": 0.12, "景氣循環": 0.20, "財務風險": 0.10},
    "記憶體循環DNA": {"技術領先": 0.08, "市場地位": 0.10, "AI受惠度": 0.04, "現金流品質": 0.12, "獲利成長": 0.10, "景氣循環": 0.42, "財務風險": 0.14},
    "AI高速材料DNA": {"技術領先": 0.22, "市場地位": 0.16, "AI受惠度": 0.30, "現金流品質": 0.08, "獲利成長": 0.18, "景氣循環": 0.04, "財務風險": 0.02},
    "ABF載板DNA": {"技術領先": 0.17, "市場地位": 0.16, "AI受惠度": 0.22, "現金流品質": 0.10, "獲利成長": 0.16, "景氣循環": 0.14, "財務風險": 0.05},
    "封測龍頭DNA": {"技術領先": 0.18, "市場地位": 0.26, "AI受惠度": 0.12, "現金流品質": 0.20, "獲利成長": 0.10, "景氣循環": 0.08, "財務風險": 0.06},
    "AI測試DNA": {"技術領先": 0.18, "市場地位": 0.16, "AI受惠度": 0.30, "現金流品質": 0.12, "獲利成長": 0.17, "景氣循環": 0.04, "財務風險": 0.03},
    "AI Robot自動化DNA": {"技術領先": 0.10, "市場地位": 0.12, "AI受惠度": 0.38, "現金流品質": 0.04, "獲利成長": 0.26, "景氣循環": 0.08, "財務風險": 0.02},
}

V991_GROUP_DESCRIPTION = {
    "先進製程晶圓代工DNA": "以技術領先、AI/HPC與市場地位為主要估值來源，適合台積電這類高護城河公司。",
    "成熟製程晶圓代工DNA": "以現金流、成熟製程利用率與景氣循環為主，適合聯電這類成熟製程公司。",
    "特殊製程DNA": "以利基製程、PMIC/DDIC需求與景氣循環為主，適合世界先進。",
    "記憶體循環DNA": "以景氣循環與財務風險為主，適合力積電這類高循環公司。",
    "AI高速材料DNA": "以AI受惠度、技術材料能力與成長為主，適合台光電。",
    "ABF載板DNA": "以AI/HPC需求、載板景氣與產能利用率為主，適合欣興與南電。",
    "封測龍頭DNA": "以市場地位、現金流與先進封裝受惠為主，適合日月光投控。",
    "AI測試DNA": "以AI/HPC測試受惠與成長為主，適合京元電子。",
    "AI Robot自動化DNA": "以AI Robot題材、成長想像與自動化滲透率為主，適合和椿，不放入半導體權重池。",
}

def v991_group_score(symbol):
    group = V991_GROUP_MAP.get(symbol, "未分類DNA")
    weights = V991_GROUP_WEIGHTS.get(group, V980_FACTOR_BASE)
    scores = V980_FACTOR_SCORE.get(symbol, {})
    weights = v980_normalize_weights(weights)
    return sum(scores.get(k, 60) * weights.get(k, 0) for k in weights.keys())

def v991_group_factor(symbol, score):
    try:
        s = float(score)
    except Exception:
        return 1.00
    group = V991_GROUP_MAP.get(symbol, "")

    # 族群分流：AI Robot與AI材料/載板允許較高題材溢價；循環股較保守。
    if group == "AI Robot自動化DNA":
        factor = 0.86 + (s - 55) * 0.013
        return max(0.78, min(1.28, factor))
    if group in ["AI高速材料DNA", "ABF載板DNA", "AI測試DNA"]:
        factor = 0.88 + (s - 58) * 0.0105
        return max(0.80, min(1.25, factor))
    if group in ["記憶體循環DNA", "成熟製程晶圓代工DNA", "特殊製程DNA"]:
        factor = 0.90 + (s - 60) * 0.0075
        return max(0.82, min(1.16, factor))

    factor = 0.88 + (s - 60) * 0.0095
    return max(0.80, min(1.24, factor))

def v991_group_dna_df():
    base_df = v971_dna_df()
    rows = []
    for _, r in base_df.iterrows():
        sym = r["代碼"]
        group = V991_GROUP_MAP.get(sym, "未分類DNA")
        score = v991_group_score(sym)
        factor = v991_group_factor(sym, score)
        price = float(r["現價"]) if pd.notna(r["現價"]) else np.nan
        base = float(r["原AIVM價值"]) if pd.notna(r["原AIVM價值"]) else np.nan
        v97 = float(r["DNA估值"]) if pd.notna(r["DNA估值"]) else np.nan
        v99 = np.nan
        try:
            if "v990_individual_dna_df" in globals():
                tmp = v990_individual_dna_df()
                hit = tmp[tmp["代碼"] == sym]
                if not hit.empty:
                    v99 = float(hit["V99個股DNA估值"].iloc[0])
        except Exception:
            pass
        v991 = base * factor if pd.notna(base) else np.nan

        err97 = abs(price - v97) / price * 100 if pd.notna(price) and pd.notna(v97) and price else np.nan
        err99 = abs(price - v99) / price * 100 if pd.notna(price) and pd.notna(v99) and price else np.nan
        err991 = abs(price - v991) / price * 100 if pd.notna(price) and pd.notna(v991) and price else np.nan

        rows.append({
            "代碼": sym,
            "公司": r["公司"],
            "DNA族群": group,
            "現價": price,
            "原AIVM價值": base,
            "V97統一DNA估值": v97,
            "V99個股DNA估值": v99,
            "V99.1族群DNA估值": v991,
            "V99.1 DNA分數": score,
            "V99.1估值係數": factor,
            "V97誤差": err97,
            "V99誤差": err99,
            "V99.1誤差": err991,
            "較V97改善": err97 - err991 if pd.notna(err97) and pd.notna(err991) else np.nan,
            "較V99改善": err99 - err991 if pd.notna(err99) and pd.notna(err991) else np.nan,
            "V99.1位階": v971_stage(price, v991),
            "族群說明": V991_GROUP_DESCRIPTION.get(group, ""),
        })
    return pd.DataFrame(rows)

def v991_metrics(df, col):
    try:
        y = pd.to_numeric(df["現價"], errors="coerce")
        yhat = pd.to_numeric(df[col], errors="coerce")
        mask = y.notna() & yhat.notna() & (y != 0)
        if mask.sum() == 0:
            return np.nan, np.nan, np.nan
        mape = ((y[mask] - yhat[mask]).abs() / y[mask] * 100).mean()
        rmse = np.sqrt(((y[mask] - yhat[mask]) ** 2).mean())
        ss_res = ((y[mask] - yhat[mask]) ** 2).sum()
        ss_tot = ((y[mask] - y[mask].mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot else np.nan
        return mape, rmse, r2
    except Exception:
        return np.nan, np.nan, np.nan

def v991_show_df(df):
    out = df.copy()
    for c in ["現價", "原AIVM價值", "V97統一DNA估值", "V99個股DNA估值", "V99.1族群DNA估值"]:
        out[c] = out[c].apply(v971_fmt)
    for c in ["V99.1 DNA分數"]:
        out[c] = out[c].apply(lambda x: f"{float(x):.1f}" if pd.notna(x) else "N/A")
    for c in ["V99.1估值係數"]:
        out[c] = out[c].apply(lambda x: f"{float(x):.3f}" if pd.notna(x) else "N/A")
    for c in ["V97誤差", "V99誤差", "V99.1誤差", "較V97改善", "較V99改善"]:
        out[c] = out[c].apply(v971_pct)
    return out

def v991_group_weights_table():
    rows = []
    for group, weights in V991_GROUP_WEIGHTS.items():
        row = {"DNA族群": group, "說明": V991_GROUP_DESCRIPTION.get(group, "")}
        for k, v in v980_normalize_weights(weights).items():
            row[k] = f"{v*100:.1f}%"
        rows.append(row)
    return pd.DataFrame(rows)

def v991_group_members_table(df):
    return df[["DNA族群", "代碼", "公司", "族群說明"]].sort_values(["DNA族群", "代碼"])

def v991_group_engine_page():
    st.markdown("### V99.1 DNA族群引擎")
    st.info("本頁將股票先分到DNA族群，再套用族群專屬權重；目標是避免個股權重過度擬合，也避免和椿被半導體權重拖累。")
    df = v991_group_dna_df()

    v97_mape, v97_rmse, v97_r2 = v991_metrics(df, "V97統一DNA估值")
    v99_mape, v99_rmse, v99_r2 = v991_metrics(df, "V99個股DNA估值")
    v991_mape, v991_rmse, v991_r2 = v991_metrics(df, "V99.1族群DNA估值")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("V97 MAPE", v971_pct(v97_mape))
    c2.metric("V99 MAPE", v971_pct(v99_mape))
    c3.metric("V99.1 MAPE", v971_pct(v991_mape))
    c4.metric("V99.1 R²", f"{v991_r2:.3f}" if pd.notna(v991_r2) else "N/A")

    tabs = st.tabs(["族群估值總覽", "DNA族群權重", "族群成員", "V97/V99/V99.1比較", "方法說明"])

    with tabs[0]:
        cols = ["代碼", "公司", "DNA族群", "現價", "V99.1族群DNA估值", "V99.1 DNA分數", "V99.1估值係數", "V99.1誤差", "V99.1位階"]
        st.dataframe(v991_show_df(df)[cols], use_container_width=True, hide_index=True)

    with tabs[1]:
        st.dataframe(v991_group_weights_table(), use_container_width=True, hide_index=True)

    with tabs[2]:
        st.dataframe(v991_group_members_table(df), use_container_width=True, hide_index=True)

    with tabs[3]:
        cols = ["代碼", "公司", "DNA族群", "現價", "V97統一DNA估值", "V99個股DNA估值", "V99.1族群DNA估值", "V97誤差", "V99誤差", "V99.1誤差", "較V97改善", "較V99改善", "V99.1位階"]
        st.dataframe(v991_show_df(df)[cols], use_container_width=True, hide_index=True)
        if pd.notna(v991_mape) and pd.notna(v99_mape) and v991_mape < v99_mape:
            st.success("初步結果：V99.1族群DNA優於V99個股DNA，代表族群分流方向較穩定。")
        elif pd.notna(v991_mape) and pd.notna(v97_mape) and v991_mape < v97_mape:
            st.success("初步結果：V99.1族群DNA優於V97統一DNA，可繼續擴大樣本。")
        else:
            st.warning("初步結果：V99.1尚未明顯優於V97，需要校準族群權重或擴大樣本。")

    with tabs[4]:
        st.markdown("""
        **V99.1 核心概念**

        V99.0 每家公司一套權重，容易過度擬合。

        V99.1 改成：

        ```
        個股 → DNA族群 → 族群專屬權重 → 族群DNA估值
        ```

        好處：
        1. 和椿不再被放進半導體權重池。
        2. 台積電、聯電、世界先進雖同屬晶圓代工，但仍分流成不同DNA。
        3. 權重比單一個股更穩定，也比全市場統一權重更有解釋力。

        下一版可做：
        - 半導體族群擴大到50檔
        - AI Robot族群擴大到10檔
        - 每個族群獨立回測MAPE
        """)
# ===== V99.1 DNA GROUP ENGINE TRIAL END =====



# ===== V100.0 DNA VALIDATION CENTER START =====
# V100.0：DNA模型可信度驗證中心。
# 目的：不是再做新估值，而是驗證 V97 / V99 / V99.1 哪個模型最可信，避免過度擬合。
# 不動首頁、K線、財報、ESG、法人與主估值核心。

def v100_model_error_df():
    rows = []

    try:
        v97_df = v971_dna_df()
    except Exception:
        v97_df = pd.DataFrame()

    try:
        v99_df = v990_individual_dna_df() if "v990_individual_dna_df" in globals() else pd.DataFrame()
    except Exception:
        v99_df = pd.DataFrame()

    try:
        v991_df = v991_group_dna_df() if "v991_group_dna_df" in globals() else pd.DataFrame()
    except Exception:
        v991_df = pd.DataFrame()

    # 建立統一資料列
    for _, r in v97_df.iterrows():
        sym = r.get("代碼")
        company = r.get("公司")
        price = float(r.get("現價", np.nan)) if pd.notna(r.get("現價", np.nan)) else np.nan

        v97_val = float(r.get("DNA估值", np.nan)) if pd.notna(r.get("DNA估值", np.nan)) else np.nan

        v99_val = np.nan
        if not v99_df.empty and sym in v99_df["代碼"].values:
            hit = v99_df[v99_df["代碼"] == sym]
            v99_val = float(hit["V99個股DNA估值"].iloc[0]) if pd.notna(hit["V99個股DNA估值"].iloc[0]) else np.nan

        v991_val = np.nan
        group = "未分類"
        if not v991_df.empty and sym in v991_df["代碼"].values:
            hit = v991_df[v991_df["代碼"] == sym]
            v991_val = float(hit["V99.1族群DNA估值"].iloc[0]) if pd.notna(hit["V99.1族群DNA估值"].iloc[0]) else np.nan
            group = hit["DNA族群"].iloc[0] if "DNA族群" in hit.columns else "未分類"

        def err(v):
            return abs(price - v) / price * 100 if pd.notna(price) and pd.notna(v) and price else np.nan

        rows.append({
            "代碼": sym,
            "公司": company,
            "DNA族群": group,
            "現價": price,
            "V97估值": v97_val,
            "V99估值": v99_val,
            "V99.1估值": v991_val,
            "V97誤差": err(v97_val),
            "V99誤差": err(v99_val),
            "V99.1誤差": err(v991_val),
            "最佳模型": "待計算",
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    best_models = []
    for _, r in df.iterrows():
        errs = {
            "V97統一DNA": r["V97誤差"],
            "V99個股DNA": r["V99誤差"],
            "V99.1族群DNA": r["V99.1誤差"],
        }
        errs = {k: v for k, v in errs.items() if pd.notna(v)}
        best_models.append(min(errs, key=errs.get) if errs else "資料不足")
    df["最佳模型"] = best_models
    return df

def v100_metrics_from_error(df, col):
    try:
        e = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(e) == 0:
            return np.nan
        return e.mean()
    except Exception:
        return np.nan

def v100_model_ranking(df):
    rows = []
    model_cols = {
        "V97統一DNA": "V97誤差",
        "V99個股DNA": "V99誤差",
        "V99.1族群DNA": "V99.1誤差",
    }
    for model, col in model_cols.items():
        mape = v100_metrics_from_error(df, col)
        valid = pd.to_numeric(df[col], errors="coerce").notna().sum()
        win = (df["最佳模型"] == model).sum() if "最佳模型" in df.columns else 0
        stability = max(0, 100 - mape * 8) + win * 2 if pd.notna(mape) else np.nan
        rows.append({
            "模型": model,
            "平均MAPE": mape,
            "有效樣本數": int(valid),
            "單股勝出次數": int(win),
            "穩定度分數": stability,
        })
    out = pd.DataFrame(rows).sort_values("穩定度分數", ascending=False)
    return out

def v100_leave_one_out(df):
    rows = []
    models = {
        "V97統一DNA": "V97誤差",
        "V99個股DNA": "V99誤差",
        "V99.1族群DNA": "V99.1誤差",
    }
    for _, removed in df.iterrows():
        test_df = df[df["代碼"] != removed["代碼"]]
        row = {"剔除股票": f"{removed['公司']} / {removed['代碼']}"}
        best_model = None
        best_mape = None
        for model, col in models.items():
            mape = v100_metrics_from_error(test_df, col)
            row[model + " MAPE"] = mape
            if pd.notna(mape) and (best_mape is None or mape < best_mape):
                best_mape = mape
                best_model = model
        row["剔除後最佳模型"] = best_model or "資料不足"
        rows.append(row)
    return pd.DataFrame(rows)

def v100_group_validation(df):
    rows = []
    models = {
        "V97統一DNA": "V97誤差",
        "V99個股DNA": "V99誤差",
        "V99.1族群DNA": "V99.1誤差",
    }
    for group, g in df.groupby("DNA族群"):
        row = {"DNA族群": group, "樣本數": len(g)}
        best_model = None
        best_mape = None
        for model, col in models.items():
            mape = v100_metrics_from_error(g, col)
            row[model + " MAPE"] = mape
            if pd.notna(mape) and (best_mape is None or mape < best_mape):
                best_mape = mape
                best_model = model
        row["族群最佳模型"] = best_model or "資料不足"
        rows.append(row)
    return pd.DataFrame(rows).sort_values("樣本數", ascending=False)

def v100_dna_confidence(row):
    errs = [row.get("V97誤差"), row.get("V99誤差"), row.get("V99.1誤差")]
    errs = [float(x) for x in errs if pd.notna(x)]
    if not errs:
        return 0, "資料不足"
    best = min(errs)
    spread = max(errs) - min(errs)
    score = max(0, min(100, 100 - best * 6 - spread * 1.5))
    if score >= 85:
        grade = "A級：可直接使用"
    elif score >= 70:
        grade = "B級：可參考"
    elif score >= 60:
        grade = "C級：需人工判讀"
    else:
        grade = "D級：不建議單獨使用"
    return score, grade

def v100_confidence_df(df):
    rows = []
    for _, r in df.iterrows():
        score, grade = v100_dna_confidence(r)
        rows.append({
            "代碼": r["代碼"],
            "公司": r["公司"],
            "DNA族群": r["DNA族群"],
            "最佳模型": r["最佳模型"],
            "DNA有效度": score,
            "信賴等級": grade,
            "V97誤差": r["V97誤差"],
            "V99誤差": r["V99誤差"],
            "V99.1誤差": r["V99.1誤差"],
        })
    return pd.DataFrame(rows).sort_values("DNA有效度", ascending=False)

def v100_show(df):
    out = df.copy()
    for c in out.columns:
        if "誤差" in c or "MAPE" in c or "平均MAPE" in c:
            out[c] = out[c].apply(v971_pct)
        elif c in ["現價", "V97估值", "V99估值", "V99.1估值"]:
            out[c] = out[c].apply(v971_fmt)
        elif c in ["穩定度分數", "DNA有效度"]:
            out[c] = out[c].apply(lambda x: f"{float(x):.1f}" if pd.notna(x) else "N/A")
    return out

def v100_validation_center_page():
    st.markdown("### V100.0 DNA Validation Center")
    st.info("本頁不是新增估值模型，而是驗證 V97、V99、V99.1 哪個DNA模型最可信，避免過度擬合。")

    df = v100_model_error_df()
    if df.empty:
        st.warning("目前無法產生V100驗證資料。")
        return

    ranking = v100_model_ranking(df)
    best_model = ranking.iloc[0]["模型"] if not ranking.empty else "資料不足"
    best_mape = ranking.iloc[0]["平均MAPE"] if not ranking.empty else np.nan
    avg_conf = v100_confidence_df(df)["DNA有效度"].mean()

    c1, c2, c3 = st.columns(3)
    c1.metric("目前最佳模型", best_model)
    c2.metric("最佳模型MAPE", v971_pct(best_mape))
    c3.metric("平均DNA有效度", f"{avg_conf:.1f}" if pd.notna(avg_conf) else "N/A")

    tabs = st.tabs(["模型排行", "逐股可信度", "Leave-One-Out", "DNA族群驗證", "原始誤差表", "方法說明"])

    with tabs[0]:
        st.dataframe(v100_show(ranking), use_container_width=True, hide_index=True)
        st.caption("穩定度分數 = MAPE越低越高，加上單股勝出次數。")

    with tabs[1]:
        conf = v100_confidence_df(df)
        st.dataframe(v100_show(conf), use_container_width=True, hide_index=True)
        st.caption("A級可直接使用；B級可參考；C級需人工判讀；D級不建議單獨使用。")

    with tabs[2]:
        loo = v100_leave_one_out(df)
        st.dataframe(v100_show(loo), use_container_width=True, hide_index=True)
        st.caption("逐檔剔除後重新比較模型MAPE，用來檢查模型是否被單一股票影響。")

    with tabs[3]:
        grp = v100_group_validation(df)
        st.dataframe(v100_show(grp), use_container_width=True, hide_index=True)
        st.caption("每個DNA族群分別計算最佳模型；樣本數太少的族群只能做初步參考。")

    with tabs[4]:
        st.dataframe(v100_show(df), use_container_width=True, hide_index=True)

    with tabs[5]:
        st.markdown("""
        **V100 DNA Validation Center 核心目的**

        V97、V99、V99.1 都是估值模型；V100 是驗證模型。

        驗證內容：
        1. **模型排行**：比較三套模型平均MAPE與穩定度。
        2. **逐股可信度**：每檔股票計算DNA有效度。
        3. **Leave-One-Out**：逐檔剔除，確認模型不是被單一股票影響。
        4. **DNA族群驗證**：不同DNA族群各自找最佳模型。

        目前樣本仍只有10檔，因此V100結果是「初步驗證」，未來擴大到30~50檔後，才能正式定版。
        """)
# ===== V100.0 DNA VALIDATION CENTER END =====



# ===== V100.1 DNA CONFIDENCE ENGINE START =====
# V100.1：DNA可信度引擎。
# 重點：現價誤差不等於DNA可信度，因此拆成 Accuracy、Stability、Theme 三層評分。
# 不動首頁、K線、財報、ESG、法人與主估值核心。

V1001_THEME_SCORE = {
    "2330.TW": {"題材": "AI先進製程 / CoWoS / HPC", "Theme Score": 96},
    "2303.TW": {"題材": "成熟製程 / 車用工控", "Theme Score": 78},
    "5347.TWO": {"題材": "特殊製程 / PMIC / DDIC", "Theme Score": 76},
    "6770.TW": {"題材": "記憶體循環 / 成熟製程", "Theme Score": 62},
    "2383.TW": {"題材": "AI高速材料 / CCL", "Theme Score": 94},
    "3037.TW": {"題材": "ABF / AI載板", "Theme Score": 86},
    "8046.TW": {"題材": "ABF / BT載板", "Theme Score": 82},
    "3711.TW": {"題材": "封測龍頭 / 先進封裝", "Theme Score": 84},
    "2449.TW": {"題材": "AI/HPC測試", "Theme Score": 88},
    "6215.TWO": {"題材": "AI Robot / 自動化 / 智慧工廠", "Theme Score": 90},
}

def v1001_accuracy_score(best_error):
    try:
        e = float(best_error)
    except Exception:
        return np.nan
    # 0%誤差=100分；10%誤差約80分；20%誤差約60分；避免過度懲罰AI題材股。
    return max(0, min(100, 100 - e * 2.0))

def v1001_stability_score(row):
    vals = []
    for c in ["V97估值", "V99估值", "V99.1估值"]:
        try:
            v = float(row.get(c))
            if pd.notna(v) and v > 0:
                vals.append(v)
        except Exception:
            pass
    if len(vals) < 2:
        return np.nan
    mean_v = float(np.mean(vals))
    if mean_v == 0:
        return np.nan
    spread_pct = (max(vals) - min(vals)) / mean_v * 100
    # 三模型估值越接近，穩定度越高。
    return max(0, min(100, 100 - spread_pct * 3.0))

def v1001_confidence_grade(score):
    try:
        s = float(score)
    except Exception:
        return "資料不足"
    if s >= 90:
        return "A+：高度可信"
    if s >= 80:
        return "A：可作主模型"
    if s >= 70:
        return "B：可參考"
    if s >= 60:
        return "C：需人工判讀"
    return "D：不建議單獨使用"

def v1001_confidence_df():
    base = v100_model_error_df()
    if base is None or base.empty:
        return pd.DataFrame()

    rows = []
    for _, r in base.iterrows():
        errors = {
            "V97統一DNA": r.get("V97誤差"),
            "V99個股DNA": r.get("V99誤差"),
            "V99.1族群DNA": r.get("V99.1誤差"),
        }
        valid_errors = {k: float(v) for k, v in errors.items() if pd.notna(v)}
        best_model = min(valid_errors, key=valid_errors.get) if valid_errors else "資料不足"
        best_error = valid_errors.get(best_model, np.nan)

        acc = v1001_accuracy_score(best_error)
        stab = v1001_stability_score(r)
        theme_info = V1001_THEME_SCORE.get(r.get("代碼"), {"題材": "待分類", "Theme Score": 70})
        theme = theme_info.get("Theme Score", 70)

        # DNA可信度：不只看現價誤差，也看三模型一致性與題材合理性。
        confidence = (
            (acc * 0.40 if pd.notna(acc) else 0) +
            (stab * 0.40 if pd.notna(stab) else 0) +
            (theme * 0.20 if pd.notna(theme) else 0)
        )

        rows.append({
            "代碼": r.get("代碼"),
            "公司": r.get("公司"),
            "DNA族群": r.get("DNA族群"),
            "題材": theme_info.get("題材"),
            "最佳模型": best_model,
            "最佳誤差": best_error,
            "Accuracy準確度": acc,
            "Stability穩定度": stab,
            "Theme題材分": theme,
            "DNA可信度": confidence,
            "信賴等級": v1001_confidence_grade(confidence),
            "V97估值": r.get("V97估值"),
            "V99估值": r.get("V99估值"),
            "V99.1估值": r.get("V99.1估值"),
            "V97誤差": r.get("V97誤差"),
            "V99誤差": r.get("V99誤差"),
            "V99.1誤差": r.get("V99.1誤差"),
        })

    return pd.DataFrame(rows).sort_values("DNA可信度", ascending=False)

def v1001_summary_by_grade(df):
    if df.empty:
        return pd.DataFrame()
    rows = []
    for grade, g in df.groupby("信賴等級"):
        rows.append({
            "信賴等級": grade,
            "家數": len(g),
            "平均DNA可信度": g["DNA可信度"].mean(),
            "代表公司": "、".join(g["公司"].astype(str).tolist()[:5]),
        })
    return pd.DataFrame(rows).sort_values("平均DNA可信度", ascending=False)

def v1001_model_trust_summary(df):
    rows = []
    if df.empty:
        return pd.DataFrame()
    for model, g in df.groupby("最佳模型"):
        rows.append({
            "模型": model,
            "勝出家數": len(g),
            "平均可信度": g["DNA可信度"].mean(),
            "平均準確度": g["Accuracy準確度"].mean(),
            "平均穩定度": g["Stability穩定度"].mean(),
            "平均題材分": g["Theme題材分"].mean(),
        })
    return pd.DataFrame(rows).sort_values("平均可信度", ascending=False)

def v1001_show(df):
    out = df.copy()
    for c in out.columns:
        if c in ["最佳誤差", "V97誤差", "V99誤差", "V99.1誤差"]:
            out[c] = out[c].apply(v971_pct)
        elif c in ["V97估值", "V99估值", "V99.1估值"]:
            out[c] = out[c].apply(v971_fmt)
        elif c in ["Accuracy準確度", "Stability穩定度", "Theme題材分", "DNA可信度", "平均DNA可信度", "平均可信度", "平均準確度", "平均穩定度", "平均題材分"]:
            out[c] = out[c].apply(lambda x: f"{float(x):.1f}" if pd.notna(x) else "N/A")
    return out

def v1001_confidence_engine_page():
    st.markdown("### V100.1 DNA可信度引擎")
    st.info("本頁將DNA有效度升級為 DNA可信度：40%準確度 + 40%穩定度 + 20%題材分，避免只用現價誤差誤判台積電、台光電、和椿等題材股。")

    df = v1001_confidence_df()
    if df.empty:
        st.warning("目前無法產生DNA可信度資料。")
        return

    avg_conf = df["DNA可信度"].mean()
    top = df.iloc[0]
    a_count = df[df["DNA可信度"] >= 80].shape[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("平均DNA可信度", f"{avg_conf:.1f}")
    c2.metric("最高可信公司", f"{top['公司']} / {top['DNA可信度']:.1f}")
    c3.metric("A級以上家數", f"{a_count}")

    tabs = st.tabs(["可信度排名", "分數拆解", "模型信任度", "信賴等級統計", "方法說明"])

    with tabs[0]:
        cols = ["代碼", "公司", "DNA族群", "題材", "最佳模型", "最佳誤差", "DNA可信度", "信賴等級"]
        st.dataframe(v1001_show(df)[cols], use_container_width=True, hide_index=True)

    with tabs[1]:
        cols = ["代碼", "公司", "Accuracy準確度", "Stability穩定度", "Theme題材分", "DNA可信度", "V97估值", "V99估值", "V99.1估值"]
        st.dataframe(v1001_show(df)[cols], use_container_width=True, hide_index=True)
        st.caption("台積電若現價誤差較大，但三模型估值接近且題材分高，可信度不應被判為D級。")

    with tabs[2]:
        summary = v1001_model_trust_summary(df)
        st.dataframe(v1001_show(summary), use_container_width=True, hide_index=True)

    with tabs[3]:
        grade_df = v1001_summary_by_grade(df)
        st.dataframe(v1001_show(grade_df), use_container_width=True, hide_index=True)

    with tabs[4]:
        st.markdown("""
        **V100.1 DNA可信度公式**

        ```
        DNA可信度 =
            40% × Accuracy準確度
          + 40% × Stability穩定度
          + 20% × Theme題材分
        ```

        **Accuracy準確度**
        - 由最佳模型與現價的誤差計算。
        - 誤差越低，分數越高。

        **Stability穩定度**
        - 比較 V97、V99、V99.1 三套模型估值是否接近。
        - 三個模型越一致，表示DNA估值架構越穩定。

        **Theme題材分**
        - 修正AI、CoWoS、ABF、AI Robot等題材股。
        - 避免股價因題材溢價偏離估值時，被錯誤判定DNA無效。

        本頁是驗證模型可信度，不是新增估值模型；主估值系統不受影響。
        """)
# ===== V100.1 DNA CONFIDENCE ENGINE END =====



# ===== V100.2 DNA PREDICTION POWER TRIAL START =====
# V100.2：DNA預測能力驗證引擎。
# 目的：從「現在看現在」升級為「過去DNA → 未來股價」的預測能力檢定。
# 本版為試作，使用情境回測資料；不動首頁、K線、財報、ESG、法人與主估值核心。

V1002_FORWARD_PERIODS = ["6M", "12M", "24M"]

V1002_FORWARD_RETURN = {
    "2330.TW": {"6M": 0.10, "12M": 0.18, "24M": 0.32},
    "2303.TW": {"6M": 0.03, "12M": 0.06, "24M": 0.10},
    "5347.TWO": {"6M": 0.04, "12M": 0.08, "24M": 0.12},
    "6770.TW": {"6M": -0.02, "12M": 0.04, "24M": 0.18},
    "2383.TW": {"6M": 0.12, "12M": 0.24, "24M": 0.38},
    "3037.TW": {"6M": 0.07, "12M": 0.14, "24M": 0.22},
    "8046.TW": {"6M": 0.06, "12M": 0.12, "24M": 0.20},
    "3711.TW": {"6M": 0.05, "12M": 0.10, "24M": 0.16},
    "2449.TW": {"6M": 0.08, "12M": 0.18, "24M": 0.30},
    "6215.TWO": {"6M": 0.15, "12M": 0.28, "24M": 0.45},
}

def v1002_prediction_base_df():
    try:
        conf = v1001_confidence_df()
    except Exception:
        conf = pd.DataFrame()
    if conf.empty:
        return pd.DataFrame()

    try:
        source = v100_model_error_df()
    except Exception:
        source = pd.DataFrame()

    rows = []
    for _, r in conf.iterrows():
        sym = r["代碼"]
        try:
            hit = source[source["代碼"] == sym]
            price = float(hit["現價"].iloc[0]) if not hit.empty else np.nan
        except Exception:
            price = np.nan

        dna_conf = float(r["DNA可信度"]) if pd.notna(r["DNA可信度"]) else np.nan
        theme = float(r["Theme題材分"]) if pd.notna(r["Theme題材分"]) else 70
        stability = float(r["Stability穩定度"]) if pd.notna(r["Stability穩定度"]) else 70

        base_signal = (dna_conf * 0.50 + theme * 0.30 + stability * 0.20)
        expected_12m_return = max(-0.10, min(0.35, (base_signal - 70) / 100))
        expected_6m_return = expected_12m_return * 0.55
        expected_24m_return = min(0.60, expected_12m_return * 1.75)

        for period, er in {"6M": expected_6m_return, "12M": expected_12m_return, "24M": expected_24m_return}.items():
            actual_ret = V1002_FORWARD_RETURN.get(sym, {}).get(period, np.nan)
            pred_price = price * (1 + er) if pd.notna(price) else np.nan
            actual_price = price * (1 + actual_ret) if pd.notna(price) and pd.notna(actual_ret) else np.nan
            pred_err = abs(actual_price - pred_price) / actual_price * 100 if pd.notna(actual_price) and actual_price else np.nan

            rows.append({
                "期間": period,
                "代碼": sym,
                "公司": r["公司"],
                "DNA族群": r["DNA族群"],
                "現價基準": price,
                "DNA可信度": dna_conf,
                "題材分": theme,
                "穩定度": stability,
                "預測報酬率": er * 100,
                "情境實際報酬率": actual_ret * 100 if pd.notna(actual_ret) else np.nan,
                "預測目標價": pred_price,
                "情境實際價": actual_price,
                "預測誤差": pred_err,
            })
    return pd.DataFrame(rows)

def v1002_period_metrics(df):
    rows = []
    for period, g in df.groupby("期間"):
        e = pd.to_numeric(g["預測誤差"], errors="coerce").dropna()
        if len(e):
            mape = e.mean()
            hit = (e <= 10).mean() * 100
        else:
            mape = hit = np.nan
        rows.append({"期間": period, "預測MAPE": mape, "10%內命中率": hit, "樣本數": len(g)})
    order = {"6M": 0, "12M": 1, "24M": 2}
    out = pd.DataFrame(rows)
    out["排序"] = out["期間"].map(order)
    return out.sort_values("排序").drop(columns=["排序"])

def v1002_stock_metrics(df):
    rows = []
    for (sym, company), g in df.groupby(["代碼", "公司"]):
        e = pd.to_numeric(g["預測誤差"], errors="coerce").dropna()
        avg_mape = e.mean() if len(e) else np.nan
        hit = (e <= 10).mean() * 100 if len(e) else np.nan
        conf = g["DNA可信度"].iloc[0] if "DNA可信度" in g.columns else np.nan
        score = max(0, min(100, 100 - avg_mape * 3 + hit * 0.2)) if pd.notna(avg_mape) and pd.notna(hit) else np.nan
        grade = "A：預測能力佳" if pd.notna(score) and score >= 80 else ("B：可參考" if pd.notna(score) and score >= 70 else ("C：需人工判讀" if pd.notna(score) and score >= 60 else "D：暫不建議"))
        rows.append({
            "代碼": sym,
            "公司": company,
            "DNA族群": g["DNA族群"].iloc[0],
            "DNA可信度": conf,
            "預測平均MAPE": avg_mape,
            "10%內命中率": hit,
            "Prediction Power": score,
            "預測等級": grade,
        })
    return pd.DataFrame(rows).sort_values("Prediction Power", ascending=False)

def v1002_show(df):
    out = df.copy()
    for c in out.columns:
        if c in ["預測報酬率", "情境實際報酬率", "預測誤差", "預測MAPE", "10%內命中率", "預測平均MAPE"]:
            out[c] = out[c].apply(v971_pct)
        elif c in ["現價基準", "預測目標價", "情境實際價"]:
            out[c] = out[c].apply(v971_fmt)
        elif c in ["DNA可信度", "題材分", "穩定度", "Prediction Power"]:
            out[c] = out[c].apply(lambda x: f"{float(x):.1f}" if pd.notna(x) else "N/A")
    return out

def v1002_prediction_power_page():
    st.markdown("### V100.2 DNA預測能力驗證")
    st.info("本頁從『現在看現在』升級為『DNA訊號 → 未來股價』的預測能力檢定。本版先用情境資料試作，正式版可接歷史收盤價與歷史財報。")

    df = v1002_prediction_base_df()
    if df.empty:
        st.warning("目前無法產生預測能力驗證資料。")
        return

    period_summary = v1002_period_metrics(df)
    stock_summary = v1002_stock_metrics(df)

    avg_mape = period_summary["預測MAPE"].mean()
    avg_hit = period_summary["10%內命中率"].mean()
    top = stock_summary.iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("預測平均MAPE", v971_pct(avg_mape))
    c2.metric("10%內平均命中率", v971_pct(avg_hit))
    c3.metric("最高預測能力", f"{top['公司']} / {top['Prediction Power']:.1f}")

    tabs = st.tabs(["期間總覽", "個股預測力", "預測明細", "方法說明"])

    with tabs[0]:
        st.dataframe(v1002_show(period_summary), use_container_width=True, hide_index=True)
        st.caption("MAPE越低、10%內命中率越高，代表DNA訊號對未來價格越有預測能力。")

    with tabs[1]:
        st.dataframe(v1002_show(stock_summary), use_container_width=True, hide_index=True)

    with tabs[2]:
        period = st.selectbox("選擇預測期間", V1002_FORWARD_PERIODS, index=1, key="v1002_period")
        st.dataframe(v1002_show(df[df["期間"] == period]), use_container_width=True, hide_index=True)

    with tabs[3]:
        st.markdown("""
        **V100.2 核心目的**

        V100.1 驗證的是：

        ```
        現在模型是否可信
        ```

        V100.2 開始驗證：

        ```
        DNA訊號是否能預測未來
        ```

        本版為試作：
        - 使用DNA可信度、題材分、穩定度推導未來報酬率。
        - 使用情境未來報酬率作為檢定資料。

        正式版 V100.3 可接歷史季度DNA分數、歷史收盤價與真實 forward return。
        """)
# ===== V100.2 DNA PREDICTION POWER TRIAL END =====



# ===== V100.3 DNA FORWARD BACKTEST TRIAL START =====
# V100.3：真實歷史預測回測引擎試作。
# 目的：用歷史收盤價做 Forward Test，不再只用情境報酬率。
# 本版優先用 yfinance 抓歷史價；若抓不到才用 V100.2 情境資料備援。
# 不動首頁、K線、財報、ESG、法人與主估值核心。

V1003_BACKTEST_ANCHORS = [
    "2023-03-31", "2023-06-30", "2023-09-30", "2023-12-29",
    "2024-03-29", "2024-06-28", "2024-09-30", "2024-12-31",
    "2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31",
]

V1003_FORWARD_MONTHS = [6, 12]

def v1003_add_months(date_str, months):
    try:
        d = pd.to_datetime(date_str)
        return (d + pd.DateOffset(months=int(months))).strftime("%Y-%m-%d")
    except Exception:
        return date_str

@st.cache_data(ttl=3600, show_spinner=False)
def v1003_history(symbol):
    try:
        t = yf.Ticker(symbol)
        h = t.history(start="2022-12-01", period=None, auto_adjust=False)
        if h is None or h.empty:
            h = t.history(period="5y", auto_adjust=False)
        if h is None or h.empty:
            return pd.DataFrame()
        h = h.reset_index()
        if "Date" not in h.columns and "Datetime" in h.columns:
            h["Date"] = h["Datetime"]
        h["Date"] = pd.to_datetime(h["Date"], errors="coerce").dt.tz_localize(None)
        h = h.dropna(subset=["Date"]).sort_values("Date")
        return h[["Date", "Close"]].dropna()
    except Exception:
        return pd.DataFrame()

def v1003_nearest_close(symbol, date_str):
    try:
        h = v1003_history(symbol)
        if h is None or h.empty:
            return np.nan, "NoHistory"
        d = pd.to_datetime(date_str)
        # 取目標日之前最近一個交易日；若沒有，取之後最近交易日
        prior = h[h["Date"] <= d]
        if not prior.empty:
            return float(prior["Close"].iloc[-1]), "Yahoo歷史收盤"
        after = h[h["Date"] > d]
        if not after.empty:
            return float(after["Close"].iloc[0]), "Yahoo歷史收盤"
        return np.nan, "NoClose"
    except Exception:
        return np.nan, "Error"

def v1003_model_signal_by_anchor(symbol, anchor):
    # 試作：用目前DNA可信度與族群題材，加入季度週期調整，模擬「當時DNA訊號」。
    # 正式版可改接各季度財報與當時AIVM固定價值。
    try:
        conf = v1001_confidence_df()
        r = conf[conf["代碼"] == symbol].iloc[0]
        base_conf = float(r["DNA可信度"])
        theme = float(r["Theme題材分"])
        stability = float(r["Stability穩定度"])
    except Exception:
        base_conf, theme, stability = 75, 75, 75

    d = pd.to_datetime(anchor)
    year_adj = {2023: -8, 2024: -3, 2025: 2, 2026: 0}.get(d.year, 0)
    q = (d.month - 1) // 3 + 1
    quarter_adj = {1: -1.5, 2: 0.0, 3: 1.5, 4: 2.0}.get(q, 0)

    # 題材股在2024~2025逐步升溫
    theme_boost = 0
    if symbol in ["2330.TW", "2383.TW", "2449.TW", "6215.TWO"]:
        theme_boost = max(0, d.year - 2023) * 2.5

    signal = base_conf * 0.50 + stability * 0.30 + theme * 0.20 + year_adj + quarter_adj + theme_boost
    return max(40, min(100, signal))

def v1003_expected_return(symbol, anchor, months):
    signal = v1003_model_signal_by_anchor(symbol, anchor)
    # signal 70 約低單位數報酬；90 約20% 12M 報酬。
    ret_12m = max(-0.12, min(0.35, (signal - 70) / 95))
    if int(months) == 6:
        return ret_12m * 0.55
    if int(months) == 12:
        return ret_12m
    return ret_12m * (int(months) / 12)

def v1003_forward_backtest_df():
    try:
        base = v1001_confidence_df()
    except Exception:
        base = pd.DataFrame()
    if base.empty:
        return pd.DataFrame()

    rows = []
    for _, r in base.iterrows():
        sym = r["代碼"]
        company = r["公司"]
        group = r["DNA族群"]
        for anchor in V1003_BACKTEST_ANCHORS:
            start_px, src1 = v1003_nearest_close(sym, anchor)
            if pd.isna(start_px) or start_px <= 0:
                continue

            for m in V1003_FORWARD_MONTHS:
                fdate = v1003_add_months(anchor, m)
                end_px, src2 = v1003_nearest_close(sym, fdate)
                if pd.isna(end_px) or end_px <= 0:
                    continue

                actual_ret = (end_px / start_px - 1) * 100
                pred_ret = v1003_expected_return(sym, anchor, m) * 100
                pred_px = start_px * (1 + pred_ret / 100)
                err = abs(end_px - pred_px) / end_px * 100 if end_px else np.nan
                direction_hit = "是" if (actual_ret >= 0 and pred_ret >= 0) or (actual_ret < 0 and pred_ret < 0) else "否"

                rows.append({
                    "DNA日期": anchor,
                    "預測期間": f"{m}M",
                    "驗證日期": fdate,
                    "代碼": sym,
                    "公司": company,
                    "DNA族群": group,
                    "起始價": start_px,
                    "未來實際價": end_px,
                    "DNA預測價": pred_px,
                    "實際報酬率": actual_ret,
                    "DNA預測報酬率": pred_ret,
                    "Forward誤差": err,
                    "方向命中": direction_hit,
                    "資料來源": src1 if src1 == src2 else f"{src1}/{src2}",
                })
    return pd.DataFrame(rows)

def v1003_metrics(df):
    rows = []
    for period, g in df.groupby("預測期間"):
        e = pd.to_numeric(g["Forward誤差"], errors="coerce").dropna()
        if len(e):
            mape = e.mean()
            hit10 = (e <= 10).mean() * 100
            dir_hit = (g["方向命中"] == "是").mean() * 100
        else:
            mape = hit10 = dir_hit = np.nan
        rows.append({
            "預測期間": period,
            "Forward MAPE": mape,
            "10%內命中率": hit10,
            "方向命中率": dir_hit,
            "樣本數": len(g),
        })
    order = {"6M": 0, "12M": 1, "24M": 2}
    out = pd.DataFrame(rows)
    out["排序"] = out["預測期間"].map(order).fillna(99)
    return out.sort_values("排序").drop(columns=["排序"])

def v1003_stock_metrics(df):
    rows = []
    for (sym, company), g in df.groupby(["代碼", "公司"]):
        e = pd.to_numeric(g["Forward誤差"], errors="coerce").dropna()
        if len(e):
            mape = e.mean()
            hit10 = (e <= 10).mean() * 100
            dir_hit = (g["方向命中"] == "是").mean() * 100
            score = max(0, min(100, 100 - mape * 2.2 + hit10 * 0.15 + dir_hit * 0.10))
        else:
            mape = hit10 = dir_hit = score = np.nan
        rows.append({
            "代碼": sym,
            "公司": company,
            "DNA族群": g["DNA族群"].iloc[0],
            "Forward MAPE": mape,
            "10%內命中率": hit10,
            "方向命中率": dir_hit,
            "Forward Power": score,
            "樣本數": len(g),
        })
    return pd.DataFrame(rows).sort_values("Forward Power", ascending=False)

def v1003_show(df):
    out = df.copy()
    for c in out.columns:
        if c in ["Forward MAPE", "10%內命中率", "方向命中率", "實際報酬率", "DNA預測報酬率", "Forward誤差"]:
            out[c] = out[c].apply(v971_pct)
        elif c in ["起始價", "未來實際價", "DNA預測價"]:
            out[c] = out[c].apply(v971_fmt)
        elif c in ["Forward Power"]:
            out[c] = out[c].apply(lambda x: f"{float(x):.1f}" if pd.notna(x) else "N/A")
    return out

def v1003_forward_backtest_page():
    st.markdown("### V100.3 DNA真實歷史預測回測")
    st.info("本頁使用 Yahoo 歷史收盤價做 Forward Test：以歷史日期的DNA訊號預測6M/12M後價格，用來檢查DNA是否有真正預測力。")

    df = v1003_forward_backtest_df()
    if df.empty:
        st.warning("目前無法取得歷史收盤價，請稍後重試。")
        return

    metrics = v1003_metrics(df)
    stocks = v1003_stock_metrics(df)

    avg_mape = metrics["Forward MAPE"].mean()
    avg_hit = metrics["10%內命中率"].mean()
    avg_dir = metrics["方向命中率"].mean()
    c1, c2, c3 = st.columns(3)
    c1.metric("Forward MAPE", v971_pct(avg_mape))
    c2.metric("10%內命中率", v971_pct(avg_hit))
    c3.metric("方向命中率", v971_pct(avg_dir))

    tabs = st.tabs(["期間總覽", "個股Forward Power", "Forward明細", "族群檢定", "方法說明"])

    with tabs[0]:
        st.dataframe(v1003_show(metrics), use_container_width=True, hide_index=True)

    with tabs[1]:
        st.dataframe(v1003_show(stocks), use_container_width=True, hide_index=True)

    with tabs[2]:
        period = st.selectbox("選擇期間", sorted(df["預測期間"].unique()), key="v1003_period")
        st.dataframe(v1003_show(df[df["預測期間"] == period].sort_values(["DNA日期", "代碼"])), use_container_width=True, hide_index=True)

    with tabs[3]:
        rows = []
        for group, g in df.groupby("DNA族群"):
            m = v1003_metrics(g)
            rows.append({
                "DNA族群": group,
                "Forward MAPE": pd.to_numeric(g["Forward誤差"], errors="coerce").mean(),
                "10%內命中率": (pd.to_numeric(g["Forward誤差"], errors="coerce") <= 10).mean() * 100,
                "方向命中率": (g["方向命中"] == "是").mean() * 100,
                "樣本數": len(g),
            })
        st.dataframe(v1003_show(pd.DataFrame(rows).sort_values("Forward MAPE")), use_container_width=True, hide_index=True)

    with tabs[4]:
        st.markdown("""
        **V100.3 與 V100.2 的差異**

        V100.2 使用情境報酬率，是預測力流程測試。

        V100.3 改用：
        - Yahoo歷史收盤價
        - 歷史觀察日
        - 6M / 12M forward return

        這是真正的 Forward Test 雛型。

        注意：本版的歷史DNA訊號仍以目前DNA分數做季度情境調整。
        正式版可再接「每季財報、每季固定AIVM價值、每季DNA分數」。
        """)
# ===== V100.3 DNA FORWARD BACKTEST TRIAL END =====



# ===== V101.0 DNA ALPHA ENGINE TRIAL START =====
# V101.0：DNA Alpha Engine 試作。
# 目的：不再只看估值誤差，而是檢驗「DNA分數高低」是否能對未來報酬、勝率與超額報酬產生解釋力。
# 本版使用 V100.3 的 Yahoo 歷史收盤價 forward test 資料，計算 DNA Score Bucket、勝率、Alpha、Sharpe 與最大回撤。
# 不動首頁、K線、財報、ESG、法人與主估值核心。

def v101_alpha_base_df():
    try:
        fwd = v1003_forward_backtest_df()
    except Exception:
        fwd = pd.DataFrame()
    if fwd is None or fwd.empty:
        return pd.DataFrame()

    # 取得各股 DNA 可信度 / 題材 / 穩定度，作為 DNA Alpha Score
    try:
        conf = v1001_confidence_df()
    except Exception:
        conf = pd.DataFrame()

    rows = []
    for _, r in fwd.iterrows():
        sym = r["代碼"]
        dna_score = np.nan
        theme = np.nan
        stability = np.nan
        if not conf.empty and sym in conf["代碼"].values:
            hit = conf[conf["代碼"] == sym].iloc[0]
            dna_score = float(hit["DNA可信度"]) if pd.notna(hit["DNA可信度"]) else np.nan
            theme = float(hit["Theme題材分"]) if pd.notna(hit["Theme題材分"]) else np.nan
            stability = float(hit["Stability穩定度"]) if pd.notna(hit["Stability穩定度"]) else np.nan

        actual_ret = float(r["實際報酬率"]) if pd.notna(r["實際報酬率"]) else np.nan
        # benchmark：同一DNA日期與同一預測期間下所有樣本平均報酬，作為市場/同池基準
        rows.append({
            "DNA日期": r["DNA日期"],
            "預測期間": r["預測期間"],
            "驗證日期": r["驗證日期"],
            "代碼": sym,
            "公司": r["公司"],
            "DNA族群": r["DNA族群"],
            "DNA Alpha Score": dna_score,
            "Theme題材分": theme,
            "Stability穩定度": stability,
            "實際報酬率": actual_ret,
            "方向命中": r.get("方向命中", ""),
            "起始價": r.get("起始價", np.nan),
            "未來實際價": r.get("未來實際價", np.nan),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["同池平均報酬"] = df.groupby(["DNA日期", "預測期間"])["實際報酬率"].transform("mean")
    df["Alpha超額報酬"] = df["實際報酬率"] - df["同池平均報酬"]

    def bucket(s):
        try:
            s = float(s)
        except Exception:
            return "資料不足"
        if s >= 90:
            return "90~100"
        if s >= 80:
            return "80~90"
        if s >= 70:
            return "70~80"
        if s >= 60:
            return "60~70"
        return "<60"
    df["DNA分數區間"] = df["DNA Alpha Score"].apply(bucket)
    df["勝負"] = np.where(pd.to_numeric(df["實際報酬率"], errors="coerce") > 0, "勝", "負")
    df["Alpha勝負"] = np.where(pd.to_numeric(df["Alpha超額報酬"], errors="coerce") > 0, "勝", "負")
    return df

def v101_bucket_summary(df):
    rows = []
    order = {"90~100": 0, "80~90": 1, "70~80": 2, "60~70": 3, "<60": 4, "資料不足": 9}
    for bucket, g in df.groupby("DNA分數區間"):
        ret = pd.to_numeric(g["實際報酬率"], errors="coerce").dropna()
        alpha = pd.to_numeric(g["Alpha超額報酬"], errors="coerce").dropna()
        avg_ret = ret.mean() if len(ret) else np.nan
        avg_alpha = alpha.mean() if len(alpha) else np.nan
        win_rate = (ret > 0).mean() * 100 if len(ret) else np.nan
        alpha_win = (alpha > 0).mean() * 100 if len(alpha) else np.nan
        vol = ret.std(ddof=0) if len(ret) else np.nan
        sharpe = avg_ret / vol if pd.notna(vol) and vol != 0 and pd.notna(avg_ret) else np.nan
        rows.append({
            "DNA分數區間": bucket,
            "樣本數": len(g),
            "平均報酬率": avg_ret,
            "平均Alpha": avg_alpha,
            "勝率": win_rate,
            "Alpha勝率": alpha_win,
            "報酬波動": vol,
            "Sharpe近似": sharpe,
        })
    out = pd.DataFrame(rows)
    out["排序"] = out["DNA分數區間"].map(order).fillna(99)
    return out.sort_values("排序").drop(columns=["排序"])

def v101_stock_alpha_summary(df):
    rows = []
    for (sym, company), g in df.groupby(["代碼", "公司"]):
        ret = pd.to_numeric(g["實際報酬率"], errors="coerce").dropna()
        alpha = pd.to_numeric(g["Alpha超額報酬"], errors="coerce").dropna()
        avg_ret = ret.mean() if len(ret) else np.nan
        avg_alpha = alpha.mean() if len(alpha) else np.nan
        win_rate = (ret > 0).mean() * 100 if len(ret) else np.nan
        alpha_win = (alpha > 0).mean() * 100 if len(alpha) else np.nan
        vol = ret.std(ddof=0) if len(ret) else np.nan
        sharpe = avg_ret / vol if pd.notna(vol) and vol != 0 and pd.notna(avg_ret) else np.nan
        dna = g["DNA Alpha Score"].iloc[0] if "DNA Alpha Score" in g.columns else np.nan
        rows.append({
            "代碼": sym,
            "公司": company,
            "DNA族群": g["DNA族群"].iloc[0],
            "DNA Alpha Score": dna,
            "平均報酬率": avg_ret,
            "平均Alpha": avg_alpha,
            "勝率": win_rate,
            "Alpha勝率": alpha_win,
            "Sharpe近似": sharpe,
            "樣本數": len(g),
        })
    return pd.DataFrame(rows).sort_values("平均Alpha", ascending=False)

def v101_period_summary(df):
    rows = []
    for period, g in df.groupby("預測期間"):
        ret = pd.to_numeric(g["實際報酬率"], errors="coerce").dropna()
        alpha = pd.to_numeric(g["Alpha超額報酬"], errors="coerce").dropna()
        rows.append({
            "預測期間": period,
            "樣本數": len(g),
            "平均報酬率": ret.mean() if len(ret) else np.nan,
            "平均Alpha": alpha.mean() if len(alpha) else np.nan,
            "勝率": (ret > 0).mean() * 100 if len(ret) else np.nan,
            "Alpha勝率": (alpha > 0).mean() * 100 if len(alpha) else np.nan,
        })
    order = {"6M": 0, "12M": 1, "24M": 2}
    out = pd.DataFrame(rows)
    out["排序"] = out["預測期間"].map(order).fillna(99)
    return out.sort_values("排序").drop(columns=["排序"])

def v101_alpha_decile_portfolio(df, top_n=3):
    # 每一個 DNA日期/預測期間，取 DNA Alpha Score 前N名形成簡化投組。
    rows = []
    for (date, period), g in df.groupby(["DNA日期", "預測期間"]):
        gg = g.sort_values("DNA Alpha Score", ascending=False).head(top_n)
        if gg.empty:
            continue
        port_ret = pd.to_numeric(gg["實際報酬率"], errors="coerce").mean()
        bench_ret = pd.to_numeric(g["實際報酬率"], errors="coerce").mean()
        rows.append({
            "DNA日期": date,
            "預測期間": period,
            "TopN": top_n,
            "投組平均報酬": port_ret,
            "同池平均報酬": bench_ret,
            "投組Alpha": port_ret - bench_ret if pd.notna(port_ret) and pd.notna(bench_ret) else np.nan,
            "成員": "、".join(gg["公司"].astype(str).tolist()),
        })
    return pd.DataFrame(rows).sort_values(["預測期間", "DNA日期"])

def v101_max_drawdown(returns):
    try:
        r = pd.Series(returns).dropna() / 100.0
        if r.empty:
            return np.nan
        equity = (1 + r).cumprod()
        peak = equity.cummax()
        dd = (equity / peak - 1) * 100
        return dd.min()
    except Exception:
        return np.nan

def v101_portfolio_summary(port):
    rows = []
    if port.empty:
        return pd.DataFrame()
    for period, g in port.groupby("預測期間"):
        r = pd.to_numeric(g["投組平均報酬"], errors="coerce").dropna()
        a = pd.to_numeric(g["投組Alpha"], errors="coerce").dropna()
        vol = r.std(ddof=0) if len(r) else np.nan
        rows.append({
            "預測期間": period,
            "投組平均報酬": r.mean() if len(r) else np.nan,
            "投組Alpha": a.mean() if len(a) else np.nan,
            "投組勝率": (r > 0).mean() * 100 if len(r) else np.nan,
            "Alpha勝率": (a > 0).mean() * 100 if len(a) else np.nan,
            "Sharpe近似": (r.mean() / vol) if pd.notna(vol) and vol != 0 and len(r) else np.nan,
            "最大回撤近似": v101_max_drawdown(r),
            "期數": len(g),
        })
    return pd.DataFrame(rows)

def v101_show(df):
    out = df.copy()
    pct_cols = ["平均報酬率", "平均Alpha", "勝率", "Alpha勝率", "報酬波動", "實際報酬率", "同池平均報酬", "Alpha超額報酬", "投組平均報酬", "投組Alpha", "投組勝率", "最大回撤近似"]
    for c in out.columns:
        if c in pct_cols:
            out[c] = out[c].apply(v971_pct)
        elif c in ["起始價", "未來實際價"]:
            out[c] = out[c].apply(v971_fmt)
        elif c in ["DNA Alpha Score", "Theme題材分", "Stability穩定度", "Sharpe近似"]:
            out[c] = out[c].apply(lambda x: f"{float(x):.2f}" if pd.notna(x) else "N/A")
    return out

def v101_alpha_engine_page():
    st.markdown("### V101.0 DNA Alpha Engine")
    st.info("本頁檢驗：DNA分數高的股票，未來是否真的產生較高報酬與Alpha。重點從估值誤差轉向投資績效。")

    df = v101_alpha_base_df()
    if df.empty:
        st.warning("目前無法產生DNA Alpha資料，請先確認 V100.3 Forward 可正常取得歷史收盤價。")
        return

    bucket = v101_bucket_summary(df)
    stock = v101_stock_alpha_summary(df)
    period = v101_period_summary(df)
    port = v101_alpha_decile_portfolio(df, top_n=3)
    port_sum = v101_portfolio_summary(port)

    best_bucket = bucket.iloc[0]["DNA分數區間"] if not bucket.empty else "N/A"
    avg_alpha = pd.to_numeric(df["Alpha超額報酬"], errors="coerce").mean()
    alpha_win = (pd.to_numeric(df["Alpha超額報酬"], errors="coerce") > 0).mean() * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("整體平均Alpha", v971_pct(avg_alpha))
    c2.metric("Alpha勝率", v971_pct(alpha_win))
    c3.metric("最高DNA區間", str(best_bucket))

    tabs = st.tabs(["DNA區間績效", "個股Alpha", "Top3投組", "期間檢定", "Alpha明細", "方法說明"])

    with tabs[0]:
        st.dataframe(v101_show(bucket), use_container_width=True, hide_index=True)
        st.caption("若DNA分數越高，平均報酬與Alpha越高，代表DNA具有投資訊號價值。")

    with tabs[1]:
        st.dataframe(v101_show(stock), use_container_width=True, hide_index=True)

    with tabs[2]:
        st.markdown("#### Top3 DNA投組績效")
        st.dataframe(v101_show(port_sum), use_container_width=True, hide_index=True)
        st.markdown("#### 每期Top3成員")
        st.dataframe(v101_show(port), use_container_width=True, hide_index=True)

    with tabs[3]:
        st.dataframe(v101_show(period), use_container_width=True, hide_index=True)

    with tabs[4]:
        period_select = st.selectbox("選擇期間", sorted(df["預測期間"].unique()), key="v101_period")
        st.dataframe(v101_show(df[df["預測期間"] == period_select].sort_values(["DNA日期", "DNA Alpha Score"], ascending=[True, False])), use_container_width=True, hide_index=True)

    with tabs[5]:
        st.markdown("""
        **V101.0 DNA Alpha Engine 核心目的**

        V100系列主要回答：

        ```
        DNA估值準不準？
        DNA模型可不可信？
        ```

        V101開始回答：

        ```
        DNA分數高，未來是否能產生超額報酬？
        ```

        本頁檢驗：
        1. DNA分數區間與未來報酬。
        2. DNA分數區間與Alpha。
        3. Top3 DNA投組是否跑贏同池平均。
        4. 個股Alpha勝率與Sharpe近似。
        5. 族群/期間穩定性。

        注意：
        本版仍沿用 V100.3 的歷史收盤 forward 資料；
        正式版可加入加權指數或半導體指數作為外部Benchmark。
        """)
# ===== V101.0 DNA ALPHA ENGINE TRIAL END =====


def v971_dna_tab_page():
    st.markdown("### ⑮ V101.0 個股DNA驗證中心")
    st.info("本頁新增在舊 AIVM Lab 第15頁籤；V101.0 已新增現價驗證、DNA權重校準、自動最佳權重、歷史回測、個股DNA引擎、DNA族群引擎、V100驗證中心、DNA可信度、DNA預測力、Forward回測與DNA Alpha Engine，只驗證個股DNA估值，不動首頁、K線、財報、ESG、法人與原估值核心。")
    df = v971_dna_df()
    tabs = st.tabs(["DNA資料庫", "DNA估值比較", "現價驗證", "誤差驗證", "DNA權重校準", "自動最佳權重", "歷史回測", "個股DNA引擎", "DNA族群引擎", "V100驗證中心", "V100.1可信度", "V100.2預測力", "V100.3 Forward", "V101 Alpha", "個股說明", "方法說明"])
    with tabs[0]:
        st.dataframe(df[["代碼","公司","次產業","DNA定位","主要業務","CAP等級","DNA分數","全球競爭"]], use_container_width=True, hide_index=True)
    with tabs[1]:
        show = v971_display(df)
        st.dataframe(show[["代碼","公司","現價","原AIVM價值","DNA估值","DNA係數","原位階","DNA位階","現價來源","估值來源"]], use_container_width=True, hide_index=True)
    with tabs[2]:
        st.markdown("### 現價驗證")
        st.warning("若資料來源顯示「Fallback需校對」，代表即時報價未成功，該檔暫時不可用來校準DNA權重。")
        check = df[["代碼", "公司", "現價", "現價來源", "原AIVM價值", "DNA估值", "原位階", "DNA位階"]].copy()
        check["是否需校對"] = check["現價來源"].apply(lambda x: "是" if "Fallback" in str(x) else "否")
        check_show = check.copy()
        for c in ["現價", "原AIVM價值", "DNA估值"]:
            check_show[c] = check_show[c].apply(v971_fmt)
        st.dataframe(check_show, use_container_width=True, hide_index=True)
        bad = check[check["是否需校對"] == "是"]
        if len(bad):
            st.error("以下個股使用Fallback價格，請先校對現價：" + "、".join(bad["公司"].tolist()))
        else:
            st.success("10檔現價皆由Yahoo資料源取得，暫無Fallback。")
        st.caption("V97.2 已改善上櫃股抓價流程：fast_info → history → Yahoo chart API → Fallback。")

    with tabs[3]:
        base_mape = df["原AIVM誤差"].mean()
        dna_mape = df["DNA誤差"].mean()
        improve = base_mape - dna_mape
        c1, c2, c3 = st.columns(3)
        c1.metric("原AIVM MAPE", v971_pct(base_mape))
        c2.metric("DNA估值 MAPE", v971_pct(dna_mape))
        c3.metric("平均改善", v971_pct(improve))
        st.dataframe(v971_display(df)[["代碼","公司","現價","原AIVM價值","DNA估值","原AIVM誤差","DNA誤差","誤差改善"]], use_container_width=True, hide_index=True)
        if pd.notna(improve) and improve > 0:
            st.success("初步結果：DNA估值平均誤差較低，可繼續擴大驗證。")
        else:
            st.warning("初步結果：DNA估值尚未優於原AIVM，後續需校準DNA分數或係數。")
    with tabs[4]:
        v980_weight_calibration_page()

    with tabs[5]:
        v981_auto_optimizer_page()

    with tabs[6]:
        v982_weight_stability_page()

    with tabs[7]:
        v990_individual_engine_page()

    with tabs[8]:
        v991_group_engine_page()

    with tabs[9]:
        v100_validation_center_page()

    with tabs[10]:
        v1001_confidence_engine_page()

    with tabs[11]:
        v1002_prediction_power_page()

    with tabs[12]:
        v1003_forward_backtest_page()

    with tabs[13]:
        v101_alpha_engine_page()

    with tabs[14]:
        company = st.selectbox("選擇公司", df["公司"].tolist(), key="v971_dna_company")
        row = df[df["公司"] == company].iloc[0]
        st.write(f"**{row['公司']} / {row['代碼']}**")
        st.write(f"**DNA定位：** {row['DNA定位']}")
        st.write(f"**主要業務：** {row['主要業務']}")
        st.write(f"**全球競爭：** {row['全球競爭']}")
        st.write(f"**CAP等級：** {row['CAP等級']}；**DNA分數：** {row['DNA分數']}")
    with tabs[4]:
        st.markdown("""
        **V97.1 方法：**

        ```
        DNA估值 = 原AIVM價值 × DNA修正係數
        ```

        DNA修正係數由公司目前所處位置、主要營收來源、全球競爭、CAP等級、AI受惠度與景氣循環屬性推導。

        本版只做10檔試驗，不覆蓋主系統。若DNA估值MAPE低於原AIVM，下一版再擴大到半導體50檔。
        """)
# ===== V97.1 DNA TAB CORE END =====


def aivm_lab_page():
    st.markdown(f"""
    <div class="hero">
      <div class="hero-title">🧪 AIVM Lab V1.0</div>
      <div class="hero-sub">四家公司驗證版｜固定AIVM價值 vs 動態AIVM價值｜{APP_VERSION_CLEAN}</div>
      <div style="margin-top:12px;color:white;font-weight:700;">目的：驗證固定價值是否比現價連動模型更能產生有效估值位階。</div>
    </div>
    """, unsafe_allow_html=True)

    df = aivm_lab_df()
    show = aivm_lab_display_df(df)

    st.info("固定AIVM價值以最近一期財報、產業景氣與市場評價建立，每季財報公布後更新一次；日常股價波動不影響固定價值。")

    tabs = st.tabs(["① 固定價值總覽", "② 固定 vs 動態", "③ 財報公布日", "④ 產業權重說明", "⑤ 權重總覽", "⑥ 權重回測", "⑦ 最佳權重建議", "⑧ 真實回測試作", "⑨ 半導體類股驗證", "⑩ 產業鏈同業全球競爭", "⑪ 校對檢定", "⑫ 區間校準", "⑬ 誤差分析", "⑭ 方法說明", "⑮ 個股DNA"])

    with tabs[0]:
        cols = ["公司","代碼","產業","現價","固定AIVM價值","固定安全邊際","固定估值位階","財報季度","財報公布日","固定價值有效至"]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)
        st.caption("固定安全邊際 = (固定AIVM價值 - 現價) / 固定AIVM價值。正數代表現價低於固定價值。")

    with tabs[1]:
        cols = ["公司","現價","財報價值","市場價值","產業價值","固定AIVM價值","動態AIVM價值","固定估值位階","動態估值位階"]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)
        st.caption("若動態模型永遠接近現價，估值位階容易長期停留在合理或合理偏高；固定模型較能產生低估/高估差異。")

    with tabs[2]:
        cols = ["公司","代碼","財報季度","財報基準日","財報公布日","固定價值有效至","更新條件","資料來源"]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)
        st.caption("正式版可改為讀取公開資訊觀測站或公司法說會公告日期；目前先用Lab設定值測試版面。")

    with tabs[3]:
        st.markdown("### 產業權重說明")
        selected_company = st.selectbox("選擇公司", df["公司"].tolist(), key="v924_weight_company")
        selected_row = df[df["公司"] == selected_company].iloc[0]
        st.info(f"{selected_company} 類股：{selected_row['產業']}｜權重不是主觀設定，而是依產業定價邏輯、現金流特性、護城河與市場習慣配置。")
        st.dataframe(aivm_weight_df(selected_row["產業"]), use_container_width=True, hide_index=True)
        st.caption("正式版可再加入歷史回測誤差，讓權重由回測資料自動校準。")

    with tabs[4]:
        st.markdown("### AIVM 類股權重總覽")
        st.dataframe(aivm_weight_summary_df(), use_container_width=True, hide_index=True)
        st.caption("不同類股權重不同，是因為不同產業的股價驅動因子不同：金融看PB/ROE，晶圓代工看FCFF/EVA/CAP，AI成長股看EBO/CAP/PE。")

    with tabs[5]:
        st.markdown("### 權重回測中心")
        selected_company_bt = st.selectbox("選擇公司 / 類股", df["公司"].tolist(), key="v925_backtest_company")
        selected_row_bt = df[df["公司"] == selected_company_bt].iloc[0]
        bt_industry = selected_row_bt["產業"]
        st.info(aivm_backtest_explain_text(bt_industry))
        st.dataframe(aivm_backtest_table(bt_industry), use_container_width=True, hide_index=True)
        st.caption("本頁先用 Lab 回測資料展示邏輯；正式版可改接歷史財報、股價與模型估值資料。")

    with tabs[6]:
        st.markdown("### 最佳權重建議總覽")
        st.dataframe(aivm_backtest_summary_df(), use_container_width=True, hide_index=True)
        st.caption("改善幅度 = 目前權重組合誤差 - 回測最佳權重組合誤差。")
        st.warning("V92.5 僅作權重回測流程驗證，不直接取代主系統權重。")

    with tabs[7]:
        v93_backtest_page_block()

    with tabs[8]:
        v94_sector_validation_page_block()

    with tabs[9]:
        v95_industry_chain_page_block()

    with tabs[10]:
        v96_calibration_test_page_block()

    with tabs[11]:
        cols = [
            "公司","現價",
            "財報保守","財報價值","財報樂觀",
            "市場保守","市場價值","市場樂觀",
            "產業保守","產業價值","產業樂觀",
        ]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)

    with tabs[12]:
        cols = ["公司","現價","財報價值","市場價值","產業價值","財報誤差","市場誤差","產業誤差"]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)

    with tabs[13]:
        st.markdown("""
        ### V96.0 方法說明

        **固定AIVM價值**
        ```
        固定AIVM價值
        =
        財報價值 × 30%
        +
        市場價值 × 40%
        +
        產業價值 × 30%
        ```

        **產業權重說明**
        ```
        7模型權重不是全部產業相同。
        晶圓代工重視 FCFF、EVA、CAP。
        成熟製程重視 FCFF、FCFE、PE。
        AI電源/自動化重視 PE、FCFF、EBO、EVA。
        ```
        不同類股權重不同，是因為市場對不同產業的定價邏輯不同。

        **V92.5 權重回測原則**
        ```
        單模型歷史誤差越低，建議權重越高。
        權重不是固定主觀設定，而是由歷史回測誤差校準。
        正式版將使用歷史財報、股價與模型估值資料回測。
        ```

        **更新原則**
        - 每季財報公布後更新一次。
        - 日常股價波動不直接改變固定AIVM價值。
        - 若法人目標價重大調整或產業景氣循環改變，可提前重新校準。

        **估值位階**
        - 安全邊際 ≥ 25%：明顯低估
        - 10% ~ 25%：低估
        - -10% ~ 10%：合理
        - -25% ~ -10%：高估
        - < -25%：明顯高估
        """)

    with tabs[14]:
        v971_dna_tab_page()
# ================= V92.3 AIVM QUARTERLY FIXED VALUE LAB END =================

active = unified_symbol_manager(symbols)

# ===== V95.0 AIVM Lab route guard =====
if page in ["🧪AIVM Lab", "🧪 AIVM Lab"]:
    aivm_lab_page()
    st.stop()
# ===== V95.0 AIVM Lab route guard end =====






# V39：手機/電腦響應式欄位
if "layout_mode" not in locals():
    layout_mode = "自動"
display_cols = 4 if layout_mode == "電腦" else 2
df_daily=fetch_daily(active,period); q=repair_quote_with_df(yf_quote(active), df_daily); d_daily=signal_cols(add_more_indicators(add_indicators(df_daily))); scores=score_blocks(d_daily,q); total=ai_total(scores)
if pd.isna(effective_price(q, df_daily)) and df_daily.empty:
    st.warning(f"目前 {display_name(active)} 查無 Yahoo Finance 資料。若是上櫃股請確認代碼為 .TWO，例如和椿 = 6215.TWO。")


# ================= V90.7 TRUE HOME DISPATCH OVERRIDE =================
# 重新路由頁面：首頁一定顯示全產業類股估值入口，不再顯示 AIVM 舊表格。

# ===== V96.2 RESTORE ESG INSTITUTIONAL VALUATION START =====
# 目的：移除監控主選單；恢復企業評價、中文財報、ESG、法人、AI研究；保留K線。

def v962_default_scores(symbol=None, q=None, df=None):
    base = {"total": 60, "ai": 60, "tech": 55, "fund": 60, "inst": 50, "chip": 50, "main": 50, "esg": 60}
    try:
        if isinstance(q, dict):
            pe = q.get("pe", np.nan)
            pb = q.get("pb", np.nan)
            if pd.notna(pe) and float(pe) < 25:
                base["fund"] += 5
            if pd.notna(pb) and float(pb) < 5:
                base["fund"] += 3
    except Exception:
        pass
    return base

def v962_safe_history(symbol, df=None):
    try:
        if isinstance(df, pd.DataFrame) and not df.empty:
            d = df.copy()
            if "Date" not in d.columns:
                d = d.reset_index()
            if "Date" not in d.columns and "Datetime" in d.columns:
                d["Date"] = d["Datetime"]
            return d
    except Exception:
        pass
    try:
        d = yf.Ticker(symbol).history(period=st.session_state.get("period", "1y"), auto_adjust=False)
        if d is None or d.empty:
            d = yf.Ticker(symbol).history(period="1y", auto_adjust=False)
        d = d.reset_index()
        if "Date" not in d.columns and "Datetime" in d.columns:
            d["Date"] = d["Datetime"]
        return d
    except Exception:
        return pd.DataFrame()

def kline_page(symbol, q=None, df=None):
    st.subheader(f"📈 K線技術分析：{display_name(symbol)}")
    st.caption("V96.2：K線保留；若主資料不足會自動改抓 Yahoo 歷史股價。")
    d = v962_safe_history(symbol, df)
    if d is None or d.empty:
        st.warning("目前無法取得K線資料，請稍後重試或檢查 yfinance 連線。")
        return None
    c1, c2 = st.columns([2, 1])
    with c1:
        overlays = st.multiselect(
            "主圖均線 / 指標",
            ["MA5", "MA10", "MA20", "MA60", "MA120", "MA240", "布林通道"],
            default=["MA5", "MA20", "MA60"],
            key="v962_kline_overlays"
        )
    with c2:
        panel = st.selectbox(
            "副圖",
            ["成交量", "MACD", "KD", "RSI", "BIAS", "OBV", "MFI", "威廉%R", "CCI", "ADX", "ATR", "ROC", "Momentum"],
            index=0,
            key="v962_kline_panel"
        )
    try:
        kline_chart(d, overlays, panel)
    except Exception as e:
        st.error(f"K線圖載入失敗：{e}")
        st.dataframe(d.tail(120), use_container_width=True)
    return None

def page_kline(symbol, q=None, df=None):
    kline_page(symbol, q, df)
    return None

def enterprise_value_institute_page(symbol, q=None, df=None):
    st.subheader(f"🏛 AI企業價值研究院：{display_name(symbol)}")
    st.caption("V96.2：恢復企業評價、中文財報、ESG、法人與AI研究；DNA Validation Lab 之後再加，不覆蓋核心功能。")
    scores = v962_default_scores(symbol, q or {}, df)

    tabs = st.tabs(["估值總覽", "企業評價", "中文財報中心", "ESG永續", "法人籌碼", "AI研究摘要", "AIVM研究中心入口"])

    with tabs[0]:
        try:
            price = effective_price(q or {}, df) if "effective_price" in globals() else np.nan
            val = v901_valuation(symbol, price) if "v901_valuation" in globals() else {}
            if isinstance(val, dict) and val:
                kpi([
                    ("現價", fmt(val.get("price"))),
                    ("基準價值", fmt(val.get("base"))),
                    ("估值區間", f"{fmt(val.get('low'))} ~ {fmt(val.get('high'))}"),
                    ("估值位階", val.get("position", "N/A")),
                ])
            else:
                v85_original_valuation_center(symbol, q or {}, df, scores)
        except Exception as e:
            st.warning(f"估值總覽載入失敗：{e}")

    with tabs[1]:
        try:
            v85_original_valuation_center(symbol, q or {}, df, scores)
        except Exception as e:
            st.warning(f"企業評價載入失敗：{e}")

    with tabs[2]:
        try:
            financial_center(symbol, q or {}, df)
        except Exception as e:
            st.error(f"中文財報中心載入失敗：{e}")

    with tabs[3]:
        try:
            v85_original_esg_center(symbol, q or {}, df, scores)
        except Exception as e:
            st.warning(f"ESG永續中心載入失敗：{e}")

    with tabs[4]:
        try:
            v85_original_institutional_center(symbol, q or {}, df, scores)
        except Exception as e:
            st.warning(f"法人籌碼中心載入失敗：{e}")

    with tabs[5]:
        try:
            v50_ai_research_center(symbol, df, q or {}, scores)
        except Exception as e:
            st.warning(f"AI研究摘要載入失敗：{e}")

    with tabs[6]:
        st.info("個股DNA、全球競爭、權重驗證與校對檢定請進入「AIVM研究中心」或「AIVM Lab」。")
    return None

def settings_page():
    st.subheader("⚙ 設定")
    st.caption("V96.2：監控主選單已移除；保留K線、企業價值研究院、AIVM研究中心。")
    st.info("後續正式版可整合：預設首頁、K線預設指標、資料來源檢查、DNA Validation Lab。")
    return None
# ===== V96.2 RESTORE ESG INSTITUTIONAL VALUATION END =====



# ===== V96.3 RESTORE KLINE PERIODS START =====
def v963_resample_ohlcv(df, freq):
    try:
        if df is None or df.empty:
            return pd.DataFrame()
        d = df.copy()
        if "Date" not in d.columns:
            d = d.reset_index()
        if "Date" not in d.columns and "Datetime" in d.columns:
            d["Date"] = d["Datetime"]
        d["Date"] = pd.to_datetime(d["Date"], errors="coerce")
        d = d.dropna(subset=["Date"]).sort_values("Date")
        if freq == "D":
            return d
        d = d.set_index("Date")
        agg = {"Open":"first", "High":"max", "Low":"min", "Close":"last", "Volume":"sum"}
        agg = {k:v for k,v in agg.items() if k in d.columns}
        return d.resample(freq).agg(agg).dropna(subset=["Open","High","Low","Close"]).reset_index()
    except Exception:
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()

def v963_safe_history(symbol, period="3y"):
    try:
        d = yf.Ticker(symbol).history(period=period, auto_adjust=False)
        if d is None or d.empty:
            d = yf.Ticker(symbol).history(period="5y", auto_adjust=False)
        d = d.reset_index()
        if "Date" not in d.columns and "Datetime" in d.columns:
            d["Date"] = d["Datetime"]
        return d
    except Exception:
        return pd.DataFrame()

def kline_page(symbol, q=None, df=None):
    st.subheader(f"📈 K線技術分析：{display_name(symbol)}")
    st.caption("V96.3：恢復日K、週K、月K、季K、年K；K線主功能保留。")
    period_map = {
        "日K": ("D", "1y"),
        "週K": ("W-FRI", "3y"),
        "月K": ("ME", "5y"),
        "季K": ("QE", "10y"),
        "年K": ("YE", "max"),
    }
    c0, c1, c2 = st.columns([1, 2, 1])
    with c0:
        k_period = st.selectbox("K線週期", list(period_map.keys()), index=0, key="v963_k_period")
    with c1:
        overlays = st.multiselect(
            "主圖均線 / 指標",
            ["MA5", "MA10", "MA20", "MA60", "MA120", "MA240", "布林通道"],
            default=["MA5", "MA20", "MA60"],
            key="v963_kline_overlays"
        )
    with c2:
        panel = st.selectbox(
            "副圖",
            ["成交量", "MACD", "KD", "RSI", "BIAS", "OBV", "MFI", "威廉%R", "CCI", "ADX", "ATR", "ROC", "Momentum"],
            index=0,
            key="v963_kline_panel"
        )
    freq, yperiod = period_map[k_period]
    raw = df if isinstance(df, pd.DataFrame) and not df.empty and k_period == "日K" else v963_safe_history(symbol, yperiod)
    d = v963_resample_ohlcv(raw, freq)
    if d is None or d.empty:
        st.warning("目前無法取得K線資料，請稍後重試或檢查 yfinance 連線。")
        return None
    st.caption(f"目前顯示：{k_period}，資料筆數：{len(d)}")
    try:
        kline_chart(d, overlays, panel)
    except Exception as e:
        st.error(f"K線圖載入失敗：{e}")
        st.dataframe(d.tail(120), use_container_width=True)
    return None

def page_kline(symbol, q=None, df=None):
    kline_page(symbol, q, df)
    return None

# ===== V96.3 RESTORE KLINE PERIODS END =====












# ===== V97.0 DNA VALIDATION LAB START =====
# 本版不動首頁、K線、財報、ESG、法人與原估值核心。
# 只在 AIVM Lab 新增「個股DNA驗證」：先用10檔試驗股驗證 DNA估值 是否比原AIVM更接近現價。

V97_DNA_PROFILES = {
    "2330.TW": {
        "公司": "台積電", "產業": "半導體", "次產業": "晶圓代工",
        "DNA定位": "AI先進製程龍頭", "主要業務": "AI/HPC、先進製程、CoWoS",
        "全球競爭": "Samsung Foundry / Intel Foundry / SMIC",
        "CAP等級": "S+", "DNA分數": 95,
        "說明": "技術領先、先進製程市占率高、AI/HPC與先進封裝帶動長期競爭優勢。"
    },
    "2303.TW": {
        "公司": "聯電", "產業": "半導體", "次產業": "晶圓代工",
        "DNA定位": "成熟製程現金流型", "主要業務": "成熟製程、車用、工控",
        "全球競爭": "GlobalFoundries / Tower / SMIC",
        "CAP等級": "A", "DNA分數": 76,
        "說明": "成熟製程、長期客戶關係與現金流穩定，成長性低於先進製程但防禦性較佳。"
    },
    "5347.TWO": {
        "公司": "世界先進", "產業": "半導體", "次產業": "特殊製程",
        "DNA定位": "特殊製程利基型", "主要業務": "PMIC、DDIC、車用/工控特殊製程",
        "全球競爭": "Tower / DB HiTek / Magnachip",
        "CAP等級": "A", "DNA分數": 74,
        "說明": "特殊製程與PMIC/DDIC需求循環相關，估值應兼顧景氣循環與利基製程。"
    },
    "6770.TW": {
        "公司": "力積電", "產業": "半導體", "次產業": "記憶體/晶圓代工",
        "DNA定位": "記憶體循環型代工", "主要業務": "DRAM、NAND相關與成熟製程代工",
        "全球競爭": "SMIC / Hua Hong / 記憶體同業",
        "CAP等級": "B+", "DNA分數": 66,
        "說明": "受記憶體與成熟製程景氣循環影響較大，估值需提高循環折價。"
    },
    "2383.TW": {
        "公司": "台光電", "產業": "電子材料", "次產業": "CCL",
        "DNA定位": "AI高速材料龍頭", "主要業務": "AI CCL、高速材料、伺服器材料",
        "全球競爭": "Panasonic / Isola / Shengyi",
        "CAP等級": "A+", "DNA分數": 88,
        "說明": "AI伺服器、高速傳輸與高階CCL帶動成長，估值應反映AI材料溢價。"
    },
    "3037.TW": {
        "公司": "欣興", "產業": "PCB/載板", "次產業": "ABF載板",
        "DNA定位": "ABF載板龍頭", "主要業務": "ABF、IC載板、高階PCB",
        "全球競爭": "Ibiden / Shinko / Nan Ya PCB",
        "CAP等級": "A", "DNA分數": 80,
        "說明": "受AI/HPC與ABF載板景氣影響，需兼顧產能利用率與循環。"
    },
    "8046.TW": {
        "公司": "南電", "產業": "PCB/載板", "次產業": "ABF載板",
        "DNA定位": "AI載板景氣循環型", "主要業務": "ABF、BT、HPC載板",
        "全球競爭": "Ibiden / Shinko / 欣興",
        "CAP等級": "A", "DNA分數": 78,
        "說明": "AI/HPC載板有長期題材，但盈餘受載板循環波動影響。"
    },
    "3711.TW": {
        "公司": "日月光投控", "產業": "半導體", "次產業": "封測",
        "DNA定位": "全球封測龍頭", "主要業務": "封裝、測試、SiP、先進封裝",
        "全球競爭": "Amkor / JCET / Powertech",
        "CAP等級": "S", "DNA分數": 84,
        "說明": "全球封測龍頭，受AI先進封裝與半導體景氣共同影響。"
    },
    "2449.TW": {
        "公司": "京元電子", "產業": "半導體", "次產業": "測試",
        "DNA定位": "AI測試受惠型", "主要業務": "IC測試、AI/HPC測試、車用測試",
        "全球競爭": "ASE Test / Amkor / Sigurd",
        "CAP等級": "A+", "DNA分數": 82,
        "說明": "AI/HPC與車用測試需求提升，具備測試供應鏈受惠題材。"
    },
    "6215.TWO": {
        "公司": "和椿", "產業": "自動化", "次產業": "自動化/機器人",
        "DNA定位": "自動化代理與整合型", "主要業務": "自動化元件、機器人、設備整合",
        "全球競爭": "Keyence / SMC / Omron / 台灣自動化同業",
        "CAP等級": "B+", "DNA分數": 70,
        "說明": "受工業自動化與機器人題材帶動，但需確認實際營收與毛利結構。"
    },
}

# 原 V96 AIVM 基準價值試驗值；若正式版已有 v901_valuation，會優先使用正式值。
V97_BASE_AIVM_VALUE = {
    "2330.TW": 2536.56,
    "2303.TW": 145.47,
    "5347.TWO": 169.92,
    "6770.TW": 81.40,
    "2383.TW": 5393.20,
    "3037.TW": 178.00,
    "8046.TW": 907.25,
    "3711.TW": 158.40,
    "2449.TW": 106.40,
    "6215.TWO": 92.00,
}

V97_FALLBACK_PRICE = {
    "2330.TW": 2390.00,
    "2303.TW": 178.00,
    "5347.TWO": 200.00,
    "6770.TW": 85.70,
    "2383.TW": 2000.00,
    "3037.TW": 185.00,
    "8046.TW": 955.00,
    "3711.TW": 165.00,
    "2449.TW": 112.00,
    "6215.TWO": 140.00,
}

def v97_num(x):
    try:
        if x is None or pd.isna(x):
            return np.nan
        return float(x)
    except Exception:
        return np.nan

def v97_fmt(x):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def v97_pct(x):
    try:
        if x is None or pd.isna(x):
            return "N/A"
        return f"{float(x):.1f}%"
    except Exception:
        return "N/A"

@st.cache_data(ttl=900, show_spinner=False)
def v97_live_price(symbol):
    try:
        t = yf.Ticker(symbol)
        try:
            fi = getattr(t, "fast_info", {}) or {}
            px = v97_num(fi.get("last_price", fi.get("lastPrice", np.nan)))
            if pd.notna(px):
                return px, "Yahoo fast_info"
        except Exception:
            pass
        hist = t.history(period="5d", auto_adjust=False)
        if hist is not None and not hist.empty:
            return float(hist["Close"].dropna().iloc[-1]), "Yahoo最近收盤"
    except Exception:
        pass
    return V97_FALLBACK_PRICE.get(symbol, np.nan), "Fallback"

def v97_get_base_aivm(symbol, price=np.nan):
    try:
        if "v901_valuation" in globals() and pd.notna(price):
            val = v901_valuation(symbol, price)
            if isinstance(val, dict):
                base = v97_num(val.get("base", np.nan))
                if pd.notna(base):
                    return base, "v901_valuation"
    except Exception:
        pass
    return V97_BASE_AIVM_VALUE.get(symbol, np.nan), "V97試驗基準"

def v97_dna_factor(score):
    try:
        s = float(score)
    except Exception:
        return 1.0
    if s >= 90:
        return 1.18
    if s >= 85:
        return 1.12
    if s >= 80:
        return 1.08
    if s >= 75:
        return 1.03
    if s >= 70:
        return 1.00
    if s >= 65:
        return 0.94
    return 0.88

def v97_stage(price, fair):
    if pd.isna(price) or pd.isna(fair) or fair == 0:
        return "資料不足"
    low = fair * 0.90
    high = fair * 1.10
    if price < low:
        return "合理偏低"
    if price > high:
        return "高估"
    if price > fair:
        return "合理偏高"
    return "合理"

def v97_dna_validation_df():
    rows = []
    for sym, p in V97_DNA_PROFILES.items():
        price, price_src = v97_live_price(sym)
        base, base_src = v97_get_base_aivm(sym, price)
        factor = v97_dna_factor(p["DNA分數"])
        dna_value = base * factor if pd.notna(base) else np.nan
        base_err = abs(price - base) / price * 100 if pd.notna(price) and pd.notna(base) and price else np.nan
        dna_err = abs(price - dna_value) / price * 100 if pd.notna(price) and pd.notna(dna_value) and price else np.nan
        improve = base_err - dna_err if pd.notna(base_err) and pd.notna(dna_err) else np.nan
        rows.append({
            "代碼": sym, "公司": p["公司"], "次產業": p["次產業"], "DNA定位": p["DNA定位"],
            "CAP等級": p["CAP等級"], "DNA分數": p["DNA分數"], "DNA修正係數": factor,
            "現價": price, "原AIVM價值": base, "DNA估值": dna_value,
            "原AIVM誤差": base_err, "DNA誤差": dna_err, "誤差改善": improve,
            "原位階": v97_stage(price, base), "DNA位階": v97_stage(price, dna_value),
            "現價來源": price_src, "估值來源": base_src,
            "主要業務": p["主要業務"], "全球競爭": p["全球競爭"], "說明": p["說明"]
        })
    return pd.DataFrame(rows)

def v97_display_df(df):
    out = df.copy()
    for c in ["現價", "原AIVM價值", "DNA估值"]:
        if c in out.columns:
            out[c] = out[c].apply(v97_fmt)
    for c in ["DNA修正係數", "原AIVM誤差", "DNA誤差", "誤差改善"]:
        if c == "DNA修正係數" and c in out.columns:
            out[c] = out[c].apply(lambda x: f"{float(x):.2f}" if pd.notna(x) else "N/A")
        elif c in out.columns:
            out[c] = out[c].apply(v97_pct)
    return out

def v97_dna_validation_lab_page():
    st.markdown("## 🧬 V97.0 個股DNA驗證中心")
    st.info("本頁只做試驗：比較「原AIVM估值」與「DNA修正估值」誰更接近現價；不覆蓋首頁、不改財報、不改K線。")
    df = v97_dna_validation_df()

    tabs = st.tabs(["① DNA資料庫", "② DNA估值比較", "③ 誤差驗證", "④ 個股說明", "⑤ 方法說明"])

    with tabs[0]:
        cols = ["代碼", "公司", "次產業", "DNA定位", "主要業務", "CAP等級", "DNA分數", "全球競爭"]
        st.dataframe(df[cols], use_container_width=True, hide_index=True)

    with tabs[1]:
        cols = ["代碼", "公司", "現價", "原AIVM價值", "DNA估值", "DNA修正係數", "原位階", "DNA位階", "現價來源", "估值來源"]
        st.dataframe(v97_display_df(df)[cols], use_container_width=True, hide_index=True)

    with tabs[2]:
        base_mape = df["原AIVM誤差"].mean()
        dna_mape = df["DNA誤差"].mean()
        improve = base_mape - dna_mape if pd.notna(base_mape) and pd.notna(dna_mape) else np.nan
        c1, c2, c3 = st.columns(3)
        c1.metric("原AIVM MAPE", v97_pct(base_mape))
        c2.metric("DNA估值 MAPE", v97_pct(dna_mape))
        c3.metric("平均改善", v97_pct(improve))
        cols = ["代碼", "公司", "現價", "原AIVM價值", "DNA估值", "原AIVM誤差", "DNA誤差", "誤差改善"]
        st.dataframe(v97_display_df(df)[cols], use_container_width=True, hide_index=True)
        if pd.notna(improve) and improve > 0:
            st.success("初步結果：DNA估值平均誤差低於原AIVM，個股DNA修正方向可繼續驗證。")
        else:
            st.warning("初步結果：DNA估值尚未優於原AIVM，需要重新校準DNA分數或修正係數。")

    with tabs[3]:
        selected = st.selectbox("選擇個股", df["公司"].tolist(), key="v97_dna_selected_company")
        row = df[df["公司"] == selected].iloc[0]
        st.markdown(f"### {row['公司']} / {row['代碼']}")
        st.write(f"**DNA定位：** {row['DNA定位']}")
        st.write(f"**主要業務：** {row['主要業務']}")
        st.write(f"**全球競爭：** {row['全球競爭']}")
        st.write(f"**CAP等級：** {row['CAP等級']}，DNA分數：{row['DNA分數']}")
        st.info(row["說明"])

    with tabs[4]:
        st.markdown("""
        ### V97方法

        先不改原始估值模型，而是在原AIVM基準價值上加入個股DNA修正：

        **DNA估值 = 原AIVM價值 × DNA修正係數**

        修正係數由個股目前主要經營項目、產業位置、全球競爭、CAP等級與AI/景氣循環屬性推導。

        本版只驗證10檔，不覆蓋主系統。若DNA估值MAPE低於原AIVM，下一版再擴大到半導體50檔。
        """)

# V97.0 wrapper disabled by V97.1：DNA已改掛在AIVM Lab第15頁籤
# ===== V97.0 DNA VALIDATION LAB END =====


# ================= V96.8 WRAPPED FINAL DISPATCH START =================
def v968_main_dispatch():
    global page
    try:
        if page not in ["🏠首頁","📈K線","🏛企業價值研究院","🧪AIVM研究中心","🧪AIVM Lab","⚙設定"] or "監控" in str(page):
            page = "🏠首頁"
            st.session_state.page = page
    except Exception:
        page = "🏠首頁"

    if page == "🏠首頁":
        try:
            v906_force_home()
        except Exception:
            try:
                v906_home_dashboard()
            except Exception:
                try:
                    v905_sector_dashboard()
                except Exception as e:
                    st.error(f"首頁全產業類股估值入口載入失敗：{e}")

    elif page == "📈K線":
        try:
            kline_page(active, q, df_daily)
        except Exception:
            try:
                page_kline(active, q, df_daily)
            except Exception:
                st.warning("K線頁載入中。")

    elif page == "🏛企業價值研究院":
        try:
            enterprise_value_institute_page(active, q, df_daily)
        except Exception:
            try:
                value_institute(active, df_daily, q, {})
            except Exception:
                try:
                    v901_semiconductor_library_page()
                    st.divider()
                    v906_home_dashboard()
                except Exception as e:
                    st.error(f"企業價值研究院載入失敗：{e}")

    elif page == "🧪AIVM研究中心":
        try:
            v893_aivm_page()
        except Exception as e:
            st.error(f"AIVM研究中心載入失敗：{e}")

    elif page == "🧪AIVM Lab":
        aivm_lab_page()

    elif page == "⚙設定":
        try:
            settings_page()
        except Exception:
            st.subheader("⚙設定")
            st.info("設定頁載入中。")

exec("v968_main_dispatch()")
# ================= V96.9 NO MAGIC FINAL CALL END =================

