import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="SENTINEL-KE | Early Warning System",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ SENTINEL-KE")
st.markdown("*AI-Powered Early Warning System for Western Kenya*")

# Load data
@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv('data/processed/latest_predictions.csv')
        return df
    except:
        return None

df = load_data()

if df is None:
    st.error("No prediction data available. Waiting for first update.")
    st.stop()

# Show current date
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Status cards
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Counties Monitored", len(df))
with col2:
    alert_count = len(df[df['alert'] == True])
    st.metric("Active Alerts", alert_count, 
              delta="⚠️ Alert" if alert_count > 0 else "✅ Clear")
with col3:
    st.metric("Risk Range", f"{df['risk_score'].min():.1%} - {df['risk_score'].max():.1%}")

# Main map/table
st.subheader("📊 Risk Status by County")

# Color coding
def color_alert(val):
    if val:
        return 'background-color: #ff6b6b; color: white'
    return 'background-color: #4CAF50; color: white'

styled_df = df.style.applymap(color_alert, subset=['alert'])
st.dataframe(styled_df, use_container_width=True)

# Bar chart
fig = px.bar(df, x='county', y='risk_score', 
             color='risk_score', color_continuous_scale='RdYlGn_r',
             title='Outbreak Risk Score by County')
fig.add_hline(y=0.65, line_dash="dash", line_color="red", 
              annotation_text="Alert Threshold")
fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)

# Alerts section
if alert_count > 0:
    st.error(f"🚨 ALERTS: {', '.join(df[df['alert']]['county'].tolist())}")
    st.info("""
    **Recommended Actions:**
    1. Notify sub-county health teams
    2. Activate community health workers
    3. Review emergency supplies
    4. Issue public health messaging
    """)
else:
    st.success("✅ No active alerts - all counties within normal range")

# Footer
st.markdown("---")
st.markdown("*SENTINEL-KE v1.0 | Data updates daily at 6 AM EAT*")
