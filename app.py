import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

st.set_page_config(page_title="李孟霖 | AI首席投研終端", layout="wide")

# 防斷行 CSS 積木 (完整版面)
css = (
    "<style>"
    ":root{color-scheme:light !important;}"
    ".stApp,.main{background-color:#F7F3E9 !important;}"
    "html,body,p,span,div,h1,h2,h3,h4,h5,h6,label,li{color:#000000 !important;font-family:'Noto Serif TC',serif;}"
    ".status-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;background:#FFFFFF;padding:15px;border-radius:10px;border:1px solid #D6D2C4;margin-bottom:20px;}"
    ".s-title{font-size:12px;color:#666666;text-align:center;}"
    ".s-val{font-size:16px;font-weight:600;color:#000000;text-align:center;}"
    ".report-header{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid #E5E1D5;padding-bottom:10px;margin-bottom:15px;}"
    ".report-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;font-size:14.5px;line-height:1.7;}"
    "@media (max-width:768px){.status-grid{grid-template-columns:repeat(2,1fr);}.report-grid{grid-template-columns:1fr;}}"
    "</style>"
)
st.markdown(css, unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 AI 投資指揮中心")
    api_k = st.text_input("🔑 Groq API Key", type="password", placeholder="貼上後按 Enter")
    cap = st.number_input("本金設定", value=2000000)
    ind_map = {
        "半導體核心": {"台積電 (2330)": "2330.TW", "聯發科 (2454)": "2454.TW"},
        "AI與伺服器": {"鴻海 (2317)": "2317.TW", "廣達 (2382)": "2382.TW", "緯穎 (6669)": "6669.TW"},
        "🔍 全台股手動輸入": "MANUAL"
    }
    sel_ind = st.radio("📁 產業類別", list(ind_map.keys()))
    if sel_ind == "🔍 全台股手動輸入":
        raw_code = st.text_input("輸入代號", value="2382")
        t_sym, t_nm = f"{raw_code}.TW", f"自選 ({raw_code})"
    else:
        t_nm = st.selectbox("🎯 選擇標的", list(ind_map[sel_ind].keys()))
        t_sym = ind_map[sel_ind][t_nm]

with st.spinner("🚀 AI 正在深度分析籌碼情境..."): 
    sig = get_trading_signal(t_sym, t_nm, cap, api_k)

if sig:
    df, l_df, an, sr = sig['history'], pd.DataFrame(sig['ledger']), sig['report'], sig['stats']
    
    # 狀態牆數值
    v_r, v_s = str(int(sr['High'])), str(int(sr['Low']))
    v_sl, v_
