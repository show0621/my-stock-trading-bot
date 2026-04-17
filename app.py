import streamlit as st, pandas as pd, plotly.graph_objects as go
from strategy_engine import get_trading_signal
st.set_page_config(page_title="李孟霖 | AI首席投研終端", layout="wide", initial_sidebar_state="expanded")
css = "<style>:root{color-scheme:light !important;}.stApp,.main{background-color:#F7F3E9 !important;}html,body,[class*='css'],p,span,div,h1,h2,h3,h4,h5,h6,label,li{color:#000000 !important;font-family:'Noto Serif TC',serif;}[data-testid='stSidebar']{background-color:#FFFFFF !important;border-right:1px solid #D6D2C4;}header[data-testid='stHeader']{background-color:transparent !important;}[data-testid='collapsedControl']{background-color:#FFFFFF !important;border-radius:50% !important;}[data-testid='stExpander']{background-color:#FFFFFF !important;border:1px solid #D6D2C4 !important;border-radius:8px !important;}input,select,textarea{background-color:#FFFFFF !important;color:#000000 !important;-webkit-text-fill-color:#000000 !important;}.status-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;background:#FFFFFF;padding:15px;border-radius:10px;border:1px solid #D6D2C4;margin-bottom:20px;}.s-title{font-size:12px;color:#666666;text-align:center;}.s-val{font-size:18px;font-weight:600;color:#000000;text-align:center;}.report-header{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid #E5E1D5;padding-bottom:10px;margin-bottom:15px;}.report-grid{display:grid;grid-template-columns:1fr 1fr;gap:25px;font-size:14.5px;line-height:1.7;}@media (max-width:768px){.status-grid{grid-template-columns:repeat(2,1fr);gap:15px;}.report-header{flex-direction:column;}.report-grid{grid-template-columns:1fr;}}.sidebar-footer{font-size:11px;color:#888888;margin-top:50px;border-top:1px solid #EEE;padding-top:10px;line-height:1.5;}</style>"
st.markdown(css, unsafe_allow_html=True)
with st.sidebar:
    st.title("🎐 AI 投資指揮中心")
    api_k = st.text_input("🔑 Gemini API Key", type="password", help="請至 Google AI Studio 申請")
    cap = st.number_input("本金設定", value=2000000)
    ind_map = {"半導體核心":{"台積電 (2330)":"2330.TW","聯發科 (2454)":"2454.TW","日月光 (3711)":"3711.TW"},"AI與伺服器":{"鴻海 (2317)":"2317.TW","廣達 (2382)":"2382.TW","緯穎 (6669)":"6669.TW"},"傳產與金控":{"富邦金 (2881)":"2881.TW","中信金 (2891)":"2891.TW","信錦 (1582)":"1582.TW"},"🔍 全台股手動輸入":"MANUAL"}
    sel_ind = st.radio("📁 產業類別", list(ind_map.keys()))
    if sel_ind == "🔍 全台股手動輸入":
        raw_code = st.text_input("輸入代號", value="2382")
        t_sym, t_nm = f"{raw_code}.TW", f"自選 ({raw_code})"
    else:
        t_nm = st.selectbox("🎯 選擇標的", list(ind_map[sel_ind].keys()))
        t_sym = ind_map[sel_ind][t_nm]
    st.markdown(f'<div class="sidebar-footer"><b>作者：</b> 李孟霖<br><b>版本：</b> 20260416-V01-AI<br><b>策略參考：</b><br>Time Series Momentum (2012)</div>', unsafe_allow_html=True)
with st.spinner("🚀 AI 正在深度掃描全球新聞與量化數據..."): sig = get_trading_signal(t_sym, t_nm, cap, api_k)
if sig:
    df, l_df, an, sr = sig['history'], pd.DataFrame(sig['ledger']), sig['report'], sig['stats']
    v_r, v_s, v_sl, v_tp = str(int(sr['Res'])), str(int(sr['Sup'])), str(round(sr['SL'],1)), str(round(sr['TP'],1))
    v_c, v_v, v_w = str(round(sr['Confidence'],2)), str(round(sr['YZ_Vol']*100,1))+"%", str(round(sr['Weight']*100,1))+"%"
    st.markdown(f'<div class="status-grid"><div><div class="s-title">壓力 / 支撐位</div><div class="s-val">{v_r} / {v_s}</div></div><div><div class="s-title">停損 / 停利點</div><div class="s-val" style="color:#9F353A;">{v_sl} / {v_tp}</div></div><div><div class="s-title">趨勢信心 / YZ年化</div><div class="s-val">{v_c} / {v_v}</div></div><div><div class="s-title">動態配置權重</div><div class="s-val" style="color:#B18D4D;">{v_w}</div></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background:#FFFFFF;padding:20px;border:2px solid #B18D4D;border-radius:12px;color:#000;margin-bottom:20px;"><div class="report-header"><h3 style="margin:0;color:#9F353A;">⚖️ AI 首席深度投研報告：{t_nm}</h3><div style="font-size:11px;color:#888;text-align:right;">核心：Gemini AI 動態聯網分析</div></div><div class="report-grid"><div><b style="color:#9F353A;">【利多題材與觸及率】</b><br>{an["利多"]}<br><br><b style="color:#3A5F41;">【利空風險與觸及率】</b><br>{an["利空"]}<br><br><b>【核心利基點】</b><br>{an["利基"]}</div><div><b>【最新法說題材】</b><br>{an["題材"]}<br><br><b>【未來展望 (Outlook)】</b><br>{an["展望"]}<br><br><b>【機率分布】</b>多頭 <span style="color:#9F353A;font-weight:bold;">{an["機率"]["多"]}%</span> | 盤整 {an["機率"]["盤"]}% | 空頭 {an["機率"]["空"]}%</div></div></div>', unsafe_allow_html=True)
    un_n = sr.get('Unrealized_PnL', 0)
    un_s = f" <span style='font-size:15px;color:{'#9F353A' if un_n>=0 else '#3A5F41'};'>(包含未平倉損益：{'+' if un_n>=0 else ''}{int(un_n)} TWD)</span>" if sr.get('Is_Holding', False) else ""
    st.markdown(f"### 💰 帳戶資金變動：總淨值 {sig['equity']:,} TWD {un_s}", unsafe_allow_html=True)
    if not l_df.empty:
        c1, c2 = st.columns([1, 1])
        with c1: st.download_button("📥 下載完整紀錄", data=l_df.to_csv(index=False).encode('utf-8-sig'), file_name=f"{t_nm}_Report.csv")
        with c2: p_num = st.number_input(f"📄 選擇頁碼 (共 {max(1,(len(l_df)-1)//10+1)} 頁)", min_value=1, max_value=max(1,(len(l_df)-1)//10+1), value=1)
        for _, r in l_df.iloc[(p_num-1)*10 : p_num*10].iterrows():
            with st.expander(f"📅 {r['日期']} | {r['動作']} | 價格: {r['價格']} | 結算: {r['餘額']:,}"): st.markdown(r['分析'])
    fig = go.Figure().add_trace(go.Scatter(x=df.index, y=df['Close'], name="收盤價", line=dict(color="#000", width=1.5)))
    if not l_df.empty:
        ls = l_df[l_df['動作'].str.contains("買進")]
        if not ls.empty: fig.add_trace(go.Scatter(x=pd.to_datetime(ls['日期']), y=ls['價格'], mode='markers', name='進場', marker=dict(symbol='triangle-up', size=16, color='#9F353A')))
        ss = l_df[l_df['動作'].str.contains("平倉")]
        if not ss.empty: fig.add_trace(go.Scatter(x=pd.to_datetime(ss['日期']), y=ss['價格'], mode='markers', name='出場', marker=dict(symbol='triangle-down', size=16, color='#3A5F41')))
    fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=400, margin=dict(l=0,r=0,t=20,b=10), dragmode='pan')
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
else: st.error("❌ 系統初始化失敗，請檢查 API Key 或網路。")
