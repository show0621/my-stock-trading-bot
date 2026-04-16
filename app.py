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
        display: flex; justify-content: space-between; align-items: flex-
