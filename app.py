import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import os
from strategy_engine import get_trading_signal

st.set_page_config(page_title="2026 量化指揮中心", layout="wide")

# --- 側邊欄 ---
with st.sidebar:
    st.header("🎎 帳戶設定")
    initial_cap = st.number_input("初始資金 (TWD)", value=200000)
    tickers = {"台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW", "廣達 (2382)": "2382.TW", "台指期 (^TWII)": "^TWII"}
    selected_name = st.selectbox("監控標的", list(tickers.keys()))
    target_vol = st.slider("目標風險控管", 0.05, 0.25, 0.15)

# --- 數據處理 ---
signal = get_trading_signal(tickers[selected_name], target_vol)
df = signal['history']
latest = df.iloc[-1]
price = round(float(latest['Adj Close']), 1)
pos_ratio = round(float(signal['suggested_pos'] * 100), 1)
vol_val = round(float(signal['volatility'] * 100), 2)
mom = int(signal['mom_score'])

# 分析師診斷邏輯
m_h = latest['MACD_Hist']
macd_desc = "動能金叉轉強" if m_h > 0 else "動能偏弱盤整"
k_trend = "多頭架構 (站上20/60MA)" if price > latest['SMA_20'] and price > latest['SMA_60'] else "趨勢盤整中"
vol_ratio = latest['Volume'] / df['Volume'].rolling(5).mean().iloc[-1]
chip_desc = "主力換手積極" if vol_ratio > 1.2 else "籌碼沉澱盤整"

# 期貨計算
margin_per_lot = price * 100 * 0.135
suggested_lots = int((initial_cap * (pos_ratio/100)) / margin_per_lot) if margin_per_lot > 0 else 0
total_cost = (price * 100 * 0.00002 * 2 + 40) * suggested_lots

# --- 介面渲染 ---
html_content = f"""
<div style="background:#F7F3E9; color:#434343; font-family:serif; padding:25px; border-radius:12px; border:2px solid #D6D2C4;">
    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:15px; margin-bottom:25px;">
        <div style="background:#FFF; padding:15px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:11px;">Current Price</div><div style="font-size:24px; font-weight:600;">{price:,}</div>
        </div>
        <div style="background:#FFF; padding:15px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:11px;">建議口數</div><div style="font-size:24px; color:#B18D4D;">{suggested_lots} 口</div>
        </div>
        <div style="background:#FFF; padding:15px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:11px;">YZ 波動率</div><div style="font-size:24px;">{vol_val}%</div>
        </div>
        <div style="background:#FFF; padding:15px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:11px;">建議持倉比</div><div style="font-size:24px; color:#9F353A;">{pos_ratio}%</div>
        </div>
    </div>
    <div style="background:#FFF; padding:20px; border:1px solid #E5E1D5; line-height:1.8; font-size:14px;">
        <div style="color:#B18D4D; font-size:18px; font-weight:600; border-bottom:1px solid #E5E1D5; margin-bottom:15px;">⚖️ 首席分析師報告：{selected_name}</div>
        <b>【交易執行】</b> 小型期貨每口保證金：{int(margin_per_lot):,} 元。建議持有 {suggested_lots} 口。<br>
        預估成本：約 {int(total_cost)} 元 | 每跳動一點損益：{int(suggested_lots * 100)} 元。<br><br>
        <b>【深度診斷】</b><br>
        • MACD 動能：{macd_desc} (柱狀值 {m_h:.2f})。<br>
        • K線趨勢：{k_trend}。<br>
        • 籌碼結構：成交量比率 {vol_ratio:.2f}，目前 {chip_desc}。
    </div>
</div>
"""
components.html(html_content, height=520)

# --- 歷史紀錄與圖表 ---
st.markdown("### 📜 歷史觀測紀錄")
csv_path = "daily_status.csv"
if os.path.exists(csv_path):
    st.dataframe(pd.read_csv(csv_path).query(f"Ticker=='{tickers[selected_name]}'").sort_values("Date", ascending=False), use_container_width=True)

st.markdown("### 📈 技術指標追蹤")
t1, t2 = st.tabs(["K線趨勢", "MACD 柱狀圖"])
with t1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df.index, y=df['Adj Close'], name="價格", line=dict(color="#434343")))
    fig1.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name="20MA", line=dict(color="#B18D4D", dash='dot')))
    fig1.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9")
    st.plotly_chart(fig1, use_container_width=True)
with t2:
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name="MACD Hist", marker_color="#9F353A"))
    fig2.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9")
    st.plotly_chart(fig2, use_container_width=True)
