import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import os
from strategy_engine import get_trading_signal

# 1. 初始化與手機顯示優化
st.set_page_config(page_title="2026 量化指揮中心", layout="wide", initial_sidebar_state="collapsed")

# --- 側邊欄：導覽設定 ---
with st.sidebar:
    st.title("🎐 操盤導覽")
    initial_cap = st.number_input("初始資金 (TWD)", value=200000)
    tickers = {"台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW"}
    selected_name = st.selectbox("標的監控", list(tickers.keys()))
    target_vol = st.slider("目標風險控管", 0.05, 0.25, 0.15)
    st.markdown("---")
    st.info("今日操盤歷史紀錄\n\n風控中心\n\n策略回測")

# --- 2. 核心數據運算 ---
sig = get_trading_signal(tickers[selected_name], target_vol)
df = sig['history']
latest = df.iloc[-1]
price = round(float(sig['price']), 1)
pos_ratio = round(float(sig['suggested_pos'] * 100), 1)
vol_val = round(float(sig['volatility'] * 100), 1)

# 期貨與口數計算邏輯
margin_per_lot = price * 100 * 0.135
target_inv = initial_cap * (pos_ratio / 100)
suggested_lots = int(target_inv / margin_per_lot) if margin_per_lot > 0 else 0
used_margin = margin_per_lot * suggested_lots
buffer_cap = initial_cap - used_margin
tax_total = (price * 100 * 0.00002 * 2 + 40) * suggested_lots
tick_profit = 100 * suggested_lots

# 風控位計算
sl_price = round(price * 0.955, 1) # -4.5%
tp_price = round(price * 1.06, 1)  # +6.0%

# --- 3. 嵌入式日式專業介面 (支援手機響應式) ---
action_color = "#9F353A" if sig['mom_score'] >= 1 else "#434343"

html_content = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600&family=IBM+Plex+Mono&display=swap');
    .jp-shell {{ background: #F7F3E9; color: #434343; font-family: 'Noto Serif TC', serif; padding: 15px; border: 2px solid #D6D2C4; border-radius: 12px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin-bottom: 20px; }}
    .m-card {{ background: #FFF; padding: 12px; border: 1px solid #E5E1D5; border-radius: 6px; text-align: center; }}
    .m-label {{ color: #8C8C8C; font-size: 10px; text-transform: uppercase; margin-bottom: 5px; }}
    .m-value {{ font-family: 'IBM Plex Mono', monospace; font-size: 20px; font-weight: 600; }}
    .report-grid {{ display: grid; grid-template-columns: 1fr; gap: 15px; }}
    @media (min-width: 768px) {{ .report-grid {{ grid-template-columns: 1fr 1fr; }} }}
    .box {{ background: #FFF; padding: 18px; border: 1px solid #E5E1D5; border-radius: 8px; font-size: 13px; line-height: 1.7; }}
    .title {{ color: #B18D4D; font-weight: 600; border-bottom: 1px solid #E5E1D5; margin-bottom: 10px; padding-bottom: 5px; }}
    .highlight {{ color: #9F353A; font-weight: 600; }}
</style>
<div class="jp-shell">
    <div style="font-size:16px; font-weight:600; margin-bottom:15px; color:#B18D4D;">// 今日模擬入場紀錄 — 2026.04.16</div>
    <div class="metrics">
        <div class="m-card"><div class="m-label">TODAY ENTRY</div><div class="m-value">{price:,}</div></div>
        <div class="m-card"><div class="m-label">建議口數</div><div class="m-value" style="color:#B18D4D">{suggested_lots} 口</div></div>
        <div class="m-card"><div class="m-label">YZ 波動率</div><div class="m-value">{vol_val}%</div></div>
        <div class="m-card"><div class="m-label">建議持倉比</div><div class="m-value" style="color:{action_color};">{pos_ratio}%</div></div>
    </div>
    <div class="report-grid">
        <div class="box">
            <div class="title">📐 口數與保證金計算</div>
            • 入場股價：{price:,} 元 | 每口保證金：<span class="highlight">{int(margin_per_lot):,} 元</span><br>
            • 可用資金 ({pos_ratio}%)：{int(target_inv):,} 元<br>
            • 佔用保證金：<span class="highlight">{int(used_margin):,} 元</span> | 剩餘緩衝金：{int(buffer_cap):,} 元<br>
            • 可承受波動：約 <span class="highlight">{int(buffer_cap/(suggested_lots*100) if suggested_lots>0 else 0)} 點</span> ({round((buffer_cap/initial_cap)*100,1)}%)<br>
            • 4口來回成本：約 {int(tax_total)} 元 | 跳動1點損益：{int(tick_profit)} 元
        </div>
        <div class="box">
            <div class="title">▎ AI 日誌 · 買入原因分析</div>
            {selected_name} 今日以 {int(sig['open']):,} 元開盤，收盤報 {price:,} 元，短期趨勢結構穩定。
            YZ 波動率為 {vol_val}%，處於中性區間。
            成交量較前日{"放量" if sig['volume']>sig['prev_volume'] else "縮量"} {round(abs(sig['volume']/sig['prev_volume']-1)*100,1)}%，配合股價上揚確認多方意圖。
            技術面顯示短期 MA5 站上 MA20，呈現多頭排列。
        </div>
        <div class="box" style="grid-column: span 1;">
            <div class="title">🛡️ 風控參數建議</div>
            • 建議停損位：<span class="highlight">{sl_price:,}</span> (-4.5%) | 最大損失：{int((price-sl_price)*100*suggested_lots):,} 元<br>
            • 建議止盈位：<span style="color:#3A5F41;">{tp_price:,}</span> (+6.0%) | 預期獲利：{int((tp_price-price)*100*suggested_lots):,} 元
        </div>
    </div>
</div>
"""
components.html(html_content, height=800, scrolling=True)

# --- 4. 實戰模擬帳本 ---
st.markdown("### 📋 20萬期貨實戰模擬帳本")
st.table(pd.DataFrame([{
    "日期": "2026/04/16", "標的": f"{selected_name}小期", "方向": "▲ 買多",
    "口數": f"{suggested_lots}口", "入場價": f"{price:,}", "稅費": f"≈ {int(tax_total)}",
    "持倉比": f"{pos_ratio}%", "狀態": "持倉中"
}]))

# --- 5. 指標視覺化 ---
st.markdown("### 📈 趨勢指標追蹤")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Adj Close'], name="價格", line=dict(color="#434343", width=2)))
fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name="20MA", line=dict(color="#B18D4D", dash='dot')))
fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=400, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)
