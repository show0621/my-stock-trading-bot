import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 頁面配置
st.set_page_config(page_title="2026 量化決策中心", layout="wide", initial_sidebar_state="expanded")

# 2. 精確 CSS：解決選單無法滑動、黑字優化、絕不亂碼
st.markdown("""
<style>
    .stApp { background-color: #F7F3E9; }
    /* 精確黑化文字，避開 Streamlit SVG 系統圖標 */
    div[data-testid="stMarkdownContainer"] p, 
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stExpander"] span,
    h1, h2, h3, .stMetric label { color: #000000 !important; font-family: 'Noto Serif TC', serif; }
    
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #D6D2C4; }
    [data-testid="stSidebar"] * { color: #000000 !important; }
    
    div[data-baseweb="popover"] { z-index: 10000 !important; }
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# 3. 產業資料庫
industry_map = {
    "半導體/IC核心": {"台積電 (2330)": "2330.TW", "聯發科 (2454)": "2454.TW", "日月光 (3711)": "3711.TW", "世芯 (3661)": "3661.TW", "聯電 (2303)": "2303.TW"},
    "AI/伺服器代工": {"鴻海 (2317)": "2317.TW", "廣達 (2382)": "2382.TW", "緯穎 (6669)": "6669.TW", "技嘉 (2376)": "2376.TW", "台達電 (2308)": "2308.TW"},
    "金融/金控": {"富邦金 (2881)": "2881.TW", "國泰金 (2882)": "2882.TW", "中信金 (2891)": "2891.TW", "兆豐金 (2886)": "2886.TW", "玉山金 (2884)": "2884.TW"},
    "🔍 全台股手動輸入": "MANUAL"
}

with st.sidebar:
    st.title("🎐 策略指揮中心")
    cap = st.number_input("初始投資本金", value=200000)
    selected_ind = st.radio("📁 產業類別 (解決選單無法捲動問題)", list(industry_map.keys()))
    
    if selected_ind == "🔍 全台股手動輸入":
        code = st.text_input("輸入台股 4 位代號", value="2330")
        ticker_symbol = f"{code}.TW"
        ticker_name = f"自選標的 ({code})"
    else:
        ticker_name = st.selectbox("🎯 選擇公司名稱 (代號)", list(industry_map[selected_ind].keys()))
        ticker_symbol = industry_map[selected_ind][ticker_name]

# --- 4. 數據獲取與安全性檢查 (修復 TypeError) ---
sig = get_trading_signal(ticker_symbol, ticker_name, cap)

if sig is not None:
    df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])
    an = sig['report']

    # --- 5. 首席深度投研報告 (利基、展望、動態) ---
    html_report = f"""
    <div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
        <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:8px;">⚖️ 首席分析師深度報告：{ticker_name}</h3>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; font-size:14.5px; line-height:1.7;">
            <div>
                <b>【產業核心地位】</b><br>{an['產業核心']}<br><br>
                <b>【三大核心利基】</b><br>{an['核心利基']}
            </div>
            <div>
                <b>【未來展望 (Outlook)】</b><br>{an['未來展望']}<br><br>
                <b>【最新產業動態 / 新聞】</b><br>{an['最新動態']}
            </div>
        </div>
        <div style="margin-top:15px; font-size:13px; border-top:1px dashed #D6D2C4; padding-top:10px; display:flex; justify-content:space-between;">
            <span><b>未來展望分布：</b>看多機率 <span style="color:#9F353A; font-weight:600;">{an['機率預測']}%</span> | {an['統計分布']}</span>
            <span><b>當前動能：</b>{'加速向上' if sig['mom']>0 else '動能收斂'}</span>
        </div>
    </div>
    """
    components.html(html_report, height=450)

    # --- 6. 財務累積帳本與詳細日誌 ---
    st.markdown(f"### 💰 帳戶資金變動：目前累積淨值 {sig['equity']:,} TWD (獲利 {sig['equity']-cap:+,})")
    st.markdown("### 📑 資深操盤詳細日誌 (形態訓練與動能偵測)")
    if not ledger_df.empty:
        for _, row in ledger_df.head(15).iterrows():
            with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']} | 本金變動: {row['餘額']:,}"):
                st.info(row['分析'])

    # --- 7. 圖表無視覺化 ---
    st.markdown("### 📈 雙向訊號點位追蹤 (紅多綠空)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000", width=1)))
    if not ledger_df.empty:
        longs = ledger_df[ledger_df['動作'] == "▲ 做多"]
        fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='做多', marker=dict(symbol='triangle-up', size=14, color='#9F353A')))
        shorts = ledger_df[ledger_df['動作'] == "▼ 放空"]
        fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='放空', marker=dict(symbol='triangle-down', size=14, color='#3A5F41')))
    fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=500)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("❌ 無法獲取該代號之歷史數據。請確認輸入代號是否正確，或檢查網路連線。")
