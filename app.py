import streamlit as st
import plotly.graph_objects as go
from strategy_engine import get_trading_signal
import pandas as pd

st.set_page_config(page_title="2026 量化指揮中心", layout="wide")

# 自定義 CSS 讓網頁更像專業交易終端
st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ TEJ 波動率調節策略：智能投資顧問")

# --- 側邊欄參數 ---
with st.sidebar:
    st.header("⚙️ 模擬帳戶設定")
    initial_cap = st.number_input("初始資金 (TWD)", value=200000)
    # 增加多標的監控
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

# --- 獲取數據 ---
signal = get_trading_signal(ticker, target_vol)
df = signal['history']
price = signal['price']
pos_ratio = signal['suggested_pos']
vol = signal['volatility']
mom = signal['mom_score']

# --- 第一層：核心動作指令 (大字顯示) ---
st.subheader("🚀 今日執行動作建議")

# 計算建議口數 (以 20 萬資金換算)
# 假設小期規格 100 股，但鴻海這類標的一口小期價值約 2-4 萬
contract_value = price * 100 
suggested_lots = int((initial_cap * pos_ratio) / contract_value)

col_action, col_lots = st.columns(2)

# 判斷動作邏輯
if mom >= 1 and pos_ratio > 0.1:
    action_text = "🟢 建議建立多單 (Long)"
    action_color = "green"
elif mom == 0 and pos_ratio < 0.1:
    action_text = "🔴 建議建立空單或清倉 (Short/Flat)"
    action_color = "red"
else:
    action_text = "🟡 觀望與持倉調整 (Neutral)"
    action_color = "orange"

col_action.markdown(f"<h2 style='color:{action_color};'>{action_text}</h2>", unsafe_allow_html=True)
col_lots.metric("建議操作口數 (小期)", f"{suggested_lots} 口", f"曝險比 {pos_ratio:.1%}")

# --- 第二層：詳細策略說明 ---
st.markdown("---")
st.subheader("📑 策略深度說明與風險分析")

with st.expander("查看詳細診斷報告", expanded=True):
    col_text, col_metrics = st.columns([2, 1])
    
    with col_text:
        st.write(f"**【趨勢動能分析】**")
        if mom == 2:
            st.write(f"目前 {selected_name} 的 20D 與 60D 動能均為正向，這代表市場正處於強勁的上升趨勢。根據 TEJ 策略邏輯，此時應積極尋找買點。")
        elif mom == 1:
            st.write(f"目前動能出現分歧（短強長弱或短弱長強），屬於震盪格局。系統建議僅配置中性頭寸。")
        else:
            st.write(f"動能分數為 0，代表標的已跌破關鍵移動平均線，趨勢向下，系統建議避開多單，甚至考慮反手建立空單。")
            
        st.write(f"**【波動率調節邏輯】**")
        st.write(f"目前的 Yang-Zhang 波動率為 {vol:.2%}。當波動率高於目標值時，系統會自動縮減口數以防止資產大幅回測；反之則放大部位。")
        
        # 稅費試算
        tax_fee = (price * 100 * 0.00002) + 20
        st.write(f"**【交易成本預估】**：單邊交易成本約 **{tax_fee:.0f} TWD**。建議在比例變動超過 10% 時再調整部位，以節省交易磨耗。")

    with col_metrics:
        st.metric("當前股價", f"{price:,.1f}")
        st.metric("YZ 波動率", f"{vol:.2%}")
        st.metric("動能分數 (0-2)", f"{mom}")

# --- 第三層：圖表標示 ---
st.markdown("---")
st.subheader("📈 買賣點位視覺化")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Adj Close'], name="還原股價", line=dict(color="#1f77b4")))
# 標示買入點 (簡化邏輯：動能滿分)
buy_signals = df[df['mom_score'] == 2].index
fig.add_trace(go.Scatter(x=buy_signals, y=df.loc[buy_signals, 'Adj Close'], mode='markers', name='策略建議買入點', marker=dict(color='green', symbol='triangle-up', size=10)))

st.plotly_chart(fig, use_container_width=True)
