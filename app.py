import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 配置
st.set_page_config(page_title="2026 量化決策室", layout="wide", initial_sidebar_state="expanded")

# 2. 精確 CSS：解決亂碼與黑字問題
st.markdown("""
<style>
    .stApp { background-color: #F7F3E9; }
    /* 只黑化內容文字，保留系統 Icon */
    .stMarkdown div p, .stMarkdown div li, h1, h2, h3, .stMetric div, .stExpander p { 
        color: #000000 !important; 
        font-family: 'Noto Serif TC', serif; 
    }
    
    /* 側邊欄黑字且確保可滑動 */
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #D6D2C4; }
    [data-testid="stSidebar"] * { color: #000000 !important; }
    
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# 3. 產業資料庫
industry_groups = {
    "半導體核心": {"台積電 (2330)": "2330.TW", "聯發科 (2454)": "2454.TW", "日月光投控 (3711)": "3711.TW", "聯電 (2303)": "2303.TW"},
    "AI與伺服器": {"鴻海 (2317)": "2317.TW", "廣達 (2382)": "2382.TW", "緯穎 (6669)": "6669.TW", "技嘉 (2376)": "2376.TW"},
    "金融金控": {"富邦金 (2881)": "2881.TW", "國泰金 (2882)": "2882.TW", "中信金 (2891)": "2891.TW", "兆豐金 (2886)": "2886.TW"},
    "🔍 全台股手動輸入": "MANUAL"
}

with st.sidebar:
    st.title("🎐 投資指揮中心")
    cap = st.number_input("本金設定", value=200000)
    selected_ind = st.radio("📁 產業類別選擇", list(industry_groups.keys()))
    
    if selected_ind == "🔍 全台股手動輸入":
        code = st.text_input("輸入台股代碼 (如: 2330)", value="2330")
        ticker_symbol = f"{code}.TW"
        ticker_name = f"自選標的 ({code})"
    else:
        ticker_name = st.selectbox("🎯 選擇標的公司", list(industry_groups[selected_ind].keys()))
        ticker_symbol = industry_groups[selected_ind][ticker_name]

# --- 4. 數據獲取與分析 ---
sig = get_trading_signal(ticker_symbol, ticker_name, cap)
df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])
an = sig['report']

# --- 5. 首席深度投研報告 (詳細展望與利基) ---
html_report = f"""
<div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
    <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:10px;">⚖️ 首席分析師深度報告：{ticker_name}</h3>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:25px; font-size:14.5px; line-height:1.7;">
        <div>
            <b>【核心利基點 (Niches)】</b><br>{an['核心利基']}<br><br>
            <b>【未來展望 (Outlook)】</b><br>{an['未來展望']}
        </div>
        <div>
            <b>【最新產業動態/新聞】</b><br>{an['產業動態']}<br><br>
            <b>【機率分布與動能】</b><br>
            • 未來看多機率：<span style="color:#9F353A; font-weight:600;">{an['機率預測']['看多']}%</span><br>
            • 動能狀態：<span style="color:{'#9F353A' if sig['mom']>0 else '#3A5F41'};">{'加速增強' if sig['mom']>0 else '高檔衰退'}</span><br>
            • 統計分佈：{an['機率預測']['分布']}
        </div>
    </div>
</div>
"""
components.html(html_report, height=450)

# --- 6. 損益帳本與變動 ---
st.markdown(f"### 💰 帳戶資金變動：目前累積淨值 {sig['equity']:,} TWD (獲利 {sig['equity']-cap:+,})")
st.markdown("### 📑 資深操盤詳細日誌 (K棒形態與動能偵測)")
if not ledger_df.empty:
    for _, row in ledger_df.head(15).iterrows():
        with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']} | 本金累積: {row['餘額']:,}"):
            st.info(row['分析'])

# --- 7. 圖表視覺化 (三角形訊號) ---
st.markdown("### 📈 雙向訊號追蹤與形態標註 (紅多綠空)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000", width=1)))

if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'] == "▲ 做多"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='做多', marker=dict(symbol='triangle-up', size=14, color='#9F353A')))
    shorts = ledger_df[ledger_df['動作'] == "▼ 放空"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='放空', marker=dict(symbol='triangle-down', size=14, color='#3A5F41')))

fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=500)
st.plotly_chart(fig, use_container_width=True)
