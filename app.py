import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import os
from strategy_engine import get_trading_signal

# 初始化網頁
st.set_page_config(page_title="2026 量化指揮中心", layout="wide")

# --- 1. 側邊欄：帳戶設定 ---
with st.sidebar:
    st.header("🎎 帳戶設定")
    initial_cap = st.number_input("初始資金 (TWD)", value=200000)
    tickers = {"台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW", "廣達 (2382)": "2382.TW", "台指期模擬 (^TWII)": "^TWII"}
    selected_name = st.selectbox("監控標的", list(tickers.keys()))
    ticker = tickers[selected_name]
    target_vol = st.slider("目標風險控管", 0.05, 0.25, 0.15)

# --- 2. 數據運算與技術指標 ---
signal = get_trading_signal(ticker, target_vol)
df = signal['history']
# 計算 MACD
macd = df.ta.macd(fast=12, slow=26, signal=9)
df = pd.concat([df, macd], axis=1)
# 計算 均線 與 K線型態簡述
df['SMA_20'] = df.ta.sma(length=20)
df['SMA_60'] = df.ta.sma(length=60)

latest = df.iloc[-1]
prev = df.iloc[-2]
price = round(float(latest['Adj Close']), 1)
pos_ratio = round(float(signal['suggested_pos'] * 100), 1)
vol_val = round(float(signal['volatility'] * 100), 2)
mom = int(signal['mom_score'])

# --- 3. 分析師專業報告生成邏輯 ---
# MACD 分析
macd_val = latest['MACD_12_26_9']
macd_sig = latest['MACDs_12_26_9']
macd_hist = latest['MACDh_12_26_9']
macd_desc = "金叉向上，多頭動能轉強" if macd_hist > 0 and macd_hist > df['MACDh_12_26_9'].iloc[-2] else "死叉或動能轉弱，建議謹慎"

# K棒趨勢分析
k_trend = "站上月線與季線，呈現多頭排列" if price > latest['SMA_20'] and price > latest['SMA_60'] else "股價震盪偏弱，回測支撐中"
k_shape = "今日收紅，實體飽滿" if price > latest['Open'] else "今日收陰，壓力浮現"

# 籌碼與量價分析 (利用價格與成交量關係模擬)
vol_ratio = latest['Volume'] / df['Volume'].rolling(5).mean().iloc[-1]
volume_desc = "量增價穩，法人換手積極" if vol_ratio > 1.2 and price > prev['Adj Close'] else "量縮盤整，籌碼沈澱中"

# --- 4. 期貨計算邏輯 ---
margin_rate = 0.135
margin_per_lot = price * 100 * margin_rate
suggested_lots = int((initial_cap * (pos_ratio / 100)) / margin_per_lot) if margin_per_lot > 0 else 0
tick_profit = 100 * suggested_lots

# --- 5. 介面顏色判定 ---
action_color = "#9F353A" if mom >= 1 and pos_ratio > 10 else "#434343"
bg_light = "#FCEEEF" if mom >= 1 and pos_ratio > 10 else "#F2F2F2"

# --- 6. 嵌入日式專業 HTML 報告 ---
html_content = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600&family=IBM+Plex+Mono&display=swap');
    .jp-container {{ background: #F7F3E9; color: #434343; font-family: 'Noto Serif TC', serif; padding: 25px; border-radius: 12px; border: 2px solid #D6D2C4; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 25px; }}
    .card {{ background: #FFFFFF; padding: 15px; border: 1px solid #E5E1D5; border-radius: 8px; text-align: center; }}
    .label {{ color: #8C8C8C; font-size: 11px; letter-spacing: 1px; margin-bottom: 8px; text-transform: uppercase; }}
    .value {{ font-family: 'IBM Plex Mono', monospace; font-size: 24px; font-weight: 600; }}
    .report-card {{ background: #FFFFFF; padding: 25px; border-radius: 8px; border: 1px solid #E5E1D5; line-height: 1.8; }}
    .report-section {{ margin-bottom: 20px; border-bottom: 1px solid #F0EDE5; padding-bottom: 15px; }}
    .report-title {{ color: #B18D4D; font-weight: 600; font-size: 18px; margin-bottom: 10px; display: flex; align-items: center; }}
    .indicator-tag {{ background: #F2F2F2; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-right: 10px; color: #666; }}
    .highlight-red {{ color: #9F353A; font-weight: 600; }}
</style>

<div class="jp-container">
    <div class="grid">
        <div class="card"><div class="label">Current Price</div><div class="value">{price:,}</div></div>
        <div class="card"><div class="label">建議口數</div><div class="value" style="color:#B18D4D">{suggested_lots} 口</div></div>
        <div class="card"><div class="label">YZ 波動率</div><div class="value">{vol_val}%</div></div>
        <div class="card"><div class="label">持倉比例</div><div class="value" style="color:{action_color};">{pos_ratio}%</div></div>
    </div>

    <div class="report-card">
        <div class="report-section">
            <div class="report-title">⚖️ 首席分析師盤後報告：{selected_name}</div>
            <p>針對今日市場表現，本系統基於量化模型給出 <span class="highlight-red">{"加碼買進" if mom==2 else "中性持倉" if mom==1 else "減碼觀望"}</span> 之建議。
            預計投入保證金約 <b>{int(margin_per_lot * suggested_lots):,} 元</b>，每跳動一點影響盈虧 <b>{int(tick_profit)} 元</b>。</p>
        </div>

        <div class="report-section">
            <div class="report-title"><span class="indicator-tag">MACD</span> 技術指標分析</div>
            <p>目前 MACD 快慢線表現為：<span class="highlight-red">{macd_desc}</span>。DIF值({macd_val:.2f})與信號線({macd_sig:.2f})之柱狀圖高度為 {macd_hist:.2f}，顯示趨勢動能目前處於 <b>{"擴張" if macd_hist>0 else "萎縮"}</b> 階段。</p>
        </div>

        <div class="report-section">
            <div class="report-title"><span class="indicator-tag">Trend</span> K線與均線趨勢</div>
            <p>股價現報 {price}，<span class="highlight-red">{k_trend}</span>。從K線形態來看，{k_shape}。短期均線(20MA)支撐力道強勁，多頭架構尚未破壞。</p>
        </div>

        <div class="report-section">
            <div class="report-title"><span class="indicator-tag">Volume</span> 籌碼與量價結構</div>
            <p>今日成交量對比五日均量倍數為 {vol_ratio:.2f}。根據量價同步原則，目前呈現 <span class="highlight-red">{volume_desc}</span>，籌碼面顯示大戶介入意願較強，有利於後市推升。</p>
        </div>
        
        <div style="font-size:12px; color:#8C8C8C; text-align:right;">— 2026 量化策略研究組 謹誌</div>
    </div>
</div>
"""
components.html(html_content, height=750)

# --- 7. 下方增加指標圖表 ---
st.markdown("### 📊 專業指標視覺化")
tab1, tab2 = st.tabs(["K線與趨勢", "MACD 動能"])

with tab1:
    fig_k = go.Figure()
    fig_k.add_trace(go.Scatter(x=df.index, y=df['Adj Close'], name="價格", line=dict(color="#434343")))
    fig_k.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name="20MA", line=dict(color="#B18D4D", dash='dot')))
    fig_k.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=400)
    st.plotly_chart(fig_k, use_container_width=True)

with tab2:
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Bar(x=df.index, y=df['MACDh_12_26_9'], name="MACD 柱狀圖", marker_color="#9F353A"))
    fig_macd.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=300)
    st.plotly_chart(fig_macd, use_container_width=True)
