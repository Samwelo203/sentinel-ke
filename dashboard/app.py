
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="SENTINEL-KE | Early Warning System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2.8rem; color: #1E88E5; text-align: center; font-weight: bold; padding: 0.5rem; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 10px; margin-bottom: 1rem; }
    .metric-card { background: white; padding: 1.2rem; border-radius: 12px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.08); border-left: 4px solid #1E88E5; }
    .explanation-box { background: #f8f9fa; padding: 1.5rem; border-radius: 12px; border-left: 5px solid #1E88E5; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# Load Data
@st.cache_data(ttl=3600)
def load_data():
    try: return pd.read_csv('data/processed/latest_predictions.csv')
    except: return None

df = load_data()

# Sidebar
with st.sidebar:
    st.title("🛡️ SENTINEL-KE")
    selected_county = st.selectbox("📍 Select County", ['Kisumu', 'Homa Bay', 'Siaya', 'Migori', 'Nyamira', 'Kisii'])
    disease = st.radio("🦠 Disease Target", ['Cholera', 'Malaria', 'Both'])
    threshold = st.slider("⚙️ Threshold", 0.3, 0.8, 0.65)

st.markdown('<div class="main-header">🛡️ SENTINEL-KE Dashboard</div>', unsafe_allow_html=True)

if df is not None:
    county_row = df[df['county'] == selected_county]
    if not county_row.empty:
        risk = county_row['risk_score'].iloc[0]
        st.metric("Current Risk", f"{risk:.1%}")
        
        st.subheader("Regional Comparison")
        fig = px.bar(df, x='county', y='risk_score', color='risk_score', color_continuous_scale='RdYlGn_r')
        fig.add_hline(y=threshold, line_dash='dash', line_color='red')
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Awaiting data synchronization...")
