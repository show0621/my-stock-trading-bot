import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import os
from strategy_engine import get_trading_signal

# 1. 頁面配置 (必須放在第一行)
st.set_page_config(page_title="2026 量化指揮中心", layout="wide", initial_sidebar_state="collapsed")

# 鎖定 Streamlit 頂層容器防止回彈
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        overscroll-behavior-y: none;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 側邊欄 ---
with st.sidebar:
    st.title("🎐 操盤導覽")
    initial_cap = st.number_input("初始資金 (TWD)", value=200000)
    tickers = {"台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW"}
    selected_name = st.selectbox("標的監控", list(tickers.keys()))
    target_vol = st.slider("目標風險控管", 0.05, 0.25, 0.15)

# --- 2. 數據獲取與保護邏輯 ---
sig = get_trading_signal(tickers[selected_name], target_vol)

if sig is None:
    st.error("❌ 數據載入失敗，請確認網路連線或稍後再試。")
else:
    df = sig['history']
    price = round(float(sig['price']), 1)
    pos_ratio = round(float(sig['suggested_pos'] * 100), 1)
    vol_val = round(float(sig['volatility'] * 100), 1)
    
    # 計算公式
    margin_per_lot = price * 100 * 0.135
    suggested_lots = int((initial_cap * (pos_ratio/100)) / margin_per_lot) if margin_per_lot > 0 else 0
    used_margin = margin_per_lot * suggested_lots
    buffer_cap = initial_cap - used_margin
    tax_total = (price * 100 * 0.00002 * 2 + 40) * suggested_lots
    tick_profit = 100 * suggested_lots
    sl_price, tp_price = round(price * 0.955, 1), round(price * 1.06, 1)

    # --- 3. 嵌入式日式介面 ---
    action_color = "#9F353A" if sig['mom_score'] >= 1 else "#434343"
    html_content = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600&family=IBM+Plex+Mono&display=swap');
        html, body {{ overscroll-behavior-y: none; background: #F7F3E9; color: #434343; font-family: 'Noto Serif TC', serif; }}
        .jp-shell {{ padding: 15px; border: 2px solid #D6D2C4; border-radius: 12px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin-bottom: 20px; }}
        .card {{ background: #FFF; padding: 12px; border: 1px solid #E5E1D5; border-radius: 6px; text-align: center; }}
        .m-value {{ font-family: 'IBM Plex Mono', monospace; font-size: 20px; font-weight: 600; }}
        .report-grid {{ display: grid; grid-template-columns: 1fr; gap: 15px; }}
        @media (min-width: 768px) {{ .report-grid {{ grid-template-columns: 1fr 1fr; }} }}
        .box {{ background: #FFF; padding: 18px; border: 1px solid #E5E1D5; border-radius: 8px; font-size: 13px; line-height: 1.7; }}
        .title {{ color: #B18D4D; font-weight: 600; border-bottom: 1px solid #E5E1D5; margin-bottom: 10px; padding-bottom: 5px; }}
        .highlight {{ color: #9F353A; font-weight: 600; }}
    </style>
    <div class="jp-shell">
        <div class="grid">
            <div class="card"><div>ENTRY PRICE</div><div class="m-value">{price:,}</div></div>
            <div class="card"><div>建議口數</div><div class="m-value" style="color:#B18D4D">{suggested_lots} 口</div></div>
            <div class="card"><div>YZ 波動率</div><div class="m-value">{vol_val}%</div></div>
            <div class="card"><div>建議持倉比</div><div class="m-value" style="color:{action_color};">{pos_ratio}%</div></div>
        </div>
        <div class="report-grid">
            <div class="box">
                <div class="title">📐 口數與保證金計算</div>
                • 每口保證金：<span class="highlight">{int(margin_per_lot):,} 元</span><br>
                • 佔用保證金：{int(used_margin):,} 元 | 剩餘緩衝金：{int(buffer_cap):,} 元<br>
                • 可承受波動：約 <span class="highlight">{int(buffer_cap/(suggested_lots*100) if suggested_lots > 0 else 0)} 點</span><br>
                • 合計成本：約 {int(tax_total)} 元 | 每跳 1 點：{int(tick_profit)} 元
            </div>
            <div class="box">
                <div class="title">▎ AI 日誌 · 買入原因分析</div>
                {selected_name} 今日收盤報 {price:,} 元。YZ 波動率 {vol_val}%。<br>
                成交量對比前日{"放量" if sig['volume']>sig['prev_volume'] else "縮量"}，多方意圖明確。<br>
                技術面顯示均線多頭排列。依建議比 {pos_ratio}% 配置，足以承受約 {round((buffer_cap/initial_cap)*100,1)}% 波動而不觸及追繳。
            </div>
            <div class="box">
                <div class="title">🛡️ 風控參數建議</div>
                • 建議停損位：<span class="highlight">{sl_price:,}</span> (-4.5%)<br>
                • 建議止盈位：<span style="color:#3A5F41;">{tp_price:,}</span> (+6.0%)<br>
                • 最大預期損失：{int((price-sl_price)*100*suggested_lots):,} 元
            </div>
        </div>
    </div>
    """
    components.html(html_content, height=800, scrolling=True)

    # --- 帳本表格 ---
    st.markdown("### 📋 實戰模擬帳本")
    st.dataframe(pd.DataFrame([{
        "日期": "2026/04/16", "標的": selected_name, "口數": f"{suggested_lots}口",
        "入場價": price, "稅費": int(tax_total), "狀態": "持倉中"
    }]), use_container_width=True)

    # --- 圖表 ---
    st.markdown("### 📈 指標視覺化")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Adj Close'], name="價格", line=dict(color="#434343")))
    fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=400, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
