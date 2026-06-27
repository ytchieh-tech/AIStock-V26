import os, json
os.environ["STREAMLIT_RUNNER_MAGIC_ENABLED"] = "false"
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

APP_VERSION = "V210.0 Global Competition Database"
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
if __name__ == '__main__':
    main()
