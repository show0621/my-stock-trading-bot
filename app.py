import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

st.set_page_config(page_title="2026 雙向指揮中心", layout="wide", initial_sidebar_state="collapsed")

# 修正 CSS 語法
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { overscroll-behavior-y: none; }
    .stExpander { background-color: #F7F3E9 !important; border: 1px solid #D6D2C4 !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 雙向操盤設定")
    cap = st.number_input("初始資金", value=200000)
    # 擴展 0050 主要權值股
    stocks_0050 = {
        "台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW",
        "廣達 (2382)": "2382.TW", "台達電 (2308)": "2308.TW", "富邦金 (2881)": "2881.TW",
        "國泰金 (2882)": "2882.TW", "中信金 (2891)": "2891.TW", "日月光 (3711)": "3711.TW"
    }
    selected_stock = st.selectbox("0050 權值股監控", list(stocks_0050.keys()))
    t_vol = st.slider("風險目標", 0.05, 0.25, 0.15)

sig = get_trading_signal(stocks_0050[selected_stock], t_vol, cap)
df = sig['history']
ledger_df = pd.DataFrame(sig['ledger'])

# --- 專業看板 ---
html_header = f"""
<div style="background:#F7F3E9; color:#434343; font-family:serif; padding:20px; border-radius:12px; border:2px solid #D6D2C4;">
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:10px; margin-bottom:20px;">
        <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:10px;">當前市價</div><div style="font-size:22px; font-weight:600;">{df.iloc[-1]['Close']:,}</div>
        </div>
        <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:10px;">回測總淨值</div><div style="font-size:22px; color:#B18D4D;">{sig['equity']:,}</div>
        </div>
        <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:10px;">RSI 強弱</div><div style="font-size:22px;">{sig['rsi']:.1f}</div>
        </div>
        <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:10px;">目前訊號</div><div style="font-size:22px; color:{'#9F353A' if sig['macd']>0 else '#3A5F41'};">{'多頭動能' if sig['macd']>0 else '空頭動能'}</div>
        </div>
    </div>
    <div style="background:#FFF; padding:15px; border:1px solid #E5E1D5; border-radius:8px; font-size:13px;">
        <b style="color:#B18D4D;">⚖️ 雙向 7 天波段系統</b>：支援做多與放空。
        停損 -3% / 停利 +6% / 破 5MA 或滿 7 天強制平倉。
    </div>
</div>
"""
components.html(html_header, height=320)

# --- AI 日誌庫 ---
st.markdown("### 📑 雙向交易 AI 分析日誌")
if not ledger_df.empty:
    for _, row in ledger_df.head(10).iterrows():
        with st.expander(f"📅 {row['日期']} - {row['動作']} ({row['價格']})"):
            st.info(row['日誌'])

# --- 訊號視覺化 ---
st.markdown("### 📈 多空訊號追蹤圖")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#434343", width=1)))

if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'] == "▲ 做多"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='做多訊號', marker=dict(symbol='triangle-up', size=12, color='#9F353A')))
    shorts = ledger_df[ledger_df['動作'] == "▼ 放空"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='放空訊號', marker=dict(symbol='triangle-down', size=12, color='#3A5F41')))

fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=450)
st.plotly_chart(fig, use_container_width=True)

st.markdown("### 📋 完整交易帳目")
st.dataframe(ledger_df, use_container_width=True)
