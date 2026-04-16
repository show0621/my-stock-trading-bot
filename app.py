import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import os
from strategy_engine import get_trading_signal

# 1. 網頁初始化與標題
st.set_page_config(page_title="2026 量化指揮中心", layout="wide")

# --- 側邊欄：帳戶設定 ---
with st.sidebar:
    st.header("🎎 帳戶設定")
    initial_cap = st.number_input("初始資金 (TWD)", value=200000)
    tickers = {
        "台積電 (2330)": "2330.TW", 
        "鴻海 (2317)": "2317.TW", 
        "聯發科 (2454)": "2454.TW", 
        "廣達 (2382)": "2382.TW", 
        "台指期模擬 (^TWII)": "^TWII"
    }
    selected_name = st.selectbox("監控標的", list(tickers.keys()))
    ticker = tickers[selected_name]
    target_vol = st.slider("目標風險控管", 0.05, 0.25, 0.15)

# --- 2. 數據分析與指標計算 ---
signal = get_trading_signal(ticker, target_vol)
df = signal['history']

# 計算 MACD、SMA 與 籌碼指標 (成交量)
df.ta.macd(fast=12, slow=26, signal=9, append=True)
df.ta.sma(length=20, append=True)
df.ta.sma(length=60, append=True)

latest = df.iloc[-1]
prev = df.iloc[-2]
price = round(float(latest['Adj Close']), 1)
pos_ratio = round(float(signal['suggested_pos'] * 100), 1)
vol_val = round(float(signal['volatility'] * 100), 2)
mom = int(signal['mom_score'])

# --- 3. 分析師診斷邏輯 (MACD, K線, 籌碼) ---
# MACD
m_h = latest['MACDh_12_26_9']
macd_desc = "金叉向上，多頭動能轉強" if m_h > 0 and m_h > df['MACDh_12_26_9'].iloc[-2] else "趨勢盤整或動能轉弱"
# K線與均線
k_trend = "站穩月季線，呈現多頭排列" if price > latest['SMA_20'] and price > latest['SMA_60'] else "股價震盪偏弱，回測支撐中"
# 籌碼 (成交量比率)
vol_ratio = latest['Volume'] / df['Volume'].rolling(5).mean().iloc[-1]
chip_desc = "量增價穩，法人換手積極" if vol_ratio > 1.2 else "量縮盤整，籌碼沉澱中"

# --- 4. 模擬權益計算 (Equity Curve) ---
csv_path = "daily_status.csv"
if os.path.exists(csv_path):
    hist_df = pd.read_csv(csv_path)
    ticker_hist = hist_df[hist_df['Ticker'] == ticker].copy()
    ticker_hist['Daily_Return'] = ticker_hist['Price'].pct_change()
    ticker_hist['Equity'] = initial_cap * (1 + (ticker_hist['Daily_Return'] * ticker_hist['Suggested_Pos']).cumsum())
    current_equity = ticker_hist['Equity'].iloc[-1] if not ticker_hist.empty else initial_cap
else:
    hist_df = pd.DataFrame()
    current_equity = initial_cap

# --- 5. 期貨計算與稅費明細 ---
margin_rate = 0.135
margin_per_lot = price * 100 * margin_rate
target_investment = initial_cap * (pos_ratio / 100)
suggested_lots = int(target_investment / margin_per_lot) if margin_per_lot > 0 else 0

# 稅費預估 (來回)
tax_one_way = price * 100 * 0.00002
total_tax = tax_one_way * suggested_lots * 2
total_fee = 20 * suggested_lots * 2  # 預設單邊20元
total_cost = total_tax + total_fee
tick_profit = 100 * suggested_lots

# --- 6. 介面渲染 (日式專業風) ---
action_color = "#9F353A" if mom >= 1 else "#434343"
bg_light = "#FCEEEF" if mom >= 1 else "#F2F2F2"

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
        <div class="card"><div class="label">Current Price</div><div class="value">{price:,}</div></div>
        <div class="card"><div class="label">模擬總權益</div><div class="value" style="color:#B18D4D">{int(current_equity):,}</div></div>
        <div class="card"><div class="label">建議操作口數</div><div class="value">{suggested_lots} 口</div></div>
        <div class="card"><div class="label">建議持倉比</div><div class="value" style="color:{action_color};">{pos_ratio}%</div></div>
    </div>
    <div class="report-card">
        <div class="report-title">⚖️ 首席分析師盤後報告：{selected_name}</div>
        <b>【口數計算結果】</b><br>
        小型期貨(1口=100股)，保證金率 13.5%：每口需 <span class="highlight">{int(margin_per_lot):,} 元</span>。<br>
        建議買入 <span class="highlight">{suggested_lots} 口</span>，佔用保證金 {int(margin_per_lot * suggested_lots):,} 元，保留緩衝金 {int(current_equity - (margin_per_lot * suggested_lots)):,} 元。<br><br>
        <b>【預估稅費與損益】</b><br>
        來回期交稅：{int(total_tax)} 元 | 手續費：{int(total_fee)} 元 | <b>合計成本：約 {int(total_cost)} 元</b>。<br>
        <b>跳動損益：</b>每跳動 1 點，合約價值變動 <span class="highlight">{int(tick_profit)} 元</span>。<br><br>
        <b>【多維度技術分析】</b><br>
        • <b>MACD動能：</b>指標顯示 <span class="highlight">{macd_desc}</span> (柱狀值 {m_h:.2f})。<br>
        • <b>K線趨勢：</b>目前 <span class="highlight">{k_trend}</span>，趨勢架構穩定。<br>
        • <b>量價籌碼：</b>成交量比率為 {vol_ratio:.2f}，顯示 <span class="highlight">{chip_desc}</span>。
    </div>
</div>
"""
components.html(html_content, height=680)

# --- 7. 下方增加紀錄表與圖表 ---
st.markdown("### 📜 每日觀測與變動紀錄表")
if not hist_df.empty:
    st.dataframe(hist_df[hist_df['Ticker']==ticker].sort_values("Date", ascending=False), use_container_width=True, hide_index=True)

st.markdown("### 📈 專業指標視覺化")
tab1, tab2 = st.tabs(["趨勢 K 線 (20/60MA)", "MACD 動能圖"])
with tab1:
    fig_k = go.Figure()
    fig_k.add_trace(go.Scatter(x=df.index, y=df['Adj Close'], name="價格", line=dict(color="#434343")))
    fig_k.add_trace(go.Scatter(x=df.index, y=df['SMA_20_append'], name="20MA", line=dict(color="#B18D4D", dash='dot')))
    fig_k.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9")
    st.plotly_chart(fig_k, use_container_width=True)
with tab2:
    fig_m = go.Figure()
    fig_m.add_trace(go.Bar(x=df.index, y=df['MACDh_12_26_9'], name="MACD Histogram", marker_color="#9F353A"))
    fig_m.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9")
    st.plotly_chart(fig_m, use_container_width=True)
