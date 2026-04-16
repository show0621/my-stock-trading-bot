import streamlit as st
import streamlit.components.v1 as components
from strategy_engine import get_trading_signal
import pandas as pd
import json

# 設定網頁標題與佈局
st.set_page_config(page_title="2026 量化指揮中心", layout="wide", initial_sidebar_state="expanded")

# --- 1. 側邊欄：參數輸入 ---
with st.sidebar:
    st.header("⚙️ 模擬帳戶設定")
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
    target_vol = st.slider("目標風險控管 (Target Vol)", 0.05, 0.25, 0.15)

# --- 2. 核心數據運算 ---
signal = get_trading_signal(ticker, target_vol)
price = round(signal['price'], 1)
pos_ratio = round(signal['suggested_pos'] * 100, 1)
vol = round(signal['volatility'] * 100, 2)
mom = signal['mom_score']

# 計算建議口數 (以 20 萬資金換算)
# 假設小期規格 100 股
contract_value = price * 100 
suggested_lots = int((initial_cap * (pos_ratio/100)) / contract_value) if contract_value > 0 else 0

# 判定動作與顏色
if mom >= 1 and pos_ratio > 10:
    action_text = "🟢 建議建立多單 (Long)"
    action_color = "#2a9d5c"
elif mom == 0 and pos_ratio < 10:
    action_text = "🔴 建議建立空單 (Short/Flat)"
    action_color = "#d94f4f"
else:
    action_text = "🟡 觀望與持倉調整 (Neutral)"
    action_color = "#c9a84c"

# --- 3. 嵌入整合 HTML/CSS ---
# 將 Python 數據注入 HTML
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Noto+Sans+TC:wght@300;400;500&display=swap');
        *{{box-sizing:border-box;margin:0;padding:0}}
        :root{{
            --black:#0a0c0f;--white:#f5f4f0;
            --gold:#c9a84c;--green:#2a9d5c;--red:#d94f4f;
            --surface:#111317;--border:#2a2e3a;
            --font-main:'Noto Sans TC',sans-serif;
            --font-mono:'IBM Plex Mono',monospace;
        }}
        body{{background:var(--black);color:var(--white);font-family:var(--font-main);padding:20px;}}
        .metrics-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-bottom:20px}}
        .metric-card{{background:var(--surface);border:1px solid var(--border);padding:15px;border-radius:4px}}
        .metric-label{{color:#6b7280;font-size:11px;text-transform:uppercase;margin-bottom:5px}}
        .metric-value{{font-family:var(--font-mono);font-size:24px;font-weight:500}}
        .action-box{{background:var(--surface);border-left:4px solid {action_color};padding:20px;margin-bottom:20px;border-radius:4px}}
        .reason-box{{background:#181b20;padding:15px;border-radius:4px;font-size:14px;line-height:1.6;color:#d1d5db}}
        .gold-text {{color:var(--gold)}}
    </style>
</head>
<body>
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">CURRENT PRICE</div>
            <div class="metric-value">{price:,}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">建議操作口數</div>
            <div class="metric-value" style="color:var(--gold)">{suggested_lots} 口</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">YZ 波動率</div>
            <div class="metric-value">{vol}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">建議持倉比</div>
            <div class="metric-value" style="color:{action_color}">{pos_ratio}%</div>
        </div>
    </div>

    <div class="action-box">
        <div style="font-size:12px;color:#6b7280;margin-bottom:5px">SYSTEM ACTION SIGNAL</div>
        <div style="font-size:22px;font-weight:500;color:{action_color}">{action_text}</div>
    </div>

    <div class="reason-box">
        <h4 style="margin-bottom:10px;color:var(--gold)">📑 策略深度說明與風險分析</h4>
        <p>目前 <b>{selected_name}</b> 的動能分數為 <b>{mom}/2</b>。
        {"趨勢呈現多頭排列，系統建議積極參與。" if mom == 2 else "動能出現分歧，建議採中性配置。" if mom == 1 else "趨勢偏弱，建議縮減多單持倉。"}
        </p>
        <p style="margin-top:10px">
        當前的 Yang-Zhang 波動率為 {vol}%。根據您的風險控管設定（Target Vol: {target_vol:.0%}），
        系統已將您的虛擬帳戶曝險自動調整至 {pos_ratio}%。
        </p>
        <p style="margin-top:10px;font-size:12px;color:#6b7280">
        預估單邊摩擦成本（稅+費）：約 {int(price * 100 * 0.00002 + 20)} TWD。
        </p>
    </div>
</body>
</html>
"""

# 渲染精美 HTML 介面
components.html(html_content, height=500, scrolling=False)

# --- 4. 底部圖表 (使用原本的 Plotly 保持互動性) ---
st.markdown("### 📈 買賣點位標示圖")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Adj Close'], name="還原股價", line=dict(color="#c9a84c")))
# 標示買入訊號
buy_signals = df[df['mom_score'] == 2].index
fig.add_trace(go.Scatter(x=buy_signals, y=df.loc[buy_signals, 'Adj Close'], mode='markers', name='買入訊號', marker=dict(color='#2a9d5c', symbol='triangle-up', size=10)))

fig.update_layout(template="plotly_dark", paper_bgcolor="#0a0c0f", plot_bgcolor="#0a0c0f")
st.plotly_chart(fig, use_container_width=True)
