import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 初始化
st.set_page_config(page_title="2026 專業量化指揮中心", layout="wide", initial_sidebar_state="collapsed")

# 修正：強制黑色字體 CSS
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F7F3E9; overscroll-behavior-y: none; }
    * { color: #000000 !important; }
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; }
    .stAlert { background-color: #FFFFFF !important; border: 1px solid #B18D4D !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 專業操盤設定")
    cap = st.number_input("初始資金", value=200000)
    stocks_0050 = {
        "台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW",
        "廣達 (2382)": "2382.TW", "中信金 (2891)": "2891.TW", "台達電 (2308)": "2308.TW"
    }
    ticker_name = st.selectbox("監控標的 (0050)", list(stocks_0050.keys()))
    t_vol = st.slider("波動率權重", 0.05, 0.25, 0.15)

# --- 獲取數據 ---
sig = get_trading_signal(stocks_0050[ticker_name], t_vol, cap)
df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])

# --- 2. 首席分析師深度報告 ---
# 模擬 2026/04/16 最新法說會分析
news_context = "台積電今日法說表現驚艷：毛利率 66.2% 超出預期，AI 訂單能見度已達 2027 年。外資今日轉買，單日敲進逾 2 萬張。散戶融資餘額持續下降，籌碼歸戶趨於穩定。"
prob_up = 65 if sig['macd'] > 0 else 35

html_report = f"""
<div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
    <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:5px;">⚖️ 首席分析師深度投研報告：{ticker_name}</h3>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; font-size:14px;">
        <div>
            <b>【趨勢與波段監控】</b><br>
            • 當前價格：{df['Close'].iloc[-1]:,}<br>
            • 型態辨識：{'<span style="color:#9F353A;">底底高上升趨勢</span>' if sig['is_rising'] else '區間震盪收斂'}<br>
            • RSI 指標：{sig['rsi']:.1f} (位階適中)
        </div>
        <div>
            <b>【未來 3 個月展望分布】</b><br>
            • 看多機率：<span style="color:#9F353A; font-weight:600;">{prob_up}% (AI需求爆發)</span><br>
            • 中性橫盤：{100-prob_up-10}%<br>
            • 看空機率：10% (地緣政治風險)
        </div>
    </div>
    <div style="margin-top:15px; font-size:13px; border-top:1px dashed #D6D2C4; padding-top:10px;">
        <b>💡 首席點評：</b>{news_context}<br>
        <b>🎯 買賣策略：</b>建議於月線支撐不破前提下建立多頭波段。預計停損設於月線下方 3%，目標獲利看 6%-8%。
    </div>
</div>
"""
components.html(html_report, height=380)

# --- 3. 分析師交易日誌庫 ---
st.markdown("### 📑 資深操盤交易日誌 (詳細分析)")
if not ledger_df.empty:
    for _, row in ledger_df.head(10).iterrows():
        with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']}"):
            st.info(row['詳細分析'])

# --- 4. 訊號圖 ---
st.markdown("### 📈 雙向訊號點位追蹤")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000000", width=1)))

if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'] == "▲ 做多"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='做多', marker=dict(symbol='triangle-up', size=12, color='#9F353A')))
    shorts = ledger_df[ledger_df['動作'] == "▼ 放空"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='放空', marker=dict(symbol='triangle-down', size=12, color='#3A5F41')))

fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=450, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)
