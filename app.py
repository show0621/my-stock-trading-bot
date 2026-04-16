import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 頁面配置：必須展開
st.set_page_config(page_title="2026 量化首席終端", layout="wide", initial_sidebar_state="expanded")

# 2. 精確 CSS：修正亂碼、黑化文字、解決側邊欄無法捲動問題
st.markdown("""
<style>
    /* 核心：只黑化內容文字，保留系統圖示與小箭頭 */
    div[data-testid="stMarkdownContainer"] p, 
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stExpander"] span,
    .stMetric label, .stMetric div[data-testid="stMetricValue"],
    h1, h2, h3 { color: #000000 !important; font-family: 'Noto Serif TC', serif; }

    /* 全局背景 */
    .stApp { background-color: #F7F3E9; }

    /* 側邊欄優化：確保可捲動、不被遮擋、文字清晰 */
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #D6D2C4; }
    [data-testid="stSidebar"] * { color: #000 !important; }
    
    /* 修正下拉選單下拉時的視覺層次 */
    div[data-baseweb="select"] { cursor: pointer; }
    div[data-baseweb="popover"] { z-index: 9999 !important; }
    
    /* Expander 美化 */
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 專業策略設定")
    cap = st.number_input("初始帳戶本金", value=200000)
    
    # 0050 全權值股數據字典 (大幅擴充)
    stocks = {
        "台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW",
        "廣達 (2382)": "2382.TW", "台達電 (2308)": "2308.TW", "日月光 (3711)": "3711.TW",
        "富邦金 (2881)": "2881.TW", "國泰金 (2882)": "2882.TW", "中信金 (2891)": "2891.TW",
        "世芯-KY (3661)": "3661.TW", "緯穎 (6669)": "6669.TW", "緯創 (3231)": "3231.TW",
        "統一 (1216)": "1216.TW", "台塑 (1301)": "1301.TW", "中華電 (2412)": "2412.TW",
        "兆豐金 (2886)": "2886.TW", "玉山金 (2884)": "2884.TW", "元大金 (2885)": "2885.TW",
        "長榮 (2603)": "2603.TW", "技嘉 (2376)": "2376.TW", "中鋼 (2002)": "2002.TW"
    }
    # 修正選單：現在能正常上下捲動
    ticker_name = st.selectbox("監控標的 (0050 全權值)", list(stocks.keys()))

# --- 獲取分析數據 ---
sig = get_trading_signal(stocks[ticker_name], ticker_name, cap)
df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])
an = sig['report']

# --- 3. 首席分析師深度投研報告 ---
html_report = f"""
<div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
    <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:8px;">⚖️ 首席分析師投研專欄：{ticker_name}</h3>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; font-size:14.4px; line-height:1.6;">
        <div>
            <b>【產業類別】</b> {an['產業']}<br>
            <b>【關鍵題材】</b><br>{an['題材']}<br><br>
            <b>【最新法說會/新聞摘要】</b><br>{an['法說']}
        </div>
        <div>
            <b>【財務表現分析】</b><br>{an['財務']}<br><br>
            <b>【未來 3 個月展望分布】</b><br>
            • 看多機率：<span style="color:#9F353A; font-weight:600;">{an['看多']}%</span><br>
            • 看空機率：{an['看空']}%<br>
            • 統計分佈：{an['分布']}
        </div>
    </div>
    <div style="margin-top:15px; font-size:13.5px; border-top:1px dashed #D6D2C4; padding-top:12px;">
        <b>🎯 操盤官建議：</b>針對 {ticker_name}，目前技術面呈現「{'動能擴張' if df['MACD_Hist'].iloc[-1]>0 else '趨勢整理'}」狀態。
        操作宜鎖定 7 天波段，並嚴格執行 3% 動態止損。
    </div>
</div>
"""
components.html(html_report, height=420)

# --- 4. 財務紀錄與累積數 ---
st.markdown(f"### 💰 帳戶資金變動：目前累積淨值 {sig['equity']:,} TWD (獲利 {sig['equity']-cap:+,})")
st.dataframe(ledger_df, use_container_width=True)

# --- 5. 操盤日誌 ---
st.markdown("### 📑 資深分析師詳細操盤日誌 (型態與動能)")
if not ledger_df.empty:
    for _, row in ledger_df.head(15).iterrows():
        with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']}"):
            st.info(row['分析'])

# --- 6. 訊號圖 ---
st.markdown("### 📈 雙向訊號點位追蹤 (紅多綠空)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000", width=1)))
if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'] == "▲ 做多"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='做多', marker=dict(symbol='triangle-up', size=12, color='#9F353A')))
    shorts = ledger_df[ledger_df['動作'] == "▼ 放空"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='放空', marker=dict(symbol='triangle-down', size=12, color='#3A5F41')))
st.plotly_chart(fig, use_container_width=True)
