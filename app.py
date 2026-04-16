import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

st.set_page_config(page_title="2026 量化指揮中心", layout="wide", initial_sidebar_state="collapsed")

# 修正：CSS 內的大括號必須寫成 {{}} 才能在 f-string 中使用
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { overscroll-behavior-y: none; }
    .stExpander { background-color: #F7F3E9 !important; border: 1px solid #D6D2C4 !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 操盤設定")
    cap = st.number_input("初始資金", value=200000)
    ticker = st.selectbox("監控標的", ["2330.TW", "2317.TW", "2454.TW"])
    t_vol = st.slider("風險目標", 0.05, 0.25, 0.15)

sig = get_trading_signal(ticker, t_vol, cap)
df = sig['history']
ledger_df = pd.DataFrame(sig['ledger'])
price = df.iloc[-1]['Close']

# --- 原本功能：精確看板 ---
margin_lot = price * 100 * 0.135
html_header = f"""
<div style="background:#F7F3E9; color:#434343; font-family:serif; padding:20px; border-radius:12px; border:2px solid #D6D2C4;">
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:10px; margin-bottom:20px;">
        <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:10px;">現價</div><div style="font-size:22px; font-weight:600;">{price:,}</div>
        </div>
        <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:10px;">回測淨值</div><div style="font-size:22px; color:#B18D4D;">{sig['equity']:,}</div>
        </div>
        <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:10px;">RSI 指標</div><div style="font-size:22px;">{sig['rsi']:.1f}</div>
        </div>
        <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:10px;">每口保證金</div><div style="font-size:22px; color:#9F353A;">{int(margin_lot):,}</div>
        </div>
    </div>
    <div style="background:#FFF; padding:15px; border:1px solid #E5E1D5; border-radius:8px; font-size:13px; line-height:1.6;">
        <b style="color:#B18D4D;">⚖️ 策略狀態：7天波段核心</b><br>
        結合 RSI 強弱過濾與 MACD 動能同步。採 <b>-3% 停損 / +6% 停利</b> 雙軌並進，最長持有不超過 7 個交易日。
    </div>
</div>
"""
components.html(html_header, height=320)

# --- 新功能：買賣分析日誌庫 ---
st.markdown("### 📑 歷史買賣 AI 分析日誌")
if not ledger_df.empty:
    for _, row in ledger_df.head(10).iterrows(): # 顯示最近10筆
        with st.expander(f"📅 {row['日期']} - {row['動作']} 價格: {row['價格']}"):
            st.info(row['日誌'])

# --- 原本功能：訊號視覺化 (含三角形) ---
st.markdown("### 📈 買賣訊號點位追蹤")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#434343", width=1)))

# 繪製三角形
if not ledger_df.empty:
    buys = ledger_df[ledger_df['動作'] == "▲ 買進"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(buys['日期']), y=buys['價格'], mode='markers', name='買入訊號', marker=dict(symbol='triangle-up', size=12, color='#9F353A')))
    
    sells = ledger_df[ledger_df['動作']
