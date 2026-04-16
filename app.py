import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import os
from strategy_engine import get_trading_signal

st.set_page_config(page_title="2026 量化指揮中心", layout="wide")

# --- 側邊欄：帳戶設定 ---
with st.sidebar:
    st.header("🎎 帳戶設定")
    initial_cap = st.number_input("初始資金 (TWD)", value=200000)
    tickers = {
        "台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", 
        "聯發科 (2454)": "2454.TW", "廣達 (2382)": "2382.TW", 
        "台指期模擬 (^TWII)": "^TWII"
    }
    selected_name = st.selectbox("監控標的", list(tickers.keys()))
    ticker = tickers[selected_name]
    target_vol = st.slider("目標風險控管", 0.05, 0.25, 0.15)

# --- 核心數據 ---
signal = get_trading_signal(ticker, target_vol)
df = signal['history']
latest = df.iloc[-1]
price = round(float(latest['Adj Close']), 1)
pos_ratio = round(float(signal['suggested_pos'] * 100), 1)
vol_val = round(float(signal['volatility'] * 100), 2)
mom = int(signal['mom_score'])

# --- 專業分析邏輯 ---
m_h = latest['MACD_Hist']
macd_desc = "動能金叉轉強" if m_h > 0 else "趨勢盤整或動能轉弱"
k_trend = "強勢多頭 (站上20MA/60MA)" if price > latest['SMA_20'] and price > latest['SMA_60'] else "區間震盪，回測支撐中"
vol_ratio = latest['Volume'] / df['Volume'].rolling(5).mean().iloc[-1]
chip_desc = "主力換手積極" if vol_ratio > 1.2 else "籌碼沉澱盤整"

# 期貨與口數計算
margin_rate = 0.135
margin_per_lot = price * 100 * margin_rate
suggested_lots = int((initial_cap * (pos_ratio/100)) / margin_per_lot) if margin_per_lot > 0 else 0
total_tax_fee = (price * 100 * 0.00002 * 2 + 40) * suggested_lots
tick_profit = 100 * suggested_lots

# --- 介面渲染 (日式和風) ---
action_color = "#9F353A" if mom >= 1 else "#434343"

html_content = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600&family=IBM+Plex+Mono&display=swap');
    .jp-container {{ background: #F7F3E9; color: #434343; font-family: 'Noto Serif TC', serif; padding: 25px; border-radius: 12px; border: 2px solid #D6D2C4; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 25px; }}
    .card {{ background: #FFFFFF; padding: 15px; border: 1px solid #E5E1D5; border-radius: 8px; text-align: center; }}
    .label {{ color: #8C8C8C; font-size: 11px; margin-bottom: 8px; text-transform: uppercase; }}
    .value {{ font-family: 'IBM Plex Mono', monospace; font-size: 24px; font-weight: 600; }}
    .report-card {{ background: #FFFFFF; padding: 25px; border-radius: 8px; border: 1px solid #E5E1D5; line-height: 1.8; font-size: 14px; }}
    .report-title {{ color: #B18D4D; font-weight: 600; font-size: 18px; margin-bottom: 15px; border-bottom: 1px solid #E5E1D5; padding-bottom: 5px; }}
    .highlight {{ color: #9F353A; font-weight: 600; }}
</style>
<div class="jp-container">
    <div class="grid">
        <div class="card"><div class="label">Price</div><div class="value">{price:,}</div></div>
        <div class="card"><div class="label">建議操作口數</div><div class="value" style="color:#B18D4D">{suggested_lots} 口</div></div>
        <div class="card"><div class="label">YZ 波動率</div><div class="value">{vol_val}%</div></div>
        <div class="card"><div class="label">建議持倉比</div><div class="value" style="color:{action_color};">{pos_ratio}%</div></div>
    </div>
    <div class="report-card">
        <div class="report-title">⚖️ 首席分析師報告：{selected_name}</div>
        <b>【計算詳情】</b> 小型期貨每口保證金率 13.5%：<span class="highlight">{int(margin_per_lot):,} 元</span>。<br>
        預估持有 {suggested_lots} 口，佔用資金 {int(margin_per_lot * suggested_lots):,} 元，保留緩衝金 {int(initial_cap - (margin_per_lot * suggested_lots)):,} 元。<br>
        預估來回成本 (稅+費)：約 {int(total_tax_fee)} 元 | 每跳動一點損益：<span class="highlight">{int(tick_profit)} 元</span>。<br><br>
        <b>【深度診斷】</b><br>
        • <b>MACD 動能：</b>{macd_desc} (柱狀值 {m_h:.2f})。<br>
        • <b>K線趨勢：</b>{k_trend}，多頭趨勢觀察中。<br>
        • <b>量價籌碼：</b>成交量比率為 {vol_ratio:.2f}，目前顯示 {chip_desc}。<br><br>
        <div style="font-size:12px; color:#8C8C8C; border-top:1px dashed #D6D2C4; padding-top:10px;">
        ⚠️ 本儀表板為模擬投資工具，不構成實際投資建議。期貨具高槓桿風險，請自行評估。
        </div>
    </div>
</div>
"""
components.html(html_content, height=620)

# --- 圖表與紀錄表 ---
st.markdown("### 📜 歷史觀測紀錄")
csv_path = "daily_status.csv"
if os.path.exists(csv_path):
    st.dataframe(pd.read_csv(csv_path).query(f"Ticker=='{ticker}'").sort_values("Date", ascending=False), use_container_width=True)

st.markdown("### 📈 技術指標視覺化")
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
