import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 頁面初始化
st.set_page_config(page_title="李孟霖 | 首席投研終端", layout="wide", initial_sidebar_state="expanded")

# 2. 終極防護 CSS (加入報告的響應式 RWD 設計)
css_style = """
<style>
    :root { color-scheme: light !important; }
    .stApp, .main { background-color: #F7F3E9 !important; }
    html, body, [class*="css"], p, span, div, h1, h2, h3, h4, h5, h6, label, li { 
        color: #000000 !important; font-family: 'Noto Serif TC', serif; 
    }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #D6D2C4; }
    header[data-testid="stHeader"] { background-color: transparent !important; }
    [data-testid="collapsedControl"] { background-color: #FFFFFF !important; border-radius: 50% !important; }
    [data-testid="collapsedControl"] svg { fill: #000000 !important; }
    [data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid #D6D2C4 !important; border-radius: 8px !important; }
    
    input, select, textarea { background-color: #FFFFFF !important; color: #000000 !important; -webkit-text-fill-color: #000000 !important; }
    button[data-testid="stNumberInputStepDown"], button[data-testid="stNumberInputStepUp"] { background-color: #F7F3E9 !important; color: #000000 !important; }
    button[data-testid="stNumberInputStepDown"] svg, button[data-testid="stNumberInputStepUp"] svg { fill: #000000 !important; }
    
    div[data-baseweb="select"] > div { background-color: #FFFFFF !important; border-color: #D6D2C4 !important; }
    div[data-baseweb="select"] span { color: #000000 !important; -webkit-text-fill-color: #000000 !important; }
    div[data-baseweb="select"] svg { fill: #000000 !important; }
    div[data-baseweb="popover"], div[data-baseweb="popover"] > div { background-color: #FFFFFF !important; }
    ul[role="listbox"], li[role="option"] { background-color: #FFFFFF !important; color: #000000 !important; }
    
    .status-grid {
        display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
        background: #FFFFFF; padding: 15px; border-radius: 10px; border: 1px solid #D6D2C4; margin-bottom: 20px;
    }
    .s-title { font-size: 12px; color: #666666; text-align: center; margin-bottom: 4px; }
    .s-val { font-size: 18px; font-weight: 600; color: #000000; text-align: center; }
    
    /* 報告專屬排版 CSS */
    .report-header {
        display: flex; justify-content: space-between; align-items: flex-start;
        border-bottom: 1px solid #E5E1D5; padding-bottom: 10px; margin-bottom: 15px;
    }
    .report-grid {
        display: grid; grid-template-columns: 1fr 1fr; gap: 25px; font-size: 14.5px; line-height: 1.7;
    }

    /* 手機版適配 */
    @media (max-width: 768px) {
        .status-grid { grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .report-header { flex-direction: column; gap: 8px; }
        .report-header div { text-align: left !important; max-width: 100% !important; }
        .report-grid { grid-template-columns: 1fr; gap: 15px; } 
    }
    .sidebar-footer { font-size: 11px; color: #888888; margin-top: 50px; border-top: 1px solid #EEE; padding-top: 10px; line-height: 1.5; }
</style>
"""
st.markdown(css_style, unsafe_allow_html=True)

# 3. 側邊欄設定
with st.sidebar:
    st.title("🎐 投資指揮中心")
    cap = st.number_input("本金設定", value=2000000)
    
    industry_map = {
        "半導體核心": {"台積電 (2330)": "2330.TW", "聯發科 (2454)": "2454.TW", "日月光 (3711)": "3711.TW"},
        "AI與伺服器": {"鴻海 (2317)": "2317.TW", "廣達 (2382)": "2382.TW", "緯穎 (6669)": "6669.TW"},
        "傳產與金控": {"富邦金 (2881)": "2881.TW", "中信金 (2891)": "2891.TW", "信錦 (1582)": "1582.TW"},
        "🔍 全台股手動輸入": "MANUAL"
    }
    selected_ind = st.radio("📁 產業類別", list(industry_map.keys()))
    
    if selected_ind == "🔍 全台股手動輸入":
        code = st.text_input("輸入代號", value="1582")
        ticker_symbol, ticker_name = f"{code}.TW", f"自選標的 ({code})"
    else:
        ticker_name = st.selectbox("🎯 選擇標的", list(industry_map[selected_ind].keys()))
        ticker_symbol = industry_map[selected_ind][ticker_name]

    st.markdown(f"""
    <div class="sidebar-footer">
        <b>作者：</b> 李孟霖<br>
        <b>版本：</b> 20260416-V01<br>
        <b>策略參考：</b><br>
        <span style="font-size:10px;">Time Series Momentum<br>(Tobias J. Moskowitz, Yao Hua Ooi, Lasse Heje Pedersen, 2012)</span>
    </div>
    """, unsafe_allow_html=True)

# --- 4. 執行引擎 ---
with st.spinner("載入量化數據中..."):
    sig = get_trading_signal(ticker_symbol, ticker_name, cap)

if sig:
    df, ledger_df, an, st_row = sig['history'], pd.DataFrame(sig['ledger']), sig['report'], sig['stats']

    # --- 5. 狀態牆 ---
    st.markdown(f"""
    <div class="status-grid">
        <div><div class="s-title">壓力 / 支撐位</div><div class="s-val">{st_row['Res']:.0f} / {st_row['Sup']:.0f}</div></div>
        <div><div class="s-title">停損 / 停利點</div><div class="s-val" style="color:#9F353A;">{st_row['SL']:.1f} / {st_row['TP']:.1f}</div></div>
        <div><div class="s-title">趨勢信心 / YZ年化</div><div class="s-val">{st_
