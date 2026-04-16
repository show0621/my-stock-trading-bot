import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 頁面配置
st.set_page_config(page_title="2026 量化首席終端", layout="wide", initial_sidebar_state="collapsed")

# 2. 精確 CSS 解決黑字、亂碼、側邊欄滑動
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F7F3E9; }
    /* 僅黑化主文，不干擾 Streamlit 系統元件 */
    .stMarkdown, p, span, h1, h2, h3, .stExpander label { color: #000000 !important; font-family: 'Noto Serif TC', serif; }
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; }
    .stSidebar [data-testid="stVerticalBlock"] { padding-top: 2rem; }
    /* 修正下拉選單字體與顏色 */
    div[data-baseweb="select"] * { color: #000 !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 指揮中心設定")
    cap = st.number_input("初始本金 (TWD)", value=200000)
    stocks = {
        "台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW",
        "廣達 (2382)": "2382.TW", "台達電 (2308)": "2308.TW", "國泰金 (2882)": "2882.TW"
    }
    ticker_name = st.selectbox("0050 權值股選單", list(stocks.keys()))

sig = get_trading_signal(stocks[ticker_name], ticker_name, cap)
df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])
an = sig['analyst']

# --- 3. 首席分析師深度投研報告 (2026/04 最新) ---
prob_up = 65 if sig['rsi'] > 50 else 35
html_report = f"""
<div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
    <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5;">⚖️ 首席分析師深度報告：{ticker_name}</h3>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; font-size:14px;">
        <div>
            <b>【核心題材】</b><br>{an['題材']}<br><br>
            <b>【法說會摘要】</b><br>{an['法說']}
        </div>
        <div>
            <b>【未來 3 個月機率分布】</b><br>
            • 看多機率：<span style="color:#9F353A; font-weight:600;">{prob_up}%</span><br>
            • 橫盤中性：{100-prob_up-10}%<br>
            • 看空機率：10%
        </div>
    </div>
    <div style="margin-top:15px; font-size:13px; border-top:1px dashed #D6D2C4; padding-top:10px; line-height:1.6;">
        <b>🎯 專業操作建議：</b>目前 {ticker_name} 的{an['動向']}<br>
        建議於 20MA 支撐附近建立頭寸，嚴格執行 7 天波段平倉與 3% 動態止損。
    </div>
</div>
"""
components.html(html_report, height=380)

# --- 4. 財務變動與累積數 ---
st.markdown(f"### 💰 帳戶資金變動：目前累積淨值 {sig['equity']:,} TWD (獲利 {sig['equity']-cap:+,})")
st.dataframe(ledger_df, use_container_width=True)

# --- 5. 操盤日誌庫 ---
st.markdown("### 📑 資深操盤詳細日誌 (K棒型態與動能)")
if not ledger_df.empty:
    for _, row in ledger_df.head(10).iterrows():
        with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']}"):
            st.info(row['分析'])

# --- 6. 訊號圖 ---
st.markdown("### 📈 雙向訊號點位追蹤")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000", width=1)))
if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'] == "▲ 做多"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='做多', marker=dict(symbol='triangle-up', size=12, color='#9F353A')))
    shorts = ledger_df[ledger_df['動作'] == "▼ 放空"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='放空', marker=dict(symbol='triangle-down', size=12, color='#3A5F41')))
st.plotly_chart(fig, use_container_width=True)
