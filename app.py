import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

st.set_page_config(page_title="2026 專業量化指揮中心", layout="wide", initial_sidebar_state="collapsed")

# 強制手機版字體為黑色，並優化 UI 背景
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F7F3E9; }
    * { color: #000000 !important; }
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; }
    .stAlert { background-color: #FFFFFF !important; border: 1px solid #B18D4D !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 指揮中心設定")
    cap = st.number_input("初始資金", value=200000)
    stocks_0050 = {"台積電": "2330.TW", "鴻海": "2317.TW", "聯發科": "2454.TW", "廣達": "2382.TW", "中信金": "2891.TW"}
    ticker = st.selectbox("監控標的", list(stocks_0050.keys()))
    t_vol = st.slider("風險權重", 0.05, 0.25, 0.15)

sig = get_trading_signal(stocks_0050[ticker], t_vol, cap)
df = sig['history']
ledger_df = pd.DataFrame(sig['ledger'])

# --- 專業分析師即時看板 ---
html_header = f"""
<div style="background:#FFFFFF; color:#000000; font-family:serif; padding:20px; border-radius:12px; border:2px solid #B18D4D;">
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:10px; margin-bottom:20px;">
        <div style="border:1px solid #E5E1D5; text-align:center; padding:10px;">
            <div style="color:#666; font-size:10px;">當前市價</div><div style="font-size:22px; font-weight:600;">{df.iloc[-1]['Close']:,}</div>
        </div>
        <div style="border:1px solid #E5E1D5; text-align:center; padding:10px;">
            <div style="color:#666; font-size:10px;">回測總淨值</div><div style="font-size:22px; color:#B18D4D;">{sig['equity']:,}</div>
        </div>
        <div style="border:1px solid #E5E1D5; text-align:center; padding:10px;">
            <div style="color:#666; font-size:10px;">RSI 強弱</div><div style="font-size:22px;">{sig['rsi']:.1f}</div>
        </div>
        <div style="border:1px solid #E5E1D5; text-align:center; padding:10px;">
            <div style="color:#666; font-size:10px;">MACD 動能</div><div style="font-size:22px; color:{'#9F353A' if sig['macd']>0 else '#3A5F41'};">{'偏多' if sig['macd']>0 else '偏空'}</div>
        </div>
    </div>
    <div style="line-height:1.7; font-size:14px; border-top: 1px solid #E5E1D5; padding-top:15px;">
        <b>⚖️ 首席分析師盤勢解讀：</b><br>
        針對 {ticker}，目前系統偵測到其 K 棒呈現 <span style="color:#9F353A;">{'上升型態' if df.iloc[-1]['Is_Rising'] else '收斂盤整'}</span>。
        配合 RSI 位階與 MACD 柱狀體變化，建議執行 <b>雙向 7 天波段策略</b>。
        目前籌碼面顯示為 <span style="color:#B18D4D;">{'量增攻擊' if df.iloc[-1]['Vol_Ratio']>1.2 else '量縮沈澱'}</span>。
    </div>
</div>
"""
components.html(html_header, height=350)

# --- 詳細分析日誌庫 ---
st.markdown("### 📑 資深分析師交易日誌 (詳細原因)")
if not ledger_df.empty:
    for _, row in ledger_df.head(15).iterrows():
        with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']}"):
            st.write(f"**詳細分析報告：**")
            st.info(row['詳細分析'])

# --- 訊號點位視覺化 (含三角形) ---
st.markdown("### 📈 趨勢指標與型態標註")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000000", width=1)))

if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'] == "▲ 做多"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='做多', marker=dict(symbol='triangle-up', size=12, color='#9F353A')))
    shorts = ledger_df[ledger_df['動作'] == "▼ 放空"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='放空', marker=dict(symbol='triangle-down', size=12, color='#3A5F41')))

fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=500)
st.plotly_chart(fig, use_container_width=True)
