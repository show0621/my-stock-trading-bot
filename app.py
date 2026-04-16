import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 頁面配置
st.set_page_config(page_title="2026 量化首席指揮中心", layout="wide", initial_sidebar_state="expanded")

# 2. 精確 CSS：解決選單無法捲動、黑字優化、不干擾系統圖標
st.markdown("""
<style>
    .stApp { background-color: #F7F3E9; }
    /* 精確黑化內容文字 */
    div[data-testid="stMarkdownContainer"] p, 
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stExpander"] span,
    h1, h2, h3, label { color: #000000 !important; font-family: 'Noto Serif TC', serif; }
    
    /* 側邊欄與選單捲動修正 */
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #D6D2C4; }
    [data-testid="stSidebar"] * { color: #000000 !important; }
    div[data-baseweb="select"] * { color: #000 !important; }
    div[data-baseweb="popover"] { z-index: 10000 !important; }
    
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# 3. 產業群組資料庫
industry_groups = {
    "半導體核心": {
        "台積電 (2330)": "2330.TW", "聯發科 (2454)": "2454.TW", "日月光 (3711)": "3711.TW",
        "聯電 (2303)": "2303.TW", "世芯-KY (3661)": "3661.TW", "創意 (3443)": "3443.TW"
    },
    "AI與電子代工": {
        "鴻海 (2317)": "2317.TW", "廣達 (2382)": "2382.TW", "緯穎 (6669)": "6669.TW",
        "台達電 (2308)": "2308.TW", "技嘉 (2376)": "2376.TW", "緯創 (3231)": "3231.TW"
    },
    "金融金控": {
        "富邦金 (2881)": "2881.TW", "國泰金 (2882)": "2882.TW", "中信金 (2891)": "2891.TW",
        "兆豐金 (2886)": "2886.TW", "第一金 (2892)": "2892.TW", "玉山金 (2884)": "2884.TW"
    },
    "傳產航運": {
        "長榮 (2603)": "2603.TW", "中鋼 (2002)": "2002.TW", "統一 (1216)": "1216.TW",
        "台塑 (1301)": "1301.TW", "中華電 (2412)": "2412.TW"
    },
    "🔍 手動輸入 (全台股代碼)": "MANUAL"
}

with st.sidebar:
    st.title("🎐 專業操盤設定")
    cap = st.number_input("初始帳戶本金", value=200000)
    
    # 產業選單 (解決長選單捲動問題)
    selected_ind = st.radio("📁 請點選產業別", list(industry_groups.keys()))
    
    if selected_ind == "🔍 手動輸入 (全台股代碼)":
        code = st.text_input("輸入台股代號 (如: 2303)", value="2303")
        ticker_symbol = f"{code}.TW"
        ticker_name = f"自選標的 ({code})"
    else:
        ticker_name = st.selectbox("🎯 選擇產業標的", list(industry_groups[selected_ind].keys()))
        ticker_symbol = industry_groups[selected_ind][ticker_name]

# --- 4. 數據獲取與首席報告 ---
sig = get_trading_signal(ticker_symbol, ticker_name, cap)
df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])
an = sig['report']

# 首席投研報告 HTML
html_report = f"""
<div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
    <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5;">⚖️ 首席投研報告：{ticker_name}</h3>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; font-size:14px; line-height:1.7;">
        <div>
            <b>【產業題材】</b><br>{an['題材']}<br><br>
            <b>【法說會/財務展望】</b><br>{an['法說']}
        </div>
        <div>
            <b>【未來 3 個月機率分布】</b><br>
            • 看多機率：<span style="color:#9F353A; font-weight:600;">{an['看多機率']}%</span><br>
            • 統計分布：{an['分布']}<br><br>
            <b>【關鍵財務能力】</b><br>{an['財務']}
        </div>
    </div>
    <div style="margin-top:15px; font-size:13px; border-top:1px dashed #D6D2C4; padding-top:10px;">
        <b>🎯 專業操作建議：</b>目前波動率 YZ 為 {sig['yz']*100:.1f}%。
        建議於 20MA 附近佈局，執行 7 天波段平倉與 3% 動態止損策略。
    </div>
</div>
"""
components.html(html_report, height=420)

# --- 5. 帳戶損益與詳細日誌 (確保詳細分析不丟失) ---
st.markdown(f"### 💰 帳戶資金變動：目前累積淨值 {sig['equity']:,} TWD (獲利 {sig['equity']-cap:+,})")
st.markdown("### 📑 資深操盤詳細日誌 (含本金變動)")
if not ledger_df.empty:
    for _, row in ledger_df.head(15).iterrows():
        with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']} | 餘額: {row['餘額']:,}"):
            st.info(row['分析'])

# --- 6. 訊號圖 (紅買綠賣三角形) ---
st.markdown("### 📈 雙向訊號點位視覺化")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000", width=1)))

if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'] == "▲ 做多"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='做多', marker=dict(symbol='triangle-up', size=14, color='#9F353A')))
    shorts = ledger_df[ledger_df['動作'] == "▼ 放空"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='放空', marker=dict(symbol='triangle-down', size=14, color='#3A5F41')))

fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=500)
st.plotly_chart(fig, use_container_width=True)
