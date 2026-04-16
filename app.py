import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 初始化
st.set_page_config(page_title="2026 量化首席指揮中心", layout="wide", initial_sidebar_state="expanded")

# 2. 精確 CSS：修正字體顏色、亂碼、解決選單無法滑動問題
# 將 CSS 字串化，避免 f-string 導致的 SyntaxError
custom_css = """
<style>
    .stApp { background-color: #F7F3E9; }
    div[data-testid="stMarkdownContainer"] p, 
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stExpander"] span,
    h1, h2, h3, .stMetric div, .stExpander p { 
        color: #000000 !important; 
        font-family: 'Noto Serif TC', serif; 
    }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #D6D2C4; }
    [data-testid="stSidebar"] * { color: #000000 !important; }
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; border-radius: 8px !important; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 3. 產業資料庫與名稱對照
industry_map = {
    "半導體/IC核心": {"台積電 (2330)": "2330.TW", "聯發科 (2454)": "2454.TW", "日月光投控 (3711)": "3711.TW", "世芯-KY (3661)": "3661.TW", "聯電 (2303)": "2303.TW"},
    "AI/伺服器代工": {"鴻海 (2317)": "2317.TW", "廣達 (2382)": "2382.TW", "緯穎 (6669)": "6669.TW", "緯創 (3231)": "3231.TW", "技嘉 (2376)": "2376.TW"},
    "金融/金控": {"富邦金 (2881)": "2881.TW", "國泰金 (2882)": "2882.TW", "中信金 (2891)": "2891.TW", "兆豐金 (2886)": "2886.TW", "玉山金 (2884)": "2884.TW"},
    "🔍 手動輸入代碼": "MANUAL"
}

with st.sidebar:
    st.title("🎐 策略指揮中心")
    cap = st.number_input("本金設定", value=200000)
    selected_ind = st.radio("📁 產業類別 (解決選單滑動問題)", list(industry_map.keys()))
    
    if selected_ind == "🔍 手動輸入代碼":
        code = st.text_input("輸入 4 位台股代號", value="2330")
        ticker_symbol = f"{code}.TW"
        ticker_name = f"標的 ({code})"
    else:
        ticker_name = st.selectbox("🎯 選擇公司名稱 (代號)", list(industry_map[selected_ind].keys()))
        ticker_symbol = industry_groups = industry_map[selected_ind][ticker_name]

# --- 4. 數據獲取 ---
sig = get_trading_signal(ticker_symbol, ticker_name, cap)
df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])
an = sig['report']

# --- 5. 首席分析師深度投研報告 ---
# 使用 Python 字串拼接代替 f-string 內的大括號，防止 HTML 解析出錯
html_report = f"""
<div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
    <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:10px;">⚖️ 首席分析師深度報告：{ticker_name}</h3>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:25px; font-size:14.5px; line-height:1.7;">
        <div>
            <b>【核心利基點 (Niches)】</b><br>{an['核心利基']}<br><br>
            <b>【未來展望 (Outlook)】</b><br>{an['未來展望']}
        </div>
        <div>
            <b>【最新利多題材 / 動態】</b><br>{an['利多題材']}<br><br>
            <b>【法人動向分析】</b><br>{an['法人動向']}
        </div>
    </div>
    <div style="margin-top:15px; font-size:13.5px; border-top:1px dashed #D6D2C4; padding-top:10px;">
        <span><b>展望分布：</b>看多機率 <span style="color:#9F353A; font-weight:600;">{an['看多機率']}%</span> | {an['分布特徵']}</span>
        <span style="float:right;"><b>當前動能：</b>{'加速向上' if sig['mom']>0 else '動能放緩'}</span>
    </div>
</div>
"""
components.html(html_report, height=480)

# --- 6. 損益帳本與詳細日誌 ---
st.markdown(f"### 💰 帳戶資金變動：目前累積淨值 {sig['equity']:,} TWD (獲利 {sig['equity']-cap:+,})")
st.markdown("### 📑 資深操盤詳細日誌 (形態偵測與動能訓練)")
if not ledger_df.empty:
    for _, row in ledger_df.head(15).iterrows():
        with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']} | 本金變動: {row['餘額']:,}"):
            st.info(row['分析'])

# --- 7. 圖表視覺化 (三角形訊號) ---
st.markdown("### 📈 雙向訊號點位追蹤 (紅買綠賣)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000", width=1)))

if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'] == "▲ 做多"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='做多', marker=dict(symbol='triangle-up', size=14, color='#9F353A')))
    shorts = ledger_df[ledger_df['動作'] == "▼ 放空"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='放空', marker=dict(symbol='triangle-down', size=14, color='#3A5F41')))

fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=500)
st.plotly_chart(fig, use_container_width=True)
