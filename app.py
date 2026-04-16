import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 初始化頁面
st.set_page_config(page_title="2026 首席投研終端", layout="wide", initial_sidebar_state="expanded")

# 2. 終極防護 CSS (維持 V19 完美抗深色模式與排版，不變動)
css_style = """
<style>
    :root { color-scheme: light !important; }
    .stApp, .main { background-color: #F7F3E9 !important; }
    html, body, [class*="css"], p, span, div, h1, h2, h3, h4, h5, h6, label, li { 
        color: #000000 !important; font-family: 'Noto Serif TC', serif; 
    }
    
    header[data-testid="stHeader"] { background-color: transparent !important; }
    [data-testid="collapsedControl"] { 
        background-color: #FFFFFF !important; border-radius: 50% !important; box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    }
    [data-testid="collapsedControl"] svg { fill: #000000 !important; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #D6D2C4; }

    input, select, textarea { 
        background-color: #FFFFFF !important; color: #000000 !important; -webkit-text-fill-color: #000000 !important; 
    }
    button[data-testid="stNumberInputStepDown"], button[data-testid="stNumberInputStepUp"] {
        background-color: #F7F3E9 !important; color: #000000 !important;
    }
    button[data-testid="stNumberInputStepDown"] svg, button[data-testid="stNumberInputStepUp"] svg {
        fill: #000000 !important;
    }
    
    div[data-baseweb="select"] > div { background-color: #FFFFFF !important; border-color: #D6D2C4 !important; }
    div[data-baseweb="select"] span { color: #000000 !important; -webkit-text-fill-color: #000000 !important; }
    div[data-baseweb="select"] svg { fill: #000000 !important; }
    
    div[data-baseweb="popover"], div[data-baseweb="popover"] > div { background-color: #FFFFFF !important; }
    ul[role="listbox"] { background-color: #FFFFFF !important; }
    li[role="option"] { background-color: #FFFFFF !important; color: #000000 !important; }
    li[role="option"]:hover { background-color: #F7F3E9 !important; }
    
    [data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid #D6D2C4 !important; border-radius: 8px !important; }
    [data-testid="stExpanderDetails"] { background-color: #FFFFFF !important; }
    .stExpander svg { fill: #434343 !important; }

    .status-grid {
        display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
        background: #FFFFFF; padding: 15px; border-radius: 10px; border: 1px solid #D6D2C4; margin-bottom: 20px;
    }
    .s-title { font-size: 12px; color: #666666; text-align: center; margin-bottom: 4px; }
    .s-val { font-size: 18px; font-weight: 600; color: #000000; text-align: center; }
    .s-val.red { color: #9F353A; }
    .s-val.gold { color: #B18D4D; }
    
    @media (max-width: 768px) {
        .status-grid { grid-template-columns: repeat(2, 1fr); gap: 15px; padding: 12px; }
        .s-val { font-size: 16px; }
    }
</style>
"""
st.markdown(css_style, unsafe_allow_html=True)

# 3. 產業資料庫
industry_map = {
    "半導體核心": {"台積電 (2330)": "2330.TW", "聯發科 (2454)": "2454.TW", "日月光 (3711)": "3711.TW", "世芯 (3661)": "3661.TW"},
    "AI與伺服器": {"鴻海 (2317)": "2317.TW", "廣達 (2382)": "2382.TW", "緯穎 (6669)": "6669.TW", "緯創 (3231)": "3231.TW"},
    "傳產與金控": {"富邦金 (2881)": "2881.TW", "中信金 (2891)": "2891.TW", "信錦 (1582)": "1582.TW", "長榮 (2603)": "2603.TW"},
    "🔍 全台股手動輸入": "MANUAL"
}

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

# --- 4. 執行分析引擎 ---
with st.spinner("載入量化數據中..."):
    sig = get_trading_signal(ticker_symbol, ticker_name, cap)

if sig is not None:
    df = sig['history']
    ledger_df = pd.DataFrame(sig['ledger'])
    an = sig['report']
    st_row = sig['stats']

    # --- 5. 專業操盤狀態牆 ---
    st.markdown(f"""
    <div class="status-grid">
        <div><div class="s-title">壓力 / 支撐位</div><div class="s-val">{st_row['Res']:.0f} / {st_row['Sup']:.0f}</div></div>
        <div><div class="s-title">停損 / 停利點</div><div class="s-val red">{st_row['SL']:.1f} / {st_row['TP']:.1f}</div></div>
        <div><div class="s-title">趨勢信心 / YZ年化</div><div class="s-val">{st_row['Confidence']:.2f} / {st_row['YZ_Vol']:.1%}</div></div>
        <div><div class="s-title">動態配置權重</div><div class="s-val gold">{st_row['Weight']:.1%}</div></div>
    </div>
    """, unsafe_allow_html=True)

    # --- 6. 雙向新聞與深度報告 ---
    prob = an['機率']
    html_report = f"""
    <div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
        <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:8px;">⚖️ 首席深度投研報告：{ticker_name}</h3>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:25px; font-size:14.5px; line-height:1.7;">
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

    # --- 7. 帳戶淨值與未平倉損益顯示 ---
    unrealized_str = f" <span style='font-size:16px; color:{'#9F353A' if st_row['Unrealized_PnL'] >= 0 else '#3A5F41'};'>(包含未平倉損益：{st_row['Unrealized_PnL']:+.0f} TWD)</span>" if st_row['Is_Holding'] else " <span style='font-size:16px; color:#666;'>(目前空手觀望)</span>"
    st.markdown(f"### 💰 帳戶資金變動：總淨值 {sig['equity']:,} TWD {unrealized_str}", unsafe_allow_html=True)
    
    # --- 【新增區塊】CSV下載與分頁邏輯 ---
    if not ledger_df.empty:
        col1, col2 = st.columns([1, 1])
        with col1:
            # 產生 CSV 並轉碼為 utf-8-sig 以支援 Excel 繁體中文
            csv_data = ledger_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 下載完整歷史交易紀錄 (CSV)", 
                data=csv_data, 
                file_name=f"{ticker_name}_歷史交易帳本.csv", 
                mime="text/csv"
            )
        with col2:
            # 分頁控制器 (每頁 10 筆)
            items_per_page = 10
            total_pages = max(1, (len(ledger_df) - 1) // items_per_page + 1)
            page_num = st.number_input(f"📄 選擇頁碼 (共 {total_pages} 頁)", min_value=1, max_value=total_pages, value=1)
            
        start_idx = (page_num - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        # 依照分頁渲染日誌
        for _, row in ledger_df.iloc[start_idx:end_idx].iterrows():
            with st.expander(f"📅 {row['日期']} | {row['動作']} | 成交價: {row['價格']} | 結算淨值: {row['餘額']:,}"):
                st.markdown(row['分析'])

    # --- 8. 訊號圖 (維持原樣) ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="收盤價", line=dict(color="#000", width=1.5)))
    
    if not ledger_df.empty:
        longs = ledger_df[ledger_df['動作'].str.contains("買進建倉")]
        if not longs.empty:
            fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='波段進場', marker=dict(symbol='triangle-up', size=16, color='#9F353A')))
            
        shorts = ledger_df[ledger_df['動作'].str.contains("平倉保護")]
        if not shorts.empty:
            fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='平倉出場', marker=dict(symbol='triangle-down', size=16, color='#3A5F41')))
            
    fig.update_layout(
        template="plotly_white", 
        paper_bgcolor="#F7F3E9", 
        plot_bgcolor="#F7F3E9", 
        height=400, 
        margin=dict(l=0, r=0, t=20, b=10), 
        dragmode='pan',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

else:
    st.error("❌ 系統初始化失敗，請檢查網路連線或代號輸入。")
