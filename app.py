import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 頁面配置
st.set_page_config(page_title="2026 量化首席指揮中心", layout="wide", initial_sidebar_state="expanded")

# 2. 修復版 CSS (黑字優化 + 鎖定側邊欄滾動)
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F7F3E9; }
    /* 只黑化內容文字，保留系統圖示 */
    div[data-testid="stMarkdownContainer"] p, 
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stExpander"] span,
    h1, h2, h3 { color: #000000 !important; font-family: 'Noto Serif TC', serif; }

    /* 確保側邊欄文字清晰且可捲動 */
    section[data-testid="stSidebar"] { background-color: #FFFFFF !important; }
    section[data-testid="stSidebar"] * { color: #000000 !important; }
    
    /* 修正下拉選單層次與滾動 */
    div[data-baseweb="popover"] { z-index: 999999 !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 策略指揮中心")
    cap = st.number_input("初始投資本金", value=200000)
    
    # 擴充後的 0050 全清單
    stocks = {
        "台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW",
        "廣達 (2382)": "2382.TW", "台達電 (2308)": "2308.TW", "日月光 (3711)": "3711.TW",
        "富邦金 (2881)": "2881.TW", "國泰金 (2882)": "2882.TW", "中信金 (2891)": "2891.TW",
        "世芯-KY (3661)": "3661.TW", "緯穎 (6669)": "6669.TW", "緯創 (3231)": "3231.TW",
        "長榮 (2603)": "2603.TW", "兆豐金 (2886)": "2886.TW", "中鋼 (2002)": "2002.TW"
    }
    # 下拉選單：現在能正常滑動選擇
    ticker_name = st.selectbox("0050 標的全監控", list(stocks.keys()))

# --- 獲取數據 (增加安全檢查) ---
sig = get_trading_signal(stocks[ticker_name], ticker_name, cap)

if sig is not None:
    df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])
    an = sig['report']  # 現在保證 strategy_engine 有這個 key

    # --- 3. 首席分析師投研報告 ---
    html_report = f"""
    <div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
        <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:8px;">⚖️ 首席分析師深度報告：{ticker_name}</h3>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; font-size:14px; line-height:1.6;">
            <div>
                <b>【產業動態與題材】</b><br>{an['題材']}<br><br>
                <b>【法說會/市場摘要】</b><br>{an['法說']}
            </div>
            <div>
                <b>【未來機率分布預測】</b><br>
                • 看多機率：<span style="color:#9F353A; font-weight:600;">{an['看多']}%</span><br>
                • 看空機率：{100 - an['看多'] - 10}%<br>
                • 趨勢分布：{an['分布']}
            </div>
        </div>
        <div style="margin-top:15px; font-size:13px; border-top:1px dashed #D6D2C4; padding-top:10px;">
            <b>🎯 專業操作策略：</b>針對 {ticker_name}，建議鎖定 7 天波段，並嚴格執行 3% 動態止損。
        </div>
    </div>
    """
    components.html(html_report, height=380)

    # --- 4. 財務與損益累積 ---
    st.markdown(f"### 💰 帳戶資金變動：目前累積淨值 {sig['equity']:,} TWD (總獲利 {sig['equity']-cap:+,})")
    st.table(ledger_df.head(10)) # 用 table 更清晰

    # --- 5. 訊號圖 ---
    st.markdown("### 📈 雙向訊號追蹤")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000", width=1)))
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("❌ 無法獲取該標的數據，請確認股票代碼或網路連線。")
