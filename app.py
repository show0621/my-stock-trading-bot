import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 初始化
st.set_page_config(page_title="2026 量化首席終端", layout="wide", initial_sidebar_state="expanded")

# 2. 修復版 CSS：確保選單不見的問題解決，且圖標不亂碼
st.markdown("""
<style>
    .stApp { background-color: #F7F3E9; }
    /* 精確指向 Markdown 內容，不干擾 Streamlit 系統元件 */
    .stMarkdown div p, .stMarkdown div li, h1, h2, h3, label { color: #000000 !important; font-family: 'Noto Serif TC', serif; }
    
    /* 修復亂碼：鎖定 Expander 箭頭不被塗黑位移 */
    .stExpander svg { fill: #434343 !important; }
    
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #D6D2C4; }
    [data-testid="stSidebar"] * { color: #000000 !important; }
    
    /* 強化側邊欄層級 */
    div[data-baseweb="popover"] { z-index: 10000 !important; }
</style>
""", unsafe_allow_html=True)

# 3. 側邊欄 (修正選單消失邏輯)
with st.sidebar:
    st.title("🎐 投資指揮中心")
    cap = st.number_input("本金設定", value=200000)
    industry_map = {
        "半導體核心": {"台積電 (2330)": "2330.TW", "聯發科 (2454)": "2454.TW", "日月光 (3711)": "3711.TW"},
        "AI與伺服器": {"鴻海 (2317)": "2317.TW", "廣達 (2382)": "2382.TW", "緯穎 (6669)": "6669.TW"},
        "金融金控": {"富邦金 (2881)": "2881.TW", "國泰金 (2882)": "2882.TW", "中信金 (2891)": "2891.TW"},
        "🔍 全台股手動輸入": "MANUAL"
    }
    selected_ind = st.radio("📁 產業類別", list(industry_map.keys()))
    
    if selected_ind == "🔍 全台股手動輸入":
        code = st.text_input("輸入代號 (如: 2303)", value="2303")
        ticker_symbol, ticker_name = f"{code}.TW", f"自選標的 ({code})"
    else:
        ticker_name = st.selectbox("🎯 選擇公司名稱", list(industry_map[selected_ind].keys()))
        ticker_symbol = industry_map[selected_ind][ticker_name] # 修正此處的變數覆蓋問題

# --- 4. 數據獲取 ---
sig = get_trading_signal(ticker_symbol, ticker_name, cap)

if sig:
    df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])
    an, st_row = sig['report'], sig['stats']

    # --- 5. 操盤狀態牆 (修復數字不見與顯示問題) ---
    st.markdown(f"""
    <div style="background:#FFFFFF; padding:15px; border-radius:10px; border:1px solid #D6D2C4; display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; margin-bottom:20px;">
        <div style="text-align:center;"><div style="font-size:12px; color:#666;">壓力 / 支撐</div><div style="font-size:18px; font-weight:600; color:#000;">{st_row['Res']:.0f} / {st_row['Sup']:.0f}</div></div>
        <div style="text-align:center;"><div style="font-size:12px; color:#666;">停損 / 停利</div><div style="font-size:18px; font-weight:600; color:#9F353A;">{st_row['SL']:.1f} / {st_row['TP']:.1f}</div></div>
        <div style="text-align:center;"><div style="font-size:12px; color:#666;">信心 / 波動率</div><div style="font-size:18px; font-weight:600; color:#000;">{st_row['Confidence']:.2f} / {st_row['YZ_Vol']:.1%}</div></div>
        <div style="text-align:center;"><div style="font-size:12px; color:#666;">配置權重</div><div style="font-size:18px; font-weight:600; color:#B18D4D;">{st_row['Weight']:.1%}</div></div>
    </div>
    """, unsafe_allow_html=True)

    # --- 6. 深度報告 ---
    prob = an['機率']
    html_report = f"""
    <div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
        <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:8px;">⚖️ 首席深度投研報告：{ticker_name}</h3>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:25px; font-size:14px; line-height:1.7;">
            <div>
                <b style="color:#9F353A;">【利多題材與觸及率】</b><br>{an['利多']}<br><br>
                <b style="color:#3A5F41;">【利空風險與觸及率】</b><br>{an['利空']}<br><br>
                <b>【核心利基點】</b><br>{an['利基']}
            </div>
            <div>
                <b>【最新法說題材】</b><br>{an['題材']}<br><br>
                <b>【未來展望 (Outlook)】</b><br>{an['展望']}<br><br>
                <b>【機率分布】</b>多 {prob['多']}% | 空 {prob['空']}% | 盤 {prob['盤']}%
            </div>
        </div>
    </div>
    """
    components.html(html_report, height=450)

    # --- 7. 日誌帳本 ---
    st.markdown(f"### 💰 帳戶資金變動：目前累積淨值 {sig['equity']:,} TWD")
    if not ledger_df.empty:
        for _, row in ledger_df.head(10).iterrows():
            with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']} | 餘額: {row['餘額']:,}"):
                st.info(row['分析'])

    # --- 8. 訊號圖 ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000", width=1.5)))
    if not ledger_df.empty:
        longs = ledger_df[ledger_df['動作'].str.contains("進場")]
        fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='進場', marker=dict(symbol='triangle-up', size=14, color='#9F353A')))
    fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=500)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("❌ 系統初始化失敗，請檢查網路連線或代號輸入。")
