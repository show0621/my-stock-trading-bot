import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

st.set_page_config(page_title="2026 量化指揮中心", layout="wide", initial_sidebar_state="collapsed")

with st.sidebar:
    st.header("🎎 帳戶設定")
    cap = st.number_input("初始資金", value=200000)
    ticker_map = {"台積電": "2330.TW", "鴻海": "2317.TW"}
    selected = st.selectbox("標的", list(ticker_map.keys()))
    t_vol = st.slider("目標風險", 0.05, 0.25, 0.15)

sig = get_trading_signal(ticker_map[selected], t_vol, cap)

if sig:
    # --- 頂部數據卡片 ---
    st.markdown(f"### 🚀 {selected} 一年回測結果：獲利 {sig['equity'] - cap:,} TWD (ROI: {sig['roi']}%)")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("最終淨值", f"{sig['equity']:,}")
    col2.metric("交易次數", f"{len(sig['ledger'])}")
    col3.metric("目前價格", f"{sig['price']:,}")
    col4.metric("YZ 波動率", f"{sig['volatility']*100:.1f}%")

    # --- 模擬帳本 ---
    st.markdown("### 📋 完整虛擬操作帳本")
    st.dataframe(pd.DataFrame(sig['ledger']), use_container_width=True)

    # --- 損益曲線圖 ---
    st.markdown("### 📈 帳戶淨值曲線 (Equity Curve)")
    fig_equity = go.Figure()
    fig_equity.add_trace(go.Scatter(y=sig['curve'], name="帳戶餘額", fill='tozeroy', line=dict(color="#B18D4D")))
    fig_equity.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", height=300)
    st.plotly_chart(fig_equity, use_container_width=True)

    # --- K線訊號圖 ---
    st.markdown("### 📉 買賣點位視覺化")
    fig_k = go.Figure()
    fig_k.add_trace(go.Scatter(x=sig['history'].index, y=sig['history']['Close'], name="股價", line=dict(color="#434343")))
    st.plotly_chart(fig_k, use_container_width=True)
