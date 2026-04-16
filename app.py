import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go  # 修正 go 未定義問題
from strategy_engine import get_trading_signal

# 初始化網頁
st.set_page_config(page_title="2026 量化指揮中心", layout="wide")

# --- 側邊欄設定 ---
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
    target_vol = st.slider("目標風險控管", 0.05, 0.25, 0.15)

# --- 數據運算 ---
signal = get_trading_signal(ticker, target_vol)
df = signal['history']
price = round(float(signal['price']), 1)
pos_ratio = round(float(signal['suggested_pos'] * 100), 1)
vol = round(float(signal['volatility'] * 100), 2)
mom = int(signal['mom_score'])

# 計算口數
contract_value = price * 100 
suggested_lots = int((initial_cap * (pos_ratio/100)) / contract_value) if contract_value > 0 else 0

# 判定動作
if mom >= 1 and pos_ratio > 10:
    action_text, action_color = "🟢 建議建立多單", "#2a9d5c"
elif mom == 0 and pos_ratio < 10:
    action_text, action_color = "🔴 建議建立空單", "#d94f4f"
else:
    action_text, action_color = "🟡 觀望與調整", "#c9a84c"

# --- 嵌入黑金 HTML ---
html_content = f"""
<div style="background:#0a0c0f; color:#f5f4f0; font-family:sans-serif; padding:20px; border-radius:8px; border:1px solid #2a2e3a;">
    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:15px; margin-bottom:20px;">
        <div style="background:#111317; padding:15px; border:1px solid #2a2e3a;">
            <div style="color:#6b7280; font-size:11px;">CURRENT PRICE</div>
            <div style="font-size:24px; color:#f5f4f0;">{price:,}</div>
        </div>
        <div style="background:#111317; padding:15px; border:1px solid #2a2e3a;">
            <div style="color:#6b7280; font-size:11px;">建議操作口數</div>
            <div style="font-size:24px; color:#c9a84c;">{suggested_lots} 口</div>
        </div>
        <div style="background:#111317; padding:15px; border:1px solid #2a2e3a;">
            <div style="color:#6b7280; font-size:11px;">YZ 波動率</div>
            <div style="font-size:24px;">{vol}%</div>
        </div>
        <div style="background:#111317; padding:15px; border:1px solid #2a2e3a;">
            <div style="color:#6b7280; font-size:11px;">建議持倉比</div>
            <div style="font-size:24px; color:{action_color};">{pos_ratio}%</div>
        </div>
    </div>
    <div style="background:#111317; border-left:4px solid {action_color}; padding:20px; margin-bottom:20px;">
        <div style="color:{action_color}; font-size:22px; font-weight:bold;">{action_text}</div>
    </div>
    <div style="background:#181b20; padding:15px; font-size:14px; color:#d1d5db; line-height:1.6;">
        <h4 style="color:#c9a84c; margin-bottom:10px;">📑 策略分析報告</h4>
        目前的動能評分為 {mom}/2。{selected_name} 目前趨勢{"強勁" if mom==2 else "平穩" if mom==1 else "偏弱"}。
        根據目標風控 {target_vol:.0%}，系統自動調節曝險至 {pos_ratio}%。
    </div>
</div>
"""
components.html(html_content, height=450)

# --- 底部圖表 ---
st.markdown("### 📈 買賣點位標示圖")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Adj Close'], name="還原股價", line=dict(color="#c9a84c")))

# 標示買入點
if 'mom_score' in df.columns:
    buy_signals = df[df['mom_score'] == 2].index
    if not buy_signals.empty:
        fig.add_trace(go.Scatter(x=buy_signals, y=df.loc[buy_signals, 'Adj Close'], mode='markers', name='買入點', marker=dict(color='#2a9d5c', symbol='triangle-up', size=10)))

fig.update_layout(template="plotly_dark", paper_bgcolor="#0a0c0f", plot_bgcolor="#0a0c0f", margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)
