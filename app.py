import streamlit as st, pandas as pd, plotly.graph_objects as go
from strategy_engine import get_trading_signal
st.set_page_config(page_title="李孟霖 | 離線極速投研終端", layout="wide")
css="<style>:root{color-scheme:light !important;}.stApp,.main{background-color:#F7F3E9 !important;}html,body,p,span,div,h1,h2,h3,h4,h5,h6,label,li{color:#000000 !important;font-family:'Noto Serif TC',serif;}.status-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;background:#FFFFFF;padding:15px;border-radius:10px;border:1px solid #D6D2C4;margin-bottom:20px;}.s-title{font-size:12px;color:#666666;text-align:center;}.s-val{font-size:16px;font-weight:600;color:#000000;text-align:center;}.report-header{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid #E5E1D5;padding-bottom:10px;margin-bottom:15px;}.report-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;font-size:14.5px;line-height:1.7;}@media (max-width:768px){.status-grid{grid-template-columns:repeat(2,1fr);}.report-grid{grid-template-columns:1fr;}}</style>"
st.markdown(css, unsafe_allow_html=True)
with st.sidebar:
    st.title("🎐 極速投資指揮中心")
    cap = st.number_input("本金設定", value=2000000)
    im = {"半導體核心":{"台積電 (2330)":"2330.TW","聯發科 (2454)":"2454.TW"},"AI與伺服器":{"鴻海 (2317)":"2317.TW","廣達 (2382)":"2382.TW","緯穎 (6669)":"6669.TW"},"🔍 全台股手動輸入":"MANUAL"}
    si = st.radio("📁 產業類別", list(im.keys()))
    if si == "🔍 全台股手動輸入":
        rc = st.text_input("輸入代號", value="2382")
        sym, nm = f"{rc}.TW", f"自選 ({rc})"
    else:
        nm = st.selectbox("🎯 選擇標的", list(im[si].keys()))
        sym = im[si][nm]
with st.spinner("⚡ 載入本地資料庫..."): sig = get_trading_signal(sym, cap)
if sig:
    df, l_df, an, sr = sig['history'], pd.DataFrame(sig['ledger']), sig['report'], sig['stats']
    vr, vs, vsl, vtp = str(int(sr['High'])), str(int(sr['Low'])), str(round(sr['Close']*0.97,1)), str(round(sr['Close']*1.06,1))
    vc, vv, vw = str(round(sr['Confidence'],2)), str(round(sr['YZ_Vol']*100,1))+"%", str(round(sr['Weight']*100,1))+"%"
    st.markdown(f'<div class="status-grid"><div><div class="s-title">壓力/支撐</div><div class="s-val">{vr}/{vs}</div></div><div><div class="s-title">停損/停利</div><div class="s-val" style="color:#9F353A;">{vsl}/{vtp}</div></div><div><div class="s-title">信心/波動</div><div class="s-val">{vc}/{vv}</div></div><div><div class="s-title">配置權重</div><div class="s-val" style="color:#B18D4D;">{vw}</div></div><div><div class="s-title">籌碼主導權</div><div class="s-val" style="color:#3A5F41;">{sig["chip_type"]}</div></div></div>', unsafe_allow_html=True)
    pu, pf, pdn = an.get("機率",{}).get("多",33) if isinstance(an.get("機率"),dict) else 33, an.get("機率",{}).get("盤",34) if isinstance(an.get("機率"),dict) else 34, an.get("機率",{}).get("空",33) if isinstance(an.get("機率"),dict) else 33
    st.markdown(f'<div style="background:#FFFFFF;padding:20px;border:2px solid #B18D4D;border-radius:12px;color:#000;margin-bottom:20px;"><div class="report-header"><h3 style="margin:0;color:#9F353A;">⚖️ AI 深度投研報告：{nm}</h3><div style="font-size:11px;color:#888;">更新時間: {sig["update_time"]}</div></div><div class="report-grid"><div><b style="color:#9F353A;">【利多分析】</b><br>{an.get("利多","-")}<br><br><b style="color:#3A5F41;">【利空分析】</b><br>{an.get("利空","-")}<br><br><b>【核心利基】</b><br>{an.get("利基","-")}</div><div><b>【法說/籌碼】</b><br>{an.get("題材","-")}<br><br><b>【未來展望】</b><br>{an.get("展望","-")}<br><br><b>【機率分布】</b>多頭 <span style="color:#9F353A;font-weight:bold;">{pu}%</span> | 盤整 {pf}% | 空頭 {pdn}%</div></div></div>', unsafe_allow_html=True)
    st.markdown(f"### 💰 帳戶淨值：{sig['equity']:,} TWD", unsafe_allow_html=True)
    if not l_df.empty:
        c1, c2 = st.columns([1,1])
        with c1: st.download_button("📥 下載CSV", data=l_df.to_csv(index=False).encode('utf-8-sig'), file_name=f"{nm}_Log.csv", mime="text/csv")
        with c2: pn = st.number_input("📄 頁碼", 1, max(1,(len(l_df)-1)//10+1), 1)
        for _, r in l_df.iloc[(pn-1)*10 : pn*10].iterrows():
            with st.expander(f"📅 {r['日期']} | {r['動作']} | 價格: {r['價格']} | 結算: {r['餘額']:,}"): st.markdown(r['分析'])
    fig = go.Figure().add_trace(go.Scatter(x=df.index, y=df['Close'], name="收盤價", line=dict(color="#000", width=1.5)))
    ls, ss = l_df[l_df['動作'].str.contains("買進")], l_df[l_df['動作'].str.contains("平倉")]
    if not ls.empty: fig.add_trace(go.Scatter(x=pd.to_datetime(ls['日期']), y=ls['價格'], mode='markers', name='進場', marker=dict(symbol='triangle-up', size=16, color='#9F353A')))
    if not ss.empty: fig.add_trace(go.Scatter(x=pd.to_datetime(ss['日期']), y=ss['價格'], mode='markers', name='出場', marker=dict(symbol='triangle-down', size=16, color='#3A5F41')))
    fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=400, margin=dict(l=0,r=0,t=20,b=10))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})
else: st.error("❌ 系統初始化失敗。")
