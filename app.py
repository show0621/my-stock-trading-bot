import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import os
from strategy_engine import get_trading_signal

# 1. 網頁初始化與佈局優化
st.set_page_config(page_title="2026 量化指揮中心", layout="wide", initial_sidebar_state="collapsed")

# 鎖定 Streamlit 頂層容器防止回彈 (CSS Injection)
st.markdown("<style>iframe { overscroll-behavior: none; }</style>", unsafe_allow_html=True)

# --- 側邊欄設定 ---
with st.sidebar:
    st.title("🎐 操盤導覽")
    initial_cap = st.number_input("初始資金 (TWD)", value=200000)
    tickers = {"台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW"}
    selected_name = st.selectbox("標的監控", list(tickers.keys()))
    target_vol = st.slider("目標風險控管", 0.05, 0.25, 0.15)

# --- 2. 數據獲取 ---
sig = get_trading_signal(tickers[selected_name], target_vol)
df = sig['history']
latest = df.iloc[-1]
price = round(float(sig['price']), 1)
pos_ratio = round(float(sig['suggested_pos'] * 100), 1)
vol_val = round(float(sig['volatility'] * 100), 1)

# 期貨計算細節
margin_rate = 0.135
margin_per_lot = price * 100 * margin_rate
target_inv = initial_cap * (pos_ratio / 100)
suggested_lots = int(target_inv / margin_per_lot) if margin_per_lot > 0 else 0
used_margin = margin_per_lot * suggested_lots
buffer_cap = initial_cap - used_margin

# 風控與稅費
sl_price = round(price * 0.955, 1) # -4.5%
tp_price = round(price * 1.06, 1)  # +6%
tax_total = (price * 100 * 0.00002 * 2 + 40) * suggested_lots

# --- 3. 響應式日式介面 (加入滑動鎖
