import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 初始化網頁介面
st.set_page_config(page_title="2026 量化操盤日誌", layout="wide")

# --- 側邊欄：參數輸入 ---
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

# --- 核心數據運算 ---
signal = get_trading_signal(ticker, target_vol)
df = signal['history']
price = round(float(signal['price']), 1)
pos_ratio = round(float(signal['suggested_pos'] * 100), 1)
vol = round(float(signal['volatility'] * 100), 2)
mom = int(signal['mom_score'])

# 計算建議口數
contract_value = price * 100 
suggested_lots = int((initial_cap * (pos_ratio/100)) / contract_value) if contract_value > 0 else 0

# --- 日式配色定義 ---
# 背景: #F7F3E9 (米白/和紙), 邊框: #D6D2C4 (石紋), 文字: #434343 (墨)
# 多頭: #9F353A (茜色/暗紅), 空頭: #3A5F41 (松葉綠)
if mom >= 1 and pos_ratio > 10:
    action_text, action_color, bg_light = "🟢 建議建立多單 (買進)", "#9F353A", "#FCEEEF"
elif mom == 0 and pos_ratio < 10:
    action_text, action_color, bg_light = "⚪ 建議觀望或清倉", "#434343", "#F2F2F2"
else:
    action_text, action_color, bg_light = "🟡 部位調整 (中性)", "#B18D4D", "#FDF7E6"

# --- 嵌入日式精美 HTML ---
html_content = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600&family=IBM+Plex+Mono&display=swap');
    .jp-container {{
        background: #F7F3E9;
        color: #434343;
        font-family: 'Noto Serif TC', serif;
        padding: 25px;
        border-radius: 12px;
        border: 2px solid #D6D2C4;
    }}
    .grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
        margin-bottom: 25px;
    }}
    .card {{
        background: #FFFFFF;
        padding: 15px;
        border: 1px solid #E5E1D5;
        border-radius: 8px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.02);
    }}
    .label {{
        color: #8C8C8C;
        font-size: 12px;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }}
    .value {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 26px;
        font-weight: 600;
    }}
    .action-banner {{
        background: {bg_light};
        border: 1px solid {action_color};
        padding: 18px;
        border-radius: 8px;
        margin-bottom: 25px;
        text-align: center;
    }}
    .action-title {{
        font-size: 22px;
        font-weight: 600;
        color: {action_color};
    }}
    .report-box {{
        background: #FFFFFF;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #E5E1D5;
        line-height: 1.8;
        font-size: 15px;
    }}
</style>
<div class="jp-container">
    <div class="grid">
        <div class="card">
            <div class="label">當前市價</div>
            <div class="value">{price:,}</div>
        </div>
        <div class="card">
            <div class="label">建議操作口數</div>
            <div class="value" style="color:#B18D4D">{suggested_lots} 口</div>
        </div>
        <div class="card">
            <div class="label">YZ 波動率</div>
            <div class="value">{vol}%</div>
        </div>
        <div class="card">
            <div class="label">建議持倉比</div>
            <div class="value" style="color:{action_color};">{pos_ratio}%</div>
        </div>
    </div>
    <div class="action-banner">
        <div class="action-title">{action_text}</div>
    </div>
    <div class="report-box">
        <b style="color:#B18D4D; font-size:16px;">📖 策略日誌分析</b><br>
        今日標的 <b>{selected_name}</b> 趨勢評分為 {mom}/2。
        基於當前波動率調節，系統建議將曝險控制在帳戶總值的 {pos_ratio}%。
        請注意日式風控準則：在市場動盪時減少交易頻率，保持心境平穩。
    </div>
</div>
"""
components.html(html_content, height=520)

# --- 底部圖表 (改為亮色系日式風格) ---
st.markdown("### 📉 策略歷史點位追蹤")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Adj Close'], name="還原價格", line=dict(color="#434343", width=2)))

# 標示買入點 (茜色三角形)
if 'mom_score' in df.columns:
    buy_signals = df[df['mom_score'] == 2].index
    if not buy_signals.empty:
        fig.add_trace(go.Scatter(x=buy_signals, y=df.loc[buy_signals, 'Adj Close'], mode='markers', name='買入訊號', marker=dict(color='#9F353A', symbol='triangle-up', size=12)))

fig.update_layout(
    template="plotly_white",
    paper_bgcolor="#F7F3E9",
    plot_bgcolor="#F7F3E9",
    font=dict(color="#434343", family="Noto Serif TC"),
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(gridcolor="#E5E1D5"),
    yaxis=dict(gridcolor="#E5E1D5")
)
st.plotly_chart(fig, use_container_width=True)
