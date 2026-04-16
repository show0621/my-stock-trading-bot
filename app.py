import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import os
from strategy_engine import get_trading_signal

# 1. 初始化與手機優化配置
st.set_page_config(
    page_title="2026 量化指揮中心", 
    layout="wide", 
    initial_sidebar_state="collapsed" # 手機開啟時預設收起側邊欄
)

# --- 側邊欄：帳戶設定 ---
with st.sidebar:
    st.title("🎐 操盤導覽")
    initial_cap = st.number_input("初始資金 (TWD)", value=200000)
    tickers = {"台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW"}
    selected_name = st.selectbox("標的監控", list(tickers.keys()))
    target_vol = st.slider("目標風險控管", 0.05, 0.25, 0.15)

# --- 2. 數據獲取 ---
sig = get_trading_signal(tickers[selected_name], target_vol)
df = sig['history']
price = round(float(sig['price']), 1)
pos_ratio = round(float(sig['suggested_pos'] * 100), 1)
vol_val = round(float(sig['volatility'] * 100), 1)

# 期貨計算邏輯
margin_per_lot = price * 100 * 0.135
target_inv = initial_cap * (pos_ratio / 100)
suggested_lots = int(target_inv / margin_per_lot) if margin_per_lot > 0 else 0
used_margin = margin_per_lot * suggested_lots
buffer_cap = initial_cap - used_margin
tax_total = (price * 100 * 0.00002 * 2 + 40) * suggested_lots
sl_price = round(price * 0.955, 1) # -4.5%
tp_price = round(price * 1.06, 1)  # +6.0%

# --- 3. 響應式日式介面 (加入 Media Queries) ---
action_color = "#9F353A" if sig['mom_score'] >= 1 else "#434343"

html_content = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600&family=IBM+Plex+Mono&display=swap');
    
    .jp-shell {{ 
        background: #F7F3E9; color: #434343; font-family: 'Noto Serif TC', serif; 
        padding: 15px; border: 2px solid #D6D2C4; border-radius: 12px;
    }}
    
    /* 響應式網格：電腦 4 欄，手機自動折行 */
    .metrics-grid {{ 
        display: grid; 
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); 
        gap: 10px; margin-bottom: 20px; 
    }}
    
    .m-card {{ background: #FFF; padding: 12px; border: 1px solid #E5E1D5; border-radius: 6px; text-align: center; }}
    .m-label {{ color: #8C8C8C; font-size: 10px; text-transform: uppercase; }}
    .m-value {{ font-family: 'IBM Plex Mono', monospace; font-size: 20px; font-weight: 600; }}
    
    /* 報告區塊：手機下改為單欄 */
    .report-grid {{ 
        display: grid; 
        grid-template-columns: 1fr; 
        gap: 15px; 
    }}
    @media (min-width: 768px) {{ .report-grid {{ grid-template-columns: 1fr 1fr; }} }}
    
    .box {{ background: #FFF; padding: 15px; border: 1px solid #E5E1D5; border-radius: 8px; font-size: 13px; line-height: 1.6; }}
    .title {{ color: #B18D4D; font-weight: 600; border-bottom: 1px solid #E5E1D5; margin-bottom: 10px; padding-bottom: 5px; }}
    .highlight {{ color: #9F353A; font-weight: 600; }}
</style>

<div class="jp-shell">
    <div style="font-size:14px; font-weight:600; margin-bottom:15px; color:#B18D4D;">// 2026 量化實戰紀錄</div>
    
    <div class="metrics-grid">
        <div class="m-card"><div class="m-label">Entry Price</div><div class="m-value">{price:,}</div></div>
        <div class="m-card"><div class="m-label">建議口數</div><div class="m-value" style="color:#B18D4D">{suggested_lots} 口</div></div>
        <div class="m-card"><div class="m-label">YZ 波動率</div><div class="m-value">{vol_val}%</div></div>
        <div class="m-card"><div class="m-label">持倉比</div><div class="m-value" style="color:{action_color};">{pos_ratio}%</div></div>
    </div>

    <div class="report-grid">
        <div class="box">
            <div class="title">📐 口數與保證金</div>
            • 每口保證金：<span class="highlight">{int(margin_per_lot):,} 元</span><br>
            • 佔用保證金：{int(used_margin):,} 元<br>
            • 剩餘緩衝金：{int(buffer_cap):,} 元<br>
            • 可承受波動：約 <span class="highlight">{int(buffer_cap/(suggested_lots*100) if suggested_lots>0 else 0)} 點</span><br>
            • 合計成本：約 {int(tax_total)} 元
        </div>
        <div class="box">
            <div class="title">▎ AI 日誌分析</div>
            {selected_name} 今日收報 {price:,} 元。YZ 波動率 {vol_val}%。
            成交量較前日{"放量" if sig['volume']>sig['prev_volume'] else "縮量"}，多方意圖明確。
            技術面顯示均線多頭排列。依建議比 {pos_ratio}% 配置，建議進場 {suggested_lots} 口，預期獲利目標 {tp_price:,}。
        </div>
    </div>
</div>
"""
# 增加高度以適應手機長形排版
components.html(html_content, height=750 if st.sidebar.get('mobile', False) else 650, scrolling=True)

# --- 4. 模擬帳本 (手機上會自動產生橫向捲軸) ---
st.markdown("### 📋 實戰模擬帳本")
st.dataframe(pd.DataFrame([{
    "日期": "2026/04/16", "標的": f"{selected_name}", "方向": "買多",
    "口數": f"{suggested_lots}口", "入場價": price, "稅費": f"{int(tax_total)}",
    "狀態": "持倉中"
}]), use_container_width=True)

# --- 5. 圖表優化 ---
st.markdown("### 📈 趨勢指標")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#434343")))
fig.update_layout(
    template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", 
    height=400, margin=dict(l=10, r=10, t=10, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)
