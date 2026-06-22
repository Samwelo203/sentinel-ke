
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="SENTINEL-KE | Early Warning System",
    page_icon="☁  ",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        color: #1E88E5;
        text-align: center;
        font-weight: bold;
        padding: 0.5rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .alert-box-critical {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        font-weight: bold;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border-left: 4px solid #1E88E5;
    }
    .footer {
        text-align: center;
        padding: 2rem;
        color: #999;
        font-size: 0.8rem;
        border-top: 1px solid #eee;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">☁   SENTINEL-KE</div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("☁   SENTINEL-KE")
    selected_county = st.selectbox("Select County", ['Kisumu', 'Homa Bay', 'Siaya', 'Migori', 'Nyamira', 'Kisii'])
    disease = st.radio("Select Disease", ['Cholera', 'Malaria', 'Both'])
    threshold = st.slider("Alert Threshold", 0.3, 0.8, 0.65)

@st.cache_data(ttl=3600)
def load_data():
    try:
        return pd.read_csv('data/processed/latest_predictions.csv')
    except:
        return None

df = load_data()

if df is not None:
    county_data = df[df['county'] == selected_county]
    if not county_data.empty:
        risk = county_data['risk_score'].iloc[0]
        if risk > threshold:
            st.markdown(f'<div class="alert-box-critical">☁   CRITICAL ALERT: {selected_county} County at High Risk ({risk:.1%})</div>', unsafe_allow_html=True)
        
        st.subheader("Regional Risk Comparison")
        fig = px.bar(df, x='county', y='risk_score', color='risk_score', color_continuous_scale="RdYlGn_r")
        fig.add_hline(y=threshold, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Data for selected county not found.")
else:
    st.info("Initializing dashboard data. Please wait or check data pipeline.")

st.markdown('<div class="footer"> 2026 SENTINEL-KE Project | AI-Powered Early Warning System</div>', unsafe_allow_html=True)
