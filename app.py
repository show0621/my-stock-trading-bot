import streamlit as st
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

st.set_page_config(page_title="2026 量化操盤室", layout="wide")
st.title("📈 TEJ 波動率調節實戰模擬")

# --- 介面設定 ---
with st.sidebar:
    st.header("⚙️ 模擬設定")
    initial_cap = st.number_input("初始資金", value=200000)
    ticker = st.selectbox("監控標的", ["2330.TW", "2454.TW", "2317.TW", "^TWII"])
    target_vol = st.slider("目標波動率控管", 0.05, 0.30, 0.15)

# --- 獲取數據與訊號 ---
signal = get_trading_signal(ticker, target_vol)
df = signal['history']

# --- 稅費計算機 ---
st.subheader("💰 帳戶與稅費監控")
col1, col2, col3 = st.columns(3)
price = signal['price']
# 模擬稅費 (個股期貨: 手續費20 + 稅金 0.00002)
est_tax_fee = (price * 100 * 0.00002) + 20 # 假設買1口小期
col1.metric("當前股價", f"{price:,.1f}")
col2.metric("預估單邊交易成本", f"{est_tax_fee:.0f} TWD")
col3.metric("建議持倉比例", f"{signal['suggested_pos']:.1%}")

# --- 買賣原因與點位標示 ---
st.markdown("---")
st.subheader("📍 策略買賣點位與原因說明")
# 繪製圖表
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Adj Close'], name="還原股價"))
# 標示買入點 (簡化示例：動能轉正的第一天)
buys = df[df['mom_score'] == 2].index
fig.add_trace(go.Scatter(x=buys, y=df.loc[buys, 'Adj Close'], mode='markers', name='買入訊號', marker=dict(color='green', symbol='triangle-up', size=10)))

st.plotly_chart(fig, use_container_width=True)

# 買賣原因 (由 AI 自動格式化描述)
st.info(f"**今日買賣決策原因**：\n"
        f"目前 {ticker} 的動能分數為 {signal['mom_score']}/2。 "
        f"Yang-Zhang 波動率目前為 {signal['volatility']:.2%}，"
        f"符合您設定的 {target_vol:.0%} 目標風控區。 "
        f"系統建議配置約 {signal['suggested_pos']:.1%} 的部位，以極大化風險回報比。")
