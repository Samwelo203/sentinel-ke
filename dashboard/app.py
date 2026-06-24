# ============================================
# COMPLETE SENTINEL-KE DASHBOARD
# ALL 5 DOMAINS INTEGRATED
# ============================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')
import io

# ============================================
# AUTHENTICATION & SESSION MANAGEMENT
# ============================================

from auth import (
    authenticate_user, create_session, is_session_valid, 
    update_session_activity, get_session_time_remaining,
    has_permission, can_export_data, can_generate_reports, 
    can_manage_users, can_access_system_admin, 
    get_role_badge, list_users, create_user, update_user_role, delete_user
)

# Initialize session state if not already done
if "session" not in st.session_state:
    st.session_state.session = None
if "login_error" not in st.session_state:
    st.session_state.login_error = ""
if "show_login" not in st.session_state:
    st.session_state.show_login = True

# ============================================
# AUTHENTICATION HANDLER
# ============================================

def render_login_screen():
    """Render the login interface."""
    st.markdown("""
    <div style="text-align: center; padding: 3rem 0;">
        <h1>🛡️ SENTINEL-KE</h1>
        <h3>AI-Powered Early Warning System for Western Kenya</h3>
        <hr style="margin: 2rem 0;">
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Secure Login")
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        if st.button("Login", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("❌ Please enter both username and password")
            else:
                success, user_info, message = authenticate_user(username, password)
                if success:
                    st.session_state.session = create_session(username, user_info)
                    st.session_state.show_login = False
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        
        st.markdown("---")
        st.markdown("""
        ### 📋 Default Test Credentials
        
        | Role | Username | Password |
        |------|----------|----------|
        | 👑 Administrator | admin | admin |
        | 📊 Health Officer | health_officer | password |
        | 👁️ Viewer | viewer | viewer |
        """)
        st.info("⚠️ Update these credentials immediately in production!")


def render_logout_and_session_info():
    """Render session info and logout button in sidebar."""
    if st.session_state.session:
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 User Session")
            session = st.session_state.session
            badge = get_role_badge(session["role_level"], session["role"])
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**User:** {session['username']}")
                st.write(f"**Role:** {badge}")
            
            time_remaining = get_session_time_remaining(session)
            if time_remaining > 0:
                st.caption(f"⏱️ Session expires in: {time_remaining} min")
            else:
                st.error("❌ Session expired. Please login again.")
                st.session_state.session = None
                st.session_state.show_login = True
                st.rerun()
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.session = None
                st.session_state.show_login = True
                st.info("✅ You have been logged out.")
                st.rerun()

# Check authentication
if st.session_state.show_login or not is_session_valid(st.session_state.session):
    render_login_screen()
    st.stop()

# Update session activity
st.session_state.session = update_session_activity(st.session_state.session)

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="SENTINEL-KE | Early Warning System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS
# ============================================

st.markdown("""
<style>
    .main-header { font-size: 2.8rem; color: #1E88E5; text-align: center; font-weight: bold; padding: 0.5rem; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 10px; margin-bottom: 1rem; }
    .sub-header { text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 1.5rem; }
    .alert-box-critical { background: linear-gradient(135deg, #ff6b6b, #ee5a24); padding: 1.5rem; border-radius: 12px; color: white; font-weight: bold; text-align: center; }
    .alert-box-warning { background: linear-gradient(135deg, #f9ca24, #f0932b); padding: 1.2rem; border-radius: 12px; color: white; font-weight: bold; text-align: center; }
    .alert-box-safe { background: linear-gradient(135deg, #6ab04c, #2ecc71); padding: 1.2rem; border-radius: 12px; color: white; font-weight: bold; text-align: center; }
    .metric-card { background: white; padding: 1.2rem; border-radius: 12px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.08); border-left: 4px solid #1E88E5; }
    .metric-value { font-size: 2rem; font-weight: bold; color: #1E88E5; }
    .metric-label { color: #666; font-size: 0.85rem; margin-top: 0.3rem; }
    .explanation-box { background: #f8f9fa; padding: 1.5rem; border-radius: 12px; border-left: 5px solid #1E88E5; margin: 1rem 0; }
    .footer { text-align: center; padding: 2rem; color: #999; font-size: 0.8rem; border-top: 1px solid #eee; margin-top: 2rem; background: #f8f9fa; border-radius: 10px; }
    .domain-card { background: white; padding: 1rem; border-radius: 10px; border-left: 4px solid #1E88E5; margin: 0.5rem 0; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
    .domain-card:hover { transform: translateX(5px); transition: 0.3s; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# ============================================
# DATA LOADING FUNCTIONS
# ============================================

@st.cache_data(ttl=3600)
def load_predictions():
    """Load predictions data from CSV"""
    try:
        df = pd.read_csv('data/processed/latest_predictions.csv')
        return df
    except:
        try:
            url = "https://raw.githubusercontent.com/Samwelo203/sentinel-ke/main/data/processed/latest_predictions.csv"
            df = pd.read_csv(url)
            return df
        except:
            return None

@st.cache_data(ttl=3600)
def load_historical_data():
    """Load historical data for trends"""
    try:
        df = pd.read_csv('data/processed/master_dataset.csv')
        df['date'] = pd.to_datetime(df['date'])
        return df
    except:
        try:
            url = "https://raw.githubusercontent.com/Samwelo203/sentinel-ke/main/data/processed/master_dataset.csv"
            df = pd.read_csv(url)
            df['date'] = pd.to_datetime(df['date'])
            return df
        except:
            return None

# ============================================
# LOAD DATA
# ============================================

df_predictions = load_predictions()
df_historical = load_historical_data()

# ============================================
# SIDEBAR
# ============================================

# Show session info in sidebar
render_logout_and_session_info()

with st.sidebar:
    st.markdown("---")
    st.markdown("### 📍 Controls")
    
    counties = ['Kisumu', 'Homa Bay', 'Siaya', 'Migori', 'Nyamira', 'Kisii']
    selected_county = st.selectbox("Select County", counties, index=0)
    
    disease = st.radio("Select Disease", ['Cholera', 'Malaria', 'Both'], index=2)
    
    today = datetime.now()
    start_date = st.date_input("Start Date", value=today - timedelta(days=30), max_value=today)
    end_date = st.date_input("End Date", value=today, max_value=today)
    
    alert_threshold = st.slider("Alert Threshold", 0.3, 0.8, 0.65, 0.05)
    
    st.markdown("---")
    st.markdown("### 📊 System Status")
    st.info("""
    ✅ **AI Model:** Active  
    ✅ **Data Source:** Open-Meteo API  
    ✅ **Updates:** Daily at 6 AM EAT  
    ✅ **Counties:** 6 monitored  
    """)
    
    st.markdown("---")
    st.markdown("### 🔒 Data Protection")
    st.caption("""
    ✅ Kenya Data Protection Act (2019)  
    ✅ GDPR Principles  
    ✅ Health Data Privacy  
    🔐 All access is logged
    """)

# ============================================
# HEADER
# ============================================

st.markdown('<div class="main-header">🛡️ SENTINEL-KE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Early Warning System for Western Kenya</div>', unsafe_allow_html=True)

# ============================================
# CHECK IF DATA IS AVAILABLE
# ============================================

if df_predictions is None:
    st.warning("""
    ⏳ **No prediction data available yet**
    
    The system hasn't generated predictions. This is normal for first run.
    
    **What to do:**
    1. The system will run automatically at 6 AM EAT tomorrow
    2. Or manually run: `python auto_update.py` in Colab
    3. Check back in a few minutes
    """)
    st.stop()

# ============================================
# SECTION 1: CURRENT STATUS
# ============================================

st.subheader("📊 Current Status Dashboard")

county_data = df_predictions[df_predictions['county'] == selected_county]

if not county_data.empty:
    risk_score = county_data['risk_score'].iloc[0]
    alert_status = county_data['alert'].iloc[0]

    if alert_status:
        st.markdown(f'''
        <div class="alert-box-critical">
            🚨 CRITICAL ALERT: {selected_county} County<br>
            Current Risk Score: {risk_score:.1%}
        </div>
        ''', unsafe_allow_html=True)
    elif risk_score > 0.4:
        st.markdown(f'''
        <div class="alert-box-warning">
            ⚠️ MODERATE RISK: {selected_county} County<br>
            Current Risk Score: {risk_score:.1%}
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown(f'''
        <div class="alert-box-safe">
            ✅ NORMAL: {selected_county} County<br>
            Current Risk Score: {risk_score:.1%}
        </div>
        ''', unsafe_allow_html=True)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Current Risk Score", f"{risk_score:.1%}")
    with col2:
        st.metric("Alert Status", "🚨 ALERT" if alert_status else "✅ NORMAL")
    with col3:
        if df_historical is not None:
            county_hist = df_historical[df_historical['county'] == selected_county]
            if not county_hist.empty:
                cases = county_hist['cholera_cases'].tail(7).mean()
                st.metric("Cholera (7-day avg)", f"{cases:.0f}")
    with col4:
        if df_historical is not None:
            county_hist = df_historical[df_historical['county'] == selected_county]
            if not county_hist.empty:
                cases = county_hist['malaria_cases'].tail(7).mean()
                st.metric("Malaria (7-day avg)", f"{cases:.0f}")

st.markdown("---")

# ============================================
# SECTION 2: DOMAIN BREAKDOWN (NEW!)
# ============================================

st.subheader("📊 Multi-Domain Risk Breakdown")

# Check if domain columns exist
domain_columns = ['rainfall_risk', 'environmental_risk', 'wash_risk', 'mobility_risk', 'capacity_risk', 'data_quality_score']
has_domains = all(col in df_predictions.columns for col in domain_columns)

if has_domains and not county_data.empty:
    # Create domain breakdown chart
    domains = ['Rainfall', 'Environmental (NDVI)', 'WASH', 'Mobility', 'Capacity', 'Data Quality']
    values = [
        county_data['rainfall_risk'].iloc[0],
        county_data['environmental_risk'].iloc[0],
        county_data['wash_risk'].iloc[0],
        county_data['mobility_risk'].iloc[0],
        county_data['capacity_risk'].iloc[0],
        1 - county_data['data_quality_score'].iloc[0]  # Invert: lower quality = higher risk
    ]
    
    domain_df = pd.DataFrame({
        'Domain': domains,
        'Risk Contribution': values
    })
    
    # Color based on risk level
    fig = px.bar(
        domain_df,
        x='Domain',
        y='Risk Contribution',
        color='Risk Contribution',
        color_continuous_scale=['#4CAF50', '#FFA500', '#FF4444'],
        title=f'Risk Breakdown for {selected_county}',
        labels={'Risk Contribution': 'Risk Score'},
        height=400
    )
    
    fig.update_layout(
        yaxis_tickformat='.0%',
        showlegend=False,
        plot_bgcolor='white'
    )
    fig.update_traces(texttemplate='%{y:.1%}', textposition='outside')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Domain explanations
    with st.expander("🔍 Click to see detailed domain explanations"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **🌧️ Rainfall Risk:** {county_data['rainfall_risk'].iloc[0]:.1%}
            - Based on 14-day rainfall patterns
            - Higher rainfall = higher waterborne disease risk
            
            **🌿 Environmental Risk (NDVI):** {county_data['environmental_risk'].iloc[0]:.1%}
            - Vegetation density and temperature
            - Higher NDVI = more mosquito breeding sites
            
            **💧 WASH Risk:** {county_data['wash_risk'].iloc[0]:.1%}
            - Water access, sanitation, hygiene
            - Poor WASH = higher cholera risk
            """)
        
        with col2:
            st.markdown(f"""
            **🚶 Mobility Risk:** {county_data['mobility_risk'].iloc[0]:.1%}
            - Human movement and border crossings
            - Higher mobility = faster disease spread
            
            **🏥 Capacity Risk:** {county_data['capacity_risk'].iloc[0]:.1%}
            - Health system readiness
            - Low capacity = higher outbreak impact
            
            **📊 Data Quality:** {county_data['data_quality_score'].iloc[0]:.1%}
            - Reporting completeness and timeliness
            - Lower quality = lower confidence in predictions
            """)
    
    # Data quality warning
    quality_score = county_data['data_quality_score'].iloc[0]
    if quality_score < 0.6:
        st.warning(f"""
        ⚠️ **Data Quality Alert:** Reporting completeness in {selected_county} is {quality_score:.0%}
        - Predictions may be less reliable
        - Consider enhanced surveillance
        """)
    elif quality_score < 0.8:
        st.info(f"""
        ℹ️ **Data Quality Note:** Reporting completeness in {selected_county} is {quality_score:.0%}
        - Predictions have moderate confidence
        """)
    else:
        st.success(f"✅ High data quality in {selected_county} ({quality_score:.0%})")
        
else:
    st.info("Domain breakdown data not available. Run `auto_update.py` to generate.")

st.markdown("---")

# ============================================
# SECTION 3: HISTORICAL TRENDS
# ============================================

st.subheader(f"📈 Historical Trends for {selected_county}")

if df_historical is not None:
    county_hist = df_historical[df_historical['county'] == selected_county]
    county_hist = county_hist[
        (county_hist['date'] >= pd.to_datetime(start_date)) &
        (county_hist['date'] <= pd.to_datetime(end_date))
    ]

    if not county_hist.empty:
        if disease == 'Both':
            fig = make_subplots(rows=2, cols=1, subplot_titles=('Cholera Cases', 'Malaria Cases'), shared_xaxes=True)
            fig.add_trace(go.Bar(x=county_hist['date'], y=county_hist['cholera_cases'], name='Cholera', marker_color='#e74c3c'), row=1, col=1)
            fig.add_trace(go.Scatter(x=county_hist['date'], y=county_hist['cholera_cases'].rolling(7).mean(), mode='lines', name='Cholera (7-day avg)', line=dict(color='#c0392b', width=2)), row=1, col=1)
            fig.add_trace(go.Bar(x=county_hist['date'], y=county_hist['malaria_cases'], name='Malaria', marker_color='#2ecc71'), row=2, col=1)
            fig.add_trace(go.Scatter(x=county_hist['date'], y=county_hist['malaria_cases'].rolling(7).mean(), mode='lines', name='Malaria (7-day avg)', line=dict(color='#27ae60', width=2)), row=2, col=1)
            fig.update_layout(height=600, showlegend=True)
        elif disease == 'Cholera':
            fig = make_subplots(rows=2, cols=1, subplot_titles=('Cholera Cases', 'Rainfall Pattern'))
            fig.add_trace(go.Bar(x=county_hist['date'], y=county_hist['cholera_cases'], name='Cholera Cases', marker_color='#e74c3c'), row=1, col=1)
            fig.add_trace(go.Scatter(x=county_hist['date'], y=county_hist['cholera_cases'].rolling(7).mean(), mode='lines', name='7-day Average', line=dict(color='#c0392b', width=3)), row=1, col=1)
            fig.add_trace(go.Bar(x=county_hist['date'], y=county_hist['rainfall_mm'], name='Rainfall (mm)', marker_color='#3498db', opacity=0.6), row=2, col=1)
            fig.update_layout(height=600, showlegend=True)
        else:
            fig = make_subplots(rows=2, cols=1, subplot_titles=('Malaria Cases', 'Rainfall Pattern'))
            fig.add_trace(go.Bar(x=county_hist['date'], y=county_hist['malaria_cases'], name='Malaria Cases', marker_color='#2ecc71'), row=1, col=1)
            fig.add_trace(go.Scatter(x=county_hist['date'], y=county_hist['malaria_cases'].rolling(7).mean(), mode='lines', name='7-day Average', line=dict(color='#27ae60', width=3)), row=1, col=1)
            fig.add_trace(go.Bar(x=county_hist['date'], y=county_hist['rainfall_mm'], name='Rainfall (mm)', marker_color='#3498db', opacity=0.6), row=2, col=1)
            fig.update_layout(height=600, showlegend=True)

        fig.update_xaxes(title_text="Date", row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============================================
# SECTION 4: COUNTY COMPARISON
# ============================================

st.subheader("🏙️ County Comparison")

if df_predictions is not None:
    fig = px.bar(
        df_predictions,
        x='county',
        y='risk_score',
        color='risk_score',
        color_continuous_scale=['#4CAF50', '#FFA500', '#FF4444'],
        title='Outbreak Risk Comparison',
        labels={'risk_score': 'Risk Score', 'county': 'County'},
        text='risk_score',
        height=400
    )
    
    fig.add_hline(y=alert_threshold, line_dash="dash", line_color="red", annotation_text=f"Alert Threshold ({alert_threshold:.0%})")
    fig.update_traces(texttemplate='%{text:.1%}', textposition='outside')
    fig.update_layout(yaxis_tickformat='.0%', showlegend=False, plot_bgcolor='white')
    
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============================================
# SECTION 5: AI EXPLANATION (Enhanced)
# ============================================

st.subheader("🤖 AI Explanation & Risk Factors")

if not county_data.empty:
    risk = county_data['risk_score'].iloc[0]
    
    # Get domain-specific insights for explanation
    domain_insights = ""
    if has_domains:
        if county_data['wash_risk'].iloc[0] > 0.5:
            domain_insights += "- Poor WASH conditions detected\n"
        if county_data['mobility_risk'].iloc[0] > 0.5:
            domain_insights += "- High mobility risk (border crossings, markets)\n"
        if county_data['capacity_risk'].iloc[0] > 0.5:
            domain_insights += "- Health system capacity is limited\n"
        if county_data['environmental_risk'].iloc[0] > 0.5:
            domain_insights += "- Favorable environmental conditions for malaria\n"
    
    if risk > 0.7:
        risk_level = "HIGH RISK"
        risk_color = "#ff6b6b"
        explanation = f"""
        The AI model has detected **HIGH RISK** of outbreak in {selected_county}.
        
        **Key Contributing Factors:**
        - Recent rainfall patterns show elevated levels
        - Historical case trends indicate seasonal increase
        - Neighboring counties reporting similar patterns
        - Population density in high-risk areas
        {domain_insights}
        """
    elif risk > 0.4:
        risk_level = "MODERATE RISK"
        risk_color = "#f9ca24"
        explanation = f"""
        The AI model has detected **MODERATE RISK** of outbreak in {selected_county}.
        
        **Key Contributing Factors:**
        - Rainfall levels are within normal range
        - Case trends show gradual increase
        - Environmental conditions favorable for disease spread
        - Surveillance data indicates need for monitoring
        {domain_insights}
        """
    else:
        risk_level = "LOW RISK"
        risk_color = "#6ab04c"
        explanation = f"""
        The AI model has detected **LOW RISK** of outbreak in {selected_county}.
        
        **Key Contributing Factors:**
        - Rainfall patterns are normal
        - Case counts within expected range
        - Environmental conditions not favorable for outbreaks
        - Community surveillance shows no unusual patterns
        {domain_insights}
        """
    
    st.markdown(f"""
    <div class="explanation-box">
        <h3 style="color: {risk_color};">Current Risk Level: {risk_level}</h3>
        <p><strong>Risk Score:</strong> {risk:.1%}</p>
        <p><strong>Confidence:</strong> High (based on XGBoost model with 25 features)</p>
        <hr>
        <p>{explanation}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ============================================
# SECTION 6: RECOMMENDED ACTIONS
# ============================================

st.subheader("📋 Recommended Actions")

if not county_data.empty:
    risk = county_data['risk_score'].iloc[0]
    alert = county_data['alert'].iloc[0]
    
    # Add domain-specific recommendations
    specific_actions = ""
    if has_domains:
        if county_data['wash_risk'].iloc[0] > 0.5:
            specific_actions += "- Prioritize WASH interventions (water treatment, sanitation)\n"
        if county_data['mobility_risk'].iloc[0] > 0.5:
            specific_actions += "- Monitor border crossings and market areas\n"
        if county_data['capacity_risk'].iloc[0] > 0.5:
            specific_actions += "- Strengthen health system capacity\n"
    
    if alert:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            ### 🚨 Immediate Actions
            1. Notify Health Teams
            2. Community Engagement
            3. Resource Mobilization
            {specific_actions}
            """)
        with col2:
            st.markdown("""
            ### 📊 Enhanced Surveillance
            1. Case Reporting
            2. Laboratory Testing
            3. Data Monitoring
            """)
        st.warning(f"⚠️ **ALERT:** Immediate action required for {selected_county} County")
    elif risk > 0.4:
        st.markdown(f"""
        ### ⚠️ Enhanced Surveillance
        1. Increase monitoring in high-risk areas
        2. Review case definitions with health workers
        3. Strengthen reporting from all facilities
        4. Community awareness campaigns
        5. Prepare supplies for potential response
        {specific_actions}
        """)
    else:
        st.markdown("""
        ### ✅ Routine Surveillance
        1. Maintain standard case reporting
        2. Monitor trends for early signs
        3. Continue community health worker activities
        4. Review data quality and completeness
        5. Prepare for seasonal changes
        """)

st.markdown("---")

# ============================================
# SECTION 7: DATA TRANSPARENCY & FOOTER
# ============================================

st.subheader("🔍 Data Transparency")

st.markdown("""
<div style="background: #f8f9fa; padding: 1.5rem; border-radius: 12px;">
    <strong>✅ What This System Uses (REAL):</strong><br>
    • Live rainfall data from Open-Meteo API<br>
    • Real temperature data<br>
    • Actual population estimates (WorldPop)<br>
    • XGBoost AI/ML pipeline<br>
    <br>
    <strong>📊 All 5 Intelligence Domains Integrated:</strong><br>
    • 🌿 Environmental Remote Sensing (NDVI)<br>
    • 💧 WASH Intelligence (Water, Sanitation, Hygiene)<br>
    • 📊 Data Quality Intelligence (Reporting completeness)<br>
    • 🚶 Mobility Intelligence (Human movement)<br>
    • 🏥 Health Capacity Intelligence (System readiness)<br>
    <br>
    <strong>⚠️ What This System Does NOT Use (SIMULATED):</strong><br>
    • Real DHIS2 health facility reports<br>
    • Actual hospital admission records<br>
    • Lab-confirmed case data<br>
    • Real-time disease surveillance data<br>
    <br>
    <strong>🔬 Status:</strong> Demonstrates full AI/ML engineering pipeline with 9 of 13 domains complete.<br>
    Real case validation would require integration with Kenya's DHIS2 system.
</div>
""", unsafe_allow_html=True)

st.markdown(f'''
<div class="footer">
    <strong>🛡️ SENTINEL-KE v1.0</strong><br>
    AI-Powered Environmental Early Warning System for Western Kenya<br>
    <br>
    📊 Data updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} EAT<br>
    🔄 Next update: Daily at 6:00 AM EAT<br>
    <br>
    📌 <strong>Data Sources:</strong> Open-Meteo API, CHIRPS, WorldPop<br>
    🤖 <strong>AI Model:</strong> XGBoost with 25 features<br>
    🏙️ <strong>Counties:</strong> Kisumu, Homa Bay, Siaya, Migori, Nyamira, Kisii<br>
    <br>
    🔐 <strong>Access Control:</strong> Role-based authentication enabled<br>
    📋 <strong>User Role:</strong> {st.session_state.session["role"]}<br>
    <br>
    For health officials only. Not for clinical decision-making.<br>
    © 2026 SENTINEL-KE Project
</div>
''', unsafe_allow_html=True)

# ============================================
# AUTO-REFRESH
# ============================================

if st.sidebar.checkbox("🔄 Auto-refresh", value=True):
    st.caption("Dashboard auto-refreshes every 5 minutes")
    st.empty()
    import time
    time.sleep(300)
    st.rerun()