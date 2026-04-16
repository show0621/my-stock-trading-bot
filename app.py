import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 頁面初始化
st.set_page_config(page_title="李孟霖 | 首席投研終端", layout="wide", initial_sidebar_state="expanded")

# 2. 終極防護 CSS
css_style = """
<style>
    :root { color-scheme: light !important; }
    .stApp, .main { background-color: #F7F3E9 !important; }
    html, body, [class*="css"], p, span, div, h1, h2, h3, h4, h5, h6, label, li { 
        color: #000000 !important; font-family: 'Noto Serif TC', serif; 
    }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #D6D2C4; }
    header[data-testid="stHeader"] { background-color: transparent !important; }
    [data-testid="collapsedControl"] { background-color: #FFFFFF !important; border-radius: 50% !important; }
    [data-testid="collapsedControl"] svg { fill: #000000 !important; }
    [data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid #D6D2C4 !important; border-radius: 8px !important; }
    
    input, select, textarea { background-color: #FFFFFF !important; color: #000000 !important; -webkit-text-fill-color: #000000 !important; }
    button[data-testid="stNumberInputStepDown"], button[data-testid="stNumberInputStepUp"] { background-color: #F7F3E9 !important; color: #000000 !important; }
    button[data-testid="stNumberInputStepDown"] svg, button[data-testid="stNumberInputStepUp"] svg { fill: #000000 !important; }
    
    div[data-baseweb="select"] > div { background-color: #FFFFFF !important; border-color: #D6D2C4 !important; }
    div[data-baseweb="select"] span { color: #000000 !important; -webkit-text-fill-color: #000000 !important; }
    div[data-baseweb="select"] svg { fill: #000000 !important; }
    div[data-baseweb="popover"], div[data-baseweb="popover"] > div { background-color: #FFFFFF !important; }
    ul[role="listbox"], li[role="option"] { background-color: #FFFFFF !important; color: #000000 !important; }
    
    .status-grid {
        display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
        background: #FFFFFF; padding: 15px; border-radius: 10px; border: 1px solid #D6D2C4; margin-bottom: 20px;
    }
    .s-title { font-size: 12px; color: #666666; text-align: center; margin-bottom: 4px; }
    .s-val { font-size: 18px; font-weight: 600; color: #000000; text-align: center; }
    
    .report-header {
        display: flex; justify-content: space-between; align-items: flex-start;
        border-bottom: 1px solid #E5E1D5; padding-bottom: 10px; margin-bottom: 15px;
    }
    .report-grid {
        display: grid; grid-template-columns: 1fr 1fr; gap: 25px; font-size: 14.5px; line-height: 1.7;
    }

    @media (max-width: 768px) {
        .status-grid { grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .report-header { flex-direction: column; gap: 8px; }
        .report-header div { text-align: left !important; max-width: 100% !important; }
        .report-grid { grid-template-columns: 1fr; gap: 15px; } 
    }
    .sidebar-footer { font-size: 11px; color: #888888; margin-top: 50px; border-top: 1px solid #EEE; padding-top: 10px; line-height: 1.5; }
</style>
"""
st.markdown(css_style, unsafe_allow_html=True)

# 3. 側邊欄設定
with st.sidebar:
    st.title("🎐 投資指揮中心")
    cap = st.number_input("本金設定", value=2000000)
    
    industry_map = {
        "半導體核心": {"台積電 (2330)": "2330.TW", "聯發科 (2454)": "2454.TW", "日月光 (3711)": "3711.TW"},
        "AI與伺服器": {"鴻海 (2317)": "2317.TW", "廣達 (2382)": "2382.TW", "緯穎 (6669)": "6669.TW"},
        "傳產與金控": {"富邦金 (2881)": "2881.TW", "中信金 (2891)": "2891.TW", "信錦 (1582)": "1582.TW"},
        "🔍 全台股手動輸入": "MANUAL"
    }
    selected_ind = st.radio("📁 產業類別", list(industry_map.keys()))
    
    if selected_ind == "🔍 全台股手動輸入":
        code = st.text_input("輸入代號", value="1582")
        ticker_symbol, ticker_name = f"{code}.TW", f"自選標的 ({code})"
    else:
        ticker_name = st.selectbox("🎯 選擇標的", list(industry_map[selected_ind].keys()))
        ticker_symbol = industry_map[selected_ind][ticker_name]

    st.markdown("""
    <div class="sidebar-footer">
        <b>作者：</b> 李孟霖<br>
        <b>版本：</b> 20260416-V01<br>
        <b>策略參考：</b><br>
        <span style="font-size:10px;">Time Series Momentum<br>(Tobias J. Moskowitz, Yao Hua Ooi, Lasse Heje Pedersen, 2012)</span>
    </div>
    """, unsafe_allow_html=True)

# --- 4. 執行引擎 ---
with st.spinner("載入量化數據中..."):
    sig = get_trading_signal(ticker_symbol, ticker_name, cap)

if sig:
    df = sig['history']
    ledger_df = pd.DataFrame(sig['ledger'])
    an = sig['report']
    st_row = sig['stats']

    val_res = str(int(round(st_row.get('Res', 0), 0)))
    val_sup = str(int(round(st_row.get('Sup', 0), 0)))
    val_sl = str(round(st_row.get('SL', 0), 1))
    val_tp = str(round(st_row.get('TP', 0), 1))
    val_conf = str(round(st_row.get('Confidence', 0), 2))
    val_vol = str(round(st_row.get('YZ_Vol', 0) * 100, 1)) + "%"
    val_weight = str(round(st_row.get('Weight', 0) * 100, 1)) + "%"

    # --- 5. 狀態牆 ---
    st.markdown("""
    <div class="status-grid">
        <div><div class="s-title">壓力 / 支撐位</div><div class="s-val">""" + val_res + """ / """ + val_sup + """</div></div>
        <div><div class="s-title">停損 / 停利點</div><div class="s-val" style="color:#9F353A;">""" + val_sl + """ / """ + val_tp + """</div></div>
        <div><div class="s-title">趨勢信心 / YZ年化</div><div class="s-val">""" + val_conf + """ / """ + val_vol + """</div></div>
        <div><div class="s-title">動態配置權重</div><div class="s-val" style="color:#B18D4D;">""" + val_weight + """</div></div>
    </div>
    """, unsafe_allow_html=True)

    p_up = str(an['機率']['多'])
    p_flat = str(an['機率']['盤'])
    p_down = str(an['機率']['空'])
    an_good = an['利多']
    an_bad = an['利空']
    an_core = an['利基']
    an_news = an['題材']
    an_out = an['展望']

    # --- 6. 深度報告渲染 ---
    st.markdown("""
    <div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000; margin-bottom:20px;">
        <div class="report-header">
            <h3 style="margin:0; color:#9F353A;">⚖️ 首席深度投研報告：""" + ticker_name + """</h3>
            <div style="font-size:11px; color:#888; text-align:right; max-width:250px;">
                策略參考：Time Series Momentum<br>(Tobias J. Moskowitz, Yao Hua Ooi, Lasse Heje Pedersen, 2012)
            </div>
        </div>
        <div class="report-grid">
            <div>
                <b style="color:#9F353A;">【利多題材與觸及率】</b><br>""" + an_good + """<br><br>
                <b style="color:#3A5F41;">【利空風險與觸及率】</b><br>""" + an_bad + """<br><br>
                <b>【核心利基點】</b><br>""" + an_core + """
            </div>
            <div>
                <b>【最新法說題材】</b><br>""" + an_news + """<br><br>
                <b>【未來展望 (Outlook)】</b><br>""" + an_out + """<br><br>
                <b>【機率分布】</b>多頭 <span style="color:#9F353A; font-weight:bold;">""" + p_up + """%</span> | 盤整 """ + p_flat + """% | 空頭 """ + p_down + """%
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 7. 帳戶與分頁日誌 ---
    unreal_num = st_row.get('Unrealized_PnL', 0)
    if st_row.get('Is_Holding', False):
        color = "#9F353A" if unreal_num >= 0 else "#3A5F41"
        sign = "+" if unreal_num >= 0 else ""
        unreal_str = f" <span style='font-size:15px; color:{color};'>(含未平倉損益：{sign}{int(unreal_num)} TWD)</span>"
    else:
        unreal_str = ""
        
    st.markdown(f"### 💰 帳戶資金變動：總淨值 {sig['equity']:,} TWD {unreal_str}", unsafe_allow_html=True)
    
    if not ledger_df.empty:
        col1, col2 = st.columns([1, 1])
        with col1:
            csv_data = ledger_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 下載完整歷史交易紀錄 (CSV)", data=csv_data, file_name=f"{ticker_name}_TSMOM_Report.csv", mime="text/csv")
        with col2:
            items_per_page = 10
            total_pages = max(1, (len(ledger_df) - 1) // items_per_page + 1)
            page_num = st.number_input(f"📄 分頁瀏覽 (共 {total_pages} 頁)", min_value=1, max_value=total_pages, value=1)
            
        start_idx = (page_num - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        for _, row in ledger_df.iloc[start_idx:end_idx].iterrows():
            with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']} | 結算: {row['餘額']:,}"):
                st.markdown(row['分析'])

    # --- 8. 訊號圖 ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="收盤價", line=dict(color="#000", width=1.5)))
    
    if not ledger_df.empty:
        longs = ledger_df[ledger_df['動作'].str.contains("買進")]
        if not longs.empty:
            fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='波段進場', marker=dict(symbol='triangle-up', size=16, color='#9F353A')))
            
        shorts = ledger_df[ledger_df['動作'].str.contains("平倉")]
        if not shorts.empty:
            fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='平倉出場', marker=dict(symbol='triangle-down', size=16, color='#3A5F41')))
            
    fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=400, margin=dict(l=0, r=0, t=20, b=10), dragmode='pan')
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

else:
    st.error("❌ 系統初始化失敗，請檢查網路連線或代號輸入。")
