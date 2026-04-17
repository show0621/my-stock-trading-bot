import streamlit as st, pandas as pd, plotly.graph_objects as go
from strategy_engine import get_trading_signal
st.set_page_config(page_title="李孟霖 | AI首席投研終端", layout="wide")
css = "<style>:root{color-scheme:light !important;}.stApp,.main{background-color:#F7F3E9 !important;}html,body,p,span,div,h1,h2,h3,h4,h5,h6,label,li{color:#000000 !important;font-family:'Noto Serif TC',serif;}.status-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;background:#FFFFFF;padding:15px;border-radius:10px;border:1px solid #D6D2C4;margin-bottom:20px;}.s-title{font-size:12px;color:#666666;text-align:center;}.s-val{font-size:16px;font-weight:600;color:#000000;text-align:center;}.report-header{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid #E5E1D5;padding-bottom:10px;margin-bottom:15px;}.report-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;font-size:14.5px;line-height:1.7;}@media (max-width:768px){.status-grid{grid-template-columns:repeat(2,1fr);}}</style>"
st.markdown(css, unsafe_allow_html=True)
with st.sidebar:
    st.title("🎐 AI 投資指揮中心")
    api_k = st.text_input("🔑 Groq API Key", type="password")
    cap = st.number_input("本金設定", value=2000000)
    ind_map = {"半導體核心":{"台積電 (2330)":"2330.TW","聯發科 (2454)":"2454.TW"},"AI與伺服器":{"鴻海 (2317)":"2317.TW","廣達 (2382)":"2382.TW","緯穎 (6669)":"6669.TW"},"🔍 全台股手動輸入":"MANUAL"}
    sel_ind = st.radio("📁 產業類別", list(ind_map.keys()))
    if sel_ind == "🔍 全台股手動輸入":
        raw_code = st.text_input("輸入代號", value="2382")
        t_sym, t_nm = f"{raw_code}.TW", f"自選 ({raw_code})"
    else:
        t_nm = st.selectbox("🎯 選擇標的", list(ind_map[sel_ind].keys()))
        t_sym = ind_map[sel_ind][t_nm]
with st.spinner("🚀 AI 正在深度分析籌碼情境..."): sig = get_trading_signal(t_sym, t_nm, cap, api_k)
if sig:
    df, l_df, an, sr = sig['history'], pd.DataFrame(sig['ledger']), sig['report'], sig['stats']
    v_r, v_s, v_sl, v_tp = str(int(sr['High'])), str(int(sr['Low'])), str(round(sr['Close']*0.97,1)), str(round(sr['Close']*1.06,1))
    v_c, v_v, v_w = str(round(sr['Confidence'],2)), str(round(sr['YZ_Vol']*100,1))+"%", str(round(sr['Weight']*100,1))+"%"
    st.markdown(f'<div class="status-grid"><div><div class="s-title">壓力/支撐</div><div class="s-val">{v_r}/{v_s}</div></div><div><div class="s-title">停損/停利</div><div class="s-val" style="color:#9F353A;">{v_sl}/{v_tp}</div></div><div><div class="s-title">信心/波動</div><div class="s-val">{v_c}/{v_v}</div></div><div><div class="s-title">配置權重</div><div class="s-val" style="color:#B18D4D;">{v_w}</div></div><div><div class="s-title">籌碼主導權</div><div class="s-val" style="color:#3A5F41;">{sig["chip_type"]}</div></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background:#FFFFFF;padding:20px;border:2px solid #B18D4D;border-radius:12px;color:#000;margin-bottom:20px;"><div class="report-header"><h3 style="margin:0;color:#9F353A;">⚖️ AI 首席深度投研報告：{t_nm}</h3><div style="font-size:11px;color:#888;">核心：Llama-3.3 籌碼融合分析</div></div><div class="report-grid"><div><b style="color:#9F353A;">【利多分析】</b><br>{an["利多"]}<br><br><b style="color:#3A5F41;">【利空分析】</b><br>{an["利空"]}<br><br><b>【核心利基】</b><br>{an["利基"]}</div><div><b>【法說/籌碼題材】</b><br>{an["題材"]}<br><br><b>【未來展望】</b><br>{an["展望"]}<br><br><b>【機率分布】</b>多頭 <span style="color:#9F353A;font-weight:bold;">{an["機率"]["多"]}%</span> | 盤整 {an["機率"]["盤"]}% | 空頭 {an["機率"]["空"]}%</div></div></div>', unsafe_allow_html=True)
    st.markdown(f"### 💰 淨值：{sig['equity']:,} TWD", unsafe_allow_html=True)
    if not l_df.empty:
        p_num = st.number_input("📄 頁碼", 1, max(1,(len(l_df)-1)//5+1), 1)
        for _, r in l_df.iloc[(p_num-1)*5 : p_num*5].iterrows():
            with st.expander(f"📅 {r['日期']} | {r['動作']} | 價格: {r['價格']}"): st.markdown(r['分析'])
    fig = go.Figure().add_trace(go.Scatter(x=df.index, y=df['Close'], name="收盤價", line=dict(color="#000", width=1.5)))
    st.plotly_chart(fig, use_container_width=True)
else: st.error("❌ 初始化失敗")
