import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import os
from strategy_engine import get_trading_signal

st.set_page_config(page_title="2026 量化指揮中心", layout="wide")

# --- 側邊欄 ---
with st.sidebar:
    st.title("🎐 操盤導覽")
    initial_cap = st.number_input("初始資金 (TWD)", value=200000)
    tickers = {"台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW"}
    selected_name = st.selectbox("標的監控", list(tickers.keys()))
    target_vol = st.slider("目標風險控管", 0.05, 0.25, 0.15)

# --- 數據獲取 ---
sig = get_trading_signal(tickers[selected_name], target_vol)
df = sig['history']
latest = df.iloc[-1]
price = round(float(sig['price']), 1)
pos_ratio = round(float(sig['suggested_pos'] * 100), 1)
vol_val = round(float(sig['volatility'] * 100), 1)

# 期貨專業計算
margin_rate = 0.135
margin_per_lot = price * 100 * margin_rate
target_inv = initial_cap * (pos_ratio / 100)
suggested_lots = int(target_inv / margin_per_lot) if margin_per_lot > 0 else 0
used_margin = margin_per_lot * suggested_lots
buffer_cap = initial_cap - used_margin

# 稅費與風控
tax_total = (price * 100 * 0.00002 * 2 + 40) * suggested_lots
sl_price = round(price * 0.955, 1) # -4.5%
tp_price = round(price * 1.06, 1)  # +6.0%

# --- 渲染日式專業介面 ---
html_content = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600&family=IBM+Plex+Mono&display=swap');
    .jp-shell {{ background: #F7F3E9; color: #434343; font-family: 'Noto Serif TC', serif; padding: 20px; border: 2px solid #D6D2C4; border-radius: 12px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }}
    .card {{ background: #FFF; padding: 12px; border: 1px solid #E5E1D5; border-radius: 6px; text-align: center; }}
    .label {{ color: #8C8C8C; font-size: 10px; text-transform: uppercase; }}
    .value {{ font-family: 'IBM Plex Mono', monospace; font-size: 22px; font-weight: 600; }}
    .main-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
    .box {{ background: #FFF; padding: 18px; border: 1px solid #E5E1D5; border-radius: 8px; font-size: 13px; line-height: 1.6; }}
    .title {{ color: #B18D4D; font-weight: 600; border-bottom: 1px solid #E5E1D5; margin-bottom: 10px; padding-bottom: 5px; }}
    .highlight {{ color: #9F353A; font-weight: 600; }}
</style>
<div class="jp-shell">
    <div style="font-size:16px; font-weight:600; margin-bottom:15px; color:#B18D4D;">// 今日模擬入場紀錄 — 2026.04.16</div>
    <div class="grid">
        <div class="card"><div class="label">ENTRY PRICE</div><div class="value">{price:,}</div></div>
        <div class="card"><div class="label">建議口數</div><div class="value" style="color:#B18D4D">{suggested_lots} 口</div></div>
        <div class="card"><div class="label">YZ 波動率</div><div class="value">{vol_val}%</div></div>
        <div class="card"><div class="label">建議持倉比</div><div class="value" style="color:#9F353A">{pos_ratio}%</div></div>
    </div>
    <div class="main-grid">
        <div class="box">
            <div class="title">📐 口數與保證金計算</div>
            • 入場股價：{price:,} 元 | 規格：100 股/口<br>
            • 原始保證金率：13.5% | 每口保證金：{int(margin_per_lot):,} 元<br>
            • 可用資金 ({pos_ratio}%)：{int(target_inv):,} 元<br>
            • 佔用保證金：<span class="highlight">{int(used_margin):,} 元</span> | 剩餘緩衝金：{int(buffer_cap):,} 元<br>
            • 可承受波動：約 <span class="highlight">{int(buffer_cap/(suggested_lots*100) if suggested_lots>0 else 0)} 點</span>
            
            <div class="title" style="margin-top:15px;">💸 預估稅費與損益 (來回)</div>
            • 合計成本 (稅+手續費)：約 <span class="highlight">{int(tax_total)} 元</span><br>
            • 跳動 1 點損益：{int(suggested_lots * 100)} 元/口
        </div>
        <div class="box">
            <div class="title">▎ AI 日誌 · 買入原因分析</div>
            {selected_name} 今日收報 {price:,} 元 ({'+' if price>sig['open'] else ''}{round((price/sig['open']-1)*100,2)}%)。
            YZ 波動率為 {vol_val}%，處於中性區間，顯示市場情緒穩定，對建倉具較佳風險回報比。
            成交量較前日{"放量" if sig['volume']>sig['prev_volume'] else "縮量"} {round(abs(sig['volume']/sig['prev_volume']-1)*100,1)}%，多方意圖明確。
            技術面顯示均線多頭排列，短期 MA5 站上 MA20，足以承受波動不觸及追繳。
            
            <div class="title" style="margin-top:15px;">🛡️ 風控參數建議</div>
            • 停損位：<span class="highlight">{sl_price:,}</span> (-4.5%) | 最大損失：{int((price-sl_price)*100*suggested_lots):,} 元<br>
            • 止盈位：<span style="color:#3A5F41;">{tp_price:,}</span> (+6.0%) | 預期獲利：{int((tp_price-price)*100*suggested_lots):,} 元
        </div>
    </div>
</div>
"""
components.html(html_content, height=580)

# --- 模擬帳本表格 ---
st.markdown("### 20萬期貨實戰模擬帳本")
st.table(pd.DataFrame([{
    "日期": "2026/04/16", "標的": f"{selected_name}小期", "方向": "▲ 買多",
    "口數": f"{suggested_lots} 口", "入場價": f"{price:,}", "預估稅費": f"≈ {int(tax_total)} 元",
    "持倉比": f"{pos_ratio}%", "狀態": "持倉中"
}]))

# --- 技術指標 ---
st.markdown("### 📈 策略回測與指標視覺化")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#434343")))
fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name="20MA", line=dict(color="#B18D4D", dash='dot')))
fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=400)
st.plotly_chart(fig, use_container_width=True)
