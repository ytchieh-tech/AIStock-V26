import os, json
os.environ["STREAMLIT_RUNNER_MAGIC_ENABLED"] = "false"
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

APP_VERSION = "V226.0 Stock Database Expansion II"
APP_NAME = "智策股市 AI 決策平台"
st.set_page_config(page_title=f"{APP_NAME} {APP_VERSION}", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

STOCK_DB = json.loads(r'''{"2330.TW": {"name": "台積電", "industry": "半導體", "sub": "晶圓代工", "rank": "#1", "power": "★★★★★", "position": "晶圓代工全球龍頭", "peers": "Samsung Foundry、Intel Foundry、GlobalFoundries", "moat": "極高：先進製程、CoWoS、客戶黏著", "risk": "地緣政治、AI需求循環、資本支出", "fair_mult": 1.08}, "2303.TW": {"name": "聯電", "industry": "半導體", "sub": "成熟製程晶圓代工", "rank": "成熟製程主要廠", "power": "★★★☆☆", "position": "成熟製程晶圓代工重要供應商", "peers": "SMIC、GlobalFoundries、世界先進、力積電", "moat": "中：成熟產能、車用/工控客戶", "risk": "成熟製程價格競爭、稼動率", "fair_mult": 0.96}, "5347.TWO": {"name": "世界先進", "industry": "半導體", "sub": "特殊製程晶圓代工", "rank": "特殊製程主要廠", "power": "★★★☆☆", "position": "PMIC/DDI特殊製程晶圓代工", "peers": "聯電、力積電、GlobalFoundries", "moat": "中：特殊製程與電源管理客戶", "risk": "DDI/PMIC需求波動與價格壓力", "fair_mult": 0.96}, "6770.TW": {"name": "力積電", "industry": "半導體", "sub": "成熟製程/記憶體", "rank": "成熟製程循環股", "power": "★★☆☆☆", "position": "成熟製程與記憶體相關晶圓代工", "peers": "聯電、世界先進、SMIC", "moat": "低中：成熟製程產能", "risk": "價格循環、稼動率", "fair_mult": 0.92}, "2454.TW": {"name": "聯發科", "industry": "IC設計", "sub": "手機SoC/邊緣AI", "rank": "全球前三", "power": "★★★★☆", "position": "手機SoC與邊緣AI晶片主要供應商", "peers": "Qualcomm、Samsung LSI、展銳", "moat": "高：通訊IP、SoC整合能力", "risk": "手機需求循環、中國競爭", "fair_mult": 1.1}, "3034.TW": {"name": "聯詠", "industry": "IC設計", "sub": "DDI/TDDI", "rank": "全球DDI主要廠", "power": "★★★★☆", "position": "顯示驅動IC與車用顯示IC供應商", "peers": "Synaptics、LX Semicon、奇景", "moat": "中高：顯示IC設計與客戶導入", "risk": "面板循環、庫存調整", "fair_mult": 1.02}, "2379.TW": {"name": "瑞昱", "industry": "IC設計", "sub": "網通/音訊IC", "rank": "網通IC主要廠", "power": "★★★★☆", "position": "乙太網路、WiFi、音訊IC重要供應商", "peers": "Broadcom、MediaTek、Qualcomm", "moat": "中高：網通IP與客戶基礎", "risk": "PC/網通需求循環", "fair_mult": 1.05}, "5274.TWO": {"name": "信驊", "industry": "IC設計", "sub": "BMC伺服器管理晶片", "rank": "#1", "power": "★★★★★", "position": "全球BMC伺服器管理晶片龍頭", "peers": "Nuvoton、Microchip、Renesas", "moat": "極高：Server生態系、客戶認證、高轉換成本", "risk": "AI伺服器循環、估值偏高", "fair_mult": 1.18}, "3661.TW": {"name": "世芯-KY", "industry": "IC設計", "sub": "ASIC設計服務", "rank": "ASIC設計主要廠", "power": "★★★★☆", "position": "AI ASIC設計服務供應商", "peers": "創意、智原、Marvell、Broadcom", "moat": "高：先進製程設計能力與客戶專案", "risk": "客戶集中、專案波動", "fair_mult": 1.12}, "3443.TW": {"name": "創意", "industry": "IC設計", "sub": "ASIC/NRE", "rank": "ASIC主要廠", "power": "★★★★☆", "position": "ASIC與NRE設計服務重要供應商", "peers": "世芯-KY、智原、Alchip", "moat": "中高：設計服務與先進製程合作", "risk": "客戶集中、NRE波動", "fair_mult": 1.1}, "3035.TW": {"name": "智原", "industry": "IC設計", "sub": "ASIC/IP", "rank": "ASIC/IP供應商", "power": "★★★☆☆", "position": "ASIC與IP設計服務供應商", "peers": "創意、世芯-KY、M31", "moat": "中：IP與ASIC整合能力", "risk": "專案波動、毛利變化", "fair_mult": 1.06}, "3711.TW": {"name": "日月光投控", "industry": "半導體", "sub": "封測/SiP", "rank": "#1", "power": "★★★★★", "position": "全球封測與SiP龍頭", "peers": "Amkor、JCET、力成", "moat": "高：全球封測規模與SiP能力", "risk": "終端需求循環、匯率", "fair_mult": 1.06}, "2449.TW": {"name": "京元電子", "industry": "半導體", "sub": "測試/AI HPC", "rank": "測試主要廠", "power": "★★★★☆", "position": "AI/HPC與晶圓測試供應商", "peers": "欣銓、矽格、日月光", "moat": "中高：測試產能與客戶黏著", "risk": "客戶集中、資本支出", "fair_mult": 1.06}, "3131.TWO": {"name": "弘塑", "industry": "半導體設備", "sub": "濕製程設備", "rank": "濕製程關鍵供應商", "power": "★★★★☆", "position": "半導體濕製程與先進封裝設備供應商", "peers": "SCREEN、TEL、Lam Research", "moat": "高：設備認證與先進封裝需求", "risk": "資本支出波動、客戶集中", "fair_mult": 1.12}, "6223.TWO": {"name": "旺矽", "industry": "半導體設備", "sub": "探針卡", "rank": "探針卡主要廠", "power": "★★★★☆", "position": "高階探針卡與測試介面供應商", "peers": "精測、FormFactor、Technoprobe", "moat": "中高：先進測試與客戶認證", "risk": "資本支出與出貨波動", "fair_mult": 1.08}, "2382.TW": {"name": "廣達", "industry": "AI伺服器/ODM", "sub": "AI伺服器ODM", "rank": "全球ODM龍頭", "power": "★★★★★", "position": "AI伺服器與雲端伺服器ODM龍頭", "peers": "緯創、緯穎、英業達、Supermicro", "moat": "高：雲端客戶與AI伺服器整合能力", "risk": "AI資本支出循環、毛利率", "fair_mult": 1.1}, "3231.TW": {"name": "緯創", "industry": "AI伺服器/ODM", "sub": "AI伺服器ODM", "rank": "全球ODM主要廠", "power": "★★★★☆", "position": "AI伺服器與企業伺服器ODM供應商", "peers": "廣達、緯穎、英業達、鴻海", "moat": "中高：AI伺服器組裝與客戶關係", "risk": "毛利率、客戶集中", "fair_mult": 1.08}, "6669.TW": {"name": "緯穎", "industry": "AI伺服器/ODM", "sub": "雲端伺服器", "rank": "雲端伺服器主要廠", "power": "★★★★☆", "position": "雲端資料中心伺服器供應商", "peers": "廣達、Supermicro、緯創", "moat": "中高：雲端客戶與高階伺服器設計", "risk": "客戶集中、估值波動", "fair_mult": 1.1}, "2356.TW": {"name": "英業達", "industry": "AI伺服器/ODM", "sub": "伺服器ODM", "rank": "ODM主要廠", "power": "★★★☆☆", "position": "伺服器與筆電ODM供應商", "peers": "廣達、緯創、仁寶", "moat": "中：伺服器組裝、客戶基礎", "risk": "毛利較低、產品組合", "fair_mult": 1.03}, "2317.TW": {"name": "鴻海", "industry": "AI伺服器/ODM", "sub": "伺服器/電子製造", "rank": "EMS龍頭", "power": "★★★★☆", "position": "全球EMS與AI伺服器組裝供應商", "peers": "廣達、緯創、Flex、Jabil", "moat": "高：製造規模、客戶關係、垂直整合", "risk": "毛利率、蘋果依賴、資本支出", "fair_mult": 1.05}, "2345.TW": {"name": "智邦", "industry": "網通", "sub": "交換器/資料中心網通", "rank": "白牌交換器主要廠", "power": "★★★★☆", "position": "資料中心交換器與網通設備供應商", "peers": "Arista、Cisco供應鏈", "moat": "中高：雲端網通客戶與交換器設計", "risk": "雲端資本支出與客戶集中", "fair_mult": 1.08}, "2383.TW": {"name": "台光電", "industry": "電子材料", "sub": "AI高速材料/CCL", "rank": "AI高速材料主要供應商", "power": "★★★★☆", "position": "AI伺服器高速材料重要供應商", "peers": "聯茂、台燿、Panasonic、Isola", "moat": "高：高階CCL材料與供應鏈認證", "risk": "AI需求、原物料、產品組合", "fair_mult": 1.12}, "6274.TWO": {"name": "台燿", "industry": "電子材料", "sub": "高速CCL", "rank": "高速材料供應商", "power": "★★★★☆", "position": "高速網通與AI伺服器CCL供應商", "peers": "台光電、聯茂、Panasonic", "moat": "中高：高速材料與認證", "risk": "需求循環、原料成本", "fair_mult": 1.08}, "3037.TW": {"name": "欣興", "industry": "PCB/載板", "sub": "ABF載板", "rank": "ABF載板主要廠", "power": "★★★★☆", "position": "ABF載板與高階PCB供應商", "peers": "南電、景碩、Ibiden、Shinko", "moat": "中高：ABF載板與先進封裝需求", "risk": "ABF循環、庫存調整", "fair_mult": 1.05}, "8046.TW": {"name": "南電", "industry": "PCB/載板", "sub": "ABF/BT載板", "rank": "ABF載板主要廠", "power": "★★★★☆", "position": "載板與封裝基板重要供應商", "peers": "欣興、景碩、Ibiden、Shinko", "moat": "中高：載板產能與集團資源", "risk": "ABF需求循環、價格壓力", "fair_mult": 1.04}, "2368.TW": {"name": "金像電", "industry": "PCB/載板", "sub": "伺服器PCB", "rank": "伺服器PCB供應商", "power": "★★★★☆", "position": "AI伺服器與高速PCB供應商", "peers": "欣興、健鼎、瀚宇博", "moat": "中高：伺服器PCB與高速板技術", "risk": "AI出貨節奏、原料與良率", "fair_mult": 1.08}, "3017.TW": {"name": "奇鋐", "industry": "散熱", "sub": "AI伺服器散熱", "rank": "散熱主要廠", "power": "★★★★☆", "position": "AI伺服器散熱模組主要供應商", "peers": "雙鴻、建準、健策", "moat": "中高：散熱模組、液冷、客戶導入", "risk": "AI出貨節奏、毛利率", "fair_mult": 1.1}, "3324.TWO": {"name": "雙鴻", "industry": "散熱", "sub": "AI散熱/液冷", "rank": "散熱主要廠", "power": "★★★★☆", "position": "AI伺服器散熱與液冷供應商", "peers": "奇鋐、建準、健策", "moat": "中高：液冷技術與散熱設計", "risk": "短線漲多、客戶集中", "fair_mult": 1.1}, "3653.TW": {"name": "健策", "industry": "散熱", "sub": "均熱片/導熱元件", "rank": "高階散熱材料廠", "power": "★★★★☆", "position": "高階散熱與導熱元件供應商", "peers": "奇鋐、雙鴻、超眾", "moat": "中高：高階導熱材料與客戶認證", "risk": "AI需求波動、估值", "fair_mult": 1.09}, "2059.TW": {"name": "川湖", "industry": "機構件", "sub": "伺服器滑軌", "rank": "#1", "power": "★★★★★", "position": "全球伺服器滑軌龍頭", "peers": "Accuride、King Slide同業", "moat": "高：精密滑軌、客戶認證、良率", "risk": "伺服器出貨循環、估值偏高", "fair_mult": 1.1}, "2308.TW": {"name": "台達電", "industry": "電源管理", "sub": "資料中心電源/自動化", "rank": "#1", "power": "★★★★★", "position": "全球電源管理與資料中心電源領導廠", "peers": "Schneider、Eaton、ABB、Siemens、Vertiv", "moat": "極高：高效率電源、能源管理、全球製造", "risk": "AI資料中心資本支出、原料、匯率", "fair_mult": 1.12}, "1519.TW": {"name": "華城", "industry": "電力/重電", "sub": "變壓器/電網", "rank": "台灣重電主要廠", "power": "★★★★☆", "position": "電網升級與變壓器供應商", "peers": "中興電、士電、ABB、Siemens", "moat": "中高：電網建設、外銷訂單、認證", "risk": "政策節奏、原物料、匯率", "fair_mult": 1.1}, "1513.TW": {"name": "中興電", "industry": "電力/重電", "sub": "重電/電網/充電樁", "rank": "台灣重電主要廠", "power": "★★★★☆", "position": "電網設備與充電樁供應商", "peers": "華城、士電、ABB、Siemens", "moat": "中高：電網與充電樁布局", "risk": "政策、交期、估值波動", "fair_mult": 1.09}, "2327.TW": {"name": "國巨", "industry": "被動元件", "sub": "MLCC/晶片電阻", "rank": "全球前三MLCC廠", "power": "★★★★★", "position": "全球被動元件龍頭之一", "peers": "Murata、Samsung Electro-Mechanics、TDK", "moat": "高：高階車用/工規MLCC、通路與規模", "risk": "景氣循環、價格波動", "fair_mult": 1.08}, "2492.TW": {"name": "華新科", "industry": "被動元件", "sub": "MLCC/晶片電阻", "rank": "台灣被動元件主要廠", "power": "★★★★☆", "position": "MLCC與晶片電阻重要供應商", "peers": "國巨、Murata、TDK", "moat": "中高：車用/工規被動元件與集團資源", "risk": "價格循環、庫存調整", "fair_mult": 1.06}, "6173.TWO": {"name": "信昌電", "industry": "被動元件", "sub": "晶片電阻/陶瓷粉末", "rank": "利基被動元件供應商", "power": "★★★☆☆", "position": "被動元件材料與晶片電阻供應商", "peers": "國巨、華新科、厚聲", "moat": "中：材料與晶片電阻供應", "risk": "需求波動、規模較小", "fair_mult": 1.03}, "2375.TW": {"name": "凱美", "industry": "被動元件", "sub": "鋁質電容/固態電容", "rank": "電容主要廠", "power": "★★★☆☆", "position": "電容與被動元件供應商", "peers": "國巨、華新科、日系電容廠", "moat": "中：電容產品線與集團資源", "risk": "景氣循環、競爭", "fair_mult": 1.03}, "2472.TW": {"name": "立隆電", "industry": "被動元件", "sub": "鋁質電容", "rank": "鋁質電容主要廠", "power": "★★★☆☆", "position": "鋁質電容與固態電容供應商", "peers": "凱美、日系電容廠、國巨集團", "moat": "中：電容產品與工控應用", "risk": "電容景氣循環、原料成本", "fair_mult": 1.04}, "2408.TW": {"name": "南亞科", "industry": "記憶體", "sub": "DRAM", "rank": "台灣DRAM龍頭", "power": "★★★★☆", "position": "台灣DRAM主要製造商", "peers": "Samsung、SK Hynix、Micron", "moat": "中高：DRAM製造與集團資源", "risk": "記憶體價格循環、資本支出", "fair_mult": 1.12}, "2344.TW": {"name": "華邦電", "industry": "記憶體", "sub": "NOR Flash/DRAM", "rank": "利基記憶體主要廠", "power": "★★★☆☆", "position": "NOR Flash與利基型DRAM供應商", "peers": "旺宏、Samsung、Micron", "moat": "中：利基記憶體與車用/工控客戶", "risk": "記憶體價格循環、庫存", "fair_mult": 1.08}, "2337.TW": {"name": "旺宏", "industry": "記憶體", "sub": "NOR Flash", "rank": "NOR Flash主要廠", "power": "★★★☆☆", "position": "NOR Flash與ROM供應商", "peers": "華邦電、Micron、GigaDevice", "moat": "中：NOR Flash與長期客戶", "risk": "價格循環、需求波動", "fair_mult": 1.04}, "3260.TWO": {"name": "威剛", "industry": "記憶體", "sub": "記憶體模組", "rank": "記憶體模組主要通路商", "power": "★★★☆☆", "position": "DRAM/NAND模組與通路供應商", "peers": "創見、十銓、金士頓", "moat": "中：模組品牌、通路、庫存操作", "risk": "記憶體價格波動、庫存風險", "fair_mult": 1.08}, "4967.TWO": {"name": "十銓", "industry": "記憶體", "sub": "記憶體模組", "rank": "模組品牌商", "power": "★★★☆☆", "position": "電競與工控記憶體模組品牌", "peers": "威剛、創見、金士頓", "moat": "中：品牌、通路與產品設計", "risk": "記憶體價格波動", "fair_mult": 1.06}, "8299.TWO": {"name": "群聯", "industry": "記憶體", "sub": "SSD控制IC", "rank": "全球SSD控制IC龍頭之一", "power": "★★★★☆", "position": "NAND控制IC與儲存解決方案供應商", "peers": "慧榮、Marvell、Realtek", "moat": "高：控制IC設計、韌體、客戶認證", "risk": "NAND價格循環、庫存", "fair_mult": 1.1}, "3008.TW": {"name": "大立光", "industry": "光學", "sub": "高階手機鏡頭", "rank": "全球主要鏡頭廠", "power": "★★★★☆", "position": "高階手機光學鏡頭領導廠", "peers": "玉晶光、舜宇光學、AAC", "moat": "高：光學設計、製程良率、客戶認證", "risk": "手機需求循環、客戶集中", "fair_mult": 1.02}, "3406.TW": {"name": "玉晶光", "industry": "光學", "sub": "手機/AR光學鏡頭", "rank": "全球主要鏡頭廠", "power": "★★★★☆", "position": "手機與AR/VR光學供應商", "peers": "大立光、舜宇光學、AAC", "moat": "中高：光學製程、客戶導入", "risk": "手機需求循環、毛利波動", "fair_mult": 1.05}, "3019.TW": {"name": "亞光", "industry": "光學", "sub": "光學模組/鏡頭", "rank": "光學模組主要廠", "power": "★★★☆☆", "position": "車用與光學模組供應商", "peers": "大立光、玉晶光、舜宇光學", "moat": "中：光學模組整合與車用應用", "risk": "終端需求波動、競爭", "fair_mult": 1.03}, "6789.TW": {"name": "采鈺", "industry": "光學", "sub": "影像感測/光學元件", "rank": "半導體光學元件供應商", "power": "★★★☆☆", "position": "影像感測與半導體光學元件供應商", "peers": "晶相光、Sony供應鏈", "moat": "中高：半導體製程與光學元件整合", "risk": "消費電子波動", "fair_mult": 1.04}, "4979.TWO": {"name": "華星光", "industry": "光通訊/CPO", "sub": "光收發模組", "rank": "光通訊供應商", "power": "★★★★☆", "position": "AI資料中心光通訊模組供應商", "peers": "聯亞、上詮、眾達、Finisar", "moat": "中高：光模組、AI資料中心需求", "risk": "出貨節奏、客戶集中", "fair_mult": 1.12}, "3363.TWO": {"name": "上詮", "industry": "光通訊/CPO", "sub": "光通訊元件", "rank": "光通訊元件供應商", "power": "★★★☆☆", "position": "光通訊與資料中心元件供應商", "peers": "華星光、聯亞、眾達", "moat": "中：光通訊元件與客戶導入", "risk": "需求波動、競爭", "fair_mult": 1.08}, "6215.TWO": {"name": "和椿", "industry": "自動化/機器人", "sub": "AI Robot自動化", "rank": "自動化設備供應商", "power": "★★★☆☆", "position": "工業自動化與智慧工廠供應商", "peers": "上銀、亞德客、盟立、全球自動化設備商", "moat": "中：自動化整合、機器人與智慧工廠題材", "risk": "設備景氣循環、接單波動", "fair_mult": 1.06}, "2049.TW": {"name": "上銀", "industry": "自動化/機器人", "sub": "線性滑軌/機器人", "rank": "全球傳動元件主要廠", "power": "★★★★☆", "position": "線性傳動與工業機器人供應商", "peers": "THK、NSK、Bosch Rexroth、台灣精銳", "moat": "中高：精密傳動元件與全球品牌", "risk": "工具機循環、中國競爭", "fair_mult": 1.05}, "4583.TW": {"name": "台灣精銳", "industry": "自動化/機器人", "sub": "精密傳動/機器人", "rank": "精密自動化供應商", "power": "★★★☆☆", "position": "精密傳動與自動化零組件供應商", "peers": "上銀、亞德客、日系傳動廠", "moat": "中：精密製造與自動化應用", "risk": "景氣循環、規模與競爭", "fair_mult": 1.04}}''')
ALIASES = {}
for sym, v in STOCK_DB.items():
    ALIASES[sym.upper()] = sym
    ALIASES[sym.split('.')[0]] = sym
    ALIASES[v['name']] = sym
    ALIASES[v['name'].upper()] = sym

# ===== V210.0 GLOBAL COMPETITION DATABASE START =====
# 追加更多上市櫃股票、全球競爭對手、護城河、競爭優勢與風險資料。
V210_EXTRA_STOCKS = {
    '1597.TWO': {'name': '直得', 'industry': '自動化/機器人', 'sub': '微型線性滑軌', 'rank': '精密傳動供應商', 'power': '★★★☆☆', 'position': '微型線性滑軌與精密傳動供應商', 'peers': '上銀、全球傳動、THK', 'moat': '中：微型傳動與精密加工', 'risk': '需求循環、競爭', 'fair_mult': 1.04, 'advantage': '微型滑軌、精密傳動'},
    '2324.TW': {'name': '仁寶', 'industry': 'AI伺服器/ODM', 'sub': 'NB ODM/伺服器', 'rank': 'ODM主要廠', 'power': '★★★☆☆', 'position': '筆電ODM與伺服器代工供應商', 'peers': '廣達、緯創、英業達', 'moat': '中：ODM規模與客戶基礎', 'risk': '毛利率、PC需求循環', 'fair_mult': 1.02, 'advantage': 'ODM規模、客戶基礎'},
    '2353.TW': {'name': '宏碁', 'industry': 'AI PC/品牌', 'sub': 'PC品牌', 'rank': '全球PC品牌', 'power': '★★★☆☆', 'position': '全球PC品牌與AI PC受惠股', 'peers': '華碩、Lenovo、HP、Dell', 'moat': '中：品牌通路與PC產品線', 'risk': 'PC需求循環、毛利率', 'fair_mult': 1.02, 'advantage': '品牌通路、AI PC'},
    '2357.TW': {'name': '華碩', 'industry': 'AI PC/品牌', 'sub': 'PC/伺服器/AI PC', 'rank': '全球PC品牌', 'power': '★★★★☆', 'position': '全球PC、主機板與AI PC品牌', 'peers': 'Lenovo、HP、Dell、Acer、MSI', 'moat': '高：品牌、通路、主機板技術', 'risk': 'PC需求循環、庫存', 'fair_mult': 1.04, 'advantage': '品牌通路、主機板、AI PC'},
    '2359.TW': {'name': '所羅門', 'industry': '自動化/機器人', 'sub': '機器視覺/AI應用', 'rank': '機器視覺題材股', 'power': '★★★☆☆', 'position': '機器視覺、AI辨識與自動化應用供應商', 'peers': 'Keyence、Cognex、台灣自動化廠', 'moat': '中：機器視覺與AI應用', 'risk': '題材波動、商業化速度', 'fair_mult': 1.06, 'advantage': '機器視覺、AI辨識'},
    '2363.TW': {'name': '矽統', 'industry': 'IC設計', 'sub': 'SoC/投資題材', 'rank': '轉型IC設計股', 'power': '★★☆☆☆', 'position': '早期晶片組與IC設計公司', 'peers': '聯發科、瑞昱、威盛', 'moat': '低中：品牌歷史與投資題材', 'risk': '轉型成效、獲利波動', 'fair_mult': 0.98, 'advantage': 'IC設計經驗、集團資源'},
    '2376.TW': {'name': '技嘉', 'industry': 'AI伺服器/品牌', 'sub': '主機板/伺服器', 'rank': '板卡與伺服器品牌', 'power': '★★★★☆', 'position': '主機板、顯卡與AI伺服器供應商', 'peers': '華碩、微星、Supermicro', 'moat': '中高：板卡設計、伺服器整合', 'risk': 'AI訂單波動、顯卡循環', 'fair_mult': 1.06, 'advantage': '主機板、顯卡、AI伺服器'},
    '2377.TW': {'name': '微星', 'industry': 'AI PC/品牌', 'sub': '電競PC/主機板', 'rank': '電競品牌', 'power': '★★★★☆', 'position': '電競筆電、主機板與AI PC品牌', 'peers': '華碩、技嘉、Lenovo、Dell', 'moat': '中高：電競品牌、板卡設計', 'risk': 'PC循環、通路庫存', 'fair_mult': 1.04, 'advantage': '電競品牌、AI PC、板卡'},
    '2388.TW': {'name': '威盛', 'industry': 'IC設計', 'sub': '處理器/AI邊緣', 'rank': '利基IC設計', 'power': '★★★☆☆', 'position': '處理器、AI邊緣與嵌入式平台公司', 'peers': 'Intel、AMD、ARM生態系、瑞昱', 'moat': '中：處理器IP與嵌入式平台', 'risk': '產品商業化、競爭壓力', 'fair_mult': 1.03, 'advantage': '處理器IP、邊緣AI、嵌入式'},
    '2401.TW': {'name': '凌陽', 'industry': 'IC設計', 'sub': '消費/車用IC', 'rank': '消費IC供應商', 'power': '★★★☆☆', 'position': '多媒體、車用與消費IC供應商', 'peers': '瑞昱、聯詠、偉詮電', 'moat': '中：消費IC與車用布局', 'risk': '消費電子波動、毛利壓力', 'fair_mult': 1.02, 'advantage': '消費IC、車用IC、產品組合'},
    '2420.TW': {'name': '新巨', 'industry': '電源管理', 'sub': '電源供應器', 'rank': '電源供應商', 'power': '★★★☆☆', 'position': '工業與伺服器電源供應器公司', 'peers': '台達電、光寶科、康舒', 'moat': '中：工業電源與客戶基礎', 'risk': '需求波動、競爭', 'fair_mult': 1.03, 'advantage': '工業電源、伺服器電源'},
    '2457.TW': {'name': '飛宏', 'industry': '電源管理', 'sub': '電源/充電樁', 'rank': '電源供應商', 'power': '★★★☆☆', 'position': '電源供應器與充電樁相關供應商', 'peers': '台達電、光寶科、康舒', 'moat': '中：電源與充電應用', 'risk': '轉型成效、毛利率', 'fair_mult': 1.03, 'advantage': '電源、EV充電'},
    '2458.TW': {'name': '義隆', 'industry': 'IC設計', 'sub': '觸控/MCU', 'rank': '觸控IC主要廠', 'power': '★★★☆☆', 'position': '觸控與微控制器IC供應商', 'peers': 'Synaptics、Goodix、瑞昱、聯詠', 'moat': '中：觸控IC與客戶基礎', 'risk': 'PC/消費電子需求循環、價格競爭', 'fair_mult': 1.03, 'advantage': '觸控IC、MCU、客戶導入'},
    '2880.TW': {'name': '華南金', 'industry': '金融', 'sub': '公股銀行金控', 'rank': '公股金控', 'power': '★★★☆☆', 'position': '公股銀行型金控', 'peers': '第一金、合庫金、兆豐金', 'moat': '中：銀行通路與公股資源', 'risk': '利差、信用風險', 'fair_mult': 1.02, 'advantage': '銀行通路、公股資源'},
    '2884.TW': {'name': '玉山金', 'industry': '金融', 'sub': '金控/銀行', 'rank': '銀行金控', 'power': '★★★☆☆', 'position': '台灣銀行型金控', 'peers': '中信金、兆豐金、第一金', 'moat': '中：銀行通路與財管能力', 'risk': '利差、信用風險', 'fair_mult': 1.02, 'advantage': '銀行通路、財管'},
    '2885.TW': {'name': '元大金', 'industry': '金融', 'sub': '金控/證券', 'rank': '證券金控', 'power': '★★★☆☆', 'position': '證券與ETF通路領導金控', 'peers': '富邦金、中信金、國泰金', 'moat': '中高：證券通路、ETF、市場份額', 'risk': '股市成交量波動', 'fair_mult': 1.03, 'advantage': '證券通路、ETF'},
    '2892.TW': {'name': '第一金', 'industry': '金融', 'sub': '公股銀行金控', 'rank': '公股金控', 'power': '★★★☆☆', 'position': '公股銀行型金控', 'peers': '兆豐金、合庫金、華南金', 'moat': '中：公股銀行通路', 'risk': '利差、景氣循環', 'fair_mult': 1.02, 'advantage': '銀行通路、公股資源'},
    '3026.TW': {'name': '禾伸堂', 'industry': '被動元件', 'sub': 'MLCC/被動元件', 'rank': '被動元件供應商', 'power': '★★★☆☆', 'position': 'MLCC與被動元件供應商', 'peers': '國巨、華新科、Murata', 'moat': '中：MLCC產品與通路', 'risk': '景氣循環、價格波動', 'fair_mult': 1.03, 'advantage': 'MLCC、通路'},
    '3044.TW': {'name': '健鼎', 'industry': 'PCB/載板', 'sub': 'PCB', 'rank': 'PCB主要廠', 'power': '★★★☆☆', 'position': 'PCB量產與車用/伺服器板供應商', 'peers': '欣興、華通、瀚宇博', 'moat': '中：PCB量產能力與客戶基礎', 'risk': '景氣循環、原料成本', 'fair_mult': 1.03, 'advantage': 'PCB量產、車用/工控'},
    '3068.TWO': {'name': '美磊', 'industry': '被動元件', 'sub': '電感', 'rank': '電感供應商', 'power': '★★★☆☆', 'position': '電感與磁性元件供應商', 'peers': '奇力新同業、TDK、Murata', 'moat': '中：電感產品線', 'risk': '需求循環、價格競爭', 'fair_mult': 1.03, 'advantage': '電感、磁性元件'},
    '3081.TWO': {'name': '聯亞', 'industry': '光通訊/CPO', 'sub': '磊晶/光通訊元件', 'rank': '光通訊磊晶供應商', 'power': '★★★★☆', 'position': '光通訊磊晶與雷射元件供應商', 'peers': '華星光、上詮、Lumentum、Coherent', 'moat': '中高：磊晶與光元件技術', 'risk': 'CPO導入時程、客戶集中', 'fair_mult': 1.1, 'advantage': '磊晶、雷射元件、CPO'},
    '3227.TWO': {'name': '原相', 'industry': 'IC設計', 'sub': '感測IC', 'rank': '滑鼠感測IC主要廠', 'power': '★★★☆☆', 'position': '光學感測與影像感測IC供應商', 'peers': 'PixArt同業、OmniVision、Sony感測供應鏈', 'moat': '中：感測IC與演算法', 'risk': '消費電子需求波動', 'fair_mult': 1.03, 'advantage': '感測IC、演算法、遊戲周邊'},
    '3362.TWO': {'name': '先進光', 'industry': '光學', 'sub': '光學鏡頭/模組', 'rank': '光學元件供應商', 'power': '★★★☆☆', 'position': '手機、車用與光學模組供應商', 'peers': '大立光、玉晶光、亞光', 'moat': '中：光學製程與客戶導入', 'risk': '需求波動、良率', 'fair_mult': 1.03, 'advantage': '鏡頭模組、車用光學'},
    '3504.TWO': {'name': '揚明光', 'industry': '光學', 'sub': '投影/光學模組', 'rank': '光學模組供應商', 'power': '★★★☆☆', 'position': '投影與光學模組供應商', 'peers': '亞光、先進光、大立光', 'moat': '中：光學模組設計', 'risk': '終端需求波動', 'fair_mult': 1.02, 'advantage': '投影光學、模組整合'},
    '3529.TWO': {'name': '力旺', 'industry': 'IC設計', 'sub': '矽智財/IP', 'rank': 'IP授權利基廠', 'power': '★★★★☆', 'position': '嵌入式非揮發性記憶體IP供應商', 'peers': 'Synopsys、ARM、M31、晶心科', 'moat': '高：IP授權、製程導入與高毛利', 'risk': '授權案時程、客戶集中', 'fair_mult': 1.1, 'advantage': 'IP授權、高毛利、先進製程導入'},
    '3545.TW': {'name': '敦泰', 'industry': 'IC設計', 'sub': '觸控/DDI', 'rank': '觸控IC供應商', 'power': '★★★☆☆', 'position': '觸控與顯示相關IC設計公司', 'peers': '義隆、聯詠、Goodix', 'moat': '中：觸控IC與顯示IC經驗', 'risk': '面板與手機循環', 'fair_mult': 1.02, 'advantage': '觸控IC、面板供應鏈'},
    '3715.TW': {'name': '定穎投控', 'industry': 'PCB/載板', 'sub': '車用PCB', 'rank': '車用PCB供應商', 'power': '★★★☆☆', 'position': '車用與高頻PCB供應商', 'peers': '健鼎、華通、TTM', 'moat': '中：車用PCB客戶導入', 'risk': '車市循環、產品組合', 'fair_mult': 1.04, 'advantage': '車用PCB、高頻應用'},
    '4147.TWO': {'name': '中裕', 'industry': '生技醫療', 'sub': '新藥/抗體', 'rank': '新藥公司', 'power': '★★☆☆☆', 'position': '抗體與新藥開發公司', 'peers': '國際新藥公司、台灣生技同業', 'moat': '低中：研發管線', 'risk': '臨床、法規、商業化', 'fair_mult': 1.02, 'advantage': '抗體新藥、研發'},
    '4162.TWO': {'name': '智擎', 'industry': '生技醫療', 'sub': '新藥授權', 'rank': '新藥授權公司', 'power': '★★☆☆☆', 'position': '新藥開發與授權公司', 'peers': '國際藥廠、台灣新藥公司', 'moat': '低中：新藥授權與研發能力', 'risk': '臨床、授權進度', 'fair_mult': 1.02, 'advantage': '新藥授權、研發'},
    '4540.TWO': {'name': '全球傳動', 'industry': '自動化/機器人', 'sub': '線性傳動', 'rank': '傳動元件供應商', 'power': '★★★☆☆', 'position': '線性傳動與自動化元件供應商', 'peers': '上銀、直得、THK', 'moat': '中：傳動元件製造能力', 'risk': '工具機循環、中國競爭', 'fair_mult': 1.04, 'advantage': '線性傳動、自動化'},
    '4576.TW': {'name': '大銀微系統', 'industry': '自動化/機器人', 'sub': '精密傳動/機器人', 'rank': '精密傳動供應商', 'power': '★★★☆☆', 'position': '精密傳動與自動化零組件供應商', 'peers': '上銀、台灣精銳、THK', 'moat': '中：精密傳動與機器人應用', 'risk': '工具機循環、規模', 'fair_mult': 1.04, 'advantage': '精密傳動、機器人'},
    '4919.TW': {'name': '新唐', 'industry': 'IC設計', 'sub': 'MCU/音訊IC', 'rank': 'MCU主要廠', 'power': '★★★☆☆', 'position': 'MCU、音訊與工控IC供應商', 'peers': 'STMicro、Renesas、Microchip', 'moat': '中：MCU產品線與工控應用', 'risk': '庫存循環、價格競爭', 'fair_mult': 1.03, 'advantage': 'MCU、工控、車用'},
    '4958.TW': {'name': '臻鼎-KY', 'industry': 'PCB/載板', 'sub': 'PCB/HDI', 'rank': '全球PCB龍頭之一', 'power': '★★★★☆', 'position': '全球PCB與HDI主要供應商', 'peers': '欣興、華通、健鼎、TTM', 'moat': '中高：規模、蘋果供應鏈、製程', 'risk': '客戶集中、消費電子循環', 'fair_mult': 1.04, 'advantage': 'PCB規模、HDI、客戶認證'},
    '4966.TW': {'name': '譜瑞-KY', 'industry': 'IC設計', 'sub': '高速傳輸IC', 'rank': '高速介面IC主要廠', 'power': '★★★★☆', 'position': '高速傳輸與顯示介面IC供應商', 'peers': 'Parade同業、瑞昱、祥碩、聯詠', 'moat': '中高：高速介面IC技術', 'risk': 'PC/消費電子波動', 'fair_mult': 1.06, 'advantage': '高速介面、USB/Display、客戶認證'},
    '4976.TW': {'name': '佳凌', 'industry': '光學', 'sub': '光學鏡頭/車用', 'rank': '光學供應商', 'power': '★★★☆☆', 'position': '光學鏡頭與車用光學供應商', 'peers': '大立光、玉晶光、亞光', 'moat': '中：光學製程與車用應用', 'risk': '車用導入時程、需求波動', 'fair_mult': 1.03, 'advantage': '車用光學、鏡頭'},
    '4977.TWO': {'name': '眾達-KY', 'industry': '光通訊/CPO', 'sub': '光收發模組', 'rank': '光通訊模組供應商', 'power': '★★★☆☆', 'position': '光收發模組與資料中心光通訊供應商', 'peers': '華星光、上詮、光聖', 'moat': '中：光模組設計與客戶基礎', 'risk': '需求波動、客戶集中', 'fair_mult': 1.06, 'advantage': '光模組、資料中心'},
    '5269.TW': {'name': '祥碩', 'industry': 'IC設計', 'sub': '高速傳輸IC', 'rank': 'USB控制IC主要廠', 'power': '★★★★☆', 'position': '高速傳輸控制IC與USB IC供應商', 'peers': '瑞昱、譜瑞、創惟', 'moat': '中高：高速傳輸IC與客戶導入', 'risk': 'PC平台循環、產品週期', 'fair_mult': 1.06, 'advantage': 'USB高速IC、平台認證'},
    '5351.TWO': {'name': '鈺創', 'industry': '記憶體', 'sub': 'DRAM/影像IC', 'rank': '利基記憶體IC', 'power': '★★☆☆☆', 'position': '利基記憶體與影像IC供應商', 'peers': '華邦電、旺宏、利基IC同業', 'moat': '低中：利基記憶體設計', 'risk': '獲利波動、競爭', 'fair_mult': 1.02, 'advantage': '利基記憶體、影像IC'},
    '5469.TW': {'name': '瀚宇博', 'industry': 'PCB/載板', 'sub': 'PCB', 'rank': 'PCB供應商', 'power': '★★★☆☆', 'position': '消費電子與伺服器PCB供應商', 'peers': '華通、健鼎、欣興', 'moat': '中：PCB客戶基礎', 'risk': '景氣循環、毛利波動', 'fair_mult': 1.02, 'advantage': 'PCB量產、客戶基礎'},
    '5471.TWO': {'name': '松翰', 'industry': 'IC設計', 'sub': 'MCU/消費IC', 'rank': 'MCU供應商', 'power': '★★★☆☆', 'position': 'MCU與消費控制IC供應商', 'peers': '盛群、新唐、凌陽', 'moat': '中：MCU與消費IC產品線', 'risk': '需求循環、價格競爭', 'fair_mult': 1.02, 'advantage': 'MCU、消費控制IC'},
    '5880.TW': {'name': '合庫金', 'industry': '金融', 'sub': '公股銀行金控', 'rank': '公股金控', 'power': '★★★☆☆', 'position': '大型公股銀行金控', 'peers': '第一金、華南金、兆豐金', 'moat': '中：銀行通路與公股資源', 'risk': '利差、景氣循環', 'fair_mult': 1.02, 'advantage': '銀行通路、公股資源'},
    '6104.TWO': {'name': '創惟', 'industry': 'IC設計', 'sub': 'USB控制IC', 'rank': 'USB控制IC供應商', 'power': '★★★☆☆', 'position': 'USB與高速傳輸控制IC供應商', 'peers': 'Genesys Logic同業、瑞昱、群聯', 'moat': '中：USB控制IC與韌體能力', 'risk': 'PC/周邊需求循環', 'fair_mult': 1.04, 'advantage': 'USB控制IC、韌體、通路'},
    '6166.TW': {'name': '凌華', 'industry': '工業電腦', 'sub': '邊緣運算/自動化', 'rank': '工業電腦供應商', 'power': '★★★☆☆', 'position': '工業電腦、邊緣運算與自動化平台供應商', 'peers': '研華、Kontron、Siemens IPC', 'moat': '中：工業電腦與邊緣平台', 'risk': '工業景氣循環、競爭', 'fair_mult': 1.04, 'advantage': '工業電腦、邊緣AI'},
    '6191.TW': {'name': '精成科', 'industry': 'PCB/載板', 'sub': 'PCB/EMS', 'rank': 'PCB供應商', 'power': '★★★☆☆', 'position': 'PCB與電子製造服務供應商', 'peers': '瀚宇博、華通、健鼎', 'moat': '中：PCB與EMS整合', 'risk': '景氣循環、競爭', 'fair_mult': 1.02, 'advantage': 'PCB、EMS整合'},
    '6202.TW': {'name': '盛群', 'industry': 'IC設計', 'sub': 'MCU', 'rank': 'MCU供應商', 'power': '★★★☆☆', 'position': '微控制器MCU供應商', 'peers': '新唐、松翰、Microchip', 'moat': '中：MCU產品線與通路', 'risk': '庫存循環、價格競爭', 'fair_mult': 1.02, 'advantage': 'MCU、家電/工控應用'},
    '6209.TW': {'name': '今國光', 'industry': '光學', 'sub': '光學鏡頭', 'rank': '光學元件供應商', 'power': '★★☆☆☆', 'position': '光學鏡頭與元件供應商', 'peers': '大立光、玉晶光、亞光', 'moat': '低中：光學量產能力', 'risk': '價格競爭、需求循環', 'fair_mult': 1.0, 'advantage': '鏡頭製造、量產'},
    '6282.TW': {'name': '康舒', 'industry': '電源管理', 'sub': '電源供應器', 'rank': '電源供應主要廠', 'power': '★★★☆☆', 'position': '電源供應器與新能源應用供應商', 'peers': '台達電、光寶科、群電', 'moat': '中：電源設計與客戶基礎', 'risk': '毛利率、需求循環', 'fair_mult': 1.03, 'advantage': '電源供應器、新能源'},
    '6442.TW': {'name': '光聖', 'industry': '光通訊/CPO', 'sub': '光通訊元件', 'rank': '光通訊元件供應商', 'power': '★★★★☆', 'position': '資料中心光通訊零組件供應商', 'peers': '華星光、上詮、眾達、Finisar', 'moat': '中高：光通訊零組件與客戶導入', 'risk': '出貨時程、競爭', 'fair_mult': 1.1, 'advantage': '光通訊元件、資料中心'},
    '6446.TW': {'name': '藥華藥', 'industry': '生技醫療', 'sub': '新藥/血液疾病', 'rank': '新藥公司', 'power': '★★★☆☆', 'position': '血液疾病新藥商業化公司', 'peers': '國際新藥公司、台灣生技同業', 'moat': '中：藥證與商業化進展', 'risk': '銷售成長、法規、研發風險', 'fair_mult': 1.06, 'advantage': '新藥商業化、藥證'},
    '6462.TW': {'name': '神盾', 'industry': 'IC設計', 'sub': '生物辨識/資安', 'rank': '生物辨識IC供應商', 'power': '★★★☆☆', 'position': '指紋辨識與資安IC設計公司', 'peers': 'Goodix、Synaptics、敦泰', 'moat': '中：生物辨識演算法與IC整合', 'risk': '手機需求、客戶集中', 'fair_mult': 1.03, 'advantage': '指紋辨識、資安IC'},
    '6531.TW': {'name': '愛普', 'industry': 'IC設計', 'sub': '記憶體IP/AI記憶體', 'rank': '記憶體IP供應商', 'power': '★★★☆☆', 'position': '高頻寬記憶體與AI記憶體相關IC供應商', 'peers': 'Samsung、SK Hynix、Micron、力旺', 'moat': '中：記憶體IP與封裝整合', 'risk': '產品導入時程、競爭', 'fair_mult': 1.06, 'advantage': '記憶體IP、AI記憶體、封裝'},
    '6533.TW': {'name': '晶心科', 'industry': 'IC設計', 'sub': 'RISC-V IP', 'rank': 'RISC-V IP主要廠', 'power': '★★★★☆', 'position': 'RISC-V處理器IP供應商', 'peers': 'ARM、SiFive、MIPS、Synopsys', 'moat': '中高：RISC-V IP與工具鏈', 'risk': 'IP商業化速度、競爭', 'fair_mult': 1.08, 'advantage': 'RISC-V IP、授權模式'},
    '8088.TWO': {'name': '品安', 'industry': '記憶體', 'sub': '記憶體模組', 'rank': '模組供應商', 'power': '★★☆☆☆', 'position': '記憶體模組與通路供應商', 'peers': '威剛、十銓、創見', 'moat': '低中：模組通路與庫存操作', 'risk': '價格波動、庫存風險', 'fair_mult': 1.04, 'advantage': '記憶體模組、通路'},
    '8271.TWO': {'name': '宇瞻', 'industry': '記憶體', 'sub': '工控記憶體模組', 'rank': '工控模組品牌', 'power': '★★★☆☆', 'position': '工控與嵌入式記憶體模組供應商', 'peers': '威剛、創見、十銓', 'moat': '中：工控通路、產品穩定性', 'risk': '記憶體價格波動、庫存', 'fair_mult': 1.04, 'advantage': '工控記憶體、嵌入式'},
    '8374.TWO': {'name': '羅昇', 'industry': '自動化/機器人', 'sub': '自動化代理/整合', 'rank': '自動化整合商', 'power': '★★☆☆☆', 'position': '工業自動化零組件代理與整合商', 'peers': '和椿、盟立、上銀', 'moat': '低中：通路與整合能力', 'risk': '設備景氣循環、毛利率', 'fair_mult': 1.02, 'advantage': '自動化通路、整合'},
}

try:
    STOCK_DB.update(V210_EXTRA_STOCKS)
except Exception:
    pass

# 重建別名，讓新增股票可用中文名稱或代碼搜尋
try:
    ALIASES.clear()
    for sym, v in STOCK_DB.items():
        ALIASES[sym.upper()] = sym
        ALIASES[sym.split(".")[0]] = sym
        ALIASES[v["name"]] = sym
        ALIASES[v["name"].upper()] = sym
except Exception:
    pass
# ===== V210.0 GLOBAL COMPETITION DATABASE END =====


OTC_CODES = {s.split('.')[0] for s in STOCK_DB if s.endswith('.TWO')}

def tw_now():
    return (datetime.utcnow() + timedelta(hours=8)).strftime('%Y/%m/%d %H:%M')

def normalize_symbol(q):
    q = str(q or '').strip()
    uq = q.upper().replace(' ', '')
    if not q:
        return '2330.TW'
    if q in ALIASES:
        return ALIASES[q]
    if uq in ALIASES:
        return ALIASES[uq]
    if '.' in uq:
        return uq
    if uq.isdigit():
        return uq + ('.TWO' if uq in OTC_CODES else '.TW')
    for sym, v in STOCK_DB.items():
        if q in v['name'] or v['name'] in q:
            return sym
    return uq

@st.cache_data(ttl=3600, show_spinner=False)
def live_price(symbol):
    try:
        hist = yf.Ticker(symbol).history(period='5d', interval='1d')
        if hist is not None and len(hist) > 0 and 'Close' in hist:
            return float(hist['Close'].dropna().iloc[-1])
    except Exception:
        pass
    return np.nan

def fmt_price(x):
    try:
        return 'N/A' if pd.isna(x) else f'{float(x):,.2f}'
    except Exception:
        return 'N/A'

def decision(symbol):
    symbol = normalize_symbol(symbol)
    m = STOCK_DB.get(symbol, {'name': symbol, 'industry': '待補', 'sub': '待補', 'rank': '待補', 'power': '★★★☆☆', 'position': '待補', 'peers': '待補', 'moat': '待補', 'risk': '資料庫尚待補齊', 'fair_mult': 1.0})
    price = live_price(symbol)
    mult = float(m.get('fair_mult', 1.0))
    if pd.notna(price) and price > 0:
        cons = price * max(.78, mult - .16)
        fair = price * mult
        opt = price * (mult + .14)
        ret = (fair / price - 1) * 100
    else:
        cons = fair = opt = np.nan
        ret = 0.0
    action = '買進' if ret >= 15 else ('觀察偏多' if ret >= 8 else ('觀察' if ret >= 0 else '減碼/迴避'))
    rating = '★★★★☆' if (m.get('power','').count('★') >= 5 and ret >= 5) or ret >= 15 else ('★★★☆☆' if ret >= 0 else '★★☆☆☆')
    return {**m, 'symbol': symbol, 'price': price, 'cons': cons, 'fair': fair, 'opt': opt, 'ret': ret, 'action': action, 'rating': rating, 'source': 'Yahoo Finance / V200資料庫', 'updated': tw_now()}

def css():
    st.markdown('''<style>#MainMenu,footer{visibility:hidden}.block-container{padding-top:1rem;max-width:1280px}.hero{background:linear-gradient(135deg,#061225 0%,#10295f 55%,#2450b8 100%);color:white;padding:30px 34px;border-radius:20px;box-shadow:0 16px 36px rgba(0,0,0,.18);margin:8px 0 22px}.hero-title{font-size:34px;font-weight:900;margin-bottom:9px}.hero-sub{font-size:16px;opacity:.94;margin-bottom:16px}.badge{display:inline-block;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.24);padding:8px 13px;border-radius:999px;margin-right:8px;margin-top:6px;font-size:14px}.note{background:#eaf4ff;border-left:5px solid #2f7df6;padding:15px 18px;border-radius:12px;color:#064b8a;margin:14px 0 18px;font-size:15px}.section-title{font-size:30px;font-weight:900;margin:24px 0 10px;color:#0f172a}div[data-testid="stMetricValue"]{font-size:32px}@media(max-width:768px){.hero-title{font-size:25px}.hero{padding:22px 20px}div[data-testid="stMetricValue"]{font-size:25px}}</style>''', unsafe_allow_html=True)

def industry_options():
    return sorted({v['industry'] for v in STOCK_DB.values()})

def stock_options(ind):
    return [f"{v['name']} / {sym}" for sym, v in sorted(STOCK_DB.items()) if v['industry'] == ind]

def db_rows():
    return [{'產業': v['industry'], '子產業': v['sub'], '公司': v['name'], '代碼': sym, '全球競爭力': v['power'], '產業地位': v['position']} for sym, v in STOCK_DB.items()]

def set_active(x):
    st.session_state['active_symbol'] = normalize_symbol(x)


# ===== V220.0 AI INDUSTRY CHAIN MAP START =====
# 產業鏈主題分類：一家公司可同時屬於多個 AI 主題，不再硬塞單一類股。

THEME_DB = {
    "AI伺服器": {
        "desc": "AI伺服器、雲端資料中心、伺服器ODM、電源、散熱、機殼與高速材料。",
        "symbols": ["2382.TW","3231.TW","6669.TW","2356.TW","2317.TW","2308.TW","3017.TW","3324.TWO","3653.TW","2059.TW","2383.TW","2368.TW","3037.TW","8046.TW","5274.TWO"]
    },
    "AI ASIC": {
        "desc": "AI ASIC設計、NRE、IP與客製化晶片服務。",
        "symbols": ["3661.TW","3443.TW","3035.TW","6643.TWO","6533.TW","3529.TWO","2330.TW"]
    },
    "CoWoS/先進封裝": {
        "desc": "先進封裝、測試、ABF載板與封測供應鏈。",
        "symbols": ["2330.TW","3711.TW","2449.TW","3264.TWO","6510.TWO","6223.TWO","3037.TW","8046.TW","3189.TWO"]
    },
    "HBM/記憶體": {
        "desc": "DRAM、NAND、NOR Flash、SSD控制IC與記憶體模組。",
        "symbols": ["2408.TW","2344.TW","2337.TW","3260.TWO","4967.TWO","2451.TW","8299.TWO","8271.TWO","8088.TWO"]
    },
    "CPO/光通訊": {
        "desc": "光收發模組、光通訊元件、磊晶、資料中心光傳輸。",
        "symbols": ["4979.TWO","3363.TWO","3163.TWO","3081.TWO","6442.TW","4977.TWO"]
    },
    "液冷/散熱": {
        "desc": "AI伺服器散熱、液冷、均熱片、風扇與導熱材料。",
        "symbols": ["3017.TW","3324.TWO","3653.TW","2421.TW","2308.TW"]
    },
    "電源/能源管理": {
        "desc": "資料中心電源、UPS、電網、重電、能源管理與工業電源。",
        "symbols": ["2308.TW","2301.TW","6412.TW","6282.TW","2420.TW","1519.TW","1513.TW","1503.TW","1504.TW","1514.TW"]
    },
    "AI PC": {
        "desc": "AI PC、主機板、品牌PC、處理器平台與周邊IC。",
        "symbols": ["2357.TW","2376.TW","2377.TW","2353.TW","2324.TW","2379.TW","2454.TW","4966.TW","5269.TW"]
    },
    "AI手機/光學": {
        "desc": "AI手機、AR/VR、手機鏡頭、光學模組與影像感測。",
        "symbols": ["3008.TW","3406.TW","3019.TW","3362.TWO","3504.TWO","6209.TW","4976.TW","6789.TW","2454.TW"]
    },
    "機器人/自動化": {
        "desc": "人形機器人、工業自動化、線性滑軌、機器視覺與自動化整合。",
        "symbols": ["6215.TWO","2049.TW","4583.TW","4540.TWO","1597.TWO","4576.TW","8374.TWO","2359.TW","6166.TW","2467.TW","6187.TWO","6438.TW"]
    },
    "被動元件": {
        "desc": "MLCC、晶片電阻、電感、電容與AI伺服器被動元件需求。",
        "symbols": ["2327.TW","2492.TW","6173.TWO","2375.TW","2472.TW","3026.TW","3068.TWO"]
    },
    "車用/電動車": {
        "desc": "車用電子、EV、連接線、車用零組件與能源系統。",
        "symbols": ["2308.TW","3665.TW","1536.TW","2379.TW","4919.TW","3044.TW","3715.TW"]
    }
}

def v220_apply_themes():
    try:
        for sym, meta in STOCK_DB.items():
            meta["themes"] = []
        for theme, info in THEME_DB.items():
            for sym in info.get("symbols", []):
                if sym in STOCK_DB:
                    STOCK_DB[sym].setdefault("themes", [])
                    if theme not in STOCK_DB[sym]["themes"]:
                        STOCK_DB[sym]["themes"].append(theme)
        for sym, meta in STOCK_DB.items():
            meta["theme_text"] = "、".join(meta.get("themes", [])) if meta.get("themes") else "一般產業"
            # AI受惠度：依主題數與產業關聯粗估，後續可接模型
            n = len(meta.get("themes", []))
            if any(t in meta.get("themes", []) for t in ["AI伺服器","AI ASIC","CoWoS/先進封裝","HBM/記憶體","CPO/光通訊"]):
                meta["ai_score"] = min(10, 7 + n)
            elif any(t in meta.get("themes", []) for t in ["AI PC","AI手機/光學","機器人/自動化","液冷/散熱","電源/能源管理"]):
                meta["ai_score"] = min(10, 5 + n)
            else:
                meta["ai_score"] = min(10, 2 + n)
    except Exception:
        pass

v220_apply_themes()

def v220_theme_rows(theme):
    rows = []
    info = THEME_DB.get(theme, {})
    for sym in info.get("symbols", []):
        if sym in STOCK_DB:
            v = STOCK_DB[sym]
            rows.append({
                "公司": v.get("name", sym),
                "代碼": sym,
                "主產業": v.get("industry", ""),
                "次產業": v.get("sub", ""),
                "AI受惠度": v.get("ai_score", ""),
                "全球競爭力": v.get("power", ""),
                "全球地位": v.get("position", ""),
                "主要競爭者": v.get("peers", ""),
                "主題": v.get("theme_text", "")
            })
    return rows

def v220_industry_chain_page():
    st.header("🧬 AI產業鏈地圖")
    st.info("一家公司可以同時屬於多個主題，例如台達電同時屬於電源/能源管理、AI伺服器、液冷/散熱與車用/電動車。")
    theme = st.selectbox("選擇AI產業鏈主題", list(THEME_DB.keys()), key="v220_theme")
    st.caption(THEME_DB.get(theme, {}).get("desc", ""))
    rows = v220_theme_rows(theme)
    if rows:
        st.dataframe(pd.DataFrame(rows).sort_values(["AI受惠度","全球競爭力"], ascending=[False, False]), use_container_width=True, hide_index=True)
        st.markdown("### 主題快速分析")
        top = rows[:8]
        cols = st.columns(min(4, len(top))) if top else []
        for i, r in enumerate(top[:4]):
            with cols[i]:
                if st.button(r["公司"], key=f"v220_theme_btn_{theme}_{r['代碼']}", use_container_width=True):
                    set_active(r["代碼"])
                    st.rerun()
    else:
        st.warning("此主題資料尚待補齊。")

# 覆蓋/補強 db_rows，讓產業個股清單顯示主題與AI受惠度
def db_rows():
    return [
        {"產業":v.get("industry",""),"子產業":v.get("sub",""),"公司":v.get("name",sym),"代碼":sym,
         "AI主題":v.get("theme_text","一般產業"),"AI受惠度":v.get("ai_score",""),
         "全球競爭力":v.get("power",""),"產業地位":v.get("position","")}
        for sym, v in STOCK_DB.items()
    ]
# ===== V220.0 AI INDUSTRY CHAIN MAP END =====



# ===== V221.0 STABLE INVESTOR HOME PATCH START =====
# 目的：首頁只放一般投資人最在意的價格與區間；深度研究資料收進展開區。
# 全球競爭力用 主產業 → 子產業 → 個股 方式篩選，避免全部擠在一起。

def v221_ai_score_text(d):
    try:
        score = int(d.get("ai_score", 0))
    except Exception:
        score = 0
    return f"{score}/10" if score > 0 else "非AI主題"

def v221_ai_theme_text(d):
    try:
        score = int(d.get("ai_score", 0))
    except Exception:
        score = 0
    if score <= 0:
        return "非AI主題"
    return d.get("theme_text", d.get("themes", "AI主題"))

def v221_score_explanation():
    st.markdown("""
    ### AI受惠度評分說明

    | 分數 | 定義 | 代表類型 |
    |---|---|---|
    | 10 | AI核心基礎建設或不可或缺關鍵晶片 | 台積電、信驊、緯穎 |
    | 9 | AI關鍵零組件 | 台光電、奇鋐、雙鴻、CPO光通訊 |
    | 8 | AI供應鏈直接受惠 | 封測、ABF載板、測試、ASIC設計 |
    | 7 | AI需求明確帶動，但非唯一主軸 | 台達電、機器人、自動化 |
    | 5~6 | 中度受惠 | AI PC、AI手機、光學 |
    | 3~4 | 間接受惠 | 一般電子零組件 |
    | 0 | 非AI主題 | 金融、航運、鋼鐵、塑化等傳統產業 |
    """)
    st.caption("AI受惠度不是買賣建議，而是衡量公司營收、訂單、估值是否可能受到 AI 投資循環帶動。")

def v221_price_summary(symbol):
    d = v108_get_decision(symbol) if "v108_get_decision" in globals() else v107_get_decision(symbol)
    st.caption(f"資料更新時間：{d.get('updated','N/A')}｜現價來源：{d.get('source','N/A')}｜預期報酬率＝(合理價－現價)÷現價。")

    st.markdown(f"## {d.get('name', symbol)}（{symbol}）")

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("投資建議", d.get("action","觀察"))
    m2.metric("現價", v108_fmt_price(d.get("price", np.nan)) if "v108_fmt_price" in globals() else v107_fmt_price(d.get("price", np.nan)))
    m3.metric("合理價", v108_fmt_price(d.get("fair", np.nan)) if "v108_fmt_price" in globals() else v107_fmt_price(d.get("fair", np.nan)))
    try:
        ret_txt = f"{float(d.get('ret',0)):.1f}%"
    except Exception:
        ret_txt = "N/A"
    m4.metric("預期報酬", ret_txt)

    p1,p2,p3 = st.columns(3)
    fmtf = v108_fmt_price if "v108_fmt_price" in globals() else v107_fmt_price
    p1.metric("保守價", fmtf(d.get("cons", np.nan)))
    p2.metric("合理價", fmtf(d.get("fair", np.nan)))
    p3.metric("樂觀價", fmtf(d.get("opt", np.nan)))

    with st.expander("展開更多研究資料", expanded=False):
        st.markdown("### 🌍 全球競爭力與產業定位")
        g1,g2,g3,g4 = st.columns(4)
        g1.metric("AI受惠度", v221_ai_score_text(d))
        g2.metric("全球競爭力", d.get("power", d.get("global_power","★★★☆☆")))
        g3.metric("產業排名", d.get("rank", d.get("global_rank","待補")))
        g4.metric("全球地位", d.get("position", d.get("global_position","待補")))

        st.dataframe(pd.DataFrame([{
            "主產業":d.get("industry","待補"),
            "子產業":d.get("sub", d.get("sub_industry","待補")),
            "AI主題":v221_ai_theme_text(d),
            "主要競爭者":d.get("peers", d.get("competitors","待補")),
            "護城河":d.get("moat","待補"),
            "競爭優勢":d.get("advantage","待補"),
            "主要風險":d.get("risk","待補")
        }]), use_container_width=True, hide_index=True)

        tabs = st.tabs(["投資人摘要","價格區間","風險提示","AI受惠度說明"])
        with tabs[0]:
            st.dataframe(pd.DataFrame([{
                "公司":d.get("name",symbol),
                "代碼":symbol,
                "主產業":d.get("industry","待補"),
                "子產業":d.get("sub", d.get("sub_industry","待補")),
                "AI主題":v221_ai_theme_text(d),
                "AI受惠度":v221_ai_score_text(d),
                "全球競爭力":d.get("power", d.get("global_power","★★★☆☆")),
                "投資建議":d.get("action","觀察"),
                "現價":fmtf(d.get("price",np.nan)),
                "合理價":fmtf(d.get("fair",np.nan)),
                "預期報酬":ret_txt
            }]), use_container_width=True, hide_index=True)
        with tabs[1]:
            st.dataframe(pd.DataFrame([{
                "保守價":fmtf(d.get("cons",np.nan)),
                "合理價":fmtf(d.get("fair",np.nan)),
                "樂觀價":fmtf(d.get("opt",np.nan)),
                "說明":"首頁先提供價格區間；進階版企業價值研究院將接回 DCF、EVA、EBO、CAP、ESG Premium。"
            }]), use_container_width=True, hide_index=True)
        with tabs[2]:
            st.write(f"- 主要風險：{d.get('risk','待補')}")
            st.write("- 財報、產業景氣、利率與匯率變化都可能影響估值。")
        with tabs[3]:
            v221_score_explanation()

def v221_investor_home():
    v108_css() if "v108_css" in globals() else v107_css()
    now_show = datetime.now().strftime("%Y/%m/%d %H:%M")
    st.markdown(f"""
    <div class="v108-hero">
      <div class="v108-title">智策股市 AI 決策平台</div>
      <div class="v108-sub">首頁先看股價與合理價區間；想深入再展開產業鏈、全球競爭力與企業評價。</div>
      <span class="v108-badge">最後更新：{now_show}</span>
      <span class="v108-badge">資料來源：TWSE・TPEx・Yahoo Finance</span>
      <span class="v108-badge">V221 Stable Investor Home</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="v108-note">一般投資人先看現價、保守價、合理價、樂觀價與預期報酬；深度研究資料已收合在「展開更多研究資料」。</div>', unsafe_allow_html=True)

    c1,c2 = st.columns([1.2,1])
    with c1:
        q = st.text_input("搜尋股票代碼或公司名稱", value=st.session_state.get("v221_query",""), placeholder="例如：2330、台積電、2308、台達電、5274、信驊", key="v221_query_input")
    with c2:
        st.caption("現價每小時快取；重新整理頁面可取得最新資料。")

    if str(q or "").strip():
        st.session_state["v221_query"] = str(q).strip()
        symbol = v108_normalize_symbol(q) if "v108_normalize_symbol" in globals() else v107_get_symbol(q)
    else:
        symbol = st.session_state.get("v221_active_symbol","2330.TW")

    # 快速查詢
    groups = [
        ("核心", [("台積電","2330"),("台達電","2308"),("信驊","5274"),("聯發科","2454"),("廣達","2382"),("大立光","3008")]),
        ("AI伺服器", [("緯穎","6669"),("緯創","3231"),("奇鋐","3017"),("雙鴻","3324"),("川湖","2059"),("台光電","2383")])
    ]
    for title, items in groups:
        st.markdown(f"#### {title}快速查詢")
        cols = st.columns(len(items))
        for col, (label, code) in zip(cols, items):
            with col:
                if st.button(label, key=f"v221_quick_{code}", use_container_width=True):
                    st.session_state["v221_query"] = code
                    st.session_state["v221_active_symbol"] = v108_normalize_symbol(code) if "v108_normalize_symbol" in globals() else v107_get_symbol(code)
                    st.rerun()

    with st.expander("產業 → 子產業 → 個股", expanded=False):
        rows = v108_rows() if "v108_rows" in globals() else v107_rows()
        df = pd.DataFrame(rows)
        if not df.empty:
            ind_col = "產業"
            sub_col = "子產業"
            stock_col = "公司"
            code_col = "代碼"
            a,b,c,dcol = st.columns([1,1,1,0.25])
            with a:
                ind = st.selectbox("主產業", sorted(df[ind_col].dropna().unique()), key="v221_ind")
            sub_df = df[df[ind_col] == ind]
            with b:
                sub = st.selectbox("子產業", sorted(sub_df[sub_col].dropna().unique()), key="v221_sub")
            stock_df = sub_df[sub_df[sub_col] == sub]
            with c:
                label_map = {f"{r[stock_col]} / {r[code_col]}": r[code_col] for _, r in stock_df.iterrows()}
                picked = st.selectbox("個股", list(label_map.keys()), key="v221_stock")
            with dcol:
                st.write("")
                st.write("")
                if st.button("套用", key="v221_apply", use_container_width=True):
                    st.session_state["v221_active_symbol"] = label_map[picked]
                    st.session_state["v221_query"] = label_map[picked]
                    st.rerun()

    v221_price_summary(symbol)

def global_competition():
    st.header("🌏 全球競爭力")
    with st.expander("AI受惠度如何評分？", expanded=False):
        v221_score_explanation()

    rows = v108_rows() if "v108_rows" in globals() else v107_rows()
    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("資料庫尚未載入。")
        return

    a,b = st.columns(2)
    with a:
        ind = st.selectbox("主產業", ["全部"] + sorted(df["產業"].dropna().unique()), key="v221_global_ind")
    if ind != "全部":
        df = df[df["產業"] == ind]
    with b:
        sub = st.selectbox("子產業", ["全部"] + sorted(df["子產業"].dropna().unique()), key="v221_global_sub")
    if sub != "全部":
        df = df[df["子產業"] == sub]

    st.dataframe(df.sort_values(["產業","子產業","代碼"]), use_container_width=True, hide_index=True)

# ===== V221.0 STABLE INVESTOR HOME PATCH END =====


def sidebar_nav():
    st.sidebar.title('智策股市 AI 平台')
    st.sidebar.caption(APP_VERSION)
    page = st.sidebar.radio('主選單', ['🏠 首頁','📈 股票分析','🏭 產業分析','🌏 全球競爭力','🏢 企業價值研究院','⭐ 自選股','⚙️ 設定'])
    q = st.sidebar.text_input('快速搜尋', placeholder='2330、台積電、5274、信驊')
    if q:
        set_active(q)
    st.sidebar.caption('公開版不顯示模型權重；如需研究資料請洽開發者。')
    return page

def selector_area():
    c1, c2 = st.columns([1.2,1])
    with c1:
        q = st.text_input('搜尋股票代碼或公司名稱', placeholder='例如：2330、台積電、2308、台達電、5274、信驊')
        if q:
            set_active(q)
    with c2:
        st.caption('現價每小時快取更新；重新整理頁面可取得最新資料。')
    with st.expander('產業快速導航', expanded=False):
        a,b,c = st.columns([1,1,.28])
        with a:
            ind = st.selectbox('選擇產業', industry_options())
        with b:
            picked = st.selectbox('選擇個股', stock_options(ind))
        with c:
            st.write(''); st.write('')
            if st.button('套用', use_container_width=True):
                set_active(picked.split('/')[-1].strip())
                st.rerun()

def quick_buttons():
    groups = [
        ('核心', [('台積電','2330'),('台達電','2308'),('信驊','5274'),('聯發科','2454'),('廣達','2382'),('大立光','3008')]),
        ('AI伺服器', [('緯穎','6669'),('緯創','3231'),('奇鋐','3017'),('雙鴻','3324'),('川湖','2059'),('台光電','2383')]),
        ('記憶體/被動', [('南亞科','2408'),('華邦電','2344'),('威剛','3260'),('群聯','8299'),('國巨','2327'),('華新科','2492')]),
    ]
    for title, items in groups:
        st.markdown(f'#### {title}快速查詢')
        cols = st.columns(len(items))
        for col, (label, qv) in zip(cols, items):
            with col:
                if st.button(label, key=f'quick_{qv}', use_container_width=True):
                    set_active(qv)
                    st.rerun()

def show_decision(symbol):
    d = decision(symbol)
    st.caption(f"資料更新時間：{d['updated']}｜現價來源：{d['source']}｜預期報酬率＝(合理價－現價)÷現價。")
    st.markdown(f'<div class="section-title">{d["name"]}（{d["symbol"]}）</div>', unsafe_allow_html=True)
    m1,m2,m3,m4 = st.columns(4)
    m1.metric('AI評級', d['rating']); m2.metric('投資建議', d['action']); m3.metric('現價', fmt_price(d['price'])); m4.metric('預期報酬', f"{d['ret']:.1f}%")
    p1,p2,p3 = st.columns(3)
    p1.metric('保守價', fmt_price(d['cons'])); p2.metric('合理價', fmt_price(d['fair'])); p3.metric('樂觀價', fmt_price(d['opt']))
    st.markdown('### 🌍 產業全球競爭')
    g1,g2,g3 = st.columns(3)
    g1.metric('全球競爭力', d['power']); g2.metric('產業排名', d['rank']); g3.metric('全球地位', d['position'])
    st.dataframe(pd.DataFrame([{'產業': d['industry'], '子產業': d['sub'], '主要競爭者': d['peers'], '護城河': d['moat'], '主要風險': d['risk']}]), use_container_width=True, hide_index=True)
    tabs = st.tabs(['投資人摘要','價格區間','風險提示','產業個股清單','研究說明'])
    with tabs[0]:
        st.dataframe(pd.DataFrame([{'公司': d['name'], '代碼': d['symbol'], 'AI評級': d['rating'], '投資建議': d['action'], '現價': fmt_price(d['price']), '合理價': fmt_price(d['fair']), '預期報酬': f"{d['ret']:.1f}%", '全球競爭力': d['power'], '更新時間': d['updated']}]), use_container_width=True, hide_index=True)
    with tabs[1]:
        st.dataframe(pd.DataFrame([{'保守價': fmt_price(d['cons']), '合理價': fmt_price(d['fair']), '樂觀價': fmt_price(d['opt']), '計算說明': 'V200預設區間＝現價×產業合理倍率；後續可接入DCF/EBO/EVA/CAP完整模型。'}]), use_container_width=True, hide_index=True)
    with tabs[2]:
        st.write(f"- 主要風險：{d['risk']}")
        st.write('- 若財報、產業景氣或市場利率變化，估值區間可能調整。')
        st.write('- 本頁為研究輔助，不等於保證報酬。')
    with tabs[3]:
        st.dataframe(pd.DataFrame(db_rows()).sort_values(['產業','子產業','代碼']), use_container_width=True, hide_index=True)
    with tabs[4]:
        st.info('模型細節屬內部研究方法；如需完整研究資料請洽開發者。')

def home():
    css()
    st.session_state.setdefault('active_symbol', '2330.TW')
    st.markdown(f'''<div class="hero"><div class="hero-title">智策股市 AI 決策平台</div><div class="hero-sub">上市櫃投資決策、合理價區間、預期報酬與全球競爭力分析</div><span class="badge">最後更新：{tw_now()}</span><span class="badge">資料來源：TWSE・TPEx・Yahoo Finance</span><span class="badge">模型細節：內部研究方法</span></div>''', unsafe_allow_html=True)
    st.markdown('<div class="note">請直接輸入股票代碼或公司名稱，也可從產業快速導航選股。首頁只保留投資人最需要的答案。</div>', unsafe_allow_html=True)
    selector_area(); quick_buttons(); show_decision(st.session_state['active_symbol'])

def industry_page():
    st.header('🏭 產業分析')
    ind = st.selectbox('選擇產業', industry_options(), key='ind_page')
    st.dataframe(pd.DataFrame([r for r in db_rows() if r['產業'] == ind]), use_container_width=True, hide_index=True)

def competition_page():
    st.header('🌏 全球競爭力')
    st.dataframe(pd.DataFrame(db_rows()).sort_values(['全球競爭力','產業'], ascending=[False,True]), use_container_width=True, hide_index=True)

def valuation_page():
    st.header('🏢 企業價值研究院')
    st.info('此頁保留 DCF、FCFF、FCFE、EVA、EBO、CAP、ESG Premium、Super Bull 模型入口。V200 先完成乾淨架構與資料庫。')
    show_decision(st.session_state.get('active_symbol','2330.TW'))

def watchlist():
    st.header('⭐ 自選股')
    syms = ['2330.TW','2308.TW','5274.TWO','2382.TW','3231.TW','6669.TW','3017.TW','3324.TWO','2327.TW','2408.TW','3008.TW']
    rows = []
    for s in syms:
        d = decision(s)
        rows.append({'公司': d['name'], '代碼': d['symbol'], '投資建議': d['action'], '現價': fmt_price(d['price']), '合理價': fmt_price(d['fair']), '預期報酬': f"{d['ret']:.1f}%", '全球競爭力': d['power']})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

def main():
    page = sidebar_nav()
    if page in ['🏠 首頁','📈 股票分析']:
        home()
    elif page == '🏭 產業分析':
        industry_page()
    elif page == '🌏 全球競爭力':
        competition_page()
    elif page == '🏢 企業價值研究院':
        valuation_page()
    elif page == '⭐ 自選股':
        watchlist()
    else:
        st.header('⚙️ 設定')
        st.write('版本：', APP_VERSION)
        st.write('資料庫股票數：', len(STOCK_DB))
        st.info('公開版不顯示模型權重。')



# ===== V222.0 FORCE INVESTOR PAGES START =====
def v222_fmt_price(x):
    try:
        if pd.isna(x): return "N/A"
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def v222_get_symbol(q):
    try:
        return v108_normalize_symbol(q)
    except Exception:
        try:
            return v107_get_symbol(q)
        except Exception:
            q=str(q or "").strip().upper()
            return q+".TW" if q.isdigit() else (q or "2330.TW")

def v222_get_decision(symbol):
    try:
        return v108_get_decision(symbol)
    except Exception:
        try:
            return v107_get_decision(symbol)
        except Exception:
            try:
                return decision(symbol)
            except Exception:
                return {"name":symbol,"price":np.nan,"fair":np.nan,"cons":np.nan,"opt":np.nan,"ret":0,"action":"觀察","updated":"N/A","source":"N/A"}

def v222_rows_df():
    for fn in ["v108_rows","v107_rows","db_rows"]:
        try:
            df = pd.DataFrame(globals()[fn]())
            if not df.empty:
                return df
        except Exception:
            pass
    return pd.DataFrame()

def v222_ai_score_explanation():
    st.markdown("""
### AI受惠度如何評分？

| 分數 | 說明 | 常見類型 |
|---:|---|---|
| 10 | AI核心基礎建設或不可或缺關鍵晶片 | 台積電、信驊、緯穎 |
| 9 | AI關鍵零組件，訂單與AI資本支出高度連動 | 台光電、奇鋐、雙鴻、CPO光通訊 |
| 8 | AI供應鏈直接受惠 | 封測、ABF載板、測試、ASIC設計服務 |
| 7 | AI需求明確帶動，但非唯一主軸 | 台達電、機器人、自動化 |
| 5~6 | 中度受惠 | AI PC、AI手機、光學 |
| 3~4 | 間接受惠 | 一般電子零組件 |
| 0 | 非AI主題 | 金融、航運、鋼鐵、塑化、食品等傳統產業 |
""")
    st.caption("傳統產業若不是AI直接供應鏈，不硬塞AI分數，改看成長驅動因子。")

def v222_investor_home():
    try:
        v108_css()
    except Exception:
        try: v107_css()
        except Exception: pass

    now_show = datetime.now().strftime("%Y/%m/%d %H:%M")
    st.markdown(f"""
    <div class="v108-hero">
      <div class="v108-title">智策股市 AI 決策平台</div>
      <div class="v108-sub">首頁先看價格與區間；深度資料收合在研究資料中。</div>
      <span class="v108-badge">最後更新：{now_show}</span>
      <span class="v108-badge">V222 Investor Home</span>
      <span class="v108-badge">一般投資人版</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="v108-note">一般投資人先看現價、保守價、合理價、樂觀價、預期報酬與投資建議；想深入再展開研究資料。</div>', unsafe_allow_html=True)

    q = st.text_input("搜尋股票代碼或公司名稱", value=st.session_state.get("v222_query","2330"), placeholder="例如：2330、台積電、2308、台達電、5274、信驊", key="v222_query_input")
    symbol = v222_get_symbol(q)
    st.session_state["v222_query"] = q

    quick = [("台積電","2330"),("台達電","2308"),("信驊","5274"),("聯發科","2454"),("廣達","2382"),("大立光","3008")]
    st.markdown("#### 核心快速查詢")
    cols = st.columns(len(quick))
    for col, (name, code_) in zip(cols, quick):
        with col:
            if st.button(name, key=f"v222_quick_{code_}", use_container_width=True):
                st.session_state["v222_query"] = code_
                st.rerun()

    with st.expander("產業 → 子產業 → 個股", expanded=False):
        df = v222_rows_df()
        if not df.empty and all(c in df.columns for c in ["產業","子產業","公司","代碼"]):
            c1,c2,c3,c4 = st.columns([1,1,1,0.25])
            with c1:
                ind = st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v222_home_ind")
            sub_df = df[df["產業"] == ind]
            with c2:
                sub = st.selectbox("子產業", sorted(sub_df["子產業"].dropna().unique()), key="v222_home_sub")
            stock_df = sub_df[sub_df["子產業"] == sub]
            labels = {f"{r['公司']} / {r['代碼']}": r["代碼"] for _, r in stock_df.iterrows()}
            with c3:
                picked = st.selectbox("個股", list(labels.keys()), key="v222_home_stock")
            with c4:
                st.write(""); st.write("")
                if st.button("套用", key="v222_home_apply", use_container_width=True):
                    st.session_state["v222_query"] = labels[picked]
                    st.rerun()

    d = v222_get_decision(symbol)
    fmtf = v222_fmt_price
    st.caption(f"資料更新時間：{d.get('updated','N/A')}｜現價來源：{d.get('source','Yahoo Finance')}｜預期報酬率＝(合理價－現價)÷現價。")
    st.markdown(f"## {d.get('name', symbol)}（{symbol}）")

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("投資建議", d.get("action","觀察"))
    m2.metric("現價", fmtf(d.get("price", np.nan)))
    m3.metric("合理價", fmtf(d.get("fair", np.nan)))
    try: ret_txt=f"{float(d.get('ret',0)):.1f}%"
    except Exception: ret_txt="N/A"
    m4.metric("預期報酬", ret_txt)

    p1,p2,p3 = st.columns(3)
    p1.metric("保守價", fmtf(d.get("cons", np.nan)))
    p2.metric("合理價", fmtf(d.get("fair", np.nan)))
    p3.metric("樂觀價", fmtf(d.get("opt", np.nan)))

    with st.expander("展開更多研究資料", expanded=False):
        st.markdown("### 全球競爭力與產業定位")
        g1,g2,g3 = st.columns(3)
        ai_score = d.get("ai_score", d.get("AI受惠度", 0))
        try: ai_txt=f"{int(ai_score)}/10" if int(ai_score)>0 else "非AI主題"
        except Exception: ai_txt=str(ai_score) if ai_score else "非AI主題"
        g1.metric("AI受惠度", ai_txt)
        g2.metric("全球競爭力", d.get("power", d.get("global_power","★★★☆☆")))
        g3.metric("產業排名", d.get("rank", d.get("global_rank","待補")))

        st.dataframe(pd.DataFrame([{
            "主產業":d.get("industry","待補"),
            "子產業":d.get("sub", d.get("sub_industry","待補")),
            "AI主題":d.get("theme_text", d.get("themes","非AI主題")) if ai_txt!="非AI主題" else "非AI主題",
            "全球地位":d.get("position", d.get("global_position","待補")),
            "主要競爭者":d.get("peers", d.get("competitors","待補")),
            "護城河":d.get("moat","待補"),
            "主要風險":d.get("risk","待補")
        }]), use_container_width=True, hide_index=True)
        v222_ai_score_explanation()

def home():
    v222_investor_home()

def v108_enterprise_home():
    v222_investor_home()

def v107_premium_home():
    v222_investor_home()

def industry_analysis():
    st.header("🏭 產業分析")
    df = v222_rows_df()
    if df.empty:
        st.warning("資料庫尚未載入。"); return
    c1,c2 = st.columns(2)
    with c1:
        ind = st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v222_industry_ind")
    dff = df[df["產業"] == ind]
    with c2:
        sub = st.selectbox("子產業", ["全部"] + sorted(dff["子產業"].dropna().unique()), key="v222_industry_sub")
    if sub != "全部":
        dff = dff[dff["子產業"] == sub]
    st.dataframe(dff.sort_values(["產業","子產業","代碼"]), use_container_width=True, hide_index=True)

def global_competition():
    st.header("🌏 全球競爭力")
    with st.expander("AI受惠度如何評分？", expanded=True):
        v222_ai_score_explanation()
    df = v222_rows_df()
    if df.empty:
        st.warning("資料庫尚未載入。"); return
    c1,c2,c3 = st.columns(3)
    with c1:
        ind = st.selectbox("主產業", ["全部"] + sorted(df["產業"].dropna().unique()), key="v222_global_ind")
    if ind != "全部":
        df = df[df["產業"] == ind]
    with c2:
        sub = st.selectbox("子產業", ["全部"] + sorted(df["子產業"].dropna().unique()), key="v222_global_sub")
    if sub != "全部":
        df = df[df["子產業"] == sub]
    with c3:
        labels = ["全部"] + [f"{r['公司']} / {r['代碼']}" for _, r in df.iterrows()]
        picked = st.selectbox("個股", labels, key="v222_global_stock")
    if picked != "全部":
        df = df[df["代碼"] == picked.split("/")[-1].strip()]
    st.dataframe(df.sort_values(["產業","子產業","代碼"]), use_container_width=True, hide_index=True)
# ===== V222.0 FORCE INVESTOR PAGES END =====





# ===== V223.0 DIRECT SELECT + GLOBAL COMPETITION DETAIL START =====
# 修正：
# 1) 首頁取消套用按鈕，選到個股後直接切換
# 2) 全球競爭力頁面改成 主產業 → 子產業 → 個股
# 3) AI受惠度說明固定放在全球競爭力頁面底下

def v223_fmt(x):
    try:
        if pd.isna(x): return "N/A"
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def v223_symbol(q):
    try:
        return v108_normalize_symbol(q)
    except Exception:
        try:
            return v107_get_symbol(q)
        except Exception:
            q = str(q or "").strip().upper()
            if q.isdigit(): return q + ".TW"
            return q or "2330.TW"

def v223_decision(symbol):
    try:
        return v108_get_decision(symbol)
    except Exception:
        try:
            return v107_get_decision(symbol)
        except Exception:
            return {"name":symbol,"industry":"待補","sub":"待補","price":np.nan,"fair":np.nan,"cons":np.nan,"opt":np.nan,"ret":0,"action":"觀察","updated":"N/A","source":"N/A","power":"★★★☆☆","rank":"待補","position":"待補","peers":"待補","moat":"待補","risk":"待補","theme_text":"非AI主題","ai_score":0}

def v223_rows_df():
    for fn in ["v108_rows","v107_rows","db_rows"]:
        try:
            df = pd.DataFrame(globals()[fn]())
            if not df.empty:
                return df
        except Exception:
            pass
    return pd.DataFrame()

def v223_ai_score_explanation():
    st.markdown("### AI受惠度如何評分？")
    st.dataframe(pd.DataFrame([
        {"分數":"10","說明":"AI核心基礎建設或不可或缺關鍵晶片","常見類型":"台積電、信驊、緯穎"},
        {"分數":"9","說明":"AI關鍵零組件，訂單與AI資本支出高度連動","常見類型":"台光電、奇鋐、雙鴻、CPO光通訊"},
        {"分數":"8","說明":"AI供應鏈直接受惠","常見類型":"封測、ABF載板、測試、ASIC設計服務"},
        {"分數":"7","說明":"AI需求明確帶動，但非唯一主軸","常見類型":"台達電、機器人、自動化"},
        {"分數":"5~6","說明":"中度受惠","常見類型":"AI PC、AI手機、光學"},
        {"分數":"3~4","說明":"間接受惠","常見類型":"一般電子零組件"},
        {"分數":"0","說明":"非AI主題","常見類型":"金融、航運、鋼鐵、塑化、食品等傳統產業"},
    ]), use_container_width=True, hide_index=True)
    st.caption("傳統產業若不是AI直接供應鏈，不硬塞AI分數，改看成長驅動因子。")

def v223_price_block(symbol):
    d = v223_decision(symbol)
    fmtf = v223_fmt
    st.caption(f"資料更新時間：{d.get('updated','N/A')}｜現價來源：{d.get('source','Yahoo Finance')}｜預期報酬率＝(合理價－現價)÷現價。")
    st.markdown(f"## {d.get('name', symbol)}（{symbol}）")

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("投資建議", d.get("action","觀察"))
    m2.metric("現價", fmtf(d.get("price", np.nan)))
    m3.metric("合理價", fmtf(d.get("fair", np.nan)))
    try: ret_txt = f"{float(d.get('ret',0)):.1f}%"
    except Exception: ret_txt = "N/A"
    m4.metric("預期報酬", ret_txt)

    p1,p2,p3 = st.columns(3)
    p1.metric("保守價", fmtf(d.get("cons", np.nan)))
    p2.metric("合理價", fmtf(d.get("fair", np.nan)))
    p3.metric("樂觀價", fmtf(d.get("opt", np.nan)))

    with st.expander("展開更多研究資料", expanded=False):
        st.markdown("### 全球競爭力與產業定位")
        ai_score = d.get("ai_score", d.get("AI受惠度", 0))
        try: ai_txt = f"{int(ai_score)}/10" if int(ai_score)>0 else "非AI主題"
        except Exception: ai_txt = str(ai_score) if ai_score else "非AI主題"
        c1,c2,c3 = st.columns(3)
        c1.metric("AI受惠度", ai_txt)
        c2.metric("全球競爭力", d.get("power", d.get("global_power","★★★☆☆")))
        c3.metric("產業排名", d.get("rank", d.get("global_rank","待補")))

        st.dataframe(pd.DataFrame([{
            "主產業":d.get("industry","待補"),
            "子產業":d.get("sub", d.get("sub_industry","待補")),
            "AI主題":d.get("theme_text", d.get("themes","非AI主題")) if ai_txt!="非AI主題" else "非AI主題",
            "全球地位":d.get("position", d.get("global_position","待補")),
            "主要競爭者":d.get("peers", d.get("competitors","待補")),
            "護城河":d.get("moat","待補"),
            "主要風險":d.get("risk","待補")
        }]), use_container_width=True, hide_index=True)

def home():
    try:
        v108_css()
    except Exception:
        try: v107_css()
        except Exception: pass

    if "v223_active_symbol" not in st.session_state:
        st.session_state["v223_active_symbol"] = "2330.TW"

    now_show = datetime.now().strftime("%Y/%m/%d %H:%M")
    st.markdown(f"""
    <div class="v108-hero">
      <div class="v108-title">智策股市 AI 決策平台</div>
      <div class="v108-sub">首頁先看價格與區間；深度資料收合在研究資料中。</div>
      <span class="v108-badge">最後更新：{now_show}</span>
      <span class="v108-badge">V223 Direct Select</span>
      <span class="v108-badge">一般投資人版</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="v108-note">一般投資人先看現價、保守價、合理價、樂觀價、預期報酬與投資建議；選到個股後直接切換，不必再按套用。</div>', unsafe_allow_html=True)

    q = st.text_input("搜尋股票代碼或公司名稱", placeholder="例如：2330、台積電、2308、台達電、5274、信驊", key="v223_search")
    if str(q or "").strip():
        st.session_state["v223_active_symbol"] = v223_symbol(q)

    quick = [("台積電","2330"),("台達電","2308"),("信驊","5274"),("聯發科","2454"),("廣達","2382"),("大立光","3008")]
    st.markdown("#### 核心快速查詢")
    cols = st.columns(len(quick))
    for col, (name, code_) in zip(cols, quick):
        with col:
            if st.button(name, key=f"v223_quick_{code_}", use_container_width=True):
                st.session_state["v223_active_symbol"] = v223_symbol(code_)
                st.rerun()

    with st.expander("產業 → 子產業 → 個股", expanded=False):
        df = v223_rows_df()
        if not df.empty and all(c in df.columns for c in ["產業","子產業","公司","代碼"]):
            c1,c2,c3 = st.columns(3)
            with c1:
                ind = st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v223_home_ind")
            sub_df = df[df["產業"] == ind]
            with c2:
                sub = st.selectbox("子產業", sorted(sub_df["子產業"].dropna().unique()), key="v223_home_sub")
            stock_df = sub_df[sub_df["子產業"] == sub]
            labels = {f"{r['公司']} / {r['代碼']}": r["代碼"] for _, r in stock_df.iterrows()}
            with c3:
                picked = st.selectbox("個股（選到後直接切換）", list(labels.keys()), key="v223_home_stock")
            selected_code = labels.get(picked)
            if selected_code and st.session_state.get("v223_last_pick") != picked:
                st.session_state["v223_last_pick"] = picked
                st.session_state["v223_active_symbol"] = selected_code
                st.rerun()

    v223_price_block(st.session_state.get("v223_active_symbol","2330.TW"))

def industry_page():
    st.header("🏭 產業分析")
    df = v223_rows_df()
    if df.empty:
        st.warning("資料庫尚未載入。"); return
    c1,c2 = st.columns(2)
    with c1:
        ind = st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v223_industry_ind")
    dff = df[df["產業"] == ind]
    with c2:
        sub = st.selectbox("子產業", ["全部"] + sorted(dff["子產業"].dropna().unique()), key="v223_industry_sub")
    if sub != "全部":
        dff = dff[dff["子產業"] == sub]
    st.dataframe(dff.sort_values(["產業","子產業","代碼"]), use_container_width=True, hide_index=True)

def competition_page():
    st.header("🌏 全球競爭力")
    df = v223_rows_df()
    if df.empty:
        st.warning("資料庫尚未載入。"); return

    c1,c2,c3 = st.columns(3)
    with c1:
        ind = st.selectbox("主產業", ["全部"] + sorted(df["產業"].dropna().unique()), key="v223_global_ind")
    if ind != "全部":
        df = df[df["產業"] == ind]
    with c2:
        sub = st.selectbox("子產業", ["全部"] + sorted(df["子產業"].dropna().unique()), key="v223_global_sub")
    if sub != "全部":
        df = df[df["子產業"] == sub]
    with c3:
        labels = ["全部"] + [f"{r['公司']} / {r['代碼']}" for _, r in df.iterrows()]
        picked = st.selectbox("個股", labels, key="v223_global_stock")

    if picked != "全部":
        code_ = picked.split("/")[-1].strip()
        row = df[df["代碼"] == code_]
        if not row.empty:
            r = row.iloc[0].to_dict()
            st.markdown(f"## {r.get('公司','')}（{r.get('代碼','')}）")
            m1,m2,m3 = st.columns(3)
            ai = r.get("AI受惠度", "")
            ai_txt = f"{ai}/10" if str(ai).strip() not in ["", "0", "0.0", "nan"] else "非AI主題"
            m1.metric("AI受惠度", ai_txt)
            m2.metric("全球競爭力", r.get("全球競爭力",""))
            m3.metric("產業地位", r.get("產業地位",""))
            st.dataframe(pd.DataFrame([r]), use_container_width=True, hide_index=True)
    else:
        st.dataframe(df.sort_values(["產業","子產業","代碼"]), use_container_width=True, hide_index=True)

    st.markdown("---")
    v223_ai_score_explanation()

# 保險：若舊版路由還呼叫這些名稱，也導向新版
def global_competition():
    competition_page()

def industry_analysis():
    industry_page()

def v108_enterprise_home():
    home()

def v107_premium_home():
    home()
# ===== V223.0 DIRECT SELECT + GLOBAL COMPETITION DETAIL END =====





# ===== V224.0 RESEARCH PAGES + STOCK EXPANSION START =====
# 1) 首頁使用核心 decision() + fallback price，降低 N/A
# 2) 產業分析改成 主產業/子產業/產業規模/成長率/AI關聯度/主要公司
# 3) 全球競爭力改成 主產業/子產業/個股 + 詳細卡片
# 4) 順便補齊部分重點股票資料

V224_EXTRA_STOCKS = {
    "1504.TW":{"name":"東元","industry":"電力/重電","sub":"馬達/機電/電網","rank":"馬達與機電主要廠","power":"★★★★☆","position":"馬達、機電與能源設備供應商","peers":"ABB、Siemens、WEG、中興電","moat":"中高：馬達技術、機電整合、品牌通路","risk":"原料、匯率、景氣循環","fair_mult":1.05},
    "1514.TW":{"name":"亞力","industry":"電力/重電","sub":"電力設備/配電","rank":"配電設備供應商","power":"★★★☆☆","position":"電力設備與配電盤供應商","peers":"華城、中興電、士電","moat":"中：電力設備認證與工程經驗","risk":"政策進度、原料成本","fair_mult":1.06},
    "1605.TW":{"name":"華新","industry":"電線電纜","sub":"電線電纜/不銹鋼","rank":"電纜主要廠","power":"★★★☆☆","position":"電線電纜與不銹鋼供應商","peers":"大亞、合機、東元","moat":"中：電纜產能與通路","risk":"銅價、景氣循環","fair_mult":1.02},
    "1609.TW":{"name":"大亞","industry":"電線電纜","sub":"電線電纜/綠能","rank":"電纜主要廠","power":"★★★☆☆","position":"電線電纜與綠能題材供應商","peers":"華新、合機、華榮","moat":"中：電纜產能與能源轉型題材","risk":"銅價、政策進度","fair_mult":1.04},
    "3023.TW":{"name":"信邦","industry":"車用/連接線","sub":"連接線/車用電子","rank":"連接線主要廠","power":"★★★★☆","position":"車用、工控與綠能連接線供應商","peers":"貿聯-KY、胡連、正崴","moat":"中高：客戶認證、多元應用","risk":"車市循環、匯率","fair_mult":1.05},
    "3665.TW":{"name":"貿聯-KY","industry":"車用/連接線","sub":"車用/高速線束","rank":"全球線束主要廠","power":"★★★★☆","position":"車用與高速線束供應商","peers":"信邦、Aptiv、TE Connectivity","moat":"中高：車用客戶認證與全球產能","risk":"車用需求、匯率","fair_mult":1.07},
    "6415.TW":{"name":"矽力-KY","industry":"IC設計","sub":"PMIC/電源管理IC","rank":"PMIC主要廠","power":"★★★★☆","position":"電源管理IC供應商","peers":"TI、MPS、立錡、致新","moat":"中高：PMIC產品線與客戶導入","risk":"庫存循環、競爭","fair_mult":1.06},
    "3529.TWO":{"name":"力旺","industry":"IC設計","sub":"矽智財/IP","rank":"IP授權利基廠","power":"★★★★☆","position":"嵌入式非揮發性記憶體IP供應商","peers":"Synopsys、ARM、M31、晶心科","moat":"高：IP授權、製程導入、高毛利","risk":"授權案時程、客戶集中","fair_mult":1.10},
    "6643.TWO":{"name":"M31","industry":"IC設計","sub":"高速IP/矽智財","rank":"IP供應商","power":"★★★★☆","position":"高速介面IP與矽智財供應商","peers":"Synopsys、Cadence、力旺、晶心科","moat":"中高：高速IP與客戶導入","risk":"授權波動、先進製程競爭","fair_mult":1.08},
    "6533.TW":{"name":"晶心科","industry":"IC設計","sub":"RISC-V IP","rank":"RISC-V IP主要廠","power":"★★★★☆","position":"RISC-V處理器IP供應商","peers":"ARM、SiFive、MIPS、Synopsys","moat":"中高：RISC-V IP與工具鏈","risk":"IP商業化速度、競爭","fair_mult":1.08},
    "4966.TW":{"name":"譜瑞-KY","industry":"IC設計","sub":"高速傳輸IC","rank":"高速介面IC主要廠","power":"★★★★☆","position":"高速傳輸與顯示介面IC供應商","peers":"祥碩、瑞昱、Parade同業","moat":"中高：高速介面IC技術","risk":"PC/消費電子循環","fair_mult":1.06},
    "5269.TW":{"name":"祥碩","industry":"IC設計","sub":"高速傳輸IC","rank":"USB控制IC主要廠","power":"★★★★☆","position":"高速傳輸控制IC供應商","peers":"瑞昱、譜瑞、創惟","moat":"中高：高速傳輸IC與平台認證","risk":"PC平台循環、產品週期","fair_mult":1.06},
    "6442.TW":{"name":"光聖","industry":"光通訊/CPO","sub":"光通訊元件","rank":"光通訊元件供應商","power":"★★★★☆","position":"資料中心光通訊零組件供應商","peers":"華星光、上詮、眾達、Finisar","moat":"中高：光通訊元件與客戶導入","risk":"出貨時程、競爭","fair_mult":1.10},
    "3081.TWO":{"name":"聯亞","industry":"光通訊/CPO","sub":"磊晶/光通訊元件","rank":"光通訊磊晶供應商","power":"★★★★☆","position":"光通訊磊晶與雷射元件供應商","peers":"華星光、上詮、Lumentum、Coherent","moat":"中高：磊晶與光元件技術","risk":"CPO導入時程、客戶集中","fair_mult":1.10},
    "3363.TWO":{"name":"上詮","industry":"光通訊/CPO","sub":"光通訊元件","rank":"光通訊元件供應商","power":"★★★☆☆","position":"光通訊與資料中心元件供應商","peers":"華星光、聯亞、眾達","moat":"中：光通訊元件與客戶導入","risk":"需求波動、競爭","fair_mult":1.08},
    "4977.TWO":{"name":"眾達-KY","industry":"光通訊/CPO","sub":"光收發模組","rank":"光通訊模組供應商","power":"★★★☆☆","position":"光收發模組與資料中心光通訊供應商","peers":"華星光、上詮、光聖","moat":"中：光模組設計與客戶基礎","risk":"需求波動、客戶集中","fair_mult":1.06},
    "8046.TW":{"name":"南電","industry":"PCB/載板","sub":"ABF/BT載板","rank":"ABF載板主要廠","power":"★★★★☆","position":"載板與封裝基板重要供應商","peers":"欣興、景碩、Ibiden、Shinko","moat":"中高：載板產能與集團資源","risk":"ABF需求循環、價格壓力","fair_mult":1.04},
    "3189.TWO":{"name":"景碩","industry":"PCB/載板","sub":"ABF/BT載板","rank":"載板主要廠","power":"★★★☆☆","position":"ABF與BT載板供應商","peers":"欣興、南電、Ibiden","moat":"中：載板技術與客戶認證","risk":"載板循環、價格壓力","fair_mult":1.02},
    "4958.TW":{"name":"臻鼎-KY","industry":"PCB/載板","sub":"PCB/HDI","rank":"全球PCB龍頭之一","power":"★★★★☆","position":"全球PCB與HDI主要供應商","peers":"欣興、華通、健鼎、TTM","moat":"中高：規模、客戶認證、製程","risk":"客戶集中、消費電子循環","fair_mult":1.04},
    "3044.TW":{"name":"健鼎","industry":"PCB/載板","sub":"PCB","rank":"PCB主要廠","power":"★★★☆☆","position":"PCB量產與車用/伺服器板供應商","peers":"欣興、華通、瀚宇博","moat":"中：PCB量產能力與客戶基礎","risk":"景氣循環、原料成本","fair_mult":1.03},
    "3406.TW":{"name":"玉晶光","industry":"光學","sub":"手機/AR光學鏡頭","rank":"全球主要鏡頭廠","power":"★★★★☆","position":"手機與AR/VR光學供應商","peers":"大立光、Sunny Optical、AAC","moat":"中高：光學製程與客戶導入","risk":"手機需求循環、毛利波動","fair_mult":1.05},
    "3019.TW":{"name":"亞光","industry":"光學","sub":"光學模組","rank":"光學模組供應商","power":"★★★☆☆","position":"光學模組與影像應用供應商","peers":"大立光、玉晶光、舜宇光學","moat":"中：光學模組與車用應用","risk":"需求循環、競爭","fair_mult":1.03},
    "6789.TW":{"name":"采鈺","industry":"光學","sub":"CIS/影像感測","rank":"影像感測封裝供應商","power":"★★★☆☆","position":"影像感測與光學相關封裝供應商","peers":"Sony供應鏈、同欣電、精材","moat":"中：影像感測封裝能力","risk":"手機/車用需求循環","fair_mult":1.04},
    "2492.TW":{"name":"華新科","industry":"被動元件","sub":"MLCC/晶片電阻","rank":"台灣被動元件主要廠","power":"★★★★☆","position":"MLCC與晶片電阻重要供應商","peers":"國巨、Murata、TDK","moat":"中：車用/工規被動元件","risk":"價格循環、庫存調整","fair_mult":1.06},
    "3026.TW":{"name":"禾伸堂","industry":"被動元件","sub":"MLCC/被動元件","rank":"被動元件供應商","power":"★★★☆☆","position":"MLCC與被動元件供應商","peers":"國巨、華新科、Murata","moat":"中：MLCC產品與通路","risk":"景氣循環、價格波動","fair_mult":1.03},
    "2375.TW":{"name":"凱美","industry":"被動元件","sub":"鋁電容/被動元件","rank":"電容供應商","power":"★★★☆☆","position":"鋁電容與被動元件供應商","peers":"立隆電、Nichicon、Nippon Chemi-Con","moat":"中：電容產品線與通路","risk":"價格循環、庫存","fair_mult":1.03},
    "2472.TW":{"name":"立隆電","industry":"被動元件","sub":"鋁電容","rank":"鋁電容供應商","power":"★★★☆☆","position":"鋁電容與固態電容供應商","peers":"凱美、Nichicon、Nippon Chemi-Con","moat":"中：電容產品與車用/工控應用","risk":"原料成本、景氣循環","fair_mult":1.03},
    "3260.TWO":{"name":"威剛","industry":"記憶體","sub":"記憶體模組","rank":"記憶體模組主要通路商","power":"★★★☆☆","position":"DRAM/NAND模組與通路供應商","peers":"創見、十銓、金士頓","moat":"中：模組品牌、通路、庫存操作","risk":"記憶體價格波動、庫存","fair_mult":1.08},
    "4967.TWO":{"name":"十銓","industry":"記憶體","sub":"記憶體模組","rank":"模組供應商","power":"★★★☆☆","position":"記憶體模組與電競儲存供應商","peers":"威剛、創見、金士頓","moat":"中：品牌與通路","risk":"記憶體價格波動、庫存","fair_mult":1.06},
    "2451.TW":{"name":"創見","industry":"記憶體","sub":"工控記憶體模組","rank":"工控模組品牌","power":"★★★☆☆","position":"工控與嵌入式記憶體模組供應商","peers":"威剛、十銓、宇瞻","moat":"中：工控通路、產品穩定性","risk":"記憶體價格波動、庫存","fair_mult":1.04},
    "2881.TW":{"name":"富邦金","industry":"金融","sub":"金控/壽險/銀行","rank":"台灣大型金控","power":"★★★★☆","position":"壽險、銀行、證券綜合金控","peers":"國泰金、中信金、兆豐金","moat":"中高：金融通路與資本規模","risk":"利率、股債市、信用風險","fair_mult":1.02},
    "2882.TW":{"name":"國泰金","industry":"金融","sub":"金控/壽險/銀行","rank":"台灣大型金控","power":"★★★★☆","position":"壽險與銀行大型金控","peers":"富邦金、中信金、兆豐金","moat":"中高：壽險規模、金融通路","risk":"利率、匯率、股債市","fair_mult":1.02},
    "2891.TW":{"name":"中信金","industry":"金融","sub":"金控/銀行","rank":"銀行型金控","power":"★★★★☆","position":"銀行與金融服務金控","peers":"富邦金、國泰金、玉山金","moat":"中高：銀行通路、財管能力","risk":"利差、信用風險、景氣","fair_mult":1.02},
    "2886.TW":{"name":"兆豐金","industry":"金融","sub":"公股銀行金控","rank":"公股大型金控","power":"★★★★☆","position":"公股銀行金控與外匯業務","peers":"第一金、華南金、合庫金","moat":"中高：公股銀行通路與外匯業務","risk":"利差、政策、信用風險","fair_mult":1.02},
    "2603.TW":{"name":"長榮","industry":"航運","sub":"貨櫃航運","rank":"全球貨櫃航運主要業者","power":"★★★★☆","position":"全球貨櫃航運公司","peers":"Maersk、MSC、CMA CGM、陽明","moat":"中：船隊規模與航線布局","risk":"運價循環、油價、地緣政治","fair_mult":1.00},
    "2609.TW":{"name":"陽明","industry":"航運","sub":"貨櫃航運","rank":"全球貨櫃航運業者","power":"★★★☆☆","position":"貨櫃航運公司","peers":"長榮、萬海、Maersk、MSC","moat":"中：航線與船隊","risk":"運價循環、油價","fair_mult":0.98},
    "2615.TW":{"name":"萬海","industry":"航運","sub":"貨櫃航運","rank":"亞洲航線主要業者","power":"★★★☆☆","position":"區域貨櫃航運公司","peers":"長榮、陽明、區域航商","moat":"中：區域航線布局","risk":"運價循環、油價","fair_mult":0.98},
}
try:
    STOCK_DB.update(V224_EXTRA_STOCKS)
    ALIASES.clear()
    for sym, v in STOCK_DB.items():
        ALIASES[sym.upper()] = sym
        ALIASES[sym.split(".")[0]] = sym
        ALIASES[v["name"]] = sym
        ALIASES[v["name"].upper()] = sym
except Exception:
    pass

V224_FALLBACK_PRICE = {
    "2330.TW":2340,"2308.TW":1810,"2454.TW":1520,"5274.TWO":6200,"3661.TW":4200,"3443.TW":900,"3035.TW":95,
    "2382.TW":300,"3231.TW":120,"6669.TW":2800,"2317.TW":210,"3017.TW":950,"3324.TWO":760,"2059.TW":3300,
    "2383.TW":1500,"3037.TW":180,"8046.TW":130,"2408.TW":65,"8299.TWO":600,"2327.TW":600,"3008.TW":4720,
    "4979.TWO":250,"6215.TWO":90,"2049.TW":230,"2359.TW":126.5,"1519.TW":650,"1513.TW":180,"2357.TW":701,
    "6415.TW":520,"3529.TWO":2500,"6643.TWO":1200,"6533.TW":520,"4966.TW":800,"5269.TW":1400,"6442.TW":760,
    "3081.TWO":450,"3363.TWO":220,"2492.TW":120,"3260.TWO":110,"2881.TW":90,"2882.TW":75,"2603.TW":220
}

V224_INDUSTRY_META = {
    "半導體": {"規模":"極大","成長率":"中高","AI關聯度":"極高","說明":"AI算力、先進製程、成熟製程與封測核心供應鏈"},
    "IC設計": {"規模":"大","成長率":"高","AI關聯度":"極高","說明":"AI ASIC、BMC、SoC、IP、PMIC與高速傳輸IC"},
    "AI伺服器/ODM": {"規模":"大","成長率":"高","AI關聯度":"極高","說明":"雲端伺服器、AI伺服器ODM與EMS"},
    "AI PC/品牌": {"規模":"中大","成長率":"中","AI關聯度":"中高","說明":"AI PC、主機板、品牌PC與週邊平台"},
    "散熱": {"規模":"中","成長率":"高","AI關聯度":"極高","說明":"AI伺服器散熱、液冷、均熱片與風扇"},
    "電子材料": {"規模":"中大","成長率":"高","AI關聯度":"高","說明":"高速CCL、AI伺服器材料與電子材料"},
    "PCB/載板": {"規模":"大","成長率":"中高","AI關聯度":"高","說明":"ABF載板、HDI、PCB與先進封裝基板"},
    "光通訊/CPO": {"規模":"中","成長率":"高","AI關聯度":"極高","說明":"資料中心光模組、CPO、矽光與光通訊元件"},
    "記憶體": {"規模":"大","成長率":"高循環","AI關聯度":"高","說明":"DRAM、NAND、SSD控制IC、記憶體模組"},
    "被動元件": {"規模":"中大","成長率":"中","AI關聯度":"中","說明":"MLCC、電阻、電感、電容，受AI伺服器與車用帶動"},
    "光學": {"規模":"中","成長率":"中","AI關聯度":"中","說明":"手機鏡頭、AR/VR、車用鏡頭與機器視覺"},
    "自動化/機器人": {"規模":"中","成長率":"中高","AI關聯度":"高","說明":"工業自動化、機器視覺、機器人零組件與整合"},
    "電力/重電": {"規模":"中大","成長率":"中高","AI關聯度":"非直接AI","說明":"電網升級、變壓器、配電與能源轉型"},
    "電線電纜": {"規模":"中","成長率":"中","AI關聯度":"非直接AI","說明":"電網、建設、綠能與工業用電線電纜"},
    "車用/連接線": {"規模":"中大","成長率":"中高","AI關聯度":"間接","說明":"車用線束、連接線、EV與工控連接需求"},
    "金融": {"規模":"極大","成長率":"低中","AI關聯度":"非AI主題","說明":"利率、金融通路、壽險、銀行與資本市場"},
    "航運": {"規模":"大","成長率":"循環","AI關聯度":"非AI主題","說明":"運價循環、貨櫃航運與全球貿易"},
}

def v224_fmt(x):
    try:
        if pd.isna(x): return "N/A"
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def v224_symbol(q):
    try:
        return normalize_symbol(q)
    except Exception:
        q=str(q or "").strip().upper()
        return q+".TW" if q.isdigit() else (q or "2330.TW")

def v224_decision(symbol):
    try:
        d = decision(symbol)
    except Exception:
        d = v223_decision(symbol) if "v223_decision" in globals() else {}
    symbol = d.get("symbol", v224_symbol(symbol))
    if pd.isna(d.get("price", np.nan)) or d.get("price", np.nan) in [None, "N/A"]:
        price = V224_FALLBACK_PRICE.get(symbol, np.nan)
        mult = float(d.get("fair_mult", STOCK_DB.get(symbol, {}).get("fair_mult", 1.0)))
        if pd.notna(price) and price > 0:
            d["price"] = price
            d["cons"] = price * max(.78, mult - .16)
            d["fair"] = price * mult
            d["opt"] = price * (mult + .14)
            d["ret"] = (d["fair"] / price - 1) * 100
            d["source"] = "Yahoo Finance / fallback估算"
        else:
            d.setdefault("price", np.nan); d.setdefault("cons", np.nan); d.setdefault("fair", np.nan); d.setdefault("opt", np.nan); d.setdefault("ret", 0)
    d.setdefault("symbol", symbol)
    d.setdefault("name", STOCK_DB.get(symbol, {}).get("name", symbol))
    d.setdefault("industry", STOCK_DB.get(symbol, {}).get("industry", "待補"))
    d.setdefault("sub", STOCK_DB.get(symbol, {}).get("sub", "待補"))
    d.setdefault("updated", tw_now() if "tw_now" in globals() else "N/A")
    return d

def v224_ai_score(d):
    t = d.get("theme_text", "")
    industry = d.get("industry", "")
    sym = d.get("symbol", "")
    if "AI ASIC" in t or "CoWoS" in t or sym in ["2330.TW","5274.TWO","6669.TW"]:
        return 10
    if any(k in t for k in ["AI伺服器","CPO","液冷","光通訊"]) or industry in ["散熱","光通訊/CPO"]:
        return 9
    if any(k in t for k in ["HBM","記憶體","ABF","先進封裝"]) or industry in ["PCB/載板"]:
        return 8
    if industry in ["自動化/機器人","電源/能源管理"] or "機器人" in t:
        return 7
    if industry in ["AI PC/品牌","光學"]:
        return 6
    if industry in ["金融","航運","電力/重電","電線電纜"]:
        return 0
    return 2

def v224_rows_df():
    rows = []
    for sym, v in STOCK_DB.items():
        d = {**v, "symbol": sym}
        ai = v224_ai_score(d)
        rows.append({
            "產業": v.get("industry","待補"),
            "子產業": v.get("sub","待補"),
            "公司": v.get("name",sym),
            "代碼": sym,
            "AI主題": v.get("theme_text", "一般產業" if ai > 0 else "非AI主題"),
            "AI受惠度": ai,
            "全球競爭力": v.get("power","★★★☆☆"),
            "全球排名": v.get("rank","待補"),
            "產業地位": v.get("position","待補"),
            "主要競爭者": v.get("peers","待補"),
            "護城河": v.get("moat","待補"),
            "主要風險": v.get("risk","待補"),
        })
    return pd.DataFrame(rows)

def v224_ai_score_explanation():
    st.markdown("### AI受惠度評分說明")
    st.dataframe(pd.DataFrame([
        {"分數":"10","說明":"AI核心基礎建設或不可或缺關鍵晶片","常見類型":"台積電、信驊、緯穎"},
        {"分數":"9","說明":"AI關鍵零組件，訂單與AI資本支出高度連動","常見類型":"台光電、奇鋐、雙鴻、CPO光通訊"},
        {"分數":"8","說明":"AI供應鏈直接受惠","常見類型":"封測、ABF載板、測試、ASIC設計服務"},
        {"分數":"7","說明":"AI需求明確帶動，但非唯一主軸","常見類型":"台達電、機器人、自動化"},
        {"分數":"5~6","說明":"中度受惠","常見類型":"AI PC、AI手機、光學"},
        {"分數":"3~4","說明":"間接受惠","常見類型":"一般電子零組件"},
        {"分數":"0","說明":"非AI主題","常見類型":"金融、航運、鋼鐵、塑化、食品等傳統產業"},
    ]), use_container_width=True, hide_index=True)
    st.caption("傳統產業若不是AI直接供應鏈，不硬塞AI分數，改看成長驅動因子。")

def v224_price_block(symbol):
    d = v224_decision(symbol)
    st.caption(f"資料更新時間：{d.get('updated','N/A')}｜現價來源：{d.get('source','Yahoo Finance')}｜預期報酬率＝(合理價－現價)÷現價。")
    st.markdown(f"## {d.get('name', symbol)}（d.get('symbol', symbol)）".replace("d.get('symbol', symbol)", d.get("symbol", symbol)))
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("投資建議", d.get("action","觀察"))
    c2.metric("現價", v224_fmt(d.get("price", np.nan)))
    c3.metric("合理價", v224_fmt(d.get("fair", np.nan)))
    try: ret_txt = f"{float(d.get('ret',0)):.1f}%"
    except Exception: ret_txt = "N/A"
    c4.metric("預期報酬", ret_txt)
    p1,p2,p3 = st.columns(3)
    p1.metric("保守價", v224_fmt(d.get("cons", np.nan)))
    p2.metric("合理價", v224_fmt(d.get("fair", np.nan)))
    p3.metric("樂觀價", v224_fmt(d.get("opt", np.nan)))
    with st.expander("展開更多研究資料", expanded=False):
        ai = v224_ai_score(d)
        g1,g2,g3 = st.columns(3)
        g1.metric("AI受惠度", f"{ai}/10" if ai > 0 else "非AI主題")
        g2.metric("全球競爭力", d.get("power","★★★☆☆"))
        g3.metric("產業排名", d.get("rank","待補"))
        st.dataframe(pd.DataFrame([{
            "主產業":d.get("industry","待補"),
            "子產業":d.get("sub","待補"),
            "AI主題":d.get("theme_text","一般產業" if ai>0 else "非AI主題"),
            "全球地位":d.get("position","待補"),
            "主要競爭者":d.get("peers","待補"),
            "護城河":d.get("moat","待補"),
            "主要風險":d.get("risk","待補"),
        }]), use_container_width=True, hide_index=True)

def home():
    try: v108_css()
    except Exception:
        try: v107_css()
        except Exception: pass
    if "v224_active_symbol" not in st.session_state:
        st.session_state["v224_active_symbol"] = "2330.TW"
    now_show = datetime.now().strftime("%Y/%m/%d %H:%M")
    st.markdown(f"""
    <div class="v108-hero">
      <div class="v108-title">智策股市 AI 決策平台</div>
      <div class="v108-sub">首頁先看價格與區間；深度資料收合在研究資料中。</div>
      <span class="v108-badge">最後更新：{now_show}</span>
      <span class="v108-badge">V224 Research Pages</span>
      <span class="v108-badge">一般投資人版</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="v108-note">一般投資人先看現價、保守價、合理價、樂觀價、預期報酬與投資建議；想深入再看產業分析與全球競爭力。</div>', unsafe_allow_html=True)
    q = st.text_input("搜尋股票代碼或公司名稱", placeholder="例如：2330、台積電、2308、台達電、5274、信驊", key="v224_search")
    if str(q or "").strip():
        st.session_state["v224_active_symbol"] = v224_symbol(q)
    quick = [("台積電","2330"),("台達電","2308"),("信驊","5274"),("聯發科","2454"),("廣達","2382"),("大立光","3008")]
    st.markdown("#### 核心快速查詢")
    cols = st.columns(len(quick))
    for col, (name, code_) in zip(cols, quick):
        with col:
            if st.button(name, key=f"v224_quick_{code_}", use_container_width=True):
                st.session_state["v224_active_symbol"] = v224_symbol(code_)
                st.rerun()
    with st.expander("產業 → 子產業 → 個股", expanded=False):
        df = v224_rows_df()
        c1,c2,c3 = st.columns(3)
        with c1:
            ind = st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v224_home_ind")
        sub_df = df[df["產業"] == ind]
        with c2:
            sub = st.selectbox("子產業", sorted(sub_df["子產業"].dropna().unique()), key="v224_home_sub")
        stock_df = sub_df[sub_df["子產業"] == sub]
        labels = {f"{r['公司']} / {r['代碼']}": r["代碼"] for _, r in stock_df.iterrows()}
        with c3:
            picked = st.selectbox("個股（選到後直接切換）", list(labels.keys()), key="v224_home_stock")
        code_ = labels.get(picked)
        if code_ and st.session_state.get("v224_last_pick") != picked:
            st.session_state["v224_last_pick"] = picked
            st.session_state["v224_active_symbol"] = code_
            st.rerun()
    v224_price_block(st.session_state.get("v224_active_symbol","2330.TW"))

def industry_page():
    st.header("🏭 產業分析")
    df = v224_rows_df()
    c1,c2 = st.columns(2)
    with c1:
        ind = st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v224_industry_ind")
    dff = df[df["產業"] == ind]
    with c2:
        sub = st.selectbox("子產業", ["全部"] + sorted(dff["子產業"].dropna().unique()), key="v224_industry_sub")
    if sub != "全部":
        dff = dff[dff["子產業"] == sub]
    meta = V224_INDUSTRY_META.get(ind, {"規模":"待補","成長率":"待補","AI關聯度":"待補","說明":"待補"})
    m1,m2,m3 = st.columns(3)
    m1.metric("產業規模", meta["規模"])
    m2.metric("成長率", meta["成長率"])
    m3.metric("AI關聯度", meta["AI關聯度"])
    st.info(meta["說明"])
    st.markdown("### 主要公司")
    st.dataframe(dff[["公司","代碼","子產業","AI主題","AI受惠度","全球競爭力","產業地位"]].sort_values(["子產業","代碼"]), use_container_width=True, hide_index=True)

def competition_page():
    st.header("🌏 全球競爭力")
    df = v224_rows_df()
    c1,c2,c3 = st.columns(3)
    with c1:
        ind = st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v224_global_ind")
    dff = df[df["產業"] == ind]
    with c2:
        sub = st.selectbox("子產業", sorted(dff["子產業"].dropna().unique()), key="v224_global_sub")
    dff = dff[dff["子產業"] == sub]
    labels = {f"{r['公司']} / {r['代碼']}": r["代碼"] for _, r in dff.iterrows()}
    with c3:
        picked = st.selectbox("個股", list(labels.keys()), key="v224_global_stock")
    row = dff[dff["代碼"] == labels[picked]].iloc[0].to_dict()
    st.markdown(f"## {row['公司']}（{row['代碼']}）")
    g1,g2,g3,g4 = st.columns(4)
    ai_txt = f"{row['AI受惠度']}/10" if int(row["AI受惠度"]) > 0 else "非AI主題"
    g1.metric("全球排名", row["全球排名"])
    g2.metric("AI受惠度", ai_txt)
    g3.metric("全球競爭力", row["全球競爭力"])
    g4.metric("產業地位", row["產業地位"])
    st.dataframe(pd.DataFrame([{
        "主產業":row["產業"],"子產業":row["子產業"],"個股":row["公司"],"代碼":row["代碼"],
        "競爭者":row["主要競爭者"],"護城河":row["護城河"],"主要風險":row["主要風險"],"AI主題":row["AI主題"]
    }]), use_container_width=True, hide_index=True)
    st.markdown("---")
    v224_ai_score_explanation()

def global_competition():
    competition_page()
def industry_analysis():
    industry_page()
def v108_enterprise_home():
    home()
def v107_premium_home():
    home()
# ===== V224.0 RESEARCH PAGES + STOCK EXPANSION END =====





# ===== V225.0 STOCK DATABASE EXPANSION START =====
V225_EXTRA_STOCKS = {'2356.TW': {'name': '英業達', 'industry': 'AI伺服器/ODM', 'sub': '伺服器ODM', 'rank': '伺服器與筆電ODM供應商', 'power': '★★★★☆', 'position': '伺服器與筆電ODM供應商', 'peers': '廣達、緯創、仁寶、和碩', 'moat': '中：ODM規模、客戶基礎', 'risk': '毛利率、客戶集中、PC循環', 'fair_mult': 1.04}, '2324.TW': {'name': '仁寶', 'industry': 'AI伺服器/ODM', 'sub': 'NB ODM/伺服器', 'rank': '筆電ODM主要廠', 'power': '★★★☆☆', 'position': '筆電ODM與伺服器代工供應商', 'peers': '廣達、緯創、英業達', 'moat': '中：ODM規模與客戶基礎', 'risk': '毛利率、PC需求循環', 'fair_mult': 1.02}, '4938.TW': {'name': '和碩', 'industry': 'AI伺服器/ODM', 'sub': 'EMS/ODM', 'rank': 'EMS/ODM主要廠', 'power': '★★★☆☆', 'position': '電子製造與ODM供應商', 'peers': '鴻海、廣達、緯創', 'moat': '中：製造規模與客戶基礎', 'risk': '毛利率、客戶集中', 'fair_mult': 1.02}, '8210.TW': {'name': '勤誠', 'industry': 'AI伺服器/機殼', 'sub': '伺服器機殼', 'rank': '伺服器機殼主要廠', 'power': '★★★★☆', 'position': 'AI伺服器機殼與機構件供應商', 'peers': '晟銘電、迎廣、Chenbro同業', 'moat': '中高：伺服器機殼設計與客戶導入', 'risk': 'AI伺服器出貨節奏、原料成本', 'fair_mult': 1.08}, '3013.TW': {'name': '晟銘電', 'industry': 'AI伺服器/機殼', 'sub': '伺服器機殼', 'rank': '伺服器機殼供應商', 'power': '★★★☆☆', 'position': '伺服器機殼與金屬機構件供應商', 'peers': '勤誠、迎廣、營邦', 'moat': '中：機構件設計與量產', 'risk': '題材波動、毛利率', 'fair_mult': 1.06}, '6117.TWO': {'name': '迎廣', 'industry': 'AI伺服器/機殼', 'sub': '機殼/伺服器機構', 'rank': '機殼供應商', 'power': '★★★☆☆', 'position': 'PC與伺服器機殼供應商', 'peers': '勤誠、晟銘電、營邦', 'moat': '中：機殼設計與客戶基礎', 'risk': '需求波動、競爭', 'fair_mult': 1.04}, '6412.TW': {'name': '群電', 'industry': '電源/能源管理', 'sub': '電源供應器', 'rank': '電源供應器主要廠', 'power': '★★★★☆', 'position': '電源供應器與伺服器電源供應商', 'peers': '台達電、光寶科、康舒', 'moat': '中高：電源設計與客戶導入', 'risk': '毛利率、原料、終端需求', 'fair_mult': 1.05}, '2301.TW': {'name': '光寶科', 'industry': '電源/能源管理', 'sub': '電源/光電/車用', 'rank': '電子零組件大廠', 'power': '★★★★☆', 'position': '電源、光電與車用電子供應商', 'peers': '台達電、群電、康舒', 'moat': '中高：產品線與客戶基礎', 'risk': '景氣循環、毛利率', 'fair_mult': 1.04}, '3711.TW': {'name': '日月光投控', 'industry': '半導體', 'sub': '封測/SiP', 'rank': '#1', 'power': '★★★★★', 'position': '全球封測與SiP龍頭', 'peers': 'Amkor、JCET、力成、京元電', 'moat': '高：封測規模、SiP能力、客戶基礎', 'risk': '終端需求循環、匯率', 'fair_mult': 1.06}, '6239.TW': {'name': '力成', 'industry': '半導體', 'sub': '記憶體封測', 'rank': '記憶體封測主要廠', 'power': '★★★★☆', 'position': '記憶體封測與儲存封裝供應商', 'peers': '日月光、Amkor、南茂', 'moat': '中高：記憶體封測技術與客戶', 'risk': '記憶體循環、稼動率', 'fair_mult': 1.04}, '6147.TWO': {'name': '頎邦', 'industry': '半導體', 'sub': 'DDI封測', 'rank': 'DDI封測主要廠', 'power': '★★★☆☆', 'position': '顯示驅動IC封測供應商', 'peers': '南茂、日月光、ChipMOS同業', 'moat': '中：DDI封測客戶基礎', 'risk': '面板循環、價格壓力', 'fair_mult': 1.02}, '2449.TW': {'name': '京元電子', 'industry': '半導體', 'sub': '測試/HPC', 'rank': '測試主要廠', 'power': '★★★★☆', 'position': 'AI/HPC與晶圓測試供應商', 'peers': '欣銓、矽格、日月光', 'moat': '中高：測試產能與客戶黏著', 'risk': '客戶集中、資本支出', 'fair_mult': 1.06}, '6510.TWO': {'name': '精測', 'industry': '半導體', 'sub': '測試介面', 'rank': '測試介面主要廠', 'power': '★★★★☆', 'position': '高階測試介面與探針卡供應商', 'peers': '旺矽、穎崴、FormFactor', 'moat': '中高：測試介面技術與客戶認證', 'risk': '先進製程需求波動、客戶集中', 'fair_mult': 1.08}, '6223.TWO': {'name': '旺矽', 'industry': '半導體', 'sub': '探針卡/測試介面', 'rank': '探針卡主要廠', 'power': '★★★★☆', 'position': '半導體探針卡與測試介面供應商', 'peers': '精測、穎崴、FormFactor', 'moat': '中高：探針卡技術與客戶導入', 'risk': '半導體測試需求循環', 'fair_mult': 1.08}, '3583.TW': {'name': '辛耘', 'industry': '半導體設備', 'sub': '設備/再生晶圓', 'rank': '半導體設備供應商', 'power': '★★★☆☆', 'position': '半導體設備、濕製程與再生晶圓供應商', 'peers': '弘塑、家登、帆宣', 'moat': '中：設備代理與製程服務', 'risk': '資本支出循環、客戶集中', 'fair_mult': 1.06}, '3131.TWO': {'name': '弘塑', 'industry': '半導體設備', 'sub': '濕製程設備', 'rank': '濕製程設備主要廠', 'power': '★★★★☆', 'position': '高階濕製程設備供應商', 'peers': 'SCREEN、TEL、辛耘', 'moat': '中高：濕製程設備技術與客戶認證', 'risk': '設備出貨時程、客戶集中', 'fair_mult': 1.1}, '3680.TWO': {'name': '家登', 'industry': '半導體設備', 'sub': 'EUV/晶圓載具', 'rank': 'EUV載具供應商', 'power': '★★★★☆', 'position': 'EUV與晶圓載具供應商', 'peers': 'Entegris、Gudeng同業', 'moat': '中高：EUV載具與客戶認證', 'risk': '先進製程資本支出、良率', 'fair_mult': 1.08}, '2345.TW': {'name': '智邦', 'industry': '網通', 'sub': '交換器/資料中心網通', 'rank': '白牌交換器主要廠', 'power': '★★★★★', 'position': '資料中心交換器與白牌網通龍頭之一', 'peers': 'Arista、Cisco、Celestica', 'moat': '高：資料中心客戶、網通設計能力', 'risk': '客戶集中、AI網通出貨節奏', 'fair_mult': 1.12}, '3596.TW': {'name': '智易', 'industry': '網通', 'sub': '寬頻/CPE', 'rank': '寬頻設備供應商', 'power': '★★★☆☆', 'position': '寬頻與網通CPE供應商', 'peers': '中磊、啟碁、Sercomm', 'moat': '中：CPE產品與電信客戶', 'risk': '電信資本支出、價格競爭', 'fair_mult': 1.03}, '5388.TWO': {'name': '中磊', 'industry': '網通', 'sub': '寬頻/CPE', 'rank': '網通CPE主要廠', 'power': '★★★☆☆', 'position': '寬頻網通與CPE供應商', 'peers': '智易、啟碁、Sercomm', 'moat': '中：電信客戶與產品線', 'risk': '電信需求循環、毛利率', 'fair_mult': 1.03}, '6285.TW': {'name': '啟碁', 'industry': '網通', 'sub': '車用/網通模組', 'rank': '網通模組供應商', 'power': '★★★☆☆', 'position': '網通、車用與衛星通訊模組供應商', 'peers': '中磊、智易、環旭電子', 'moat': '中：模組設計與客戶導入', 'risk': '需求循環、客戶集中', 'fair_mult': 1.04}, '2464.TW': {'name': '盟立', 'industry': '自動化/機器人', 'sub': '自動化系統整合', 'rank': '自動化系統整合商', 'power': '★★★☆☆', 'position': '工業自動化與系統整合供應商', 'peers': '和椿、羅昇、FANUC、Yaskawa', 'moat': '中：自動化整合經驗與客戶基礎', 'risk': '設備景氣循環、接單波動', 'fair_mult': 1.04}, '4540.TWO': {'name': '全球傳動', 'industry': '自動化/機器人', 'sub': '線性傳動', 'rank': '傳動元件供應商', 'power': '★★★☆☆', 'position': '線性傳動與自動化元件供應商', 'peers': '上銀、直得、THK', 'moat': '中：傳動元件製造能力', 'risk': '工具機循環、中國競爭', 'fair_mult': 1.04}, '1597.TWO': {'name': '直得', 'industry': '自動化/機器人', 'sub': '微型線性滑軌', 'rank': '精密傳動供應商', 'power': '★★★☆☆', 'position': '微型線性滑軌與精密傳動供應商', 'peers': '上銀、全球傳動、THK', 'moat': '中：微型傳動與精密加工', 'risk': '需求循環、競爭', 'fair_mult': 1.04}, '1536.TW': {'name': '和大', 'industry': '車用/機器人', 'sub': '齒輪/減速機', 'rank': '精密齒輪供應商', 'power': '★★★☆☆', 'position': '車用齒輪與精密傳動零件供應商', 'peers': '宇隆、日系齒輪廠、台灣精銳', 'moat': '中：精密加工與車用客戶', 'risk': '車市循環、匯率', 'fair_mult': 1.03}, '2002.TW': {'name': '中鋼', 'industry': '鋼鐵', 'sub': '一貫鋼廠', 'rank': '台灣鋼鐵龍頭', 'power': '★★★★☆', 'position': '台灣一貫鋼廠龍頭', 'peers': '寶鋼、浦項、新日鐵', 'moat': '中高：規模、通路、產品線', 'risk': '鋼價循環、原料成本、景氣', 'fair_mult': 0.98}, '1101.TW': {'name': '台泥', 'industry': '水泥', 'sub': '水泥/能源轉型', 'rank': '台灣水泥龍頭', 'power': '★★★★☆', 'position': '水泥與能源轉型公司', 'peers': '亞泥、海螺水泥、國際水泥廠', 'moat': '中高：水泥通路、資產、能源布局', 'risk': '中國需求、碳成本、能源轉型', 'fair_mult': 1.0}, '1102.TW': {'name': '亞泥', 'industry': '水泥', 'sub': '水泥', 'rank': '台灣水泥主要廠', 'power': '★★★☆☆', 'position': '台灣水泥主要供應商', 'peers': '台泥、海螺水泥、國際水泥廠', 'moat': '中：水泥通路與資產', 'risk': '中國需求、成本、景氣', 'fair_mult': 0.98}, '1216.TW': {'name': '統一', 'industry': '食品', 'sub': '食品/通路', 'rank': '台灣食品通路龍頭', 'power': '★★★★★', 'position': '食品、飲料、超商與通路集團', 'peers': '全家、味全、康師傅、食品同業', 'moat': '高：品牌、通路、規模', 'risk': '原物料、消費景氣、匯率', 'fair_mult': 1.04}, '1210.TW': {'name': '大成', 'industry': '食品', 'sub': '飼料/肉品/食品', 'rank': '食品飼料主要廠', 'power': '★★★☆☆', 'position': '飼料、肉品與食品供應商', 'peers': '卜蜂、統一、泰國CP', 'moat': '中：飼料與食品通路', 'risk': '原料價格、消費景氣', 'fair_mult': 1.02}, '2912.TW': {'name': '統一超', 'industry': '零售通路', 'sub': '便利商店', 'rank': '台灣超商龍頭', 'power': '★★★★★', 'position': '台灣便利商店與零售通路龍頭', 'peers': '全家、萊爾富、OK Mart', 'moat': '高：門市密度、品牌、物流', 'risk': '人力成本、消費景氣', 'fair_mult': 1.04}, '2881.TW': {'name': '富邦金', 'industry': '金融', 'sub': '金控/壽險/銀行', 'rank': '台灣大型金控', 'power': '★★★★☆', 'position': '壽險、銀行、證券綜合金控', 'peers': '國泰金、中信金、兆豐金', 'moat': '中高：金融通路與資本規模', 'risk': '利率、股債市、信用風險', 'fair_mult': 1.02}, '2882.TW': {'name': '國泰金', 'industry': '金融', 'sub': '金控/壽險/銀行', 'rank': '台灣大型金控', 'power': '★★★★☆', 'position': '壽險與銀行大型金控', 'peers': '富邦金、中信金、兆豐金', 'moat': '中高：壽險規模、金融通路', 'risk': '利率、匯率、股債市', 'fair_mult': 1.02}, '2891.TW': {'name': '中信金', 'industry': '金融', 'sub': '金控/銀行', 'rank': '銀行型金控', 'power': '★★★★☆', 'position': '銀行與金融服務金控', 'peers': '富邦金、國泰金、玉山金', 'moat': '中高：銀行通路、財管能力', 'risk': '利差、信用風險、景氣', 'fair_mult': 1.02}, '2603.TW': {'name': '長榮', 'industry': '航運', 'sub': '貨櫃航運', 'rank': '全球貨櫃航運主要業者', 'power': '★★★★☆', 'position': '全球貨櫃航運公司', 'peers': 'Maersk、MSC、CMA CGM、陽明', 'moat': '中：船隊規模與航線布局', 'risk': '運價循環、油價、地緣政治', 'fair_mult': 1.0}, '2609.TW': {'name': '陽明', 'industry': '航運', 'sub': '貨櫃航運', 'rank': '全球貨櫃航運業者', 'power': '★★★☆☆', 'position': '貨櫃航運公司', 'peers': '長榮、萬海、Maersk、MSC', 'moat': '中：航線與船隊', 'risk': '運價循環、油價', 'fair_mult': 0.98}, '2615.TW': {'name': '萬海', 'industry': '航運', 'sub': '貨櫃航運', 'rank': '亞洲航線主要業者', 'power': '★★★☆☆', 'position': '區域貨櫃航運公司', 'peers': '長榮、陽明、區域航商', 'moat': '中：區域航線布局', 'risk': '運價循環、油價', 'fair_mult': 0.98}}
V225_FALLBACK_PRICE = {'2356.TW': 58, '2324.TW': 42, '4938.TW': 95, '8210.TW': 420, '3013.TW': 160, '6117.TWO': 110, '6412.TW': 160, '2301.TW': 120, '3711.TW': 170, '6239.TW': 155, '6147.TWO': 70, '2449.TW': 180, '6510.TWO': 650, '6223.TWO': 850, '3583.TW': 420, '3131.TWO': 1300, '3680.TWO': 420, '2345.TW': 850, '3596.TW': 180, '5388.TWO': 120, '6285.TW': 150, '2464.TW': 95, '4540.TWO': 75, '1597.TWO': 90, '1536.TW': 110, '2002.TW': 24, '1101.TW': 34, '1102.TW': 40, '1216.TW': 86, '1210.TW': 55, '2912.TW': 285, '2881.TW': 90, '2882.TW': 75, '2891.TW': 45, '2603.TW': 220, '2609.TW': 80, '2615.TW': 90}
V225_INDUSTRY_META = {'AI伺服器/機殼': {'規模': '中', '成長率': '高', 'AI關聯度': '高', '說明': 'AI伺服器機殼、機構件、機櫃與資料中心硬體供應鏈'}, '半導體設備': {'規模': '中大', '成長率': '高循環', 'AI關聯度': '高', '說明': '半導體設備、廠務工程、先進製程與資本支出供應鏈'}, '網通': {'規模': '中大', '成長率': '中高', 'AI關聯度': '高', '說明': 'AI資料中心交換器、寬頻網通、CPE與高速網路設備'}, '鋼鐵': {'規模': '大', '成長率': '循環', 'AI關聯度': '非AI主題', '說明': '鋼價、基建、製造業景氣與原料成本主導'}, '水泥': {'規模': '中大', '成長率': '低中', 'AI關聯度': '非AI主題', '說明': '水泥、建設、碳成本與能源轉型'}, '食品': {'規模': '中大', '成長率': '穩定', 'AI關聯度': '非AI主題', '說明': '品牌、通路、食品安全與原物料成本'}, '零售通路': {'規模': '大', '成長率': '穩定', 'AI關聯度': '非AI主題', '說明': '門市密度、物流、消費景氣與品牌力'}, '車用/機器人': {'規模': '中', '成長率': '中高', 'AI關聯度': '中', '說明': '車用精密零件、減速機、機器人傳動與精密加工'}}

try:
    STOCK_DB.update(V225_EXTRA_STOCKS)
    ALIASES.clear()
    for sym, v in STOCK_DB.items():
        ALIASES[sym.upper()] = sym
        ALIASES[sym.split(".")[0]] = sym
        ALIASES[v["name"]] = sym
        ALIASES[v["name"].upper()] = sym
except Exception:
    pass

try:
    V224_FALLBACK_PRICE.update(V225_FALLBACK_PRICE)
except Exception:
    V224_FALLBACK_PRICE = V225_FALLBACK_PRICE

try:
    V224_INDUSTRY_META.update(V225_INDUSTRY_META)
except Exception:
    V224_INDUSTRY_META = V225_INDUSTRY_META

def v225_rows_df():
    rows = []
    for sym, v in STOCK_DB.items():
        d = {**v, "symbol": sym}
        try:
            ai = v224_ai_score(d)
        except Exception:
            ai = 0
        rows.append({
            "產業": v.get("industry","待補"),
            "子產業": v.get("sub","待補"),
            "公司": v.get("name",sym),
            "代碼": sym,
            "AI主題": v.get("theme_text", "一般產業" if ai > 0 else "非AI主題"),
            "AI受惠度": ai,
            "全球競爭力": v.get("power","★★★☆☆"),
            "全球排名": v.get("rank","待補"),
            "產業地位": v.get("position","待補"),
            "主要競爭者": v.get("peers","待補"),
            "護城河": v.get("moat","待補"),
            "主要風險": v.get("risk","待補"),
        })
    return pd.DataFrame(rows)

def v224_rows_df():
    return v225_rows_df()

def industry_page():
    st.header("🏭 產業分析")
    df = v225_rows_df()
    c1,c2 = st.columns(2)
    with c1:
        ind = st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v225_industry_ind")
    dff = df[df["產業"] == ind]
    with c2:
        sub = st.selectbox("子產業", ["全部"] + sorted(dff["子產業"].dropna().unique()), key="v225_industry_sub")
    if sub != "全部":
        dff = dff[dff["子產業"] == sub]
    meta = V224_INDUSTRY_META.get(ind, {"規模":"待補","成長率":"待補","AI關聯度":"待補","說明":"待補"})
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("產業規模", meta["規模"])
    m2.metric("成長率", meta["成長率"])
    m3.metric("AI關聯度", meta["AI關聯度"])
    m4.metric("主要公司數", len(dff))
    st.info(meta["說明"])
    st.markdown("### 主要公司")
    st.dataframe(dff[["公司","代碼","子產業","AI主題","AI受惠度","全球競爭力","產業地位"]].sort_values(["子產業","代碼"]), use_container_width=True, hide_index=True)

def competition_page():
    st.header("🌏 全球競爭力")
    df = v225_rows_df()
    c1,c2,c3 = st.columns(3)
    with c1:
        ind = st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v225_global_ind")
    dff = df[df["產業"] == ind]
    with c2:
        sub = st.selectbox("子產業", sorted(dff["子產業"].dropna().unique()), key="v225_global_sub")
    dff = dff[dff["子產業"] == sub]
    labels = {f"{r['公司']} / {r['代碼']}": r["代碼"] for _, r in dff.iterrows()}
    with c3:
        picked = st.selectbox("個股", list(labels.keys()), key="v225_global_stock")
    row = dff[dff["代碼"] == labels[picked]].iloc[0].to_dict()
    st.markdown(f"## {row['公司']}（{row['代碼']}）")
    g1,g2,g3,g4 = st.columns(4)
    ai_txt = f"{row['AI受惠度']}/10" if int(row["AI受惠度"]) > 0 else "非AI主題"
    g1.metric("全球排名", row["全球排名"])
    g2.metric("AI受惠度", ai_txt)
    g3.metric("全球競爭力", row["全球競爭力"])
    g4.metric("產業地位", row["產業地位"])
    st.dataframe(pd.DataFrame([{
        "主產業":row["產業"],"子產業":row["子產業"],"個股":row["公司"],"代碼":row["代碼"],
        "競爭者":row["主要競爭者"],"護城河":row["護城河"],"主要風險":row["主要風險"],"AI主題":row["AI主題"]
    }]), use_container_width=True, hide_index=True)
    st.markdown("---")
    v224_ai_score_explanation()

def global_competition():
    competition_page()
def industry_analysis():
    industry_page()
# ===== V225.0 STOCK DATABASE EXPANSION END =====





# ===== V226.0 STOCK DATABASE EXPANSION II START =====
V226_EXTRA_STOCKS = {'3591.TW': {'name': '艾笛森', 'industry': 'LED/光電', 'sub': 'LED照明/車用光源', 'rank': 'LED光源供應商', 'power': '★★★☆☆', 'position': 'LED照明與車用光源供應商', 'peers': '億光、光磊、隆達、Nichia', 'moat': '中：LED封裝、照明模組與車用應用', 'risk': 'LED價格競爭、需求循環', 'fair_mult': 1.02}, '2393.TW': {'name': '億光', 'industry': 'LED/光電', 'sub': 'LED封裝', 'rank': '台灣LED封裝主要廠', 'power': '★★★☆☆', 'position': 'LED封裝與光電元件供應商', 'peers': 'Nichia、Osram、Lumileds、艾笛森', 'moat': '中：LED封裝技術與客戶基礎', 'risk': '價格競爭、終端需求', 'fair_mult': 1.02}, '2340.TW': {'name': '台亞', 'industry': 'LED/光電', 'sub': 'LED/化合物半導體', 'rank': '光電與化合物半導體供應商', 'power': '★★★☆☆', 'position': 'LED晶粒與化合物半導體供應商', 'peers': '晶電、光磊、三安光電', 'moat': '中：磊晶與化合物半導體經驗', 'risk': 'LED循環、資本支出', 'fair_mult': 1.03}, '2455.TW': {'name': '全新', 'industry': '化合物半導體', 'sub': '砷化鎵磊晶', 'rank': '砷化鎵磊晶供應商', 'power': '★★★★☆', 'position': 'RF與光通訊砷化鎵磊晶供應商', 'peers': 'IQE、VPEC同業、宏捷科', 'moat': '中高：磊晶技術與客戶認證', 'risk': '手機/RF需求循環、客戶集中', 'fair_mult': 1.06}, '8086.TWO': {'name': '宏捷科', 'industry': '化合物半導體', 'sub': '砷化鎵/PA', 'rank': '砷化鎵代工供應商', 'power': '★★★☆☆', 'position': '砷化鎵與射頻元件供應商', 'peers': '穩懋、全新、Skyworks、Qorvo', 'moat': '中：砷化鎵製程與RF客戶', 'risk': '手機需求、價格競爭', 'fair_mult': 1.04}, '3105.TWO': {'name': '穩懋', 'industry': '化合物半導體', 'sub': '砷化鎵晶圓代工', 'rank': '全球砷化鎵代工龍頭之一', 'power': '★★★★☆', 'position': '砷化鎵RF晶圓代工龍頭之一', 'peers': '宏捷科、GlobalFoundries RF、WIN同業', 'moat': '中高：GaAs製程、客戶認證、產能規模', 'risk': '手機/RF循環、產能利用率', 'fair_mult': 1.05}, '2409.TW': {'name': '友達', 'industry': '面板/顯示器', 'sub': '面板/顯示器', 'rank': '面板主要廠', 'power': '★★★☆☆', 'position': '顯示面板與智慧顯示解決方案供應商', 'peers': '群創、BOE、LG Display、Samsung Display', 'moat': '中：面板製程與客戶基礎', 'risk': '面板價格循環、產能競爭', 'fair_mult': 0.98}, '3481.TW': {'name': '群創', 'industry': '面板/顯示器', 'sub': '面板/顯示器', 'rank': '面板主要廠', 'power': '★★★☆☆', 'position': '顯示面板與車用/工控顯示供應商', 'peers': '友達、BOE、LG Display', 'moat': '中：面板產能與應用布局', 'risk': '面板價格循環、稼動率', 'fair_mult': 0.98}, '6116.TW': {'name': '彩晶', 'industry': '面板/顯示器', 'sub': '中小尺寸面板', 'rank': '中小尺寸面板供應商', 'power': '★★☆☆☆', 'position': '中小尺寸面板供應商', 'peers': '友達、群創、中國面板廠', 'moat': '低中：既有產能與客戶', 'risk': '價格競爭、產能利用率', 'fair_mult': 0.96}, '5371.TWO': {'name': '中光電', 'industry': '面板/顯示器', 'sub': '背光模組/投影', 'rank': '背光與投影供應商', 'power': '★★★☆☆', 'position': '背光模組、投影與節能顯示供應商', 'peers': '瑞儀、光寶、日系光學廠', 'moat': '中：光學模組與客戶基礎', 'risk': '顯示需求循環、毛利率', 'fair_mult': 1.02}, '6176.TW': {'name': '瑞儀', 'industry': '面板/顯示器', 'sub': '背光模組', 'rank': '背光模組主要廠', 'power': '★★★☆☆', 'position': '背光模組與顯示應用供應商', 'peers': '中光電、日系背光模組廠', 'moat': '中：背光模組與客戶導入', 'risk': '終端需求循環、客戶集中', 'fair_mult': 1.02}, '2392.TW': {'name': '正崴', 'industry': '連接器/零組件', 'sub': '連接器/線材', 'rank': '連接器與線材供應商', 'power': '★★★☆☆', 'position': '連接器、線材與消費電子零組件供應商', 'peers': '信邦、貿聯-KY、鴻海集團零組件', 'moat': '中：連接器與客戶基礎', 'risk': '消費電子循環、毛利率', 'fair_mult': 1.02}, '3605.TW': {'name': '宏致', 'industry': '連接器/零組件', 'sub': '連接器', 'rank': '連接器供應商', 'power': '★★★☆☆', 'position': '連接器與電子零組件供應商', 'peers': '信邦、正崴、嘉澤、貿聯-KY', 'moat': '中：連接器設計與製造', 'risk': '需求循環、價格競爭', 'fair_mult': 1.03}, '3533.TW': {'name': '嘉澤', 'industry': '連接器/零組件', 'sub': 'CPU Socket/連接器', 'rank': 'CPU Socket主要供應商', 'power': '★★★★☆', 'position': '高階連接器與CPU Socket供應商', 'peers': 'Lotes、Foxconn Interconnect、TE Connectivity', 'moat': '中高：高階連接器認證與製程', 'risk': 'PC/伺服器平台週期、客戶集中', 'fair_mult': 1.06}, '6213.TW': {'name': '聯茂', 'industry': '電子材料', 'sub': 'CCL/銅箔基板', 'rank': 'CCL主要供應商', 'power': '★★★☆☆', 'position': '銅箔基板與電子材料供應商', 'peers': '台光電、台燿、Panasonic、Isola', 'moat': '中：CCL材料與客戶基礎', 'risk': '材料價格、AI需求波動', 'fair_mult': 1.04}, '2457.TW': {'name': '飛宏', 'industry': '電源/能源管理', 'sub': '電源供應器/充電', 'rank': '電源供應器供應商', 'power': '★★★☆☆', 'position': '電源供應器、充電與能源產品供應商', 'peers': '台達電、群電、康舒', 'moat': '中：電源設計與客戶基礎', 'risk': '毛利率、終端需求', 'fair_mult': 1.03}, '6282.TW': {'name': '康舒', 'industry': '電源/能源管理', 'sub': '電源/能源', 'rank': '電源供應器主要廠', 'power': '★★★☆☆', 'position': '電源供應器與能源應用供應商', 'peers': '台達電、群電、光寶科', 'moat': '中：電源產品線與客戶基礎', 'risk': '毛利率、原料、景氣循環', 'fair_mult': 1.03}, '4147.TWO': {'name': '中裕', 'industry': '生技醫療', 'sub': '新藥/抗體', 'rank': '新藥開發公司', 'power': '★★☆☆☆', 'position': '抗體與新藥開發公司', 'peers': '國際新藥公司、台灣生技同業', 'moat': '低中：研發管線與專利', 'risk': '臨床進度、資金需求、法規', 'fair_mult': 1.0}, '4162.TWO': {'name': '智擎', 'industry': '生技醫療', 'sub': '新藥授權', 'rank': '新藥開發與授權公司', 'power': '★★☆☆☆', 'position': '新藥開發與授權公司', 'peers': '中裕、台灣浩鼎、國際新藥公司', 'moat': '低中：授權管線與研發成果', 'risk': '臨床進度、授權收入波動', 'fair_mult': 1.0}, '4105.TWO': {'name': '東洋', 'industry': '生技醫療', 'sub': '學名藥/癌症用藥', 'rank': '台灣藥品主要廠', 'power': '★★★☆☆', 'position': '癌症用藥與特殊學名藥供應商', 'peers': '美時、杏輝、國際學名藥廠', 'moat': '中：產品組合、通路、藥證', 'risk': '藥價、競爭、法規', 'fair_mult': 1.03}, '1795.TWO': {'name': '美時', 'industry': '生技醫療', 'sub': '學名藥/特殊藥', 'rank': '特殊學名藥主要廠', 'power': '★★★☆☆', 'position': '特殊學名藥與國際通路供應商', 'peers': '東洋、國際學名藥廠', 'moat': '中：藥證、通路、產品線', 'risk': '藥價、法規、競爭', 'fair_mult': 1.04}, '4743.TWO': {'name': '合一', 'industry': '生技醫療', 'sub': '新藥/傷口照護', 'rank': '新藥與傷口照護公司', 'power': '★★☆☆☆', 'position': '新藥與傷口照護應用公司', 'peers': '中裕、智擎、國際生技公司', 'moat': '低中：專利與產品管線', 'risk': '臨床、銷售放量、法規', 'fair_mult': 1.0}, '2618.TW': {'name': '長榮航', 'industry': '航空/觀光', 'sub': '航空運輸', 'rank': '台灣航空主要業者', 'power': '★★★☆☆', 'position': '國際航空與客運貨運公司', 'peers': '華航、星宇、ANA、Cathay Pacific', 'moat': '中：航線、品牌、機隊', 'risk': '油價、匯率、旅運需求', 'fair_mult': 1.02}, '2610.TW': {'name': '華航', 'industry': '航空/觀光', 'sub': '航空運輸', 'rank': '台灣航空主要業者', 'power': '★★★☆☆', 'position': '航空客運與貨運公司', 'peers': '長榮航、星宇、Cathay Pacific', 'moat': '中：航線、貨運與品牌', 'risk': '油價、匯率、旅運需求', 'fair_mult': 1.02}, '2727.TW': {'name': '王品', 'industry': '觀光餐飲', 'sub': '連鎖餐飲', 'rank': '台灣連鎖餐飲主要品牌', 'power': '★★★☆☆', 'position': '連鎖餐飲品牌集團', 'peers': '瓦城、漢來美食、國際餐飲品牌', 'moat': '中：品牌、展店能力、營運管理', 'risk': '人力成本、消費景氣、食材成本', 'fair_mult': 1.03}, '2731.TWO': {'name': '雄獅', 'industry': '觀光餐飲', 'sub': '旅行社', 'rank': '台灣旅行社龍頭之一', 'power': '★★★☆☆', 'position': '旅遊服務與旅行社供應商', 'peers': '鳳凰、五福、易飛網', 'moat': '中：品牌、通路、產品組合', 'risk': '景氣、匯率、旅遊政策', 'fair_mult': 1.03}, '2542.TW': {'name': '興富發', 'industry': '營建', 'sub': '住宅建商', 'rank': '台灣大型建商', 'power': '★★★☆☆', 'position': '住宅開發與建設公司', 'peers': '遠雄、華固、國建、長虹', 'moat': '中：土地庫存、銷售能力', 'risk': '利率、房市政策、去化速度', 'fair_mult': 1.0}, '5522.TW': {'name': '遠雄', 'industry': '營建', 'sub': '住宅/商辦建設', 'rank': '大型建設公司', 'power': '★★★☆☆', 'position': '住宅、商辦與開發建設公司', 'peers': '興富發、華固、長虹、國建', 'moat': '中：土地資源與品牌', 'risk': '房市政策、利率、工程成本', 'fair_mult': 1.0}, '2548.TW': {'name': '華固', 'industry': '營建', 'sub': '高端住宅/商辦', 'rank': '高端建商', 'power': '★★★☆☆', 'position': '高端住宅與商辦開發公司', 'peers': '長虹、遠雄、興富發', 'moat': '中：地段選擇、品牌、財務體質', 'risk': '房市政策、利率、推案進度', 'fair_mult': 1.02}, '5534.TW': {'name': '長虹', 'industry': '營建', 'sub': '住宅/商辦', 'rank': '大型建商', 'power': '★★★☆☆', 'position': '住宅與商辦建設公司', 'peers': '華固、遠雄、興富發', 'moat': '中：土地庫存與推案能力', 'risk': '房市政策、利率、銷售速度', 'fair_mult': 1.01}}
V226_FALLBACK_PRICE = {'3591.TW': 26.45, '2393.TW': 80, '2340.TW': 40, '2455.TW': 180, '8086.TWO': 120, '3105.TWO': 150, '2409.TW': 17, '3481.TW': 15, '6116.TW': 9, '5371.TWO': 90, '6176.TW': 130, '2392.TW': 80, '3605.TW': 55, '3533.TW': 1500, '6213.TW': 110, '2457.TW': 60, '6282.TW': 42, '4147.TWO': 85, '4162.TWO': 100, '4105.TWO': 75, '1795.TWO': 280, '4743.TWO': 140, '2618.TW': 40, '2610.TW': 25, '2727.TW': 220, '2731.TWO': 160, '2542.TW': 45, '5522.TW': 75, '2548.TW': 130, '5534.TW': 90}
V226_INDUSTRY_META = {'LED/光電': {'規模': '中', '成長率': '低中', 'AI關聯度': '低', '說明': 'LED照明、車用光源、光電元件，受價格競爭與應用需求影響'}, '化合物半導體': {'規模': '中', '成長率': '中高', 'AI關聯度': '中', '說明': '砷化鎵、RF、磊晶與化合物半導體供應鏈'}, '面板/顯示器': {'規模': '大', '成長率': '循環', 'AI關聯度': '低中', '說明': '面板、背光、車用與工控顯示，主要看價格循環與應用轉型'}, '連接器/零組件': {'規模': '中大', '成長率': '中', 'AI關聯度': '中', '說明': '連接器、線材、高速傳輸與電子零組件'}, '生技醫療': {'規模': '中', '成長率': '高不確定', 'AI關聯度': '非AI主題', '說明': '藥證、臨床、授權、醫療通路與法規是核心'}, '航空/觀光': {'規模': '大', '成長率': '循環', 'AI關聯度': '非AI主題', '說明': '旅運需求、油價、匯率與景氣循環主導'}, '觀光餐飲': {'規模': '中', '成長率': '中', 'AI關聯度': '非AI主題', '說明': '消費景氣、展店、品牌與人力成本主導'}, '營建': {'規模': '大', '成長率': '循環', 'AI關聯度': '非AI主題', '說明': '利率、房市政策、土地庫存與推案進度主導'}}

try:
    STOCK_DB.update(V226_EXTRA_STOCKS)
    ALIASES.clear()
    for sym, v in STOCK_DB.items():
        ALIASES[sym.upper()] = sym
        ALIASES[sym.split(".")[0]] = sym
        ALIASES[v["name"]] = sym
        ALIASES[v["name"].upper()] = sym
except Exception:
    pass

try:
    V224_FALLBACK_PRICE.update(V226_FALLBACK_PRICE)
except Exception:
    V224_FALLBACK_PRICE = V226_FALLBACK_PRICE

try:
    V224_INDUSTRY_META.update(V226_INDUSTRY_META)
except Exception:
    V224_INDUSTRY_META = V226_INDUSTRY_META

def v226_rows_df():
    rows = []
    for sym, v in STOCK_DB.items():
        d = {**v, "symbol": sym}
        try:
            ai = v224_ai_score(d)
        except Exception:
            ai = 0
        rows.append({
            "產業": v.get("industry","待補"),
            "子產業": v.get("sub","待補"),
            "公司": v.get("name",sym),
            "代碼": sym,
            "AI主題": v.get("theme_text", "一般產業" if ai > 0 else "非AI主題"),
            "AI受惠度": ai,
            "全球競爭力": v.get("power","★★★☆☆"),
            "全球排名": v.get("rank","待補"),
            "產業地位": v.get("position","待補"),
            "主要競爭者": v.get("peers","待補"),
            "護城河": v.get("moat","待補"),
            "主要風險": v.get("risk","待補"),
        })
    return pd.DataFrame(rows)

def v225_rows_df():
    return v226_rows_df()
def v224_rows_df():
    return v226_rows_df()

def industry_page():
    st.header("🏭 產業分析")
    df = v226_rows_df()
    c1,c2 = st.columns(2)
    with c1:
        ind = st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v226_industry_ind")
    dff = df[df["產業"] == ind]
    with c2:
        sub = st.selectbox("子產業", ["全部"] + sorted(dff["子產業"].dropna().unique()), key="v226_industry_sub")
    if sub != "全部":
        dff = dff[dff["子產業"] == sub]
    meta = V224_INDUSTRY_META.get(ind, {"規模":"待補","成長率":"待補","AI關聯度":"待補","說明":"待補"})
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("產業規模", meta["規模"])
    m2.metric("成長率", meta["成長率"])
    m3.metric("AI關聯度", meta["AI關聯度"])
    m4.metric("主要公司數", len(dff))
    st.info(meta["說明"])
    st.markdown("### 主要公司")
    st.dataframe(dff[["公司","代碼","子產業","AI主題","AI受惠度","全球競爭力","產業地位"]].sort_values(["子產業","代碼"]), use_container_width=True, hide_index=True)

def competition_page():
    st.header("🌏 全球競爭力")
    df = v226_rows_df()
    c1,c2,c3 = st.columns(3)
    with c1:
        ind = st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v226_global_ind")
    dff = df[df["產業"] == ind]
    with c2:
        sub = st.selectbox("子產業", sorted(dff["子產業"].dropna().unique()), key="v226_global_sub")
    dff = dff[dff["子產業"] == sub]
    labels = {f"{r['公司']} / {r['代碼']}": r["代碼"] for _, r in dff.iterrows()}
    with c3:
        picked = st.selectbox("個股", list(labels.keys()), key="v226_global_stock")
    row = dff[dff["代碼"] == labels[picked]].iloc[0].to_dict()
    st.markdown(f"## {row['公司']}（{row['代碼']}）")
    g1,g2,g3,g4 = st.columns(4)
    try:
        ai_txt = f"{int(row['AI受惠度'])}/10" if int(row["AI受惠度"]) > 0 else "非AI主題"
    except Exception:
        ai_txt = "非AI主題"
    g1.metric("全球排名", row["全球排名"])
    g2.metric("AI受惠度", ai_txt)
    g3.metric("全球競爭力", row["全球競爭力"])
    g4.metric("產業地位", row["產業地位"])
    st.dataframe(pd.DataFrame([{
        "主產業":row["產業"],"子產業":row["子產業"],"個股":row["公司"],"代碼":row["代碼"],
        "競爭者":row["主要競爭者"],"護城河":row["護城河"],"主要風險":row["主要風險"],"AI主題":row["AI主題"]
    }]), use_container_width=True, hide_index=True)
    st.markdown("---")
    v224_ai_score_explanation()

def global_competition():
    competition_page()
def industry_analysis():
    industry_page()
# ===== V226.0 STOCK DATABASE EXPANSION II END =====


if __name__ == '__main__':
    main()
