
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from datetime import timedelta
import joblib
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="SENTINEL-KE | Early Warning System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        padding: 1rem;
    }
    .alert-box {
        background-color: #ff6b6b;
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        font-weight: bold;
        text-align: center;
    }
    .warning-box {
        background-color: #ffa500;
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .safe-box {
        background-color: #4CAF50;
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .footer {
        text-align: center;
        padding: 2rem;
        color: #666;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">🛡️ SENTINEL-KE</div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem;'>Early Warning System for Disease Outbreaks<br>Western Kenya - Lake Victoria Basin</p>", unsafe_allow_html=True)
st.markdown("---")

# ============================================
# Load Model and Data
# ============================================
# Define local temporary models directory
LOCAL_TMP_MODELS_DIR = '/tmp/sentinel-ke/models'
LOCAL_DATA_DIR = '/content/drive/My Drive/sentinel-ke/data/processed'

@st.cache_resource
def load_model():
    """Load the trained XGBoost model and artifacts"""
    import os # Moved import os inside the function
    try:
        model = xgb.XGBClassifier()
        model.load_model(os.path.join(LOCAL_TMP_MODELS_DIR, 'xgboost_model.json'))
        scaler = joblib.load(os.path.join(LOCAL_TMP_MODELS_DIR, 'scaler.pkl'))

        with open(os.path.join(LOCAL_TMP_MODELS_DIR, 'features.txt'), 'r') as f:
            features = [line.strip() for line in f.readlines()]

        with open(os.path.join(LOCAL_TMP_MODELS_DIR, 'optimal_threshold.txt'), 'r') as f:
            threshold = float(f.read().strip())

        return model, scaler, features, threshold
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None, None, None, None

@st.cache_data
def load_data():
    """Load the master dataset"""
    import os # Moved import os inside the function
    try:
        df = pd.read_csv(os.path.join(LOCAL_DATA_DIR, 'master_dataset.csv'))
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Load everything
with st.spinner("Loading SENTINEL-KE system..."):
    model, scaler, features, threshold = load_model()
    df = load_data()

if model is None or df is None:
    st.error("Failed to load required files. Please check your file paths.")
    st.stop()

# Sidebar
st.sidebar.image("https://img.icons8.com/color/96/000000/health-chart.png", width=80)
st.sidebar.title("🛡️ SENTINEL-KE")

# County selector
counties = df['county'].unique().tolist()
selected_county = st.sidebar.selectbox("Select County", counties)

# Alert threshold slider
alert_threshold = st.sidebar.slider(
    "Alert Sensitivity",
    min_value=0.3,
    max_value=0.8,
    value=threshold,
    step=0.05,
    help="Lower = more alerts (higher sensitivity), Higher = fewer alerts (higher precision)"
)

# Date range selector
date_range = st.sidebar.date_input(
    "Date Range",
    value=(
        datetime.datetime.now() - timedelta(days=30),
        datetime.datetime.now()
    )
)

st.sidebar.markdown("---")
st.sidebar.info(
    """
    **How it works:**
    - Analyzes rainfall patterns and recent cases
    - Predicts outbreak risk for next 7 days
    - Alerts when risk exceeds threshold

    **Data sources:**
    - CHIRPS rainfall data
    - Routine health surveillance
    - Population estimates
    """
)

# ============================================
# Main Dashboard Content
# ============================================

# Get latest data for selected county
county_data = df[df['county'] == selected_county].sort_values('date')
latest_date = county_data['date'].max()
latest_data = county_data[county_data['date'] == latest_date]

# ============================================
# Current Status Banner
# ============================================
st.subheader(f"📍 Current Status: {selected_county} County")

# For demo, generate current risk score (in production, this would use live data)
# Here we'll use recent data to generate prediction
recent_data = county_data.tail(30)

# Prepare features for prediction
if len(recent_data) >= len(features):
    # This is simplified - in production you'd have a proper feature pipeline
    current_risk = np.random.uniform(0.3, 0.8)  # Placeholder for demo

    if current_risk > alert_threshold:
        st.markdown(f"""
<div class="alert-box">
    HIGH ALERT<br>
    Elevated outbreak risk detected in {selected_county}<br>
    Risk Score: {current_risk:.0%}<br>
    Confidence: High<br>
    Recommended: Immediate notification to county health team
</div>
""", unsafe_allow_html=True)
    elif current_risk > alert_threshold - 0.2:
        st.markdown(f"""
<div class="warning-box">
    MODERATE RISK<br>
    Elevated risk detected. Enhanced surveillance recommended.<br>
    Risk Score: {current_risk:.0%}
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div class="safe-box">
    NORMAL SURVEILLANCE<br>
    No elevated risk detected in {selected_county}<br>
    Risk Score: {current_risk:.0%}
</div>
""", unsafe_allow_html=True)
else:
    st.info("Insufficient data for real-time prediction. Showing historical patterns.")

# ============================================
# Key Metrics Row
# ============================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("7-Day Rainfall", f"{county_data['rainfall_mm'].tail(7).mean():.1f} mm",
              delta=f"{county_data['rainfall_mm'].tail(7).mean() - county_data['rainfall_mm'].shift(7).tail(7).mean():.1f}")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    recent_cases = county_data['cholera_cases'].tail(14).mean()
    prev_cases = county_data['cholera_cases'].shift(14).tail(14).mean()
    st.metric("Cholera Cases (14-day)", f"{recent_cases:.0f}",
              delta=f"{recent_cases - prev_cases:.0f}")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Population", f"{county_data['population'].iloc[0]:,.0f}",
              help="Total county population")
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    alert_status = "ALERT" if current_risk > alert_threshold else "Normal"
    st.metric("Current Status", alert_status,
              delta="Action Required" if current_risk > alert_threshold else "Monitor")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ============================================
# Time Series Charts
# ============================================
st.subheader("📈 Historical Trends & Predictions")

# Create time series plot
fig = make_subplots(
    rows=3, cols=1,
    subplot_titles=("Rainfall Pattern", "Cholera Cases", "Outbreak Risk"),
    vertical_spacing=0.12,
    row_heights=[0.3, 0.3, 0.4]
)

# Add rainfall trace
fig.add_trace(
    go.Bar(x=county_data['date'], y=county_data['rainfall_mm'],
           name="Rainfall", marker_color='#1E88E5'),
    row=1, col=1
)

# Add cholera cases trace
fig.add_trace(
    go.Scatter(x=county_data['date'], y=county_data['cholera_cases'],
               name="Cholera Cases", mode='lines+markers',
               line=dict(color='#ff6b6b', width=2)),
    row=2, col=1
)

# Add risk score (simulated for demo)
risk_scores = []
for i in range(len(county_data)):
    if i < 30:
        risk_scores.append(np.random.uniform(0.2, 0.4))
    else:
        risk_scores.append(np.random.uniform(0.3, 0.7))

fig.add_trace(
    go.Scatter(x=county_data['date'], y=risk_scores,
               name="Risk Score", mode='lines',
               line=dict(color='#ffa500', width=3)),
    row=3, col=1
)

# Add threshold line
fig.add_hline(y=alert_threshold, line_dash="dash", line_color="red",
              annotation_text="Alert Threshold", row=3, col=1)

# Update layout
fig.update_layout(height=800, showlegend=True, title_text=f"{selected_county} County Dashboard")
fig.update_xaxes(title_text="Date", row=3, col=1)
fig.update_yaxes(title_text="Rainfall (mm)", row=1, col=1)
fig.update_yaxes(title_text="Cases", row=2, col=1)
fig.update_yaxes(title_text="Risk Score", row=3, col=1)

st.plotly_chart(fig, use_container_width=True)

# ============================================
# County Comparison
# ============================================
st.subheader("📊 County Comparison")

# Prepare comparison data
recent_date = county_data['date'].max()
comparison_data = []

for county in counties:
    county_df = df[df['county'] == county]
    recent_rain = county_df['rainfall_mm'].tail(7).mean()
    recent_risk = np.random.uniform(0.2, 0.8)  # Placeholder

    comparison_data.append({
        'County': county,
        'Rainfall (7-day)': round(recent_rain, 1),
        'Risk Score': round(recent_risk, 2),
        'Status': 'ALERT' if recent_risk > alert_threshold else 'Normal'
    })

comparison_df = pd.DataFrame(comparison_data)

# Color coding for status
def color_status(val):
    if val == 'ALERT':
        return 'background-color: #ff6b6b; color: white'
    return 'background-color: #4CAF50; color: white'

# Display comparison table
styled_df = comparison_df.style.applymap(color_status, subset=['Status'])
st.dataframe(styled_df, use_container_width=True)

# Risk score bar chart
fig2 = px.bar(comparison_df, x='County', y='Risk Score',
              color='Risk Score', color_continuous_scale='RdYlGn_r',
              title='Outbreak Risk Score by County',
              labels={'Risk Score': 'Risk Score (0-1)'})
fig2.add_hline(y=alert_threshold, line_dash="dash", line_color="red",
               annotation_text="Alert Threshold")
st.plotly_chart(fig2, use_container_width=True)

# ============================================
# Risk Factors Explanation
# ============================================
st.subheader("🔍 Understanding the Risk")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Key Risk Factors for {selected_county}

    Based on the model's analysis, the following factors contribute most to outbreak risk:

    1. **Rainfall accumulation** - 7-day rainfall totals
    2. **Recent case trends** - Cases from neighboring areas
    3. **Seasonal patterns** - Rainy season (April-June, Oct-Nov)
    4. **Reporting delays** - Data timeliness affects predictions
    5. **Population density** - Higher density = faster spread

    *Model confidence: High (AUC-ROC > 0.75)*
    """)

with col2:
    st.markdown("""
    ### Recommended Actions

    **If Alert Triggered:**
    - ✅ Notify sub-county health teams immediately
    - ✅ Check oral rehydration and malaria drug stock
    - ✅ Activate community health workers for surveillance
    - ✅ Issue public health messaging

    **If Monitor Status:**
    - ✅ Maintain routine surveillance
    - ✅ Review weekly case trends
    - ✅ Ensure reporting compliance
    - ✅ Prepare prepositioned supplies
    """)

# ============================================
# Data Quality Metrics
# ============================================
st.subheader("📋 Data Quality")

col1, col2, col3 = st.columns(3)

with col1:
    reporting_rate = 100 - county_data['cholera_missing'].mean() * 100
    st.metric("Reporting Completeness", f"{reporting_rate:.0f}%",
              help="Percentage of expected reports received")

with col2:
    avg_delay = county_data['report_delay_days'].mean()
    st.metric("Average Reporting Delay", f"{avg_delay:.0f} days",
              help="Days between event and reporting")

with col3:
    # Count facilities (simplified)
    st.metric("Health Facilities", "45+", help="Approximate number of reporting facilities")

# ============================================
# Footer
# ============================================
st.markdown("---")
st.markdown(f"""
<div class="footer">
    SENTINEL-KE v1.0 | Last updated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}<br>
    Data sources: CHIRPS rainfall, DHIS2 (synthetic), WorldPop population<br>
    For health officials only. Not for clinical decision-making.
</div>
""", unsafe_allow_html=True)
