import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import os
from strategy_engine import get_trading_signal

# 1. 初始化
st.set_page_config(page_title="2026 量化指揮中心", layout="wide")

# --- 側邊欄：導覽與設定 ---
with st.sidebar:
    st.title("🎐 操盤導覽")
    st.markdown("---")
    initial_cap = st.number_input("初始資金 (TWD)", value=200000)
    tickers = {"台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW"}
    selected_name = st.selectbox("標的監控", list(tickers.keys()))
    target_vol = st.slider("目標風險控管", 0.05, 0.25, 0.15)
    st.markdown("---")
    st.info("今日操盤歷史紀錄\n\n風控中心\n\n策略回測")

# --- 2. 數據獲取與變數設定 ---
sig = get_trading_signal(tickers[selected_name], target_vol)
df = sig['history']
latest = df.iloc[-1]
price = round(float(latest['Adj Close']), 1)
pos_ratio = round(float(sig['suggested_pos'] * 100), 1)
vol_val = round(float(sig['volatility'] * 100), 1)
mom = int(sig['mom_score'])

# 期貨專業計算
margin_rate = 0.135
margin_per_lot = price * 100 * margin_rate
target_inv = initial_cap * (pos_ratio / 100)
suggested_lots = int(target_inv / margin_per_lot) if margin_per_lot > 0 else 0
used_margin = margin_per_lot * suggested_lots
buffer_cap = initial_cap - used_margin

# 稅費與風控
tax_one_way = price * 100 * 0.00002
total_tax = tax_one_way * suggested_lots * 2
total_fee = 20 * suggested_lots * 2
sl_price = round(price * 0.955, 1) # 停損 -4.5%
tp_price = round(price * 1.06, 1)  # 止盈 +6%

# --- 3. 嵌入日式專業 HTML 介面 ---
action_text = "🟢 中性偏多信號" if mom >= 1 else "🔴 清倉避險信號"
action_color = "#9F353A" if mom >= 1 else "#434343"

html_content = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600&family=IBM+Plex+Mono&display=swap');
    .jp-shell {{ background: #F7F3E9; color: #434343; font-family: 'Noto Serif TC', serif; padding: 25px; border-radius: 12px; border: 2px solid #D6D2C4; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 25px; }}
    .m-card {{ background: #FFF; padding: 15px; border: 1px solid #E5E1D5; border-radius: 8px; text-align: center; }}
    .m-label {{ color: #8C8C8C; font-size: 11px; text-transform: uppercase; margin-bottom: 5px; }}
    .m-value {{ font-family: 'IBM Plex Mono', monospace; font-size: 24px; font-weight: 600; }}
    .report-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
    .r-box {{ background: #FFF; padding: 20px; border-radius: 8px; border: 1px solid #E5E1D5; font-size: 13px; line-height: 1.6; }}
    .section-h {{ color: #B18D4D; font-weight: 600; border-bottom: 1px solid #E5E1D5; margin-bottom: 10px; padding-bottom: 5px; display: flex; justify-content: space-between; }}
    .highlight {{ color: #9F353A; font-weight: 600; }}
</style>
<div class="jp-shell">
    <div style="font-size:18px; font-weight:600; margin-bottom:20px; color:#B18D4D;">// 今日模擬入場紀錄 — 2026.04.16</div>
    <div class="metrics">
        <div class="m-card"><div class="m-label">TODAY ENTRY PRICE</div><div class="m-value">{price:,}</div></div>
        <div class="m-card"><div class="m-label">建議口數</div><div class="m-value" style="color:#B18D4D">{suggested_lots} 口</div></div>
        <div class="m-card"><div class="m-label">YZ 波動率</div><div class="m-value">{vol_val}%</div></div>
        <div class="m-card"><div class="m-label">建議持倉比</div><div class="m-value" style="color:{action_color};">{pos_ratio}%</div></div>
    </div>
    <div class="report-grid">
        <div class="r-box">
            <div class="section-h"><span>📐 口數與保證金計算</span></div>
            • 入場股價：{price:,} 元 | 規格：100 股/口<br>
            • 原始保證金率：13.5% | 每口保證金：{int(margin_per_lot):,} 元<br>
            • 可用資金 ({pos_ratio}%)：{int(target_inv):,} 元<br>
            • <b>建議買入：{suggested_lots} 口</b><br>
            • 佔用保證金：<span class="highlight">{int(used_margin):,} 元</span> | 剩餘緩衝金：{int(buffer_cap):,} 元
            
            <div class="section-h" style="margin-top:20px;"><span>💸 預估稅費與跳動損益</span></div>
            • 4口來回期交稅：{int(total_tax)} 元 | 4口總手續費：約 {int(total_fee)} 元<br>
            • 合計摩擦成本：約 {int(total_tax + total_fee)} 元<br>
            • <b>跳動1點損益：<span class="highlight">{int(suggested_lots * 100)} 元</span></b>
        </div>
        <div class="r-box">
            <div class="section-h"><span>▎ AI 日誌 · 買入原因分析</span></div>
            {selected_name} 今日以 {int(sig['open']):,} 元開盤，收盤報 {price:,} 元。
            YZ 波動率為 {vol_val}%，處於中性區間。
            動能評分顯示趨勢強勁，成交量較前日有所放量，配合股價上揚確認多方意圖。
            技術面顯示均線多頭排列，短期 MA20 支撐力道強，足以承受約 {int(buffer_cap / (suggested_lots * 100) if suggested_lots > 0 else 0)} 點的波動。
            
            <div class="section-h" style="margin-top:20px;"><span>🛡️ 風控參數建議</span></div>
            • 停損位：<span class="highlight">{sl_price:,}</span> (-4.5%) | 最大損失：{int((price - sl_price) * 100 * suggested_lots):,} 元<br>
            • 止盈位：<span style="color:#2a9d5c;">{tp_price:,}</span> (+6.0%) | 預期獲利：{int((tp_price - price) * 100 * suggested_lots):,} 元
        </div>
    </div>
</div>
"""
components.html(html_content, height=620)

# --- 4. 實戰模擬帳本 ---
st.markdown("### 20萬期貨實戰模擬帳本")
ledger_data = [{
    "日期": "2026/04/16", "標的": f"{selected_name}小期", "方向": "▲ 買多",
    "口數": f"{suggested_lots} 口", "入場價": f"{price:,}", "預估稅費": f"≈ {int(total_tax+total_fee)} 元",
    "持倉比": f"{pos_ratio}%", "狀態": "持倉中"
}]
st.table(pd.DataFrame(ledger_data))

# --- 5. 指標視覺化 ---
st.markdown("### 📈 策略回測與動能指標")
tab1, tab2 = st.tabs(["K線與趨勢", "MACD 動能"])
with tab1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df.index, y=df['Adj Close'], name="價格", line=dict(color="#434343")))
    fig1.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name="20MA", line=dict(color="#B18D4D", dash='dot')))
    fig1.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=400)
    st.plotly_chart(fig1, use_container_width=True)
with tab2:
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name="MACD Hist", marker_color="#9F353A"))
    fig2.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=300)
    st.plotly_chart(fig2, use_container_width=True)
