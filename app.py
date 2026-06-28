import os, json
os.environ["STREAMLIT_RUNNER_MAGIC_ENABLED"] = "false"
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

APP_VERSION = "V240.0 Version Fix + Completion Dashboard"
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





# ===== V227.0 AUTO LOAD MULTI THEME START =====
V227_THEME_UPDATES = {'2330.TW': {'theme_text': 'AI伺服器、CoWoS、先進封裝、HPC、機器人、低軌衛星', 'chain_position': '中游核心', 'market_share': '全球晶圓代工龍頭'}, '2313.TW': {'name': '華通', 'industry': 'PCB', 'sub': '高階PCB/衛星PCB', 'rank': 'PCB主要廠', 'power': '★★★★☆', 'position': '高階PCB、網通與低軌衛星PCB供應商', 'peers': '欣興、健鼎、臻鼎、TTM', 'moat': '中高：高階PCB量產、客戶認證、衛星通訊應用', 'risk': '終端需求循環、PCB價格競爭', 'fair_mult': 1.05, 'theme_text': 'AI伺服器、低軌衛星、網通、高速傳輸、軍工通訊', 'chain_position': '上游材料/PCB', 'market_share': '台灣高階PCB主要廠'}, '2383.TW': {'theme_text': 'AI伺服器、高速CCL、800G交換器、資料中心', 'chain_position': '上游材料', 'market_share': 'AI高速材料主要供應商'}, '3017.TW': {'theme_text': 'AI伺服器、液冷散熱、資料中心、機器人', 'chain_position': '中游關鍵零組件', 'market_share': '散熱模組主要廠'}, '3324.TWO': {'theme_text': 'AI伺服器、液冷散熱、資料中心', 'chain_position': '中游關鍵零組件', 'market_share': '液冷散熱主要廠'}, '3491.TWO': {'name': '昇達科', 'industry': '低軌衛星', 'sub': '衛星通訊/射頻元件', 'rank': '台灣LEO供應鏈龍頭之一', 'power': '★★★★☆', 'position': '低軌衛星與微波通訊元件供應商', 'peers': 'Comtech、Viasat、Gilat、啟碁', 'moat': '中高：微波通訊、衛星射頻模組、客戶認證', 'risk': '衛星訂單時程、客戶集中、題材波動', 'fair_mult': 1.08, 'theme_text': '低軌衛星、軍工、射頻、衛星通訊', 'chain_position': '中游射頻元件', 'market_share': '台灣LEO衛星射頻受惠股'}, '6285.TW': {'theme_text': '低軌衛星、網通、車用通訊、衛星終端', 'chain_position': '下游終端設備', 'market_share': '網通與衛星終端設備供應商'}, '5388.TWO': {'theme_text': '低軌衛星、寬頻網通、衛星終端', 'chain_position': '下游終端設備', 'market_share': '網通CPE主要廠'}, '2345.TW': {'theme_text': 'AI資料中心、交換器、網通、低軌衛星', 'chain_position': '中游網通設備', 'market_share': '資料中心交換器主要廠'}, '3596.TW': {'theme_text': '寬頻網通、低軌衛星、家庭網路', 'chain_position': '下游網通設備', 'market_share': '寬頻設備供應商'}, '4908.TWO': {'name': '前鼎', 'industry': '光通訊/CPO', 'sub': '光收發模組', 'rank': '光通訊供應商', 'power': '★★★☆☆', 'position': '光通訊與網通光收發模組供應商', 'peers': '華星光、波若威、上詮、眾達', 'moat': '中：光收發模組與網通客戶', 'risk': '需求波動、價格競爭', 'fair_mult': 1.05, 'theme_text': '光通訊、CPO、低軌衛星、資料中心', 'chain_position': '中游光通訊模組', 'market_share': '台灣光通訊供應商'}, '3163.TWO': {'name': '波若威', 'industry': '光通訊/CPO', 'sub': '光通訊模組/元件', 'rank': '光通訊元件供應商', 'power': '★★★☆☆', 'position': '光通訊元件與資料中心供應商', 'peers': '華星光、上詮、聯亞、眾達', 'moat': '中：光通訊產品與客戶導入', 'risk': '需求波動、競爭', 'fair_mult': 1.06, 'theme_text': '光通訊、CPO、低軌衛星、資料中心', 'chain_position': '中游光通訊元件', 'market_share': '台灣光通訊供應商'}, '3450.TW': {'name': '聯鈞', 'industry': '光通訊/CPO', 'sub': '光通訊元件', 'rank': '光通訊供應商', 'power': '★★★☆☆', 'position': '光通訊與雷射元件供應商', 'peers': '聯亞、華星光、上詮', 'moat': '中：光元件與客戶基礎', 'risk': '光通訊需求循環、毛利率', 'fair_mult': 1.05, 'theme_text': '光通訊、CPO、低軌衛星', 'chain_position': '中游光元件', 'market_share': '台灣光通訊元件供應商'}, '2634.TW': {'name': '漢翔', 'industry': '國防軍工', 'sub': '軍機/航太', 'rank': '台灣航太軍工龍頭', 'power': '★★★★☆', 'position': '軍機、航太結構與國防供應鏈核心公司', 'peers': 'Boeing、Lockheed Martin供應鏈、長榮航太', 'moat': '中高：航太認證、軍方訂單、製造能力', 'risk': '政策預算、交期、成本', 'fair_mult': 1.06, 'theme_text': '國防軍工、無人機、航太、軍機', 'chain_position': '下游系統/整機', 'market_share': '台灣航太軍工龍頭'}, '8033.TWO': {'name': '雷虎', 'industry': '無人機', 'sub': '無人機/軍工', 'rank': '無人機題材股', 'power': '★★★☆☆', 'position': '無人機、模型與軍工題材供應商', 'peers': '經緯航太、漢翔、國際無人機廠', 'moat': '中：無人機研發與題材認知', 'risk': '訂單實現、題材波動、規模', 'fair_mult': 1.06, 'theme_text': '無人機、國防軍工、軍用無人機', 'chain_position': '下游無人機系統', 'market_share': '台灣無人機題材股'}, '2645.TW': {'name': '長榮航太', 'industry': '國防軍工', 'sub': '航太維修/製造', 'rank': '航太維修主要廠', 'power': '★★★☆☆', 'position': '航太維修與航太零組件供應商', 'peers': '漢翔、亞航、國際MRO廠', 'moat': '中：維修認證、航太客戶', 'risk': '航空景氣、政策訂單', 'fair_mult': 1.04, 'theme_text': '國防軍工、航太、無人機', 'chain_position': '中下游航太維修/零組件', 'market_share': '台灣航太維修主要廠'}, '2630.TW': {'name': '亞航', 'industry': '國防軍工', 'sub': '航空維修/軍工', 'rank': '航太維修供應商', 'power': '★★★☆☆', 'position': '航空維修與軍工維修供應商', 'peers': '長榮航太、漢翔、國際MRO廠', 'moat': '中：航空維修認證與軍方業務', 'risk': '航空景氣、政策預算', 'fair_mult': 1.03, 'theme_text': '國防軍工、航太、無人機', 'chain_position': '中下游維修服務', 'market_share': '台灣航太維修供應商'}, '4572.TW': {'name': '駐龍', 'industry': '國防軍工', 'sub': '航太零組件', 'rank': '航太零組件供應商', 'power': '★★★☆☆', 'position': '航太精密零組件供應商', 'peers': '漢翔、千附精密、達航科技', 'moat': '中：航太加工認證與精密製造', 'risk': '訂單波動、匯率', 'fair_mult': 1.03, 'theme_text': '國防軍工、航太', 'chain_position': '中游航太零組件', 'market_share': '台灣航太零組件供應商'}, '6829.TW': {'name': '千附精密', 'industry': '國防軍工', 'sub': '航太/半導體零組件', 'rank': '精密零組件供應商', 'power': '★★★☆☆', 'position': '航太與半導體精密零組件供應商', 'peers': '駐龍、漢翔、達航科技', 'moat': '中：精密加工與航太/半導體客戶', 'risk': '訂單波動、毛利率', 'fair_mult': 1.04, 'theme_text': '國防軍工、航太、半導體設備', 'chain_position': '中游精密零組件', 'market_share': '台灣精密零組件供應商'}, '4576.TW': {'theme_text': '機器人、人形機器人、精密傳動、自動化', 'chain_position': '中游精密傳動', 'market_share': '精密傳動供應商'}, '2049.TW': {'theme_text': '機器人、人形機器人、線性滑軌、自動化', 'chain_position': '中游傳動元件', 'market_share': '全球傳動元件主要廠'}}
V227_FALLBACK_PRICE = {'2313.TW': 75, '3491.TWO': 430, '4908.TWO': 120, '3163.TWO': 180, '3450.TW': 95, '2634.TW': 65, '8033.TWO': 90, '2645.TW': 120, '2630.TW': 45, '4572.TW': 180, '6829.TW': 110}
V227_INDUSTRY_META = {'晶圓代工': {'規模': '極大', '成長率': '高', 'AI關聯度': '極高', '說明': '先進製程、成熟製程、AI/HPC晶片製造與全球半導體核心供應鏈'}, '封裝測試': {'規模': '大', '成長率': '中高', 'AI關聯度': '高', '說明': '封測、IC測試、先進封裝與AI/HPC晶片後段製程'}, '低軌衛星': {'規模': '中高', '成長率': '高', 'AI關聯度': '中高', '說明': '衛星終端、衛星通訊、射頻、天線、地面設備與太空網路供應鏈'}, '無人機': {'規模': '中', '成長率': '高', 'AI關聯度': '中高', '說明': '軍用與商用無人機、飛控、影像、通訊、導航與國防應用'}, '國防軍工': {'規模': '中高', '成長率': '中高', 'AI關聯度': '中', '說明': '軍機、飛彈、雷達、軍規電子、航太與國防自主供應鏈'}, 'PCB': {'規模': '大', '成長率': '中高', 'AI關聯度': '高', '說明': '高階PCB、AI伺服器PCB、低軌衛星、網通與軍工通訊基板'}}
try:
    for sym, upd in V227_THEME_UPDATES.items():
        if sym in STOCK_DB:
            STOCK_DB[sym].update(upd)
        else:
            STOCK_DB[sym] = upd
    ALIASES.clear()
    for sym, v in STOCK_DB.items():
        ALIASES[sym.upper()] = sym
        ALIASES[sym.split('.')[0]] = sym
        ALIASES[v['name']] = sym
        ALIASES[v['name'].upper()] = sym
except Exception:
    pass
try:
    V224_FALLBACK_PRICE.update(V227_FALLBACK_PRICE)
except Exception:
    V224_FALLBACK_PRICE = V227_FALLBACK_PRICE
try:
    V224_INDUSTRY_META.update(V227_INDUSTRY_META)
except Exception:
    V224_INDUSTRY_META = V227_INDUSTRY_META

def v227_theme_list():
    themes=set()
    for v in STOCK_DB.values():
        for t in str(v.get('theme_text','')).replace('，','、').split('、'):
            t=t.strip()
            if t: themes.add(t)
    return sorted(themes)

def v227_ai_score(v):
    t=str(v.get('theme_text',''))
    sym=v.get('symbol','')
    industry=v.get('industry','')
    if sym in ['2330.TW','5274.TWO','6669.TW'] or any(x in t for x in ['CoWoS','HPC','先進封裝']): return 10
    if any(x in t for x in ['AI伺服器','CPO','光通訊','液冷散熱','低軌衛星']): return 9
    if any(x in t for x in ['HBM','資料中心','軍工','無人機','機器人']): return 8
    if industry in ['金融','航運','食品','營建','水泥','鋼鐵']: return 0
    return 3

def v227_rows_df():
    rows=[]
    for sym,v in STOCK_DB.items():
        vv={**v,'symbol':sym}
        ai=v227_ai_score(vv)
        rows.append({'產業':v.get('industry','待補'),'子產業':v.get('sub','待補'),'公司':v.get('name',sym),'代碼':sym,'產業鏈位置':v.get('chain_position','待補'),'主題標籤':v.get('theme_text','一般產業' if ai>0 else '非AI主題'),'AI受惠度':ai,'全球競爭力':v.get('power','★★★☆☆'),'全球排名':v.get('rank','待補'),'全球市占率':v.get('market_share','待補'),'產業地位':v.get('position','待補'),'主要競爭者':v.get('peers','待補'),'護城河':v.get('moat','待補'),'主要風險':v.get('risk','待補')})
    return pd.DataFrame(rows)

def v226_rows_df(): return v227_rows_df()
def v225_rows_df(): return v227_rows_df()
def v224_rows_df(): return v227_rows_df()

def v227_set_symbol(code):
    st.session_state['v227_active_symbol']=code
    st.session_state['v224_active_symbol']=code
    st.session_state['v223_active_symbol']=code

def v224_price_block(symbol):
    d = v224_decision(symbol) if 'v224_decision' in globals() else decision(symbol)
    fmtf = v224_fmt if 'v224_fmt' in globals() else fmt_price
    st.caption(f"資料更新時間：{d.get('updated','N/A')}｜現價來源：{d.get('source','Yahoo Finance')}｜預期報酬率＝(綜合合理價－現價)÷現價。")
    st.markdown(f"## {d.get('name', symbol)}（{d.get('symbol', symbol)}）")
    c1,c2,c3,c4=st.columns(4)
    c1.metric('投資建議', d.get('action','觀察'))
    c2.metric('現價', fmtf(d.get('price', float('nan'))))
    c3.metric('綜合合理價', fmtf(d.get('fair', float('nan'))))
    try: ret_txt=f"{float(d.get('ret',0)):.1f}%"
    except Exception: ret_txt='N/A'
    c4.metric('預期報酬', ret_txt)
    p1,p2,p3=st.columns(3)
    p1.metric('安全邊際價', fmtf(d.get('cons', float('nan'))))
    p2.metric('合理價值', fmtf(d.get('fair', float('nan'))))
    p3.metric('潛在價值', fmtf(d.get('opt', float('nan'))))
    with st.expander('展開更多研究資料', expanded=False):
        df=v227_rows_df(); row=df[df['代碼']==d.get('symbol',symbol)]
        if not row.empty:
            st.dataframe(row[['產業','子產業','產業鏈位置','主題標籤','AI受惠度','全球競爭力','全球排名','全球市占率','產業地位','主要競爭者','護城河','主要風險']], use_container_width=True, hide_index=True)

def industry_page():
    st.header('🏭 產業分析')
    df=v227_rows_df()
    c1,c2,c3=st.columns(3)
    with c1: ind=st.selectbox('主產業', sorted(df['產業'].dropna().unique()), key='v227_industry_ind')
    dff=df[df['產業']==ind]
    with c2: sub=st.selectbox('子產業', sorted(dff['子產業'].dropna().unique()), key='v227_industry_sub')
    dff=dff[dff['子產業']==sub]
    labels={f"{r['公司']} / {r['代碼']}":r['代碼'] for _,r in dff.iterrows()}
    with c3: picked=st.selectbox('個股（選到即查詢）', list(labels.keys()), key='v227_industry_stock')
    code=labels[picked]; v227_set_symbol(code)
    row=dff[dff['代碼']==code].iloc[0].to_dict()
    meta=V224_INDUSTRY_META.get(ind, V227_INDUSTRY_META.get(ind, {'規模':'待補','成長率':'待補','AI關聯度':'待補','說明':'待補'}))
    m1,m2,m3,m4=st.columns(4)
    m1.metric('產業規模', meta.get('規模','待補')); m2.metric('成長率', meta.get('成長率','待補')); m3.metric('AI關聯度', meta.get('AI關聯度','待補')); m4.metric('主要公司數', len(dff))
    st.info(meta.get('說明',''))
    st.markdown('### 公司基本資料')
    st.dataframe(pd.DataFrame([{'公司名稱':row['公司'],'股票代號':row['代碼'],'主產業':row['產業'],'子產業':row['子產業'],'產業鏈位置':row['產業鏈位置'],'主題標籤':row['主題標籤'],'全球排名':row['全球排名'],'全球市占率':row['全球市占率'],'產業地位':row['產業地位']}]), use_container_width=True, hide_index=True)
    st.markdown('### 同產業主要公司')
    st.dataframe(dff[['公司','代碼','子產業','產業鏈位置','主題標籤','AI受惠度','全球競爭力','產業地位']].sort_values(['子產業','代碼']), use_container_width=True, hide_index=True)

def competition_page():
    st.header('🌏 全球競爭力')
    df=v227_rows_df(); themes=['全部']+v227_theme_list()
    c0,c1,c2,c3=st.columns(4)
    with c0: theme=st.selectbox('主題標籤', themes, key='v227_global_theme')
    if theme!='全部': df=df[df['主題標籤'].astype(str).str.contains(theme, na=False)]
    with c1: ind=st.selectbox('主產業', sorted(df['產業'].dropna().unique()), key='v227_global_ind')
    dff=df[df['產業']==ind]
    with c2: sub=st.selectbox('子產業', sorted(dff['子產業'].dropna().unique()), key='v227_global_sub')
    dff=dff[dff['子產業']==sub]
    labels={f"{r['公司']} / {r['代碼']}":r['代碼'] for _,r in dff.iterrows()}
    with c3: picked=st.selectbox('個股（選到即查詢）', list(labels.keys()), key='v227_global_stock')
    code=labels[picked]; v227_set_symbol(code)
    row=dff[dff['代碼']==code].iloc[0].to_dict()
    st.markdown(f"## {row['公司']}（{row['代碼']}）")
    g1,g2,g3,g4=st.columns(4); ai_txt=f"{int(row['AI受惠度'])}/10" if int(row['AI受惠度'])>0 else '非AI主題'
    g1.metric('全球排名',row['全球排名']); g2.metric('AI受惠度',ai_txt); g3.metric('全球競爭力',row['全球競爭力']); g4.metric('全球市占率',row['全球市占率'])
    st.dataframe(pd.DataFrame([{'產業地位':row['產業地位'],'競爭者':row['主要競爭者'],'護城河':row['護城河'],'主要風險':row['主要風險'],'主題標籤':row['主題標籤'],'產業鏈位置':row['產業鏈位置']}]), use_container_width=True, hide_index=True)
    st.markdown('---'); v224_ai_score_explanation()

def global_competition(): competition_page()
def industry_analysis(): industry_page()

def home():
    try: v108_css()
    except Exception:
        try: v107_css()
        except Exception: pass
    if 'v227_active_symbol' not in st.session_state: st.session_state['v227_active_symbol']='2330.TW'
    now_show=datetime.now().strftime('%Y/%m/%d %H:%M')
    st.markdown(f"""<div class="v108-hero"><div class="v108-title">智策股市 AI 決策平台</div><div class="v108-sub">產業鏈、全球競爭力與企業價值研究平台</div><span class="v108-badge">最後更新：{now_show}</span><span class="v108-badge">V227 Multi-Theme</span><span class="v108-badge">選股即查詢</span></div>""", unsafe_allow_html=True)
    q=st.text_input('搜尋股票代碼或公司名稱', placeholder='例如：2330、台積電、2313、華通、3491、昇達科', key='v227_search')
    if str(q or '').strip():
        try: v227_set_symbol(normalize_symbol(q))
        except Exception: pass
    df=v227_rows_df()
    with st.expander('產業 → 子產業 → 個股', expanded=False):
        c1,c2,c3=st.columns(3)
        with c1: ind=st.selectbox('主產業', sorted(df['產業'].dropna().unique()), key='v227_home_ind')
        dff=df[df['產業']==ind]
        with c2: sub=st.selectbox('子產業', sorted(dff['子產業'].dropna().unique()), key='v227_home_sub')
        dff=dff[dff['子產業']==sub]
        labels={f"{r['公司']} / {r['代碼']}":r['代碼'] for _,r in dff.iterrows()}
        with c3: picked=st.selectbox('個股（選到即查詢）', list(labels.keys()), key='v227_home_stock')
        if picked:
            code=labels[picked]
            if st.session_state.get('v227_last_pick')!=picked:
                st.session_state['v227_last_pick']=picked; v227_set_symbol(code); st.rerun()
    v224_price_block(st.session_state.get('v227_active_symbol','2330.TW'))

def v108_enterprise_home(): home()
def v107_premium_home(): home()
# ===== V227.0 AUTO LOAD MULTI THEME END =====





# ===== V228.0 SECTOR EXPANSION THEME II START =====
V228_UPDATES = {'3264.TWO': {'name': '欣銓', 'industry': '封裝測試', 'sub': 'IC測試/車用測試', 'rank': '晶圓測試主要廠', 'power': '★★★★☆', 'position': '車用、HPC與晶圓測試供應商', 'peers': '京元電、矽格、日月光、Teradyne供應鏈', 'moat': '中高：測試產能、車用客戶、認證門檻', 'risk': '客戶集中、測試需求循環', 'fair_mult': 1.06, 'theme_text': '封裝測試、車用電子、HPC、AI伺服器', 'chain_position': '中游測試服務', 'market_share': '台灣晶圓測試主要廠'}, '6257.TW': {'name': '矽格', 'industry': '封裝測試', 'sub': 'IC測試/封裝', 'rank': '封測主要廠', 'power': '★★★☆☆', 'position': 'IC測試與封裝服務供應商', 'peers': '京元電、欣銓、日月光、南茂', 'moat': '中：測試封裝產能與客戶基礎', 'risk': '稼動率、景氣循環', 'fair_mult': 1.04, 'theme_text': '封裝測試、車用電子、AI伺服器', 'chain_position': '中游封測服務', 'market_share': '台灣封測主要廠'}, '8150.TW': {'name': '南茂', 'industry': '封裝測試', 'sub': '記憶體/DDI封測', 'rank': '封測主要廠', 'power': '★★★☆☆', 'position': '記憶體與顯示驅動IC封測供應商', 'peers': '力成、頎邦、日月光', 'moat': '中：封測產能與客戶基礎', 'risk': '記憶體與面板循環', 'fair_mult': 1.02, 'theme_text': '封裝測試、記憶體、DDI', 'chain_position': '中游封測服務', 'market_share': '台灣封測主要廠'}, '3711.TW': {'industry': '封裝測試', 'sub': '封測/SiP/先進封裝', 'theme_text': '封裝測試、先進封裝、SiP、AI伺服器', 'chain_position': '中游封測龍頭', 'market_share': '全球封測龍頭'}, '6239.TW': {'industry': '封裝測試', 'sub': '記憶體封測', 'theme_text': '封裝測試、記憶體、AI伺服器', 'chain_position': '中游封測服務', 'market_share': '記憶體封測主要廠'}, '2449.TW': {'industry': '封裝測試', 'sub': 'IC測試/HPC測試', 'theme_text': '封裝測試、HPC、AI伺服器、晶圓測試', 'chain_position': '中游測試服務', 'market_share': 'AI/HPC測試主要廠'}, '6147.TWO': {'industry': '封裝測試', 'sub': 'DDI封測', 'theme_text': '封裝測試、DDI、面板/顯示器', 'chain_position': '中游封測服務', 'market_share': 'DDI封測主要廠'}, '6285.TW': {'industry': '低軌衛星', 'sub': '衛星終端/網通模組', 'theme_text': '低軌衛星、衛星終端、網通、車用通訊', 'chain_position': '下游終端設備', 'market_share': '衛星終端與網通模組供應商'}, '5388.TWO': {'industry': '低軌衛星', 'sub': '衛星終端/CPE', 'theme_text': '低軌衛星、衛星終端、寬頻網通', 'chain_position': '下游終端設備', 'market_share': '衛星終端與寬頻CPE供應商'}, '3596.TW': {'industry': '低軌衛星', 'sub': '寬頻設備/CPE', 'theme_text': '低軌衛星、寬頻網通、家庭網路', 'chain_position': '下游網通設備', 'market_share': '寬頻設備供應商'}, '2345.TW': {'theme_text': 'AI資料中心、交換器、網通、低軌衛星、高速傳輸', 'chain_position': '中游網通設備', 'market_share': '資料中心交換器主要廠'}, '8499.TWO': {'name': '鼎炫-KY', 'industry': '國防軍工', 'sub': '電磁防護/材料', 'rank': 'EMI材料供應商', 'power': '★★★☆☆', 'position': '電磁干擾防護與材料供應商', 'peers': 'Laird、3M、台灣材料同業', 'moat': '中：EMI材料與客戶導入', 'risk': '需求波動、客戶集中', 'fair_mult': 1.03, 'theme_text': '國防軍工、軍規電子、電磁防護、無人機', 'chain_position': '上游材料', 'market_share': '台灣EMI材料供應商'}, '8044.TWO': {'name': '網家', 'industry': '電商/數位服務', 'sub': '電商平台', 'rank': '台灣電商平台', 'power': '★★☆☆☆', 'position': '台灣電商與數位服務平台', 'peers': 'momo、蝦皮、Yahoo購物', 'moat': '低中：品牌與平台流量', 'risk': '競爭、毛利、營運轉型', 'fair_mult': 0.98, 'theme_text': '電商、數位服務', 'chain_position': '下游平台', 'market_share': '台灣電商平台'}, '2646.TW': {'name': '星宇航空', 'industry': '航空/觀光', 'sub': '航空運輸', 'rank': '台灣航空業者', 'power': '★★★☆☆', 'position': '台灣國際航空公司', 'peers': '長榮航、華航、國際航空業者', 'moat': '中：品牌、服務與航線布局', 'risk': '油價、匯率、機隊擴張', 'fair_mult': 1.03, 'theme_text': '航空、觀光、旅運復甦', 'chain_position': '下游航空服務', 'market_share': '台灣航空公司'}, '2368.TW': {'name': '金像電', 'industry': 'PCB', 'sub': 'AI伺服器PCB', 'rank': 'AI伺服器PCB主要廠', 'power': '★★★★☆', 'position': 'AI伺服器與高速PCB供應商', 'peers': '華通、健鼎、欣興、TTM', 'moat': '中高：AI伺服器PCB製程與客戶認證', 'risk': 'AI出貨節奏、價格競爭', 'fair_mult': 1.08, 'theme_text': 'AI伺服器、高速PCB、資料中心、網通', 'chain_position': '上游PCB', 'market_share': 'AI伺服器PCB主要廠'}, '6274.TWO': {'name': '台燿', 'industry': 'CCL/電子材料', 'sub': '高速CCL', 'rank': '高速材料供應商', 'power': '★★★★☆', 'position': '高速網通與AI伺服器CCL供應商', 'peers': '台光電、聯茂、Panasonic', 'moat': '中高：高速CCL材料與客戶導入', 'risk': '材料需求循環、原料成本', 'fair_mult': 1.08, 'theme_text': 'AI伺服器、高速CCL、800G交換器、資料中心', 'chain_position': '上游材料', 'market_share': '高速CCL主要廠'}, '6213.TW': {'industry': 'CCL/電子材料', 'sub': 'CCL/銅箔基板', 'theme_text': 'AI伺服器、高速CCL、資料中心、網通', 'chain_position': '上游材料', 'market_share': 'CCL主要供應商'}, '2383.TW': {'industry': 'CCL/電子材料', 'sub': 'AI高速材料/CCL', 'theme_text': 'AI伺服器、高速CCL、800G交換器、資料中心', 'chain_position': '上游材料', 'market_share': 'AI高速材料龍頭之一'}, '4979.TWO': {'theme_text': '光通訊、CPO、AI資料中心、800G、低軌衛星', 'chain_position': '中游光模組', 'market_share': 'AI資料中心光通訊供應商'}, '6442.TW': {'theme_text': '光通訊、CPO、AI資料中心、800G', 'chain_position': '中游光通訊元件', 'market_share': '資料中心光通訊零組件供應商'}, '3081.TWO': {'theme_text': '光通訊、CPO、雷射元件、AI資料中心', 'chain_position': '上游磊晶/雷射元件', 'market_share': '光通訊磊晶供應商'}, '3363.TWO': {'theme_text': '光通訊、CPO、低軌衛星、資料中心', 'chain_position': '中游光通訊元件', 'market_share': '光通訊元件供應商'}}
V228_FALLBACK_PRICE = {'3264.TWO': 95, '6257.TW': 70, '8150.TW': 45, '8499.TWO': 120, '8044.TWO': 38, '2646.TW': 28, '2368.TW': 280, '6274.TWO': 260}
V228_INDUSTRY_META = {'封裝測試': {'規模': '大', '成長率': '中高', 'AI關聯度': '高', '說明': 'IC封裝、晶圓測試、HPC測試、先進封裝與AI晶片後段製程'}, 'CCL/電子材料': {'規模': '中大', '成長率': '高', 'AI關聯度': '高', '說明': '高速CCL、AI伺服器材料、800G交換器與高頻高速板材'}, '電商/數位服務': {'規模': '中大', '成長率': '中', 'AI關聯度': '低', '說明': '電商平台、物流、數位服務與消費景氣'}}

try:
    for sym, upd in V228_UPDATES.items():
        if sym in STOCK_DB:
            STOCK_DB[sym].update(upd)
        else:
            STOCK_DB[sym] = upd
    ALIASES.clear()
    for sym, v in STOCK_DB.items():
        ALIASES[sym.upper()] = sym
        ALIASES[sym.split(".")[0]] = sym
        ALIASES[v["name"]] = sym
        ALIASES[v["name"].upper()] = sym
except Exception:
    pass

try:
    V224_FALLBACK_PRICE.update(V228_FALLBACK_PRICE)
except Exception:
    V224_FALLBACK_PRICE = V228_FALLBACK_PRICE

try:
    V224_INDUSTRY_META.update(V228_INDUSTRY_META)
except Exception:
    V224_INDUSTRY_META = V228_INDUSTRY_META

# 讓 V227 頁面吃到新增資料
try:
    def v228_rows_df():
        return v227_rows_df()
except Exception:
    pass
# ===== V228.0 SECTOR EXPANSION THEME II END =====





# ===== V230.0 WHITE DASHBOARD INVESTOR UI START =====
def v230_css():
    st.markdown("""
    <style>
    .main .block-container{padding-top:1.2rem;max-width:1320px;}
    section[data-testid="stSidebar"]{background:#f3f6fb;}
    .v230-topbar{display:flex;align-items:center;justify-content:space-between;background:#fff;border:1px solid #e6edf7;border-radius:18px;padding:18px 22px;margin:8px 0 18px 0;box-shadow:0 10px 30px rgba(15,23,42,.06);}
    .v230-brand{font-size:28px;font-weight:900;color:#102033;line-height:1.1;}
    .v230-sub{font-size:13px;color:#64748b;margin-top:5px;}
    .v230-version{font-size:13px;color:#2563eb;font-weight:700;}
    .v230-card{background:#fff;border:1px solid #e6edf7;border-radius:18px;padding:18px;margin:10px 0;box-shadow:0 10px 24px rgba(15,23,42,.05);}
    .v230-card-title{font-size:18px;font-weight:850;color:#102033;margin-bottom:10px;}
    .v230-kpi-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin:16px 0 18px 0;}
    .v230-kpi{background:#fff;border:1px solid #e6edf7;border-radius:18px;padding:16px;min-height:108px;box-shadow:0 8px 22px rgba(15,23,42,.05);}
    .v230-kpi-icon{font-size:24px;margin-bottom:8px;}
    .v230-kpi-label{color:#64748b;font-size:13px;font-weight:700;}
    .v230-kpi-value{font-size:28px;font-weight:900;color:#0f172a;margin-top:4px;}
    .v230-kpi-note{font-size:12px;color:#64748b;margin-top:4px;}
    .v230-tag-wrap{display:flex;flex-wrap:wrap;gap:7px;max-width:100%;white-space:normal;line-height:2.2;}
    .v230-tag{display:inline-flex;align-items:center;border:1px solid #bfdbfe;background:#eff6ff;color:#1d4ed8;border-radius:9px;padding:3px 8px;font-size:13px;font-weight:750;white-space:nowrap;}
    .v230-tag:nth-child(2n){background:#faf5ff;color:#7e22ce;border-color:#d8b4fe;}
    .v230-tag:nth-child(3n){background:#fff7ed;color:#c2410c;border-color:#fed7aa;}
    .v230-tag:nth-child(4n){background:#ecfdf5;color:#15803d;border-color:#bbf7d0;}
    .v230-tag:nth-child(5n){background:#fdf2f8;color:#be185d;border-color:#fbcfe8;}
    .v230-small-muted{color:#64748b;font-size:12px;}
    div[data-testid="stDataFrame"] div[role="gridcell"]{white-space:normal !important;}
    .stButton>button{border-radius:12px;border:1px solid #dbe7f5;background:#fff;min-height:42px;font-weight:700;color:#1e293b;}
    .stButton>button:hover{border-color:#60a5fa;color:#1d4ed8;background:#eff6ff;}
    @media(max-width:1000px){.v230-kpi-grid{grid-template-columns:repeat(2,1fr);} .v230-topbar{display:block;}}
    </style>
    """, unsafe_allow_html=True)

def v230_tag_html(text):
    parts=[p.strip() for p in str(text or "").replace("，","、").replace(",", "、").split("、") if p.strip()]
    if not parts: parts=["一般產業"]
    return '<div class="v230-tag-wrap">' + ''.join([f'<span class="v230-tag">{p}</span>' for p in parts]) + '</div>'

def v230_rows_df():
    for fn in ["v227_rows_df","v226_rows_df","v225_rows_df","v224_rows_df"]:
        try:
            return globals()[fn]()
        except Exception:
            pass
    return pd.DataFrame()

def v230_symbol(q):
    try:
        return normalize_symbol(q)
    except Exception:
        q=str(q or "").strip().upper()
        return q+".TW" if q.isdigit() else (q or "2330.TW")

def v230_decision(symbol):
    try:
        return v224_decision(symbol)
    except Exception:
        try:
            return decision(symbol)
        except Exception:
            return {"symbol":symbol,"name":symbol,"price":float("nan"),"fair":float("nan"),"cons":float("nan"),"opt":float("nan"),"ret":0,"action":"觀察","source":"N/A","updated":"N/A"}

def v230_fmt(x):
    try:
        if pd.isna(x): return "N/A"
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def v230_price_block(symbol):
    d=v230_decision(symbol); sym=d.get("symbol", symbol)
    st.caption(f"資料更新時間：{d.get('updated','N/A')}｜現價來源：{d.get('source','Yahoo Finance')}｜預期報酬率＝(綜合合理價－現價)÷現價。")
    st.markdown(f"## {d.get('name', sym)}（{sym}）")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("投資建議", d.get("action","觀察"))
    c2.metric("現價", v230_fmt(d.get("price", float("nan"))))
    c3.metric("綜合合理價", v230_fmt(d.get("fair", float("nan"))))
    try: ret_txt=f"{float(d.get('ret',0)):.1f}%"
    except Exception: ret_txt="N/A"
    c4.metric("預期報酬", ret_txt)
    p1,p2,p3=st.columns(3)
    p1.metric("安全邊際價", v230_fmt(d.get("cons", float("nan"))))
    p2.metric("合理價值", v230_fmt(d.get("fair", float("nan"))))
    p3.metric("潛在價值", v230_fmt(d.get("opt", float("nan"))))
    df=v230_rows_df(); row=df[df["代碼"]==sym] if not df.empty and "代碼" in df.columns else pd.DataFrame()
    with st.expander("展開更多研究資料", expanded=False):
        if not row.empty:
            r=row.iloc[0].to_dict()
            st.markdown("### 公司基本資料")
            st.markdown(f'<div class="v230-card"><div class="v230-card-title">{r.get("公司","")}｜{r.get("代碼","")}</div><div class="v230-small-muted">主產業：{r.get("產業","")}　｜　子產業：{r.get("子產業","")}　｜　產業鏈位置：{r.get("產業鏈位置","待補")}</div><div style="margin-top:10px;">{v230_tag_html(r.get("主題標籤",""))}</div></div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame([{"全球排名":r.get("全球排名","待補"),"全球市占率":r.get("全球市占率","待補"),"產業地位":r.get("產業地位","待補"),"主要競爭者":r.get("主要競爭者","待補"),"護城河":r.get("護城河","待補"),"主要風險":r.get("主要風險","待補")}]), use_container_width=True, hide_index=True)
        else:
            st.info("此個股仍在資料庫補齊中，後續會補上產業鏈位置、主題標籤、競爭者與護城河。")

def home():
    v230_css()
    if "v227_active_symbol" not in st.session_state: st.session_state["v227_active_symbol"]="2330.TW"
    now_show=datetime.now().strftime("%Y/%m/%d %H:%M")
    st.markdown(f'<div class="v230-topbar"><div><div class="v230-brand">📈 智策股市 AI 決策平台</div><div class="v230-sub">企業價值研究平台｜產業鏈 × 全球競爭力 × 財務預測 × 合理價推估</div></div><div class="v230-version">V230 White Dashboard<br>{now_show}</div></div>', unsafe_allow_html=True)
    q=st.text_input("搜尋公司名稱 / 代號 / 產業 / 主題標籤", placeholder="例如：2330、台積電、2313、華通、低軌衛星、CoWoS", key="v230_search")
    if str(q or "").strip(): st.session_state["v227_active_symbol"]=v230_symbol(q)
    df=v230_rows_df()
    if df.empty:
        st.warning("資料庫尚未載入。"); return
    total=len(df); hot_ind=df["產業"].nunique()
    hot_theme=len(set("、".join(df["主題標籤"].fillna("").astype(str)).split("、"))) if "主題標籤" in df.columns else 0
    ai9=int((pd.to_numeric(df["AI受惠度"], errors="coerce").fillna(0)>=9).sum()) if "AI受惠度" in df.columns else 0
    global5=int(df["全球競爭力"].astype(str).str.contains("★★★★★", regex=False).sum()) if "全球競爭力" in df.columns else 0
    st.markdown(f'<div class="v230-kpi-grid"><div class="v230-kpi"><div class="v230-kpi-icon">🔥</div><div class="v230-kpi-label">熱門產業</div><div class="v230-kpi-value">{hot_ind}</div><div class="v230-kpi-note">涵蓋主要主產業</div></div><div class="v230-kpi"><div class="v230-kpi-icon">🏆</div><div class="v230-kpi-label">個股資料庫</div><div class="v230-kpi-value">{total}</div><div class="v230-kpi-note">持續補齊中</div></div><div class="v230-kpi"><div class="v230-kpi-icon">🏷️</div><div class="v230-kpi-label">主題標籤</div><div class="v230-kpi-value">{hot_theme}</div><div class="v230-kpi-note">可多重歸屬</div></div><div class="v230-kpi"><div class="v230-kpi-icon">🤖</div><div class="v230-kpi-label">AI高受惠</div><div class="v230-kpi-value">{ai9}</div><div class="v230-kpi-note">AI受惠度 ≥ 9</div></div><div class="v230-kpi"><div class="v230-kpi-icon">🌏</div><div class="v230-kpi-label">全球強勢</div><div class="v230-kpi-value">{global5}</div><div class="v230-kpi-note">★★★★★</div></div><div class="v230-kpi"><div class="v230-kpi-icon">📊</div><div class="v230-kpi-label">後續模組</div><div class="v230-kpi-value">2026E</div><div class="v230-kpi-note">財務預測預留</div></div></div>', unsafe_allow_html=True)
    quick=[("台積電","2330"),("華通","2313"),("昇達科","3491"),("廣達","2382"),("奇鋐","3017"),("聯鈞","3450")]
    st.markdown("### 核心快速查詢")
    cols=st.columns(len(quick))
    for col,(name,code_) in zip(cols,quick):
        with col:
            if st.button(name, key=f"v230_quick_{code_}", use_container_width=True):
                st.session_state["v227_active_symbol"]=v230_symbol(code_); st.rerun()
    left,right=st.columns([1.2,1])
    with left:
        st.markdown('<div class="v230-card"><div class="v230-card-title">熱門個股 TOP 10</div>', unsafe_allow_html=True)
        show=df.sort_values(["AI受惠度","全球競爭力"], ascending=False).head(10)[["公司","代碼","產業","子產業","AI受惠度","全球競爭力"]]
        st.dataframe(show, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="v230-card"><div class="v230-card-title">熱門主題標籤</div>', unsafe_allow_html=True)
        st.markdown(v230_tag_html("AI伺服器、CoWoS、先進封裝、HBM、光通訊、CPO、低軌衛星、機器人、無人機、國防軍工、車用電子、資料中心"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with st.expander("產業 → 子產業 → 個股（選到即查詢）", expanded=False):
        c1,c2,c3=st.columns(3)
        with c1: ind=st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v230_home_ind")
        dff=df[df["產業"]==ind]
        with c2: sub=st.selectbox("子產業", sorted(dff["子產業"].dropna().unique()), key="v230_home_sub")
        dff=dff[dff["子產業"]==sub]
        labels={f"{r['公司']} / {r['代碼']}":r["代碼"] for _,r in dff.iterrows()}
        with c3: picked=st.selectbox("個股", list(labels.keys()), key="v230_home_stock")
        if picked:
            code=labels[picked]
            if st.session_state.get("v230_last_pick")!=picked:
                st.session_state["v230_last_pick"]=picked; st.session_state["v227_active_symbol"]=code; st.rerun()
    st.markdown("---")
    v230_price_block(st.session_state.get("v227_active_symbol","2330.TW"))

def industry_page():
    v230_css(); st.header("🏭 產業分析")
    df=v230_rows_df()
    c1,c2,c3=st.columns(3)
    with c1: ind=st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v230_industry_ind")
    dff=df[df["產業"]==ind]
    with c2: sub=st.selectbox("子產業", sorted(dff["子產業"].dropna().unique()), key="v230_industry_sub")
    dff=dff[dff["子產業"]==sub]
    labels={f"{r['公司']} / {r['代碼']}":r["代碼"] for _,r in dff.iterrows()}
    with c3: picked=st.selectbox("個股（選到即查詢）", list(labels.keys()), key="v230_industry_stock")
    code=labels[picked]; st.session_state["v227_active_symbol"]=code
    row=dff[dff["代碼"]==code].iloc[0].to_dict()
    meta=V224_INDUSTRY_META.get(ind, {"規模":"待補","成長率":"待補","AI關聯度":"待補","說明":"待補"})
    k1,k2,k3,k4=st.columns(4); k1.metric("產業規模", meta.get("規模","待補")); k2.metric("成長率", meta.get("成長率","待補")); k3.metric("AI關聯度", meta.get("AI關聯度","待補")); k4.metric("同產業公司", len(dff))
    st.info(meta.get("說明",""))
    st.markdown("### 公司基本資料")
    st.markdown(f'<div class="v230-card"><div class="v230-card-title">{row.get("公司","")}｜{row.get("代碼","")}</div><div class="v230-small-muted">主產業：{row.get("產業","")}　｜　子產業：{row.get("子產業","")}　｜　產業鏈位置：{row.get("產業鏈位置","待補")}</div><div style="margin-top:10px;">{v230_tag_html(row.get("主題標籤",""))}</div></div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([{"全球排名":row.get("全球排名","待補"),"全球市占率":row.get("全球市占率","待補"),"產業地位":row.get("產業地位","待補"),"主要競爭者":row.get("主要競爭者","待補"),"護城河":row.get("護城河","待補"),"主要風險":row.get("主要風險","待補")}]), use_container_width=True, hide_index=True)
    st.markdown("### 同產業主要公司")
    st.dataframe(dff[["公司","代碼","子產業","產業鏈位置","AI受惠度","全球競爭力","產業地位"]], use_container_width=True, hide_index=True)

def competition_page():
    v230_css(); st.header("🌏 全球競爭力")
    df=v230_rows_df()
    themes=["全部"]+sorted(set([p.strip() for s in df["主題標籤"].fillna("").astype(str) for p in s.replace("，","、").split("、") if p.strip()]))
    c0,c1,c2,c3=st.columns(4)
    with c0: theme=st.selectbox("主題標籤", themes, key="v230_global_theme")
    if theme!="全部": df=df[df["主題標籤"].astype(str).str.contains(theme, na=False)]
    with c1: ind=st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v230_global_ind")
    dff=df[df["產業"]==ind]
    with c2: sub=st.selectbox("子產業", sorted(dff["子產業"].dropna().unique()), key="v230_global_sub")
    dff=dff[dff["子產業"]==sub]
    labels={f"{r['公司']} / {r['代碼']}":r["代碼"] for _,r in dff.iterrows()}
    with c3: picked=st.selectbox("個股（選到即查詢）", list(labels.keys()), key="v230_global_stock")
    code=labels[picked]; st.session_state["v227_active_symbol"]=code
    row=dff[dff["代碼"]==code].iloc[0].to_dict()
    st.markdown(f"## {row['公司']}（{row['代碼']}）")
    g1,g2,g3,g4=st.columns(4)
    ai_txt=f"{int(row['AI受惠度'])}/10" if int(row["AI受惠度"])>0 else "非AI主題"
    g1.metric("全球排名", row["全球排名"]); g2.metric("AI受惠度", ai_txt); g3.metric("全球競爭力", row["全球競爭力"]); g4.metric("全球市占率", row["全球市占率"])
    st.markdown(v230_tag_html(row.get("主題標籤","")), unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([{"產業地位":row["產業地位"],"競爭者":row["主要競爭者"],"護城河":row["護城河"],"主要風險":row["主要風險"],"產業鏈位置":row["產業鏈位置"]}]), use_container_width=True, hide_index=True)
    st.markdown("---"); v224_ai_score_explanation()

def global_competition(): competition_page()
def industry_analysis(): industry_page()
def v108_enterprise_home(): home()
def v107_premium_home(): home()
# ===== V230.0 WHITE DASHBOARD INVESTOR UI END =====





# ===== V231.0 RANKING DASHBOARD START =====

def v231_rank_table(df):
    rows = []
    for _, r in df.iterrows():
        sym = r.get("代碼", "")
        try:
            info = STOCK_DB.get(sym, {})
        except Exception:
            info = {}
        try:
            px = V224_FALLBACK_PRICE.get(sym, float("nan"))
        except Exception:
            px = float("nan")
        try:
            fair_mult = float(info.get("fair_mult", 1.0))
        except Exception:
            fair_mult = 1.0
        try:
            fair = float(px) * fair_mult
            ret = (fair - float(px)) / float(px) * 100 if float(px) > 0 else float("nan")
        except Exception:
            fair, ret = float("nan"), float("nan")
        rows.append({
            "公司": r.get("公司",""),
            "代碼": sym,
            "產業": r.get("產業",""),
            "子產業": r.get("子產業",""),
            "現價": px,
            "綜合合理價": fair,
            "預期報酬%": ret,
            "AI受惠度": r.get("AI受惠度",0),
            "全球競爭力": r.get("全球競爭力",""),
            "主題標籤": r.get("主題標籤",""),
        })
    out = pd.DataFrame(rows)
    if not out.empty:
        out["現價"] = pd.to_numeric(out["現價"], errors="coerce")
        out["綜合合理價"] = pd.to_numeric(out["綜合合理價"], errors="coerce")
        out["預期報酬%"] = pd.to_numeric(out["預期報酬%"], errors="coerce")
        out["AI受惠度"] = pd.to_numeric(out["AI受惠度"], errors="coerce").fillna(0)
    return out

def v231_fmt_rank(df):
    d = df.copy()
    for c in ["現價","綜合合理價"]:
        if c in d.columns:
            d[c] = d[c].map(lambda x: "N/A" if pd.isna(x) else f"{x:,.2f}")
    if "預期報酬%" in d.columns:
        d["預期報酬%"] = d["預期報酬%"].map(lambda x: "N/A" if pd.isna(x) else f"{x:.1f}%")
    return d

def home():
    v230_css()
    if "v227_active_symbol" not in st.session_state:
        st.session_state["v227_active_symbol"] = "2330.TW"

    now_show = datetime.now().strftime("%Y/%m/%d %H:%M")
    st.markdown(f"""
    <div class="v230-topbar">
      <div>
        <div class="v230-brand">📈 智策股市 AI 決策平台</div>
        <div class="v230-sub">企業價值研究平台｜產業鏈 × 全球競爭力 × 財務預測 × 合理價推估</div>
      </div>
      <div class="v230-version">V231 Ranking Dashboard<br>{now_show}</div>
    </div>
    """, unsafe_allow_html=True)

    q = st.text_input("搜尋公司名稱 / 代號 / 產業 / 主題標籤", placeholder="例如：2330、台積電、2313、華通、低軌衛星、CoWoS", key="v231_search")
    if str(q or "").strip():
        st.session_state["v227_active_symbol"] = v230_symbol(q)

    df = v230_rows_df()
    if df.empty:
        st.warning("資料庫尚未載入。")
        return

    rank = v231_rank_table(df)

    total = len(df)
    hot_ind = df["產業"].nunique()
    hot_theme = len(set("、".join(df["主題標籤"].fillna("").astype(str)).split("、"))) if "主題標籤" in df.columns else 0
    ai9 = int((pd.to_numeric(df["AI受惠度"], errors="coerce").fillna(0) >= 9).sum()) if "AI受惠度" in df.columns else 0
    undervalued = int((rank["預期報酬%"].fillna(0) > 0).sum()) if not rank.empty else 0
    global5 = int(df["全球競爭力"].astype(str).str.contains("★★★★★", regex=False).sum()) if "全球競爭力" in df.columns else 0

    st.markdown(f"""
    <div class="v230-kpi-grid">
      <div class="v230-kpi"><div class="v230-kpi-icon">🔥</div><div class="v230-kpi-label">熱門產業</div><div class="v230-kpi-value">{hot_ind}</div><div class="v230-kpi-note">涵蓋主要主產業</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">🏆</div><div class="v230-kpi-label">個股資料庫</div><div class="v230-kpi-value">{total}</div><div class="v230-kpi-note">持續補齊中</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">🏷️</div><div class="v230-kpi-label">主題標籤</div><div class="v230-kpi-value">{hot_theme}</div><div class="v230-kpi-note">可多重歸屬</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">📉</div><div class="v230-kpi-label">低估個股</div><div class="v230-kpi-value">{undervalued}</div><div class="v230-kpi-note">預期報酬 > 0</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">🤖</div><div class="v230-kpi-label">AI高受惠</div><div class="v230-kpi-value">{ai9}</div><div class="v230-kpi-note">AI受惠度 ≥ 9</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">🌏</div><div class="v230-kpi-label">全球強勢</div><div class="v230-kpi-value">{global5}</div><div class="v230-kpi-note">★★★★★</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 核心快速查詢")
    quick = [("台積電","2330"),("華通","2313"),("昇達科","3491"),("廣達","2382"),("奇鋐","3017"),("聯鈞","3450")]
    cols = st.columns(len(quick))
    for col, (name, code_) in zip(cols, quick):
        with col:
            if st.button(name, key=f"v231_quick_{code_}", use_container_width=True):
                st.session_state["v227_active_symbol"] = v230_symbol(code_)
                st.rerun()

    with st.expander("排行計算標準", expanded=False):
        st.markdown("""
        **熱門個股 TOP 10**：以 AI受惠度、全球競爭力、產業鏈資料完整度作為排序基礎。  
        **低估排行 TOP 10**：以 `預期報酬 = (綜合合理價 - 現價) ÷ 現價` 排序。  
        **AI受惠排行 TOP 10**：以 AI受惠度 1–10 分排序。  
        **全球競爭力排行 TOP 10**：以全球競爭力星等與產業地位排序。  

        目前仍是研究資料庫版本；等企業評價模型與財務預測中心完成後，低估排行會改用 DCF / EVA / EBO / FCFF / 財測模型的綜合結果。
        """)

    tab1, tab2, tab3, tab4 = st.tabs(["熱門個股", "低估排行", "AI受惠排行", "全球競爭力排行"])

    with tab1:
        show = df.copy()
        show["_stars"] = show["全球競爭力"].astype(str).str.count("★")
        show = show.sort_values(["AI受惠度","_stars"], ascending=False).head(10)
        st.dataframe(show[["公司","代碼","產業","子產業","AI受惠度","全球競爭力","產業地位"]], use_container_width=True, hide_index=True)

    with tab2:
        low = rank.dropna(subset=["預期報酬%"]).sort_values("預期報酬%", ascending=False).head(10)
        st.dataframe(v231_fmt_rank(low[["公司","代碼","產業","子產業","現價","綜合合理價","預期報酬%","AI受惠度"]]), use_container_width=True, hide_index=True)

    with tab3:
        ai = df.copy()
        ai["_stars"] = ai["全球競爭力"].astype(str).str.count("★")
        ai = ai.sort_values(["AI受惠度","_stars"], ascending=False).head(10)
        st.dataframe(ai[["公司","代碼","產業","子產業","AI受惠度","全球競爭力","主題標籤"]], use_container_width=True, hide_index=True)

    with tab4:
        gl = df.copy()
        gl["_stars"] = gl["全球競爭力"].astype(str).str.count("★")
        gl = gl.sort_values(["_stars","AI受惠度"], ascending=False).head(10)
        st.dataframe(gl[["公司","代碼","產業","子產業","全球競爭力","全球排名","產業地位"]], use_container_width=True, hide_index=True)

    right1, right2 = st.columns([1,1])
    with right1:
        st.markdown('<div class="v230-card"><div class="v230-card-title">熱門主題標籤</div>', unsafe_allow_html=True)
        st.markdown(v230_tag_html("AI伺服器、CoWoS、先進封裝、HBM、光通訊、CPO、低軌衛星、機器人、無人機、國防軍工、車用電子、資料中心"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with right2:
        st.markdown('<div class="v230-card"><div class="v230-card-title">後續資料補齊重點</div><div class="v230-small-muted">1. 清除 N/A 股價與待補欄位<br>2. 補齊產業鏈位置<br>3. 補企業評價模型<br>4. 接財務預測 2026E / 2027E / 2028E</div></div>', unsafe_allow_html=True)

    with st.expander("產業 → 子產業 → 個股（選到即查詢）", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            ind = st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v231_home_ind")
        dff = df[df["產業"] == ind]
        with c2:
            sub = st.selectbox("子產業", sorted(dff["子產業"].dropna().unique()), key="v231_home_sub")
        dff = dff[dff["子產業"] == sub]
        labels = {f"{r['公司']} / {r['代碼']}": r["代碼"] for _, r in dff.iterrows()}
        with c3:
            picked = st.selectbox("個股", list(labels.keys()), key="v231_home_stock")
        if picked:
            code = labels[picked]
            if st.session_state.get("v231_last_pick") != picked:
                st.session_state["v231_last_pick"] = picked
                st.session_state["v227_active_symbol"] = code
                st.rerun()

    st.markdown("---")
    v230_price_block(st.session_state.get("v227_active_symbol","2330.TW"))

def v108_enterprise_home(): home()
def v107_premium_home(): home()
# ===== V231.0 RANKING DASHBOARD END =====





# ===== V232.0 DATA CLEANUP EXPANSION III START =====
V232_UPDATES = {'2408.TW': {'name': '南亞科', 'industry': '記憶體', 'sub': 'DRAM', 'rank': '台灣DRAM主要廠', 'power': '★★★☆☆', 'position': '台灣DRAM製造商，受記憶體循環與AI伺服器記憶體需求影響', 'peers': 'Samsung、SK hynix、Micron、華邦電、力積電', 'moat': '中：DRAM製程與產能，受全球寡占供給影響', 'risk': 'DRAM價格循環、資本支出、技術世代落差', 'fair_mult': 1.05, 'theme_text': '記憶體、DRAM、AI伺服器、HBM供應鏈外溢', 'chain_position': '上游記憶體製造', 'market_share': '台灣DRAM主要供應商'}, '2357.TW': {'name': '華碩', 'industry': 'AI PC/品牌', 'sub': 'PC/伺服器/AI PC', 'rank': '全球PC品牌', 'power': '★★★★☆', 'position': '全球PC、主機板與AI PC品牌', 'peers': 'Lenovo、HP、Dell、Acer、MSI', 'moat': '高：品牌、通路、主機板技術', 'risk': 'PC需求循環、庫存、匯率', 'fair_mult': 1.04, 'theme_text': 'AI PC、主機板、品牌PC、邊緣AI', 'chain_position': '下游品牌/系統', 'market_share': '全球PC與主機板主要品牌'}, '2353.TW': {'name': '宏碁', 'industry': 'AI PC/品牌', 'sub': 'PC品牌', 'rank': '全球PC品牌', 'power': '★★★☆☆', 'position': '全球PC品牌與AI PC受惠股', 'peers': 'Lenovo、HP、Dell、華碩、MSI', 'moat': '中：品牌、通路、教育與商用市場', 'risk': 'PC需求循環、庫存、競爭', 'fair_mult': 1.03, 'theme_text': 'AI PC、品牌PC、邊緣AI', 'chain_position': '下游品牌/系統', 'market_share': '全球PC品牌'}, '2377.TW': {'name': '微星', 'industry': 'AI PC/品牌', 'sub': '電競PC/主機板', 'rank': '電競PC與主機板品牌', 'power': '★★★☆☆', 'position': '電競筆電、主機板與AI PC品牌', 'peers': '華碩、技嘉、宏碁、Lenovo', 'moat': '中：電競品牌、主機板與顯卡通路', 'risk': 'PC需求循環、庫存、GPU供給', 'fair_mult': 1.04, 'theme_text': 'AI PC、電競PC、主機板、邊緣AI', 'chain_position': '下游品牌/系統', 'market_share': '全球電競PC與主機板品牌'}, '2376.TW': {'name': '技嘉', 'industry': 'AI伺服器/ODM', 'sub': '主機板/伺服器', 'rank': '主機板與伺服器供應商', 'power': '★★★★☆', 'position': '主機板、顯卡與AI伺服器供應商', 'peers': '華碩、微星、廣達、緯穎', 'moat': '中高：主機板、伺服器平台與通路', 'risk': 'AI伺服器出貨、PC循環、庫存', 'fair_mult': 1.06, 'theme_text': 'AI伺服器、AI PC、主機板、資料中心', 'chain_position': '中下游伺服器平台', 'market_share': '主機板與AI伺服器平台供應商'}, '3661.TW': {'name': '世芯-KY', 'industry': 'IC設計', 'sub': 'ASIC設計服務', 'rank': 'AI ASIC設計服務供應商', 'power': '★★★★☆', 'position': 'AI ASIC與客製化晶片設計服務供應商', 'peers': '創意、智原、Broadcom ASIC、Marvell', 'moat': '中高：ASIC設計能力、先進製程合作與客戶導入', 'risk': '客戶集中、專案時程、先進製程成本', 'fair_mult': 1.08, 'theme_text': 'AI ASIC、AI伺服器、HPC、客製化晶片', 'chain_position': '上游IC設計服務', 'market_share': 'AI ASIC設計服務主要廠'}, '3037.TW': {'name': '欣興', 'industry': 'PCB', 'sub': 'ABF載板/高階PCB', 'rank': 'ABF載板主要廠', 'power': '★★★★☆', 'position': 'ABF載板與高階PCB供應商', 'peers': '南電、景碩、Ibiden、Shinko', 'moat': '中高：ABF載板技術、客戶認證、產能規模', 'risk': 'ABF循環、AI需求波動、資本支出', 'fair_mult': 1.08, 'theme_text': 'ABF載板、AI伺服器、先進封裝、HPC', 'chain_position': '上游載板/PCB', 'market_share': 'ABF載板全球主要供應商'}, '3189.TW': {'name': '景碩', 'industry': 'PCB', 'sub': 'IC載板/ABF', 'rank': 'IC載板主要廠', 'power': '★★★☆☆', 'position': 'IC載板與ABF載板供應商', 'peers': '欣興、南電、Ibiden、Shinko', 'moat': '中：IC載板製程與客戶基礎', 'risk': 'ABF需求循環、資本支出', 'fair_mult': 1.05, 'theme_text': 'ABF載板、先進封裝、AI伺服器', 'chain_position': '上游載板/PCB', 'market_share': 'IC載板主要供應商'}, '8046.TW': {'name': '南電', 'industry': 'PCB', 'sub': 'ABF載板/IC載板', 'rank': 'ABF載板主要廠', 'power': '★★★★☆', 'position': 'ABF載板與IC載板主要供應商', 'peers': '欣興、景碩、Ibiden、Shinko', 'moat': '中高：ABF載板製程、客戶認證、集團資源', 'risk': 'ABF價格循環、客戶需求波動', 'fair_mult': 1.06, 'theme_text': 'ABF載板、先進封裝、AI伺服器、HPC', 'chain_position': '上游載板/PCB', 'market_share': 'ABF載板全球主要供應商'}, '2327.TW': {'name': '國巨', 'industry': '被動元件', 'sub': 'MLCC/晶片電阻', 'rank': '全球被動元件龍頭之一', 'power': '★★★★★', 'position': '全球MLCC、晶片電阻與被動元件龍頭之一', 'peers': 'Murata、TDK、Samsung Electro-Mechanics、華新科', 'moat': '高：規模、通路、產品組合、併購整合', 'risk': '被動元件循環、價格競爭、庫存', 'fair_mult': 1.05, 'theme_text': '被動元件、AI伺服器、車用電子、工業電子', 'chain_position': '上游零組件', 'market_share': '全球被動元件主要供應商'}, '2492.TW': {'name': '華新科', 'industry': '被動元件', 'sub': 'MLCC/晶片電阻', 'rank': '被動元件主要廠', 'power': '★★★☆☆', 'position': 'MLCC、晶片電阻與被動元件供應商', 'peers': '國巨、禾伸堂、Murata、TDK', 'moat': '中：產品線與集團資源', 'risk': '價格循環、庫存、需求波動', 'fair_mult': 1.03, 'theme_text': '被動元件、車用電子、AI伺服器', 'chain_position': '上游零組件', 'market_share': '台灣被動元件主要廠'}, '3026.TW': {'name': '禾伸堂', 'industry': '被動元件', 'sub': 'MLCC/通路', 'rank': '被動元件供應商', 'power': '★★★☆☆', 'position': 'MLCC與被動元件供應商', 'peers': '國巨、華新科、Murata、TDK', 'moat': '中：通路與產品組合', 'risk': '價格循環、庫存、需求波動', 'fair_mult': 1.03, 'theme_text': '被動元件、車用電子、AI伺服器', 'chain_position': '上游零組件/通路', 'market_share': '台灣被動元件供應商'}, '2344.TW': {'name': '華邦電', 'industry': '記憶體', 'sub': 'NOR Flash/DRAM', 'rank': '利基型記憶體主要廠', 'power': '★★★☆☆', 'position': 'NOR Flash、Specialty DRAM與利基型記憶體供應商', 'peers': '旺宏、南亞科、Micron、ISSI', 'moat': '中：利基型記憶體產品與客戶基礎', 'risk': '記憶體循環、價格競爭、稼動率', 'fair_mult': 1.04, 'theme_text': '記憶體、NOR Flash、DRAM、AI邊緣裝置', 'chain_position': '上游記憶體製造', 'market_share': '利基型記憶體主要供應商'}, '2337.TW': {'name': '旺宏', 'industry': '記憶體', 'sub': 'NOR Flash/ROM', 'rank': 'NOR Flash主要廠', 'power': '★★★☆☆', 'position': 'NOR Flash與ROM記憶體供應商', 'peers': '華邦電、Micron、Infineon', 'moat': '中：NOR Flash產品與客戶基礎', 'risk': '價格循環、消費電子需求', 'fair_mult': 1.03, 'theme_text': '記憶體、NOR Flash、車用電子、工控', 'chain_position': '上游記憶體製造', 'market_share': 'NOR Flash主要供應商'}, '8299.TWO': {'name': '群聯', 'industry': '記憶體', 'sub': 'NAND控制晶片/模組', 'rank': 'NAND控制晶片主要廠', 'power': '★★★★☆', 'position': 'NAND控制晶片與儲存解決方案供應商', 'peers': '慧榮、Marvell、Samsung、Western Digital', 'moat': '中高：控制晶片、韌體與客戶基礎', 'risk': 'NAND循環、庫存、需求波動', 'fair_mult': 1.06, 'theme_text': '記憶體、NAND控制晶片、AI儲存、邊緣AI', 'chain_position': '中游控制晶片/儲存', 'market_share': '全球NAND控制晶片主要廠'}, '3260.TWO': {'name': '威剛', 'industry': '記憶體', 'sub': '記憶體模組/通路', 'rank': '記憶體模組主要廠', 'power': '★★★☆☆', 'position': 'DRAM/NAND模組與儲存品牌供應商', 'peers': '金士頓、創見、十銓、宇瞻', 'moat': '中：品牌、通路與庫存管理', 'risk': '記憶體價格循環、庫存評價', 'fair_mult': 1.05, 'theme_text': '記憶體、DRAM模組、NAND模組、AI儲存', 'chain_position': '下游模組/通路', 'market_share': '記憶體模組主要品牌'}, '2451.TW': {'name': '創見', 'industry': '記憶體', 'sub': '記憶體模組/工控儲存', 'rank': '工控儲存供應商', 'power': '★★★☆☆', 'position': '記憶體模組、工控儲存與嵌入式儲存供應商', 'peers': '威剛、十銓、宇瞻、金士頓', 'moat': '中：工控儲存、品牌與通路', 'risk': '記憶體循環、庫存', 'fair_mult': 1.03, 'theme_text': '記憶體、工控儲存、邊緣AI', 'chain_position': '下游模組/工控儲存', 'market_share': '工控儲存供應商'}, '4967.TWO': {'name': '十銓', 'industry': '記憶體', 'sub': '記憶體模組/電競儲存', 'rank': '記憶體模組品牌', 'power': '★★★☆☆', 'position': '記憶體模組、電競儲存與消費儲存品牌', 'peers': '威剛、創見、宇瞻、金士頓', 'moat': '中：品牌與通路', 'risk': '記憶體價格循環、庫存', 'fair_mult': 1.04, 'theme_text': '記憶體、電競儲存、AI PC', 'chain_position': '下游模組/品牌', 'market_share': '記憶體模組品牌'}, '8271.TW': {'name': '宇瞻', 'industry': '記憶體', 'sub': '工控記憶體/模組', 'rank': '工控記憶體供應商', 'power': '★★★☆☆', 'position': '工控記憶體與嵌入式儲存供應商', 'peers': '創見、威剛、十銓', 'moat': '中：工控客戶與嵌入式產品', 'risk': '記憶體循環、工控需求', 'fair_mult': 1.03, 'theme_text': '記憶體、工控儲存、邊緣AI', 'chain_position': '下游工控模組', 'market_share': '工控記憶體供應商'}}
V232_FALLBACK_PRICE = {'2408.TW': 72.0, '2357.TW': 701.0, '2353.TW': 48.0, '2377.TW': 170.0, '2376.TW': 260.0, '3661.TW': 4200.0, '3037.TW': 142.0, '3189.TW': 105.0, '8046.TW': 180.0, '2327.TW': 180.0, '2492.TW': 105.0, '3026.TW': 95.0, '2344.TW': 28.0, '2337.TW': 30.0, '8299.TWO': 620.0, '3260.TWO': 120.0, '2451.TW': 95.0, '4967.TWO': 150.0, '8271.TW': 80.0}
V232_INDUSTRY_META = {'被動元件': {'規模': '中大', '成長率': '循環復甦', 'AI關聯度': '中高', '說明': 'MLCC、晶片電阻、電感與保護元件，受AI伺服器、車用與工業電子需求帶動。'}, '記憶體': {'規模': '大', '成長率': '高循環', 'AI關聯度': '高', '說明': 'DRAM、NAND、NOR Flash、記憶體模組與控制晶片，受AI伺服器、HBM與儲存需求帶動。'}, 'AI PC/品牌': {'規模': '大', '成長率': '中高', 'AI關聯度': '中高', '說明': 'PC品牌、主機板、電競PC與AI PC，受換機週期與邊緣AI推動。'}}

try:
    for sym, upd in V232_UPDATES.items():
        if sym in STOCK_DB:
            STOCK_DB[sym].update(upd)
        else:
            STOCK_DB[sym] = upd
    ALIASES.clear()
    for sym, v in STOCK_DB.items():
        ALIASES[sym.upper()] = sym
        ALIASES[sym.split(".")[0]] = sym
        ALIASES[v["name"]] = sym
        ALIASES[v["name"].upper()] = sym
except Exception:
    pass

try:
    V224_FALLBACK_PRICE.update(V232_FALLBACK_PRICE)
except Exception:
    V224_FALLBACK_PRICE = V232_FALLBACK_PRICE

try:
    V224_INDUSTRY_META.update(V232_INDUSTRY_META)
except Exception:
    V224_INDUSTRY_META = V232_INDUSTRY_META

# 讓排行資料重新吃到最新價格，避免南亞科等價格失真
try:
    def v232_rank_table(df):
        return v231_rank_table(df)
except Exception:
    pass
# ===== V232.0 DATA CLEANUP EXPANSION III END =====





# ===== V233.0 LIVE PRICE RANKING FIX START =====
# 修正低估排行：不再使用錯誤硬寫價格；優先 Yahoo Finance 現價，抓不到則 N/A 並排除低估排行

@st.cache_data(ttl=1800, show_spinner=False)
def v233_get_live_price(symbol):
    try:
        s = str(symbol).strip().upper()
        if not s:
            return float("nan")
        ticker = yf.Ticker(s)
        fast = getattr(ticker, "fast_info", None)
        if fast:
            for key in ["last_price", "lastPrice", "regular_market_price", "previous_close"]:
                try:
                    val = fast.get(key) if hasattr(fast, "get") else getattr(fast, key, None)
                    if val is not None and float(val) > 0:
                        return float(val)
                except Exception:
                    pass
        hist = ticker.history(period="5d", interval="1d", auto_adjust=False)
        if hist is not None and not hist.empty and "Close" in hist.columns:
            val = hist["Close"].dropna().iloc[-1]
            if float(val) > 0:
                return float(val)
    except Exception:
        pass
    return float("nan")

def v233_fair_multiplier(symbol):
    try:
        info = STOCK_DB.get(symbol, {})
        return float(info.get("fair_mult", 1.0))
    except Exception:
        return 1.0

def v231_rank_table(df):
    rows = []
    for _, r in df.iterrows():
        sym = r.get("代碼", "")
        px = v233_get_live_price(sym)
        fair_mult = v233_fair_multiplier(sym)
        try:
            fair = float(px) * fair_mult
            ret = (fair - float(px)) / float(px) * 100 if float(px) > 0 else float("nan")
        except Exception:
            fair, ret = float("nan"), float("nan")

        rows.append({
            "公司": r.get("公司",""),
            "代碼": sym,
            "產業": r.get("產業",""),
            "子產業": r.get("子產業",""),
            "現價": px,
            "綜合合理價": fair,
            "預期報酬%": ret,
            "AI受惠度": r.get("AI受惠度",0),
            "全球競爭力": r.get("全球競爭力",""),
            "主題標籤": r.get("主題標籤",""),
        })
    out = pd.DataFrame(rows)
    if not out.empty:
        out["現價"] = pd.to_numeric(out["現價"], errors="coerce")
        out["綜合合理價"] = pd.to_numeric(out["綜合合理價"], errors="coerce")
        out["預期報酬%"] = pd.to_numeric(out["預期報酬%"], errors="coerce")
        out["AI受惠度"] = pd.to_numeric(out["AI受惠度"], errors="coerce").fillna(0)
    return out

def v233_decision(symbol):
    # 單股頁現價也改優先 Yahoo Finance，避免 fallback 錯價
    try:
        d = v230_decision(symbol)
    except Exception:
        d = {"symbol":symbol, "name":symbol, "price":float("nan"), "fair":float("nan"), "cons":float("nan"), "opt":float("nan"), "ret":0, "action":"觀察", "source":"N/A", "updated":"N/A"}
    try:
        sym = d.get("symbol", symbol)
        px = v233_get_live_price(sym)
        if pd.notna(px) and float(px) > 0:
            mult = v233_fair_multiplier(sym)
            d["price"] = float(px)
            d["fair"] = float(px) * mult
            d["cons"] = float(px) * max(mult * 0.88, 0.70)
            d["opt"] = float(px) * max(mult * 1.12, 1.05)
            d["ret"] = (d["fair"] - d["price"]) / d["price"] * 100
            d["source"] = "Yahoo Finance"
    except Exception:
        pass
    return d

def v230_decision(symbol):
    return v233_decision(symbol)

def home():
    v230_css()
    if "v227_active_symbol" not in st.session_state:
        st.session_state["v227_active_symbol"] = "2330.TW"

    now_show = datetime.now().strftime("%Y/%m/%d %H:%M")
    st.markdown(f"""
    <div class="v230-topbar">
      <div>
        <div class="v230-brand">📈 智策股市 AI 決策平台</div>
        <div class="v230-sub">企業價值研究平台｜產業鏈 × 全球競爭力 × 財務預測 × 合理價推估</div>
      </div>
      <div class="v230-version">V233 Live Price Fix<br>{now_show}</div>
    </div>
    """, unsafe_allow_html=True)

    q = st.text_input("搜尋公司名稱 / 代號 / 產業 / 主題標籤", placeholder="例如：2330、台積電、2313、華通、低軌衛星、CoWoS", key="v233_search")
    if str(q or "").strip():
        st.session_state["v227_active_symbol"] = v230_symbol(q)

    df = v230_rows_df()
    if df.empty:
        st.warning("資料庫尚未載入。")
        return

    rank = v231_rank_table(df)

    total = len(df)
    hot_ind = df["產業"].nunique()
    hot_theme = len(set("、".join(df["主題標籤"].fillna("").astype(str)).split("、"))) if "主題標籤" in df.columns else 0
    ai9 = int((pd.to_numeric(df["AI受惠度"], errors="coerce").fillna(0) >= 9).sum()) if "AI受惠度" in df.columns else 0
    valid_price = int(rank["現價"].notna().sum()) if not rank.empty else 0
    global5 = int(df["全球競爭力"].astype(str).str.contains("★★★★★", regex=False).sum()) if "全球競爭力" in df.columns else 0

    st.markdown(f"""
    <div class="v230-kpi-grid">
      <div class="v230-kpi"><div class="v230-kpi-icon">🔥</div><div class="v230-kpi-label">熱門產業</div><div class="v230-kpi-value">{hot_ind}</div><div class="v230-kpi-note">涵蓋主要主產業</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">🏆</div><div class="v230-kpi-label">個股資料庫</div><div class="v230-kpi-value">{total}</div><div class="v230-kpi-note">持續補齊中</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">🏷️</div><div class="v230-kpi-label">主題標籤</div><div class="v230-kpi-value">{hot_theme}</div><div class="v230-kpi-note">可多重歸屬</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">💹</div><div class="v230-kpi-label">有效現價</div><div class="v230-kpi-value">{valid_price}</div><div class="v230-kpi-note">Yahoo Finance</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">🤖</div><div class="v230-kpi-label">AI高受惠</div><div class="v230-kpi-value">{ai9}</div><div class="v230-kpi-note">AI受惠度 ≥ 9</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">🌏</div><div class="v230-kpi-label">全球強勢</div><div class="v230-kpi-value">{global5}</div><div class="v230-kpi-note">★★★★★</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 核心快速查詢")
    quick = [("台積電","2330"),("華通","2313"),("昇達科","3491"),("廣達","2382"),("奇鋐","3017"),("聯鈞","3450")]
    cols = st.columns(len(quick))
    for col, (name, code_) in zip(cols, quick):
        with col:
            if st.button(name, key=f"v233_quick_{code_}", use_container_width=True):
                st.session_state["v227_active_symbol"] = v230_symbol(code_)
                st.rerun()

    with st.expander("排行計算標準", expanded=False):
        st.markdown("""
        **重要修正：V233 起，低估排行不再使用硬寫價格。**  
        現價優先抓 Yahoo Finance 最近價格；抓不到現價者不列入低估排行，避免錯誤價格造成排行失真。  

        **低估排行 TOP 10**：`預期報酬 = (綜合合理價 - 現價) ÷ 現價`  
        目前綜合合理價仍是資料庫倍率模型；等企業評價模型完成後，會改用 DCF / EVA / EBO / FCFF / 財測模型。
        """)

    tab1, tab2, tab3, tab4 = st.tabs(["熱門個股", "低估排行", "AI受惠排行", "全球競爭力排行"])

    with tab1:
        show = df.copy()
        show["_stars"] = show["全球競爭力"].astype(str).str.count("★")
        show = show.sort_values(["AI受惠度","_stars"], ascending=False).head(10)
        st.dataframe(show[["公司","代碼","產業","子產業","AI受惠度","全球競爭力","產業地位"]], use_container_width=True, hide_index=True)

    with tab2:
        low = rank.dropna(subset=["現價","綜合合理價","預期報酬%"])
        low = low[low["現價"] > 0].sort_values("預期報酬%", ascending=False).head(10)
        st.dataframe(v231_fmt_rank(low[["公司","代碼","產業","子產業","現價","綜合合理價","預期報酬%","AI受惠度"]]), use_container_width=True, hide_index=True)
        st.caption("若現價為 N/A，代表 Yahoo Finance 暫時抓不到，系統會自動排除低估排行，避免錯價。")

    with tab3:
        ai = df.copy()
        ai["_stars"] = ai["全球競爭力"].astype(str).str.count("★")
        ai = ai.sort_values(["AI受惠度","_stars"], ascending=False).head(10)
        st.dataframe(ai[["公司","代碼","產業","子產業","AI受惠度","全球競爭力","主題標籤"]], use_container_width=True, hide_index=True)

    with tab4:
        gl = df.copy()
        gl["_stars"] = gl["全球競爭力"].astype(str).str.count("★")
        gl = gl.sort_values(["_stars","AI受惠度"], ascending=False).head(10)
        st.dataframe(gl[["公司","代碼","產業","子產業","全球競爭力","全球排名","產業地位"]], use_container_width=True, hide_index=True)

    with st.expander("產業 → 子產業 → 個股（選到即查詢）", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            ind = st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v233_home_ind")
        dff = df[df["產業"] == ind]
        with c2:
            sub = st.selectbox("子產業", sorted(dff["子產業"].dropna().unique()), key="v233_home_sub")
        dff = dff[dff["子產業"] == sub]
        labels = {f"{r['公司']} / {r['代碼']}": r["代碼"] for _, r in dff.iterrows()}
        with c3:
            picked = st.selectbox("個股", list(labels.keys()), key="v233_home_stock")
        if picked:
            code = labels[picked]
            if st.session_state.get("v233_last_pick") != picked:
                st.session_state["v233_last_pick"] = picked
                st.session_state["v227_active_symbol"] = code
                st.rerun()

    st.markdown("---")
    v230_price_block(st.session_state.get("v227_active_symbol","2330.TW"))

def v108_enterprise_home(): home()
def v107_premium_home(): home()
# ===== V233.0 LIVE PRICE RANKING FIX END =====




# ===== V234.0 MOBILE CSS + MAIN CUSTOMERS + STOCK DATA EXPANSION START =====
# 1) 修正手機版 Sidebar 淺底白字問題
# 2) 新增「主要客戶/終端客戶」欄位
# 3) 繼續補齊個股資料
# 4) 修正 V233 v230_decision 遞迴覆寫問題

APP_VERSION = "V235.0 Full Valuation Range + Customer Expansion"

V234_CUSTOMER_UPDATES = {
    "2330.TW": {"customers":"Apple、NVIDIA、AMD、Qualcomm、MediaTek、Broadcom、Marvell、Tesla 等全球IC與AI/HPC客戶"},
    "2303.TW": {"customers":"車用、工控、通訊與消費IC客戶；含IDM與IC設計公司"},
    "5347.TWO": {"customers":"PMIC、DDI、電源管理IC與車用/工控IC設計客戶"},
    "2454.TW": {"customers":"Android手機品牌、智慧電視、Wi-Fi/網通、車用與邊緣AI裝置客戶"},
    "3034.TW": {"customers":"面板廠、手機/IT/電視品牌、車用顯示供應鏈"},
    "2379.TW": {"customers":"PC、NB、主機板、網通設備、音訊與車用電子客戶"},
    "5274.TWO": {"customers":"全球伺服器OEM/ODM、雲端資料中心、BMC平台客戶"},
    "3661.TW": {"customers":"AI ASIC、HPC、雲端服務商與客製化晶片專案客戶"},
    "3443.TW": {"customers":"ASIC/NRE、AI/HPC、網通與系統廠客製化晶片客戶"},
    "3035.TW": {"customers":"ASIC、IP、工控、網通、AIoT與邊緣裝置晶片客戶"},
    "3711.TW": {"customers":"全球IDM、晶圓代工、IC設計、手機與AI/HPC晶片客戶"},
    "2449.TW": {"customers":"晶圓測試、AI/HPC、車用、通訊與IC設計客戶"},
    "3131.TWO": {"customers":"台積電與先進封裝/半導體濕製程設備客戶群"},
    "6223.TWO": {"customers":"晶圓測試、探針卡、AI/HPC、手機與車用晶片測試客戶"},
    "2382.TW": {"customers":"雲端CSP、AI伺服器客戶、品牌NB與資料中心客戶"},
    "3231.TW": {"customers":"雲端資料中心、AI伺服器、企業伺服器與品牌PC客戶"},
    "6669.TW": {"customers":"大型雲端服務商、資料中心、AI伺服器平台客戶"},
    "2356.TW": {"customers":"伺服器、NB、企業IT與雲端客戶"},
    "2317.TW": {"customers":"Apple、雲端/AI伺服器、電動車與全球品牌電子客戶"},
    "2345.TW": {"customers":"雲端資料中心、白牌交換器、網通品牌與電信設備客戶"},
    "2383.TW": {"customers":"AI伺服器、交換器、PCB/載板廠、品牌與雲端供應鏈客戶"},
    "6274.TWO": {"customers":"高速網通、AI伺服器、PCB廠與資料中心供應鏈客戶"},
    "3037.TW": {"customers":"CPU/GPU/ASIC、ABF載板、伺服器與消費電子客戶"},
    "8046.TW": {"customers":"ABF/BT載板、CPU/GPU/網通與封裝供應鏈客戶"},
    "3189.TW": {"customers":"IC載板、ABF、手機/網通/半導體封裝客戶"},
    "2368.TW": {"customers":"AI伺服器、網通、交換器與高階PCB客戶"},
    "3017.TW": {"customers":"AI伺服器ODM、GPU平台、資料中心與散熱模組客戶"},
    "3324.TWO": {"customers":"AI伺服器、NB、顯卡與液冷/散熱模組客戶"},
    "3653.TW": {"customers":"AI伺服器、CPU/GPU、散熱導熱與均熱元件客戶"},
    "2059.TW": {"customers":"全球伺服器滑軌、資料中心與伺服器機構件客戶"},
    "2308.TW": {"customers":"資料中心、電源管理、工業自動化、電動車與能源基礎建設客戶"},
    "1519.TW": {"customers":"台電、電網工程、變壓器、重電與海外電力基礎建設客戶"},
    "1513.TW": {"customers":"台電、電網設備、充電樁、重電工程與公共建設客戶"},
    "2327.TW": {"customers":"車用、工控、AI伺服器、通訊與消費電子被動元件客戶"},
    "2492.TW": {"customers":"車用、工控、通訊、消費電子與被動元件客戶"},
    "3026.TW": {"customers":"MLCC、被動元件通路、車用與工控客戶"},
    "2408.TW": {"customers":"DRAM、記憶體模組、PC、伺服器與消費電子客戶"},
    "2344.TW": {"customers":"NOR Flash、Specialty DRAM、車用、工控與消費電子客戶"},
    "2337.TW": {"customers":"NOR Flash、車用、工控、網通與消費電子客戶"},
    "3260.TWO": {"customers":"記憶體模組、電競、工控、通路與品牌客戶"},
    "2451.TW": {"customers":"工控儲存、嵌入式記憶體、品牌與通路客戶"},
    "4967.TWO": {"customers":"電競記憶體、消費儲存、通路與品牌客戶"},
    "8271.TW": {"customers":"工控記憶體、嵌入式儲存、邊緣裝置與通路客戶"},
    "8299.TWO": {"customers":"NAND控制晶片、SSD、記憶體品牌、工控與AI儲存客戶"},
    "6215.TWO": {"customers":"工業自動化、智慧工廠、機器人、自動化零組件與整合客戶"},
    "2049.TW": {"customers":"工具機、自動化設備、半導體設備、醫療與機器人客戶"},
}

V234_EXTRA_STOCKS = {
    "3450.TW": {"name":"聯鈞", "industry":"光通訊/CPO", "sub":"光通訊元件/雷射", "rank":"光通訊供應商", "power":"★★★★☆", "position":"AI資料中心光通訊與高速傳輸供應鏈", "peers":"華星光、上詮、眾達、光聖", "moat":"中高：光通訊元件、客戶認證與AI資料中心需求", "risk":"AI資料中心出貨節奏、價格競爭、客戶集中", "fair_mult":1.08, "theme_text":"光通訊、CPO、AI資料中心、800G、矽光子", "chain_position":"中游光通訊元件", "market_share":"光通訊元件供應商", "customers":"AI資料中心、光模組、交換器與雲端供應鏈客戶"},
    "3491.TWO": {"name":"昇達科", "industry":"低軌衛星/通訊", "sub":"微波/毫米波元件", "rank":"衛星通訊利基供應商", "power":"★★★☆☆", "position":"低軌衛星、微波通訊與毫米波元件供應商", "peers":"啟碁、穩懋、宏捷科、國際微波元件商", "moat":"中：射頻/微波設計與小量多樣利基訂單", "risk":"低軌衛星建置時程、客戶集中、題材波動", "fair_mult":1.06, "theme_text":"低軌衛星、微波通訊、國防通訊、5G", "chain_position":"上游射頻/微波元件", "market_share":"低軌衛星通訊供應鏈", "customers":"低軌衛星、微波通訊、電信設備與國防通訊客戶"},
    "2313.TW": {"name":"華通", "industry":"PCB", "sub":"HDI/伺服器PCB/衛星通訊", "rank":"PCB主要廠", "power":"★★★★☆", "position":"HDI、伺服器、低軌衛星與消費電子PCB供應商", "peers":"欣興、健鼎、金像電、臻鼎-KY", "moat":"中高：PCB量產、HDI與多元客戶認證", "risk":"消費電子循環、AI與低軌出貨節奏、匯率", "fair_mult":1.05, "theme_text":"PCB、AI伺服器、低軌衛星、HDI、車用電子", "chain_position":"上游PCB", "market_share":"全球PCB主要供應商", "customers":"Apple供應鏈、低軌衛星、伺服器、網通與消費電子客戶"},
    "6285.TW": {"name":"啟碁", "industry":"網通/低軌衛星", "sub":"網通設備/衛星通訊", "rank":"網通設備主要廠", "power":"★★★★☆", "position":"網通、衛星通訊、車用與寬頻設備供應商", "peers":"智邦、中磊、合勤控、國際網通設備商", "moat":"中高：網通整合、客戶認證與多產品線", "risk":"客戶需求波動、價格競爭、庫存", "fair_mult":1.05, "theme_text":"低軌衛星、網通、車聯網、寬頻設備", "chain_position":"中下游系統/網通設備", "market_share":"網通設備主要供應商", "customers":"電信營運商、網通品牌、車用與低軌衛星設備客戶"},
    "3105.TWO": {"name":"穩懋", "industry":"化合物半導體", "sub":"GaAs晶圓代工/RF", "rank":"GaAs晶圓代工主要廠", "power":"★★★★☆", "position":"射頻PA、Wi-Fi、手機與衛星通訊GaAs晶圓代工", "peers":"宏捷科、全新、Skyworks供應鏈、Qorvo供應鏈", "moat":"中高：GaAs製程、RF客戶認證與產能規模", "risk":"手機射頻循環、稼動率、價格競爭", "fair_mult":1.04, "theme_text":"射頻、GaAs、低軌衛星、Wi-Fi、手機PA", "chain_position":"上游化合物半導體代工", "market_share":"全球GaAs代工主要廠", "customers":"RF IC、手機PA、Wi-Fi、衛星通訊與IDM客戶"},
    "8086.TWO": {"name":"宏捷科", "industry":"化合物半導體", "sub":"GaAs磊晶/晶圓代工", "rank":"GaAs供應商", "power":"★★★☆☆", "position":"射頻元件、手機PA與衛星通訊GaAs供應鏈", "peers":"穩懋、全新、Skyworks供應鏈、Qorvo供應鏈", "moat":"中：GaAs製程與RF客戶基礎", "risk":"手機需求循環、稼動率、競爭", "fair_mult":1.03, "theme_text":"射頻、GaAs、低軌衛星、手機PA", "chain_position":"上游化合物半導體", "market_share":"GaAs供應商", "customers":"手機PA、RF IC、Wi-Fi與衛星通訊客戶"},
    "2455.TW": {"name":"全新", "industry":"化合物半導體", "sub":"GaAs磊晶", "rank":"GaAs磊晶供應商", "power":"★★★☆☆", "position":"GaAs磊晶、射頻與光通訊材料供應商", "peers":"穩懋、宏捷科、IQE、AXT", "moat":"中：磊晶技術與RF/光通訊應用", "risk":"手機PA需求、客戶集中、價格競爭", "fair_mult":1.04, "theme_text":"GaAs、射頻、光通訊、低軌衛星", "chain_position":"上游磊晶材料", "market_share":"GaAs磊晶供應商", "customers":"RF晶圓代工、PA、光通訊與衛星通訊客戶"},
    "5388.TWO": {"name":"中磊", "industry":"網通", "sub":"寬頻/網通設備", "rank":"寬頻網通設備主要廠", "power":"★★★☆☆", "position":"寬頻、電信網通、智慧家庭與企業網通設備供應商", "peers":"啟碁、智邦、合勤控、國際網通設備商", "moat":"中：電信客戶與網通設備整合", "risk":"電信資本支出、價格競爭、庫存", "fair_mult":1.03, "theme_text":"網通、寬頻、Wi-Fi 7、電信設備", "chain_position":"中下游網通設備", "market_share":"寬頻網通設備供應商", "customers":"電信營運商、寬頻設備、企業網通與智慧家庭客戶"},
}

try:
    for _sym, _upd in V234_EXTRA_STOCKS.items():
        STOCK_DB[_sym] = {**STOCK_DB.get(_sym, {}), **_upd}
    for _sym, _upd in V234_CUSTOMER_UPDATES.items():
        if _sym in STOCK_DB:
            STOCK_DB[_sym].update(_upd)
    ALIASES.clear()
    for _sym, _v in STOCK_DB.items():
        ALIASES[_sym.upper()] = _sym
        ALIASES[_sym.split(".")[0]] = _sym
        ALIASES[_v.get("name", _sym)] = _sym
        ALIASES[_v.get("name", _sym).upper()] = _sym
except Exception:
    pass

try:
    _v234_original_decision = decision
except Exception:
    _v234_original_decision = None

def v230_decision(symbol):
    """V234 safe decision: avoid V233 recursive v230_decision -> v233_decision loop."""
    sym = v230_symbol(symbol)
    try:
        if _v234_original_decision is not None:
            d = _v234_original_decision(sym)
        else:
            d = {"symbol": sym, "name": STOCK_DB.get(sym, {}).get("name", sym), "price": float("nan"), "fair": float("nan"), "cons": float("nan"), "opt": float("nan"), "ret": 0, "action": "觀察", "source": "N/A", "updated": tw_now()}
    except Exception:
        d = {"symbol": sym, "name": STOCK_DB.get(sym, {}).get("name", sym), "price": float("nan"), "fair": float("nan"), "cons": float("nan"), "opt": float("nan"), "ret": 0, "action": "觀察", "source": "N/A", "updated": tw_now()}
    try:
        px = v233_get_live_price(sym)
        if pd.notna(px) and float(px) > 0:
            mult = v233_fair_multiplier(sym)
            d["price"] = float(px)
            d["fair"] = float(px) * mult
            d["cons"] = float(px) * max(mult * 0.88, 0.70)
            d["opt"] = float(px) * max(mult * 1.12, 1.05)
            d["ret"] = (d["fair"] - d["price"]) / d["price"] * 100
            d["source"] = "Yahoo Finance"
            d["updated"] = tw_now()
    except Exception:
        pass
    try:
        info = STOCK_DB.get(sym, {})
        d["customers"] = info.get("customers", "待補")
        d["main_customers"] = info.get("customers", "待補")
    except Exception:
        pass
    return d

def v230_css():
    st.markdown("""
    <style>
    #MainMenu, footer {visibility:hidden;}
    .main .block-container{padding-top:1.2rem;max-width:1320px;}
    section[data-testid="stSidebar"]{background:#f3f6fb !important;}
    section[data-testid="stSidebar"] *{color:#0f172a !important;}
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] [data-baseweb="radio"] *{color:#0f172a !important;}
    section[data-testid="stSidebar"] input{color:#0f172a !important;background:#ffffff !important;}
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] *{color:#0f172a !important;}
    .v230-topbar{display:flex;align-items:center;justify-content:space-between;background:#fff;border:1px solid #e6edf7;border-radius:18px;padding:18px 22px;margin:8px 0 18px 0;box-shadow:0 10px 30px rgba(15,23,42,.06);}
    .v230-brand{font-size:28px;font-weight:900;color:#102033;line-height:1.1;}
    .v230-sub{font-size:13px;color:#64748b;margin-top:5px;}
    .v230-version{font-size:13px;color:#2563eb;font-weight:700;}
    .v230-card{background:#fff;border:1px solid #e6edf7;border-radius:18px;padding:18px;margin:10px 0;box-shadow:0 10px 24px rgba(15,23,42,.05);overflow:hidden;}
    .v230-card-title{font-size:18px;font-weight:850;color:#102033;margin-bottom:10px;}
    .v230-kpi-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin:16px 0 18px 0;}
    .v230-kpi{background:#fff;border:1px solid #e6edf7;border-radius:18px;padding:16px;min-height:108px;box-shadow:0 8px 22px rgba(15,23,42,.05);overflow:hidden;}
    .v230-kpi-icon{font-size:24px;margin-bottom:8px;}
    .v230-kpi-label{color:#64748b;font-size:13px;font-weight:700;}
    .v230-kpi-value{font-size:28px;font-weight:900;color:#0f172a;margin-top:4px;word-break:break-word;}
    .v230-kpi-note{font-size:12px;color:#64748b;margin-top:4px;}
    .v230-tag-wrap{display:flex;flex-wrap:wrap;gap:7px;max-width:100%;white-space:normal;line-height:2.2;}
    .v230-tag{display:inline-flex;align-items:center;border:1px solid #bfdbfe;background:#eff6ff;color:#1d4ed8;border-radius:9px;padding:3px 8px;font-size:13px;font-weight:750;white-space:nowrap;}
    .v230-tag:nth-child(2n){background:#faf5ff;color:#7e22ce;border-color:#d8b4fe;}
    .v230-tag:nth-child(3n){background:#fff7ed;color:#c2410c;border-color:#fed7aa;}
    .v230-tag:nth-child(4n){background:#ecfdf5;color:#15803d;border-color:#bbf7d0;}
    .v230-tag:nth-child(5n){background:#fdf2f8;color:#be185d;border-color:#fbcfe8;}
    .v230-small-muted{color:#64748b;font-size:12px;line-height:1.7;}
    div[data-testid="stDataFrame"] div[role="gridcell"]{white-space:normal !important;}
    .stButton>button{border-radius:12px;border:1px solid #dbe7f5;background:#fff;min-height:42px;font-weight:700;color:#1e293b;}
    .stButton>button:hover{border-color:#60a5fa;color:#1d4ed8;background:#eff6ff;}
    @media(max-width:1000px){.v230-kpi-grid{grid-template-columns:repeat(2,1fr);} .v230-topbar{display:block;}}
    @media(max-width:768px){
        .main .block-container{padding-left:1rem !important;padding-right:1rem !important;}
        .v230-brand{font-size:26px !important;}
        .v230-sub{font-size:16px !important;line-height:1.55 !important;}
        .v230-version{font-size:16px !important;margin-top:10px !important;}
        .v230-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr)) !important;gap:14px !important;}
        .v230-kpi{min-height:155px !important;padding:18px 16px !important;}
        .v230-kpi-value{font-size:34px !important;line-height:1.15 !important;}
        .v230-kpi-label{font-size:16px !important;}
        .v230-kpi-note{font-size:14px !important;}
        section[data-testid="stSidebar"]{background:#f3f6fb !important;}
        section[data-testid="stSidebar"] *{color:#0f172a !important;text-shadow:none !important;opacity:1 !important;}
        section[data-testid="stSidebar"] input{background:#111827 !important;color:#f9fafb !important;}
    }
    @media(max-width:420px){
        .v230-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr)) !important;}
        .v230-kpi{min-height:165px !important;}
        .v230-brand{font-size:24px !important;}
    }
    </style>
    """, unsafe_allow_html=True)

def v230_rows_df():
    rows=[]
    for sym, v in STOCK_DB.items():
        vv={**v,"symbol":sym}
        try:
            ai=v227_ai_score(vv)
        except Exception:
            ai=3
        rows.append({
            "產業":v.get("industry","待補"),
            "子產業":v.get("sub","待補"),
            "公司":v.get("name",sym),
            "代碼":sym,
            "產業鏈位置":v.get("chain_position","待補"),
            "主題標籤":v.get("theme_text","一般產業" if ai>0 else "非AI主題"),
            "AI受惠度":ai,
            "全球競爭力":v.get("power","★★★☆☆"),
            "全球排名":v.get("rank","待補"),
            "全球市占率":v.get("market_share","待補"),
            "產業地位":v.get("position","待補"),
            "主要客戶":v.get("customers", v.get("main_customers", "待補")),
            "主要競爭者":v.get("peers","待補"),
            "護城河":v.get("moat","待補"),
            "主要風險":v.get("risk","待補"),
        })
    return pd.DataFrame(rows)

def v224_rows_df(): return v230_rows_df()
def v225_rows_df(): return v230_rows_df()
def v226_rows_df(): return v230_rows_df()
def v227_rows_df(): return v230_rows_df()

def v230_price_block(symbol):
    d=v230_decision(symbol); sym=d.get("symbol", symbol)
    st.caption(f"資料更新時間：{d.get('updated','N/A')}｜現價來源：{d.get('source','Yahoo Finance')}｜預期報酬率＝(綜合合理價－現價)÷現價。")
    st.markdown(f"## {d.get('name', sym)}（{sym}）")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("投資建議", d.get("action","觀察"))
    c2.metric("現價", v230_fmt(d.get("price", float("nan"))))
    c3.metric("綜合合理價", v230_fmt(d.get("fair", float("nan"))))
    try: ret_txt=f"{float(d.get('ret',0)):.1f}%"
    except Exception: ret_txt="N/A"
    c4.metric("預期報酬", ret_txt)
    p1,p2,p3=st.columns(3)
    p1.metric("安全邊際價", v230_fmt(d.get("cons", float("nan"))))
    p2.metric("合理價值", v230_fmt(d.get("fair", float("nan"))))
    p3.metric("潛在價值", v230_fmt(d.get("opt", float("nan"))))
    df=v230_rows_df(); row=df[df["代碼"]==sym] if not df.empty and "代碼" in df.columns else pd.DataFrame()
    with st.expander("展開更多研究資料", expanded=True):
        if not row.empty:
            r=row.iloc[0].to_dict()
            st.markdown("### 公司基本資料")
            st.markdown(f'<div class="v230-card"><div class="v230-card-title">{r.get("公司","")}｜{r.get("代碼","")}</div><div class="v230-small-muted">主產業：{r.get("產業","")}　｜　子產業：{r.get("子產業","")}　｜　產業鏈位置：{r.get("產業鏈位置","待補")}</div><div style="margin-top:10px;">{v230_tag_html(r.get("主題標籤",""))}</div></div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame([{
                "全球排名":r.get("全球排名","待補"),
                "全球市占率":r.get("全球市占率","待補"),
                "產業地位":r.get("產業地位","待補"),
                "主要客戶":r.get("主要客戶","待補"),
                "主要競爭者":r.get("主要競爭者","待補"),
                "護城河":r.get("護城河","待補"),
                "主要風險":r.get("主要風險","待補")
            }]), use_container_width=True, hide_index=True)
        else:
            st.info("此個股仍在資料庫補齊中，後續會補上產業鏈位置、主題標籤、主要客戶、競爭者與護城河。")

def industry_page():
    v230_css(); st.header("🏭 產業分析")
    df=v230_rows_df()
    c1,c2,c3=st.columns(3)
    with c1: ind=st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v234_industry_ind")
    dff=df[df["產業"]==ind]
    with c2: sub=st.selectbox("子產業", sorted(dff["子產業"].dropna().unique()), key="v234_industry_sub")
    dff=dff[dff["子產業"]==sub]
    labels={f"{r['公司']} / {r['代碼']}":r["代碼"] for _,r in dff.iterrows()}
    with c3: picked=st.selectbox("個股（選到即查詢）", list(labels.keys()), key="v234_industry_stock")
    code=labels[picked]; st.session_state["v227_active_symbol"]=code
    row=dff[dff["代碼"]==code].iloc[0].to_dict()
    meta=V224_INDUSTRY_META.get(ind, {"規模":"待補","成長率":"待補","AI關聯度":"待補","說明":"待補"})
    k1,k2,k3,k4=st.columns(4); k1.metric("產業規模", meta.get("規模","待補")); k2.metric("成長率", meta.get("成長率","待補")); k3.metric("AI關聯度", meta.get("AI關聯度","待補")); k4.metric("同產業公司", len(dff))
    st.info(meta.get("說明",""))
    st.markdown("### 公司基本資料")
    st.markdown(f'<div class="v230-card"><div class="v230-card-title">{row.get("公司","")}｜{row.get("代碼","")}</div><div class="v230-small-muted">主產業：{row.get("產業","")}　｜　子產業：{row.get("子產業","")}　｜　產業鏈位置：{row.get("產業鏈位置","待補")}</div><div style="margin-top:10px;">{v230_tag_html(row.get("主題標籤",""))}</div></div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([{"全球排名":row.get("全球排名","待補"),"全球市占率":row.get("全球市占率","待補"),"產業地位":row.get("產業地位","待補"),"主要客戶":row.get("主要客戶","待補"),"主要競爭者":row.get("主要競爭者","待補"),"護城河":row.get("護城河","待補"),"主要風險":row.get("主要風險","待補")}]), use_container_width=True, hide_index=True)
    st.markdown("### 同產業主要公司")
    cols=["公司","代碼","子產業","產業鏈位置","主要客戶","AI受惠度","全球競爭力","產業地位"]
    st.dataframe(dff[[c for c in cols if c in dff.columns]], use_container_width=True, hide_index=True)

def competition_page():
    v230_css(); st.header("🌏 全球競爭力")
    df=v230_rows_df()
    themes=["全部"]+sorted(set([p.strip() for s in df["主題標籤"].fillna("").astype(str) for p in s.replace("，","、").split("、") if p.strip()]))
    c0,c1,c2,c3=st.columns(4)
    with c0: theme=st.selectbox("主題標籤", themes, key="v234_global_theme")
    if theme!="全部": df=df[df["主題標籤"].astype(str).str.contains(theme, na=False)]
    with c1: ind=st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v234_global_ind")
    dff=df[df["產業"]==ind]
    with c2: sub=st.selectbox("子產業", sorted(dff["子產業"].dropna().unique()), key="v234_global_sub")
    dff=dff[dff["子產業"]==sub]
    labels={f"{r['公司']} / {r['代碼']}":r["代碼"] for _,r in dff.iterrows()}
    with c3: picked=st.selectbox("個股（選到即查詢）", list(labels.keys()), key="v234_global_stock")
    code=labels[picked]; st.session_state["v227_active_symbol"]=code
    row=dff[dff["代碼"]==code].iloc[0].to_dict()
    st.markdown(f"## {row['公司']}（{row['代碼']}）")
    g1,g2,g3,g4=st.columns(4)
    try: ai_txt=f"{int(row['AI受惠度'])}/10" if int(row["AI受惠度"])>0 else "非AI主題"
    except Exception: ai_txt="N/A"
    g1.metric("全球排名", row["全球排名"]); g2.metric("AI受惠度", ai_txt); g3.metric("全球競爭力", row["全球競爭力"]); g4.metric("全球市占率", row["全球市占率"])
    st.markdown(v230_tag_html(row.get("主題標籤","")), unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([{"產業地位":row["產業地位"],"主要客戶":row.get("主要客戶","待補"),"競爭者":row["主要競爭者"],"護城河":row["護城河"],"主要風險":row["主要風險"],"產業鏈位置":row["產業鏈位置"]}]), use_container_width=True, hide_index=True)
    try:
        st.markdown("---"); v224_ai_score_explanation()
    except Exception:
        pass
# ===== V234.0 MOBILE CSS + MAIN CUSTOMERS + STOCK DATA EXPANSION END =====


# ===== V235.0 FULL VALUATION RANGE + CUSTOMER EXPANSION START =====
# 目標：所有資料庫個股都能產生「安全邊際價 / 合理價 / 潛在價」三段股價區間，並逐步補齊主要客戶與供應鏈位置。

V235_CUSTOMER_PATCH = {
    "2330.TW": {"customers":"Apple、NVIDIA、AMD、Qualcomm、Broadcom、MediaTek、Marvell、Sony、Tesla供應鏈", "ai_customers":"NVIDIA、AMD、Broadcom、Marvell、Google TPU供應鏈、AWS Trainium供應鏈", "chain_position":"AI/HPC晶圓代工核心", "market_share":"全球晶圓代工#1"},
    "2303.TW": {"customers":"Qualcomm、MediaTek、Realtek、Novatek、車用/工控IC客戶", "ai_customers":"邊緣AI與成熟製程電源/車用客戶", "chain_position":"成熟製程晶圓代工", "market_share":"成熟製程主要供應商"},
    "5347.TWO": {"customers":"聯詠、瑞昱、電源管理IC、DDI、PMIC與車用IC客戶", "ai_customers":"AI電源管理與工控周邊間接受惠", "chain_position":"特殊製程晶圓代工", "market_share":"特殊製程主要供應商"},
    "2454.TW": {"customers":"小米、OPPO、vivo、Samsung、Amazon、車用與邊緣裝置品牌", "ai_customers":"AI手機、Edge AI、車用與智慧裝置客戶", "chain_position":"SoC/邊緣AI晶片設計", "market_share":"手機SoC全球前三"},
    "3034.TW": {"customers":"京東方、群創、友達、Samsung Display、LG Display、手機/IT/TV品牌供應鏈", "ai_customers":"AI PC、車用顯示、資料中心顯示間接受惠", "chain_position":"DDI/TDDI顯示驅動IC", "market_share":"全球DDI主要廠"},
    "2379.TW": {"customers":"PC/NB品牌、主機板廠、網通設備廠、車用乙太網路客戶", "ai_customers":"AI PC、AIoT、邊緣網通與車用乙太網路", "chain_position":"網通/音訊/邊緣IC", "market_share":"乙太網路IC主要供應商"},
    "5274.TWO": {"customers":"Dell、HPE、Supermicro、Lenovo、Quanta、Wiwynn、雲端資料中心供應鏈", "ai_customers":"Microsoft、AWS、Google、Meta、NVIDIA伺服器供應鏈", "chain_position":"伺服器BMC控制晶片", "market_share":"BMC全球龍頭"},
    "3661.TW": {"customers":"北美雲端客戶、AI ASIC客戶、Marvell/Broadcom供應鏈、CSP專案客戶", "ai_customers":"Google、AWS、Microsoft、Meta等CSP ASIC供應鏈", "chain_position":"AI ASIC設計服務", "market_share":"ASIC設計服務主要廠"},
    "3443.TW": {"customers":"台積電設計服務生態系、CSP ASIC客戶、HPC/AI專案客戶", "ai_customers":"AI ASIC與先進製程客戶", "chain_position":"ASIC/NRE設計服務", "market_share":"ASIC設計服務主要廠"},
    "3035.TW": {"customers":"車用、工控、通訊、ASIC/IP專案客戶", "ai_customers":"邊緣AI與客製化ASIC客戶", "chain_position":"ASIC/IP設計服務", "market_share":"ASIC/IP供應商"},
    "2382.TW": {"customers":"Apple、Google、Amazon AWS、Meta、Microsoft、NVIDIA伺服器供應鏈", "ai_customers":"NVIDIA、Google、AWS、Meta、Microsoft", "chain_position":"AI伺服器ODM", "market_share":"全球ODM龍頭群"},
    "3231.TW": {"customers":"NVIDIA供應鏈、Dell、HPE、Microsoft、Google、企業伺服器客戶", "ai_customers":"NVIDIA、Microsoft、Google、雲端資料中心客戶", "chain_position":"AI伺服器ODM/組裝", "market_share":"全球ODM主要廠"},
    "6669.TW": {"customers":"Microsoft、Meta、Amazon AWS、Google、雲端資料中心客戶", "ai_customers":"CSP雲端AI伺服器客戶", "chain_position":"雲端伺服器ODM", "market_share":"雲端伺服器主要供應商"},
    "2317.TW": {"customers":"Apple、NVIDIA伺服器供應鏈、Microsoft、Amazon、Google、EV與電子品牌", "ai_customers":"NVIDIA、Microsoft、AWS、Google、AI伺服器客戶", "chain_position":"EMS/AI伺服器組裝", "market_share":"全球EMS龍頭"},
    "2383.TW": {"customers":"NVIDIA供應鏈、廣達、緯穎、緯創、鴻海、伺服器PCB/CCL客戶", "ai_customers":"NVIDIA GB200/AI伺服器供應鏈、CSP伺服器客戶", "chain_position":"AI高速CCL材料", "market_share":"高階CCL主要供應商"},
    "6274.TWO": {"customers":"網通/伺服器PCB廠、AI伺服器材料供應鏈、台系板廠", "ai_customers":"AI伺服器高速材料客戶", "chain_position":"高速CCL材料", "market_share":"高速材料主要供應商"},
    "3037.TW": {"customers":"NVIDIA/AMD/Intel供應鏈、Apple、伺服器與載板客戶", "ai_customers":"AI GPU/CPU載板供應鏈", "chain_position":"ABF載板/高階PCB", "market_share":"ABF載板主要供應商"},
    "8046.TW": {"customers":"Intel/AMD/NVIDIA供應鏈、載板與封裝客戶", "ai_customers":"AI/HPC封裝載板供應鏈", "chain_position":"ABF/BT載板", "market_share":"載板主要供應商"},
    "2368.TW": {"customers":"伺服器ODM、雲端資料中心、網通與高速PCB客戶", "ai_customers":"AI伺服器高速PCB客戶", "chain_position":"AI伺服器PCB", "market_share":"伺服器PCB主要供應商"},
    "3017.TW": {"customers":"NVIDIA供應鏈、廣達、緯創、緯穎、伺服器ODM客戶", "ai_customers":"NVIDIA GB200/AI伺服器液冷供應鏈", "chain_position":"AI散熱模組/液冷", "market_share":"散熱主要供應商"},
    "3324.TWO": {"customers":"NVIDIA供應鏈、伺服器ODM、筆電/伺服器散熱客戶", "ai_customers":"AI伺服器液冷與高階散熱客戶", "chain_position":"AI散熱/液冷", "market_share":"散熱主要供應商"},
    "3653.TW": {"customers":"伺服器/半導體散熱客戶、AI供應鏈、連接器與導熱元件客戶", "ai_customers":"AI伺服器導熱/均熱元件客戶", "chain_position":"高階導熱元件", "market_share":"高階散熱材料廠"},
    "2059.TW": {"customers":"Dell、HPE、Supermicro、Quanta、Wiwynn、伺服器機櫃供應鏈", "ai_customers":"AI伺服器機櫃/滑軌供應鏈", "chain_position":"伺服器滑軌", "market_share":"全球伺服器滑軌龍頭"},
    "2308.TW": {"customers":"NVIDIA供應鏈、資料中心客戶、Apple、Tesla、工業自動化與電源客戶", "ai_customers":"AI資料中心電源、液冷、能源管理客戶", "chain_position":"資料中心電源/能源管理", "market_share":"電源管理全球領導廠"},
    "1519.TW": {"customers":"台電、電網工程、資料中心與重電客戶、海外電力設備客戶", "ai_customers":"AI資料中心電力基礎建設間接受惠", "chain_position":"變壓器/電網設備", "market_share":"台灣重電主要廠"},
    "1513.TW": {"customers":"台電、公共工程、電網/充電樁/重電設備客戶", "ai_customers":"資料中心電網升級間接受惠", "chain_position":"重電/電網/充電樁", "market_share":"台灣重電主要廠"},
    "2327.TW": {"customers":"車用、工控、消費電子、通路與EMS客戶", "ai_customers":"AI伺服器電源與高階MLCC間接受惠", "chain_position":"MLCC/晶片電阻", "market_share":"全球被動元件龍頭群"},
    "2408.TW": {"customers":"記憶體模組廠、PC/伺服器/消費電子客戶", "ai_customers":"AI伺服器記憶體需求間接受惠", "chain_position":"DRAM製造", "market_share":"台灣DRAM龍頭"},
    "3260.TWO": {"customers":"通路、電競品牌、工控與記憶體模組客戶", "ai_customers":"AI PC與邊緣裝置記憶體需求間接受惠", "chain_position":"記憶體模組/通路", "market_share":"台灣記憶體模組主要廠"},
    "8299.TWO": {"customers":"NAND品牌、SSD模組廠、工控與儲存客戶", "ai_customers":"AI PC/資料中心SSD控制IC間接受惠", "chain_position":"SSD控制IC/儲存方案", "market_share":"SSD控制IC全球龍頭群"},
    "4979.TWO": {"customers":"資料中心光通訊客戶、光模組供應鏈、北美雲端客戶供應鏈", "ai_customers":"AI資料中心光通訊/CPO供應鏈", "chain_position":"光收發模組", "market_share":"光通訊供應商"},
    "3363.TWO": {"customers":"光通訊設備廠、資料中心光元件客戶", "ai_customers":"AI資料中心光通訊供應鏈", "chain_position":"光通訊元件", "market_share":"光通訊元件供應商"},
    "6215.TWO": {"customers":"電子製造、半導體、自動化設備、智慧工廠與機器人整合客戶", "ai_customers":"AI Robot與智慧製造客戶", "chain_position":"自動化/機器人整合", "market_share":"自動化設備供應商"},
    "2049.TW": {"customers":"工具機、自動化設備、半導體設備、工業機器人客戶", "ai_customers":"AI Robot/自動化設備供應鏈", "chain_position":"線性滑軌/傳動元件", "market_share":"全球傳動元件主要廠"},
}

V235_EXTRA_STOCKS = {
    "2881.TW":{"name":"富邦金","industry":"金融","sub":"金控/壽險/銀行","rank":"大型金控","power":"★★★★☆","position":"台灣大型金控，壽險、銀行、證券完整布局","peers":"國泰金、中信金、元大金","moat":"高：金融通路、資產規模、品牌","risk":"利率、匯率、投資收益波動","fair_mult":1.04},
    "2882.TW":{"name":"國泰金","industry":"金融","sub":"金控/壽險/銀行","rank":"大型金控","power":"★★★★☆","position":"台灣大型壽險與銀行金控","peers":"富邦金、中信金、南山人壽","moat":"高：壽險資產、銀行通路、品牌","risk":"利率、匯率、金融市場波動","fair_mult":1.04},
    "2891.TW":{"name":"中信金","industry":"金融","sub":"金控/銀行","rank":"大型金控","power":"★★★★☆","position":"銀行、信用卡、財管與金控整合","peers":"富邦金、國泰金、玉山金","moat":"中高：銀行通路、財管、信用卡","risk":"利差、信用風險、海外市場","fair_mult":1.04},
    "2886.TW":{"name":"兆豐金","industry":"金融","sub":"公股銀行金控","rank":"公股金控","power":"★★★☆☆","position":"外匯與企業金融優勢公股金控","peers":"第一金、合庫金、華南金","moat":"中高：公股資源、外匯業務","risk":"利差、景氣循環","fair_mult":1.03},
    "5871.TW":{"name":"中租-KY","industry":"金融","sub":"租賃/融資","rank":"租賃龍頭","power":"★★★★☆","position":"兩岸及海外租賃、融資與分期服務供應商","peers":"裕融、和潤企業、銀行租賃部門","moat":"中高：通路、授信模型、海外布局","risk":"信用風險、利率、景氣循環","fair_mult":1.04},
    "2603.TW":{"name":"長榮","industry":"航運","sub":"貨櫃航運","rank":"全球貨櫃航運主要公司","power":"★★★★☆","position":"全球貨櫃航運供應商","peers":"陽明、萬海、Maersk、MSC、CMA CGM","moat":"中：船隊規模、航線與聯盟","risk":"運價循環、油價、地緣政治","fair_mult":1.05},
    "2609.TW":{"name":"陽明","industry":"航運","sub":"貨櫃航運","rank":"貨櫃航運主要公司","power":"★★★☆☆","position":"台灣貨櫃航運主要供應商","peers":"長榮、萬海、Maersk、Hapag-Lloyd","moat":"中：航線與船隊","risk":"運價循環、油價、供需波動","fair_mult":1.03},
    "2615.TW":{"name":"萬海","industry":"航運","sub":"近洋/貨櫃航運","rank":"區域航運主要公司","power":"★★★☆☆","position":"亞洲近洋與貨櫃航運供應商","peers":"長榮、陽明、區域航商","moat":"中：近洋航線與客戶基礎","risk":"運價循環、船隊供給","fair_mult":1.03},
    "2618.TW":{"name":"長榮航","industry":"航運/航空","sub":"航空客運/貨運","rank":"台灣航空主要公司","power":"★★★☆☆","position":"航空客運與貨運服務供應商","peers":"華航、星宇航空、亞洲航空公司","moat":"中：航線、品牌、貨運能力","risk":"油價、匯率、景氣與旅遊需求","fair_mult":1.03},
    "2002.TW":{"name":"中鋼","industry":"鋼鐵","sub":"一貫作業鋼廠","rank":"台灣鋼鐵龍頭","power":"★★★★☆","position":"台灣最大一貫作業鋼鐵公司","peers":"日本製鐵、POSCO、寶鋼、燁輝","moat":"中高：規模、客戶、上游整合","risk":"鋼價循環、原料成本、中國供給","fair_mult":1.02},
    "2027.TW":{"name":"大成鋼","industry":"鋼鐵","sub":"不鏽鋼/通路","rank":"不鏽鋼通路主要廠","power":"★★★☆☆","position":"不鏽鋼與工業金屬通路供應商","peers":"允強、彰源、國際鋼鐵通路商","moat":"中：通路與庫存管理","risk":"金屬價格、需求循環","fair_mult":1.03},
    "1301.TW":{"name":"台塑","industry":"塑化","sub":"PVC/塑膠原料","rank":"台灣塑化龍頭群","power":"★★★★☆","position":"PVC、塑膠原料與化工產品供應商","peers":"台化、南亞、國際石化廠","moat":"中高：垂直整合與規模","risk":"油價、景氣循環、利差","fair_mult":1.02},
    "1303.TW":{"name":"南亞","industry":"塑化/電子材料","sub":"塑化/銅箔基板/聚酯","rank":"台灣塑化與材料龍頭群","power":"★★★★☆","position":"塑化、電子材料與聚酯產品供應商","peers":"台塑、台化、長春、國際材料廠","moat":"中高：集團整合與材料能力","risk":"景氣循環、原料價格、電子材料需求","fair_mult":1.03},
    "1326.TW":{"name":"台化","industry":"塑化","sub":"芳香烴/化纖/塑化","rank":"台灣塑化龍頭群","power":"★★★☆☆","position":"芳香烴、化纖與塑化產品供應商","peers":"台塑、南亞、國際石化廠","moat":"中高：規模與垂直整合","risk":"油價、利差、景氣循環","fair_mult":1.02},
    "6505.TW":{"name":"台塑化","industry":"塑化/能源","sub":"煉油/石化","rank":"煉油石化主要廠","power":"★★★★☆","position":"煉油、石化原料與油品供應商","peers":"中油、國際煉油與石化公司","moat":"中高：煉化規模與集團整合","risk":"油價、煉油利差、景氣循環","fair_mult":1.02},
    "2412.TW":{"name":"中華電","industry":"電信","sub":"行動/固網/IDC","rank":"台灣電信龍頭","power":"★★★★★","position":"台灣電信、固網、IDC與雲端服務龍頭","peers":"台灣大、遠傳、亞太電信","moat":"高：網路資產、用戶規模、現金流","risk":"價格競爭、資本支出、監管","fair_mult":1.04},
    "3045.TW":{"name":"台灣大","industry":"電信","sub":"行動/寬頻/電商","rank":"台灣電信主要公司","power":"★★★★☆","position":"行動通訊、寬頻與電商整合服務供應商","peers":"中華電、遠傳","moat":"中高：用戶基礎與通路整合","risk":"競爭、資本支出、整合成本","fair_mult":1.03},
    "4904.TW":{"name":"遠傳","industry":"電信","sub":"行動/企業ICT/IDC","rank":"台灣電信主要公司","power":"★★★★☆","position":"行動通訊、企業ICT與資料中心服務供應商","peers":"中華電、台灣大","moat":"中高：企業ICT、用戶與網路","risk":"價格競爭、資本支出","fair_mult":1.03},
    "2912.TW":{"name":"統一超","industry":"零售通路","sub":"便利商店/生活服務","rank":"台灣零售通路龍頭","power":"★★★★★","position":"台灣便利商店與生活服務通路龍頭","peers":"全家、萊爾富、OK Mart","moat":"高：門市密度、物流、品牌與會員資料","risk":"人事成本、租金、消費景氣","fair_mult":1.05},
    "1216.TW":{"name":"統一","industry":"食品/消費","sub":"食品飲料/通路投資","rank":"食品與通路龍頭","power":"★★★★★","position":"食品、飲料、通路與消費品牌集團","peers":"味全、卜蜂、國際食品公司","moat":"高：品牌、通路、產品組合","risk":"原物料、匯率、消費景氣","fair_mult":1.04},
    "1101.TW":{"name":"台泥","industry":"水泥/建材","sub":"水泥/儲能/循環經濟","rank":"台灣水泥龍頭","power":"★★★★☆","position":"水泥、建材、儲能與低碳轉型企業","peers":"亞泥、中國建材、海螺水泥","moat":"中高：礦權、產能、通路","risk":"需求循環、碳成本、中國市場","fair_mult":1.03},
    "1102.TW":{"name":"亞泥","industry":"水泥/建材","sub":"水泥/建材","rank":"台灣水泥主要公司","power":"★★★☆☆","position":"台灣水泥與建材主要供應商","peers":"台泥、國際水泥廠","moat":"中：產能、通路、礦權","risk":"需求循環、碳成本、區域市場","fair_mult":1.02},
    "2207.TW":{"name":"和泰車","industry":"汽車/通路","sub":"汽車代理/售服","rank":"台灣車市龍頭","power":"★★★★★","position":"Toyota/Lexus台灣代理與汽車服務龍頭","peers":"裕隆、汎德永業、國際車商代理","moat":"高：品牌代理、通路、售後服務","risk":"車市景氣、匯率、品牌供給","fair_mult":1.05},
    "2201.TW":{"name":"裕隆","industry":"汽車/電動車","sub":"汽車製造/投資","rank":"台灣汽車主要集團","power":"★★★☆☆","position":"汽車製造、品牌與電動車轉型集團","peers":"和泰車、中華車、國際車商","moat":"中：汽車製造與集團資源","risk":"轉型、競爭、景氣循環","fair_mult":1.03},
    "9910.TW":{"name":"豐泰","industry":"製鞋/紡織","sub":"運動鞋代工","rank":"全球運動鞋代工主要廠","power":"★★★★☆","position":"Nike等國際品牌運動鞋供應鏈","peers":"寶成、鈺齊-KY、申洲國際","moat":"中高：客戶認證、量產與管理能力","risk":"客戶集中、工資、匯率","fair_mult":1.04},
    "9904.TW":{"name":"寶成","industry":"製鞋/通路","sub":"運動鞋代工/通路","rank":"全球鞋業主要集團","power":"★★★★☆","position":"運動鞋代工與通路集團","peers":"豐泰、鈺齊-KY、申洲國際","moat":"中高：規模、客戶與通路","risk":"客戶訂單、工資、匯率","fair_mult":1.03},
    "1476.TW":{"name":"儒鴻","industry":"紡織","sub":"機能布/成衣","rank":"機能布與成衣主要廠","power":"★★★★☆","position":"國際運動品牌機能布與成衣供應商","peers":"聚陽、申洲國際、Makalot","moat":"中高：研發、客戶認證、彈性生產","risk":"品牌庫存、匯率、工資","fair_mult":1.04},
    "1477.TW":{"name":"聚陽","industry":"紡織","sub":"成衣代工","rank":"成衣代工主要廠","power":"★★★★☆","position":"國際品牌成衣代工供應商","peers":"儒鴻、申洲國際、Makalot","moat":"中高：客戶組合、供應鏈管理","risk":"品牌庫存、工資、匯率","fair_mult":1.04},
}

V235_GENERIC_CUSTOMERS_BY_INDUSTRY = {
    "金融":"企業金融、個人金融、財管、保險與投資客戶",
    "航運":"國際貿易、貨主、物流與貨櫃運輸客戶",
    "航運/航空":"商務/旅遊旅客、航空貨運與物流客戶",
    "鋼鐵":"營建、汽車、機械、家電與工業製造客戶",
    "塑化":"塑膠加工、包材、化纖、工業材料與化工客戶",
    "塑化/電子材料":"電子材料、塑化、包材與工業材料客戶",
    "塑化/能源":"油品、石化原料與工業能源客戶",
    "電信":"個人行動用戶、企業ICT、IDC、雲端與寬頻客戶",
    "零售通路":"消費者、會員、生活服務與品牌供應商",
    "食品/消費":"消費者、通路、餐飲與食品品牌客戶",
    "水泥/建材":"營建工程、公共工程、建材通路與預拌混凝土客戶",
    "汽車/通路":"汽車消費者、車隊、維修保養與金融服務客戶",
    "汽車/電動車":"汽車品牌、零組件、電動車與集團通路客戶",
    "製鞋/紡織":"Nike、Adidas、國際運動與戶外品牌供應鏈",
    "製鞋/通路":"國際運動品牌、零售通路與鞋類供應鏈",
    "紡織":"國際運動品牌、機能服飾、戶外品牌與成衣客戶",
}

try:
    STOCK_DB.update(V235_EXTRA_STOCKS)
    for _sym, _upd in V235_CUSTOMER_PATCH.items():
        if _sym in STOCK_DB:
            STOCK_DB[_sym].update(_upd)
    for _sym, _v in STOCK_DB.items():
        ind = _v.get("industry", "")
        if not _v.get("customers") and not _v.get("main_customers"):
            _v["customers"] = V235_GENERIC_CUSTOMERS_BY_INDUSTRY.get(ind, _v.get("customers", "待補"))
        _v.setdefault("valuation_method", "即時現價 × 產業/競爭力乘數；輸入個股後自動產生安全邊際價、合理價、潛在價")
        _v.setdefault("valuation_status", "已可計算")
except Exception:
    pass

try:
    ALIASES.clear()
    for _sym, _v in STOCK_DB.items():
        ALIASES[_sym.upper()] = _sym
        ALIASES[_sym.split(".")[0]] = _sym
        ALIASES[_v.get("name", _sym)] = _sym
        ALIASES[_v.get("name", _sym).upper()] = _sym
    OTC_CODES = {s.split('.')[0] for s in STOCK_DB if s.endswith('.TWO')}
except Exception:
    pass

def v235_get_mult(sym):
    try:
        return float(v233_fair_multiplier(sym))
    except Exception:
        try:
            return float(STOCK_DB.get(sym, {}).get("fair_mult", 1.0))
        except Exception:
            return 1.0

def v235_valuation_range(symbol):
    sym = v230_symbol(symbol)
    try:
        px = v233_get_live_price(sym)
    except Exception:
        try:
            px = live_price(sym)
        except Exception:
            px = float("nan")
    mult = v235_get_mult(sym)
    if pd.notna(px) and float(px) > 0:
        fair = float(px) * mult
        low = float(px) * max(mult * 0.88, 0.70)
        high = float(px) * max(mult * 1.12, 1.05)
        return {"symbol": sym, "price": float(px), "low": low, "fair": fair, "high": high, "mult": mult, "status":"已計算"}
    return {"symbol": sym, "price": float("nan"), "low": float("nan"), "fair": float("nan"), "high": float("nan"), "mult": mult, "status":"等待現價"}

_v235_prev_decision = v230_decision

def v230_decision(symbol):
    d = _v235_prev_decision(symbol)
    sym = d.get("symbol", v230_symbol(symbol))
    vr = v235_valuation_range(sym)
    try:
        if pd.notna(vr["price"]):
            d["price"] = vr["price"]
            d["cons"] = vr["low"]
            d["fair"] = vr["fair"]
            d["opt"] = vr["high"]
            d["ret"] = (vr["fair"] - vr["price"]) / vr["price"] * 100
    except Exception:
        pass
    info = STOCK_DB.get(sym, {})
    d["customers"] = info.get("customers", info.get("main_customers", "待補"))
    d["ai_customers"] = info.get("ai_customers", "待補")
    d["valuation_method"] = info.get("valuation_method", "即時現價 × 產業/競爭力乘數")
    return d

_v235_prev_rows_df = v230_rows_df

def v230_rows_df():
    df = _v235_prev_rows_df()
    if df is None or df.empty:
        return df
    # 補估值欄位：不強制抓 192+ 檔即時價格，避免首頁載入過慢；個股查詢時會即時計算完整價格區間。
    if "估值狀態" not in df.columns:
        df["估值狀態"] = "已可計算"
    if "估值模型" not in df.columns:
        df["估值模型"] = "現價×產業乘數"
    if "AI客戶" not in df.columns:
        df["AI客戶"] = df["代碼"].map(lambda s: STOCK_DB.get(s, {}).get("ai_customers", "待補"))
    if "主要客戶" in df.columns:
        df["主要客戶"] = df.apply(lambda r: STOCK_DB.get(r["代碼"], {}).get("customers", r.get("主要客戶", "待補")), axis=1)
    return df

def v224_rows_df(): return v230_rows_df()
def v225_rows_df(): return v230_rows_df()
def v226_rows_df(): return v230_rows_df()
def v227_rows_df(): return v230_rows_df()

_v235_prev_price_block = v230_price_block

def v230_price_block(symbol):
    d = v230_decision(symbol); sym = d.get("symbol", symbol)
    st.caption(f"資料更新時間：{d.get('updated','N/A')}｜現價來源：{d.get('source','Yahoo Finance')}｜估值模型：{d.get('valuation_method','即時現價 × 產業/競爭力乘數')}。")
    st.markdown(f"## {d.get('name', sym)}（{sym}）")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("投資建議", d.get("action","觀察"))
    c2.metric("現價", v230_fmt(d.get("price", float("nan"))))
    c3.metric("綜合合理價", v230_fmt(d.get("fair", float("nan"))))
    try: ret_txt=f"{float(d.get('ret',0)):.1f}%"
    except Exception: ret_txt="N/A"
    c4.metric("預期報酬", ret_txt)
    p1,p2,p3=st.columns(3)
    p1.metric("安全邊際價", v230_fmt(d.get("cons", float("nan"))))
    p2.metric("合理價值", v230_fmt(d.get("fair", float("nan"))))
    p3.metric("潛在價值", v230_fmt(d.get("opt", float("nan"))))
    st.dataframe(pd.DataFrame([{
        "現價": v230_fmt(d.get("price", float("nan"))),
        "安全邊際價": v230_fmt(d.get("cons", float("nan"))),
        "合理價值": v230_fmt(d.get("fair", float("nan"))),
        "潛在價值": v230_fmt(d.get("opt", float("nan"))),
        "估值模型": d.get("valuation_method", "即時現價 × 產業/競爭力乘數")
    }]), use_container_width=True, hide_index=True)
    df=v230_rows_df(); row=df[df["代碼"]==sym] if not df.empty and "代碼" in df.columns else pd.DataFrame()
    with st.expander("展開更多研究資料", expanded=True):
        if not row.empty:
            r=row.iloc[0].to_dict()
            st.markdown("### 公司基本資料")
            st.markdown(f'<div class="v230-card"><div class="v230-card-title">{r.get("公司","")}｜{r.get("代碼","")}</div><div class="v230-small-muted">主產業：{r.get("產業","")}　｜　子產業：{r.get("子產業","")}　｜　產業鏈位置：{r.get("產業鏈位置","待補")}</div><div style="margin-top:10px;">{v230_tag_html(r.get("主題標籤",""))}</div></div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame([{
                "全球排名":r.get("全球排名","待補"),
                "全球市占率":r.get("全球市占率","待補"),
                "產業地位":r.get("產業地位","待補"),
                "主要客戶":r.get("主要客戶","待補"),
                "AI客戶":r.get("AI客戶","待補"),
                "主要競爭者":r.get("主要競爭者","待補"),
                "護城河":r.get("護城河","待補"),
                "主要風險":r.get("主要風險","待補")
            }]), use_container_width=True, hide_index=True)
        else:
            st.info("此個股仍在資料庫補齊中，但已可使用即時現價產生估值區間。")

# ===== V235.0 FULL VALUATION RANGE + CUSTOMER EXPANSION END =====


# ===== V236.0 PRICE DATABASE EXPANSION START =====
# 目標：先提高「可搜尋＋可估值區間」覆蓋率，再逐步補深度研究。
# 說明：新增股票皆支援即時現價 × 產業/競爭力乘數，個股頁會自動產生安全邊際價、合理價與潛在價值。
APP_VERSION = "V236.0 Price Database Expansion"

V236_EXTRA_STOCKS = {'2886.TW': {'name': '兆豐金', 'industry': '金融', 'sub': '公股金控/銀行', 'rank': '大型公股金控', 'power': '★★★★☆', 'position': '公股銀行型金控，利差、財管與海外分行為主要收益來源', 'peers': '第一金、合庫金、華南金、玉山金', 'moat': '中高：公股通路、企業金融與外匯業務', 'risk': '利差收斂、信用風險、政策因素', 'fair_mult': 1.02, 'customers': '企業金融客戶、個人金融客戶、外匯與財管客戶', 'ai_customers': '無直接AI客戶；受惠金融數位化', 'theme_text': '金融、銀行、股息、防禦型', 'chain_position': '金融服務', 'market_share': '台灣大型公股金控'}, '2887.TW': {'name': '台新金', 'industry': '金融', 'sub': '金控/銀行', 'rank': '民營金控', 'power': '★★★☆☆', 'position': '銀行、證券與消費金融金控', 'peers': '玉山金、中信金、永豐金、國泰金', 'moat': '中：消費金融、財管與信用卡業務', 'risk': '信用風險、利差、併購整合', 'fair_mult': 1.02, 'customers': '個人金融、信用卡、企業金融與財管客戶', 'ai_customers': '無直接AI客戶；受惠金融科技', 'theme_text': '金融、銀行、消費金融', 'chain_position': '金融服務', 'market_share': '台灣民營金控'}, '2890.TW': {'name': '永豐金', 'industry': '金融', 'sub': '金控/銀行/證券', 'rank': '民營金控', 'power': '★★★☆☆', 'position': '銀行與證券並重的金融控股公司', 'peers': '台新金、玉山金、元大金、中信金', 'moat': '中：銀行、證券與數位金融通路', 'risk': '利差、信用風險、股市成交量', 'fair_mult': 1.02, 'customers': '銀行、證券、財管與企業金融客戶', 'ai_customers': '無直接AI客戶；受惠金融科技', 'theme_text': '金融、銀行、證券', 'chain_position': '金融服務', 'market_share': '台灣民營金控'}, '2897.TW': {'name': '王道銀行', 'industry': '金融', 'sub': '銀行', 'rank': '數位銀行/商業銀行', 'power': '★★☆☆☆', 'position': '銀行與企業金融服務供應商', 'peers': '玉山金、台新金、永豐金', 'moat': '低中：銀行牌照與數位通路', 'risk': '規模較小、利差、信用風險', 'fair_mult': 1.0, 'customers': '個人金融、企業金融與數位銀行客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '金融、銀行、數位金融', 'chain_position': '金融服務', 'market_share': '台灣商業銀行'}, '2801.TW': {'name': '彰銀', 'industry': '金融', 'sub': '銀行', 'rank': '老牌銀行', 'power': '★★★☆☆', 'position': '老牌商業銀行與公股金融機構', 'peers': '第一金、華南金、合庫金', 'moat': '中：分行通路與企業金融客戶', 'risk': '利差、信用風險、成長性', 'fair_mult': 1.01, 'customers': '企業金融、個人金融與財管客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '金融、銀行、股息', 'chain_position': '金融服務', 'market_share': '台灣主要銀行'}, '2812.TW': {'name': '台中銀', 'industry': '金融', 'sub': '區域銀行', 'rank': '區域銀行', 'power': '★★★☆☆', 'position': '中部地區銀行與中小企業金融服務商', 'peers': '京城銀、彰銀、王道銀行', 'moat': '中：區域客戶與中小企業金融', 'risk': '區域景氣、利差、信用風險', 'fair_mult': 1.01, 'customers': '中小企業、個人金融與區域財管客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '金融、區域銀行、股息', 'chain_position': '金融服務', 'market_share': '區域銀行'}, '2834.TW': {'name': '臺企銀', 'industry': '金融', 'sub': '中小企業銀行', 'rank': '中小企業金融', 'power': '★★★☆☆', 'position': '中小企業金融與政策性金融服務銀行', 'peers': '彰銀、台中銀、京城銀', 'moat': '中：中小企業客戶基礎', 'risk': '中小企業信用風險、利差', 'fair_mult': 1.01, 'customers': '中小企業、個人金融與政策金融客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '金融、銀行、中小企業', 'chain_position': '金融服務', 'market_share': '台灣中小企業金融主要銀行'}, '2845.TW': {'name': '遠東銀', 'industry': '金融', 'sub': '銀行', 'rank': '民營銀行', 'power': '★★★☆☆', 'position': '民營銀行與集團金融服務平台', 'peers': '台新金、永豐金、王道銀行', 'moat': '中：集團資源、消金與企業金融', 'risk': '利差、信用風險、規模', 'fair_mult': 1.01, 'customers': '個人金融、企業金融與財管客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '金融、銀行', 'chain_position': '金融服務', 'market_share': '台灣民營銀行'}, '6005.TW': {'name': '群益證', 'industry': '金融', 'sub': '證券', 'rank': '證券商', 'power': '★★★☆☆', 'position': '證券經紀、自營與財富管理業務', 'peers': '元大金、凱基金、統一證', 'moat': '中：證券通路與財管業務', 'risk': '股市成交量波動、自營部位', 'fair_mult': 1.02, 'customers': '證券交易、財管與法人客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '金融、證券、成交量', 'chain_position': '金融服務', 'market_share': '台灣證券商'}, '2855.TW': {'name': '統一證', 'industry': '金融', 'sub': '證券', 'rank': '證券商', 'power': '★★★☆☆', 'position': '證券經紀、自營與承銷業務', 'peers': '群益證、元大證、凱基金', 'moat': '中：證券通路與集團資源', 'risk': '股市成交量、自營波動', 'fair_mult': 1.02, 'customers': '證券交易、承銷與財管客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '金融、證券、股市成交量', 'chain_position': '金融服務', 'market_share': '台灣證券商'}, '1402.TW': {'name': '遠東新', 'industry': '紡織/材料', 'sub': '聚酯/紡織/投資控股', 'rank': '大型紡織與材料集團', 'power': '★★★★☆', 'position': '聚酯、紡織、通路與投資控股集團', 'peers': '新纖、南紡、國際聚酯廠', 'moat': '中高：垂直整合、資產與集團資源', 'risk': '原料價格、景氣循環、匯率', 'fair_mult': 1.02, 'customers': '國際服飾品牌、飲料包材、工業材料與集團通路客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '紡織、聚酯、資產、防禦型', 'chain_position': '上中游材料/紡織', 'market_share': '台灣大型聚酯紡織集團'}, '1476.TW': {'name': '儒鴻', 'industry': '紡織', 'sub': '機能服飾/成衣', 'rank': '高階機能服飾供應商', 'power': '★★★★★', 'position': '全球運動與機能服飾品牌代工供應商', 'peers': '聚陽、申洲國際、Makalot同業', 'moat': '高：機能布料、成衣整合、品牌客戶認證', 'risk': '品牌庫存、匯率、人力成本', 'fair_mult': 1.06, 'customers': 'Nike、Lululemon、Under Armour、Adidas 等國際運動服飾品牌', 'ai_customers': '無直接AI客戶', 'theme_text': '紡織、運動服飾、品牌供應鏈', 'chain_position': '中下游成衣供應鏈', 'market_share': '高階機能服飾主要供應商'}, '1477.TW': {'name': '聚陽', 'industry': '紡織', 'sub': '成衣代工', 'rank': '成衣代工主要廠', 'power': '★★★★☆', 'position': '全球服飾品牌成衣代工供應商', 'peers': '儒鴻、申洲國際、成衣代工同業', 'moat': '中高：快速反應、客戶組合與全球產能', 'risk': '品牌庫存、人工成本、匯率', 'fair_mult': 1.05, 'customers': '美系與日系服飾品牌、大型零售通路、運動與休閒服飾客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '紡織、成衣、品牌供應鏈', 'chain_position': '中下游成衣代工', 'market_share': '台灣成衣代工龍頭之一'}, '1301.TW': {'name': '台塑', 'industry': '塑化', 'sub': '石化原料/PVC', 'rank': '台灣石化龍頭', 'power': '★★★★☆', 'position': '石化原料、塑膠與PVC供應商', 'peers': '南亞、台化、中石化、國際石化廠', 'moat': '中高：垂直整合、規模與集團資源', 'risk': '油價、石化循環、中國供需', 'fair_mult': 1.0, 'customers': '塑膠加工、建材、包材、工業材料與下游製造客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '塑化、原物料、景氣循環', 'chain_position': '上游石化材料', 'market_share': '台灣塑化龍頭'}, '1303.TW': {'name': '南亞', 'industry': '塑化/電子材料', 'sub': '塑膠/銅箔基板/電子材料', 'rank': '大型塑化與材料集團', 'power': '★★★★☆', 'position': '塑膠、電子材料與化工材料供應商', 'peers': '台塑、台化、長春、國際材料廠', 'moat': '中高：垂直整合、材料技術、集團資源', 'risk': '石化循環、電子材料景氣、匯率', 'fair_mult': 1.01, 'customers': '電子材料、塑膠加工、PCB/CCL與工業材料客戶', 'ai_customers': 'AI伺服器材料供應鏈間接受惠', 'theme_text': '塑化、電子材料、PCB材料', 'chain_position': '上游材料', 'market_share': '台灣大型材料集團'}, '1326.TW': {'name': '台化', 'industry': '塑化', 'sub': '芳香烴/纖維/塑化', 'rank': '大型石化與纖維集團', 'power': '★★★★☆', 'position': '石化、芳香烴、纖維與塑膠材料供應商', 'peers': '台塑、南亞、國際石化廠', 'moat': '中高：規模、垂直整合與集團資源', 'risk': '油價、石化景氣、中國產能', 'fair_mult': 1.0, 'customers': '紡織、塑膠加工、化工與工業材料客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '塑化、纖維、原物料', 'chain_position': '上游石化材料', 'market_share': '台灣石化主要廠'}, '1314.TW': {'name': '中石化', 'industry': '塑化', 'sub': 'CPL/尼龍原料', 'rank': '石化原料供應商', 'power': '★★★☆☆', 'position': '尼龍原料與石化產品供應商', 'peers': '台化、國際CPL供應商', 'moat': '中：既有產能與石化產品線', 'risk': '石化循環、價格競爭、原料成本', 'fair_mult': 0.98, 'customers': '尼龍、化纖、塑膠與化工客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '塑化、尼龍原料、景氣循環', 'chain_position': '上游石化材料', 'market_share': '台灣石化原料供應商'}, '1707.TW': {'name': '葡萄王', 'industry': '食品/生技', 'sub': '保健食品', 'rank': '保健食品品牌', 'power': '★★★☆☆', 'position': '保健食品、益生菌與生技產品供應商', 'peers': '大江、生技保健品公司', 'moat': '中：品牌、通路與研發配方', 'risk': '消費景氣、法規、通路競爭', 'fair_mult': 1.03, 'customers': '保健食品消費者、藥妝通路、直銷與電商客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '食品、生技、保健食品', 'chain_position': '消費品牌/保健品', 'market_share': '台灣保健食品品牌'}, '1702.TW': {'name': '南僑', 'industry': '食品', 'sub': '油脂/冷凍麵食', 'rank': '食品品牌與代工', 'power': '★★★☆☆', 'position': '油脂、冷凍麵食與餐飲通路供應商', 'peers': '統一、大成、食品同業', 'moat': '中：食品品牌、通路與產品線', 'risk': '原物料、消費景氣、匯率', 'fair_mult': 1.02, 'customers': '餐飲、食品加工、零售通路與消費者', 'ai_customers': '無直接AI客戶', 'theme_text': '食品、餐飲、民生消費', 'chain_position': '食品製造/通路', 'market_share': '台灣食品主要廠'}, '1229.TW': {'name': '聯華', 'industry': '食品/投資', 'sub': '麵粉/食品/投資', 'rank': '食品原料供應商', 'power': '★★★☆☆', 'position': '麵粉、食品原料與轉投資公司', 'peers': '大成、統一、食品原料同業', 'moat': '中：食品原料通路與投資資產', 'risk': '原料價格、轉投資波動', 'fair_mult': 1.02, 'customers': '食品加工、烘焙、餐飲與通路客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '食品、原料、投資控股', 'chain_position': '食品原料', 'market_share': '台灣麵粉原料供應商'}, '1231.TW': {'name': '聯華食', 'industry': '食品', 'sub': '零食/鮮食', 'rank': '食品品牌商', 'power': '★★★☆☆', 'position': '休閒食品、鮮食與零售通路供應商', 'peers': '統一、旺旺、食品品牌同業', 'moat': '中：品牌、通路與鮮食供應能力', 'risk': '原物料、人力成本、消費需求', 'fair_mult': 1.03, 'customers': '便利商店、量販、超市與消費者', 'ai_customers': '無直接AI客戶', 'theme_text': '食品、零食、鮮食、通路', 'chain_position': '食品製造/通路', 'market_share': '台灣食品品牌'}, '1232.TW': {'name': '大統益', 'industry': '食品', 'sub': '油脂/飼料原料', 'rank': '油脂供應商', 'power': '★★★☆☆', 'position': '食用油脂與飼料原料供應商', 'peers': '南僑、泰山、食品油脂同業', 'moat': '中：產能、通路與原料採購', 'risk': '黃豆價格、匯率、油脂價差', 'fair_mult': 1.02, 'customers': '食品加工、餐飲、飼料與零售通路客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '食品、油脂、原物料', 'chain_position': '食品原料', 'market_share': '台灣油脂供應商'}, '2105.TW': {'name': '正新', 'industry': '橡膠/輪胎', 'sub': '輪胎', 'rank': '全球輪胎主要廠', 'power': '★★★★☆', 'position': '汽車、機車與自行車輪胎供應商', 'peers': '建大、Bridgestone、Michelin、Goodyear', 'moat': '中高：品牌、通路與產能規模', 'risk': '原料價格、車市需求、匯率', 'fair_mult': 1.02, 'customers': '汽車售後市場、機車/自行車、車廠與通路客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '輪胎、汽車、消費耐久財', 'chain_position': '汽車零組件/售後市場', 'market_share': '台灣輪胎龍頭'}, '2106.TW': {'name': '建大', 'industry': '橡膠/輪胎', 'sub': '輪胎', 'rank': '輪胎主要廠', 'power': '★★★☆☆', 'position': '汽車、機車、自行車與工業輪胎供應商', 'peers': '正新、國際輪胎廠', 'moat': '中：品牌與產能', 'risk': '原料價格、需求循環、競爭', 'fair_mult': 1.01, 'customers': '輪胎通路、車廠、機車/自行車與工業客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '輪胎、汽車零組件', 'chain_position': '汽車零組件/售後市場', 'market_share': '台灣輪胎主要廠'}, '2201.TW': {'name': '裕隆', 'industry': '汽車', 'sub': '汽車製造/品牌代理', 'rank': '汽車集團', 'power': '★★★☆☆', 'position': '汽車製造、品牌代理與電動車布局公司', 'peers': '和泰車、中華車、國際車廠', 'moat': '中：品牌代理、通路與集團資源', 'risk': '車市需求、電動車競爭、轉投資', 'fair_mult': 1.01, 'customers': '汽車消費者、商用車與經銷通路', 'ai_customers': '無直接AI客戶；受惠車用電子趨勢', 'theme_text': '汽車、電動車、品牌代理', 'chain_position': '下游整車/通路', 'market_share': '台灣汽車集團'}, '2207.TW': {'name': '和泰車', 'industry': '汽車', 'sub': '汽車代理/通路', 'rank': '台灣汽車通路龍頭', 'power': '★★★★★', 'position': 'Toyota/Lexus台灣代理與汽車金融服務', 'peers': '裕隆、中華車、汎德永業', 'moat': '高：品牌代理、通路、售後服務與市占', 'risk': '車市需求、匯率、原廠供給', 'fair_mult': 1.04, 'customers': 'Toyota/Lexus消費者、企業車隊、汽車金融客戶', 'ai_customers': '無直接AI客戶；受惠智慧車趨勢', 'theme_text': '汽車、品牌代理、消費', 'chain_position': '下游汽車通路', 'market_share': '台灣汽車銷售龍頭'}, '2227.TW': {'name': '裕日車', 'industry': '汽車', 'sub': '汽車代理', 'rank': '汽車代理商', 'power': '★★★☆☆', 'position': 'Nissan/Infiniti台灣汽車代理與銷售', 'peers': '和泰車、裕隆、中華車', 'moat': '中：品牌代理與經銷通路', 'risk': '車市需求、匯率、品牌競爭', 'fair_mult': 1.02, 'customers': 'Nissan車主、企業車隊與經銷通路', 'ai_customers': '無直接AI客戶', 'theme_text': '汽車、品牌代理', 'chain_position': '下游汽車通路', 'market_share': '台灣汽車代理商'}, '2204.TW': {'name': '中華車', 'industry': '汽車', 'sub': '商用車/乘用車', 'rank': '汽車製造商', 'power': '★★★☆☆', 'position': '商用車、乘用車與電動車相關製造商', 'peers': '裕隆、和泰車、三陽工業', 'moat': '中：商用車通路與製造能力', 'risk': '車市循環、品牌競爭、政策', 'fair_mult': 1.02, 'customers': '商用車、乘用車、物流與企業車隊客戶', 'ai_customers': '無直接AI客戶；受惠智慧車/電動車趨勢', 'theme_text': '汽車、商用車、電動車', 'chain_position': '整車/商用車', 'market_share': '台灣商用車主要廠'}, '2231.TW': {'name': '為升', 'industry': '汽車零組件', 'sub': '胎壓偵測/車用電子', 'rank': '車用電子供應商', 'power': '★★★☆☆', 'position': '胎壓偵測器與車用電子供應商', 'peers': '同致、車用電子零組件廠', 'moat': '中：車用認證與產品線', 'risk': '車市需求、價格競爭、客戶集中', 'fair_mult': 1.03, 'customers': '汽車售後市場、車廠與車用電子通路', 'ai_customers': '無直接AI客戶；受惠智慧車趨勢', 'theme_text': '車用電子、汽車零組件', 'chain_position': '中游車用零組件', 'market_share': '胎壓偵測供應商'}, '2233.TW': {'name': '宇隆', 'industry': '汽車零組件', 'sub': '精密零件/車用', 'rank': '精密加工供應商', 'power': '★★★☆☆', 'position': '汽車與精密零組件加工供應商', 'peers': '和大、精密零件同業', 'moat': '中：精密加工與車用客戶', 'risk': '車市循環、匯率、客戶集中', 'fair_mult': 1.03, 'customers': '汽車零組件、傳動系統與精密機械客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '汽車零組件、精密加工', 'chain_position': '中游零組件', 'market_share': '車用精密加工供應商'}, '1536.TW': {'name': '和大', 'industry': '汽車零組件', 'sub': '齒輪/傳動', 'rank': '車用傳動零件供應商', 'power': '★★★☆☆', 'position': '汽車齒輪與傳動系統零件供應商', 'peers': '宇隆、車用傳動零件同業', 'moat': '中：精密齒輪加工與客戶認證', 'risk': '電動車轉型、車市需求、匯率', 'fair_mult': 1.03, 'customers': '汽車傳動系統、電動車與傳統車廠供應鏈客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '汽車零組件、電動車、傳動系統', 'chain_position': '中游車用零組件', 'market_share': '車用齒輪主要供應商'}, '4551.TW': {'name': '智伸科', 'industry': '汽車零組件', 'sub': '精密零件/車用', 'rank': '精密零件供應商', 'power': '★★★☆☆', 'position': '車用、工業與精密零件供應商', 'peers': '宇隆、和大、精密加工同業', 'moat': '中：精密加工與車用客戶認證', 'risk': '車市循環、客戶集中、匯率', 'fair_mult': 1.03, 'customers': '車用零件、工業設備與精密加工客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '汽車零組件、精密加工', 'chain_position': '中游零組件', 'market_share': '車用精密零件供應商'}, '6505.TW': {'name': '台塑化', 'industry': '油電燃氣', 'sub': '煉油/石化', 'rank': '台灣煉油與石化主要廠', 'power': '★★★★☆', 'position': '煉油、石化原料與油品供應商', 'peers': '中油、國際煉油石化廠', 'moat': '中高：煉油產能、垂直整合與集團資源', 'risk': '油價、煉油利差、景氣循環', 'fair_mult': 1.0, 'customers': '油品、石化、工業燃料與下游材料客戶', 'ai_customers': '無直接AI客戶；資料中心用電需求間接受惠', 'theme_text': '油電燃氣、石化、原物料', 'chain_position': '上游能源/石化', 'market_share': '台灣大型煉油石化廠'}, '1605.TW': {'name': '華新', 'industry': '電線電纜/不鏽鋼', 'sub': '電纜/不鏽鋼/資源', 'rank': '電纜與材料集團', 'power': '★★★★☆', 'position': '電線電纜、不鏽鋼與資源材料供應商', 'peers': '大亞、合機、不鏽鋼同業', 'moat': '中高：電纜通路、材料整合與資源布局', 'risk': '銅鎳價格、景氣循環、匯率', 'fair_mult': 1.03, 'customers': '電力工程、建設、工業、不鏽鋼與能源基礎建設客戶', 'ai_customers': '資料中心電力工程間接受惠', 'theme_text': '電線電纜、電網、重電、材料', 'chain_position': '上游材料/電網工程', 'market_share': '台灣電纜與不鏽鋼主要廠'}, '1609.TW': {'name': '大亞', 'industry': '電線電纜', 'sub': '電纜/能源', 'rank': '電線電纜主要廠', 'power': '★★★☆☆', 'position': '電線電纜、太陽能與能源工程供應商', 'peers': '華新、合機、國際電纜廠', 'moat': '中：電纜產能、工程與能源布局', 'risk': '銅價、工程進度、政策', 'fair_mult': 1.03, 'customers': '台電、電力工程、建設、資料中心與能源客戶', 'ai_customers': '資料中心與電網工程間接受惠', 'theme_text': '電線電纜、電網、能源、重電', 'chain_position': '電網材料/工程', 'market_share': '台灣電線電纜主要廠'}, '1618.TW': {'name': '合機', 'industry': '電線電纜', 'sub': '電纜/工程', 'rank': '電線電纜供應商', 'power': '★★★☆☆', 'position': '電線電纜與電力工程材料供應商', 'peers': '華新、大亞、電纜同業', 'moat': '中：電纜製造與工程客戶', 'risk': '銅價、工程進度、需求波動', 'fair_mult': 1.02, 'customers': '電力工程、建設、工業與公共工程客戶', 'ai_customers': '資料中心與電網工程間接受惠', 'theme_text': '電線電纜、電網、工程', 'chain_position': '電網材料', 'market_share': '台灣電纜供應商'}, '1504.TW': {'name': '東元', 'industry': '電機/能源', 'sub': '馬達/電控/能源', 'rank': '電機與馬達主要廠', 'power': '★★★★☆', 'position': '馬達、電控、能源與資料中心機電供應商', 'peers': 'ABB、Siemens、台達電、士電', 'moat': '中高：馬達技術、工業客戶與能源工程', 'risk': '景氣循環、原料、專案進度', 'fair_mult': 1.05, 'customers': '工業馬達、空調、能源工程、資料中心與電動車客戶', 'ai_customers': '資料中心機電與散熱相關客戶', 'theme_text': '電機、資料中心、能源、電動車', 'chain_position': '中游機電設備', 'market_share': '台灣馬達與電機主要廠'}, '1503.TW': {'name': '士電', 'industry': '電力/重電', 'sub': '重電/配電設備', 'rank': '台灣重電主要廠', 'power': '★★★★☆', 'position': '重電、配電盤、馬達與電力設備供應商', 'peers': '華城、中興電、東元、ABB', 'moat': '中高：電力設備認證、台電與工程客戶', 'risk': '政策節奏、交期、原物料', 'fair_mult': 1.06, 'customers': '台電、電力工程、工業廠房、建設與資料中心客戶', 'ai_customers': '資料中心與電網升級間接受惠', 'theme_text': '重電、電網、資料中心、電力設備', 'chain_position': '中游電力設備', 'market_share': '台灣重電主要供應商'}, '1514.TW': {'name': '亞力', 'industry': '電力/重電', 'sub': '配電盤/電力設備', 'rank': '電力設備供應商', 'power': '★★★★☆', 'position': '配電盤、變電設備與電力工程供應商', 'peers': '華城、中興電、士電、東元', 'moat': '中：電力設備客戶與工程經驗', 'risk': '工程認列、政策節奏、原物料', 'fair_mult': 1.05, 'customers': '台電、公共工程、半導體廠、資料中心與工業客戶', 'ai_customers': '資料中心與半導體電力工程間接受惠', 'theme_text': '重電、電網、資料中心、半導體廠務', 'chain_position': '中游電力設備/工程', 'market_share': '台灣電力設備供應商'}, '1515.TW': {'name': '力山', 'industry': '機械/健身器材', 'sub': '健身器材/工具機', 'rank': '健身器材代工供應商', 'power': '★★★☆☆', 'position': '健身器材、工具機與工業產品代工供應商', 'peers': '喬山、岱宇、機械同業', 'moat': '中：代工製造與客戶基礎', 'risk': '終端需求、庫存、匯率', 'fair_mult': 1.02, 'customers': '健身器材品牌、工具機與工業設備客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '健身器材、機械、消費耐久財', 'chain_position': '中游製造', 'market_share': '健身器材代工供應商'}, '4532.TW': {'name': '瑞智', 'industry': '電機/家電零組件', 'sub': '壓縮機', 'rank': '壓縮機供應商', 'power': '★★★☆☆', 'position': '空調與冰箱壓縮機供應商', 'peers': 'Panasonic、GMCC、國際壓縮機廠', 'moat': '中：壓縮機製造與客戶基礎', 'risk': '家電需求、價格競爭、原料', 'fair_mult': 1.02, 'customers': '空調、冰箱與家電品牌客戶', 'ai_customers': '資料中心空調間接受惠有限', 'theme_text': '家電零組件、空調、壓縮機', 'chain_position': '中游零組件', 'market_share': '壓縮機主要供應商'}, '9933.TW': {'name': '中鼎', 'industry': '工程/環保', 'sub': '統包工程/EPC', 'rank': '工程統包主要廠', 'power': '★★★★☆', 'position': '工程設計、統包與環保工程服務商', 'peers': '國際EPC工程商、欣陸', 'moat': '中高：工程經驗、專案管理與客戶基礎', 'risk': '工程認列、海外專案、原料成本', 'fair_mult': 1.03, 'customers': '石化、半導體、能源、環保與公共工程客戶', 'ai_customers': '資料中心與半導體廠務工程間接受惠', 'theme_text': '工程、EPC、環保、半導體廠務', 'chain_position': '工程服務', 'market_share': '台灣EPC工程龍頭之一'}, '3703.TW': {'name': '欣陸', 'industry': '營建/工程', 'sub': '工程/營建/環保', 'rank': '營建工程集團', 'power': '★★★☆☆', 'position': '營建、工程與環保水務服務集團', 'peers': '中鼎、達欣工、營建同業', 'moat': '中：工程經驗與集團資源', 'risk': '工程認列、房市、政策', 'fair_mult': 1.01, 'customers': '公共工程、營建、環保水務與工業工程客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '營建、工程、環保', 'chain_position': '工程/營建服務', 'market_share': '台灣工程營建集團'}, '2515.TW': {'name': '中工', 'industry': '營建/工程', 'sub': '營造工程', 'rank': '大型營造商', 'power': '★★★☆☆', 'position': '公共工程、建築營造與開發公司', 'peers': '達欣工、工信、欣陸', 'moat': '中：營造經驗與工程案源', 'risk': '工程成本、房市、政策', 'fair_mult': 1.0, 'customers': '公共工程、建設公司、工業與住宅開發客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '營建、公共工程、資產', 'chain_position': '營造工程', 'market_share': '台灣大型營造商'}, '2535.TW': {'name': '達欣工', 'industry': '營建/工程', 'sub': '營造工程', 'rank': '營造工程主要廠', 'power': '★★★☆☆', 'position': '建築工程、廠辦與公共工程承攬商', 'peers': '中工、欣陸、工信', 'moat': '中：工程管理與客戶基礎', 'risk': '工程成本、認列時程、景氣', 'fair_mult': 1.01, 'customers': '建設公司、科技廠辦、公共工程與住宅工程客戶', 'ai_customers': '半導體/資料中心工程間接受惠', 'theme_text': '營建、科技廠辦、工程', 'chain_position': '營造工程', 'market_share': '台灣營造工程商'}, '9904.TW': {'name': '寶成', 'industry': '製鞋/消費', 'sub': '運動鞋代工/通路', 'rank': '全球運動鞋代工龍頭之一', 'power': '★★★★☆', 'position': '運動鞋代工與通路投資集團', 'peers': '豐泰、鈺齊-KY、申洲國際', 'moat': '中高：製鞋規模、品牌客戶與全球產能', 'risk': '品牌庫存、人工成本、匯率', 'fair_mult': 1.03, 'customers': 'Nike、Adidas、New Balance 等國際運動鞋品牌與零售通路', 'ai_customers': '無直接AI客戶', 'theme_text': '製鞋、品牌供應鏈、消費', 'chain_position': '中下游製造/通路', 'market_share': '全球運動鞋代工主要廠'}, '9910.TW': {'name': '豐泰', 'industry': '製鞋/消費', 'sub': '運動鞋代工', 'rank': '運動鞋代工主要廠', 'power': '★★★★☆', 'position': '國際運動鞋品牌代工供應商', 'peers': '寶成、鈺齊-KY、製鞋同業', 'moat': '中高：運動鞋製程、品牌客戶認證', 'risk': '品牌庫存、人工成本、匯率', 'fair_mult': 1.04, 'customers': 'Nike等國際運動鞋品牌客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '製鞋、運動品牌供應鏈', 'chain_position': '中下游製造', 'market_share': '運動鞋代工主要供應商'}, '9802.TW': {'name': '鈺齊-KY', 'industry': '製鞋/消費', 'sub': '戶外鞋/運動鞋代工', 'rank': '戶外鞋代工供應商', 'power': '★★★☆☆', 'position': '戶外鞋、運動鞋與功能鞋代工供應商', 'peers': '寶成、豐泰、製鞋同業', 'moat': '中：戶外鞋製程與品牌客戶', 'risk': '品牌庫存、匯率、產能利用率', 'fair_mult': 1.03, 'customers': '戶外與運動鞋品牌、休閒鞋品牌客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '製鞋、戶外運動、品牌供應鏈', 'chain_position': '中下游製造', 'market_share': '戶外鞋代工供應商'}, '9914.TW': {'name': '美利達', 'industry': '自行車', 'sub': '自行車品牌/製造', 'rank': '全球自行車品牌', 'power': '★★★★☆', 'position': '自行車品牌與製造供應商', 'peers': '巨大、Trek、Specialized', 'moat': '中高：品牌、製造與通路', 'risk': '庫存循環、消費需求、匯率', 'fair_mult': 1.03, 'customers': '自行車通路、電動自行車與品牌消費者', 'ai_customers': '無直接AI客戶', 'theme_text': '自行車、電動自行車、消費', 'chain_position': '下游品牌/製造', 'market_share': '全球自行車主要品牌'}, '9921.TW': {'name': '巨大', 'industry': '自行車', 'sub': '自行車品牌/製造', 'rank': '全球自行車龍頭之一', 'power': '★★★★☆', 'position': '自行車與電動自行車品牌及製造商', 'peers': '美利達、Trek、Specialized', 'moat': '中高：品牌、製造、通路與規模', 'risk': '庫存循環、消費景氣、匯率', 'fair_mult': 1.04, 'customers': '自行車通路、電動自行車與全球消費者', 'ai_customers': '無直接AI客戶', 'theme_text': '自行車、電動自行車、消費', 'chain_position': '下游品牌/製造', 'market_share': '全球自行車龍頭之一'}, '9938.TW': {'name': '百和', 'industry': '紡織/材料', 'sub': '黏扣帶/機能材料', 'rank': '運動材料供應商', 'power': '★★★☆☆', 'position': '黏扣帶、彈性織帶與運動材料供應商', 'peers': '運動材料同業、紡織材料廠', 'moat': '中：材料製程與品牌供應鏈', 'risk': '品牌庫存、消費需求、匯率', 'fair_mult': 1.03, 'customers': '運動鞋、服飾、戶外用品與品牌供應鏈客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '紡織材料、運動品牌供應鏈', 'chain_position': '上中游材料', 'market_share': '機能材料供應商'}, '9939.TW': {'name': '宏全', 'industry': '包材/食品供應鏈', 'sub': '飲料包材/代工', 'rank': '飲料包材主要廠', 'power': '★★★☆☆', 'position': '飲料包材、充填與代工服務供應商', 'peers': '食品包材同業、統一供應鏈', 'moat': '中：包材製造、客戶與全球產能', 'risk': '原料價格、飲料需求、匯率', 'fair_mult': 1.03, 'customers': '飲料品牌、食品公司、通路與消費品客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '包材、食品供應鏈、消費', 'chain_position': '中游包材/代工', 'market_share': '飲料包材主要供應商'}, '9945.TW': {'name': '潤泰新', 'industry': '營建/資產', 'sub': '不動產/投資', 'rank': '大型資產股', 'power': '★★★☆☆', 'position': '不動產開發、商場與轉投資控股公司', 'peers': '興富發、華固、遠雄、潤泰全', 'moat': '中：資產、商場與轉投資', 'risk': '房市政策、利率、轉投資波動', 'fair_mult': 1.01, 'customers': '住宅、商場、租賃與不動產開發客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '營建、資產、轉投資', 'chain_position': '不動產開發/資產', 'market_share': '台灣大型資產開發公司'}, '2915.TW': {'name': '潤泰全', 'industry': '零售/紡織/投資', 'sub': '量販/投資', 'rank': '零售與投資控股', 'power': '★★★☆☆', 'position': '零售、通路與轉投資控股公司', 'peers': '統一超、全家、潤泰新', 'moat': '中：通路資產與轉投資', 'risk': '消費景氣、轉投資波動', 'fair_mult': 1.01, 'customers': '量販零售、消費者與轉投資相關客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '零售、資產、轉投資', 'chain_position': '下游通路/控股', 'market_share': '台灣零售與投資控股'}, '5903.TW': {'name': '全家', 'industry': '零售通路', 'sub': '便利商店', 'rank': '台灣便利商店主要品牌', 'power': '★★★★☆', 'position': '便利商店、鮮食、物流與數位零售通路', 'peers': '統一超、萊爾富、OK Mart', 'moat': '中高：門市密度、品牌、鮮食與物流', 'risk': '人力成本、租金、消費景氣', 'fair_mult': 1.04, 'customers': '便利商店消費者、鮮食、電商取貨與會員客戶', 'ai_customers': '無直接AI客戶；受惠零售數據應用', 'theme_text': '零售、便利商店、民生消費', 'chain_position': '下游零售通路', 'market_share': '台灣便利商店主要品牌'}, '5904.TWO': {'name': '寶雅', 'industry': '零售通路', 'sub': '美妝生活百貨', 'rank': '美妝生活通路龍頭', 'power': '★★★★☆', 'position': '美妝、生活用品與連鎖零售通路', 'peers': '屈臣氏、康是美、零售同業', 'moat': '中高：門市展店、商品組合與會員數據', 'risk': '消費景氣、展店成本、競爭', 'fair_mult': 1.04, 'customers': '美妝、生活用品與女性消費客群', 'ai_customers': '無直接AI客戶；受惠零售數據應用', 'theme_text': '零售、美妝、生活百貨', 'chain_position': '下游零售通路', 'market_share': '台灣美妝生活通路龍頭'}, '8454.TW': {'name': '富邦媒', 'industry': '電商/零售', 'sub': '電商平台', 'rank': '台灣電商主要平台', 'power': '★★★★☆', 'position': 'momo電商、電視購物與線上零售平台', 'peers': 'PChome、蝦皮、博客來、Yahoo購物', 'moat': '中高：物流、會員、平台流量與供應商', 'risk': '競爭、物流成本、消費景氣', 'fair_mult': 1.04, 'customers': '線上購物消費者、品牌商、供應商與廣告客戶', 'ai_customers': '無直接AI客戶；受惠AI推薦與零售數據', 'theme_text': '電商、零售、平台經濟', 'chain_position': '下游電商平台', 'market_share': '台灣B2C電商主要平台'}, '8044.TW': {'name': '網家', 'industry': '電商/零售', 'sub': '電商平台', 'rank': '台灣電商平台', 'power': '★★★☆☆', 'position': 'PChome線上購物與電商服務平台', 'peers': '富邦媒、蝦皮、博客來', 'moat': '中：品牌、平台與物流基礎', 'risk': '競爭、獲利壓力、物流成本', 'fair_mult': 1.0, 'customers': '線上購物消費者、品牌商與供應商', 'ai_customers': '無直接AI客戶；受惠AI推薦與零售數據', 'theme_text': '電商、零售、平台', 'chain_position': '下游電商平台', 'market_share': '台灣電商平台'}, '2412.TW': {'name': '中華電', 'industry': '電信', 'sub': '電信/IDC/雲端', 'rank': '台灣電信龍頭', 'power': '★★★★★', 'position': '固定網路、行動通訊、IDC與雲端服務龍頭', 'peers': '台灣大、遠傳、亞太電信', 'moat': '高：網路基礎建設、客戶規模與頻譜資源', 'risk': '電信價格競爭、資本支出、監管', 'fair_mult': 1.03, 'customers': '個人電信、企業網路、雲端、IDC與政府客戶', 'ai_customers': 'AI資料中心/企業雲端客戶間接受惠', 'theme_text': '電信、IDC、雲端、股息', 'chain_position': '基礎網路/雲端服務', 'market_share': '台灣電信龍頭'}, '3045.TW': {'name': '台灣大', 'industry': '電信', 'sub': '電信/媒體/電商', 'rank': '台灣電信主要業者', 'power': '★★★★☆', 'position': '行動通訊、寬頻、媒體與電商整合服務商', 'peers': '中華電、遠傳、亞太電信', 'moat': '中高：電信用戶、頻譜、媒體與電商資源', 'risk': '價格競爭、整合成本、資本支出', 'fair_mult': 1.03, 'customers': '個人電信、企業通訊、媒體與電商客戶', 'ai_customers': '企業雲端/資料服務間接受惠', 'theme_text': '電信、媒體、電商、股息', 'chain_position': '電信/數位服務', 'market_share': '台灣電信主要業者'}, '4904.TW': {'name': '遠傳', 'industry': '電信', 'sub': '電信/企業ICT', 'rank': '台灣電信主要業者', 'power': '★★★★☆', 'position': '行動通訊、企業ICT與數位服務供應商', 'peers': '中華電、台灣大', 'moat': '中高：電信用戶、頻譜與企業ICT服務', 'risk': '價格競爭、資本支出、整合', 'fair_mult': 1.03, 'customers': '個人電信、企業ICT、雲端與政府客戶', 'ai_customers': '企業雲端/AI資料服務間接受惠', 'theme_text': '電信、企業ICT、雲端、股息', 'chain_position': '電信/數位服務', 'market_share': '台灣電信主要業者'}, '3005.TW': {'name': '神基', 'industry': '工業電腦/車用', 'sub': '強固型電腦/車用機構', 'rank': '強固型電腦主要廠', 'power': '★★★★☆', 'position': '強固型電腦、車用與航太零組件供應商', 'peers': '研華、Getac、Panasonic Toughbook', 'moat': '中高：強固型產品、客戶認證與利基市場', 'risk': '政府/企業標案、匯率、景氣', 'fair_mult': 1.05, 'customers': '軍警、工業、車用、航太與戶外強固型電腦客戶', 'ai_customers': '邊緣AI與工業AI客戶間接受惠', 'theme_text': '工業電腦、邊緣AI、車用', 'chain_position': '中下游系統/零組件', 'market_share': '強固型電腦主要供應商'}, '2395.TW': {'name': '研華', 'industry': '工業電腦', 'sub': 'IPC/邊緣運算', 'rank': '全球工業電腦龍頭', 'power': '★★★★★', 'position': '工業電腦、邊緣運算與物聯網平台供應商', 'peers': '凌華、Kontron、Siemens IPC', 'moat': '高：品牌、通路、工業客戶與模組化平台', 'risk': '工業景氣、庫存、匯率', 'fair_mult': 1.07, 'customers': '工業自動化、醫療、交通、能源、零售與邊緣AI客戶', 'ai_customers': '工業AI、邊緣AI、智慧製造客戶', 'theme_text': '工業電腦、邊緣AI、IoT、自動化', 'chain_position': '中下游工業系統', 'market_share': '全球工業電腦龍頭'}, '6414.TW': {'name': '樺漢', 'industry': '工業電腦', 'sub': 'IPC/嵌入式系統', 'rank': '工業電腦主要廠', 'power': '★★★★☆', 'position': '工業電腦、嵌入式系統與智慧製造解決方案供應商', 'peers': '研華、凌華、研揚、Kontron', 'moat': '中高：集團資源、系統整合與工業客戶', 'risk': '整合、景氣循環、毛利率', 'fair_mult': 1.05, 'customers': '工業自動化、零售、醫療、交通與嵌入式系統客戶', 'ai_customers': '邊緣AI、工業AI與智慧製造客戶', 'theme_text': '工業電腦、邊緣AI、智慧製造', 'chain_position': '中下游工業系統', 'market_share': '工業電腦主要廠'}, '6579.TW': {'name': '研揚', 'industry': '工業電腦', 'sub': 'IPC/邊緣運算', 'rank': '工業電腦供應商', 'power': '★★★☆☆', 'position': '工業電腦、嵌入式板卡與邊緣運算供應商', 'peers': '研華、凌華、樺漢', 'moat': '中：嵌入式板卡與工業客戶', 'risk': '工業景氣、競爭、庫存', 'fair_mult': 1.04, 'customers': '工業自動化、醫療、交通、零售與邊緣運算客戶', 'ai_customers': '邊緣AI與工業AI客戶', 'theme_text': '工業電腦、邊緣AI、IoT', 'chain_position': '中游工業電腦', 'market_share': '工業電腦供應商'}, '2352.TW': {'name': '佳世達', 'industry': '電子製造/醫療', 'sub': '顯示器/醫療/系統整合', 'rank': '電子與醫療整合集團', 'power': '★★★☆☆', 'position': '顯示器、醫療、網通與系統整合服務商', 'peers': '友達集團、電子代工同業', 'moat': '中：多元事業、醫療通路與電子製造能力', 'risk': '整合、景氣循環、毛利率', 'fair_mult': 1.03, 'customers': '顯示器、醫療通路、企業IT與系統整合客戶', 'ai_customers': '企業AI/醫療資訊間接受惠', 'theme_text': '電子製造、醫療、系統整合', 'chain_position': '中下游系統/通路', 'market_share': '電子與醫療整合集團'}, '2371.TW': {'name': '大同', 'industry': '電機/資產', 'sub': '重電/電機/資產', 'rank': '老牌電機集團', 'power': '★★★☆☆', 'position': '電機、重電、家電與資產相關集團', 'peers': '東元、士電、華城', 'moat': '中：品牌、電機資產與通路', 'risk': '轉型、資產處分、競爭', 'fair_mult': 1.02, 'customers': '電力設備、家電、工業電機與工程客戶', 'ai_customers': '資料中心與電網升級間接受惠', 'theme_text': '電機、重電、資產、電網', 'chain_position': '電機設備/資產', 'market_share': '台灣老牌電機集團'}, '2441.TW': {'name': '超豐', 'industry': '半導體', 'sub': 'IC封測', 'rank': 'IC封測供應商', 'power': '★★★☆☆', 'position': 'IC封裝測試服務供應商', 'peers': '日月光、力成、南茂、頎邦', 'moat': '中：封測產能與客戶基礎', 'risk': '半導體景氣、稼動率、價格競爭', 'fair_mult': 1.03, 'customers': 'IC設計、IDM、消費電子、通訊與車用晶片客戶', 'ai_customers': 'AI/HPC封測需求間接受惠', 'theme_text': '半導體、封測、IC設計供應鏈', 'chain_position': '中游封測', 'market_share': '台灣IC封測供應商'}, '8150.TW': {'name': '南茂', 'industry': '半導體', 'sub': '記憶體/DDI封測', 'rank': '封測主要廠', 'power': '★★★☆☆', 'position': '記憶體與顯示驅動IC封測供應商', 'peers': '日月光、力成、頎邦、Amkor', 'moat': '中：記憶體/DDI封測與客戶基礎', 'risk': '記憶體與面板循環、稼動率', 'fair_mult': 1.03, 'customers': '記憶體、DDI、IC設計與面板供應鏈客戶', 'ai_customers': 'AI記憶體封測間接受惠', 'theme_text': '半導體、封測、記憶體、DDI', 'chain_position': '中游封測', 'market_share': '記憶體/DDI封測主要廠'}, '3264.TWO': {'name': '欣銓', 'industry': '半導體', 'sub': '晶圓測試', 'rank': '晶圓測試供應商', 'power': '★★★☆☆', 'position': 'IC晶圓測試與成品測試服務供應商', 'peers': '京元電子、矽格、日月光', 'moat': '中：測試產能與客戶導入', 'risk': '半導體循環、稼動率、客戶集中', 'fair_mult': 1.04, 'customers': 'IC設計、車用、通訊、消費與工控晶片客戶', 'ai_customers': 'AI/HPC測試需求間接受惠', 'theme_text': '半導體、測試、車用IC', 'chain_position': '中游測試', 'market_share': '台灣晶圓測試供應商'}, '6257.TW': {'name': '矽格', 'industry': '半導體', 'sub': 'IC測試/封裝', 'rank': '測試封裝供應商', 'power': '★★★☆☆', 'position': 'IC測試、封裝與晶圓測試服務商', 'peers': '京元電子、欣銓、日月光', 'moat': '中：測試產能與客戶基礎', 'risk': '半導體循環、稼動率、價格競爭', 'fair_mult': 1.03, 'customers': '通訊、車用、消費、工控與IC設計客戶', 'ai_customers': 'AI/HPC測試需求間接受惠', 'theme_text': '半導體、測試、封裝', 'chain_position': '中游測試/封裝', 'market_share': '台灣測試封裝供應商'}, '3374.TWO': {'name': '精材', 'industry': '半導體', 'sub': '影像感測封裝', 'rank': '影像感測封裝供應商', 'power': '★★★☆☆', 'position': '影像感測器與晶圓級封裝供應商', 'peers': '采鈺、同欣電、Sony供應鏈', 'moat': '中：晶圓級封裝與影像感測客戶', 'risk': '手機/消費電子需求、客戶集中', 'fair_mult': 1.04, 'customers': '影像感測器、手機、車用與消費電子客戶', 'ai_customers': 'AI視覺/車用感測間接受惠', 'theme_text': '影像感測、晶圓級封裝、車用', 'chain_position': '中游封裝/感測', 'market_share': '影像感測封裝供應商'}, '2328.TW': {'name': '廣宇', 'industry': 'EMS/零組件', 'sub': '電子製造/零組件', 'rank': '電子製造供應商', 'power': '★★★☆☆', 'position': '電子製造與連接線材等零組件供應商', 'peers': '鴻海、正崴、電子製造同業', 'moat': '中：製造能力與集團資源', 'risk': '毛利率、終端需求、客戶集中', 'fair_mult': 1.02, 'customers': '消費電子、工業電子、線材與系統組裝客戶', 'ai_customers': '伺服器/資料中心供應鏈間接受惠', 'theme_text': 'EMS、電子零組件、伺服器供應鏈', 'chain_position': '中游製造/零組件', 'market_share': '電子製造供應商'}, '2313.TW': {'name': '華通', 'industry': 'PCB', 'sub': 'PCB/HDI', 'rank': 'PCB主要廠', 'power': '★★★☆☆', 'position': 'PCB、HDI與高階電路板供應商', 'peers': '欣興、健鼎、臻鼎-KY、TTM', 'moat': '中：PCB量產、客戶基礎與產品線', 'risk': '消費電子循環、原料、價格競爭', 'fair_mult': 1.04, 'customers': '手機、伺服器、網通、車用與消費電子客戶', 'ai_customers': 'AI伺服器PCB間接受惠', 'theme_text': 'PCB、HDI、AI伺服器、消費電子', 'chain_position': '上游PCB', 'market_share': '台灣PCB主要廠'}, '4915.TW': {'name': '致伸', 'industry': '電子零組件', 'sub': '輸入裝置/聲學/視覺', 'rank': '電子零組件供應商', 'power': '★★★☆☆', 'position': '鍵盤、滑鼠、聲學與視覺模組供應商', 'peers': '群光、光寶、電子零組件同業', 'moat': '中：產品整合與品牌客戶', 'risk': 'PC需求、客戶集中、毛利率', 'fair_mult': 1.03, 'customers': 'PC/NB品牌、遊戲周邊、聲學與視覺模組客戶', 'ai_customers': 'AI PC與邊緣視覺間接受惠', 'theme_text': 'AI PC、電子零組件、聲學視覺', 'chain_position': '中游零組件', 'market_share': 'PC周邊零組件供應商'}, '2385.TW': {'name': '群光', 'industry': '電子零組件', 'sub': '鍵盤/電源/影像', 'rank': 'PC零組件主要廠', 'power': '★★★★☆', 'position': '鍵盤、電源、影像與PC周邊零組件供應商', 'peers': '致伸、光寶、PC零組件同業', 'moat': '中高：PC品牌客戶、產品線與量產能力', 'risk': 'PC需求、庫存、匯率', 'fair_mult': 1.04, 'customers': 'NB/PC品牌、鍵盤、電源、影像與AI PC客戶', 'ai_customers': 'AI PC與邊緣影像需求間接受惠', 'theme_text': 'AI PC、PC零組件、影像模組', 'chain_position': '中游零組件', 'market_share': 'PC輸入裝置主要供應商'}, '2329.TW': {'name': '華泰', 'industry': '半導體', 'sub': '記憶體封測/模組', 'rank': '半導體封測供應商', 'power': '★★★☆☆', 'position': '記憶體封測、模組與半導體服務供應商', 'peers': '力成、南茂、記憶體封測同業', 'moat': '中：記憶體封測與客戶基礎', 'risk': '記憶體循環、稼動率、價格競爭', 'fair_mult': 1.03, 'customers': '記憶體、儲存、半導體與模組客戶', 'ai_customers': 'AI儲存與記憶體需求間接受惠', 'theme_text': '半導體、記憶體封測、AI儲存', 'chain_position': '中游封測/模組', 'market_share': '記憶體封測供應商'}, '5483.TWO': {'name': '中美晶', 'industry': '半導體材料/太陽能', 'sub': '矽晶圓/轉投資', 'rank': '矽晶圓與投資控股', 'power': '★★★★☆', 'position': '半導體矽晶圓、太陽能與環球晶轉投資控股', 'peers': '環球晶、信越、SUMCO', 'moat': '中高：矽晶圓資產與轉投資', 'risk': '半導體循環、太陽能景氣、轉投資波動', 'fair_mult': 1.04, 'customers': '半導體晶圓廠、太陽能與材料客戶', 'ai_customers': 'AI晶片晶圓需求間接受惠', 'theme_text': '矽晶圓、半導體材料、太陽能', 'chain_position': '上游材料/控股', 'market_share': '矽晶圓投資控股'}, '6488.TWO': {'name': '環球晶', 'industry': '半導體材料', 'sub': '矽晶圓', 'rank': '全球矽晶圓主要供應商', 'power': '★★★★☆', 'position': '半導體矽晶圓供應商', 'peers': 'Shin-Etsu、SUMCO、Siltronic', 'moat': '中高：矽晶圓技術、長約與全球產能', 'risk': '半導體循環、價格、資本支出', 'fair_mult': 1.05, 'customers': '晶圓代工、IDM、記憶體與功率半導體客戶', 'ai_customers': 'AI/HPC晶片晶圓需求間接受惠', 'theme_text': '半導體材料、矽晶圓、AI晶片供應鏈', 'chain_position': '上游矽晶圓材料', 'market_share': '全球矽晶圓主要供應商'}, '1560.TW': {'name': '中砂', 'industry': '半導體材料/工具', 'sub': '再生晶圓/鑽石碟', 'rank': '半導體耗材供應商', 'power': '★★★★☆', 'position': '再生晶圓、鑽石碟與半導體耗材供應商', 'peers': '辛耘、半導體耗材同業', 'moat': '中高：耗材認證、再生晶圓與客戶基礎', 'risk': '半導體資本支出、稼動率、價格', 'fair_mult': 1.06, 'customers': '晶圓代工、IDM、矽晶圓與半導體製程客戶', 'ai_customers': 'AI晶片製程需求間接受惠', 'theme_text': '半導體耗材、再生晶圓、先進製程', 'chain_position': '上游耗材/再生晶圓', 'market_share': '台灣半導體耗材主要廠'}, '4763.TW': {'name': '材料-KY', 'industry': '化工材料', 'sub': '醋酸纖維素/特用材料', 'rank': '特用材料供應商', 'power': '★★★☆☆', 'position': '醋酸纖維素與特用化學材料供應商', 'peers': '國際特化材料廠', 'moat': '中：材料製程與客戶認證', 'risk': '需求波動、原料、客戶集中', 'fair_mult': 1.04, 'customers': '菸草濾嘴、特用材料、工業材料與化工客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '特用化學、材料、利基產品', 'chain_position': '上游材料', 'market_share': '利基特用材料供應商'}, '1717.TW': {'name': '長興', 'industry': '化工材料', 'sub': '合成樹脂/電子材料', 'rank': '化工材料主要廠', 'power': '★★★☆☆', 'position': '合成樹脂、電子材料與特用化學品供應商', 'peers': '南亞、長春、國際化工材料廠', 'moat': '中：產品線、材料配方與客戶基礎', 'risk': '原料成本、景氣循環、競爭', 'fair_mult': 1.03, 'customers': '電子材料、塗料、工業樹脂、PCB與化工客戶', 'ai_customers': 'AI伺服器材料供應鏈間接受惠', 'theme_text': '化工材料、電子材料、PCB材料', 'chain_position': '上游化工/材料', 'market_share': '台灣化工材料主要廠'}, '1722.TW': {'name': '台肥', 'industry': '化工/資產', 'sub': '肥料/化工/資產', 'rank': '肥料與資產公司', 'power': '★★★☆☆', 'position': '肥料、化工與土地資產公司', 'peers': '東鹼、化工同業、資產股', 'moat': '中：肥料通路、品牌與資產', 'risk': '原料成本、政策、資產開發', 'fair_mult': 1.01, 'customers': '農業、化工、肥料通路與資產開發客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '化工、肥料、資產', 'chain_position': '上游化工/資產', 'market_share': '台灣肥料主要供應商'}, '2612.TW': {'name': '中航', 'industry': '航運', 'sub': '散裝航運', 'rank': '散裝航運公司', 'power': '★★★☆☆', 'position': '散裝航運與船舶運輸服務商', 'peers': '裕民、慧洋-KY、新興', 'moat': '中：船隊與航運經驗', 'risk': 'BDI運價、油價、景氣循環', 'fair_mult': 0.99, 'customers': '原物料、礦砂、穀物與散裝貨運客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '航運、散裝、原物料循環', 'chain_position': '下游運輸服務', 'market_share': '台灣散裝航運公司'}, '2606.TW': {'name': '裕民', 'industry': '航運', 'sub': '散裝航運', 'rank': '散裝航運主要業者', 'power': '★★★☆☆', 'position': '散裝航運與原物料運輸公司', 'peers': '慧洋-KY、中航、新興、國際散裝航商', 'moat': '中：船隊、航運經驗與集團資源', 'risk': 'BDI運價、油價、景氣循環', 'fair_mult': 1.0, 'customers': '礦砂、煤炭、穀物、能源與原物料運輸客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '航運、散裝、原物料循環', 'chain_position': '下游運輸服務', 'market_share': '台灣散裝航運主要公司'}, '2637.TW': {'name': '慧洋-KY', 'industry': '航運', 'sub': '散裝航運', 'rank': '散裝航運主要業者', 'power': '★★★☆☆', 'position': '國際散裝航運船隊營運公司', 'peers': '裕民、中航、新興、國際散裝航商', 'moat': '中：船隊規模與長約/現貨配置', 'risk': 'BDI運價、利率、油價', 'fair_mult': 1.0, 'customers': '礦砂、穀物、煤炭、工業原物料運輸客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '航運、散裝、股息、原物料循環', 'chain_position': '下游運輸服務', 'market_share': '台灣散裝航運主要公司'}, '2605.TW': {'name': '新興', 'industry': '航運', 'sub': '散裝航運', 'rank': '散裝航運公司', 'power': '★★★☆☆', 'position': '散裝與油輪運輸服務公司', 'peers': '裕民、慧洋-KY、中航', 'moat': '中：船隊與航運經驗', 'risk': '運價循環、油價、景氣', 'fair_mult': 0.99, 'customers': '原物料、能源、穀物與散裝貨運客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '航運、散裝、油輪', 'chain_position': '下游運輸服務', 'market_share': '台灣航運公司'}, '2636.TW': {'name': '台驊投控', 'industry': '物流/航運', 'sub': '貨運承攬/物流', 'rank': '物流承攬商', 'power': '★★★☆☆', 'position': '海空運承攬、物流與供應鏈服務商', 'peers': '中菲行、捷迅、國際貨代', 'moat': '中：客戶網絡、物流經驗與供應鏈服務', 'risk': '海空運價、景氣、競爭', 'fair_mult': 1.02, 'customers': '電子、消費品、製造業、跨境物流與供應鏈客戶', 'ai_customers': 'AI伺服器物流間接受惠', 'theme_text': '物流、航運、供應鏈', 'chain_position': '物流服務', 'market_share': '台灣貨運承攬商'}, '5607.TWO': {'name': '遠雄港', 'industry': '物流/港埠', 'sub': '航空貨運園區', 'rank': '物流園區營運商', 'power': '★★★☆☆', 'position': '航空貨運園區、物流倉儲與自由貿易港區服務商', 'peers': '倉儲物流同業、桃園航空城供應鏈', 'moat': '中：物流園區位置與營運資產', 'risk': '航空貨運景氣、租賃需求、政策', 'fair_mult': 1.02, 'customers': '航空貨運、物流、電子製造、跨境電商與倉儲客戶', 'ai_customers': 'AI伺服器/電子貨運間接受惠', 'theme_text': '物流、航空貨運、倉儲', 'chain_position': '物流基礎設施', 'market_share': '航空貨運園區營運商'}, '2634.TW': {'name': '漢翔', 'industry': '航太/國防', 'sub': '航太製造/維修', 'rank': '台灣航太龍頭', 'power': '★★★★☆', 'position': '航太結構件、軍機與民航維修製造商', 'peers': 'Aerospace供應鏈、國際航太廠', 'moat': '中高：航太認證、國防案與製造能力', 'risk': '專案進度、國防預算、匯率', 'fair_mult': 1.04, 'customers': '國防、民航、航太結構件與維修客戶', 'ai_customers': '無直接AI客戶；國防科技間接受惠', 'theme_text': '航太、國防、維修', 'chain_position': '航太製造/維修', 'market_share': '台灣航太龍頭'}, '9958.TW': {'name': '世紀鋼', 'industry': '綠能/鋼構', 'sub': '離岸風電水下基礎', 'rank': '離岸風電鋼構供應商', 'power': '★★★★☆', 'position': '離岸風電水下基礎與大型鋼構供應商', 'peers': '鋼構/風電供應鏈同業', 'moat': '中高：大型鋼構產能與離岸風電認證', 'risk': '政策、專案時程、鋼價', 'fair_mult': 1.05, 'customers': '離岸風電開發商、能源工程與大型鋼構客戶', 'ai_customers': '無直接AI客戶；能源基礎建設間接受惠', 'theme_text': '離岸風電、鋼構、能源', 'chain_position': '能源工程/鋼構', 'market_share': '台灣離岸風電鋼構主要廠'}, '2002.TW': {'name': '中鋼', 'industry': '鋼鐵', 'sub': '一貫鋼廠', 'rank': '台灣鋼鐵龍頭', 'power': '★★★★☆', 'position': '鋼鐵、鋼品與下游材料供應商', 'peers': '中鴻、新日鐵、浦項、寶鋼', 'moat': '中高：規模、產品線、通路與產業地位', 'risk': '鋼價循環、原料成本、中國供需', 'fair_mult': 1.0, 'customers': '汽車、營建、機械、家電、工業與下游鋼材客戶', 'ai_customers': '資料中心建設鋼材間接受惠有限', 'theme_text': '鋼鐵、原物料、景氣循環', 'chain_position': '上游鋼鐵材料', 'market_share': '台灣鋼鐵龍頭'}, '2014.TW': {'name': '中鴻', 'industry': '鋼鐵', 'sub': '熱冷軋鋼品', 'rank': '鋼鐵主要廠', 'power': '★★★☆☆', 'position': '熱軋、冷軋與鍍鋅鋼品供應商', 'peers': '中鋼、燁輝、盛餘', 'moat': '中：鋼品產能與集團資源', 'risk': '鋼價循環、原料、需求', 'fair_mult': 0.99, 'customers': '營建、機械、家電、汽車與下游鋼材加工客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '鋼鐵、鋼品、景氣循環', 'chain_position': '上游鋼鐵材料', 'market_share': '台灣鋼鐵主要廠'}, '2027.TW': {'name': '大成鋼', 'industry': '鋼鐵', 'sub': '不鏽鋼/鋁材通路', 'rank': '金屬材料通路商', 'power': '★★★☆☆', 'position': '美國不鏽鋼、鋁材與金屬材料通路供應商', 'peers': '不鏽鋼/鋁材通路同業', 'moat': '中：北美通路與庫存管理', 'risk': '金屬價格、景氣循環、匯率', 'fair_mult': 1.01, 'customers': '北美工業、建材、金屬加工與通路客戶', 'ai_customers': '資料中心建材間接受惠有限', 'theme_text': '鋼鐵、不鏽鋼、鋁材、北美通路', 'chain_position': '金屬材料通路', 'market_share': '北美金屬材料通路商'}, '2023.TW': {'name': '燁輝', 'industry': '鋼鐵', 'sub': '鍍鋅/烤漆鋼品', 'rank': '鍍鋅鋼品供應商', 'power': '★★★☆☆', 'position': '鍍鋅與烤漆鋼品供應商', 'peers': '中鴻、盛餘、鋼品同業', 'moat': '中：鋼品產品線與通路', 'risk': '鋼價、需求循環、競爭', 'fair_mult': 0.99, 'customers': '建材、家電、鋼構、工業與下游加工客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '鋼鐵、鍍鋅鋼品、建材', 'chain_position': '中游鋼品加工', 'market_share': '鍍鋅鋼品供應商'}, '2015.TW': {'name': '豐興', 'industry': '鋼鐵', 'sub': '鋼筋/型鋼', 'rank': '電爐鋼主要廠', 'power': '★★★☆☆', 'position': '鋼筋、型鋼與廢鋼回收電爐鋼廠', 'peers': '東和鋼鐵、威致、鋼筋同業', 'moat': '中：區域市場、電爐效率與通路', 'risk': '廢鋼價格、營建需求、鋼價', 'fair_mult': 1.01, 'customers': '營建、公共工程、鋼構與建材通路客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '鋼鐵、鋼筋、營建', 'chain_position': '中游鋼材', 'market_share': '台灣電爐鋼主要廠'}, '2031.TW': {'name': '新光鋼', 'industry': '鋼鐵', 'sub': '鋼材通路/加工', 'rank': '鋼材加工通路商', 'power': '★★★☆☆', 'position': '鋼材加工、通路與工程材料供應商', 'peers': '中鋼構、鋼材加工同業', 'moat': '中：通路、加工與庫存管理', 'risk': '鋼價波動、需求循環', 'fair_mult': 1.01, 'customers': '營建、工程、工業製造與鋼材加工客戶', 'ai_customers': '資料中心/能源工程間接受惠有限', 'theme_text': '鋼鐵、鋼材加工、工程', 'chain_position': '中下游鋼材加工', 'market_share': '台灣鋼材加工通路商'}, '2616.TW': {'name': '山隆', 'industry': '物流/油品', 'sub': '運輸/加油站', 'rank': '物流與油品通路', 'power': '★★★☆☆', 'position': '貨運物流、油品通路與加油站營運商', 'peers': '台塑化通路、物流同業', 'moat': '中：物流車隊與油品通路', 'risk': '油價、物流景氣、毛利率', 'fair_mult': 1.01, 'customers': '物流運輸、油品、加油站與企業車隊客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '物流、油品、通路', 'chain_position': '下游物流/油品通路', 'market_share': '物流與油品通路商'}, '2103.TW': {'name': '台橡', 'industry': '橡膠/化工', 'sub': '合成橡膠', 'rank': '合成橡膠供應商', 'power': '★★★☆☆', 'position': '合成橡膠與特用橡膠材料供應商', 'peers': '國際合成橡膠廠、南帝', 'moat': '中：合成橡膠產品與客戶基礎', 'risk': '原料、石化循環、需求', 'fair_mult': 1.0, 'customers': '輪胎、鞋材、工業橡膠與化工材料客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '橡膠、化工、原物料', 'chain_position': '上游材料', 'market_share': '合成橡膠供應商'}, '2104.TW': {'name': '國際中橡', 'industry': '橡膠/碳黑', 'sub': '碳黑/電池材料', 'rank': '碳黑供應商', 'power': '★★★☆☆', 'position': '碳黑、橡膠材料與能源材料供應商', 'peers': 'Orion、Cabot、碳黑同業', 'moat': '中：碳黑產能與客戶基礎', 'risk': '原料成本、景氣循環、環保法規', 'fair_mult': 1.01, 'customers': '輪胎、橡膠、塑膠、電池材料與工業客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '碳黑、橡膠材料、電池材料', 'chain_position': '上游材料', 'market_share': '碳黑供應商'}, '1904.TW': {'name': '正隆', 'industry': '造紙/包材', 'sub': '工紙/紙器', 'rank': '紙器包材主要廠', 'power': '★★★☆☆', 'position': '工業用紙、紙器與包材供應商', 'peers': '永豐餘、榮成、紙器同業', 'moat': '中：回收紙、紙器通路與客戶', 'risk': '紙價、能源成本、景氣循環', 'fair_mult': 1.01, 'customers': '電商、食品、消費品、工業與包材客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '造紙、包材、電商物流', 'chain_position': '中游包材', 'market_share': '台灣紙器包材主要廠'}, '1907.TW': {'name': '永豐餘', 'industry': '造紙/包材', 'sub': '紙漿/紙器/消費紙', 'rank': '造紙集團', 'power': '★★★☆☆', 'position': '紙漿、紙器、消費紙與包材集團', 'peers': '正隆、榮成、國際紙廠', 'moat': '中：產品線、資產與通路', 'risk': '紙價、能源、消費需求', 'fair_mult': 1.01, 'customers': '包材、消費紙、食品、電商與工業客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '造紙、包材、消費紙', 'chain_position': '上中游紙品/包材', 'market_share': '台灣造紙主要集團'}, '1909.TW': {'name': '榮成', 'industry': '造紙/包材', 'sub': '工紙/紙器', 'rank': '工紙供應商', 'power': '★★★☆☆', 'position': '工業用紙、紙器與環保回收紙供應商', 'peers': '正隆、永豐餘、紙器同業', 'moat': '中：回收紙與紙器產能', 'risk': '紙價、中國需求、能源成本', 'fair_mult': 1.0, 'customers': '電商、工業、食品與消費品包材客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '造紙、包材、循環經濟', 'chain_position': '中游包材', 'market_share': '工紙與紙器供應商'}, '2347.TW': {'name': '聯強', 'industry': '通路', 'sub': 'ICT通路/代理', 'rank': '亞太ICT通路商', 'power': '★★★★☆', 'position': '資訊、通訊、半導體與消費電子通路服務商', 'peers': '神州數碼、Synnex同業、文曄', 'moat': '中高：通路規模、物流與代理品牌', 'risk': '庫存、通路毛利、景氣', 'fair_mult': 1.03, 'customers': 'IT通路、企業客戶、品牌商、零售與系統整合商', 'ai_customers': 'AI PC/伺服器通路間接受惠', 'theme_text': 'ICT通路、AI PC、企業IT', 'chain_position': '下游通路/代理', 'market_share': '亞太ICT通路主要商'}, '3036.TW': {'name': '文曄', 'industry': '電子通路', 'sub': 'IC通路', 'rank': '全球IC通路主要商', 'power': '★★★★☆', 'position': '半導體元件代理與供應鏈服務商', 'peers': '大聯大、Arrow、Avnet、益登', 'moat': '中高：代理線、客戶規模與供應鏈金融', 'risk': '庫存、半導體循環、毛利率', 'fair_mult': 1.04, 'customers': 'IC設計、電子製造、車用、工控、通訊與消費電子客戶', 'ai_customers': 'AI伺服器、車用與邊緣AI供應鏈客戶', 'theme_text': 'IC通路、半導體、AI供應鏈', 'chain_position': '半導體通路/代理', 'market_share': '全球IC通路主要商'}, '3702.TW': {'name': '大聯大', 'industry': '電子通路', 'sub': 'IC通路', 'rank': '全球IC通路龍頭之一', 'power': '★★★★☆', 'position': '半導體零組件通路與供應鏈服務平台', 'peers': '文曄、Arrow、Avnet、益登', 'moat': '中高：代理線、客戶規模、物流與供應鏈服務', 'risk': '庫存、半導體循環、毛利率', 'fair_mult': 1.04, 'customers': '電子製造、IC設計、車用、工控、通訊與消費電子客戶', 'ai_customers': 'AI伺服器、AI PC、車用與邊緣AI供應鏈客戶', 'theme_text': 'IC通路、半導體、AI供應鏈', 'chain_position': '半導體通路/代理', 'market_share': '全球IC通路龍頭之一'}, '8112.TW': {'name': '至上', 'industry': '電子通路', 'sub': 'IC/記憶體通路', 'rank': '電子通路商', 'power': '★★★☆☆', 'position': '記憶體與電子零組件通路服務商', 'peers': '文曄、大聯大、益登', 'moat': '中：代理線與客戶基礎', 'risk': '記憶體循環、庫存、毛利率', 'fair_mult': 1.03, 'customers': '記憶體、電子製造、消費電子與工控客戶', 'ai_customers': 'AI儲存與記憶體供應鏈間接受惠', 'theme_text': '電子通路、記憶體、半導體', 'chain_position': '半導體通路/代理', 'market_share': '電子通路商'}, '3023.TW': {'name': '信邦', 'industry': '連接器/線束', 'sub': '連接線/系統整合', 'rank': '連接線材主要廠', 'power': '★★★★☆', 'position': '工業、醫療、車用與綠能連接線材供應商', 'peers': '貿聯-KY、正崴、連接器同業', 'moat': '中高：客戶認證、客製化線束與多元應用', 'risk': '景氣循環、匯率、原料', 'fair_mult': 1.05, 'customers': '醫療、工業、車用、綠能、通訊與資料中心客戶', 'ai_customers': 'AI資料中心與工業AI客戶間接受惠', 'theme_text': '連接器、線束、車用、綠能、資料中心', 'chain_position': '中游零組件', 'market_share': '連接線材主要供應商'}, '3665.TW': {'name': '貿聯-KY', 'industry': '連接器/線束', 'sub': '高速線束/車用/資料中心', 'rank': '高速線束主要供應商', 'power': '★★★★☆', 'position': '資料中心、車用、工業與高階線束供應商', 'peers': '信邦、正崴、TE Connectivity', 'moat': '中高：高速線材、車用與資料中心客戶認證', 'risk': '客戶集中、匯率、需求波動', 'fair_mult': 1.06, 'customers': '資料中心、電動車、工業設備、醫療與高速傳輸客戶', 'ai_customers': 'AI資料中心、高速伺服器與電動車客戶', 'theme_text': 'AI伺服器、高速線束、電動車、資料中心', 'chain_position': '中游線束/連接器', 'market_share': '高速線束主要供應商'}, '6670.TW': {'name': '復盛應用', 'industry': '運動器材/消費', 'sub': '高爾夫球具代工', 'rank': '高爾夫球具代工龍頭', 'power': '★★★★☆', 'position': '高爾夫球桿頭與運動器材代工供應商', 'peers': '明安、運動器材代工同業', 'moat': '中高：製程、品牌客戶與產能規模', 'risk': '品牌庫存、消費需求、匯率', 'fair_mult': 1.04, 'customers': 'Callaway、TaylorMade、Titleist 等高爾夫與運動品牌客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '運動器材、高爾夫、品牌供應鏈', 'chain_position': '中下游代工製造', 'market_share': '高爾夫球具代工主要供應商'}, '8938.TWO': {'name': '明安', 'industry': '運動器材/消費', 'sub': '高爾夫球具/複材', 'rank': '高爾夫球具供應商', 'power': '★★★☆☆', 'position': '高爾夫球桿頭、複合材料與運動用品供應商', 'peers': '復盛應用、運動器材代工同業', 'moat': '中：複材製程與品牌客戶', 'risk': '品牌庫存、消費需求、匯率', 'fair_mult': 1.03, 'customers': '高爾夫品牌、運動用品與複合材料客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '運動器材、高爾夫、複合材料', 'chain_position': '中下游製造', 'market_share': '高爾夫球具供應商'}, '8464.TW': {'name': '億豐', 'industry': '居家/消費', 'sub': '窗簾/居家裝修', 'rank': '窗簾供應商', 'power': '★★★★☆', 'position': '窗簾、居家裝修與家居產品供應商', 'peers': 'Hunter Douglas、家居用品同業', 'moat': '中高：通路、產品設計與北美市場', 'risk': '房市、消費需求、匯率', 'fair_mult': 1.04, 'customers': '北美居家通路、建材通路、裝修與消費者', 'ai_customers': '無直接AI客戶', 'theme_text': '居家、裝修、北美消費', 'chain_position': '下游消費/通路', 'market_share': '窗簾與居家產品供應商'}, '9917.TW': {'name': '中保科', 'industry': '保全/智慧城市', 'sub': '保全/系統整合', 'rank': '保全服務龍頭', 'power': '★★★★☆', 'position': '保全、智慧城市、系統整合與物業服務商', 'peers': '新保、系統整合商', 'moat': '中高：客戶基礎、通路與服務網絡', 'risk': '人力成本、競爭、景氣', 'fair_mult': 1.03, 'customers': '企業、住宅、政府、智慧城市與物業管理客戶', 'ai_customers': 'AI影像辨識與智慧城市間接受惠', 'theme_text': '保全、智慧城市、AI影像、系統整合', 'chain_position': '下游服務/系統整合', 'market_share': '台灣保全服務龍頭之一'}, '9925.TW': {'name': '新保', 'industry': '保全/智慧城市', 'sub': '保全/系統整合', 'rank': '保全服務主要業者', 'power': '★★★☆☆', 'position': '保全、智慧建築與系統整合服務商', 'peers': '中保科、系統整合商', 'moat': '中：客戶基礎與服務網絡', 'risk': '人力成本、競爭、景氣', 'fair_mult': 1.02, 'customers': '企業、住宅、政府與智慧建築客戶', 'ai_customers': 'AI影像與智慧建築間接受惠', 'theme_text': '保全、智慧建築、系統整合', 'chain_position': '下游服務/系統整合', 'market_share': '台灣保全服務主要業者'}, '9926.TW': {'name': '新海', 'industry': '油電燃氣', 'sub': '天然氣', 'rank': '瓦斯供應商', 'power': '★★★☆☆', 'position': '區域天然氣供應與能源服務公司', 'peers': '欣天然、欣高、瓦斯同業', 'moat': '中：區域管線與公用事業特性', 'risk': '用氣量、成本、監管', 'fair_mult': 1.02, 'customers': '家庭、商業、工業與區域天然氣用戶', 'ai_customers': '無直接AI客戶', 'theme_text': '天然氣、公用事業、股息', 'chain_position': '能源公用事業', 'market_share': '區域天然氣供應商'}, '9931.TW': {'name': '欣高', 'industry': '油電燃氣', 'sub': '天然氣', 'rank': '瓦斯供應商', 'power': '★★★☆☆', 'position': '高雄地區天然氣供應商', 'peers': '新海、欣天然、瓦斯同業', 'moat': '中：區域管線與公用事業特性', 'risk': '用氣量、成本、監管', 'fair_mult': 1.02, 'customers': '家庭、商業、工業與區域天然氣用戶', 'ai_customers': '無直接AI客戶', 'theme_text': '天然氣、公用事業、股息', 'chain_position': '能源公用事業', 'market_share': '區域天然氣供應商'}, '9941.TW': {'name': '裕融', 'industry': '金融/租賃', 'sub': '汽車金融/租賃', 'rank': '汽車金融主要業者', 'power': '★★★★☆', 'position': '汽車金融、分期付款與租賃服務商', 'peers': '和潤、銀行消金、租賃同業', 'moat': '中高：汽車通路、風控與金融服務', 'risk': '信用風險、利率、車市需求', 'fair_mult': 1.03, 'customers': '汽車購車、企業租賃、消費分期與車商通路客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '汽車金融、租賃、消費金融', 'chain_position': '金融服務/汽車通路', 'market_share': '台灣汽車金融主要業者'}, '6592.TW': {'name': '和潤企業', 'industry': '金融/租賃', 'sub': '汽車金融/租賃', 'rank': '汽車金融主要業者', 'power': '★★★★☆', 'position': '汽車金融、分期付款與租賃服務商', 'peers': '裕融、銀行消金、租賃同業', 'moat': '中高：和泰車通路、風控與金融服務', 'risk': '信用風險、利率、車市需求', 'fair_mult': 1.03, 'customers': 'Toyota/Lexus車主、汽車經銷、企業租賃與消費分期客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '汽車金融、租賃、消費金融', 'chain_position': '金融服務/汽車通路', 'market_share': '台灣汽車金融主要業者'}, '5871.TW': {'name': '中租-KY', 'industry': '金融/租賃', 'sub': '租賃/企業金融', 'rank': '租賃金融龍頭', 'power': '★★★★☆', 'position': '設備租賃、企業金融與消費金融服務商', 'peers': '裕融、和潤、國際租賃公司', 'moat': '中高：風控、通路、跨區域平台與產品多元', 'risk': '信用風險、利率、景氣循環', 'fair_mult': 1.04, 'customers': '中小企業、設備租賃、太陽能、消費金融與企業金融客戶', 'ai_customers': 'AI設備租賃與企業設備投資間接受惠', 'theme_text': '租賃金融、企業金融、太陽能', 'chain_position': '金融服務/設備投資', 'market_share': '台灣租賃金融龍頭'}, '5876.TW': {'name': '上海商銀', 'industry': '金融', 'sub': '銀行', 'rank': '民營銀行', 'power': '★★★★☆', 'position': '商業銀行、財管與企業金融服務商', 'peers': '玉山金、永豐金、台新金', 'moat': '中高：銀行通路、財務體質與企業客戶', 'risk': '利差、信用風險、景氣', 'fair_mult': 1.02, 'customers': '企業金融、個人金融、財管與海外金融客戶', 'ai_customers': '無直接AI客戶；受惠金融科技', 'theme_text': '金融、銀行、股息', 'chain_position': '金融服務', 'market_share': '台灣民營銀行'}, '8462.TW': {'name': '柏文', 'industry': '運動休閒', 'sub': '健身房/運動服務', 'rank': '健身房連鎖', 'power': '★★★☆☆', 'position': '健身房、運動休閒與健康服務連鎖', 'peers': 'World Gym、健身工廠同業', 'moat': '中：品牌、場館與會員制', 'risk': '展店、人力租金、消費景氣', 'fair_mult': 1.03, 'customers': '健身會員、企業健康與運動休閒客群', 'ai_customers': '無直接AI客戶', 'theme_text': '健身、運動休閒、消費服務', 'chain_position': '下游服務', 'market_share': '台灣健身房連鎖主要品牌'}, '2723.TWO': {'name': '美食-KY', 'industry': '餐飲/消費', 'sub': '咖啡連鎖/餐飲', 'rank': '餐飲連鎖品牌', 'power': '★★★☆☆', 'position': '咖啡、烘焙與餐飲連鎖品牌經營商', 'peers': '星巴克、王品、餐飲同業', 'moat': '中：品牌與展店經驗', 'risk': '展店、消費景氣、成本', 'fair_mult': 1.02, 'customers': '咖啡、烘焙、餐飲與零售消費者', 'ai_customers': '無直接AI客戶', 'theme_text': '餐飲、咖啡、消費服務', 'chain_position': '下游餐飲服務', 'market_share': '餐飲連鎖品牌'}, '2729.TWO': {'name': '瓦城', 'industry': '餐飲/消費', 'sub': '連鎖餐飲', 'rank': '連鎖餐飲品牌', 'power': '★★★☆☆', 'position': '多品牌連鎖餐飲集團', 'peers': '王品、漢來美食、餐飲同業', 'moat': '中：品牌、展店與營運管理', 'risk': '人力成本、租金、消費景氣', 'fair_mult': 1.03, 'customers': '餐飲消費者、百貨商場與外送平台客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '餐飲、消費服務、展店', 'chain_position': '下游餐飲服務', 'market_share': '台灣連鎖餐飲品牌'}, '2753.TWO': {'name': '八方雲集', 'industry': '餐飲/消費', 'sub': '連鎖餐飲', 'rank': '平價餐飲連鎖', 'power': '★★★☆☆', 'position': '鍋貼、水餃與平價餐飲連鎖品牌', 'peers': '王品、瓦城、連鎖餐飲同業', 'moat': '中：門市密度、標準化與品牌', 'risk': '人力、食材成本、展店', 'fair_mult': 1.03, 'customers': '平價餐飲消費者、外送平台與加盟通路', 'ai_customers': '無直接AI客戶', 'theme_text': '餐飲、民生消費、展店', 'chain_position': '下游餐飲服務', 'market_share': '台灣平價餐飲連鎖'}, '2739.TWO': {'name': '寒舍', 'industry': '觀光餐飲', 'sub': '飯店/餐飲', 'rank': '飯店餐飲集團', 'power': '★★★☆☆', 'position': '飯店、宴會與餐飲服務公司', 'peers': '晶華、遠雄來、飯店同業', 'moat': '中：品牌、地點與餐飲能力', 'risk': '旅遊景氣、人力成本、房價', 'fair_mult': 1.02, 'customers': '商務旅客、觀光旅客、宴會與餐飲客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '觀光、飯店、餐飲', 'chain_position': '下游觀光服務', 'market_share': '台灣飯店餐飲業者'}, '2707.TW': {'name': '晶華', 'industry': '觀光餐飲', 'sub': '飯店/餐飲', 'rank': '高端飯店品牌', 'power': '★★★★☆', 'position': '高端飯店、餐飲與旅宿管理公司', 'peers': '寒舍、國賓、國際飯店品牌', 'moat': '中高：品牌、地點與高端客群', 'risk': '旅遊景氣、人力成本、房價', 'fair_mult': 1.03, 'customers': '商務旅客、觀光旅客、宴會與高端餐飲客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '觀光、飯店、餐飲、旅遊復甦', 'chain_position': '下游觀光服務', 'market_share': '台灣高端飯店品牌'}, '2704.TW': {'name': '國賓', 'industry': '觀光餐飲', 'sub': '飯店/資產', 'rank': '飯店與資產公司', 'power': '★★★☆☆', 'position': '飯店經營、餐飲與不動產資產公司', 'peers': '晶華、寒舍、飯店同業', 'moat': '中：品牌、地點與資產', 'risk': '旅遊景氣、資產開發、房價', 'fair_mult': 1.02, 'customers': '飯店、宴會、餐飲與資產開發客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '觀光、飯店、資產', 'chain_position': '下游觀光服務/資產', 'market_share': '台灣飯店業者'}, '6547.TWO': {'name': '高端疫苗', 'industry': '生技醫療', 'sub': '疫苗/生技', 'rank': '疫苗研發公司', 'power': '★★☆☆☆', 'position': '疫苗研發與生物製劑公司', 'peers': '國光生、國際疫苗公司、生技同業', 'moat': '低中：疫苗平台與研發經驗', 'risk': '臨床、法規、商業化與政策', 'fair_mult': 1.0, 'customers': '政府採購、醫療院所、疫苗通路與公共衛生客戶', 'ai_customers': '無直接AI客戶；AI藥物研發間接受惠有限', 'theme_text': '生技、疫苗、醫療', 'chain_position': '新藥/疫苗研發', 'market_share': '台灣疫苗研發公司'}, '4142.TWO': {'name': '國光生', 'industry': '生技醫療', 'sub': '疫苗/製藥', 'rank': '疫苗製造商', 'power': '★★★☆☆', 'position': '疫苗研發、生產與銷售公司', 'peers': '高端疫苗、國際疫苗公司', 'moat': '中：疫苗製造、藥證與公共衛生通路', 'risk': '採購政策、法規、需求波動', 'fair_mult': 1.02, 'customers': '政府、公衛、醫療院所與疫苗通路客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '生技、疫苗、醫療', 'chain_position': '疫苗製造/銷售', 'market_share': '台灣疫苗製造商'}, '4746.TW': {'name': '台耀', 'industry': '生技醫療', 'sub': '原料藥/API', 'rank': '原料藥供應商', 'power': '★★★☆☆', 'position': '原料藥、特殊學名藥與CDMO相關供應商', 'peers': '保瑞、美時、原料藥同業', 'moat': '中：藥證、製程與客戶認證', 'risk': '藥價、法規、客戶集中', 'fair_mult': 1.03, 'customers': '國際藥廠、學名藥、特殊藥與CDMO客戶', 'ai_customers': '無直接AI客戶；AI製藥間接受惠有限', 'theme_text': '生技、原料藥、CDMO', 'chain_position': '上游原料藥/製藥', 'market_share': '台灣原料藥供應商'}, '6472.TW': {'name': '保瑞', 'industry': '生技醫療', 'sub': 'CDMO/藥品銷售', 'rank': '製藥CDMO主要廠', 'power': '★★★★☆', 'position': '藥品CDMO、併購整合與國際市場銷售平台', 'peers': '美時、東洋、國際CDMO', 'moat': '中高：藥證、產能、併購整合與國際通路', 'risk': '整合、法規、客戶與藥價', 'fair_mult': 1.05, 'customers': '國際藥廠、學名藥、特殊藥與CDMO客戶', 'ai_customers': '無直接AI客戶；AI製藥間接受惠', 'theme_text': '生技、CDMO、製藥、併購', 'chain_position': '製藥/CDMO', 'market_share': '台灣製藥CDMO主要廠'}, '4123.TWO': {'name': '晟德', 'industry': '生技醫療', 'sub': '生技投資/製藥', 'rank': '生技投資控股', 'power': '★★★☆☆', 'position': '生技投資、藥品與醫療相關控股平台', 'peers': '中天、生技投資同業', 'moat': '中：投資組合與醫療資源', 'risk': '轉投資波動、臨床、資金', 'fair_mult': 1.01, 'customers': '生技公司、醫藥通路、轉投資與醫療市場客戶', 'ai_customers': 'AI醫療/製藥間接受惠有限', 'theme_text': '生技、投資控股、製藥', 'chain_position': '生技投資/控股', 'market_share': '台灣生技投資平台'}, '4128.TWO': {'name': '中天', 'industry': '生技醫療', 'sub': '生技/保健/投資', 'rank': '生技公司', 'power': '★★☆☆☆', 'position': '生技研發、保健與投資平台', 'peers': '晟德、合一、生技同業', 'moat': '低中：研發管線與轉投資', 'risk': '臨床、商業化、轉投資波動', 'fair_mult': 1.0, 'customers': '生技、醫療、保健與轉投資相關客戶', 'ai_customers': 'AI醫療/製藥間接受惠有限', 'theme_text': '生技、保健、投資', 'chain_position': '生技研發/控股', 'market_share': '台灣生技公司'}, '3218.TWO': {'name': '大學光', 'industry': '生技醫療', 'sub': '眼科醫療通路', 'rank': '眼科通路主要品牌', 'power': '★★★☆☆', 'position': '眼科醫療、視光通路與眼科診所服務商', 'peers': '醫療通路、眼科診所同業', 'moat': '中：通路、醫療服務與品牌', 'risk': '醫療法規、展店、人力', 'fair_mult': 1.03, 'customers': '眼科患者、視光通路與醫療服務客戶', 'ai_customers': 'AI眼科/醫療影像間接受惠', 'theme_text': '醫療通路、眼科、消費醫療', 'chain_position': '下游醫療服務', 'market_share': '台灣眼科醫療通路'}, '3224.TWO': {'name': '三顧', 'industry': '生技醫療', 'sub': '細胞治療/醫療服務', 'rank': '細胞治療公司', 'power': '★★☆☆☆', 'position': '細胞治療、醫療服務與再生醫療相關公司', 'peers': '再生醫療與生技同業', 'moat': '低中：研發與醫療合作資源', 'risk': '法規、臨床、商業化', 'fair_mult': 1.0, 'customers': '醫療院所、再生醫療、細胞治療與患者服務客戶', 'ai_customers': 'AI醫療間接受惠有限', 'theme_text': '生技、細胞治療、再生醫療', 'chain_position': '醫療研發/服務', 'market_share': '台灣細胞治療公司'}, '8926.TWO': {'name': '台汽電', 'industry': '能源/電力', 'sub': '汽電共生', 'rank': '能源服務供應商', 'power': '★★★☆☆', 'position': '汽電共生、能源服務與電力相關投資公司', 'peers': '森崴能源、雲豹能源、能源服務同業', 'moat': '中：電力營運經驗與能源案場', 'risk': '電價政策、燃料成本、案場進度', 'fair_mult': 1.03, 'customers': '工業用電、能源服務、汽電共生與電力客戶', 'ai_customers': '資料中心用電需求間接受惠', 'theme_text': '能源、電力、資料中心用電', 'chain_position': '能源服務/發電', 'market_share': '台灣汽電共生供應商'}, '6806.TW': {'name': '森崴能源', 'industry': '能源/工程', 'sub': '綠能工程/能源服務', 'rank': '綠能工程公司', 'power': '★★★☆☆', 'position': '再生能源、工程與能源服務供應商', 'peers': '雲豹能源、台汽電、能源工程同業', 'moat': '中：工程案源、能源服務與集團資源', 'risk': '案場進度、政策、資金成本', 'fair_mult': 1.04, 'customers': '再生能源、企業用電、工程與能源服務客戶', 'ai_customers': '資料中心綠電需求間接受惠', 'theme_text': '綠能、能源工程、資料中心用電', 'chain_position': '能源工程/服務', 'market_share': '台灣綠能工程公司'}, '6869.TW': {'name': '雲豹能源', 'industry': '能源/工程', 'sub': '再生能源/儲能', 'rank': '再生能源服務商', 'power': '★★★☆☆', 'position': '太陽能、儲能與能源服務公司', 'peers': '森崴能源、台汽電、能源同業', 'moat': '中：案場開發、能源服務與儲能布局', 'risk': '政策、案場進度、資金成本', 'fair_mult': 1.04, 'customers': '企業綠電、太陽能、儲能與能源服務客戶', 'ai_customers': '資料中心綠電與儲能需求間接受惠', 'theme_text': '綠能、儲能、資料中心用電', 'chain_position': '能源開發/服務', 'market_share': '台灣再生能源服務商'}, '6443.TW': {'name': '元晶', 'industry': '太陽能', 'sub': '太陽能電池/模組', 'rank': '太陽能供應商', 'power': '★★★☆☆', 'position': '太陽能電池與模組供應商', 'peers': '茂迪、聯合再生、國際太陽能廠', 'moat': '中：太陽能製造與案場客戶', 'risk': '價格競爭、政策、產能利用率', 'fair_mult': 1.02, 'customers': '太陽能案場、能源公司、企業綠電與工程客戶', 'ai_customers': '資料中心綠電需求間接受惠', 'theme_text': '太陽能、綠電、能源', 'chain_position': '太陽能製造', 'market_share': '台灣太陽能供應商'}, '3576.TW': {'name': '聯合再生', 'industry': '太陽能', 'sub': '太陽能電池/模組/系統', 'rank': '太陽能供應商', 'power': '★★★☆☆', 'position': '太陽能電池、模組與系統服務供應商', 'peers': '元晶、茂迪、國際太陽能廠', 'moat': '中：太陽能製造與系統經驗', 'risk': '價格競爭、政策、稼動率', 'fair_mult': 1.02, 'customers': '太陽能案場、企業綠電、能源工程與系統客戶', 'ai_customers': '資料中心綠電需求間接受惠', 'theme_text': '太陽能、綠電、能源系統', 'chain_position': '太陽能製造/系統', 'market_share': '台灣太陽能供應商'}, '6244.TWO': {'name': '茂迪', 'industry': '太陽能', 'sub': '太陽能電池/模組', 'rank': '太陽能供應商', 'power': '★★★☆☆', 'position': '太陽能電池、模組與能源產品供應商', 'peers': '元晶、聯合再生、國際太陽能廠', 'moat': '中：太陽能製造與品牌', 'risk': '價格競爭、政策、稼動率', 'fair_mult': 1.02, 'customers': '太陽能案場、企業綠電與能源工程客戶', 'ai_customers': '資料中心綠電需求間接受惠', 'theme_text': '太陽能、綠電、能源', 'chain_position': '太陽能製造', 'market_share': '台灣太陽能供應商'}, '1711.TW': {'name': '永光', 'industry': '化工材料', 'sub': '染料/特用化學', 'rank': '特用化學供應商', 'power': '★★★☆☆', 'position': '染料、特用化學品與電子化學材料供應商', 'peers': '長興、國際特化材料廠', 'moat': '中：配方、製程與客戶基礎', 'risk': '原料、需求循環、環保法規', 'fair_mult': 1.02, 'customers': '紡織染料、電子化學、醫藥化學與工業材料客戶', 'ai_customers': '半導體材料間接受惠有限', 'theme_text': '特用化學、電子材料、染料', 'chain_position': '上游化工材料', 'market_share': '台灣特用化學供應商'}, '1785.TW': {'name': '光洋科', 'industry': '材料/靶材', 'sub': '貴金屬/靶材', 'rank': '靶材與貴金屬供應商', 'power': '★★★★☆', 'position': '半導體、面板與儲能用靶材/貴金屬材料供應商', 'peers': 'JX Metals、Materion、靶材同業', 'moat': '中高：材料回收、靶材認證與客戶導入', 'risk': '貴金屬價格、半導體/面板循環', 'fair_mult': 1.05, 'customers': '半導體、面板、太陽能、儲能與貴金屬材料客戶', 'ai_customers': 'AI晶片/先進製程材料間接受惠', 'theme_text': '靶材、半導體材料、貴金屬回收', 'chain_position': '上游材料', 'market_share': '台灣靶材與貴金屬材料主要廠'}, '4739.TW': {'name': '康普', 'industry': '化工材料/電池', 'sub': '電池材料/化學品', 'rank': '電池材料供應商', 'power': '★★★☆☆', 'position': '電池材料、特用化學品與金屬化學材料供應商', 'peers': '美琪瑪、材料同業', 'moat': '中：材料製程與客戶基礎', 'risk': '金屬價格、電池需求、價格競爭', 'fair_mult': 1.03, 'customers': '電池材料、化學品、工業材料與能源儲存客戶', 'ai_customers': '資料中心儲能間接受惠', 'theme_text': '電池材料、儲能、化工材料', 'chain_position': '上游材料', 'market_share': '電池材料供應商'}, '4721.TW': {'name': '美琪瑪', 'industry': '化工材料/電池', 'sub': '電池材料/鈷錳材料', 'rank': '電池材料供應商', 'power': '★★★☆☆', 'position': '鋰電池正極前驅材料與化學材料供應商', 'peers': '康普、國際電池材料廠', 'moat': '中：材料製程與客戶基礎', 'risk': '金屬價格、電池需求、價格競爭', 'fair_mult': 1.03, 'customers': '鋰電池、儲能、電動車與化學材料客戶', 'ai_customers': '資料中心儲能間接受惠', 'theme_text': '電池材料、儲能、電動車', 'chain_position': '上游材料', 'market_share': '電池材料供應商'}, '1590.TW': {'name': '亞德客-KY', 'industry': '自動化/氣動元件', 'sub': '氣動元件', 'rank': '亞洲氣動元件龍頭之一', 'power': '★★★★★', 'position': '氣動元件、自動化零組件與工業自動化供應商', 'peers': 'SMC、Festo、Parker、上銀', 'moat': '高：品牌、通路、產品線與成本效率', 'risk': '工業景氣、中國需求、競爭', 'fair_mult': 1.06, 'customers': '工業自動化、半導體、電子、汽車、機械與機器人客戶', 'ai_customers': 'AI工廠、機器人與半導體自動化客戶', 'theme_text': '自動化、機器人、工業升級', 'chain_position': '上游自動化元件', 'market_share': '亞洲氣動元件龍頭之一'}, '2236.TW': {'name': '百達-KY', 'industry': '自動化/機械', 'sub': '自動化設備/機械', 'rank': '自動化設備供應商', 'power': '★★★☆☆', 'position': '自動化設備、機械與精密零組件供應商', 'peers': '和椿、盟立、機械設備同業', 'moat': '中：設備整合與客戶基礎', 'risk': '設備景氣、接單波動、匯率', 'fair_mult': 1.03, 'customers': '工業自動化、電子製造、汽車零組件與機械客戶', 'ai_customers': 'AI工廠/自動化間接受惠', 'theme_text': '自動化、機械、智慧製造', 'chain_position': '中游設備/零組件', 'market_share': '自動化設備供應商'}, '2464.TW': {'name': '盟立', 'industry': '自動化/機器人', 'sub': '自動化系統整合', 'rank': '自動化系統整合商', 'power': '★★★☆☆', 'position': '自動化設備、物流倉儲與系統整合供應商', 'peers': '和椿、上銀、國際自動化廠', 'moat': '中：系統整合經驗與客戶案源', 'risk': '設備景氣、專案認列、毛利率', 'fair_mult': 1.04, 'customers': '半導體、電子、物流倉儲、工業自動化與智慧工廠客戶', 'ai_customers': 'AI工廠、智慧物流與半導體自動化客戶', 'theme_text': '自動化、機器人、智慧物流、半導體設備', 'chain_position': '中下游系統整合', 'market_share': '台灣自動化系統整合商'}, '6605.TW': {'name': '帝寶', 'industry': '汽車零組件', 'sub': '車燈/AM零件', 'rank': '車燈與售後零件供應商', 'power': '★★★☆☆', 'position': '車燈、汽車售後維修零件與車用零組件供應商', 'peers': '堤維西、TYC同業、車燈同業', 'moat': '中：AM通路、模具與產品線', 'risk': '法規訴訟、車市、匯率', 'fair_mult': 1.03, 'customers': '汽車售後維修市場、保險維修、通路與車用零件客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '汽車零組件、AM、車燈', 'chain_position': '中游車用零組件/售後', 'market_share': '車燈與AM零件供應商'}, '1522.TW': {'name': '堤維西', 'industry': '汽車零組件', 'sub': '車燈/AM零件', 'rank': '車燈供應商', 'power': '★★★☆☆', 'position': '車燈與汽車售後市場零件供應商', 'peers': '帝寶、TYC同業、車燈同業', 'moat': '中：AM通路、產品線與量產能力', 'risk': '法規訴訟、車市、價格競爭', 'fair_mult': 1.03, 'customers': '汽車售後維修、保險維修、車用零件與通路客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '汽車零組件、車燈、AM市場', 'chain_position': '中游車用零組件/售後', 'market_share': '車燈零件供應商'}, '1524.TW': {'name': '耿鼎', 'industry': '汽車零組件', 'sub': '車用鈑金/AM零件', 'rank': '汽車鈑金零件供應商', 'power': '★★★☆☆', 'position': '汽車售後市場鈑金件與車用零件供應商', 'peers': '東陽、帝寶、堤維西', 'moat': '中：AM產品線與通路', 'risk': 'AM需求、匯率、競爭', 'fair_mult': 1.03, 'customers': '汽車售後維修市場、保險維修、通路與車用零件客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '汽車零組件、AM、鈑金件', 'chain_position': '中游車用零組件/售後', 'market_share': '汽車AM零件供應商'}, '1319.TW': {'name': '東陽', 'industry': '汽車零組件', 'sub': 'AM零件/OEM零件', 'rank': '汽車AM零件龍頭', 'power': '★★★★☆', 'position': '汽車售後市場與OEM車用零組件供應商', 'peers': '帝寶、堤維西、耿鼎、AM零件同業', 'moat': '中高：AM產品線、模具、通路與認證', 'risk': '訴訟、車市、匯率、競爭', 'fair_mult': 1.04, 'customers': '汽車售後維修市場、保險維修、OEM車廠與通路客戶', 'ai_customers': '無直接AI客戶', 'theme_text': '汽車零組件、AM、車用', 'chain_position': '中游車用零組件/售後', 'market_share': '汽車AM零件龍頭之一'}}

try:
    STOCK_DB.update(V236_EXTRA_STOCKS)
    # 重建搜尋別名，讓新增股票可用中文名稱或代碼搜尋
    ALIASES.clear()
    for sym, v in STOCK_DB.items():
        ALIASES[sym.upper()] = sym
        ALIASES[sym.split('.')[0]] = sym
        ALIASES[v.get('name', sym)] = sym
        ALIASES[v.get('name', sym).upper()] = sym
    OTC_CODES = {s.split('.')[0] for s in STOCK_DB if s.endswith('.TWO')}
except Exception:
    pass

def v236_completion_stats():
    total = len(STOCK_DB)
    with_customer = sum(1 for v in STOCK_DB.values() if v.get('customers'))
    with_ai_customer = sum(1 for v in STOCK_DB.values() if v.get('ai_customers'))
    with_valuation = sum(1 for v in STOCK_DB.values() if v.get('fair_mult') is not None)
    return {'total': total, 'with_customer': with_customer, 'with_ai_customer': with_ai_customer, 'with_valuation': with_valuation}

_v236_prev_rows_df = v230_rows_df

def v230_rows_df():
    df = _v236_prev_rows_df()
    if df is None or df.empty:
        return df
    if '估值狀態' not in df.columns:
        df['估值狀態'] = '已可計算'
    if '估值模型' not in df.columns:
        df['估值模型'] = '現價×產業乘數'
    if '主要客戶' not in df.columns:
        df['主要客戶'] = df['代碼'].map(lambda s: STOCK_DB.get(s, {}).get('customers', '待補'))
    else:
        df['主要客戶'] = df.apply(lambda r: STOCK_DB.get(r['代碼'], {}).get('customers', r.get('主要客戶','待補')), axis=1)
    if 'AI客戶' not in df.columns:
        df['AI客戶'] = df['代碼'].map(lambda s: STOCK_DB.get(s, {}).get('ai_customers', '待補'))
    else:
        df['AI客戶'] = df.apply(lambda r: STOCK_DB.get(r['代碼'], {}).get('ai_customers', r.get('AI客戶','待補')), axis=1)
    if '資料完整度' not in df.columns:
        def _complete(s):
            v = STOCK_DB.get(s, {})
            score = 0
            for k in ['name','industry','sub','position','peers','moat','risk','fair_mult','customers','ai_customers']:
                if v.get(k): score += 10
            return f"{min(score,100)}%"
        df['資料完整度'] = df['代碼'].map(_complete)
    return df

# ===== V236.0 PRICE DATABASE EXPANSION END =====



# ===== V237.0 GLOBAL DETAIL EXPANDER + MORE STOCK PRICE COVERAGE START =====
# 目標：
# 1) 全球競爭力頁面將「主要客戶、競爭者、護城河、風險」改為可展開完整閱讀，避免 dataframe 欄位被截斷。
# 2) 繼續擴充熱門類股個股資料，讓更多股票能查詢現價與三段估值區間。

APP_VERSION = "V237.0 Global Detail Expander + More Stock Coverage"

V237_EXTRA_STOCKS = {
    # 金融/證券/保險
    "2883.TW": {"name":"開發金", "industry":"金融", "sub":"金控/證券/壽險", "rank":"大型金控", "power":"★★★☆☆", "position":"證券、壽險與投資型金控", "peers":"富邦金、國泰金、元大金、中信金", "moat":"中：金融通路、證券與投資平台", "risk":"利率、股債市波動、壽險淨值", "fair_mult":1.02, "customers":"個人金融、企業金融、證券、壽險與財富管理客戶", "ai_customers":"金融科技與AI客服間接受惠", "theme_text":"金融、金控、證券、壽險", "chain_position":"金融服務", "market_share":"台灣大型金控"},
    "2886.TW": {"name":"兆豐金", "industry":"金融", "sub":"公股銀行金控", "rank":"公股大型金控", "power":"★★★★☆", "position":"外匯、企金與銀行型金控", "peers":"第一金、華南金、合庫金、彰銀", "moat":"中高：公股資源、外匯與企金客戶", "risk":"利差、信用風險、政策", "fair_mult":1.03, "customers":"企業金融、外匯、個人金融與財富管理客戶", "ai_customers":"金融科技間接受惠", "theme_text":"金融、公股金控、銀行", "chain_position":"金融服務", "market_share":"台灣公股大型金控"},
    "2887.TW": {"name":"台新金", "industry":"金融", "sub":"金控/銀行", "rank":"銀行金控", "power":"★★★☆☆", "position":"消金、企金、財管與金融科技金控", "peers":"玉山金、中信金、永豐金", "moat":"中：零售銀行、信用卡與財管通路", "risk":"利差、信用風險、併購整合", "fair_mult":1.02, "customers":"個人金融、信用卡、企業金融與財富管理客戶", "ai_customers":"金融科技與AI客服間接受惠", "theme_text":"金融、銀行、財管", "chain_position":"金融服務", "market_share":"台灣銀行金控"},
    "2890.TW": {"name":"永豐金", "industry":"金融", "sub":"金控/銀行/證券", "rank":"銀行金控", "power":"★★★☆☆", "position":"銀行、證券與財管服務金控", "peers":"玉山金、台新金、元大金", "moat":"中：銀行通路與證券財管平台", "risk":"利差、股市成交量、信用風險", "fair_mult":1.02, "customers":"個人金融、企業金融、證券與財富管理客戶", "ai_customers":"金融科技間接受惠", "theme_text":"金融、銀行、證券", "chain_position":"金融服務", "market_share":"台灣銀行金控"},
    "2891.TW": {"name":"中信金", "industry":"金融", "sub":"金控/銀行/壽險", "rank":"大型民營金控", "power":"★★★★☆", "position":"銀行、壽險、信用卡與財富管理大型金控", "peers":"富邦金、國泰金、玉山金、兆豐金", "moat":"中高：銀行通路、信用卡、財管與品牌", "risk":"利率、壽險淨值、信用風險", "fair_mult":1.03, "customers":"個人金融、企業金融、信用卡、壽險與財富管理客戶", "ai_customers":"金融科技與AI客服間接受惠", "theme_text":"金融、金控、銀行、壽險", "chain_position":"金融服務", "market_share":"台灣大型民營金控"},
    "2882.TW": {"name":"國泰金", "industry":"金融", "sub":"金控/壽險/銀行", "rank":"大型金控", "power":"★★★★☆", "position":"壽險、銀行、證券與資產管理大型金控", "peers":"富邦金、中信金、開發金", "moat":"高：保險品牌、金融通路與資產規模", "risk":"利率、匯率、股債市波動、壽險淨值", "fair_mult":1.03, "customers":"壽險、個人金融、企業金融、信用卡與財富管理客戶", "ai_customers":"金融科技與AI客服間接受惠", "theme_text":"金融、金控、壽險、銀行", "chain_position":"金融服務", "market_share":"台灣大型金控"},
    "2881.TW": {"name":"富邦金", "industry":"金融", "sub":"金控/壽險/銀行/證券", "rank":"大型金控", "power":"★★★★☆", "position":"壽險、銀行、證券與產險大型金控", "peers":"國泰金、中信金、開發金", "moat":"高：金融通路、保險品牌與資產規模", "risk":"利率、壽險淨值、股債市波動", "fair_mult":1.03, "customers":"壽險、產險、銀行、證券與財富管理客戶", "ai_customers":"金融科技與AI客服間接受惠", "theme_text":"金融、金控、壽險、銀行", "chain_position":"金融服務", "market_share":"台灣大型金控"},

    # 航運/航空/物流
    "2615.TW": {"name":"萬海", "industry":"航運", "sub":"貨櫃航運", "rank":"亞洲區域貨櫃航商", "power":"★★★☆☆", "position":"亞洲區域航線與貨櫃運輸服務商", "peers":"長榮、陽明、ONE、HMM", "moat":"中：航線網路、船隊與區域服務", "risk":"運價循環、油價、地緣政治、船舶供給", "fair_mult":1.04, "customers":"進出口商、貨代、零售品牌、製造業與物流客戶", "ai_customers":"AI硬體供應鏈海運需求間接受惠", "theme_text":"航運、貨櫃、全球貿易", "chain_position":"下游運輸服務", "market_share":"亞洲貨櫃航商"},
    "2609.TW": {"name":"陽明", "industry":"航運", "sub":"貨櫃航運", "rank":"全球貨櫃航商", "power":"★★★☆☆", "position":"遠洋貨櫃運輸與全球航線服務商", "peers":"長榮、萬海、Maersk、MSC、Hapag-Lloyd", "moat":"中：船隊、航線與聯盟資源", "risk":"運價循環、油價、船舶供給、地緣政治", "fair_mult":1.04, "customers":"進出口商、貨代、零售品牌、製造業與物流客戶", "ai_customers":"AI硬體供應鏈海運需求間接受惠", "theme_text":"航運、貨櫃、全球貿易", "chain_position":"下游運輸服務", "market_share":"全球貨櫃航商"},
    "2603.TW": {"name":"長榮", "industry":"航運", "sub":"貨櫃航運", "rank":"全球大型貨櫃航商", "power":"★★★★☆", "position":"全球遠洋貨櫃航運與物流服務商", "peers":"陽明、萬海、Maersk、MSC、CMA CGM", "moat":"中高：船隊規模、航線網路與財務體質", "risk":"運價循環、油價、船舶供給、地緣政治", "fair_mult":1.05, "customers":"全球進出口商、貨代、零售品牌、製造業與物流客戶", "ai_customers":"AI硬體供應鏈海運需求間接受惠", "theme_text":"航運、貨櫃、全球貿易", "chain_position":"下游運輸服務", "market_share":"全球大型貨櫃航商"},
    "2610.TW": {"name":"華航", "industry":"航空", "sub":"航空客運/貨運", "rank":"台灣主要航空公司", "power":"★★★☆☆", "position":"客運、貨運與航空服務供應商", "peers":"長榮航、星宇航空、國際航空公司", "moat":"中：航權、機隊、貨運與品牌", "risk":"油價、匯率、景氣、旅遊需求", "fair_mult":1.03, "customers":"旅客、航空貨運、物流、電子零組件與跨境商務客戶", "ai_customers":"AI伺服器與電子零組件空運需求間接受惠", "theme_text":"航空、旅遊、航空貨運", "chain_position":"運輸服務", "market_share":"台灣主要航空公司"},
    "2618.TW": {"name":"長榮航", "industry":"航空", "sub":"航空客運/貨運", "rank":"台灣主要航空公司", "power":"★★★☆☆", "position":"客運、貨運與航空服務供應商", "peers":"華航、星宇航空、國際航空公司", "moat":"中：航權、機隊、服務品牌與貨運能力", "risk":"油價、匯率、景氣、旅遊需求", "fair_mult":1.03, "customers":"旅客、航空貨運、物流、電子零組件與跨境商務客戶", "ai_customers":"AI伺服器與電子零組件空運需求間接受惠", "theme_text":"航空、旅遊、航空貨運", "chain_position":"運輸服務", "market_share":"台灣主要航空公司"},
    "2646.TW": {"name":"星宇航空", "industry":"航空", "sub":"航空客運", "rank":"新興航空品牌", "power":"★★★☆☆", "position":"國際客運與航空服務品牌", "peers":"華航、長榮航、國際航空公司", "moat":"中：品牌、航線布局與服務定位", "risk":"油價、匯率、展線成本、旅遊需求", "fair_mult":1.04, "customers":"旅客、商務客、航空旅遊與國際航線客戶", "ai_customers":"無直接AI客戶", "theme_text":"航空、旅遊、消費服務", "chain_position":"運輸服務", "market_share":"台灣新興航空品牌"},

    # 鋼鐵/塑化/材料
    "2002.TW": {"name":"中鋼", "industry":"鋼鐵", "sub":"一貫作業鋼廠", "rank":"台灣鋼鐵龍頭", "power":"★★★★☆", "position":"熱軋、冷軋、鋼板、線材與高值化鋼材供應商", "peers":"寶鋼、浦項、JFE、新日鐵、台塑集團鋼鐵供應鏈", "moat":"中高：規模、產品線、下游客戶與政策地位", "risk":"景氣循環、鐵礦砂/煤價、匯率、碳成本", "fair_mult":1.02, "customers":"汽車、營建、機械、家電、造船、能源與製造業客戶", "ai_customers":"資料中心機電與機房建設間接受惠", "theme_text":"鋼鐵、基建、製造業、碳中和", "chain_position":"上游鋼材", "market_share":"台灣鋼鐵龍頭"},
    "2014.TW": {"name":"中鴻", "industry":"鋼鐵", "sub":"熱軋/冷軋鋼品", "rank":"鋼材供應商", "power":"★★★☆☆", "position":"熱軋、冷軋與鋼管鋼材供應商", "peers":"中鋼、燁輝、東和鋼鐵", "moat":"中：中鋼集團資源與鋼材客戶", "risk":"鋼價循環、原料成本、需求波動", "fair_mult":1.01, "customers":"營建、機械、製造業、鋼管與加工客戶", "ai_customers":"資料中心建設間接受惠有限", "theme_text":"鋼鐵、製造業、基建", "chain_position":"中游鋼材加工", "market_share":"台灣鋼材供應商"},
    "2027.TW": {"name":"大成鋼", "industry":"鋼鐵", "sub":"不銹鋼/鋁品通路", "rank":"金屬通路供應商", "power":"★★★☆☆", "position":"不銹鋼、鋁品與金屬材料通路服務商", "peers":"美國金屬通路商、燁聯、華新", "moat":"中：北美通路、庫存管理與客戶基礎", "risk":"金屬價格、利率、庫存評價、匯率", "fair_mult":1.02, "customers":"北美製造業、建材、工業材料與金屬加工客戶", "ai_customers":"資料中心建設間接受惠有限", "theme_text":"鋼鐵、不銹鋼、鋁、北美基建", "chain_position":"中下游金屬通路", "market_share":"北美金屬通路供應商"},
    "1301.TW": {"name":"台塑", "industry":"塑化", "sub":"PVC/塑膠原料", "rank":"台灣塑化龍頭之一", "power":"★★★★☆", "position":"PVC、PE、塑膠原料與石化產品供應商", "peers":"台化、南亞、Formosa Plastics USA、國際石化廠", "moat":"中高：垂直整合、規模與石化集團資源", "risk":"油價、石化循環、中國供給、碳成本", "fair_mult":1.02, "customers":"塑膠加工、建材、包材、工業材料與化工客戶", "ai_customers":"無直接AI客戶", "theme_text":"塑化、原物料、景氣循環", "chain_position":"上游石化原料", "market_share":"台灣塑化龍頭之一"},
    "1303.TW": {"name":"南亞", "industry":"塑化/電子材料", "sub":"塑膠/銅箔基板/電子材料", "rank":"塑化與電子材料大廠", "power":"★★★★☆", "position":"塑膠、化纖、電子材料、銅箔基板與化工產品供應商", "peers":"台塑、台化、台光電、聯茂、國際電子材料廠", "moat":"中高：集團整合、材料技術與客戶基礎", "risk":"石化循環、電子材料需求、油價與碳成本", "fair_mult":1.03, "customers":"電子材料、PCB、塑膠加工、化纖、工業材料客戶", "ai_customers":"AI伺服器PCB/材料間接受惠", "theme_text":"塑化、電子材料、PCB材料、AI伺服器", "chain_position":"上游材料", "market_share":"台灣塑化與電子材料大廠"},
    "1326.TW": {"name":"台化", "industry":"塑化/紡纖", "sub":"芳香烴/化纖/塑化", "rank":"台灣塑化大廠", "power":"★★★★☆", "position":"芳香烴、化纖、塑膠與石化產品供應商", "peers":"台塑、南亞、國際石化與化纖廠", "moat":"中高：垂直整合、集團資源與規模", "risk":"油價、石化循環、中國供給、碳成本", "fair_mult":1.02, "customers":"化纖、紡織、塑膠加工、工業材料與石化客戶", "ai_customers":"無直接AI客戶", "theme_text":"塑化、化纖、原物料", "chain_position":"上游石化/化纖", "market_share":"台灣塑化與化纖大廠"},
    "1402.TW": {"name":"遠東新", "industry":"紡纖/材料", "sub":"聚酯/紡纖/投資", "rank":"聚酯與紡纖大廠", "power":"★★★☆☆", "position":"聚酯、紡纖、環保回收材料與多角化投資集團", "peers":"新纖、力麗、國際聚酯廠", "moat":"中：垂直整合、品牌客戶與回收材料布局", "risk":"原料、紡纖景氣、投資收益波動", "fair_mult":1.02, "customers":"運動品牌、服飾、包材、工業材料與通路客戶", "ai_customers":"無直接AI客戶", "theme_text":"紡纖、聚酯、回收材料、消費", "chain_position":"上中游材料/紡纖", "market_share":"台灣聚酯與紡纖大廠"},

    # 食品/通路/消費
    "1216.TW": {"name":"統一", "industry":"食品/通路", "sub":"食品飲料/通路投資", "rank":"台灣食品龍頭", "power":"★★★★☆", "position":"食品飲料、乳品、通路與消費品集團", "peers":"味全、卜蜂、味王、統一超相關通路", "moat":"高：品牌、通路、產品組合與集團資源", "risk":"原物料、消費景氣、食品安全、匯率", "fair_mult":1.03, "customers":"超商、量販、餐飲、家庭消費者與食品通路客戶", "ai_customers":"零售數據與智慧物流間接受惠", "theme_text":"食品、通路、消費、民生必需", "chain_position":"中下游食品與通路", "market_share":"台灣食品龍頭"},
    "2912.TW": {"name":"統一超", "industry":"通路/零售", "sub":"便利商店/零售", "rank":"台灣超商龍頭", "power":"★★★★★", "position":"便利商店、零售通路、物流與生活服務平台", "peers":"全家、萊爾富、全聯、量販通路", "moat":"高：門市密度、品牌、物流與支付服務", "risk":"人事租金成本、消費景氣、展店飽和", "fair_mult":1.04, "customers":"一般消費者、食品飲料品牌、物流、支付與生活服務客戶", "ai_customers":"零售數據、AI補貨與智慧物流間接受惠", "theme_text":"通路、零售、超商、民生消費", "chain_position":"下游零售通路", "market_share":"台灣便利商店龍頭"},
    "5903.TW": {"name":"全家", "industry":"通路/零售", "sub":"便利商店", "rank":"台灣主要超商", "power":"★★★★☆", "position":"便利商店、零售通路與生活服務平台", "peers":"統一超、萊爾富、全聯", "moat":"中高：門市網路、品牌、會員與物流", "risk":"人事租金成本、消費景氣、展店飽和", "fair_mult":1.03, "customers":"一般消費者、食品飲料品牌、支付與物流服務客戶", "ai_customers":"零售數據、AI補貨與智慧物流間接受惠", "theme_text":"通路、零售、超商、民生消費", "chain_position":"下游零售通路", "market_share":"台灣主要便利商店"},
    "2915.TW": {"name":"潤泰全", "industry":"通路/投資", "sub":"流通/投資控股", "rank":"投資控股公司", "power":"★★★☆☆", "position":"流通、紡織與轉投資控股公司", "peers":"潤泰新、統一、遠東新", "moat":"中：通路與投資資產", "risk":"轉投資波動、消費景氣、資產評價", "fair_mult":1.02, "customers":"流通、消費品、轉投資與資產相關客戶", "ai_customers":"無直接AI客戶", "theme_text":"通路、投資控股、消費", "chain_position":"投資控股/流通", "market_share":"投資控股公司"},
    "1101.TW": {"name":"台泥", "industry":"水泥/能源", "sub":"水泥/儲能/能源", "rank":"台灣水泥龍頭", "power":"★★★★☆", "position":"水泥、建材、儲能與能源轉型供應商", "peers":"亞泥、環泥、國際水泥廠", "moat":"中高：品牌、礦權、通路與能源轉型資源", "risk":"營建景氣、煤價、碳成本、海外市場", "fair_mult":1.02, "customers":"營建、基礎建設、建材、儲能與能源服務客戶", "ai_customers":"資料中心儲能/用電間接受惠", "theme_text":"水泥、建材、儲能、能源轉型", "chain_position":"上游建材/能源", "market_share":"台灣水泥龍頭"},
    "1102.TW": {"name":"亞泥", "industry":"水泥/建材", "sub":"水泥/建材", "rank":"台灣水泥主要廠", "power":"★★★☆☆", "position":"水泥、建材與基礎建設材料供應商", "peers":"台泥、環泥、國際水泥廠", "moat":"中：礦權、品牌、通路與建材客戶", "risk":"營建景氣、煤價、碳成本、中國市場", "fair_mult":1.02, "customers":"營建、基礎建設、水泥與建材客戶", "ai_customers":"資料中心建設間接受惠有限", "theme_text":"水泥、建材、基建", "chain_position":"上游建材", "market_share":"台灣水泥主要廠"},

    # 電子與零組件補充
    "2324.TW": {"name":"仁寶", "industry":"AI伺服器/ODM", "sub":"NB ODM/伺服器", "rank":"ODM主要廠", "power":"★★★☆☆", "position":"筆電ODM與伺服器代工供應商", "peers":"廣達、緯創、英業達、鴻海", "moat":"中：ODM規模、品牌客戶與伺服器布局", "risk":"毛利率、PC需求、AI伺服器進度", "fair_mult":1.03, "customers":"全球PC品牌、企業伺服器、雲端與消費電子客戶", "ai_customers":"AI伺服器與邊緣AI PC客戶間接受惠", "theme_text":"ODM、AI伺服器、AI PC", "chain_position":"下游系統組裝", "market_share":"全球NB ODM主要廠"},
    "2376.TW": {"name":"技嘉", "industry":"AI伺服器/品牌", "sub":"主機板/顯卡/伺服器", "rank":"板卡與伺服器品牌", "power":"★★★★☆", "position":"主機板、顯卡、AI伺服器與工作站供應商", "peers":"華碩、微星、Supermicro、廣達", "moat":"中高：板卡設計、品牌通路與伺服器產品線", "risk":"AI訂單波動、顯卡循環、庫存", "fair_mult":1.06, "customers":"AI伺服器、企業IT、電競、通路與資料中心客戶", "ai_customers":"AI伺服器、GPU平台與企業AI客戶", "theme_text":"AI伺服器、主機板、顯卡、AI PC", "chain_position":"中下游系統/品牌", "market_share":"全球板卡品牌與伺服器供應商"},
    "2377.TW": {"name":"微星", "industry":"AI PC/品牌", "sub":"電競PC/主機板/顯卡", "rank":"電競品牌", "power":"★★★★☆", "position":"電競筆電、主機板、顯卡與AI PC品牌", "peers":"華碩、技嘉、Lenovo、Dell", "moat":"中高：電競品牌、板卡設計與通路", "risk":"PC循環、庫存、顯卡需求波動", "fair_mult":1.04, "customers":"電競玩家、通路、企業IT、AI PC與顯卡客戶", "ai_customers":"AI PC、GPU與邊緣AI使用者", "theme_text":"AI PC、電競、主機板、顯卡", "chain_position":"下游品牌/通路", "market_share":"全球電競PC品牌"},
    "2357.TW": {"name":"華碩", "industry":"AI PC/品牌", "sub":"PC/主機板/伺服器", "rank":"全球PC品牌", "power":"★★★★☆", "position":"PC、主機板、電競、AI PC與伺服器品牌", "peers":"Lenovo、HP、Dell、Acer、MSI", "moat":"高：品牌、通路、主機板技術與產品線", "risk":"PC需求、庫存、競爭、匯率", "fair_mult":1.04, "customers":"消費者、企業IT、電競、AI PC、通路與伺服器客戶", "ai_customers":"AI PC、邊緣AI與伺服器客戶", "theme_text":"AI PC、PC品牌、主機板、伺服器", "chain_position":"下游品牌/系統", "market_share":"全球PC品牌"},
    "2353.TW": {"name":"宏碁", "industry":"AI PC/品牌", "sub":"PC品牌/周邊", "rank":"全球PC品牌", "power":"★★★☆☆", "position":"PC、AI PC、顯示器與消費電子品牌", "peers":"華碩、Lenovo、HP、Dell", "moat":"中：品牌、通路與產品線", "risk":"PC需求、價格競爭、庫存", "fair_mult":1.02, "customers":"消費者、企業IT、教育、AI PC與通路客戶", "ai_customers":"AI PC與邊緣AI使用者", "theme_text":"AI PC、PC品牌、消費電子", "chain_position":"下游品牌/通路", "market_share":"全球PC品牌"},
    "2352.TW": {"name":"佳世達", "industry":"電子/系統整合", "sub":"顯示器/醫療/企業解決方案", "rank":"電子製造與解決方案公司", "power":"★★★☆☆", "position":"顯示器、醫療、企業解決方案與電子製造服務商", "peers":"明基材料、群創、ODM同業", "moat":"中：產品線、醫療與企業解決方案布局", "risk":"顯示器需求、轉型成效、毛利率", "fair_mult":1.03, "customers":"企業IT、醫療、顯示器、工業與電子品牌客戶", "ai_customers":"AI醫療與企業AI間接受惠", "theme_text":"醫療、企業解決方案、顯示器", "chain_position":"中下游系統/服務", "market_share":"電子製造與解決方案供應商"},
    "2301.TW": {"name":"光寶科", "industry":"電源管理", "sub":"電源/光電/車用", "rank":"電源與電子零組件大廠", "power":"★★★★☆", "position":"電源供應器、資料中心電源、車用電子與光電零組件供應商", "peers":"台達電、康舒、群電、飛宏", "moat":"中高：電源設計、全球客戶與製造規模", "risk":"毛利率、終端需求、競爭、匯率", "fair_mult":1.05, "customers":"資料中心、PC、車用、工業、雲端與品牌電子客戶", "ai_customers":"AI伺服器電源、資料中心與雲端客戶", "theme_text":"電源管理、AI伺服器、車用電子", "chain_position":"中游電源/零組件", "market_share":"全球電源供應器主要廠"},
    "6412.TW": {"name":"群電", "industry":"電源管理", "sub":"電源供應器", "rank":"電源供應商", "power":"★★★☆☆", "position":"電源供應器、充電器與電源模組供應商", "peers":"台達電、光寶科、康舒、飛宏", "moat":"中：電源設計、客戶基礎與量產能力", "risk":"PC需求、價格競爭、產品組合", "fair_mult":1.03, "customers":"PC品牌、消費電子、工業電源與資料中心相關客戶", "ai_customers":"AI PC與資料中心電源間接受惠", "theme_text":"電源管理、AI PC、消費電子", "chain_position":"中游電源零組件", "market_share":"電源供應器供應商"},
}

try:
    STOCK_DB.update(V237_EXTRA_STOCKS)
    ALIASES.clear()
    for sym, v in STOCK_DB.items():
        ALIASES[sym.upper()] = sym
        ALIASES[sym.split('.')[0]] = sym
        ALIASES[v.get('name', sym)] = sym
        ALIASES[v.get('name', sym).upper()] = sym
    OTC_CODES = {s.split('.')[0] for s in STOCK_DB if s.endswith('.TWO')}
except Exception:
    pass

# 小工具：將「、/，/,」分隔文字做成可閱讀的清單
def v237_split_items(text):
    s = str(text or "待補").replace("，", "、").replace(",", "、").replace("/", "、")
    parts = [p.strip() for p in s.split("、") if p.strip()]
    return parts if parts else ["待補"]

def v237_chip_html(text):
    parts = v237_split_items(text)
    return '<div class="v230-tag-wrap">' + ''.join([f'<span class="v230-tag">{p}</span>' for p in parts]) + '</div>'

def v237_detail_box(title, value, icon="🔎", expanded=False):
    with st.expander(f"{icon} {title}", expanded=expanded):
        st.markdown(v237_chip_html(value), unsafe_allow_html=True)
        st.caption(str(value or "待補"))

def v237_global_detail_panel(row):
    st.markdown("### 競爭力完整資料")
    c1, c2 = st.columns(2)
    with c1:
        v237_detail_box("主要客戶 / 終端客戶", row.get("主要客戶", "待補"), "👥", True)
        v237_detail_box("主要競爭者", row.get("主要競爭者", row.get("競爭者", "待補")), "⚔️", True)
        v237_detail_box("產業鏈位置", row.get("產業鏈位置", "待補"), "🧭", False)
    with c2:
        v237_detail_box("護城河", row.get("護城河", "待補"), "🏰", True)
        v237_detail_box("主要風險", row.get("主要風險", "待補"), "⚠️", True)
        v237_detail_box("AI 客戶 / AI 關聯", row.get("AI客戶", "待補"), "🤖", False)
    st.markdown("### 表格摘要")
    st.dataframe(pd.DataFrame([{
        "產業地位":row.get("產業地位","待補"),
        "主要客戶":row.get("主要客戶","待補"),
        "競爭者":row.get("主要競爭者", row.get("競爭者","待補")),
        "護城河":row.get("護城河","待補"),
        "主要風險":row.get("主要風險","待補"),
        "產業鏈位置":row.get("產業鏈位置","待補")
    }]), use_container_width=True, hide_index=True)

def v230_price_block(symbol):
    d=v230_decision(symbol); sym=d.get("symbol", symbol)
    st.caption(f"資料更新時間：{d.get('updated','N/A')}｜現價來源：{d.get('source','Yahoo Finance')}｜預期報酬率＝(綜合合理價－現價)÷現價。")
    st.markdown(f"## {d.get('name', sym)}（{sym}）")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("投資建議", d.get("action","觀察"))
    c2.metric("現價", v230_fmt(d.get("price", float("nan"))))
    c3.metric("綜合合理價", v230_fmt(d.get("fair", float("nan"))))
    try: ret_txt=f"{float(d.get('ret',0)):.1f}%"
    except Exception: ret_txt="N/A"
    c4.metric("預期報酬", ret_txt)
    p1,p2,p3=st.columns(3)
    p1.metric("安全邊際價", v230_fmt(d.get("cons", float("nan"))))
    p2.metric("合理價值", v230_fmt(d.get("fair", float("nan"))))
    p3.metric("潛在價值", v230_fmt(d.get("opt", float("nan"))))
    df=v230_rows_df(); row=df[df["代碼"]==sym] if not df.empty and "代碼" in df.columns else pd.DataFrame()
    with st.expander("展開更多研究資料", expanded=True):
        if not row.empty:
            r=row.iloc[0].to_dict()
            st.markdown("### 公司基本資料")
            st.markdown(f'<div class="v230-card"><div class="v230-card-title">{r.get("公司","")}｜{r.get("代碼","")}</div><div class="v230-small-muted">主產業：{r.get("產業","")}　｜　子產業：{r.get("子產業","")}　｜　產業鏈位置：{r.get("產業鏈位置","待補")}</div><div style="margin-top:10px;">{v230_tag_html(r.get("主題標籤",""))}</div></div>', unsafe_allow_html=True)
            v237_global_detail_panel(r)
        else:
            st.info("此個股仍在資料庫補齊中，後續會補上產業鏈位置、主題標籤、主要客戶、競爭者與護城河。")

def competition_page():
    v230_css(); st.header("🌏 全球競爭力")
    df=v230_rows_df()
    themes=["全部"]+sorted(set([p.strip() for s in df["主題標籤"].fillna("").astype(str) for p in s.replace("，","、").split("、") if p.strip()]))
    c0,c1,c2,c3=st.columns(4)
    with c0: theme=st.selectbox("主題標籤", themes, key="v237_global_theme")
    if theme!="全部": df=df[df["主題標籤"].astype(str).str.contains(theme, na=False)]
    with c1: ind=st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v237_global_ind")
    dff=df[df["產業"]==ind]
    with c2: sub=st.selectbox("子產業", sorted(dff["子產業"].dropna().unique()), key="v237_global_sub")
    dff=dff[dff["子產業"]==sub]
    labels={f"{r['公司']} / {r['代碼']}":r["代碼"] for _,r in dff.iterrows()}
    with c3: picked=st.selectbox("個股（選到即查詢）", list(labels.keys()), key="v237_global_stock")
    code=labels[picked]; st.session_state["v227_active_symbol"]=code
    row=dff[dff["代碼"]==code].iloc[0].to_dict()
    st.markdown(f"## {row['公司']}（{row['代碼']}）")
    g1,g2,g3,g4=st.columns(4)
    try: ai_txt=f"{int(row['AI受惠度'])}/10" if int(row["AI受惠度"])>0 else "非AI主題"
    except Exception: ai_txt="N/A"
    g1.metric("全球排名", row.get("全球排名","待補")); g2.metric("AI受惠度", ai_txt); g3.metric("全球競爭力", row.get("全球競爭力","待補")); g4.metric("全球市占率", row.get("全球市占率","待補"))
    st.markdown(v230_tag_html(row.get("主題標籤","")), unsafe_allow_html=True)
    v237_global_detail_panel(row)
    try:
        st.markdown("---"); v224_ai_score_explanation()
    except Exception:
        pass

def industry_page():
    v230_css(); st.header("🏭 產業分析")
    df=v230_rows_df()
    c1,c2,c3=st.columns(3)
    with c1: ind=st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v237_industry_ind")
    dff=df[df["產業"]==ind]
    with c2: sub=st.selectbox("子產業", sorted(dff["子產業"].dropna().unique()), key="v237_industry_sub")
    dff=dff[dff["子產業"]==sub]
    labels={f"{r['公司']} / {r['代碼']}":r["代碼"] for _,r in dff.iterrows()}
    with c3: picked=st.selectbox("個股（選到即查詢）", list(labels.keys()), key="v237_industry_stock")
    code=labels[picked]; st.session_state["v227_active_symbol"]=code
    row=dff[dff["代碼"]==code].iloc[0].to_dict()
    meta=V224_INDUSTRY_META.get(ind, {"規模":"待補","成長率":"待補","AI關聯度":"待補","說明":"待補"})
    k1,k2,k3,k4=st.columns(4); k1.metric("產業規模", meta.get("規模","待補")); k2.metric("成長率", meta.get("成長率","待補")); k3.metric("AI關聯度", meta.get("AI關聯度","待補")); k4.metric("同產業公司", len(dff))
    st.info(meta.get("說明",""))
    st.markdown("### 公司基本資料")
    st.markdown(f'<div class="v230-card"><div class="v230-card-title">{row.get("公司","")}｜{row.get("代碼","")}</div><div class="v230-small-muted">主產業：{row.get("產業","")}　｜　子產業：{row.get("子產業","")}　｜　產業鏈位置：{row.get("產業鏈位置","待補")}</div><div style="margin-top:10px;">{v230_tag_html(row.get("主題標籤",""))}</div></div>', unsafe_allow_html=True)
    v237_global_detail_panel(row)
    st.markdown("### 同產業主要公司")
    cols=["公司","代碼","子產業","產業鏈位置","主要客戶","AI受惠度","全球競爭力","產業地位"]
    st.dataframe(dff[[c for c in cols if c in dff.columns]], use_container_width=True, hide_index=True)

# ===== V237.0 GLOBAL DETAIL EXPANDER + MORE STOCK PRICE COVERAGE END =====


# ===== V238.0 MORE PRICE COVERAGE + GLOBAL DETAIL DROPDOWN START =====
APP_VERSION = "V238.0 More Price Coverage + Global Detail Dropdown"

# V238 目標：繼續擴充各類股個股，讓使用者先查得到估值區間，再往下看產業/客戶/競爭者。
# 欄位採用簡化工廠函式，避免未來擴充 500~1000 檔時維護困難。
def _v238_stock(name, industry, sub, rank, power, position, peers, moat, risk, fair_mult,
                theme_text="一般產業", chain_position="產業鏈位置待補", market_share="待補", customers="待補", ai_customers="待補"):
    return {
        "name": name, "industry": industry, "sub": sub, "rank": rank, "power": power,
        "position": position, "peers": peers, "moat": moat, "risk": risk, "fair_mult": fair_mult,
        "theme_text": theme_text, "chain_position": chain_position, "market_share": market_share,
        "customers": customers, "ai_customers": ai_customers
    }

V238_EXTRA_STOCKS = {
    # 塑化 / 化工 / 橡膠
    "1301.TW": _v238_stock("台塑","塑化","PVC/石化原料","台灣石化龍頭","★★★★☆","PVC、塑化原料與石化上游集團","台化、南亞、台塑化、國際石化廠","中高：一貫化、規模與通路","油價、景氣循環、碳排成本",1.00,"塑化、原物料、循環股","石化上游","台灣PVC主要廠","工業製造、建材、塑膠加工客戶"),
    "1303.TW": _v238_stock("南亞","塑化","塑膠/電子材料","台灣塑化與電子材料大廠","★★★★☆","塑膠、化纖、電子材料與銅箔基板相關供應商","台塑、台化、長春、國際材料廠","中高：材料整合、集團資源與電子材料布局","石化循環、電子材料景氣、原料成本",1.01,"塑化、電子材料、PCB材料","上游材料","塑化與電子材料主要供應商","PCB、電子材料、塑膠加工與工業客戶","AI伺服器PCB/材料間接受惠"),
    "1326.TW": _v238_stock("台化","塑化","芳香烴/化纖","台灣石化與化纖大廠","★★★★☆","芳香烴、塑化、化纖與石化產品供應商","台塑、南亞、國際石化廠","中：規模、集團資源、產品線","石化循環、油價、需求疲弱",0.99,"塑化、化纖、循環股","石化中上游","石化與化纖主要供應商","紡織、塑膠、工業與化工客戶"),
    "6505.TW": _v238_stock("台塑化","塑化","煉油/油品/石化","台灣煉油石化主要廠","★★★★☆","煉油、油品與石化原料供應商","中油、國際煉油與石化廠","中高：煉油規模、集團整合","油價、煉油利差、景氣循環",1.00,"塑化、油品、景氣循環","石化上游","台灣煉油主要供應商","油品、石化、工業與交通需求客戶"),
    "1304.TW": _v238_stock("台聚","塑化","PE/EVA","塑膠原料供應商","★★★☆☆","PE、EVA與塑膠原料供應商","亞聚、台塑、國際石化廠","中：產品與通路","石化循環、價格波動",0.98,"塑化、EVA","石化中游","PE/EVA供應商","塑膠加工、包材、工業客戶"),
    "1305.TW": _v238_stock("華夏","塑化","PVC","PVC供應商","★★★☆☆","PVC與塑膠原料供應商","台塑、聯成、國際PVC廠","中：PVC產品與通路","PVC價差、景氣循環",0.98,"塑化、PVC","石化中游","PVC供應商","建材、塑膠加工、工業客戶"),
    "1314.TW": _v238_stock("中石化","塑化","CPL/尼龍原料","石化原料供應商","★★★☆☆","CPL、尼龍與石化原料相關供應商","台化、國際化工廠","中：石化原料產品線","產品價差、景氣循環、轉投資波動",0.97,"塑化、尼龍原料","石化中游","石化原料供應商","紡織、塑膠與工業客戶"),
    "2105.TW": _v238_stock("正新","橡膠/輪胎","輪胎","台灣輪胎龍頭","★★★★☆","汽車、機車與自行車輪胎品牌製造商","建大、普利司通、米其林、固特異","中高：品牌、通路與量產規模","原料成本、車市景氣、匯率",1.02,"輪胎、汽車零組件","下游品牌/製造","全球輪胎品牌之一","汽車通路、機車、自行車與替換胎市場"),
    "2106.TW": _v238_stock("建大","橡膠/輪胎","輪胎","輪胎主要廠","★★★☆☆","自行車、機車與汽車輪胎供應商","正新、國際輪胎廠","中：品牌與輪胎產品線","橡膠成本、需求循環",1.00,"輪胎、自行車、汽車零組件","下游品牌/製造","輪胎供應商","自行車、機車、汽車與替換胎客戶"),

    # 紡織 / 服飾
    "1402.TW": _v238_stock("遠東新","紡織/材料","聚酯/紡織/回收材料","台灣聚酯與紡織大廠","★★★★☆","聚酯、紡織、回收材料與通路投資集團","新纖、力麗、國際聚酯廠","中高：垂直整合、回收材料與集團資源","原料成本、消費景氣、匯率",1.02,"紡織、循環經濟、回收材料","上中下游整合","聚酯與紡織主要供應商","國際運動品牌、紡織成衣與包材客戶"),
    "1476.TW": _v238_stock("儒鴻","紡織/成衣","機能服飾/成衣代工","機能成衣龍頭","★★★★★","高階機能布與成衣代工供應商","聚陽、Makalot、國際成衣代工廠","高：研發、客戶認證、快速量產","品牌客戶拉貨、匯率、人力成本",1.06,"機能服飾、成衣代工、品牌供應鏈","中下游成衣代工","高階成衣代工主要廠","Nike、Lululemon、Athleta、國際運動/休閒品牌"),
    "1477.TW": _v238_stock("聚陽","紡織/成衣","成衣代工","成衣代工主要廠","★★★★☆","快時尚、運動與休閒成衣代工供應商","儒鴻、豐泰、國際成衣代工廠","中高：客戶基礎、海外產能與交期管理","消費景氣、工資、匯率",1.05,"成衣代工、品牌供應鏈","下游成衣代工","成衣代工主要廠","Gap、Target、Walmart、國際服飾品牌"),
    "9910.TW": _v238_stock("豐泰","紡織/鞋業","運動鞋代工","運動鞋代工主要廠","★★★★☆","運動鞋與鞋材製造供應商","寶成、鈺齊-KY、國際鞋業代工廠","中高：Nike供應鏈、製程與海外產能","品牌庫存、工資、匯率",1.04,"運動鞋、品牌供應鏈","下游鞋業代工","運動鞋代工主要廠","Nike等國際運動品牌"),
    "9802.TW": _v238_stock("鈺齊-KY","紡織/鞋業","戶外鞋代工","戶外鞋代工供應商","★★★☆☆","戶外機能鞋與運動鞋代工供應商","豐泰、寶成、國際鞋業代工廠","中：戶外鞋製程與品牌客戶","消費景氣、品牌庫存、匯率",1.03,"戶外鞋、成衣鞋業","下游鞋業代工","戶外鞋代工供應商","國際戶外與運動品牌"),

    # 電機 / 電纜 / 車用 / 工具機
    "1504.TW": _v238_stock("東元","電機/能源","馬達/電力設備","台灣馬達與電機大廠","★★★★☆","馬達、電力設備、電動車動力與節能系統供應商","士電、大同、ABB、Siemens","中高：馬達技術、品牌與電力設備基礎","原料、景氣、電動車導入時程",1.05,"重電、馬達、節能、電動車","中游電機設備","馬達與電力設備主要廠","工業、自動化、電動車、資料中心與能源客戶","資料中心節能/電力間接受惠"),
    "1503.TW": _v238_stock("士電","重電/電網","重電/電力設備","台灣重電主要廠","★★★★☆","變壓器、配電盤、馬達與電力設備供應商","華城、中興電、亞力、ABB、Siemens","中高：重電認證、台電與工程客戶","政策節奏、交期、原料成本",1.08,"重電、電網、台電強韌電網","中游重電設備","台灣重電主要供應商","台電、電力工程、工業與資料中心客戶","AI資料中心用電需求間接受惠"),
    "1514.TW": _v238_stock("亞力","重電/電網","配電盤/變電設備","電力設備供應商","★★★★☆","配電盤、變電設備與電力工程供應商","華城、中興電、士電","中：電力設備認證與工程經驗","政策節奏、接單波動、原料成本",1.08,"重電、電網、台電強韌電網","中游電力設備","電力設備供應商","台電、電力工程、工業與資料中心客戶","AI資料中心用電需求間接受惠"),
    "1605.TW": _v238_stock("華新","電線電纜/不銹鋼","電纜/不銹鋼","電纜與不銹鋼大廠","★★★★☆","電線電纜、不銹鋼與電力工程材料供應商","大亞、華榮、國際不銹鋼廠","中高：電纜通路、材料與工程需求","銅鎳價格、景氣、匯率",1.03,"電線電纜、重電、基建","上游材料/電纜","台灣電線電纜主要廠","台電、工程、工業、不銹鋼與電纜客戶"),
    "1609.TW": _v238_stock("大亞","電線電纜/能源","電線電纜/儲能","電纜與能源題材廠","★★★☆☆","電線電纜、能源工程與儲能相關供應商","華新、華榮、億泰","中：電纜通路與能源轉型布局","銅價、政策、儲能案場進度",1.05,"電線電纜、儲能、電網","上游電纜/能源工程","電線電纜供應商","台電、工程、再生能源與工業客戶","資料中心/電網需求間接受惠"),
    "4526.TWO": _v238_stock("東台","工具機/自動化","工具機/設備","工具機主要廠","★★★☆☆","工具機、自動化設備與加工設備供應商","程泰、亞崴、瀧澤科、日德工具機廠","中：工具機產品線與海外通路","景氣循環、中國競爭、接單波動",1.02,"工具機、自動化、機器人","中游設備","工具機供應商","汽車、航太、精密加工與工業客戶"),
    "2049.TW": _v238_stock("上銀","自動化/機器人","線性滑軌/機器人","全球傳動元件主要廠","★★★★☆","線性傳動、滾珠螺桿與工業機器人供應商","THK、NSK、Bosch Rexroth、台灣精銳","中高：精密傳動、品牌與全球通路","工具機循環、中國競爭、匯率",1.05,"機器人、自動化、工具機","上游精密傳動","全球線性傳動主要廠","工具機、自動化、半導體設備與機器人客戶","機器人/自動化間接受惠"),

    # 車用 / 電動車
    "2201.TW": _v238_stock("裕隆","汽車/車用","汽車製造/轉投資","台灣汽車集團","★★★☆☆","汽車製造、品牌代理與轉投資集團","中華車、和泰車、國際車廠","中：通路、品牌合作與轉投資","車市景氣、轉型成效、競爭",1.00,"汽車、電動車、轉投資","下游整車/通路","台灣汽車集團","Nissan、Luxgen、汽車消費市場"),
    "2204.TW": _v238_stock("中華車","汽車/車用","商用車/汽車製造","台灣汽車製造商","★★★☆☆","商用車、乘用車與汽車製造供應商","裕隆、和泰車、國瑞、國際車廠","中：品牌合作與商用車通路","車市景氣、競爭、政策",1.02,"汽車、商用車、電動車","下游整車製造","台灣汽車製造商","Mitsubishi、商用車與乘用車市場"),
    "2207.TW": _v238_stock("和泰車","汽車/車用","汽車代理/通路","台灣汽車代理龍頭","★★★★★","Toyota、Lexus汽車代理與相關服務集團","裕隆、中華車、汎德永業、國際車廠代理","高：品牌代理、通路、售後服務與金融服務","車市景氣、匯率、供車狀況",1.05,"汽車通路、消費、金融服務","下游代理通路","台灣汽車銷售龍頭","Toyota、Lexus、台灣汽車消費市場"),
    "2227.TW": _v238_stock("裕日車","汽車/車用","汽車代理/製造","Nissan代理與汽車銷售","★★★☆☆","Nissan汽車代理、銷售與相關服務","和泰車、裕隆、中華車","中：品牌代理與通路","車市景氣、品牌競爭、匯率",1.01,"汽車、通路","下游代理通路","汽車代理商","Nissan、汽車消費市場"),
    "2231.TW": _v238_stock("為升","車用電子","胎壓偵測/車用零件","車用電子供應商","★★★☆☆","胎壓偵測器與車用電子零組件供應商","同致、車王電、國際車用零件廠","中：車用認證與零組件設計","車市循環、客戶導入、競爭",1.04,"車用電子、TPMS","上游車用零件","車用零件供應商","車廠、售後維修與車用電子客戶"),
    "2233.TW": _v238_stock("宇隆","車用/精密零件","車用精密零件","車用精密零件供應商","★★★☆☆","車用與工業精密金屬零件供應商","和大、劍麟、國際車用零件廠","中：精密加工與車用認證","車市景氣、匯率、客戶集中",1.03,"車用零件、精密加工","上游車用零件","車用零件供應商","車廠Tier 1、工業與精密零件客戶"),

    # 面板 / 顯示 / 電子通路
    "2409.TW": _v238_stock("友達","面板/顯示","面板/車用顯示","台灣面板主要廠","★★★☆☆","顯示面板、車用顯示與垂直場域解決方案供應商","群創、LG Display、BOE、Samsung Display","中：顯示技術、車用與場域應用","面板循環、價格競爭、庫存",0.98,"面板、車用顯示、Micro LED","上游面板","全球面板供應商","品牌電視、IT、車用與商用顯示客戶"),
    "3481.TW": _v238_stock("群創","面板/顯示","TFT-LCD/車用面板","台灣面板主要廠","★★★☆☆","TFT-LCD、車用、電視與IT顯示面板供應商","友達、BOE、LG Display、Samsung Display","中：面板產能、車用與工控應用","面板價格、景氣循環、庫存",0.97,"面板、車用顯示、顯示器","上游面板","全球面板供應商","電視品牌、IT品牌、車用與工控顯示客戶"),
    "6116.TW": _v238_stock("彩晶","面板/顯示","中小尺寸面板","中小尺寸面板供應商","★★☆☆☆","中小尺寸顯示面板供應商","友達、群創、天馬、BOE","低中：面板產能與利基應用","面板循環、價格競爭",0.96,"面板、中小尺寸顯示","上游面板","中小尺寸面板供應商","手機、工控、車用與顯示模組客戶"),
    "2347.TW": _v238_stock("聯強","電子通路","IT通路/代理","亞太電子通路大廠","★★★★☆","資訊、通訊、半導體與消費電子通路商","大聯大、文曄、神州數碼","中高：通路、物流與品牌代理","景氣循環、庫存、匯率",1.02,"電子通路、IT消費","下游通路","亞太IT通路主要商","IT品牌、企業、消費通路與零售客戶"),
    "3702.TW": _v238_stock("大聯大","電子通路","半導體通路","全球半導體通路大廠","★★★★☆","半導體元件代理、通路與供應鏈服務商","文曄、艾睿、安富利","中高：代理線、客戶基礎與供應鏈管理","半導體景氣、庫存、匯率",1.03,"半導體通路、電子零組件","中下游通路","全球半導體通路主要商","IC設計、電子製造、ODM/OEM客戶","AI伺服器零組件通路間接受惠"),
    "3036.TW": _v238_stock("文曄","電子通路","半導體通路","半導體通路主要商","★★★★☆","半導體元件代理與供應鏈服務商","大聯大、艾睿、安富利","中高：代理產品線與併購整合","半導體庫存、景氣循環、匯率",1.03,"半導體通路、IC代理","中下游通路","半導體通路主要商","電子製造、IC設計、汽車與工業客戶","AI/車用半導體通路間接受惠"),

    # 電信 / 網路 / 系統整合
    "2412.TW": _v238_stock("中華電","電信/網路","電信營運商","台灣電信龍頭","★★★★★","行動、固網、寬頻、IDC與雲端服務供應商","台灣大、遠傳、亞太電信","高：頻譜、網路、客戶與現金流","價格競爭、資本支出、監管",1.03,"電信、IDC、雲端、5G","下游電信服務","台灣電信龍頭","企業、個人用戶、政府與IDC客戶","IDC/AI雲端間接受惠"),
    "3045.TW": _v238_stock("台灣大","電信/網路","電信/媒體/電商","台灣電信主要業者","★★★★☆","行動通信、寬頻、媒體與電商服務供應商","中華電、遠傳","中高：電信客戶、頻譜與媒體電商整合","競爭、資本支出、整合風險",1.02,"電信、5G、媒體電商","下游電信服務","台灣電信主要業者","個人、企業、媒體與電商用戶"),
    "4904.TW": _v238_stock("遠傳","電信/網路","電信/企業ICT","台灣電信主要業者","★★★★☆","行動通信、企業ICT、雲端與資安服務供應商","中華電、台灣大","中高：頻譜、企業客戶與ICT方案","競爭、資本支出、整合風險",1.02,"電信、5G、企業ICT、雲端","下游電信服務","台灣電信主要業者","個人、企業、政府與雲端ICT客戶","企業雲端/AI間接受惠"),
    "2395.TW": _v238_stock("研華","工業電腦","IPC/邊緣運算","全球工業電腦龍頭","★★★★★","工業電腦、邊緣運算、IoT與嵌入式平台供應商","凌華、樺漢、Kontron、Advantech同業","高：品牌、通路、工業客戶與產品平台","工業景氣、庫存、匯率",1.08,"工業電腦、邊緣AI、IoT、自動化","中游IPC平台","全球工業電腦龍頭","工業自動化、醫療、交通、零售與邊緣AI客戶","邊緣AI/自動化受惠"),
    "6414.TW": _v238_stock("樺漢","工業電腦","IPC/系統整合","工業電腦主要廠","★★★★☆","工業電腦、嵌入式系統與產業電腦解決方案供應商","研華、凌華、Kontron","中高：集團資源、客製化與系統整合","併購整合、景氣循環、毛利",1.05,"工業電腦、邊緣AI、IoT","中游IPC/系統整合","工業電腦主要供應商","工業、交通、醫療、零售與邊緣運算客戶","邊緣AI/智慧製造間接受惠"),
    "8114.TWO": _v238_stock("振樺電","工業電腦/POS","POS/商用電腦","POS主要供應商","★★★☆☆","POS、商用電腦與零售自動化設備供應商","飛捷、研華、國際POS廠","中：POS品牌與客戶基礎","零售景氣、通路庫存、競爭",1.03,"POS、零售科技、工業電腦","下游商用設備","POS供應商","零售、餐飲、物流與商用自動化客戶"),
    "6206.TW": _v238_stock("飛捷","工業電腦/POS","POS/商用電腦","POS供應商","★★★☆☆","POS、商用電腦與工業電腦供應商","振樺電、研華、國際POS廠","中：POS產品與通路","零售需求、價格競爭",1.02,"POS、零售科技、商用電腦","下游商用設備","POS供應商","零售、餐飲與商用設備客戶"),

    # 金融續補
    "2883.TW": _v238_stock("開發金","金融","金控/證券/壽險","台灣金控公司","★★★☆☆","證券、壽險、銀行與私募投資金控","富邦金、國泰金、中信金、元大金","中：金融平台與投資業務","利率、資本市場、投資評價",1.00,"金融、金控、證券壽險","金融服務","金控公司","個人、企業、投資與金融服務客戶"),
    "2886.TW": _v238_stock("兆豐金","金融","公股金控/銀行","公股銀行金控","★★★★☆","銀行、外匯、企金與公股金融服務供應商","第一金、合庫金、華南金","中高：企金、外匯與公股資源","利差、信用風險、景氣",1.02,"金融、公股金控、銀行","金融服務","公股金控主要業者","企業、個人、外匯與財管客戶"),
    "2887.TW": _v238_stock("台新金","金融","金控/銀行","銀行型金控","★★★☆☆","銀行、證券、保險與消金服務金控","玉山金、中信金、永豐金","中：銀行通路、消金與財管","利差、信用風險、併購整合",1.01,"金融、銀行、金控","金融服務","銀行型金控","個人、企業、財管與信用卡客戶"),
    "2888.TW": _v238_stock("新光金","金融","金控/壽險","壽險型金控","★★★☆☆","壽險、銀行與證券金融服務集團","國泰金、富邦金、台新金","中：壽險資產與金融通路","利率、匯率、資本適足與投資評價",0.99,"金融、壽險、金控","金融服務","壽險型金控","保戶、銀行與金融服務客戶"),
    "2890.TW": _v238_stock("永豐金","金融","金控/銀行/證券","銀行證券型金控","★★★☆☆","銀行、證券、租賃與金融服務金控","中信金、玉山金、台新金","中：銀行與證券平台","利差、信用風險、資本市場",1.01,"金融、銀行、證券","金融服務","銀行型金控","個人、企業、證券與財管客戶"),
    "2801.TW": _v238_stock("彰銀","金融","銀行","公股銀行","★★★☆☆","銀行、企金、消金與財管服務供應商","第一金、華南金、合庫金","中：分行通路與公股資源","利差、信用風險、景氣",1.00,"金融、銀行、公股","金融服務","公股銀行","個人、企業、財管與放款客戶"),
    "5876.TW": _v238_stock("上海商銀","金融","銀行","銀行股","★★★☆☆","商業銀行、企金、消金與財管服務供應商","玉山銀、彰銀、台企銀","中：銀行通路與資產品質","利差、信用風險、景氣",1.01,"金融、銀行","金融服務","商業銀行","個人、企業與財管客戶"),
    "2834.TW": _v238_stock("臺企銀","金融","中小企業銀行","中小企業銀行","★★★☆☆","中小企業金融、企金與消金服務供應商","彰銀、第一金、華南金","中：中小企業客戶與公股資源","利差、信用風險、中小企業景氣",1.00,"金融、銀行、中小企業","金融服務","中小企業銀行","中小企業、個人與企金客戶"),

    # 航運 / 航空 / 物流續補
    "2606.TW": _v238_stock("裕民","航運","散裝航運","散裝航運主要業者","★★★☆☆","散裝船運與原物料運輸公司","慧洋-KY、新興、國際散裝航商","中：船隊、長約與航線經驗","BDI運價、油價、全球景氣",1.00,"航運、散裝、原物料","下游運輸服務","散裝航運業者","礦砂、煤炭、穀物與大宗物資客戶"),
    "2607.TW": _v238_stock("榮運","物流/航運","貨櫃場/物流","航運物流服務商","★★★☆☆","貨櫃場、倉儲、物流與運輸服務供應商","長榮、台航、物流同業","中：港區資源與物流服務","貨量、景氣、運價循環",1.00,"物流、航運、貨櫃場","下游物流服務","物流服務商","貨櫃航商、進出口商與物流客戶"),
    "2617.TW": _v238_stock("台航","航運","散裝/船舶運輸","航運公司","★★★☆☆","散裝、船舶運輸與航運投資公司","裕民、慧洋-KY、新興","中：船隊與航運經驗","運價循環、油價、全球景氣",0.99,"航運、散裝","下游運輸服務","航運業者","大宗物資與航運客戶"),
    "2637.TW": _v238_stock("慧洋-KY","航運","散裝航運","散裝航運主要業者","★★★☆☆","散裝船隊與長約營運航運公司","裕民、新興、國際散裝航商","中：船隊規模、長約與營運效率","BDI、利率、油價、全球景氣",1.01,"航運、散裝、BDI","下游運輸服務","散裝航運主要業者","礦砂、煤炭、穀物與大宗物資客戶"),
    "2618.TW": _v238_stock("長榮航","航空/觀光","航空客運/貨運","台灣航空主要業者","★★★★☆","航空客運、貨運與航線服務供應商","華航、星宇、Cathay Pacific","中高：航線、品牌與貨運能力","油價、匯率、旅運需求、票價",1.03,"航空、觀光、貨運","下游航空服務","台灣航空主要業者","旅客、貨運、企業差旅與航空聯盟客戶"),
    "2634.TW": _v238_stock("漢翔","航太/國防","航太零組件/國防","台灣航太與國防主要廠","★★★★☆","航太零組件、發動機零組件與國防航空供應商","波音供應鏈、空巴供應鏈、國際航太零件商","中高：航太認證、國防訂單與製造技術","交期、國防政策、航空景氣",1.05,"航太、國防、航空零組件","中游航太製造","台灣航太主要供應商","Boeing、Airbus、GE/Safran供應鏈與國防客戶"),

    # 生技 / 醫療
    "1707.TW": _v238_stock("葡萄王","生技/食品","保健食品/益生菌","保健食品主要廠","★★★☆☆","保健食品、益生菌與直銷通路供應商","大江、生達、保健食品同業","中：品牌、菌種與通路","消費景氣、法規、通路變化",1.03,"保健食品、生技、消費","下游品牌/通路","保健食品主要廠","直銷、零售與保健食品消費者"),
    "4105.TWO": _v238_stock("東洋","生技/醫療","學名藥/抗癌藥","製藥主要廠","★★★☆☆","學名藥、抗癌藥與醫療通路供應商","中化、生達、國際學名藥廠","中：藥證、通路與產品線","藥價、法規、研發與授權",1.03,"製藥、生技、醫療","中下游製藥","製藥供應商","醫院、藥局、醫療通路與患者"),
    "4123.TWO": _v238_stock("晟德","生技/醫療","生技投資/藥品","生技投資控股","★★★☆☆","生技投資、藥品與醫療相關控股公司","中裕、藥華藥、台灣生技同業","中：投資組合與生技資源","投資評價、臨床與法規風險",1.02,"生技、投資控股、醫療","生技投資平台","生技投資控股","轉投資公司、醫療與藥品客戶"),
    "4137.TWO": _v238_stock("麗豐-KY","生技/醫美","醫美保養品/通路","醫美保養品牌","★★★☆☆","醫美保養品、通路與美容服務供應商","保瑞、大江、醫美保養同業","中：品牌與醫美通路","消費景氣、中國市場、法規",1.03,"醫美、生技、消費","下游品牌/通路","醫美保養品牌","美容通路、醫美診所與消費者"),
    "4743.TWO": _v238_stock("合一","生技/新藥","新藥/傷口照護","新藥公司","★★☆☆☆","新藥研發與傷口照護產品公司","中裕、藥華藥、國際新藥公司","低中：研發管線與藥證題材","臨床、銷售、法規與估值波動",1.04,"生技、新藥、醫療","新藥研發/商業化","新藥公司","醫院、醫師、患者與授權合作夥伴"),
    "6547.TWO": _v238_stock("高端疫苗","生技/疫苗","疫苗/生技研發","疫苗公司","★★☆☆☆","疫苗研發、生產與生技平台公司","國光生、國際疫苗廠","低中：疫苗開發與生產經驗","法規、採購、研發與市場接受度",1.02,"疫苗、生技、醫療","疫苗研發/製造","疫苗供應商","政府、醫療院所與疫苗市場"),
    "1760.TW": _v238_stock("寶齡富錦","生技/製藥","腎臟病藥/製藥","製藥公司","★★★☆☆","腎臟病用藥與製藥產品供應商","東洋、生達、國際製藥廠","中：產品線與藥證","藥價、授權銷售、法規",1.03,"製藥、生技、腎臟病用藥","中下游製藥","製藥供應商","醫院、藥局與患者"),
    "1789.TWO": _v238_stock("神隆","生技/製藥","原料藥/API","原料藥供應商","★★★☆☆","原料藥與高活性原料藥供應商","國際API廠、台灣製藥同業","中：API製程與法規認證","客戶訂單、價格競爭、法規",1.02,"原料藥、生技、製藥","上游原料藥","API供應商","國際製藥廠、學名藥廠與醫療客戶"),

    # 食品 / 通路 / 消費
    "1215.TW": _v238_stock("卜蜂","食品","飼料/肉品/食品","飼料肉品主要廠","★★★☆☆","飼料、肉品與食品加工供應商","大成、統一、泰國CP","中：飼料與肉品通路","原料價格、禽畜疫情、消費景氣",1.02,"食品、飼料、肉品","中下游食品","飼料肉品供應商","養殖、通路、餐飲與消費者"),
    "1229.TW": _v238_stock("聯華","食品/投資","麵粉/食品投資","食品與投資公司","★★★☆☆","麵粉、食品與轉投資相關公司","大成、統一、食品同業","中：食品基礎與投資組合","原料價格、投資評價、消費景氣",1.02,"食品、投資、民生消費","中游食品","食品供應商","食品加工、通路與消費者"),
    "1231.TW": _v238_stock("聯華食","食品","鮮食/休閒食品","食品加工主要廠","★★★☆☆","鮮食、休閒食品與食品代工供應商","統一、味全、食品代工同業","中：鮮食製造、品牌與通路","原料、人力、通路需求",1.03,"食品、鮮食、民生消費","中下游食品加工","食品加工供應商","便利商店、量販、餐飲與消費者"),
    "1232.TW": _v238_stock("大統益","食品","油脂/黃豆加工","油脂加工主要廠","★★★☆☆","食用油脂、黃豆加工與食品原料供應商","福壽、泰山、國際油脂廠","中：油脂加工與通路","原料價格、匯率、需求波動",1.02,"食品、油脂、民生消費","中游食品原料","油脂加工供應商","食品加工、餐飲與通路客戶"),
    "5904.TWO": _v238_stock("寶雅","零售通路","美妝生活百貨","生活百貨通路龍頭","★★★★☆","美妝、生活百貨與零售通路供應商","康是美、屈臣氏、小北百貨","中高：展店能力、通路品牌與會員資料","消費景氣、展店成本、競爭",1.05,"零售、通路、民生消費","下游零售通路","美妝生活百貨主要通路","消費者、品牌供應商與生活百貨市場"),
    "5903.TW": _v238_stock("全家","零售通路","便利商店","便利商店主要業者","★★★★☆","便利商店、鮮食、物流與零售服務供應商","統一超、萊爾富、OK Mart","高：門市密度、鮮食物流、會員經營","人力成本、展店、消費景氣",1.04,"便利商店、零售、民生消費","下游零售通路","台灣便利商店主要業者","消費者、鮮食供應商與品牌商"),
    "2915.TW": _v238_stock("潤泰全","零售/投資","量販/投資","通路與投資公司","★★★☆☆","量販通路、紡織與投資相關公司","統一、遠東新、投資控股同業","中：投資資產與通路基礎","投資評價、消費景氣、房市",1.01,"通路、投資、消費","下游通路/投資","通路投資公司","量販、消費者與投資標的"),
    "2913.TW": _v238_stock("農林","食品/農產","茶葉/農產/資產","農產資產公司","★★☆☆☆","茶葉、農產、土地資產與相關開發公司","食品農產同業、資產股","低中：土地資產與品牌歷史","營運規模、資產開發、需求波動",1.00,"農產、資產、食品","上游農產/資產","農產資產公司","茶葉、農產與資產開發客戶"),

    # 營建 / 資產
    "2501.TW": _v238_stock("國建","營建","住宅/商辦建設","大型建商","★★★☆☆","住宅、商辦與土地開發建設公司","興富發、遠雄、華固、長虹","中：土地庫存與品牌","利率、房市政策、去化速度",1.00,"營建、資產、房地產","下游建設開發","大型建商","購屋者、商辦租戶與不動產市場"),
    "2504.TW": _v238_stock("國產","建材/營建","預拌混凝土/建材","建材供應商","★★★☆☆","預拌混凝土、建材與營建供應商","亞泥、台泥、建材同業","中：區域通路與建材需求","營建景氣、原料、房市政策",1.00,"建材、營建、基建","上游建材","預拌混凝土供應商","建商、工程與基建客戶"),
    "2511.TW": _v238_stock("太子","營建","住宅建設/資產","建設公司","★★★☆☆","住宅建設、土地資產與營建開發公司","興富發、國建、遠雄","中：土地資產與開發經驗","房市政策、利率、推案進度",1.00,"營建、資產、房地產","下游建設開發","建設公司","購屋者與不動產市場"),
    "2520.TW": _v238_stock("冠德","營建","住宅/商辦/百貨","建設與商場公司","★★★☆☆","住宅、商辦、商場與土地開發公司","華固、長虹、遠雄、興富發","中：地段、商場與開發能力","房市政策、利率、去化速度",1.01,"營建、商場、資產","下游建設開發","建設公司","購屋者、商場租戶與不動產市場"),
    "2539.TW": _v238_stock("櫻花建","營建","住宅建設","區域建商","★★★☆☆","住宅建設與區域開發公司","興富發、華固、地方建商","中：區域土地與推案能力","房市政策、利率、去化速度",1.01,"營建、房地產","下游建設開發","區域建商","購屋者與不動產市場"),

    # 綠能 / 環保 / 其他
    "9933.TW": _v238_stock("中鼎","工程/環保","工程統包/EPC","台灣工程統包龍頭","★★★★☆","工程設計、統包、環保與能源工程服務供應商","達欣工、國際EPC工程商","中高：工程經驗、專案管理與海外布局","工程成本、收款、海外風險",1.04,"工程、環保、能源、EPC","工程服務","台灣EPC主要業者","石化、電力、環保、科技廠與政府工程客戶","資料中心/能源工程間接受惠"),
    "3708.TW": _v238_stock("上緯投控","綠能/材料","風電樹脂/複材","風電材料供應商","★★★☆☆","風電葉片樹脂、複合材料與綠能投資公司","國際風電材料商、樹脂同業","中：材料技術與風電應用","風電政策、接單、原料成本",1.04,"風電、綠能、複合材料","上游材料","風電材料供應商","風電葉片、複材與綠能客戶"),
    "6873.TW": _v238_stock("泓德能源","綠能/能源服務","太陽能/儲能/售電","綠能服務商","★★★☆☆","太陽能、儲能、售電與能源管理服務供應商","雲豹能源、森崴能源、綠能同業","中：案場開發與能源管理","政策、案場進度、利率與資金成本",1.06,"綠能、儲能、售電、能源管理","下游能源服務","綠能服務商","企業用電戶、再生能源案場與儲能客戶","AI資料中心綠電需求間接受惠"),
    "6806.TW": _v238_stock("森崴能源","綠能/工程","再生能源工程/儲能","綠能工程商","★★★☆☆","再生能源工程、儲能與能源服務供應商","泓德能源、雲豹能源、中鼎","中：工程整合與案場開發","政策、工程進度、資金成本",1.05,"綠能、儲能、工程","能源工程/服務","綠能工程商","企業用電戶、能源案場與政府工程客戶","資料中心綠電需求間接受惠"),
    "9958.TW": _v238_stock("世紀鋼","鋼鐵/風電","離岸風電水下基礎","風電鋼構供應商","★★★★☆","離岸風電水下基礎與大型鋼構供應商","中鋼構、國際風電鋼構商","中高：大型鋼構製造與風電在地供應鏈","風電政策、工程進度、鋼價",1.06,"風電、鋼構、綠能","中游風電鋼構","離岸風電鋼構供應商","離岸風電開發商、工程與能源客戶"),
    "2013.TW": _v238_stock("中鋼構","鋼鐵/工程","鋼構/工程","鋼構供應商","★★★☆☆","鋼構、營建鋼構與工程材料供應商","世紀鋼、鋼構同業","中：鋼構製造與工程需求","鋼價、營建景氣、工程進度",1.02,"鋼構、營建、基建","中游鋼構","鋼構供應商","營建、公共工程、廠房與風電客戶"),
    "9939.TW": _v238_stock("宏全","包材/飲料代工","飲料包材/代工","飲料包材代工主要廠","★★★★☆","飲料包材、充填代工與食品飲料供應鏈服務商","統一、國際飲料包材廠","中高：客戶基礎、海外據點與代工能力","原料成本、消費需求、匯率",1.04,"包材、飲料代工、民生消費","中下游包材/代工","飲料包材主要供應商","飲料品牌、食品公司與消費品客戶"),
    "9941.TW": _v238_stock("裕融","汽車金融","租賃/分期/汽車金融","汽車金融主要業者","★★★★☆","汽車金融、租賃、分期與金融服務公司","和潤企業、中租-KY、裕隆集團","中高：通路、風控與汽車金融經驗","利率、信用風險、車市景氣",1.04,"汽車金融、租賃、消費金融","金融服務","汽車金融主要業者","汽車經銷、消費者與企業租賃客戶"),
    "6592.TW": _v238_stock("和潤企業","汽車金融","分期/租賃/汽車金融","汽車金融主要業者","★★★★☆","汽車分期、租賃與消費金融服務供應商","裕融、中租-KY、和泰車集團","中高：和泰車通路、風控與金融服務","利率、信用風險、車市景氣",1.04,"汽車金融、租賃、消費金融","金融服務","汽車金融主要業者","Toyota/Lexus經銷、消費者與企業租賃客戶"),
    "5871.TW": _v238_stock("中租-KY","租賃金融","租賃/分期/企業金融","租賃金融龍頭","★★★★★","企業租賃、分期、能源投資與金融服務供應商","裕融、和潤、國際租賃公司","高：風控、客戶基礎、跨區域規模","利率、信用風險、景氣循環",1.05,"租賃金融、能源投資、金融服務","金融服務","台灣租賃金融龍頭","中小企業、消費金融、能源案場與設備客戶"),
}

try:
    for _sym, _upd in V238_EXTRA_STOCKS.items():
        STOCK_DB[_sym] = {**STOCK_DB.get(_sym, {}), **_upd}
    ALIASES.clear()
    for _sym, _v in STOCK_DB.items():
        ALIASES[_sym.upper()] = _sym
        ALIASES[_sym.split(".")[0]] = _sym
        ALIASES[_v.get("name", _sym)] = _sym
        ALIASES[_v.get("name", _sym).upper()] = _sym
    OTC_CODES = {s.split('.')[0] for s in STOCK_DB if s.endswith('.TWO')}
except Exception:
    pass

# V238：把主要客戶/競爭者等長欄位做成「下拉查詢 + 展開卡片」，避免表格截斷。
def v237_global_detail_panel(row):
    st.markdown("### 競爭力完整資料")
    detail_map = {
        "主要客戶 / 終端客戶": row.get("主要客戶", row.get("customers", "待補")),
        "AI 客戶 / AI 關聯": row.get("AI客戶", row.get("ai_customers", "待補")),
        "主要競爭者": row.get("主要競爭者", row.get("競爭者", "待補")),
        "護城河": row.get("護城河", "待補"),
        "主要風險": row.get("主要風險", "待補"),
        "產業鏈位置": row.get("產業鏈位置", "待補"),
        "產業地位": row.get("產業地位", "待補"),
        "全球市占率": row.get("全球市占率", "待補"),
    }
    picked = st.selectbox("選擇要查看的完整欄位", list(detail_map.keys()), key="v238_detail_pick_" + str(row.get("代碼", row.get("symbol", "x"))))
    st.markdown(v237_chip_html(detail_map.get(picked, "待補")), unsafe_allow_html=True)
    st.caption(str(detail_map.get(picked, "待補")))
    tab1, tab2, tab3 = st.tabs(["客戶 / 競爭者", "護城河 / 風險", "表格摘要"])
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            v237_detail_box("主要客戶 / 終端客戶", detail_map["主要客戶 / 終端客戶"], "👥", True)
            v237_detail_box("AI 客戶 / AI 關聯", detail_map["AI 客戶 / AI 關聯"], "🤖", False)
        with c2:
            v237_detail_box("主要競爭者", detail_map["主要競爭者"], "⚔️", True)
            v237_detail_box("產業鏈位置", detail_map["產業鏈位置"], "🧭", False)
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            v237_detail_box("護城河", detail_map["護城河"], "🏰", True)
        with c2:
            v237_detail_box("主要風險", detail_map["主要風險"], "⚠️", True)
    with tab3:
        st.dataframe(pd.DataFrame([{
            "產業地位": detail_map["產業地位"],
            "主要客戶": detail_map["主要客戶 / 終端客戶"],
            "AI客戶": detail_map["AI 客戶 / AI 關聯"],
            "競爭者": detail_map["主要競爭者"],
            "護城河": detail_map["護城河"],
            "主要風險": detail_map["主要風險"],
            "產業鏈位置": detail_map["產業鏈位置"],
            "全球市占率": detail_map["全球市占率"],
        }]), use_container_width=True, hide_index=True)

# ===== V238.0 MORE PRICE COVERAGE + GLOBAL DETAIL DROPDOWN END =====



# ===== V239.0 INDUSTRY/GLOBAL SPLIT + CUSTOMER SOURCE CONFIDENCE START =====
APP_VERSION = "V240.0 Version Fix + Completion Dashboard"

# V239 重點：
# 1) 產業分析與全球競爭力分工：產業分析看「類股/子產業」，全球競爭力看「單一公司完整客戶/競爭者」。
# 2) 主要客戶資料新增「資料可信度」概念：上市公司未揭露時，以公開供應鏈/產業鏈合理推估，避免誤以為全是公司正式揭露。
# 3) 繼續補足個股，讓使用者優先查得到現價與估值區間。

V239_EXTRA_STOCKS = {
    # IC設計 / 半導體利基補充
    "2451.TW": _v238_stock("創見","記憶體","記憶體模組/工控儲存","記憶體模組品牌商","★★★☆☆","記憶體模組、工控儲存與消費儲存品牌供應商","威剛、十銓、宇瞻、金士頓","中：品牌、通路與工控儲存客戶","記憶體價格、庫存、消費需求",1.04,"記憶體、工控儲存、模組","下游模組品牌","記憶體模組供應商","工控、嵌入式、消費電子與通路客戶","AI伺服器儲存需求間接受惠"),
    "2455.TW": _v238_stock("全新","砷化鎵/通訊","GaAs磊晶/PA材料","砷化鎵磊晶供應商","★★★☆☆","射頻、PA與光電用砷化鎵磊晶供應商","穩懋、宏捷科、國際III-V材料廠","中：磊晶技術與通訊材料客戶","手機需求、PA週期、競爭",1.04,"砷化鎵、5G、射頻","上游磊晶材料","III-V材料供應商","PA、射頻元件、光電與通訊客戶","低軌衛星/通訊間接受惠"),
    "3105.TWO": _v238_stock("穩懋","砷化鎵/通訊","GaAs代工","全球GaAs代工主要廠","★★★★☆","砷化鎵晶圓代工與射頻元件供應鏈核心廠","宏捷科、GlobalFoundries、Skyworks供應鏈","中高：GaAs製程、客戶認證與產能","手機PA需求、價格競爭、稼動率",1.05,"砷化鎵、射頻、5G、低軌衛星","上游晶圓代工","全球GaAs代工主要廠","射頻IC、PA、通訊與光電客戶","低軌衛星/通訊間接受惠"),
    "8086.TWO": _v238_stock("宏捷科","砷化鎵/通訊","GaAs代工/射頻","GaAs代工供應商","★★★☆☆","砷化鎵晶圓代工與射頻元件供應商","穩懋、全新、國際射頻供應鏈","中：GaAs製程與射頻客戶","手機需求、稼動率、競爭",1.04,"砷化鎵、射頻、5G","上游晶圓代工","GaAs代工供應商","射頻IC、PA與通訊客戶","通訊/低軌衛星間接受惠"),
    "6415.TW": _v238_stock("矽力*-KY","IC設計","電源管理IC","電源管理IC主要廠","★★★★☆","電源管理IC、車用與工業電源晶片供應商","MPS、TI、ADI、立錡","中高：PMIC設計、產品線與客戶導入","中國競爭、庫存、價格壓力",1.08,"PMIC、車用、工控、AI電源","上游IC設計","亞洲PMIC主要廠","消費、工控、車用、通訊與伺服器客戶","AI伺服器電源管理間接受惠"),
    "6515.TW": _v238_stock("穎崴","半導體測試","測試介面/Socket","高階測試介面供應商","★★★★☆","高階測試座、測試介面與半導體測試耗材供應商","旺矽、精測、FormFactor、國際測試介面廠","中高：高階測試介面、客戶認證與AI/HPC需求","客戶集中、資本支出、出貨節奏",1.10,"測試介面、AI/HPC、半導體設備","中游測試介面","高階測試介面主要廠","半導體設計、測試廠、晶圓代工與封測客戶","AI/HPC晶片測試直接受惠"),
    "6781.TW": _v238_stock("AES-KY","電池/儲能","鋰電池模組/BMS","高階電池模組供應商","★★★★☆","高階鋰電池模組、BMS與工業/資料中心備援電池供應商","新普、順達、國際電池模組廠","中高：高階電池模組、BMS與客戶認證","客戶集中、電芯價格、認證時程",1.08,"電池模組、儲能、資料中心UPS","中游電池模組","高階電池模組供應商","資料中心、工業設備、電動工具與高階電子客戶","AI資料中心備援電力間接受惠"),

    # 被動元件 / 電源 / 連接器補充
    "2301.TW": _v238_stock("光寶科","電源/光電","電源供應器/光電/車用","電源與電子模組大廠","★★★★☆","電源供應器、雲端電源、車用電子與光電模組供應商","台達電、群電、康舒、國際電源廠","中高：電源設計、全球客戶與製造能力","毛利率、匯率、需求循環",1.05,"電源、AI伺服器、車用電子","中游電源模組","電源供應主要廠","雲端伺服器、PC、車用與品牌客戶","AI伺服器電源間接受惠"),
    "6412.TW": _v238_stock("群電","電源管理","電源供應器/充電器","電源供應器主要廠","★★★★☆","筆電、伺服器、消費電子與車用電源供應器供應商","台達電、光寶科、康舒、新巨","中高：電源設計、客戶基礎與量產能力","消費電子循環、毛利率、匯率",1.05,"電源、伺服器、AI PC","中游電源模組","電源供應主要廠","PC品牌、伺服器、消費電子與車用客戶","AI PC/伺服器電源間接受惠"),
    "2392.TW": _v238_stock("正崴","連接器/電子零組件","連接器/電源/線束","連接器與電子零組件供應商","★★★☆☆","連接器、電源、線束與消費電子零組件供應商","鴻海供應鏈、嘉澤、貿聯-KY、國際連接器廠","中：連接器製造、客戶與集團資源","消費電子循環、毛利率、客戶集中",1.03,"連接器、消費電子、車用","中游零組件","連接器供應商","消費電子、PC、車用與通訊客戶","AI伺服器連接線材間接受惠"),
    "3665.TW": _v238_stock("貿聯-KY","連接器/線束","高速線束/車用線束","高速線束主要廠","★★★★☆","高速傳輸線束、車用線束與資料中心連接解決方案供應商","正崴、嘉澤、Amphenol、TE Connectivity","中高：高速線束、車用與資料中心客戶認證","車市景氣、AI出貨節奏、匯率",1.09,"高速線束、AI伺服器、車用","中游連接/線束","高速線束主要供應商","資料中心、伺服器、車用、工業與醫療客戶","AI資料中心高速線束直接受惠"),
    "3533.TW": _v238_stock("嘉澤","連接器","CPU Socket/高速連接器","高階連接器主要廠","★★★★☆","CPU Socket、高速連接器與伺服器連接解決方案供應商","鴻海、Amphenol、Molex、TE Connectivity","高：高階連接器、客戶認證與伺服器平台導入","平台轉換、客戶集中、估值波動",1.10,"CPU Socket、高速連接器、AI伺服器","中游連接器","高階連接器主要廠","CPU平台、伺服器、ODM與資料中心客戶","AI伺服器/CPU平台直接受惠"),
    "6269.TW": _v238_stock("台郡","軟板/PCB","FPCB/軟板","軟板主要廠","★★★☆☆","軟性印刷電路板與消費電子供應鏈廠","臻鼎-KY、欣興、韓系/日系軟板廠","中：軟板製程與客戶認證","消費電子需求、客戶集中、價格競爭",1.02,"軟板、消費電子、車用","中游PCB","軟板供應商","手機、穿戴、車用與消費電子客戶","AI終端裝置間接受惠"),

    # PCB / 設備 / 材料補充
    "5469.TW": _v238_stock("瀚宇博","PCB/載板","PCB/伺服器板","PCB供應商","★★★☆☆","消費電子、伺服器與車用PCB供應商","華通、健鼎、金像電、欣興","中：PCB量產能力與客戶基礎","景氣循環、原料、價格競爭",1.03,"PCB、伺服器、車用","中游PCB","PCB供應商","PC、伺服器、車用與消費電子客戶","AI伺服器PCB間接受惠"),
    "2313.TW": _v238_stock("華通","PCB/載板","PCB/HDI/車用板","全球PCB主要廠","★★★★☆","PCB、HDI、車用與伺服器板供應商","臻鼎-KY、欣興、健鼎、TTM","中高：PCB規模、車用與消費電子客戶","景氣循環、客戶集中、原料成本",1.04,"PCB、HDI、車用、AI伺服器","中游PCB","全球PCB主要廠","手機、車用、伺服器、消費電子與品牌客戶","AI伺服器PCB間接受惠"),
    "6213.TW": _v238_stock("聯茂","電子材料","銅箔基板/CCL","CCL主要供應商","★★★☆☆","銅箔基板、PCB材料與高頻高速材料供應商","台光電、台燿、南亞、Panasonic","中：CCL材料技術與PCB客戶","原料成本、產品組合、高速材料競爭",1.05,"CCL、PCB材料、高速材料","上游電子材料","CCL供應商","PCB廠、伺服器、網通與電子製造客戶","AI伺服器高速材料間接受惠"),
    "6214.TW": _v238_stock("精誠","資訊服務","SI/雲端/資安","台灣資訊服務大廠","★★★★☆","系統整合、雲端、資安、企業數位轉型服務供應商","凌群、敦陽科、零壹、國際SI廠","中高：企業客戶、解決方案與服務能力","專案毛利、景氣、人才成本",1.04,"雲端、資安、AI服務、系統整合","下游資訊服務","台灣SI主要廠","金融、製造、政府、零售與企業客戶","企業AI/雲端導入間接受惠"),

    # 光學 / 光通訊 / 網通補充
    "3596.TW": _v238_stock("智易","網通","寬頻網通/CPE","網通設備主要廠","★★★★☆","寬頻CPE、WiFi、PON與網通設備供應商","中磊、啟碁、正文、國際網通廠","中高：電信客戶、網通設計與量產能力","電信資本支出、庫存、價格競爭",1.05,"網通、WiFi、寬頻、5G","中游網通設備","網通設備主要廠","電信商、網通品牌、企業與家庭寬頻客戶","AI資料中心網通需求間接受惠"),
    "6285.TW": _v238_stock("啟碁","網通","WiFi/車用/衛星通訊","網通設備主要廠","★★★★☆","WiFi、車用通訊、衛星通訊與企業網通設備供應商","中磊、智易、正文、國際網通廠","中高：網通設計、車用與衛星通訊布局","庫存、產品轉換、競爭",1.06,"網通、衛星通訊、車用、WiFi","中游網通設備","網通設備主要廠","電信商、車用、衛星通訊、企業網通客戶","低軌衛星/資料中心網通間接受惠"),
    "5388.TW": _v238_stock("中磊","網通","寬頻/電信網通","電信網通主要廠","★★★★☆","寬頻接取、PON、Cable與電信網通設備供應商","智易、啟碁、正文、國際網通廠","中高：電信客戶與寬頻設備經驗","電信資本支出、庫存、價格競爭",1.05,"網通、寬頻、PON、5G","中游網通設備","電信網通主要廠","全球電信商、寬頻服務商與網通客戶","AI資料中心網通間接受惠"),
    "4906.TW": _v238_stock("正文","網通","寬頻/無線網通","網通設備供應商","★★★☆☆","寬頻、無線通訊與網通設備供應商","中磊、智易、啟碁","中：網通設計與通路客戶","電信需求、庫存、競爭",1.03,"網通、寬頻、WiFi","中游網通設備","網通設備供應商","電信商、企業、網通品牌客戶","AI網通間接受惠"),

    # 傳產 / 消費 / 觀光補充
    "2707.TW": _v238_stock("晶華","觀光/飯店","飯店/餐飲","台灣高端飯店品牌","★★★★☆","飯店、餐飲、宴會與觀光服務供應商","寒舍、雲品、國際飯店集團","中高：品牌、地點與餐飲服務","旅遊需求、消費景氣、人力成本",1.04,"觀光、飯店、餐飲","下游服務","高端飯店品牌","旅客、商務客、餐飲與宴會客戶"),
    "2727.TW": _v238_stock("王品","餐飲/消費","連鎖餐飲","台灣連鎖餐飲主要品牌","★★★★☆","多品牌連鎖餐飲、外食與消費服務供應商","瓦城、豆府、國際餐飲品牌","中高：品牌矩陣、展店能力與營運管理","食材、人力、消費景氣",1.04,"餐飲、消費、內需","下游餐飲服務","連鎖餐飲主要品牌","一般消費者、商務聚餐與外食客群"),
    "2723.TW": _v238_stock("美食-KY","餐飲/消費","咖啡/烘焙連鎖","咖啡烘焙連鎖品牌","★★★☆☆","咖啡、烘焙與連鎖餐飲品牌營運商","星巴克、路易莎、85度C同業","中：品牌與展店經驗","中國市場、消費景氣、展店成本",1.02,"餐飲、咖啡、消費","下游餐飲服務","連鎖咖啡烘焙品牌","一般消費者、咖啡與烘焙市場"),
    "2753.TW": _v238_stock("八方雲集","餐飲/消費","連鎖餐飲/鍋貼水餃","連鎖餐飲品牌","★★★★☆","鍋貼、水餃、麵食與連鎖餐飲服務供應商","王品、豆府、連鎖餐飲同業","中高：門市密度、標準化與品牌","食材、人力、展店、消費景氣",1.04,"餐飲、內需、連鎖品牌","下游餐飲服務","連鎖餐飲品牌","一般消費者、外食客群與加盟/直營門市"),
    "2752.TW": _v238_stock("豆府","餐飲/消費","韓式/多品牌餐飲","餐飲連鎖品牌","★★★☆☆","韓式與多品牌連鎖餐飲服務供應商","王品、瓦城、八方雲集","中：餐飲品牌與展店能力","人力、食材、消費景氣",1.03,"餐飲、內需、消費","下游餐飲服務","連鎖餐飲品牌","一般消費者與外食客群"),
    "2729.TWO": _v238_stock("瓦城","餐飲/消費","多品牌餐飲","餐飲連鎖品牌","★★★☆☆","泰式與多品牌餐飲連鎖服務供應商","王品、豆府、國際餐飲品牌","中：品牌與展店能力","食材、人力、消費景氣",1.03,"餐飲、內需、消費","下游餐飲服務","一般消費者與外食客群"),

    # 營建/資產續補
    "2542.TW": _v238_stock("興富發","營建","住宅/商辦建設","大型建商","★★★★☆","住宅、商辦、土地開發與建設公司","國建、遠雄、華固、長虹","中高：土地庫存、推案量與銷售能力","利率、房市政策、去化速度",1.02,"營建、資產、房地產","下游建設開發","大型建商","購屋者、投資客、商辦租戶與不動產市場"),
    "2548.TW": _v238_stock("華固","營建","住宅/商辦建設","高端建商","★★★★☆","住宅、商辦與土地開發建設公司","長虹、遠雄、興富發、國建","中高：地段選擇、品牌與財務體質","利率、房市政策、推案時程",1.02,"營建、資產、房地產","下游建設開發","高端建商","購屋者、企業商辦租戶與不動產市場"),
    "5534.TW": _v238_stock("長虹","營建","住宅/商辦建設","高端建商","★★★★☆","住宅、商辦與都更開發建設公司","華固、遠雄、興富發","中高：地段、品牌與開發經驗","房市政策、利率、推案與認列時程",1.02,"營建、都更、資產","下游建設開發","高端建商","購屋者、商辦租戶與不動產市場"),
    "5522.TW": _v238_stock("遠雄","營建","住宅/商辦/大型開發","大型建商","★★★★☆","住宅、商辦、大型開發與資產營運公司","興富發、華固、長虹、國建","中高：土地資源、品牌與大型開發能力","政策、利率、去化、工程成本",1.02,"營建、資產、房地產","下游建設開發","大型建商","購屋者、商辦租戶、商場與不動產市場"),
}

try:
    for _sym, _upd in V239_EXTRA_STOCKS.items():
        STOCK_DB[_sym] = {**STOCK_DB.get(_sym, {}), **_upd}
    for _sym, _v in STOCK_DB.items():
        # 主要客戶資料品質：公司正式揭露很少，多數是依公開供應鏈與產業定位推估。
        if "customer_confidence" not in _v:
            cust = str(_v.get("customers", "待補"))
            _v["customer_confidence"] = "C：產業鏈推估" if cust in ["待補", "", "nan"] else "B：公開供應鏈/產業合理推估"
        if "valuation_model" not in _v:
            _v["valuation_model"] = "現價 × 產業乘數區間"
    ALIASES.clear()
    for _sym, _v in STOCK_DB.items():
        ALIASES[_sym.upper()] = _sym
        ALIASES[_sym.split(".")[0]] = _sym
        ALIASES[_v.get("name", _sym)] = _sym
        ALIASES[_v.get("name", _sym).upper()] = _sym
    OTC_CODES = {s.split('.')[0] for s in STOCK_DB if s.endswith('.TWO')}
except Exception:
    pass

_v239_prev_rows_df = v230_rows_df
def v230_rows_df():
    df = _v239_prev_rows_df()
    if df is None or df.empty:
        return df
    df["資料可信度"] = df["代碼"].map(lambda s: STOCK_DB.get(s, {}).get("customer_confidence", "B/C：待確認"))
    df["估值模型"] = df["代碼"].map(lambda s: STOCK_DB.get(s, {}).get("valuation_model", "現價 × 產業乘數區間"))
    # 明確區分：產業分析使用產業層資料；全球競爭力使用公司層資料。
    return df

def _v239_summary_stat(df, col):
    try:
        return df[col].dropna().astype(str).nunique()
    except Exception:
        return 0

def industry_page():
    v230_css(); st.header("🏭 產業分析")
    st.caption("本頁改為『類股/子產業』總覽：看同產業有哪些公司、估值狀態、AI受惠度與產業鏈分布。單一公司的主要客戶與競爭者，移到『全球競爭力』頁展開查看。")
    df = v230_rows_df()
    c1,c2,c3 = st.columns(3)
    with c1:
        ind = st.selectbox("主產業", sorted(df["產業"].dropna().unique()), key="v239_industry_ind")
    dff = df[df["產業"] == ind].copy()
    subs = ["全部"] + sorted(dff["子產業"].dropna().astype(str).unique())
    with c2:
        sub = st.selectbox("子產業", subs, key="v239_industry_sub")
    if sub != "全部":
        dff = dff[dff["子產業"].astype(str) == sub]
    with c3:
        sort_col = st.selectbox("排序方式", ["AI受惠度", "全球競爭力", "公司", "代碼"], key="v239_industry_sort")
    meta = V224_INDUSTRY_META.get(ind, {"規模":"待補","成長率":"待補","AI關聯度":"待補","說明":"此產業資料仍在擴充。"})
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("產業規模", meta.get("規模","待補")); k2.metric("成長率", meta.get("成長率","待補")); k3.metric("AI關聯度", meta.get("AI關聯度","待補")); k4.metric("涵蓋公司", len(dff))
    st.info(meta.get("說明", ""))
    st.markdown("### 產業鏈分布")
    cc1,cc2,cc3 = st.columns(3)
    cc1.metric("子產業數", _v239_summary_stat(dff, "子產業"))
    cc2.metric("已可估值", len(dff[dff.get("估值狀態","").astype(str).str.contains("已", na=False)]) if "估值狀態" in dff.columns else len(dff))
    cc3.metric("資料完整度欄位", "持續補齊")
    cols = ["公司","代碼","子產業","產業鏈位置","AI受惠度","全球競爭力","估值狀態","估值模型","資料完整度"]
    show = dff[[c for c in cols if c in dff.columns]].copy()
    if sort_col in show.columns:
        show = show.sort_values(sort_col, ascending=False if sort_col in ["AI受惠度","全球競爭力"] else True)
    st.dataframe(show, use_container_width=True, hide_index=True)
    with st.expander("同產業公司快速搜尋", expanded=False):
        q = st.text_input("輸入公司名稱或代號", key="v239_industry_q")
        if q:
            mask = dff["公司"].astype(str).str.contains(q, case=False, na=False) | dff["代碼"].astype(str).str.contains(q, case=False, na=False)
            st.dataframe(dff.loc[mask, [c for c in cols if c in dff.columns]], use_container_width=True, hide_index=True)

def global_competition_page():
    v230_css(); st.header("🌏 全球競爭力")
    st.caption("本頁專注『單一公司』：完整查看主要客戶、AI客戶、競爭者、護城河、風險與供應鏈位置。")
    df = v230_rows_df()
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        theme = st.selectbox("主題標籤", ["全部"] + sorted({p.strip() for x in df.get("主題標籤", pd.Series(dtype=str)).dropna().astype(str) for p in x.replace("，","、").replace(",","、").split("、") if p.strip()}), key="v239_global_theme")
    dff = df.copy()
    if theme != "全部":
        dff = dff[dff.get("主題標籤", "").astype(str).str.contains(theme, na=False)]
    with c2:
        ind = st.selectbox("主產業", sorted(dff["產業"].dropna().unique()), key="v239_global_ind")
    dff = dff[dff["產業"] == ind]
    with c3:
        sub = st.selectbox("子產業", sorted(dff["子產業"].dropna().astype(str).unique()), key="v239_global_sub")
    dff = dff[dff["子產業"].astype(str) == sub]
    labels = {f"{r['公司']} / {r['代碼']}": r["代碼"] for _, r in dff.iterrows()}
    with c4:
        picked = st.selectbox("個股（選到即查詢）", list(labels.keys()), key="v239_global_stock")
    code = labels[picked]
    st.session_state["v227_active_symbol"] = code
    row = df[df["代碼"] == code].iloc[0].to_dict()
    st.markdown(f"## {row.get('公司','')}（{row.get('代碼','')}）")
    g1,g2,g3,g4 = st.columns(4)
    try: ai_txt = f"{int(float(row.get('AI受惠度',0)))}/10"
    except Exception: ai_txt = "N/A"
    g1.metric("全球排名", row.get("全球排名", "待補")); g2.metric("AI受惠度", ai_txt); g3.metric("全球競爭力", row.get("全球競爭力", "待補")); g4.metric("全球市占率", row.get("全球市占率", "待補"))
    st.markdown(v230_tag_html(row.get("主題標籤", "")), unsafe_allow_html=True)
    st.info("主要客戶資料很多公司不會完整揭露，因此平台會分成：A 公司正式揭露、B 公開供應鏈/產業合理推估、C 待確認。現階段多數屬 B/C，會持續校正。")
    v237_global_detail_panel(row)
    with st.expander("資料可信度與估值模型", expanded=True):
        st.write("資料可信度：", row.get("資料可信度", "B/C：待確認"))
        st.write("估值模型：", row.get("估值模型", "現價 × 產業乘數區間"))
        st.write("說明：估值區間優先讓使用者查得到參考價格；完整DCF/EVA/EBO會放在研究院或Pro版逐步補齊。")
    try:
        st.markdown("---"); v224_ai_score_explanation()
    except Exception:
        pass

# ===== V239.0 INDUSTRY/GLOBAL SPLIT + CUSTOMER SOURCE CONFIDENCE END =====

# ===== V240.0 VERSION FIX + COMPLETION DASHBOARD START =====
APP_VERSION = "V240.0 Version Fix + Completion Dashboard"
DB_VERSION = "TW-STOCK-20260628-V240"

# 繼續補齊較常被搜尋的傳產、金融、通路、電子零組件；先提供可搜尋與估值區間，深度客戶資料持續校正。
V240_EXTRA_STOCKS = {
    "1101.TW": _v238_stock("台泥","水泥/建材","水泥/低碳建材","台灣水泥龍頭","★★★★☆","台灣水泥、預拌混凝土與低碳建材主要供應商","亞泥、環泥、國際水泥廠","中高：品牌、通路、礦源與能源轉型布局","房市、公共工程、煤價與碳成本",1.02,"水泥、基建、低碳材料","上游建材","台灣水泥龍頭","營建商、公共工程、預拌混凝土客戶"),
    "1102.TW": _v238_stock("亞泥","水泥/建材","水泥/建材","台灣水泥主要廠","★★★★☆","水泥與建材主要供應商，具兩岸市場布局","台泥、環泥、國際水泥廠","中高：產能、礦源、通路與集團資源","中國需求、煤價、碳成本",1.02,"水泥、基建、低碳材料","上游建材","台灣水泥主要廠","營建商、公共工程、建材通路"),
    "1216.TW": _v238_stock("統一","食品/通路","食品/飲料/通路","台灣食品龍頭","★★★★★","台灣食品、飲料、通路與消費品牌龍頭","味全、聯華食、國際食品品牌","高：品牌、通路、產品組合與集團資源","原物料、消費力、匯率",1.04,"食品、通路、民生消費","下游消費品牌","台灣食品龍頭","超商、量販、餐飲通路與終端消費者"),
    "2912.TW": _v238_stock("統一超","食品/通路","便利商店","台灣超商龍頭","★★★★★","台灣便利商店與零售通路龍頭","全家、萊爾富、OK、量販通路","高：門市密度、會員數據、物流與品牌","展店飽和、工資、租金與消費景氣",1.05,"通路、零售、民生消費","終端零售通路","台灣便利商店#1","消費者、品牌供應商、電商與物流合作夥伴"),
    "5903.TW": _v238_stock("全家","食品/通路","便利商店","台灣超商主要廠","★★★★☆","台灣便利商店與零售服務主要業者","統一超、萊爾富、OK","中高：會員、展店、物流與鮮食能力","競爭、工資、租金、消費景氣",1.04,"通路、零售、民生消費","終端零售通路","台灣便利商店#2","消費者、品牌供應商、物流與電商合作夥伴"),
    "1301.TW": _v238_stock("台塑","塑化/材料","PVC/石化原料","台灣石化龍頭之一","★★★★☆","PVC、石化原料與塑膠材料大型供應商","南亞、台化、國際石化廠","中高：一貫化、規模與集團供應鏈","油價、景氣循環、中國產能",1.01,"塑化、材料、景氣循環","上游石化材料","台灣石化龍頭之一","塑膠加工、建材、工業材料客戶"),
    "1303.TW": _v238_stock("南亞","塑化/材料","塑膠/電子材料","塑化與電子材料大廠","★★★★☆","塑化、聚酯、電子材料與銅箔基板相關供應商","台塑、台化、台光電、國際材料廠","中高：材料技術、規模與集團資源","景氣循環、油價、電子材料需求",1.02,"塑化、電子材料、銅箔基板","上游材料","塑化與電子材料大廠","電子、塑膠加工、工業材料客戶"),
    "1326.TW": _v238_stock("台化","塑化/材料","芳香烴/纖維/石化","石化與纖維大廠","★★★★☆","芳香烴、纖維、塑化原料大型供應商","台塑、南亞、中石化、國際石化廠","中高：石化一貫化與規模經濟","油價、利差、中國產能與景氣循環",1.01,"塑化、纖維、景氣循環","上游石化材料","台灣石化主要廠","紡織、塑膠加工、工業材料客戶"),
    "2881.TW": _v238_stock("富邦金","金融","金控/壽險/銀行","大型民營金控","★★★★☆","台灣大型金控，涵蓋壽險、銀行、證券與產險","國泰金、中信金、國際金控","中高：金融通路、資本實力、保險與銀行整合","利率、匯率、股債市波動、信用風險",1.03,"金融、金控、壽險","金融服務","台灣大型金控","存戶、保戶、企業金融與投資客戶"),
    "2882.TW": _v238_stock("國泰金","金融","金控/壽險/銀行","大型民營金控","★★★★☆","台灣大型金控，壽險與銀行為核心業務","富邦金、中信金、兆豐金","中高：壽險規模、銀行通路、品牌與資本實力","利率、匯率、資本市場、保險準備金",1.03,"金融、金控、壽險","金融服務","台灣大型金控","存戶、保戶、企業金融與財富管理客戶"),
    "2891.TW": _v238_stock("中信金","金融","金控/銀行","大型民營金控","★★★★☆","銀行、壽險與海外金融布局完整的大型金控","富邦金、國泰金、玉山金、兆豐金","中高：銀行通路、信用卡、企業金融與海外布局","利差、信用風險、資本市場波動",1.03,"金融、金控、銀行","金融服務","台灣大型銀行金控","個人金融、企業金融、財富管理客戶"),
    "2886.TW": _v238_stock("兆豐金","金融","公股金控/銀行","大型公股金控","★★★★☆","以銀行與外匯業務為核心的大型公股金控","第一金、合庫金、華南金、臺企銀","中高：公股資源、外匯業務、企業金融客戶","利差、信用風險、政策與景氣循環",1.02,"金融、銀行、公股金控","金融服務","大型公股金控","企業金融、外匯、存戶與政府相關客戶"),
    "2603.TW": _v238_stock("長榮","航運","貨櫃航運","全球貨櫃航運主要業者","★★★★☆","全球貨櫃航運主要公司，受運價循環影響大","陽明、萬海、Maersk、MSC、CMA CGM","中高：船隊、航線、成本與聯盟資源","運價循環、油價、地緣政治、供需失衡",1.04,"航運、貨櫃、景氣循環","全球物流運輸","全球貨櫃航運主要業者","出口商、進口商、物流承攬商與全球供應鏈客戶"),
    "2609.TW": _v238_stock("陽明","航運","貨櫃航運","台灣貨櫃航運主要業者","★★★★☆","台灣貨櫃航運主要公司，受運價循環影響大","長榮、萬海、Maersk、MSC","中：航線、船隊與聯盟合作","運價、油價、船舶供給、全球貿易",1.03,"航運、貨櫃、景氣循環","全球物流運輸","台灣貨櫃航運主要業者","出口商、進口商與物流承攬商"),
    "2615.TW": _v238_stock("萬海","航運","貨櫃航運/亞洲線","亞洲線貨櫃航運主要業者","★★★☆☆","以亞洲區域航線為核心的貨櫃航運公司","長榮、陽明、區域航商","中：亞洲航線、船隊與營運彈性","亞洲線運價、油價、供需循環",1.03,"航運、貨櫃、亞洲線","區域物流運輸","亞洲線貨櫃航運主要業者","亞洲區出口商、進口商與物流客戶"),
    "2002.TW": _v238_stock("中鋼","鋼鐵","一貫作業鋼廠","台灣鋼鐵龍頭","★★★★☆","台灣一貫作業鋼鐵龍頭，供應汽車、營建、機械等產業","中鴻、豐興、國際鋼廠","中高：規模、產品線與關鍵工業材料地位","鋼價、原料、景氣循環、中國供給",1.01,"鋼鐵、基建、景氣循環","上游鋼鐵材料","台灣鋼鐵龍頭","汽車、營建、機械、家電與製造業客戶"),
    "2014.TW": _v238_stock("中鴻","鋼鐵","熱軋/冷軋鋼品","中鋼集團鋼品廠","★★★☆☆","熱軋、冷軋與鋼品供應商，中鋼集團成員","中鋼、燁輝、盛餘、國際鋼廠","中：集團資源與鋼品通路","鋼價、原料、下游需求",1.00,"鋼鐵、鋼品、景氣循環","中游鋼品加工","台灣鋼品主要廠","製造、營建、加工與外銷客戶"),
    "1402.TW": _v238_stock("遠東新","紡織/材料","聚酯/紡織/零售","聚酯與紡織整合大廠","★★★★☆","聚酯、紡織、零售與轉投資多元布局公司","新纖、力麗、國際紡織廠","中高：垂直整合、品牌客戶與集團資產","原料、匯率、消費需求與景氣循環",1.02,"紡織、聚酯、資產","中上游材料/紡織","台灣紡織聚酯龍頭之一","國際品牌、成衣、工業材料與零售客戶"),
    "2105.TW": _v238_stock("正新","橡膠/輪胎","輪胎","全球輪胎主要業者","★★★★☆","汽機車、自行車與工業輪胎主要供應商","建大、普利司通、米其林、固特異","中高：品牌、通路、製造規模","橡膠價格、車市循環、匯率與競爭",1.02,"輪胎、汽車零組件、消費","下游輪胎品牌","全球輪胎主要業者","汽車通路、機車、自行車、OEM與替換胎市場"),
    "9910.TW": _v238_stock("豐泰","運動用品","製鞋/運動鞋代工","全球運動鞋代工主要廠","★★★★☆","國際運動品牌鞋類代工主要供應商","寶成、鈺齊-KY、國際製鞋廠","中高：製造能力、客戶認證與海外布局","品牌訂單、工資、匯率與庫存循環",1.03,"製鞋、運動用品、品牌供應鏈","下游代工製造","全球運動鞋代工主要廠","Nike等國際運動品牌與通路市場"),
}
try:
    for _sym, _upd in V240_EXTRA_STOCKS.items():
        STOCK_DB[_sym] = {**STOCK_DB.get(_sym, {}), **_upd}
    ALIASES.clear()
    for _sym, _v in STOCK_DB.items():
        ALIASES[_sym.upper()] = _sym
        ALIASES[_sym.split('.')[0]] = _sym
        ALIASES[_v.get('name', _sym)] = _sym
        ALIASES[_v.get('name', _sym).upper()] = _sym
    OTC_CODES = {s.split('.')[0] for s in STOCK_DB if s.endswith('.TWO')}
except Exception:
    pass

def v240_completion_counts(df=None):
    if df is None:
        df = v230_rows_df()
    total = len(df) if df is not None else 0
    def good_col(col):
        if df is None or col not in df.columns:
            return 0
        s = df[col].fillna('').astype(str).str.strip()
        return int(((s != '') & (~s.isin(['待補','nan','None','N/A']))).sum())
    valuation = good_col('綜合合理價') if '綜合合理價' in df.columns else total
    return {
        '個股資料庫': total,
        '完成估值': valuation,
        '完成競爭力': good_col('全球競爭力'),
        '完成主要客戶': good_col('主要客戶'),
        '完成產業鏈位置': good_col('產業鏈位置'),
        '資料庫版本': DB_VERSION,
    }

def v240_system_dashboard(df=None):
    if df is None:
        df = v230_rows_df()
    c = v240_completion_counts(df)
    st.markdown('### 📊 資料庫完成度')
    cols = st.columns(5)
    cols[0].metric('系統版本', APP_VERSION)
    cols[1].metric('個股資料庫', c['個股資料庫'])
    cols[2].metric('完成估值', c['完成估值'])
    cols[3].metric('完成主要客戶', c['完成主要客戶'])
    cols[4].metric('完成競爭力', c['完成競爭力'])
    st.caption(f"資料庫版本：{DB_VERSION}｜估值區間先以現價 × 產業乘數區間建立；深度DCF/EVA/EBO會逐步補在研究院/Pro版。")

# 覆蓋首頁：修正右上角仍顯示 V233 的問題，並加入資料庫完成度儀表板。
def home():
    v230_css()
    if 'v227_active_symbol' not in st.session_state:
        st.session_state['v227_active_symbol'] = '2330.TW'
    now_show = datetime.now().strftime('%Y/%m/%d %H:%M')
    st.markdown(f"""
    <div class="v230-topbar">
      <div>
        <div class="v230-brand">📈 智策股市 AI 決策平台</div>
        <div class="v230-sub">企業價值研究平台｜產業鏈 × 全球競爭力 × 財務預測 × 合理價推估</div>
      </div>
      <div class="v230-version">{APP_VERSION}<br>{now_show}</div>
    </div>
    """, unsafe_allow_html=True)
    q = st.text_input('搜尋公司名稱 / 代號 / 產業 / 主題標籤', placeholder='例如：2330、台積電、2313、華通、低軌衛星、CoWoS', key='v240_search')
    if str(q or '').strip():
        st.session_state['v227_active_symbol'] = v230_symbol(q)
    df = v230_rows_df()
    if df.empty:
        st.warning('資料庫尚未載入。')
        return
    rank = v231_rank_table(df)
    total = len(df)
    hot_ind = df['產業'].nunique()
    hot_theme = len(set('、'.join(df['主題標籤'].fillna('').astype(str)).split('、'))) if '主題標籤' in df.columns else 0
    ai9 = int((pd.to_numeric(df['AI受惠度'], errors='coerce').fillna(0) >= 9).sum()) if 'AI受惠度' in df.columns else 0
    valid_price = int(rank['現價'].notna().sum()) if not rank.empty else 0
    global5 = int(df['全球競爭力'].astype(str).str.contains('★★★★★', regex=False).sum()) if '全球競爭力' in df.columns else 0
    st.markdown(f"""
    <div class="v230-kpi-grid">
      <div class="v230-kpi"><div class="v230-kpi-icon">🔥</div><div class="v230-kpi-label">熱門產業</div><div class="v230-kpi-value">{hot_ind}</div><div class="v230-kpi-note">涵蓋主要主產業</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">🏆</div><div class="v230-kpi-label">個股資料庫</div><div class="v230-kpi-value">{total}</div><div class="v230-kpi-note">持續補齊中</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">🏷️</div><div class="v230-kpi-label">主題標籤</div><div class="v230-kpi-value">{hot_theme}</div><div class="v230-kpi-note">可多重歸屬</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">💹</div><div class="v230-kpi-label">有效現價</div><div class="v230-kpi-value">{valid_price}</div><div class="v230-kpi-note">Yahoo Finance</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">🤖</div><div class="v230-kpi-label">AI高受惠</div><div class="v230-kpi-value">{ai9}</div><div class="v230-kpi-note">AI受惠度 ≥ 9</div></div>
      <div class="v230-kpi"><div class="v230-kpi-icon">🌏</div><div class="v230-kpi-label">全球強勢</div><div class="v230-kpi-value">{global5}</div><div class="v230-kpi-note">★★★★★</div></div>
    </div>
    """, unsafe_allow_html=True)
    v240_system_dashboard(df)
    st.markdown('### 核心快速查詢')
    quick = [('台積電','2330'),('華通','2313'),('昇達科','3491'),('廣達','2382'),('奇鋐','3017'),('聯鈞','3450')]
    cols = st.columns(len(quick))
    for col, (name, code_) in zip(cols, quick):
        with col:
            if st.button(name, key=f'v240_quick_{code_}', use_container_width=True):
                st.session_state['v227_active_symbol'] = v230_symbol(code_)
                st.rerun()
    with st.expander('排行計算標準', expanded=False):
        st.markdown("""
        **V240 修正重點：** 版本顯示已同步修正，不再固定顯示 V233。  
        低估排行仍以 `預期報酬 = (綜合合理價 - 現價) ÷ 現價` 計算。  
        現價優先抓 Yahoo Finance 最近價格；抓不到現價者不列入低估排行，避免錯誤價格造成排行失真。
        """)
    tab1, tab2, tab3, tab4 = st.tabs(['熱門個股', '低估排行', 'AI受惠排行', '全球競爭力排行'])
    with tab1:
        show = df.copy(); show['_stars'] = show['全球競爭力'].astype(str).str.count('★')
        show = show.sort_values(['AI受惠度','_stars'], ascending=False).head(10)
        st.dataframe(show[['公司','代碼','產業','子產業','AI受惠度','全球競爭力','產業地位']], use_container_width=True, hide_index=True)
    with tab2:
        low = rank.dropna(subset=['現價','綜合合理價','預期報酬%'])
        low = low[low['現價'] > 0].sort_values('預期報酬%', ascending=False).head(10)
        st.dataframe(v231_fmt_rank(low[['公司','代碼','產業','子產業','現價','綜合合理價','預期報酬%','AI受惠度']]), use_container_width=True, hide_index=True)
    with tab3:
        ai = df.sort_values('AI受惠度', ascending=False).head(15)
        st.dataframe(ai[['公司','代碼','產業','子產業','AI受惠度','全球競爭力','主要客戶']], use_container_width=True, hide_index=True)
    with tab4:
        g = df.copy(); g['_stars'] = g['全球競爭力'].astype(str).str.count('★')
        g = g.sort_values(['_stars','AI受惠度'], ascending=False).head(15)
        st.dataframe(g[['公司','代碼','產業','子產業','全球競爭力','全球排名','全球市占率']], use_container_width=True, hide_index=True)

# 修正 main() 呼叫的是 competition_page，但 V239 新版函式名是 global_competition_page。
try:
    competition_page = global_competition_page
except Exception:
    pass

# 設定頁也顯示完成度，方便確認雲端部署是否為最新版。
def settings_page():
    st.header('⚙️ 設定')
    st.write('系統版本：', APP_VERSION)
    st.write('資料庫版本：', DB_VERSION)
    st.write('資料庫股票數：', len(STOCK_DB))
    try:
        v240_system_dashboard(v230_rows_df())
    except Exception:
        pass
    st.info('公開版不顯示模型權重；深度估值模型會逐步放入研究院/Pro版。')

# 覆蓋 main，讓設定頁使用新版 settings_page。
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
        settings_page()

# ===== V240.0 VERSION FIX + COMPLETION DASHBOARD END =====


# ===== V241.0 MORE STOCK COVERAGE + QUALITY DASHBOARD START =====
APP_VERSION = "V241.0 More Stock Coverage + Quality Dashboard"
DB_VERSION = "TW-STOCK-20260628-V241"

# V241：續補常用搜尋個股，先完成「可查詢、可估值區間、可看產業位置」。
# 主要客戶若公司未完整揭露，先以產業鏈/通路客戶描述，後續再逐步校正為明確公司名單。
V241_EXTRA_STOCKS = {
    "2207.TW": _v238_stock("和泰車","汽車/通路","汽車代理/售後服務","台灣汽車代理龍頭","★★★★★","Toyota/Lexus台灣代理與汽車銷售服務龍頭","裕日車、中華車、汎德永業、汽車代理同業","高：品牌代理權、通路、售後服務與金融保險整合","車市景氣、匯率、原廠供車、政策",1.04,"汽車、通路、民生消費","汽車下游通路","台灣汽車代理龍頭","Toyota、Lexus、終端車主、企業車隊、售後服務客戶"),
    "2204.TW": _v238_stock("中華車","汽車/整車","整車製造/商用車","台灣整車主要廠","★★★★☆","商用車、乘用車與電動車相關製造商","裕隆、和泰車、三陽、國際車廠","中高：製造能力、商用車通路與集團資源","車市循環、電動車競爭、供應鏈",1.03,"汽車、電動車、商用車","整車製造","台灣整車主要廠","Mitsubishi相關通路、商用車客戶、企業車隊與終端車主"),
    "2227.TW": _v238_stock("裕日車","汽車/通路","汽車代理/銷售","Nissan台灣代理主要業者","★★★☆☆","Nissan品牌代理、汽車銷售與售後服務公司","和泰車、中華車、汎德永業","中：品牌代理、通路與售後服務","車市需求、匯率、品牌競爭",1.02,"汽車、通路、民生消費","汽車下游通路","台灣汽車代理商","Nissan、終端車主、企業車隊與售後服務客戶"),
    "1592.TW": _v238_stock("英瑞-KY","汽車零組件","汽車水箱/冷卻系統","汽車零組件供應商","★★★☆☆","汽車散熱與冷卻系統零組件供應商","東陽、帝寶、國際汽車零組件廠","中：AM通路、產品線與製造能力","AM需求、匯率、原料成本",1.02,"汽車零組件、AM市場","中游車用零組件","汽車冷卻系統零組件供應商","汽車售後維修市場、零件通路、保險維修與車用客戶"),
    "2352.TW": _v238_stock("佳世達","電子品牌/醫療","顯示器/醫療/解決方案","電子與醫療解決方案集團","★★★★☆","顯示器、商用解決方案、醫療與智慧服務多元布局","宏碁、華碩、明基醫療相關同業","中高：品牌、通路、醫療與企業解決方案整合","顯示器景氣、醫療整合、匯率",1.03,"顯示器、醫療、企業解決方案","下游品牌/系統整合","電子與醫療解決方案集團","企業客戶、醫療院所、顯示器通路、商用解決方案客戶"),
    "2324.TW": _v238_stock("仁寶","AI伺服器/ODM","NB ODM/伺服器","全球NB ODM主要廠","★★★★☆","筆電ODM與伺服器代工供應商，AI伺服器逐步布局","廣達、緯創、英業達、和碩","中高：ODM規模、製造效率與客戶基礎","PC景氣、毛利率、AI伺服器滲透速度",1.04,"AI伺服器、AI PC、ODM","中下游ODM製造","全球NB ODM主要廠","HP、Dell、Lenovo、品牌PC與伺服器客戶；AI客戶多屬間接供應鏈"),
    "2353.TW": _v238_stock("宏碁","AI PC/品牌","PC品牌/電競/商用","全球PC品牌","★★★☆☆","PC、電競、商用與AI PC品牌商","華碩、Lenovo、HP、Dell","中：品牌、通路與商用客戶基礎","PC景氣、庫存、品牌競爭",1.02,"AI PC、電競、品牌通路","下游品牌","全球PC品牌","消費者、企業採購、通路商、教育與商用客戶"),
    "2357.TW": _v238_stock("華碩","AI PC/品牌","PC/主機板/伺服器","全球PC與板卡品牌","★★★★☆","PC、主機板、電競與AI PC/伺服器品牌商","宏碁、技嘉、微星、Lenovo、Dell","中高：品牌、主機板技術、電競通路與伺服器布局","PC循環、庫存、匯率、競爭",1.04,"AI PC、電競、主機板、伺服器","下游品牌/系統","全球PC與板卡品牌","消費者、企業客戶、通路商、雲端/伺服器客戶"),
    "2376.TW": _v238_stock("技嘉","AI伺服器/品牌","主機板/顯卡/伺服器","板卡與AI伺服器品牌","★★★★☆","主機板、顯卡與伺服器產品供應商，AI伺服器題材受惠","華碩、微星、Supermicro、廣達","中高：板卡設計、伺服器產品線與品牌通路","AI訂單波動、GPU循環、庫存",1.06,"AI伺服器、主機板、顯卡、AI PC","下游品牌/系統","板卡與伺服器品牌","通路商、企業伺服器客戶、雲端與AI伺服器供應鏈"),
    "2377.TW": _v238_stock("微星","AI PC/品牌","電競PC/主機板/顯卡","電競與板卡品牌","★★★★☆","電競筆電、主機板、顯卡與AI PC品牌商","華碩、技嘉、宏碁、Lenovo","中高：電競品牌、板卡設計與全球通路","PC循環、GPU庫存、品牌競爭",1.04,"AI PC、電競、主機板、顯卡","下游品牌/通路","電競品牌主要廠","消費者、電競通路、企業採購與AI PC客戶"),
    "3045.TW": _v238_stock("台灣大","電信/雲端","電信/寬頻/雲端服務","台灣大型電信商","★★★★☆","行動通訊、寬頻、企業雲端與數位服務供應商","中華電、遠傳、亞太電信","中高：頻譜、用戶、通路與企業客戶","價格競爭、5G投資、法規",1.03,"電信、雲端、5G、資料中心","下游電信服務","台灣大型電信商","個人用戶、企業客戶、雲端與IDC客戶"),
    "2412.TW": _v238_stock("中華電","電信/雲端","電信/寬頻/IDC","台灣電信龍頭","★★★★★","行動、固網、寬頻、IDC與企業雲服務龍頭","台灣大、遠傳、國際電信商","高：網路基礎建設、用戶規模、企業與政府客戶","價格競爭、資本支出、法規",1.04,"電信、5G、IDC、雲端","下游電信/資料中心服務","台灣電信龍頭","個人用戶、企業、政府機關、IDC與雲端服務客戶"),
    "4904.TW": _v238_stock("遠傳","電信/雲端","電信/5G/企業服務","台灣大型電信商","★★★★☆","行動通訊、5G、企業ICT與數位服務供應商","中華電、台灣大","中高：用戶、頻譜、企業ICT與數位服務","價格競爭、5G資本支出、法規",1.03,"電信、5G、雲端、企業ICT","下游電信服務","台灣大型電信商","個人用戶、企業ICT、雲端與數位服務客戶"),
    "2331.TW": _v238_stock("精英","AI PC/主機板","主機板/迷你PC","主機板與系統供應商","★★★☆☆","主機板、迷你PC與商用電腦相關供應商","華碩、技嘉、微星、和碩","中：主機板設計與通路基礎","PC景氣、毛利率、競爭",1.02,"AI PC、主機板、邊緣運算","中下游系統/板卡","主機板與PC系統供應商","品牌PC、通路商、企業採購與工業電腦客戶"),
    "2395.TW": _v238_stock("研華","工業電腦","IPC/邊緣AI/工業物聯網","全球工業電腦龍頭之一","★★★★★","工業電腦、邊緣運算、工業物聯網與嵌入式平台供應商","凌華、Kontron、Siemens IPC","高：品牌、通路、軟硬整合與產業客戶","工業景氣、庫存、匯率",1.06,"邊緣AI、工業電腦、自動化、IoT","中下游IPC/系統平台","全球IPC龍頭之一","工業自動化、醫療、交通、零售、能源與邊緣AI客戶"),
    "6166.TW": _v238_stock("凌華","工業電腦","IPC/邊緣運算","工業電腦供應商","★★★☆☆","工業電腦、邊緣運算與自動化平台供應商","研華、Kontron、Siemens IPC","中：IPC產品線與產業應用","工業景氣、競爭、產品組合",1.04,"邊緣AI、工業電腦、自動化","中下游IPC/系統平台","工業電腦供應商","工業自動化、交通、醫療、能源與邊緣運算客戶"),
    "6414.TW": _v238_stock("樺漢","工業電腦","IPC/嵌入式/系統整合","工業電腦與系統整合商","★★★★☆","工業電腦、嵌入式系統、POS與智慧解決方案供應商","研華、凌華、振樺電","中高：客製化整合、通路與集團資源","專案波動、整合風險、景氣",1.05,"工業電腦、邊緣AI、智慧零售","中下游系統整合","IPC與嵌入式系統供應商","零售、工業、醫療、交通與企業數位化客戶"),
    "2498.TW": _v238_stock("宏達電","AR/VR/品牌","XR/VR/智慧裝置","XR品牌與平台商","★★★☆☆","VR/XR裝置、企業解決方案與沉浸式平台供應商","Meta、Sony、Pico、XR同業","中：XR品牌、硬體經驗與企業應用","消費需求、平台競爭、獲利波動",1.03,"XR、VR、元宇宙、邊緣AI","下游品牌/平台","XR品牌商","企業訓練、教育、醫療、消費者與XR開發者"),
    "3036.TW": _v238_stock("文曄","電子通路","半導體通路/代理","亞太半導體通路商","★★★★☆","IC代理、半導體通路與供應鏈服務商","大聯大、至上、益登、Arrow、Avnet","中高：代理線、客戶網路、物流與技術支援","庫存循環、毛利率、景氣",1.03,"半導體通路、IC代理、AI供應鏈","中游通路服務","亞太半導體通路商","IC設計公司、電子製造客戶、工業/車用/AI相關客戶"),
    "3702.TW": _v238_stock("大聯大","電子通路","半導體通路/代理","全球半導體通路龍頭之一","★★★★☆","半導體零組件通路、技術支援與供應鏈服務商","文曄、至上、Arrow、Avnet","中高：代理線、規模、供應鏈服務與客戶覆蓋","庫存循環、毛利率、景氣波動",1.03,"半導體通路、IC代理、AI供應鏈","中游通路服務","全球半導體通路龍頭之一","IC供應商、電子製造、工業/車用/AI硬體客戶"),
    "8112.TW": _v238_stock("至上","電子通路","記憶體/半導體通路","半導體通路商","★★★☆☆","記憶體、半導體與電子零組件通路服務商","文曄、大聯大、益登","中：代理線與客戶基礎","記憶體循環、庫存、毛利率",1.02,"半導體通路、記憶體、IC代理","中游通路服務","半導體通路商","記憶體供應商、電子製造與通路客戶"),
    "3048.TW": _v238_stock("益登","電子通路","IC代理/解決方案","半導體通路商","★★★☆☆","IC代理、技術支援與電子解決方案供應商","文曄、大聯大、至上","中：代理線與技術服務","庫存循環、毛利率、景氣",1.02,"半導體通路、IC代理、工業電子","中游通路服務","半導體通路商","IC供應商、電子製造、工業與車用客戶"),
    "9945.TW": _v238_stock("潤泰新","營建/資產","營建/資產/轉投資","大型營建資產公司","★★★☆☆","營建開發、資產與轉投資多元布局公司","華固、長虹、興富發、營建同業","中：土地資產、開發能力與轉投資價值","房市、利率、政策、轉投資波動",1.02,"營建、資產、轉投資","下游建設開發","大型營建資產公司","購屋客戶、商辦租戶、轉投資相關市場"),
    "2542.TW": _v238_stock("興富發","營建/建設","住宅/商辦開發","台灣大型建商","★★★★☆","住宅、商辦與土地開發大型建設公司","華固、長虹、遠雄、潤泰新","中高：土地庫存、推案能力與品牌","房市循環、利率、政策、營建成本",1.03,"營建、房地產、資產","下游建設開發","台灣大型建商","購屋客戶、投資客、商辦與不動產市場"),
    "2548.TW": _v238_stock("華固","營建/建設","住宅/商辦開發","高端住宅商辦建商","★★★★☆","雙北高端住宅、商辦與都更開發建商","興富發、長虹、遠雄、國建","中高：地段、品牌、都更開發能力","利率、政策、房市循環、營建成本",1.03,"營建、房地產、資產","下游建設開發","雙北建設公司","購屋客戶、商辦租售與不動產市場"),
    "2618.TW": _v238_stock("長榮航","航空/觀光","航空客運/貨運","台灣大型航空公司","★★★★☆","國際航空客運、貨運與旅遊需求受惠公司","華航、星宇航空、國際航空公司","中高：航線、品牌、機隊與貨運能力","油價、匯率、景氣、地緣政治",1.03,"航空、觀光、貨運","全球運輸服務","台灣大型航空公司","旅客、貨運承攬、企業差旅與旅遊客戶"),
    "2610.TW": _v238_stock("華航","航空/觀光","航空客運/貨運","台灣大型航空公司","★★★★☆","國際航空客運與貨運主要公司","長榮航、星宇航空、國際航空公司","中高：航線、貨運能力與品牌","油價、匯率、景氣、地緣政治",1.03,"航空、觀光、貨運","全球運輸服務","台灣大型航空公司","旅客、貨運承攬、企業差旅與旅遊客戶"),
    "2646.TW": _v238_stock("星宇航空","航空/觀光","航空客運","新興全服務航空公司","★★★☆☆","高端客運定位的新興航空公司，航線擴張中","長榮航、華航、國際航空公司","中：品牌定位、服務體驗與航線擴張潛力","油價、匯率、機隊擴張、獲利波動",1.03,"航空、觀光、消費升級","全球運輸服務","新興航空公司","旅客、商務客、旅遊與轉機市場"),
    "2727.TWO": _v238_stock("王品","餐飲/消費","連鎖餐飲","台灣連鎖餐飲品牌集團","★★★★☆","多品牌連鎖餐飲集團，受消費與展店影響","瓦城、豆府、餐飲同業","中高：品牌組合、展店與營運管理","消費景氣、人力成本、食材成本",1.04,"餐飲、民生消費、展店","下游消費服務","台灣連鎖餐飲品牌集團","終端消費者、商場通路與外送平台"),
    "2723.TWO": _v238_stock("美食-KY","餐飲/消費","咖啡/烘焙連鎖","連鎖咖啡餐飲品牌","★★★☆☆","85度C等咖啡與烘焙連鎖品牌經營商","王品、瓦城、國際咖啡餐飲品牌","中：品牌、展店與產品組合","展店、人力、原物料、消費景氣",1.03,"餐飲、咖啡、民生消費","下游消費服務","連鎖咖啡餐飲品牌","終端消費者、商場與街邊門市客戶"),
    "2753.TWO": _v238_stock("八方雲集","餐飲/消費","連鎖餐飲/鍋貼水餃","平價連鎖餐飲品牌","★★★★☆","鍋貼、水餃與平價餐飲連鎖品牌","王品、豆府、餐飲同業","中高：品牌、展店密度、中央廚房與供應鏈","食材、人力、展店速度、消費力",1.04,"餐飲、民生消費、展店","下游消費服務","台灣平價連鎖餐飲品牌","終端消費者、加盟主、外送平台與門市客戶"),
}
try:
    for _sym, _upd in V241_EXTRA_STOCKS.items():
        STOCK_DB[_sym] = {**STOCK_DB.get(_sym, {}), **_upd}
    ALIASES.clear()
    for _sym, _v in STOCK_DB.items():
        ALIASES[_sym.upper()] = _sym
        ALIASES[_sym.split('.')[0]] = _sym
        ALIASES[_v.get('name', _sym)] = _sym
        ALIASES[_v.get('name', _sym).upper()] = _sym
    OTC_CODES = {s.split('.')[0] for s in STOCK_DB if s.endswith('.TWO')}
except Exception:
    pass

# 覆蓋完成度：增加百分比，方便快速掌握真正完成率。
def v240_system_dashboard(df=None):
    if df is None:
        df = v230_rows_df()
    c = v240_completion_counts(df)
    total = max(int(c.get('個股資料庫', 0) or 0), 1)
    st.markdown('### 📊 資料庫完成度')
    cols = st.columns(5)
    cols[0].metric('系統版本', APP_VERSION)
    cols[1].metric('個股資料庫', c['個股資料庫'])
    cols[2].metric('完成估值', f"{c['完成估值']} / {total}")
    cols[3].metric('完成主要客戶', f"{c['完成主要客戶']} / {total}")
    cols[4].metric('完成競爭力', f"{c['完成競爭力']} / {total}")
    try:
        p1 = int(c['完成估值'] / total * 100)
        p2 = int(c['完成主要客戶'] / total * 100)
        p3 = int(c['完成競爭力'] / total * 100)
        st.progress(min(p1,100), text=f"估值完成率 {p1}%")
        st.progress(min(p2,100), text=f"主要客戶完成率 {p2}%")
        st.progress(min(p3,100), text=f"競爭力完成率 {p3}%")
    except Exception:
        pass
    st.caption(f"資料庫版本：{DB_VERSION}｜V241續補汽車、電信、工業電腦、電子通路、營建、航空、餐飲等常用搜尋個股。")

# 覆蓋設定頁，確認目前雲端版本與資料庫數量。
def settings_page():
    st.header('⚙️ 設定')
    st.write('系統版本：', APP_VERSION)
    st.write('資料庫版本：', DB_VERSION)
    st.write('資料庫股票數：', len(STOCK_DB))
    st.write('本版新增：汽車、電信、工業電腦、電子通路、營建、航空、餐飲等個股覆蓋。')
    try:
        v240_system_dashboard(v230_rows_df())
    except Exception:
        pass
    st.info('公開版優先提供現價、估值區間與產業位置；主要客戶若未正式揭露，會以公開供應鏈/產業合理推估並持續校正。')

# ===== V241.0 MORE STOCK COVERAGE + QUALITY DASHBOARD END =====

if __name__ == '__main__':
    main()
