import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Page config
st.set_page_config(
    page_title="SENTINEL-KE | Early Warning System",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2.8rem; color: #1E88E5; text-align: center; font-weight: bold; }
    .sub-header { text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 1rem; }
    .alert-box { background-color: #ff6b6b; padding: 1.5rem; border-radius: 10px; color: white; font-weight: bold; text-align: center; }
    .safe-box { background-color: #4CAF50; padding: 1.5rem; border-radius: 10px; color: white; text-align: center; }
    .metric-card { background: #f8f9fa; padding: 1.2rem; border-radius: 12px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .metric-value { font-size: 2rem; font-weight: bold; }
    .metric-label { color: #666; font-size: 0.9rem; }
    .footer { text-align: center; padding: 2rem; color: #999; font-size: 0.8rem; border-top: 1px solid #eee; margin-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🛡️ SENTINEL-KE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Early Warning System<br>Western Kenya - Lake Victoria Basin</div>', unsafe_allow_html=True)
st.markdown("---")

# Load data - RELATIVE PATH ONLY (works on Streamlit Cloud)
@st.cache_data(ttl=3600)
def load_predictions():
    """Load predictions from the data folder in the repository"""
    try:
        # Try local file first (works on Streamlit Cloud)
        df = pd.read_csv('data/processed/latest_predictions.csv')
        return df
    except Exception as e1:
        try:
            # Fallback: direct from GitHub
            url = "https://raw.githubusercontent.com/Samwelo203/sentinel-ke/main/data/processed/latest_predictions.csv"
            df = pd.read_csv(url)
            return df
        except Exception as e2:
            st.error(f"Error loading data: {e1}")
            return None

df = load_predictions()

if df is None:
    st.warning("""
    ⏳ **Waiting for predictions data...**

    The system hasn't generated predictions yet.

    **Next scheduled update:** Tomorrow at 6:00 AM EAT
    """)
    st.stop()

# Show timestamp
if 'date' in df.columns:
    st.info(f"🕐 **Last Updated:** {df['date'].iloc[0]}")

st.markdown("---")

# Metrics
alert_count = len(df[df['alert'] == True]) if 'alert' in df.columns else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-card"><div class="metric-value">6</div><div class="metric-label">🏙️ Counties</div></div>', unsafe_allow_html=True)

with col2:
    alert_color = "🔴" if alert_count > 0 else "✅"
    st.markdown(f'<div class="metric-card"><div class="metric-value">{alert_color} {alert_count}</div><div class="metric-label">🚨 Active Alerts</div></div>', unsafe_allow_html=True)

with col3:
    avg_risk = df['risk_score'].mean()
    st.markdown(f'<div class="metric-card"><div class="metric-value">{avg_risk:.1%}</div><div class="metric-label">📊 Average Risk</div></div>', unsafe_allow_html=True)

with col4:
    max_risk = df['risk_score'].max()
    max_county = df[df['risk_score'] == max_risk]['county'].iloc[0]
    st.markdown(f'<div class="metric-card"><div class="metric-value">{max_risk:.1%}</div><div class="metric-label">📈 Highest Risk: {max_county}</div></div>', unsafe_allow_html=True)

st.markdown("---")

# Alert banner
if alert_count > 0:
    st.markdown(f"""
    <div class="alert-box">
        🚨 ACTIVE ALERTS: {', '.join(alert_counties)}<br>
        Immediate action recommended for these counties
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="safe-box">
        ✅ No active alerts - all counties within normal range
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# County table
st.subheader("📋 County Risk Status")

display_df = df.copy()
display_df['Risk Score'] = display_df['risk_score'].apply(lambda x: f"{x:.1%}")
display_df['Status'] = display_df['alert'].apply(lambda x: "🚨 ALERT" if x else "✅ Normal")
display_df['AI'] = display_df.get('ai_prediction', False).apply(lambda x: "🤖 AI" if x else "📊 Simple")
display_df = display_df.rename(columns={'county': 'County'})

st.dataframe(
    display_df[['County', 'Risk Score', 'Status', 'AI']],
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# Bar chart
st.subheader("📊 Risk Visualization")

fig = px.bar(
    df,
    x='county',
    y='risk_score',
    color='risk_score',
    color_continuous_scale=['#4CAF50', '#FFA500', '#FF4444'],
    title='Outbreak Risk Score by County',
    labels={'risk_score': 'Risk Score', 'county': ''},
    text='risk_score',
    height=500
)

fig.add_hline(
    y=0.65,
    line_dash="dash",
    line_color="red",
    annotation_text="Alert Threshold (0.65)",
    annotation_position="top right"
)

fig.update_traces(
    texttemplate='%{text:.1%}',
    textposition='outside'
)

fig.update_layout(
    yaxis_tickformat='.0%',
    showlegend=False,
    plot_bgcolor='white',
    yaxis=dict(gridcolor='#eee')
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Recommendations
if alert_count > 0:
    st.subheader("📋 Recommended Actions")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **🚨 Immediate Actions:**
        - 📞 Notify sub-county health teams
        - 🏥 Activate community health workers
        - 💊 Review emergency supply stocks
        - 📢 Issue public health messaging
        """)

    with col2:
        st.markdown("""
        **📊 Enhanced Surveillance:**
        - 📈 Daily case reporting
        - 🔬 Lab sample collection
        - 🗺️ Contact tracing
        - 📋 Monitor trends for 7 days
        """)

# System info
st.markdown("---")
st.subheader("ℹ️ System Information")

col1, col2, col3 = st.columns(3)

with col1:
    ai_used = df.get('ai_prediction', False).any() if 'ai_prediction' in df.columns else False
    st.metric("🤖 AI Model", "✅ Active" if ai_used else "⚠️ Fallback")

with col2:
    st.metric("🌧️ Data Source", "Open-Meteo API")

with col3:
    st.metric("⏰ Update Schedule", "Daily at 6 AM EAT")

st.markdown(f"""
<div class="footer">
    SENTINEL-KE v1.0 | Data updates daily at 6 AM EAT<br>
    For health officials only. Not for clinical decision-making.
</div>
""", unsafe_allow_html=True)
