import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 初始化頁面
st.set_page_config(page_title="2026 首席投研終端", layout="wide", initial_sidebar_state="expanded")

# 2. 終極防護 CSS (免疫手機深色模式干擾，徹底解決白字與選單隱形)
css_style = """
<style>
    /* 強制亮色背景 */
    .stApp, .main { background-color: #F7F3E9 !important; }
    
    /* 強制全域黑字，抵抗深色模式 */
    html, body, [class*="css"], p, span, div, h1, h2, h3, h4, h5, h6, label, li { 
        color: #000000 !important; 
        font-family: 'Noto Serif TC', serif; 
    }
    
    /* 側邊欄與輸入框修復 */
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #D6D2C4; }
    input, select, textarea { color: #000000 !important; background-color: #FFFFFF !important; }
    
    /* 下拉選單 (Popover/Listbox) 修復：解決點開後看不到字的問題 */
    div[data-baseweb="popover"] { z-index: 10000 !important; background-color: #FFFFFF !important; }
    ul[role="listbox"], ul[role="listbox"] li { background-color: #FFFFFF !important; color: #000000 !important; }
    
    /* Expander 日誌修復：解決裡面變成白字的問題 */
    [data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid #D6D2C4 !important; border-radius: 8px !important; }
    [data-testid="stExpanderDetails"] { background-color: #FFFFFF !important; }
    [data-testid="stExpanderDetails"] * { color: #000000 !important; }
    .stExpander svg { fill: #434343 !important; } /* 保留展開箭頭的深灰色 */
</style>
"""
st.markdown(css_style, unsafe_allow_html=True)

# 3. 產業資料庫
industry_map = {
    "半導體核心": {"台積電 (2330)": "2330.TW", "聯發科 (2454)": "2454.TW", "日月光 (3711)": "3711.TW"},
    "AI與伺服器": {"鴻海 (2317)": "2317.TW", "廣達 (2382)": "2382.TW", "緯穎 (6669)": "6669.TW"},
    "傳產與其他": {"富邦金 (2881)": "2881.TW", "中信金 (2891)": "2891.TW", "信錦 (1582)": "1582.TW"},
    "🔍 全台股手動輸入": "MANUAL"
}

# 4. 側邊欄設定
with st.sidebar:
    st.title("🎐 投資指揮中心")
    cap = st.number_input("本金設定", value=200000)
    selected_ind = st.radio("📁 產業類別", list(industry_map.keys()))
    
    if selected_ind == "🔍 全台股手動輸入":
        code = st.text_input("輸入代號 (如: 1582)", value="1582")
        ticker_symbol = f"{code}.TW"
        ticker_name = f"自選標的 ({code})"
    else:
        ticker_name = st.selectbox("🎯 選擇標的", list(industry_map[selected_ind].keys()))
        ticker_symbol = industry_map[selected_ind][ticker_name]

# --- 5. 執行分析引擎 ---
with st.spinner("載入量化數據中..."):
    sig = get_trading_signal(ticker_symbol, ticker_name, cap)

if sig is not None:
    df = sig['history']
    ledger_df = pd.DataFrame(sig['ledger'])
    an = sig['report']
    st_row = sig['stats']

    # --- 操盤狀態牆 ---
    st.markdown(f"""
    <div style="background:#FFFFFF; padding:15px; border-radius:10px; border:1px solid #D6D2C4; display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; margin-bottom:20px;">
        <div style="text-align:center;"><div style="font-size:12px; color:#666;">壓力 / 支撐位</div><div style="font-size:18px; font-weight:600; color:#000;">{st_row['Res']:.0f} / {st_row['Sup']:.0f}</div></div>
        <div style="text-align:center;"><div style="font-size:12px; color:#666;">停損 / 停利點</div><div style="font-size:18px; font-weight:600; color:#9F353A;">{st_row['SL']:.1f} / {st_row['TP']:.1f}</div></div>
        <div style="text-align:center;"><div style="font-size:12px; color:#666;">趨勢信心 / YZ年化</div><div style="font-size:18px; font-weight:600; color:#000;">{st_row['Confidence']:.2f} / {st_row['YZ_Vol']:.1%}</div></div>
        <div style="text-align:center;"><div style="font-size:12px; color:#666;">動態配置權重</div><div style="font-size:18px; font-weight:600; color:#B18D4D;">{st_row['Weight']:.1%}</div></div>
    </div>
    """, unsafe_allow_html=True)

    # --- 深度投研報告 ---
    prob = an['機率']
    html_report = f"""
    <div style="background:#FFFFFF; padding:15px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
        <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:8px;">⚖️ 首席深度投研報告：{ticker_name}</h3>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; font-size:14px; line-height:1.6;">
            <div>
                <b style="color:#9F353A;">【利多題材與觸及率】</b><br>{an['利多']}<br><br>
                <b style="color:#3A5F41;">【利空風險與觸及率】</b><br>{an['利空']}<br><br>
                <b>【核心利基點】</b><br>{an['利基']}
            </div>
            <div>
                <b>【最新法說題材】</b><br>{an['題材']}<br><br>
                <b>【未來展望 (Outlook)】</b><br>{an['展望']}<br><br>
                <b>【機率分布】</b>多頭 <span style="color:#9F353A; font-weight:bold;">{prob['多']}%</span> | 盤整 {prob['盤']}% | 空頭 {prob['空']}%
            </div>
        </div>
    </div>
    """
    components.html(html_report, height=450)

    # --- 帳戶淨值與日誌 ---
    unrealized_str = f" <span style='font-size:15px; color:{'#9F353A' if st_row['Unrealized_PnL'] >= 0 else '#3A5F41'};'>(含未平倉損益：{st_row['Unrealized_PnL']:+.0f} TWD)</span>" if st_row['Is_Holding'] else " <span style='font-size:15px; color:#666;'>(目前空手觀望)</span>"
    st.markdown(f"### 💰 帳戶資金變動：總淨值 {sig['equity']:,} TWD {unrealized_str}", unsafe_allow_html=True)
    
    if not ledger_df.empty:
        for _, row in ledger_df.head(10).iterrows():
            with st.expander(f"📅 {row['日期']} | {row['動作']} | 成交價: {row['價格']} | 結算淨值: {row['餘額']:,}"):
                st.markdown(row['分析'])

    # --- 訊號圖 (手機優化版) ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="收盤價", line=dict(color="#000", width=1.5)))
    
    if not ledger_df.empty:
        longs = ledger_df[ledger_df['動作'].str.contains("買進建倉")]
        if not longs.empty:
            fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='波段進場', marker=dict(symbol='triangle-up', size=16, color='#9F353A')))
            
        shorts = ledger_df[ledger_df['動作'].str.contains("平倉保護")]
        if not shorts.empty:
            fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='平倉出場', marker=dict(symbol='triangle-down', size=16, color='#3A5F41')))
            
    # 圖表手機端優化配置
    fig.update_layout(
        template="plotly_white", 
        paper_bgcolor="#F7F3E9", 
        plot_bgcolor="#F7F3E9", 
        height=400, # 縮減高度適應手機
        margin=dict(l=0, r=0, t=10, b=0), # 移除多餘邊距
        dragmode='pan', # 預設改為平移，避免手機滑動時誤觸放大
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # 關閉干擾的浮動工具列 (displayModeBar: False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

else:
    st.error("❌ 系統初始化失敗，請檢查網路連線或代號輸入。")
