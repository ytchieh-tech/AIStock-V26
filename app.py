# -*- coding: utf-8 -*-
"""
Flagship AI Stock Platform V24 Enterprise Edition
乾淨重建版：避免 V23 函式拼接錯誤

功能：
- 中文 / 代碼 / Yahoo 代號智慧搜尋
- 世界先進、和椿等上櫃股票自動轉 .TWO
- K線主圖技術指標疊加
- 副圖技術指標選擇
- 技術選股器
- 技術面綜合評分
- 三大法人買賣超
- 主力進出價量估算
- ESG 市場評估
- 防 N/A 市場綜合估值
- PE / Forward PE / PEG / PB / Graham / DDM / DCF / EV EBITDA / EVA / EBO / FCFF / FCFE
- XGBoost / 趨勢回歸
"""

import warnings
warnings.filterwarnings("ignore")

import re
from datetime import datetime, timedelta
from io import StringIO

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

try:
    import yfinance as yf
except Exception:
    yf = None

try:
    import requests
except Exception:
    requests = None

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LinearRegression
    SKLEARN_OK = True
except Exception:
    SKLEARN_OK = False

try:
    from xgboost import XGBRegressor
    XGBOOST_OK = True
except Exception:
    XGBOOST_OK = False


st.set_page_config(
    page_title="旗艦版 AI 股票平台 V25 Mobile Professional Edition",
    page_icon="📈",
    layout="wide",
)

st.title("📊 旗艦版 AI 股票平台 V25 Mobile Professional Edition")
st.caption("V25：手機響應式介面 + Android WebView + 智慧搜尋 + 技術分析 + 籌碼 + ESG + 估值 + AI 預測")


st.markdown("""
<style>
/* V25 Mobile Professional responsive layout */
.block-container {
    padding-top: 1.2rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 1500px;
}
[data-testid="stMetric"] {
    background: rgba(240, 242, 246, 0.65);
    border-radius: 12px;
    padding: 10px 12px;
    border: 1px solid rgba(200, 200, 200, 0.35);
}
[data-testid="stSidebar"] {
    min-width: 310px;
}
.stButton > button {
    width: 100%;
    border-radius: 12px;
    font-weight: 700;
}
@media (max-width: 768px) {
    .block-container {
        padding-left: 0.55rem;
        padding-right: 0.55rem;
        padding-top: 0.7rem;
    }
    h1 {
        font-size: 1.35rem !important;
        line-height: 1.35 !important;
    }
    h2, h3 {
        font-size: 1.05rem !important;
    }
    [data-testid="stMetric"] {
        padding: 8px 8px;
        margin-bottom: 6px;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.05rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
    }
    .stDataFrame {
        font-size: 0.78rem !important;
    }
    .stPlotlyChart {
        overflow-x: auto;
    }
}
/* Make charts easier to swipe on mobile */
.js-plotly-plot .plotly .modebar {
    right: 4px !important;
}
</style>
""", unsafe_allow_html=True)



# ============================================================
# 股票搜尋
# ============================================================

TW_STOCKS = {
    "台積電": "2330.TW", "台積": "2330.TW", "TSMC": "2330.TW",
    "聯發科": "2454.TW", "發哥": "2454.TW",
    "鴻海": "2317.TW", "富士康": "2317.TW",
    "台達電": "2308.TW",
    "聯電": "2303.TW", "UMC": "2303.TW",
    "廣達": "2382.TW", "緯創": "3231.TW",
    "技嘉": "2376.TW", "微星": "2377.TW",
    "華碩": "2357.TW", "宏碁": "2353.TW",
    "和碩": "4938.TW", "仁寶": "2324.TW", "英業達": "2356.TW",
    "大立光": "3008.TW", "日月光": "3711.TW", "日月光投控": "3711.TW",
    "台光電": "2383.TW", "金像電": "2368.TW", "欣興": "3037.TW", "南電": "8046.TW",
    "凌陽": "2401.TW",
    "台塑": "1301.TW", "南亞": "1303.TW", "中鋼": "2002.TW",
    "長榮": "2603.TW", "陽明": "2609.TW", "萬海": "2615.TW",
    "中華電": "2412.TW", "台灣大": "3045.TW", "遠傳": "4904.TW",
    "富邦金": "2881.TW", "國泰金": "2882.TW", "中信金": "2891.TW",
    "兆豐金": "2886.TW", "玉山金": "2884.TW", "第一金": "2892.TW",
    "合庫金": "5880.TW", "元大金": "2885.TW", "台新金": "2887.TW",
    "永豐金": "2890.TW", "開發金": "2883.TW",
    "群創": "3481.TW", "友達": "2409.TW",
    "瑞昱": "2379.TW", "創意": "3443.TW", "世芯": "3661.TW",
    "矽力": "6415.TW", "祥碩": "5269.TW", "力積電": "6770.TW",

    # 上櫃
    "世界先進": "5347.TWO", "世界": "5347.TWO", "VIS": "5347.TWO",
    "世界先進積體電路": "5347.TWO",
    "和椿": "6215.TWO", "和椿科技": "6215.TWO",
    "穩懋": "3105.TWO", "宏捷科": "8086.TWO", "威剛": "3260.TWO",
    "台燿": "6274.TWO",
}

TWO_CODES = {"5347", "6215", "3105", "8086", "3260", "6274"}
TW_CODES = {
    "2330", "2454", "2317", "2308", "2303", "2382", "3231", "2376", "2377",
    "2357", "2353", "4938", "2324", "2356", "3008", "3711", "2383", "2368",
    "3037", "8046", "2401", "1301", "1303", "2002", "2603", "2609", "2615",
    "2412", "3045", "4904", "2881", "2882", "2891", "2886", "2884", "2892",
    "5880", "2885", "2887", "2890", "2883", "3481", "2409", "2379", "3443",
    "3661", "6415", "5269", "6770",
}


def smart_resolve_symbol(query: str):
    q = str(query).strip()
    if not q:
        return "2330.TW", "台積電 / 2330.TW", []

    q_upper = q.upper().replace(" ", "")

    if q in TW_STOCKS:
        return TW_STOCKS[q], f"{q} / {TW_STOCKS[q]}", []
    if q_upper in TW_STOCKS:
        return TW_STOCKS[q_upper], f"{q_upper} / {TW_STOCKS[q_upper]}", []

    if re.match(r"^\d{4}\.(TW|TWO)$", q_upper):
        return q_upper, q_upper, []

    if re.match(r"^\d{4}$", q_upper):
        if q_upper in TWO_CODES:
            return f"{q_upper}.TWO", f"{q_upper}.TWO（上櫃）", []
        if q_upper in TW_CODES:
            return f"{q_upper}.TW", f"{q_upper}.TW（上市）", []
        return f"{q_upper}.TW", f"{q_upper}.TW（未知，若查無自動試 .TWO）", []

    suggestions = []
    for name, sym in TW_STOCKS.items():
        if q in name or name in q or q_upper in name.upper() or q_upper in sym:
            suggestions.append(f"{name} → {sym}")
    if suggestions:
        sym = suggestions[0].split("→")[-1].strip()
        return sym, suggestions[0], suggestions[:10]

    return q_upper, q_upper, []


def fallback_symbol(symbol: str):
    s = str(symbol).upper()
    if re.match(r"^\d{4}\.TW$", s):
        return s.replace(".TW", ".TWO")
    if re.match(r"^\d{4}\.TWO$", s):
        return s.replace(".TWO", ".TW")
    return None


def pure_stock_code(symbol: str):
    s = str(symbol).upper()
    m = re.match(r"^(\d{4})\.(TW|TWO)$", s)
    if m:
        return m.group(1)
    return s.replace(".TW", "").replace(".TWO", "")


def market_type(symbol: str):
    return "TWO" if str(symbol).upper().endswith(".TWO") else "TW"


# ============================================================
# 基本資料
# ============================================================

def safe_float(x, default=np.nan):
    try:
        if x is None:
            return default
        if isinstance(x, str):
            x = x.replace(",", "").replace('"', "").strip()
        return float(x)
    except Exception:
        return default


@st.cache_data(show_spinner=False, ttl=1800)
def fetch_price(symbol: str, period: str = "5y"):
    if yf is None:
        raise RuntimeError("尚未安裝 yfinance")

    for sym in [symbol, fallback_symbol(symbol)]:
        if not sym:
            continue
        try:
            df = yf.Ticker(sym).history(period=period)
            if df is not None and not df.empty:
                df = df.reset_index()
                if "Datetime" in df.columns and "Date" not in df.columns:
                    df = df.rename(columns={"Datetime": "Date"})
                df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
                for c in ["Open", "High", "Low", "Close", "Volume"]:
                    if c not in df.columns:
                        df[c] = np.nan
                return df[["Date", "Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"]), sym
        except Exception:
            pass

    return pd.DataFrame(), symbol


@st.cache_data(show_spinner=False, ttl=1800)
def fetch_market_inputs(symbol: str):
    result = {}
    if yf is None:
        return result

    for sym in [symbol, fallback_symbol(symbol)]:
        if not sym:
            continue
        try:
            info = yf.Ticker(sym).info or {}
            result = {
                "resolved_symbol": sym,
                "market_price": safe_float(info.get("currentPrice", info.get("regularMarketPrice"))),
                "trailing_eps": safe_float(info.get("trailingEps")),
                "forward_eps": safe_float(info.get("forwardEps")),
                "book_value": safe_float(info.get("bookValue")),
                "dividend_rate": safe_float(info.get("dividendRate")),
                "shares_outstanding": safe_float(info.get("sharesOutstanding")),
                "free_cashflow": safe_float(info.get("freeCashflow")),
                "ebitda": safe_float(info.get("ebitda")),
                "total_cash": safe_float(info.get("totalCash")),
                "total_debt": safe_float(info.get("totalDebt")),
                "return_on_equity": safe_float(info.get("returnOnEquity")),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
            }
            return result
        except Exception:
            pass
    return result


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_financials(symbol: str):
    if yf is None:
        return pd.DataFrame()

    for sym in [symbol, fallback_symbol(symbol)]:
        if not sym:
            continue
        try:
            ticker = yf.Ticker(sym)
            fin = ticker.quarterly_financials.T
            bal = ticker.quarterly_balance_sheet.T
            if fin.empty or bal.empty:
                continue
            df = fin.merge(bal, left_index=True, right_index=True, how="inner")
            df = df.reset_index().rename(columns={"index": "Date"})
            df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)

            revenue_col = next((c for c in ["Total Revenue", "Revenue"] if c in df.columns), None)
            ni_col = next((c for c in ["Net Income", "NetIncome"] if c in df.columns), None)
            asset_col = next((c for c in ["Total Assets", "TotalAssets"] if c in df.columns), None)
            liab_col = next((c for c in ["Total Liab", "Total Liabilities Net Minority Interest", "Total Liabilities"] if c in df.columns), None)

            if not all([revenue_col, ni_col, asset_col, liab_col]):
                continue

            equity = df[asset_col] - df[liab_col]
            df["ROA"] = df[ni_col] / df[asset_col].replace(0, np.nan)
            df["ROE"] = df[ni_col] / equity.replace(0, np.nan)
            df["Debt_Ratio"] = df[liab_col] / df[asset_col].replace(0, np.nan)
            df["Profit_Margin"] = df[ni_col] / df[revenue_col].replace(0, np.nan)

            out = df[["Date", revenue_col, ni_col, "ROA", "ROE", "Debt_Ratio", "Profit_Margin"]].copy()
            out = out.rename(columns={revenue_col: "Revenue", ni_col: "Net_Income"})
            return out
        except Exception:
            pass

    return pd.DataFrame()


# ============================================================
# 產業平均參數 / ESG
# ============================================================

MARKET_AVG_PRESETS = {
    "Semiconductors": {
        "target_pe": 22.0, "forward_pe": 24.0, "peg_target": 1.2,
        "target_pb": 3.0, "ev_ebitda": 14.0,
        "required_return": 10.0, "discount_rate": 10.0,
        "terminal_growth": 2.5, "eps_growth": 12.0,
        "fcf_growth": 6.0, "dividend_growth": 3.0,
    },
    "Technology Hardware": {
        "target_pe": 18.0, "forward_pe": 20.0, "peg_target": 1.1,
        "target_pb": 2.5, "ev_ebitda": 12.0,
        "required_return": 10.5, "discount_rate": 10.5,
        "terminal_growth": 2.0, "eps_growth": 8.0,
        "fcf_growth": 5.0, "dividend_growth": 2.0,
    },
    "Financial Services": {
        "target_pe": 12.0, "forward_pe": 12.5, "peg_target": 1.0,
        "target_pb": 1.2, "ev_ebitda": 8.0,
        "required_return": 9.0, "discount_rate": 9.0,
        "terminal_growth": 1.5, "eps_growth": 5.0,
        "fcf_growth": 3.0, "dividend_growth": 2.0,
    },
    "Industrials": {
        "target_pe": 18.0, "forward_pe": 19.0, "peg_target": 1.1,
        "target_pb": 2.0, "ev_ebitda": 11.0,
        "required_return": 10.0, "discount_rate": 10.0,
        "terminal_growth": 2.0, "eps_growth": 7.0,
        "fcf_growth": 5.0, "dividend_growth": 2.0,
    },
    "Default": {
        "target_pe": 18.0, "forward_pe": 20.0, "peg_target": 1.0,
        "target_pb": 2.0, "ev_ebitda": 12.0,
        "required_return": 10.0, "discount_rate": 10.0,
        "terminal_growth": 2.0, "eps_growth": 8.0,
        "fcf_growth": 5.0, "dividend_growth": 2.0,
    },
}

TW_INDUSTRY_HINTS = {
    "2330.TW": "Semiconductors", "2454.TW": "Semiconductors",
    "2303.TW": "Semiconductors", "5347.TWO": "Semiconductors",
    "6770.TW": "Semiconductors", "3711.TW": "Semiconductors",
    "6215.TWO": "Industrials",
    "2308.TW": "Technology Hardware", "2317.TW": "Technology Hardware",
    "2382.TW": "Technology Hardware", "3231.TW": "Technology Hardware",
    "2412.TW": "Communication Services",
    "2881.TW": "Financial Services", "2882.TW": "Financial Services",
    "2891.TW": "Financial Services",
}

ESG_MARKET_PRESETS = {
    "Semiconductors": {"E": 78, "S": 76, "G": 82, "reason": "半導體業通常具備較完整氣候、能源、供應鏈與治理揭露。"},
    "Technology Hardware": {"E": 74, "S": 76, "G": 80, "reason": "電子硬體業重視供應鏈、職安與客戶責任。"},
    "Financial Services": {"E": 70, "S": 78, "G": 84, "reason": "金融業治理、法遵與風控權重較高。"},
    "Industrials": {"E": 72, "S": 74, "G": 78, "reason": "工業與自動化企業受能源效率與職安管理影響。"},
    "Default": {"E": 70, "S": 72, "G": 76, "reason": "採用一般上市櫃公司市場平均 ESG 分數。"},
}

ESG_STOCK_OVERRIDES = {
    "2330.TW": {"E": 88, "S": 84, "G": 90, "reason": "大型半導體龍頭，永續揭露與治理通常優於市場平均。"},
    "2454.TW": {"E": 82, "S": 80, "G": 86, "reason": "大型 IC 設計公司，治理與人才管理通常高於產業平均。"},
    "2303.TW": {"E": 80, "S": 78, "G": 82, "reason": "半導體製造公司，能源與水資源管理權重高。"},
    "5347.TWO": {"E": 78, "S": 76, "G": 82, "reason": "世界先進屬半導體成熟製程，採半導體中高 ESG 市場評估。"},
    "6215.TWO": {"E": 74, "S": 73, "G": 78, "reason": "自動化設備公司，受益節能與智慧製造題材。"},
}


def detect_industry_group(symbol, market_info):
    resolved = market_info.get("resolved_symbol", symbol)
    if resolved in TW_INDUSTRY_HINTS:
        return TW_INDUSTRY_HINTS[resolved]

    text = (str(market_info.get("sector", "")) + " " + str(market_info.get("industry", ""))).lower()
    if "semiconductor" in text:
        return "Semiconductors"
    if "hardware" in text or "electronics" in text:
        return "Technology Hardware"
    if "financial" in text or "bank" in text:
        return "Financial Services"
    if "industrial" in text or "machinery" in text or "automation" in text:
        return "Industrials"
    return "Default"


def get_market_average_params(symbol, market_info):
    group = detect_industry_group(symbol, market_info)
    p = MARKET_AVG_PRESETS.get(group, MARKET_AVG_PRESETS["Default"]).copy()
    p["industry_group"] = group
    p["sector"] = market_info.get("sector", "")
    p["industry"] = market_info.get("industry", "")
    return p


def get_market_esg_scores(symbol, industry_group, resolved_symbol=""):
    sym = resolved_symbol or symbol
    if sym in ESG_STOCK_OVERRIDES:
        d = ESG_STOCK_OVERRIDES[sym].copy()
        d["source"] = "個股市場覆蓋值"
        return d
    d = ESG_MARKET_PRESETS.get(industry_group, ESG_MARKET_PRESETS["Default"]).copy()
    d["source"] = "產業市場平均值"
    return d


def keyword_score(text):
    text = text or ""
    keywords = {
        "E": ["碳", "溫室氣體", "再生能源", "節能", "減碳", "TCFD", "ISO 14001", "水資源", "廢棄物", "綠電"],
        "S": ["員工", "職安", "人權", "供應鏈", "客戶", "公益", "多元", "訓練", "安全衛生"],
        "G": ["董事", "獨立董事", "審計", "薪酬", "風險管理", "誠信", "法遵", "資安", "內控"],
    }
    scores = {}
    for k, words in keywords.items():
        count = sum(len(re.findall(re.escape(w), text, flags=re.IGNORECASE)) for w in words)
        scores[k] = min(100, 50 + count * 5)
    return scores


def esg_grade(score):
    if score >= 90:
        return "AAA"
    if score >= 80:
        return "AA"
    if score >= 70:
        return "A"
    if score >= 60:
        return "BBB"
    if score >= 50:
        return "BB"
    return "B"


def esg_maturity(score):
    if score >= 85:
        return "領導"
    if score >= 70:
        return "成熟"
    if score >= 55:
        return "成長"
    return "初級"


# ============================================================
# 技術指標
# ============================================================

def add_indicators(df):
    df = df.copy()

    for n in [5, 10, 20, 60, 120, 240]:
        df[f"MA{n}"] = df["Close"].rolling(n).mean()

    df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA_26"] = df["Close"].ewm(span=26, adjust=False).mean()

    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

    delta = df["Close"].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(span=14, adjust=False).mean()
    roll_down = down.ewm(span=14, adjust=False).mean()
    rs = roll_up / roll_down.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    low_min = df["Low"].rolling(14).min()
    high_max = df["High"].rolling(14).max()
    denom = (high_max - low_min).replace(0, np.nan)
    df["K"] = (df["Close"] - low_min) / denom * 100
    df["D"] = df["K"].rolling(3).mean()
    df["J"] = 3 * df["K"] - 2 * df["D"]

    df["BB_MID"] = df["Close"].rolling(20).mean()
    df["BB_STD"] = df["Close"].rolling(20).std()
    df["BB_UPPER"] = df["BB_MID"] + 2 * df["BB_STD"]
    df["BB_LOWER"] = df["BB_MID"] - 2 * df["BB_STD"]
    df["BB_WIDTH"] = (df["BB_UPPER"] - df["BB_LOWER"]) / df["BB_MID"].replace(0, np.nan)

    df["BIAS5"] = (df["Close"] - df["MA5"]) / df["MA5"].replace(0, np.nan) * 100
    df["BIAS20"] = (df["Close"] - df["MA20"]) / df["MA20"].replace(0, np.nan) * 100
    df["BIAS60"] = (df["Close"] - df["MA60"]) / df["MA60"].replace(0, np.nan) * 100

    direction = np.sign(df["Close"].diff()).fillna(0)
    df["OBV"] = (direction * df["Volume"]).cumsum()
    df["OBV_MA20"] = df["OBV"].rolling(20).mean()

    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["TR"] = tr
    df["ATR14"] = tr.rolling(14).mean()

    plus_dm_raw = df["High"].diff()
    minus_dm_raw = -df["Low"].diff()
    plus_dm = np.where((plus_dm_raw > minus_dm_raw) & (plus_dm_raw > 0), plus_dm_raw, 0)
    minus_dm = np.where((minus_dm_raw > plus_dm_raw) & (minus_dm_raw > 0), minus_dm_raw, 0)
    atr = df["ATR14"].replace(0, np.nan)
    df["PLUS_DI"] = 100 * pd.Series(plus_dm, index=df.index).rolling(14).sum() / atr
    df["MINUS_DI"] = 100 * pd.Series(minus_dm, index=df.index).rolling(14).sum() / atr
    dx = (abs(df["PLUS_DI"] - df["MINUS_DI"]) / (df["PLUS_DI"] + df["MINUS_DI"]).replace(0, np.nan)) * 100
    df["ADX"] = dx.rolling(14).mean()

    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    ma_tp = tp.rolling(20).mean()
    md = (tp - ma_tp).abs().rolling(20).mean()
    df["CCI20"] = (tp - ma_tp) / (0.015 * md.replace(0, np.nan))

    hh = df["High"].rolling(14).max()
    ll = df["Low"].rolling(14).min()
    df["WILLIAMS_R"] = -100 * (hh - df["Close"]) / (hh - ll).replace(0, np.nan)

    df["MOM10"] = df["Close"] - df["Close"].shift(10)
    df["ROC10"] = df["Close"].pct_change(10) * 100

    return df.bfill().ffill()


def detect_cross_signals(df):
    rows = []
    d = df.tail(80).reset_index(drop=True)

    for i in range(1, len(d)):
        prev = d.iloc[i - 1]
        cur = d.iloc[i]

        def add(signal):
            rows.append({"Date": cur["Date"], "Price": cur["Close"], "訊號": signal})

        if prev["MA20"] <= prev["MA60"] and cur["MA20"] > cur["MA60"]:
            add("MA黃金")
        if prev["MA20"] >= prev["MA60"] and cur["MA20"] < cur["MA60"]:
            add("MA死亡")
        if prev["K"] <= prev["D"] and cur["K"] > cur["D"]:
            add("KD黃金")
        if prev["K"] >= prev["D"] and cur["K"] < cur["D"]:
            add("KD死亡")
        if prev["MACD"] <= prev["MACD_Signal"] and cur["MACD"] > cur["MACD_Signal"]:
            add("MACD黃金")
        if prev["MACD"] >= prev["MACD_Signal"] and cur["MACD"] < cur["MACD_Signal"]:
            add("MACD死亡")
        if prev["Close"] <= prev["BB_UPPER"] and cur["Close"] > cur["BB_UPPER"]:
            add("突破上軌")
        if prev["Close"] >= prev["BB_LOWER"] and cur["Close"] < cur["BB_LOWER"]:
            add("跌破下軌")

    return pd.DataFrame(rows).tail(20)


def technical_score(df):
    latest = df.iloc[-1]
    items = []

    def add(name, ok, good, bad):
        score = 1 if bool(ok) else -1
        items.append({"指標": name, "分數": score, "解讀": good if ok else bad})

    add("均線", latest["Close"] > latest["MA20"] > latest["MA60"], "站上 MA20 且 MA20 高於 MA60", "均線排列偏弱")
    add("MACD", latest["MACD"] > latest["MACD_Signal"], "MACD 偏多", "MACD 偏弱")
    add("RSI", 45 <= latest["RSI"] <= 70, "RSI 健康偏多", "RSI 過熱或偏弱")
    add("KD", latest["K"] > latest["D"], "KD 偏多", "KD 偏弱")
    add("布林", latest["Close"] > latest["BB_MID"], "站上布林中軌", "跌破布林中軌")
    add("OBV", latest["OBV"] > latest["OBV_MA20"], "量能累積偏多", "量能偏弱")
    add("DMI", latest["PLUS_DI"] > latest["MINUS_DI"], "+DI 大於 -DI", "-DI 大於 +DI")
    add("CCI", latest["CCI20"] > 0, "CCI 站上 0 軸", "CCI 低於 0 軸")
    add("Williams", latest["WILLIAMS_R"] > -80, "未處極弱區", "接近超賣弱勢區")
    add("ROC", latest["ROC10"] > 0, "10 日動能為正", "10 日動能為負")

    raw = sum(x["分數"] for x in items)
    score = int(round((raw + len(items)) / (2 * len(items)) * 100))

    if score >= 75:
        label = "技術面偏多"
    elif score >= 55:
        label = "技術面中性偏多"
    elif score >= 45:
        label = "技術面中性"
    elif score >= 30:
        label = "技術面中性偏空"
    else:
        label = "技術面偏空"

    return score, label, pd.DataFrame(items)


def technical_screener(df, conditions):
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 2 else latest
    rows = []

    def check(name, ok):
        rows.append({"條件": name, "符合": "是" if ok else "否"})
        return bool(ok)

    result = []
    for c in conditions:
        if c == "MA20向上":
            result.append(check(c, latest["MA20"] > prev["MA20"]))
        elif c == "MA20突破MA60":
            result.append(check(c, prev["MA20"] <= prev["MA60"] and latest["MA20"] > latest["MA60"]))
        elif c == "收盤站上MA20":
            result.append(check(c, latest["Close"] > latest["MA20"]))
        elif c == "RSI低於30":
            result.append(check(c, latest["RSI"] < 30))
        elif c == "RSI高於70":
            result.append(check(c, latest["RSI"] > 70))
        elif c == "MACD黃金交叉":
            result.append(check(c, prev["MACD"] <= prev["MACD_Signal"] and latest["MACD"] > latest["MACD_Signal"]))
        elif c == "KD黃金交叉":
            result.append(check(c, prev["K"] <= prev["D"] and latest["K"] > latest["D"]))
        elif c == "布林突破上軌":
            result.append(check(c, prev["Close"] <= prev["BB_UPPER"] and latest["Close"] > latest["BB_UPPER"]))
        elif c == "OBV高於20日均線":
            result.append(check(c, latest["OBV"] > latest["OBV_MA20"]))
        elif c == "ADX大於25":
            result.append(check(c, latest["ADX"] > 25))
        elif c == "近20日新高":
            result.append(check(c, latest["Close"] >= df["Close"].tail(20).max()))
        elif c == "近60日新高":
            result.append(check(c, latest["Close"] >= df["Close"].tail(60).max()))

    return (all(result) if result else False), pd.DataFrame(rows)


# ============================================================
# 籌碼
# ============================================================


def empty_institutional_df():
    """三大法人資料抓不到時使用的標準空表，避免 KeyError: 日期。"""
    return pd.DataFrame(columns=[
        "日期",
        "外資買賣超股數",
        "投信買賣超股數",
        "自營商買賣超股數",
        "三大法人合計",
    ])


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_institutional_twse(stock_code):
    if requests is None:
        return pd.DataFrame()

    rows = []
    for i in range(12):
        d = datetime.now() - timedelta(days=i)
        date_str = d.strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={date_str}&selectType=ALLBUT0999&response=csv"
        try:
            r = requests.get(url, timeout=8)
            if r.status_code != 200 or len(r.text) < 100:
                continue
            text = r.text.replace("=", "")
            df = pd.read_csv(StringIO(text))
            if df.empty:
                continue
            df.columns = [str(c).strip().replace('"', '') for c in df.columns]
            code_col = next((c for c in df.columns if "證券代號" in c), None)
            if not code_col:
                continue
            df[code_col] = df[code_col].astype(str).str.replace('"', '').str.strip()
            row_df = df[df[code_col] == stock_code]
            if row_df.empty:
                continue
            row = row_df.iloc[0]

            def pick(words):
                for w in words:
                    for col in df.columns:
                        if w in col:
                            return safe_float(row[col], 0)
                return 0

            foreign = pick(["外陸資買賣超股數", "外資買賣超股數"])
            invest = pick(["投信買賣超股數"])
            dealer = pick(["自營商買賣超股數"])
            rows.append({
                "日期": d.strftime("%Y-%m-%d"),
                "外資買賣超股數": foreign,
                "投信買賣超股數": invest,
                "自營商買賣超股數": dealer,
                "三大法人合計": foreign + invest + dealer,
            })
        except Exception:
            pass

    df_out = pd.DataFrame(rows)
    if df_out.empty or "日期" not in df_out.columns:
        return empty_institutional_df()
    return df_out.drop_duplicates(subset=["日期"]).sort_values("日期")


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_institutional_tpex(stock_code):
    if requests is None:
        return pd.DataFrame()

    rows = []
    for i in range(12):
        d = datetime.now() - timedelta(days=i)
        roc = d.year - 1911
        date_str = f"{roc}/{d.month:02d}/{d.day:02d}"
        url = f"https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade?date={date_str}&type=Daily&response=csv"
        try:
            r = requests.get(url, timeout=8)
            if r.status_code != 200 or len(r.text) < 100:
                continue
            text = r.text.replace("=", "")
            df = pd.read_csv(StringIO(text))
            if df.empty:
                continue
            df.columns = [str(c).strip().replace('"', '') for c in df.columns]
            code_col = next((c for c in df.columns if "代號" in c), None)
            if not code_col:
                continue
            df[code_col] = df[code_col].astype(str).str.replace('"', '').str.strip()
            row_df = df[df[code_col] == stock_code]
            if row_df.empty:
                continue
            row = row_df.iloc[0]

            def pick(words):
                for w in words:
                    for col in df.columns:
                        if w in col:
                            return safe_float(row[col], 0)
                return 0

            foreign = pick(["外資", "外陸資"])
            invest = pick(["投信"])
            dealer = pick(["自營商"])
            rows.append({
                "日期": d.strftime("%Y-%m-%d"),
                "外資買賣超股數": foreign,
                "投信買賣超股數": invest,
                "自營商買賣超股數": dealer,
                "三大法人合計": foreign + invest + dealer,
            })
        except Exception:
            pass

    df_out = pd.DataFrame(rows)
    if df_out.empty or "日期" not in df_out.columns:
        return empty_institutional_df()
    return df_out.drop_duplicates(subset=["日期"]).sort_values("日期")


def fetch_institutional_trading(symbol):
    code = pure_stock_code(symbol)
    if market_type(symbol) == "TWO":
        df = fetch_institutional_tpex(code)
        if df is not None and not df.empty:
            return df
        df = fetch_institutional_twse(code)
        return df if df is not None else empty_institutional_df()

    df = fetch_institutional_twse(code)
    if df is not None and not df.empty:
        return df
    df = fetch_institutional_tpex(code)
    return df if df is not None else empty_institutional_df()


def estimate_main_force(df_price):
    d = df_price.copy().tail(60)
    d["漲跌"] = d["Close"].diff()
    d["量均20"] = d["Volume"].rolling(20).mean()
    d["量比"] = d["Volume"] / d["量均20"].replace(0, np.nan)
    d["主力估算分數"] = np.where(
        (d["漲跌"] > 0) & (d["量比"] >= 1.2), d["量比"],
        np.where((d["漲跌"] < 0) & (d["量比"] >= 1.2), -d["量比"], 0)
    )
    d["主力方向"] = np.where(d["主力估算分數"] > 0, "偏買", np.where(d["主力估算分數"] < 0, "偏賣", "中性"))
    out = d[["Date", "Close", "Volume", "漲跌", "量比", "主力估算分數", "主力方向"]].copy()
    out["Date"] = pd.to_datetime(out["Date"]).dt.strftime("%Y-%m-%d")
    return out.tail(20)


def chip_signal_score(inst_df, main_df):
    score = 0.0
    if inst_df is not None and not inst_df.empty and "三大法人合計" in inst_df.columns:
        recent = inst_df.tail(5)
        total = recent["三大法人合計"].sum()
        foreign = recent["外資買賣超股數"].sum()
        invest = recent["投信買賣超股數"].sum()
        score += 2 if total > 0 else -2 if total < 0 else 0
        score += 1 if foreign > 0 else -1 if foreign < 0 else 0
        score += 1 if invest > 0 else -1 if invest < 0 else 0

    if main_df is not None and not main_df.empty:
        main_sum = main_df.tail(10)["主力估算分數"].sum()
        if main_sum > 3:
            score += 2
        elif main_sum < -3:
            score -= 2
        elif main_sum > 0:
            score += 1
        elif main_sum < 0:
            score -= 1

    if score >= 4:
        label = "籌碼偏多"
    elif score >= 1:
        label = "籌碼中性偏多"
    elif score <= -4:
        label = "籌碼偏空"
    elif score <= -1:
        label = "籌碼中性偏空"
    else:
        label = "籌碼中性"
    return score, label


# ============================================================
# 估值
# ============================================================

def fill_missing_valuation_inputs(market_price, eps, forward_eps, bvps, dividend, fcf, shares, ebitda, net_debt, params):
    notes = []
    mp = safe_float(market_price, np.nan)
    if pd.isna(mp) or mp <= 0:
        mp = 1.0
        notes.append("股價缺漏，以1作臨時基準")

    pe = max(float(params.get("target_pe", 18.0)), 1.0)
    fpe = max(float(params.get("forward_pe", 20.0)), 1.0)
    pb = max(float(params.get("target_pb", 2.0)), 0.1)
    evm = max(float(params.get("ev_ebitda", 12.0)), 1.0)

    if pd.isna(eps) or eps <= 0:
        eps = mp / pe
        notes.append("EPS 缺漏，以股價/產業PE反推")
    if pd.isna(forward_eps) or forward_eps <= 0:
        forward_eps = mp / fpe
        notes.append("Forward EPS 缺漏，以股價/Forward PE反推")
    if pd.isna(bvps) or bvps <= 0:
        bvps = mp / pb
        notes.append("BVPS 缺漏，以股價/PB反推")
    if pd.isna(dividend) or dividend < 0:
        dividend = 0
    if pd.isna(shares) or shares <= 0:
        shares = 1.0
        notes.append("股數缺漏，改用每股化基礎")
    if pd.isna(net_debt):
        net_debt = 0.0
    if pd.isna(fcf) or fcf <= 0:
        fcf = eps * 0.8 * shares
        notes.append("FCF 缺漏，以EPS×80%估算")
    if pd.isna(ebitda) or ebitda <= 0:
        ebitda = (mp + max(net_debt / shares if shares else 0, 0)) / evm * shares
        notes.append("EBITDA 缺漏，以股價與EV/EBITDA反推")

    return {
        "market_price": mp, "eps": eps, "forward_eps": forward_eps,
        "bvps": bvps, "dividend": dividend, "fcf": fcf,
        "shares": shares, "ebitda": ebitda, "net_debt": net_debt,
        "note": "；".join(notes) if notes else "Yahoo Finance 資料完整，未啟用反推",
    }


def calc_valuation(market_price, eps, forward_eps, bvps, dividend, fcf, shares, ebitda, net_debt,
                   params, esg_score, esg_pe_premium, esg_pb_premium, esg_wacc_discount, ai_bull_multiplier):
    pe = params["target_pe"]
    fpe = params["forward_pe"]
    peg = params["peg_target"]
    pb = params["target_pb"]
    evm = params["ev_ebitda"]
    required_return = params["required_return"] / 100
    discount_rate = params["discount_rate"] / 100
    terminal_growth = params["terminal_growth"] / 100
    eps_growth = params["eps_growth"] / 100
    fcf_growth = params["fcf_growth"] / 100
    dividend_growth = params["dividend_growth"] / 100

    rows = []

    def add(method, value, desc):
        rows.append({"方法": method, "合理價": value, "說明": desc})

    factor = max(min(esg_score, 100), 0) / 100
    esg_pe = pe * (1 + esg_pe_premium * factor)
    esg_pb = pb * (1 + esg_pb_premium * factor)
    esg_discount = max(discount_rate - esg_wacc_discount * factor, 0.01)

    pe_value = eps * pe
    fpe_value = forward_eps * fpe
    peg_value = eps * (eps_growth * 100 * peg) if eps_growth > 0 else np.nan
    pb_value = bvps * pb
    graham = np.sqrt(22.5 * eps * bvps) if eps > 0 and bvps > 0 else np.nan
    ddm = dividend * (1 + dividend_growth) / (required_return - dividend_growth) if dividend > 0 and required_return > dividend_growth else np.nan

    def dcf_value(rate):
        if shares <= 0 or rate <= terminal_growth:
            return np.nan
        cur = fcf
        pv = 0
        for year in range(1, 6):
            cur *= (1 + fcf_growth)
            pv += cur / ((1 + rate) ** year)
        tv = cur * (1 + terminal_growth) / (rate - terminal_growth)
        return (pv + tv / ((1 + rate) ** 5) - net_debt) / shares

    dcf = dcf_value(discount_rate)
    esg_dcf = dcf_value(esg_discount)
    ev_ebitda = (ebitda * evm - net_debt) / shares if shares > 0 else np.nan
    fcff = dcf
    fcfe = dcf * 0.95 if pd.notna(dcf) else np.nan
    eva = pb_value + (eps - required_return * bvps) * 5 if pd.notna(pb_value) else np.nan
    ebo = bvps + (eps - required_return * bvps) / max(required_return - terminal_growth, 0.01)

    esg_pe_value = eps * esg_pe
    esg_pb_value = bvps * esg_pb

    bull_base = pd.Series([pe_value, fpe_value, peg_value, dcf, ev_ebitda, esg_pe_value, esg_dcf]).dropna()
    super_bull = bull_base.mean() * ai_bull_multiplier if not bull_base.empty else np.nan

    add("PE 本益比法", pe_value, "EPS × 市場平均 PE")
    add("Forward PE 法", fpe_value, "Forward EPS × 市場平均 Forward PE")
    add("PEG 成長估值法", peg_value, "EPS × 成長率% × PEG")
    add("PB 股價淨值比法", pb_value, "BVPS × 市場平均 PB")
    add("Graham Value", graham, "√(22.5 × EPS × BVPS)")
    add("DDM 股利折現法", ddm, "D1 / (r-g)")
    add("DCF 自由現金流折現法", dcf, "5年FCF + 終值")
    add("FCFF 企業自由現金流", fcff, "企業自由現金流估值")
    add("FCFE 權益自由現金流", fcfe, "權益自由現金流估值")
    add("EV/EBITDA 法", ev_ebitda, "EBITDA × 倍數 - 淨負債")
    add("EVA 經濟附加價值法", eva, "簡化 EVA 模型")
    add("EBO 殘餘盈餘模型", ebo, "BVPS + 殘餘盈餘現值")
    add("ESG PE 溢價法", esg_pe_value, "ESG 調整 PE")
    add("ESG PB 溢價法", esg_pb_value, "ESG 調整 PB")
    add("ESG DCF 折現率調整法", esg_dcf, "ESG 降低折現率")
    add("AI Robot 超級牛市模型", super_bull, "核心估值均值 × AI 題材倍數")

    if pd.notna(market_price) and market_price > 0:
        add("市場錨定合理價", market_price, "目前市場價格作為錨點")
        add("市場保守錨定價", market_price * 0.90, "目前市場價格 × 0.90")
        add("市場樂觀錨定價", market_price * 1.15, "目前市場價格 × 1.15")

    df = pd.DataFrame(rows)
    valid = df["合理價"].replace([np.inf, -np.inf], np.nan).dropna()
    summary = {
        "原始平均合理價": valid.mean() if len(valid) else np.nan,
        "原始中位數合理價": valid.median() if len(valid) else np.nan,
        "ESG調整PE": esg_pe,
        "ESG調整PB": esg_pb,
        "ESG調整折現率": esg_discount,
    }
    return df, summary


def get_method_weight(method, industry_group, esg_score):
    weights = {
        "PE 本益比法": 1.00, "Forward PE 法": 1.20, "PEG 成長估值法": 0.90,
        "PB 股價淨值比法": 0.75, "Graham Value": 0.55, "DDM 股利折現法": 0.50,
        "DCF 自由現金流折現法": 1.30, "FCFF 企業自由現金流": 1.20,
        "FCFE 權益自由現金流": 1.10, "EV/EBITDA 法": 1.15,
        "EVA 經濟附加價值法": 0.85, "EBO 殘餘盈餘模型": 0.80,
        "ESG PE 溢價法": 0.85, "ESG PB 溢價法": 0.70,
        "ESG DCF 折現率調整法": 1.00, "AI Robot 超級牛市模型": 0.45,
        "市場錨定合理價": 0.90, "市場保守錨定價": 0.60, "市場樂觀錨定價": 0.60,
    }
    w = weights.get(method, 0.7)
    if industry_group == "Semiconductors" and method in ["Forward PE 法", "PEG 成長估值法", "DCF 自由現金流折現法", "EV/EBITDA 法"]:
        w *= 1.15
    if industry_group == "Financial Services" and method in ["PB 股價淨值比法", "DDM 股利折現法"]:
        w *= 1.25
    if esg_score >= 80 and method.startswith("ESG"):
        w *= 1.20
    return w


def market_temperature(latest):
    score = 0
    rsi = latest.get("RSI", np.nan)
    if pd.notna(rsi):
        if rsi >= 75:
            score -= 2
        elif rsi >= 60:
            score += 1
        elif rsi <= 30:
            score -= 1
    if latest["Close"] > latest["MA20"]:
        score += 1
    else:
        score -= 1
    if latest["Close"] > latest["MA60"]:
        score += 1
    else:
        score -= 1

    if score >= 2:
        return "偏多", 1.05
    if score <= -2:
        return "偏弱", 0.92
    if pd.notna(rsi) and rsi >= 75:
        return "過熱", 0.90
    return "中性", 1.00


def comprehensive_market_valuation(df_val, market_price, industry_group, esg_score, market_factor, ai_bull_multiplier):
    df = df_val.copy()
    df["合理價"] = pd.to_numeric(df["合理價"], errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=["合理價"])
    df = df[df["合理價"] > 0].copy()

    if df.empty:
        if pd.notna(market_price) and market_price > 0:
            return {
                "保守目標價": market_price * 0.90,
                "合理目標價": market_price,
                "樂觀目標價": market_price * 1.15,
                "超級牛市目標價": market_price * ai_bull_multiplier,
                "上漲下跌空間": 0,
                "使用方法數": 1,
                "加權估值基礎": market_price,
            }
        return {
            "保守目標價": np.nan, "合理目標價": np.nan,
            "樂觀目標價": np.nan, "超級牛市目標價": np.nan,
            "上漲下跌空間": np.nan, "使用方法數": 0,
            "加權估值基礎": np.nan,
        }

    if len(df) >= 4:
        q05 = df["合理價"].quantile(0.05)
        q95 = df["合理價"].quantile(0.95)
        df["調整後合理價"] = df["合理價"].clip(q05, q95)
    else:
        df["調整後合理價"] = df["合理價"]

    df["權重"] = df["方法"].apply(lambda m: get_method_weight(m, industry_group, esg_score))
    weighted = (df["調整後合理價"] * df["權重"]).sum() / df["權重"].sum()
    fair = weighted * market_factor

    q25 = df["調整後合理價"].quantile(0.25)
    q75 = df["調整後合理價"].quantile(0.75)

    conservative = (q25 * 0.60 + fair * 0.40) * min(market_factor, 1.0)
    optimistic = (q75 * 0.50 + fair * 0.50) * max(market_factor, 1.0)
    super_bull = optimistic * max(ai_bull_multiplier, 1.0)

    upside = (fair - market_price) / market_price if pd.notna(market_price) and market_price > 0 else np.nan

    return {
        "保守目標價": conservative,
        "合理目標價": fair,
        "樂觀目標價": optimistic,
        "超級牛市目標價": super_bull,
        "上漲下跌空間": upside,
        "使用方法數": len(df),
        "加權估值基礎": weighted,
    }


# ============================================================
# AI 預測
# ============================================================

def xgboost_predict(df_price, future_days):
    if not (SKLEARN_OK and XGBOOST_OK):
        raise RuntimeError("尚未安裝 scikit-learn 或 xgboost")

    features = ["Close", "EMA_12", "EMA_26", "MACD", "RSI", "K", "D", "Volume"]
    df = df_price.copy()
    df["Tomorrow"] = df["Close"].shift(-1)
    df = df.dropna()
    if len(df) < 80:
        raise RuntimeError("資料不足，請選 1y、2y 或 5y")

    X = df[features].values
    y = df["Tomorrow"].values
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    model = XGBRegressor(
        n_estimators=150, max_depth=3, learning_rate=0.05,
        subsample=0.85, colsample_bytree=0.85,
        objective="reg:squarederror", random_state=42,
    )
    model.fit(Xs, y)

    work = df_price.copy()
    preds = []
    for _ in range(future_days):
        latest = work.iloc[-1]
        row = np.array([[latest["Close"], latest["EMA_12"], latest["EMA_26"], latest["MACD"],
                         latest["RSI"], latest["K"], latest["D"], latest["Volume"]]])
        pred = float(model.predict(scaler.transform(row))[0])
        preds.append(pred)
        new = latest.copy()
        new["Date"] = work["Date"].iloc[-1] + pd.Timedelta(days=1)
        new["Open"] = pred
        new["High"] = pred
        new["Low"] = pred
        new["Close"] = pred
        work = pd.concat([work, pd.DataFrame([new])], ignore_index=True)
        work = add_indicators(work)

    return np.array(preds)


def trend_predict(df_price, future_days):
    if not SKLEARN_OK:
        raise RuntimeError("尚未安裝 scikit-learn")
    df = df_price.dropna(subset=["Close"]).tail(252)
    if len(df) < 30:
        raise RuntimeError("資料不足")
    X = np.arange(len(df)).reshape(-1, 1)
    y = df["Close"].values
    model = LinearRegression().fit(X, y)
    future_x = np.arange(len(df), len(df) + future_days).reshape(-1, 1)
    return np.maximum(model.predict(future_x), 0)


# ============================================================
# 圖表
# ============================================================

def price_chart(df, symbol, overlays=None, show_signals=True, chart_height=720):
    overlays = overlays or []
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["Date"], open=df["Open"], high=df["High"], low=df["Low"],
        close=df["Close"], name="K線"
    ))

    overlay_map = {
        "MA5": "MA5", "MA10": "MA10", "MA20": "MA20", "MA60": "MA60",
        "MA120": "MA120", "MA240": "MA240",
        "EMA12": "EMA_12", "EMA26": "EMA_26",
        "布林上軌": "BB_UPPER", "布林中軌": "BB_MID", "布林下軌": "BB_LOWER",
    }

    for label, col in overlay_map.items():
        if label in overlays and col in df.columns:
            fig.add_trace(go.Scatter(x=df["Date"], y=df[col], mode="lines", name=label))

    if show_signals:
        sig = detect_cross_signals(df)
        if not sig.empty:
            buy = sig[sig["訊號"].str.contains("黃金|突破", regex=True)]
            sell = sig[sig["訊號"].str.contains("死亡|跌破", regex=True)]
            if not buy.empty:
                fig.add_trace(go.Scatter(
                    x=buy["Date"], y=buy["Price"], mode="markers+text",
                    text=buy["訊號"], textposition="top center",
                    marker=dict(symbol="triangle-up", size=12),
                    name="多方訊號",
                ))
            if not sell.empty:
                fig.add_trace(go.Scatter(
                    x=sell["Date"], y=sell["Price"], mode="markers+text",
                    text=sell["訊號"], textposition="bottom center",
                    marker=dict(symbol="triangle-down", size=12),
                    name="空方訊號",
                ))

    fig.update_layout(title=f"{symbol} K線主圖", height=chart_height, xaxis_rangeslider_visible=False)
    return fig


def selected_indicator_chart(df, indicator):
    fig = go.Figure()

    if indicator == "成交量 Volume":
        fig.add_trace(go.Bar(x=df["Date"], y=df["Volume"], name="Volume"))
    elif indicator == "RSI":
        fig.add_trace(go.Scatter(x=df["Date"], y=df["RSI"], name="RSI"))
        fig.add_hline(y=70, line_dash="dash")
        fig.add_hline(y=30, line_dash="dash")
    elif indicator == "KD / J":
        fig.add_trace(go.Scatter(x=df["Date"], y=df["K"], name="K"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["D"], name="D"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["J"], name="J"))
        fig.add_hline(y=80, line_dash="dash")
        fig.add_hline(y=20, line_dash="dash")
    elif indicator == "MACD":
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MACD"], name="MACD"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MACD_Signal"], name="Signal"))
        fig.add_trace(go.Bar(x=df["Date"], y=df["MACD_Hist"], name="Hist"))
    elif indicator == "OBV":
        fig.add_trace(go.Scatter(x=df["Date"], y=df["OBV"], name="OBV"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["OBV_MA20"], name="OBV MA20"))
    elif indicator == "ATR":
        fig.add_trace(go.Scatter(x=df["Date"], y=df["ATR14"], name="ATR14"))
    elif indicator == "DMI / ADX":
        fig.add_trace(go.Scatter(x=df["Date"], y=df["PLUS_DI"], name="+DI"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MINUS_DI"], name="-DI"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["ADX"], name="ADX"))
        fig.add_hline(y=25, line_dash="dash", annotation_text="ADX 25")
    elif indicator == "CCI":
        fig.add_trace(go.Scatter(x=df["Date"], y=df["CCI20"], name="CCI20"))
        fig.add_hline(y=100, line_dash="dash")
        fig.add_hline(y=-100, line_dash="dash")
    elif indicator == "Williams %R":
        fig.add_trace(go.Scatter(x=df["Date"], y=df["WILLIAMS_R"], name="Williams %R"))
        fig.add_hline(y=-20, line_dash="dash")
        fig.add_hline(y=-80, line_dash="dash")
    elif indicator == "ROC / Momentum":
        fig.add_trace(go.Scatter(x=df["Date"], y=df["ROC10"], name="ROC10%"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MOM10"], name="MOM10"))
    elif indicator == "BIAS 乖離率":
        fig.add_trace(go.Scatter(x=df["Date"], y=df["BIAS5"], name="BIAS5"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["BIAS20"], name="BIAS20"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["BIAS60"], name="BIAS60"))

    fig.update_layout(title=f"副圖指標：{indicator}", height=430)
    return fig


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:
    st.header("智慧搜尋")
    raw_query = st.text_input("股票代碼 / 中文名稱 / 英文簡稱", "世界先進")
    symbol, display_name, suggestions = smart_resolve_symbol(raw_query)
    if suggestions:
        st.caption("可能股票：" + "；".join(suggestions[:5]))
    st.write(f"解析結果：`{symbol}`")

    period = st.radio("歷史資料期間", ["6mo", "1y", "2y", "5y", "10y"], index=3, horizontal=True)
    future_days = st.slider("預測天數", 7, 60, 30)

    st.subheader("手機介面")
    mobile_mode = st.checkbox("手機精簡模式", value=True)
    mobile_chart_height = st.slider("K線圖高度", 420, 760, 560, 20)

    st.subheader("技術指標")
    kline_overlays = st.multiselect(
        "K線主圖疊加",
        ["MA5", "MA10", "MA20", "MA60", "MA120", "MA240", "EMA12", "EMA26", "布林上軌", "布林中軌", "布林下軌"],
        default=["MA20", "MA60", "布林上軌", "布林中軌", "布林下軌"],
    )
    show_kline_signals = st.checkbox("顯示黃金 / 死亡交叉", value=True)
    sub_indicator = st.selectbox(
        "副圖指標",
        ["MACD", "RSI", "KD / J", "成交量 Volume", "OBV", "ATR", "DMI / ADX", "CCI", "Williams %R", "ROC / Momentum", "BIAS 乖離率"],
        index=0,
    )
    screener_conditions = st.multiselect(
        "技術選股條件",
        ["MA20向上", "MA20突破MA60", "收盤站上MA20", "RSI低於30", "RSI高於70",
         "MACD黃金交叉", "KD黃金交叉", "布林突破上軌", "OBV高於20日均線",
         "ADX大於25", "近20日新高", "近60日新高"],
        default=["收盤站上MA20", "OBV高於20日均線"],
    )

    st.subheader("籌碼 / ESG / 估值")
    enable_chip = st.checkbox("啟用三大法人 / 主力進出", value=True)
    enable_esg = st.checkbox("啟用 ESG 市場評估", value=True)
    esg_text = st.text_area("貼上永續報告書重點文字（選填）", height=100)
    enable_valuation = st.checkbox("啟用企業評價", value=True)

    st.subheader("目標價修正")
    use_chip_adjustment = st.checkbox("籌碼面修正目標價", value=True)
    use_technical_adjustment = st.checkbox("技術面修正目標價", value=True)
    esg_pe_premium_pct = st.number_input("ESG PE 最大溢價 %", 0.0, 100.0, 20.0, 1.0)
    esg_pb_premium_pct = st.number_input("ESG PB 最大溢價 %", 0.0, 100.0, 15.0, 1.0)
    esg_wacc_discount_pct = st.number_input("ESG WACC 最大下降 %", 0.0, 5.0, 1.0, 0.1)
    ai_bull_multiplier = st.number_input("AI Robot 超級牛市倍數", 1.0, 5.0, 1.5, 0.1)

    st.subheader("AI 預測")
    use_xgb = st.checkbox("XGBoost", value=True)
    use_trend = st.checkbox("趨勢回歸", value=True)

    run = st.button("開始分析", type="primary")


st.info(f"目前查詢：{display_name}。上櫃股票如世界先進會自動使用 `.TWO`。")

if run:
    with st.spinner(f"下載 {symbol} 股價資料中..."):
        df_price, resolved_symbol = fetch_price(symbol, period)

    if df_price.empty:
        st.error(f"查無資料。已嘗試 {symbol} 與 {fallback_symbol(symbol)}。請確認網路或 Yahoo Finance 代碼。")
        st.stop()

    df_price = add_indicators(df_price)
    latest = df_price.iloc[-1]
    prev = df_price.iloc[-2] if len(df_price) > 1 else latest

    market_info = fetch_market_inputs(resolved_symbol)
    avg_params = get_market_average_params(resolved_symbol, market_info)
    industry_group = avg_params.get("industry_group", "Default")

    c1, c2, c3, c4 = st.columns(4)
    change = latest["Close"] - prev["Close"]
    pct = change / prev["Close"] if prev["Close"] else 0
    c1.metric("股票", f"{display_name} / {resolved_symbol}")
    c2.metric("最新收盤價", f"{latest['Close']:.2f}", f"{change:.2f}")
    c3.metric("漲跌幅", f"{pct:.2%}")
    c4.metric("產業分類", industry_group)

    if mobile_mode:
        st.success("已啟用手機精簡模式：圖表高度與版面已針對手機瀏覽器 / Android WebView 優化。")

    st.subheader("📈 K線主圖：技術指標可勾選疊加")
    st.plotly_chart(price_chart(df_price, resolved_symbol, overlays=kline_overlays, show_signals=show_kline_signals, chart_height=mobile_chart_height), use_container_width=True)

    st.subheader("📉 技術副圖")
    st.plotly_chart(selected_indicator_chart(df_price, sub_indicator), use_container_width=True)

    st.subheader("🎯 技術選股器")
    screen_ok, screen_df = technical_screener(df_price, screener_conditions)
    sc1, sc2 = st.columns(2)
    sc1.metric("本股是否符合條件", "符合" if screen_ok else "未完全符合")
    sc2.metric("條件數", f"{len(screener_conditions)}")
    st.dataframe(screen_df, use_container_width=True)

    tech_score_value, tech_label, tech_df = technical_score(df_price)
    tech_factor = 1.0
    if use_technical_adjustment:
        if tech_score_value >= 75:
            tech_factor = 1.06
        elif tech_score_value >= 55:
            tech_factor = 1.03
        elif tech_score_value <= 30:
            tech_factor = 0.94
        elif tech_score_value <= 45:
            tech_factor = 0.97

    st.subheader("📊 技術面綜合評分")
    t1, t2, t3 = st.columns(3)
    t1.metric("技術訊號", tech_label)
    t2.metric("技術分數", f"{tech_score_value}/100")
    t3.metric("技術修正係數", f"{tech_factor:.2f}x")
    st.dataframe(tech_df, use_container_width=True)

    latest_tech = pd.DataFrame([{
        "收盤價": latest["Close"], "MA5": latest["MA5"], "MA20": latest["MA20"],
        "MA60": latest["MA60"], "RSI": latest["RSI"], "K": latest["K"], "D": latest["D"],
        "MACD": latest["MACD"], "布林上軌": latest["BB_UPPER"], "布林中軌": latest["BB_MID"],
        "布林下軌": latest["BB_LOWER"], "BIAS20%": latest["BIAS20"], "ATR14": latest["ATR14"],
        "ADX": latest["ADX"], "CCI20": latest["CCI20"], "Williams %R": latest["WILLIAMS_R"],
        "ROC10%": latest["ROC10"],
    }]).round(2)
    st.write("最新技術指標數值")
    st.dataframe(latest_tech, use_container_width=True)

    chip_factor = 1.0
    chip_label = "未啟用"
    chip_score_value = 0.0

    if enable_chip:
        st.subheader("💰 籌碼面：三大法人 / 主力進出")
        inst_df = fetch_institutional_trading(resolved_symbol)
        main_df = estimate_main_force(df_price)
        chip_score_value, chip_label = chip_signal_score(inst_df, main_df)

        if use_chip_adjustment:
            if chip_score_value >= 4:
                chip_factor = 1.06
            elif chip_score_value >= 1:
                chip_factor = 1.03
            elif chip_score_value <= -4:
                chip_factor = 0.94
            elif chip_score_value <= -1:
                chip_factor = 0.97

        ch1, ch2, ch3 = st.columns(3)
        ch1.metric("籌碼訊號", chip_label)
        ch2.metric("籌碼分數", f"{chip_score_value:.1f}")
        ch3.metric("籌碼修正係數", f"{chip_factor:.2f}x")

        if not inst_df.empty:
            st.write("三大法人近況")
            inst_show = inst_df.copy()
            for col in ["外資買賣超股數", "投信買賣超股數", "自營商買賣超股數", "三大法人合計"]:
                inst_show[col] = inst_show[col].apply(lambda x: int(x) if pd.notna(x) else 0)
            st.dataframe(inst_show, use_container_width=True)

            fig_inst = go.Figure()
            fig_inst.add_trace(go.Bar(x=inst_df["日期"], y=inst_df["外資買賣超股數"], name="外資"))
            fig_inst.add_trace(go.Bar(x=inst_df["日期"], y=inst_df["投信買賣超股數"], name="投信"))
            fig_inst.add_trace(go.Bar(x=inst_df["日期"], y=inst_df["自營商買賣超股數"], name="自營商"))
            fig_inst.update_layout(title="三大法人買賣超股數", barmode="group", height=420)
            st.plotly_chart(fig_inst, use_container_width=True)
        else:
            st.warning("三大法人公開資料暫時抓取不到，已改用主力價量估算。")

        st.write("主力進出估算")
        st.dataframe(main_df, use_container_width=True)
        fig_main = go.Figure()
        fig_main.add_trace(go.Bar(x=main_df["Date"], y=main_df["主力估算分數"], name="主力估算分數"))
        fig_main.update_layout(title="主力進出估算分數", height=380)
        st.plotly_chart(fig_main, use_container_width=True)

    esg_score = 0.0
    if enable_esg:
        st.subheader("🌱 ESG 市場評估")
        market_esg = get_market_esg_scores(resolved_symbol, industry_group, resolved_symbol)
        e = float(market_esg["E"])
        s = float(market_esg["S"])
        g = float(market_esg["G"])

        if esg_text.strip():
            kw = keyword_score(esg_text)
            e = e * 0.7 + kw["E"] * 0.3
            s = s * 0.7 + kw["S"] * 0.3
            g = g * 0.7 + kw["G"] * 0.3

        esg_score = (e + s + g) / 3
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("環境 E", f"{e:.1f}")
        e2.metric("社會 S", f"{s:.1f}")
        e3.metric("治理 G", f"{g:.1f}")
        e4.metric("ESG 等級", esg_grade(esg_score))
        st.info(f"ESG來源：{market_esg.get('source')}。{market_esg.get('reason')}")
        st.write(f"ESG總分：**{esg_score:.1f}**，成熟度：**{esg_maturity(esg_score)}**")

        fig_esg = go.Figure()
        fig_esg.add_trace(go.Bar(x=["E", "S", "G"], y=[e, s, g], name="ESG"))
        fig_esg.update_layout(title="ESG 三構面分數", height=420)
        st.plotly_chart(fig_esg, use_container_width=True)

    st.subheader("📘 財務報表")
    df_fin = fetch_financials(resolved_symbol)
    if not df_fin.empty:
        st.dataframe(df_fin, use_container_width=True)
    else:
        st.warning("找不到完整財報資料。")

    if enable_valuation:
        st.subheader("🏦 V24 企業評價 + 市場綜合估值")
        st.info(f"估值參數來源：市場/產業平均值｜分類：{industry_group}")
        st.dataframe(pd.DataFrame([avg_params]), use_container_width=True)

        mp_auto = market_info.get("market_price", np.nan)
        eps_auto = market_info.get("trailing_eps", np.nan)
        fwd_eps_auto = market_info.get("forward_eps", np.nan)
        bvps_auto = market_info.get("book_value", np.nan)
        div_auto = market_info.get("dividend_rate", np.nan)
        fcf_auto = market_info.get("free_cashflow", np.nan)
        shares_auto = market_info.get("shares_outstanding", np.nan)
        ebitda_auto = market_info.get("ebitda", np.nan)
        net_debt_auto = safe_float(market_info.get("total_debt", 0), 0) - safe_float(market_info.get("total_cash", 0), 0)

        with st.expander("估值資料檢查 / 可手動修正", expanded=False):
            a, b, c = st.columns(3)
            market_price_in = a.number_input("目前股價", value=float(mp_auto) if pd.notna(mp_auto) else float(latest["Close"]), step=0.1)
            eps_in = b.number_input("EPS", value=float(eps_auto) if pd.notna(eps_auto) else 0.0, step=0.1)
            fwd_eps_in = c.number_input("Forward EPS", value=float(fwd_eps_auto) if pd.notna(fwd_eps_auto) else 0.0, step=0.1)

            d, e_col, f = st.columns(3)
            bvps_in = d.number_input("BVPS", value=float(bvps_auto) if pd.notna(bvps_auto) else 0.0, step=0.1)
            dividend_in = e_col.number_input("DPS", value=float(div_auto) if pd.notna(div_auto) else 0.0, step=0.1)
            fcf_in = f.number_input("FCF", value=float(fcf_auto) if pd.notna(fcf_auto) else 0.0, step=1000000.0, format="%.0f")

            g_col, h, i_col = st.columns(3)
            shares_in = g_col.number_input("流通股數", value=float(shares_auto) if pd.notna(shares_auto) else 0.0, step=1000000.0, format="%.0f")
            ebitda_in = h.number_input("EBITDA", value=float(ebitda_auto) if pd.notna(ebitda_auto) else 0.0, step=1000000.0, format="%.0f")
            net_debt_in = i_col.number_input("淨負債", value=float(net_debt_auto) if pd.notna(net_debt_auto) else 0.0, step=1000000.0, format="%.0f")

        filled = fill_missing_valuation_inputs(
            market_price_in, eps_in, fwd_eps_in, bvps_in, dividend_in,
            fcf_in, shares_in, ebitda_in, net_debt_in, avg_params,
        )
        st.info("防 N/A 估值處理：" + filled["note"])

        df_val, val_summary = calc_valuation(
            filled["market_price"], filled["eps"], filled["forward_eps"], filled["bvps"],
            filled["dividend"], filled["fcf"], filled["shares"], filled["ebitda"], filled["net_debt"],
            avg_params, esg_score, esg_pe_premium_pct / 100, esg_pb_premium_pct / 100,
            esg_wacc_discount_pct / 100, ai_bull_multiplier,
        )

        temp_label, market_factor = market_temperature(latest)
        market_summary = comprehensive_market_valuation(
            df_val, filled["market_price"], industry_group, esg_score, market_factor, ai_bull_multiplier
        )

        if use_chip_adjustment:
            for key in ["保守目標價", "合理目標價", "樂觀目標價", "超級牛市目標價", "加權估值基礎"]:
                if pd.notna(market_summary.get(key, np.nan)):
                    market_summary[key] *= chip_factor

        if use_technical_adjustment:
            for key in ["保守目標價", "合理目標價", "樂觀目標價", "超級牛市目標價", "加權估值基礎"]:
                if pd.notna(market_summary.get(key, np.nan)):
                    market_summary[key] *= tech_factor

        if pd.notna(market_summary.get("合理目標價", np.nan)) and filled["market_price"] > 0:
            market_summary["上漲下跌空間"] = (market_summary["合理目標價"] - filled["market_price"]) / filled["market_price"]

        st.subheader("📌 市場綜合估值調整")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("市場溫度", temp_label)
        m2.metric("市場修正", f"{market_factor:.2f}x")
        m3.metric("籌碼修正", f"{chip_factor:.2f}x")
        m4.metric("技術修正", f"{tech_factor:.2f}x")

        tm1, tm2, tm3, tm4 = st.columns(4)
        tm1.metric("保守目標價", f"{market_summary['保守目標價']:.2f}")
        tm2.metric("合理目標價", f"{market_summary['合理目標價']:.2f}")
        tm3.metric("樂觀目標價", f"{market_summary['樂觀目標價']:.2f}")
        tm4.metric("超級牛市價", f"{market_summary['超級牛市目標價']:.2f}")

        st.metric("合理價上漲 / 下跌空間", f"{market_summary['上漲下跌空間']:.2%}")

        df_show = df_val.copy()
        df_show["合理價"] = df_show["合理價"].replace([np.inf, -np.inf], np.nan)
        df_show["合理價"] = df_show["合理價"].apply(lambda x: "" if pd.isna(x) else round(float(x), 2))
        st.dataframe(df_show, use_container_width=True)

        valid_val = df_val.replace([np.inf, -np.inf], np.nan).dropna(subset=["合理價"])
        if not valid_val.empty:
            fig_val = go.Figure()
            fig_val.add_trace(go.Bar(x=valid_val["方法"], y=valid_val["合理價"], name="合理價"))
            fig_val.add_hline(y=filled["market_price"], line_dash="dash", annotation_text="目前股價")
            fig_val.add_hline(y=market_summary["保守目標價"], line_dash="dot", annotation_text="保守")
            fig_val.add_hline(y=market_summary["合理目標價"], line_dash="dashdot", annotation_text="合理")
            fig_val.add_hline(y=market_summary["樂觀目標價"], line_dash="dot", annotation_text="樂觀")
            fig_val.update_layout(title="V24 估值方法比較", height=650)
            st.plotly_chart(fig_val, use_container_width=True)

    st.subheader("🤖 AI / 統計預測")
    predictions = {}
    future_dates = pd.date_range(df_price["Date"].iloc[-1] + pd.Timedelta(days=1), periods=future_days)

    if use_xgb:
        try:
            predictions["XGBoost"] = xgboost_predict(df_price, future_days)
            st.success("XGBoost 完成")
        except Exception as exc:
            st.error(f"XGBoost 錯誤：{exc}")

    if use_trend:
        try:
            predictions["趨勢回歸"] = trend_predict(df_price, future_days)
            st.success("趨勢回歸完成")
        except Exception as exc:
            st.error(f"趨勢回歸錯誤：{exc}")

    if predictions:
        fig_pred = go.Figure()
        for name, values in predictions.items():
            fig_pred.add_trace(go.Scatter(x=future_dates, y=values, mode="lines+markers", name=name))
        fig_pred.update_layout(title=f"{display_name} 未來 {future_days} 天預測", height=580)
        st.plotly_chart(fig_pred, use_container_width=True)

        pred_df = pd.DataFrame({"Date": future_dates})
        for name, values in predictions.items():
            pred_df[name] = pd.Series(values).values[:len(pred_df)]
        st.dataframe(pred_df, use_container_width=True)

    st.subheader("近期股價資料")
    st.dataframe(df_price.tail(30), use_container_width=True)

else:
    st.warning("請輸入股票名稱或代碼，設定技術指標後按「開始分析」。")
