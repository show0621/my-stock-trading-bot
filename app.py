import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 頁面初始化
st.set_page_config(page_title="2026 首席投研終端", layout="wide", initial_sidebar_state="expanded")

# 2. 精確防亂碼 CSS (確保文字黑化與圖標正常)
css_code = """
<style>
    .stApp { background-color: #F7F3E9; }
    .stMarkdown div p, .stMarkdown div li, h1, h2, h3, label {
        color: #000000 !important;
        font-family: 'Noto Serif TC', serif;
    }
    .stExpander svg { fill: #434343 !important; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #D6D2C4; }
    [data-testid="stSidebar"] * { color: #000000 !important; }
    div[data-baseweb="popover"] { z-index: 10000 !important; }
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; border-radius: 8px !important; }
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# 3. 產業資料庫 (新增信錦)
industry_map = {
    "半導體核心": {"台積電 (2330)": "2330.TW", "聯發科 (2454)": "2454.TW", "日月光 (3711)": "3711.TW"},
    "AI與伺服器": {"鴻海 (2317)": "2317.TW", "廣達 (2382)": "2382.TW", "緯穎 (6669)": "6669.TW"},
    "金融/傳產/其他": {"富邦金 (2881)": "2881.TW", "中信金 (2891)": "2891.TW", "信錦 (1582)": "1582.TW"},
    "🔍 全台股手動輸入": "MANUAL"
}

with st.sidebar:
    st.title("🎐 投資指揮中心")
    cap = st.number_input("本金設定", value=200000)
    selected_ind = st.radio("📁 產業類別", list(industry_map.keys()))
    
    if selected_ind == "🔍 全台股手動輸入":
        code = st.text_input("輸入代號 (如: 1582)", value="1582")
        ticker_symbol = f"{code}.TW"
        ticker_name = f"自選標的 ({code})"
    else:
        ticker_name = st.selectbox("🎯 選擇標的", list(industry_map[selected_ind].keys()))
        ticker_symbol = industry_map[selected_ind][ticker_name]

# --- 4. 執行分析引擎 ---
with st.spinner("載入量化數據中..."):
    sig = get_trading_signal(ticker_symbol, ticker_name, cap)

if sig is not None:
    df = sig['history']
    ledger_df = pd.DataFrame(sig['ledger'])
    an = sig['report']
    st_row = sig['stats']

    # --- 5. 專業操盤狀態牆 ---
    st.markdown(f"""
    <div style="background:#FFFFFF; padding:15px; border-radius:10px; border:1px solid #D6D2C4; display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; margin-bottom:20px;">
        <div style="text-align:center;"><div style="font-size:12px; color:#666;">壓力 / 支撐位</div><div style="font-size:19px; font-weight:600; color:#000;">{st_row['Res']:.0f} / {st_row['Sup']:.0f}</div></div>
        <div style="text-align:center;"><div style="font-size:12px; color:#666;">停損 / 停利點</div><div style="font-size:19px; font-weight:600; color:#9F353A;">{st_row['SL']:.1f} / {st_row['TP']:.1f}</div></div>
        <div style="text-align:center;"><div style="font-size:12px; color:#666;">趨勢信心 / YZ年化波動</div><div style="font-size:19px; font-weight:600; color:#000;">{st_row['Confidence']:.2f} / {st_row['YZ_Vol']:.1%}</div></div>
        <div style="text-align:center;"><div style="font-size:12px; color:#666;">動態配置權重</div><div style="font-size:19px; font-weight:600; color:#B18D4D;">{st_row['Weight']:.1%}</div></div>
    </div>
    """, unsafe_allow_html=True)

    # --- 6. 雙向新聞與深度報告
