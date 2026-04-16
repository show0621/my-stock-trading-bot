import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 配置
st.set_page_config(page_title="2026 全球量化指揮中心", layout="wide", initial_sidebar_state="collapsed")

# 2. 手機版黑字優化
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F7F3E9; }
    p, span, label, h1, h2, h3, .stExpander p, .stMarkdown { color: #000000 !important; font-family: 'Noto Serif TC', serif; }
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 指揮中心設定")
    cap = st.number_input("初始資金", value=200000)
    # 擴展後的 0050 權值股清單
    stocks = {
        "台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW",
        "廣達 (2382)": "2382.TW", "台達電 (2308)": "2308.TW", "日月光 (3711)": "3711.TW",
        "富邦金 (2881)": "2881.TW", "國泰金 (2882)": "2882.TW", "中信金 (2891)": "2891.TW",
        "世芯-KY (3661)": "3661.TW", "緯穎 (6669)": "6669.TW", "統一 (1216)": "1216.TW"
    }
    ticker_name = st.selectbox("監控標的 (0050 權值股)", list(stocks.keys()))
    t_vol = st.slider("波動率權重", 0.05, 0.25, 0.15)

# --- 3. 執行分析 ---
sig = get_trading_signal(stocks[ticker_name], ticker_name, t_vol, cap)
df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])

# 動態計算機率
prob_bull = 70 if sig['macd'] > 0 and sig['rsi'] < 60 else (30 if sig['macd'] < 0 else 50)

html_report = f"""
<div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
    <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:5px;">⚖️ 首席分析師深度投研報告：{ticker_name}</h3>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; font-size:14px;">
        <div>
            <b>【波段高低點觀察】</b><br>
            • 近期高點：{df['High'].iloc[-20:].max():,}<br>
            • 近期支撐：{df['Low'].iloc[-20:].min():,}<br>
            • YZ 波動率：{sig['yz']*100:.1f}%
        </div>
        <div>
            <b>【未來 1-3 個月機率分布】</b><br>
            • 看多機率：<span style="color:#9F353A; font-weight:600;">{prob_bull}%</span><br>
            • 橫盤中性：{100-prob_bull-15}%<br>
            • 看空機率：15%
        </div>
    </div>
    <div style="margin-top:15px; font-size:13px; border-top:1px dashed #D6D2C4; padding-top:10px; line-height:1.6;">
        <b>💡 當前核心題材：</b>{sig['news']}<br>
        <b>🎯 買賣建議：</b>根據 {ticker_name} 的財務韌性，目前趨勢指標顯示為「{'偏多攻擊' if sig['macd']>0 else '震盪回測'}」。
        建議於 5MA 與 20MA 之間尋找切入點。嚴格執行 7 天波段平倉與 3% 止損。
    </div>
</div>
"""
components.html(html_report, height=380)

# --- 4. 操盤日誌庫 ---
st.markdown("### 📑 資深分析師交易日誌庫")
if not ledger_df.empty:
    for _, row in ledger_df.head(10).iterrows():
        with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']}"):
            st.info(row['分析'])

# --- 5. 圖表 ---
st.markdown("### 📈 雙向訊號點位追蹤 (紅多綠空)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000000", width=1)))
if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'] == "▲ 做多"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='做多', marker=dict(symbol='triangle-up', size=12, color='#9F353A')))
    shorts = ledger_df[ledger_df['動作'] == "▼ 放空"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='放空', marker=dict(symbol='triangle-down', size=12, color='#3A5F41')))
st.plotly_chart(fig, use_container_width=True)
