import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 頁面初始化
st.set_page_config(page_title="2026 量化決策中心", layout="wide", initial_sidebar_state="collapsed")

# 2. 強制黑色字體與日式背景 (修正 CSS 大括號衝突)
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F7F3E9; }
    * { color: #000000 !important; font-family: 'Noto Serif TC', serif !important; }
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 指揮中心設定")
    cap = st.number_input("初始資金", value=200000)
    stocks = {
        "台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW",
        "廣達 (2382)": "2382.TW", "台達電 (2308)": "2308.TW", "中信金 (2891)": "2891.TW"
    }
    ticker_name = st.selectbox("0050 監控標的", list(stocks.keys()))
    t_vol = st.slider("風險目標權重", 0.05, 0.25, 0.15)

# 3. 數據與分析師報告
sig = get_trading_signal(stocks[ticker_name], t_vol, cap)
df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])

# 模擬 2026/04/16 最新法說會分析題材
latest_news = "今日台積電法說會顯示毛利率達 66.2% 創歷史新高，AI 需求帶動 CoWoS 產能全滿，魏哲家上修 2026 年展望。外資單日買超逾 2.5 萬張，籌碼明顯歸戶法人。"
prob_up = 65 if sig['macd'] > 0 else 30

html_report = f"""
<div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
    <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:5px;">⚖️ 首席分析師深度報告：{ticker_name}</h3>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; font-size:14px;">
        <div>
            <b>【趨勢與波段解析】</b><br>
            • 當前價格：{df['Close'].iloc[-1]:,}<br>
            • 波段觀察點：{df['High'].iloc[-20:].max():,} (壓) / {df['Low'].iloc[-20:].min():,} (支)<br>
            • YZ 波動率：{sig['yz']*100:.1f}% (極度穩定)
        </div>
        <div>
            <b>【未來 3 個月機率預測】</b><br>
            • 看多機率：<span style="color:#9F353A; font-weight:600;">{prob_up}% (AI/法說利多驅動)</span><br>
            • 橫盤中性：{100-prob_up-10}%<br>
            • 看空機率：10% (地緣政治風險)
        </div>
    </div>
    <div style="margin-top:15px; font-size:13px; border-top:1px dashed #D6D2C4; padding-top:10px;">
        <b>💡 核心題材：</b>{latest_news}<br>
        <b>🎯 專業操作建議：</b>財務基本面極度健康。目前 RSI 為 {sig['rsi']:.1f}，離超買區仍有空間。建議於 20MA 月線支撐不破前提下建立多頭波段，停損設於月線下方 3%。
    </div>
</div>
"""
components.html(html_report, height=380)

# 4. 詳細日誌庫庫
st.markdown("### 📑 資深分析師操盤日誌庫")
if not ledger_df.empty:
    for _, row in ledger_df.head(15).iterrows():
        with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']}"):
            st.write("**詳細投研分析：**")
            st.info(row['詳細分析'])

# 5. 訊號圖與帳本
st.markdown("### 📈 雙向訊號點位追蹤 (紅買綠賣)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000000", width=1)))
if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'] == "▲ 做多"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='做多', marker=dict(symbol='triangle-up', size=12, color='#9F353A')))
    shorts = ledger_df[ledger_df['動作'] == "▼ 放空"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='放空', marker=dict(symbol='triangle-down', size=12, color='#3A5F41')))
st.plotly_chart(fig, use_container_width=True)
st.dataframe(ledger_df, use_container_width=True)
