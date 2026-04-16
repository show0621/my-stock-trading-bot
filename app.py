import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

st.set_page_config(page_title="2026 量化波段室", layout="wide")

with st.sidebar:
    st.header("🎎 帳戶設定")
    cap = st.number_input("初始資金", value=200000)
    ticker = st.selectbox("標的", ["2330.TW", "2317.TW", "2454.TW"])

sig = get_trading_signal(ticker, initial_cap=cap)
df = sig['history']
ledger_df = pd.DataFrame(sig['ledger'])

# --- 1. 專業分析師日誌 (HTML) ---
html_log = f"""
<div style="background:#F7F3E9; padding:20px; border:1px solid #D6D2C4; border-radius:10px; font-family:serif;">
    <h3 style="color:#B18D4D; border-bottom:1px solid #D6D2C4;">⚖️ 7天波段策略分析</h3>
    <p>目前 <b>RSI: {sig['rsi']:.1f}</b> | <b>MACD柱狀: {sig['macd']:.2f}</b></p>
    <p>策略嚴格執行 <b>7日自動平倉機制</b>。當前淨值：<span style="color:#9F353A; font-weight:600;">{sig['equity']:,} TWD</span></p>
    <p style="font-size:12px; color:#8C8C8C;">※ 結合 K 棒形態學（吞噬偵測）與 TEJ 動能過濾。</p>
</div>
"""
components.html(html_log, height=200)

# --- 2. 歷史紀錄表 ---
st.markdown("### 📜 7天波段操盤帳本")
st.dataframe(ledger_df, use_container_width=True)

# --- 3. 買賣點位視覺化 (關鍵：三角形圖示) ---
st.markdown("### 📈 買賣訊號視覺化")
fig = go.Figure()

# 主線
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="股價", line=dict(color="#434343", width=1)))

# 標註買入點 (紅三角形)
buys = ledger_df[ledger_df['動作'] == "▲ 買入"]
fig.add_trace(go.Scatter(
    x=pd.to_datetime(buys['日期']), y=buys['價格'],
    mode='markers', name='買入訊號',
    marker=dict(symbol='triangle-up', size=12, color='#9F353A')
))

# 標註賣出點 (綠三角形)
sells = ledger_df[ledger_df['動作'] == "▼ 賣出"]
fig.add_trace(go.Scatter(
    x=pd.to_datetime(sells['日期']), y=sells['價格'],
    mode='markers', name='賣出訊號',
    marker=dict(symbol='triangle-down', size=12, color='#3A5F41')
))

fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=500)
st.plotly_chart(fig, use_container_width=True)
