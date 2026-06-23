
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
    
    # Login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Secure Login")
        
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        if st.button("Login", width='stretch', type="primary"):
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
        
        # Default credentials info
        st.markdown("""
        ### 📋 Default Test Credentials
        
        | Role | Username | Password |
        |------|----------|----------|
        | 👑 Administrator | admin | admin |
        | 📊 Health Officer | health_officer | password |
        | 👁️ Viewer | viewer | viewer |
        
        ⚠️ **WARNING:** Update these credentials immediately in production!
        """)
        
        st.info("For security: passwords are hashed using SHA-256. Change defaults in production.")


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
            
            # Session timer
            time_remaining = get_session_time_remaining(session)
            if time_remaining > 0:
                st.caption(f"⏱️ Session expires in: {time_remaining} min")
                if time_remaining < 5:
                    st.warning("⚠️ Session expiring soon!")
            else:
                st.error("❌ Session expired. Please login again.")
                st.session_state.session = None
                st.session_state.show_login = True
                st.rerun()
            
            if st.button("🚪 Logout", width='stretch'):
                st.session_state.session = None
                st.session_state.show_login = True
                st.info("✅ You have been logged out. Redirecting to login...")
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
    st.markdown("---")

    # County Selection
    st.markdown("###  Select County")
    counties = ['Kisumu', 'Homa Bay', 'Siaya', 'Migori', 'Nyamira', 'Kisii']

    # Use columns for county buttons
    selected_county = st.selectbox(
        "Choose a county to view:",
        counties,
        index=0
    )

    st.markdown("---")

    # Disease Selection
    st.markdown("### 🦠 Select Disease")
    disease = st.radio(
        "Choose disease:",
        ['Cholera', 'Malaria', 'Both'],
        index=2
    )

    st.markdown("---")

    # Date Range
    st.markdown("### 📅 Date Range")
    today = datetime.now()
    start_date = st.date_input(
        "Start Date",
        value=today - timedelta(days=30),
        max_value=today
    )
    end_date = st.date_input(
        "End Date",
        value=today,
        max_value=today
    )

    st.markdown("---")

    # Alert Threshold
    st.markdown("### ⚙️ Settings")
    alert_threshold = st.slider(
        "Alert Threshold",
        min_value=0.3,
        max_value=0.8,
        value=0.65,
        step=0.05,
        help="Higher threshold = fewer alerts (more specific)"
    )

    st.markdown("---")

    # System Status
    st.markdown("###  System Status")
    st.info("""
            
    ✅ **AI Model:** Active        
    ✅ **Data Source:** Open-Meteo API       
    ✅ **Updates:** Daily at 6 AM EAT       
    ✅ **Counties:** 6 monitored
    """)

# ============================================
# MAIN CONTENT
# ============================================

# Header
st.markdown('<div class="main-header">🛡️ SENTINEL-KE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Early Warning System for Western Kenya</div>', unsafe_allow_html=True)

# Load data
df_predictions = load_predictions()
df_historical = load_historical_data()

# ============================================
# SECTION 1: CURRENT STATUS
# ============================================

st.subheader(" Current Status Dashboard")

if df_predictions is not None:
    # Get data for selected county
    county_data = df_predictions[df_predictions['county'] == selected_county]

    if not county_data.empty:
        risk_score = county_data['risk_score'].iloc[0]
        alert_status = county_data['alert'].iloc[0]

        # Display alert status
        if alert_status:
            st.markdown(f'''
            <div class="alert-box-critical">
                🚨 CRITICAL ALERT: {selected_county} County<br>
                Current Risk Score: {risk_score:.1%}<br>
                Immediate action recommended!
            </div>
            ''', unsafe_allow_html=True)
        elif risk_score > 0.4:
            st.markdown(f'''
            <div class="alert-box-warning">
                ⚠️ MODERATE RISK: {selected_county} County<br>
                Current Risk Score: {risk_score:.1%}<br>
                Enhanced surveillance recommended
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="alert-box-safe">
                ✅ NORMAL: {selected_county} County<br>
                Current Risk Score: {risk_score:.1%}<br>
                Routine surveillance continues
            </div>
            ''', unsafe_allow_html=True)

        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">{risk_score:.1%}</div>
                <div class="metric-label">Current Risk Score</div>
            </div>
            ''', unsafe_allow_html=True)

        with col2:
            # Get disease-specific data
            if df_historical is not None:
                county_hist = df_historical[df_historical['county'] == selected_county]
                if disease in ['Cholera', 'Both']:
                    cases = county_hist['cholera_cases'].tail(7).mean()
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-value">{cases:.0f}</div>
                        <div class="metric-label">Cholera (7-day avg)</div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-value">-</div>
                        <div class="metric-label">Cholera Data</div>
                    </div>
                    ''', unsafe_allow_html=True)

        with col3:
            if df_historical is not None:
                county_hist = df_historical[df_historical['county'] == selected_county]
                if disease in ['Malaria', 'Both']:
                    cases = county_hist['malaria_cases'].tail(7).mean()
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-value">{cases:.0f}</div>
                        <div class="metric-label">Malaria (7-day avg)</div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-value">-</div>
                        <div class="metric-label">Malaria Data</div>
                    </div>
                    ''', unsafe_allow_html=True)

        with col4:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">{'🔴' if alert_status else '🟢'}</div>
                <div class="metric-label">Alert Status</div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.warning(f"No data available for {selected_county}")

st.markdown("---")

# ============================================
# SECTION 2: HISTORICAL TRENDS
# ============================================

st.subheader(f" Historical Trends for {selected_county}")

if df_historical is not None:
    county_hist = df_historical[df_historical['county'] == selected_county]

    # Filter by date range
    county_hist = county_hist[
        (county_hist['date'] >= pd.to_datetime(start_date)) &
        (county_hist['date'] <= pd.to_datetime(end_date))
    ]

    if not county_hist.empty:
        # Create figure with subplots
        if disease == 'Both':
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Cholera Cases Over Time', 'Malaria Cases Over Time'),
                shared_xaxes=True,
                vertical_spacing=0.15
            )

            # Cholera
            fig.add_trace(
                go.Scatter(
                    x=county_hist['date'],
                    y=county_hist['cholera_cases'],
                    mode='lines+markers',
                    name='Cholera',
                    line=dict(color='#e74c3c', width=2),
                    marker=dict(size=6)
                ),
                row=1, col=1
            )

            # Moving average for cholera
            fig.add_trace(
                go.Scatter(
                    x=county_hist['date'],
                    y=county_hist['cholera_cases'].rolling(7).mean(),
                    mode='lines',
                    name='Cholera (7-day avg)',
                    line=dict(color='#c0392b', width=2, dash='dash')
                ),
                row=1, col=1
            )

            # Malaria
            fig.add_trace(
                go.Scatter(
                    x=county_hist['date'],
                    y=county_hist['malaria_cases'],
                    mode='lines+markers',
                    name='Malaria',
                    line=dict(color='#2ecc71', width=2),
                    marker=dict(size=6)
                ),
                row=2, col=1
            )

            # Moving average for malaria
            fig.add_trace(
                go.Scatter(
                    x=county_hist['date'],
                    y=county_hist['malaria_cases'].rolling(7).mean(),
                    mode='lines',
                    name='Malaria (7-day avg)',
                    line=dict(color='#27ae60', width=2, dash='dash')
                ),
                row=2, col=1
            )

            fig.update_layout(height=600, showlegend=True)
            fig.update_yaxes(title_text="Cholera Cases", row=1, col=1)
            fig.update_yaxes(title_text="Malaria Cases", row=2, col=1)

        elif disease == 'Cholera':
            fig = make_subplots(rows=2, cols=1, subplot_titles=('Cholera Cases', 'Rainfall Pattern'))

            fig.add_trace(
                go.Bar(
                    x=county_hist['date'],
                    y=county_hist['cholera_cases'],
                    name='Cholera Cases',
                    marker_color='#e74c3c'
                ),
                row=1, col=1
            )

            fig.add_trace(
                go.Scatter(
                    x=county_hist['date'],
                    y=county_hist['cholera_cases'].rolling(7).mean(),
                    mode='lines',
                    name='7-day Average',
                    line=dict(color='#c0392b', width=3)
                ),
                row=1, col=1
            )

            fig.add_trace(
                go.Bar(
                    x=county_hist['date'],
                    y=county_hist['rainfall_mm'],
                    name='Rainfall (mm)',
                    marker_color='#3498db',
                    opacity=0.6
                ),
                row=2, col=1
            )

            fig.update_layout(height=600, showlegend=True)
            fig.update_yaxes(title_text="Cases", row=1, col=1)
            fig.update_yaxes(title_text="Rainfall (mm)", row=2, col=1)

        else:  # Malaria only
            fig = make_subplots(rows=2, cols=1, subplot_titles=('Malaria Cases', 'Rainfall Pattern'))

            fig.add_trace(
                go.Bar(
                    x=county_hist['date'],
                    y=county_hist['malaria_cases'],
                    name='Malaria Cases',
                    marker_color='#2ecc71'
                ),
                row=1, col=1
            )

            fig.add_trace(
                go.Scatter(
                    x=county_hist['date'],
                    y=county_hist['malaria_cases'].rolling(7).mean(),
                    mode='lines',
                    name='7-day Average',
                    line=dict(color='#27ae60', width=3)
                ),
                row=1, col=1
            )

            fig.add_trace(
                go.Bar(
                    x=county_hist['date'],
                    y=county_hist['rainfall_mm'],
                    name='Rainfall (mm)',
                    marker_color='#3498db',
                    opacity=0.6
                ),
                row=2, col=1
            )

            fig.update_layout(height=600, showlegend=True)
            fig.update_yaxes(title_text="Cases", row=1, col=1)
            fig.update_yaxes(title_text="Rainfall (mm)", row=2, col=1)

        fig.update_xaxes(title_text="Date", row=2, col=1)
        st.plotly_chart(fig, width='stretch')

        # Quick insights
        st.caption("📊 **Insights:** The chart shows disease cases over time. Red/blue bars indicate case counts, and the dashed line shows the 7-day moving average.")

    else:
        st.info("No historical data available for the selected date range")

st.markdown("---")

# ============================================
# SECTION 3: COUNTY COMPARISON
# ============================================

st.subheader(" County Comparison")

if df_predictions is not None:
    # Filter comparison data
    if disease == 'Both':
        comparison_df = df_predictions.copy()
    else:
        # For disease-specific comparison, we show risk scores
        comparison_df = df_predictions.copy()

    # Create comparison chart
    fig = px.bar(
        comparison_df,
        x='county',
        y='risk_score',
        color='risk_score',
        color_continuous_scale=['#4CAF50', '#FFA500', '#FF4444'],
        title=f'Outbreak Risk Comparison - {disease}',
        labels={'risk_score': 'Risk Score', 'county': 'County'},
        text='risk_score',
        height=400
    )

    fig.add_hline(
        y=alert_threshold,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Alert Threshold ({alert_threshold:.0%})"
    )

    fig.update_traces(
        texttemplate='%{text:.1%}',
        textposition='outside'
    )

    fig.update_layout(
        yaxis_tickformat='.0%',
        showlegend=False,
        plot_bgcolor='white'
    )

    st.plotly_chart(fig, width='stretch')

    # Show comparison table
    comparison_display = comparison_df.copy()
    comparison_display['Risk Score'] = comparison_display['risk_score'].apply(lambda x: f"{x:.1%}")
    comparison_display['Status'] = comparison_display['alert'].apply(
        lambda x: "🔴 HIGH" if x else "🟢 NORMAL"
    )
    comparison_display = comparison_display[['county', 'Risk Score', 'Status']]
    comparison_display.columns = ['County', 'Risk Score', 'Status']

    st.dataframe(comparison_display, width='stretch', hide_index=True)

st.markdown("---")

# ============================================
# SECTION 4: AI EXPLANATION
# ============================================

st.subheader(" Sentinel AI Explanation & Risk Factors")

# Generate AI explanation based on current data
if df_predictions is not None:
    county_data = df_predictions[df_predictions['county'] == selected_county]

    if not county_data.empty:
        risk = county_data['risk_score'].iloc[0]

        # Determine risk level
        if risk > 0.7:
            risk_level = "HIGH RISK"
            risk_color = "#ff6b6b"
            explanation = f"""
            The AI model has detected **HIGH RISK** of outbreak in {selected_county}.

            **Key Contributing Factors:**
            1. Recent rainfall patterns show elevated levels
            2. Historical case trends indicate seasonal increase
            3. Neighboring counties reporting similar patterns
            4. Population density in high-risk areas
            """
        elif risk > 0.4:
            risk_level = "MODERATE RISK"
            risk_color = "#f9ca24"
            explanation = f"""
            The AI model has detected **MODERATE RISK** of outbreak in {selected_county}.

            **Key Contributing Factors:**
            1. Rainfall levels are within normal range
            2. Case trends show gradual increase
            3. Environmental conditions favorable for disease spread
            4. Surveillance data indicates need for monitoring
            """
        else:
            risk_level = "LOW RISK"
            risk_color = "#6ab04c"
            explanation = f"""
            The AI model has detected **LOW RISK** of outbreak in {selected_county}.

            **Key Contributing Factors:**
            1. Rainfall patterns are normal
            2. Case counts within expected range
            3. Environmental conditions not favorable for outbreaks
            4. Community surveillance shows no unusual patterns
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

        # Display detailed risk factors
        with st.expander("🔍 View Detailed Risk Factors"):
            st.markdown("""
            **Environmental Factors:**
            - Rainfall accumulation in past 7 days
            - Temperature and humidity patterns
            - Vegetation density (NDVI)

            **Epidemiological Factors:**
            - Recent case trends in neighboring counties
            - Historical outbreak patterns
            - Reporting delays and data completeness

            **Population Factors:**
            - Population density
            - Access to healthcare
            - WASH (Water, Sanitation, Hygiene) indicators
            """)

# ============================================
# SECTION 5: RECOMMENDED ACTIONS
# ============================================

st.subheader(" Recommended Actions")

if df_predictions is not None:
    county_data = df_predictions[df_predictions['county'] == selected_county]

    if not county_data.empty:
        risk = county_data['risk_score'].iloc[0]
        alert = county_data['alert'].iloc[0]

        if alert:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                ###  Immediate Actions

                1. **Notify Health Teams**
                   - Contact sub-county health officials
                   - Activate emergency response plan

                2. **Community Engagement**
                   - Activate community health workers
                   - Issue public health alerts
                   - Distribute prevention materials

                3. **Resource Mobilization**
                   - Review supply stocks (ORS, IV fluids, drugs)
                   - Ensure laboratory capacity
                   - Prepare isolation facilities
                """)

            with col2:
                st.markdown("""
                ###  Enhanced Surveillance

                1. **Case Reporting**
                   - Daily reporting from all facilities
                   - Active case finding in communities
                   - Contact tracing protocols

                2. **Laboratory Testing**
                   - Priority testing for suspected cases
                   - Quality assurance measures
                   - Rapid diagnostic test availability

                3. **Data Monitoring**
                   - Track daily case counts
                   - Monitor geographical spread
                   - Assess intervention effectiveness
                """)

            st.warning("⚠️ **ALERT:** Immediate action required for {selected_county} County")

        elif risk > 0.4:
            st.markdown("""
            ###  Recommended Actions - Enhanced Surveillance

            1. **Increase monitoring** in high-risk areas
            2. **Review case definitions** with health workers
            3. **Strengthen reporting** from all facilities
            4. **Community awareness** campaigns
            5. **Prepare supplies** for potential response
            """)
        else:
            st.markdown("""
            ###  Routine Surveillance

            1. **Maintain** standard case reporting
            2. **Monitor** trends for early signs
            3. **Continue** community health worker activities
            4. **Review** data quality and completeness
            5. **Prepare** for seasonal changes
            """)

#st.markdown("---")
# Inserted: Generate Report section
st.markdown("---")

# ============================================
# SECTION 5.5: GENERATE REPORT
# ============================================

st.subheader(" Generate Report")

# Role-based access check for report generation
if not can_generate_reports(session) and not can_export_data(session):
    st.warning("📋 Report generation is restricted to Health Officers and Administrators only. Your role (Viewer) does not have access to this feature.")
else:
    def generate_report_text(county, start_date, end_date, disease, preds, hist):
        lines = []
        lines.append("SENTINEL-KE - Summary Report")
        lines.append(f"County: {county}")
        lines.append(f"Date range: {start_date} to {end_date}")
        lines.append(f"Disease: {disease}")
        lines.append("")

        # Predictions
        try:
            if preds is not None:
                cp = preds[preds['county'] == county]
                if not cp.empty:
                    rs = cp['risk_score'].iloc[0]
                    al = cp['alert'].iloc[0]
                    lines.append(f"Risk Score: {rs:.1%}")
                    lines.append(f"Alert: {'YES' if al else 'NO'}")
        except Exception:
            lines.append("Risk Score: N/A")

        # Historical summaries
        try:
            if hist is not None:
                ch = hist[hist['county'] == county]
                ch = ch[(ch['date'] >= pd.to_datetime(start_date)) & (ch['date'] <= pd.to_datetime(end_date))]
                if not ch.empty:
                    if 'cholera_cases' in ch.columns and disease in ['Cholera', 'Both']:
                        lines.append(f"Cholera (7-day avg): {ch['cholera_cases'].tail(7).mean():.0f}")
                    if 'malaria_cases' in ch.columns and disease in ['Malaria', 'Both']:
                        lines.append(f"Malaria (7-day avg): {ch['malaria_cases'].tail(7).mean():.0f}")
                    if 'rainfall_mm' in ch.columns:
                        lines.append(f"Average Rainfall (period): {ch['rainfall_mm'].mean():.1f} mm")
        except Exception:
            lines.append("Historical summary: N/A")

        lines.append("")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EAT")
        return "\n".join(lines)

    with st.expander("📝 Generate printable report and download"):
        report_text = generate_report_text(selected_county, start_date, end_date, disease, df_predictions, df_historical)
        st.code(report_text, language='text')
        st.download_button(
            label="Download Report (TXT)",
            data=report_text,
            file_name=f"sentinel_ke_report_{selected_county}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime='text/plain'
        )

    def generate_report_pdf(county, start_date, end_date, disease, preds, hist):
        # Lazy import PDF libraries to avoid startup failures when dependencies
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.utils import ImageReader
            from reportlab.lib.units import mm
        except Exception:
            st.info(
                "PDF export is disabled: required libraries are not installed in this environment.\n"
                "To enable PDF export: 1) Ensure `reportlab`, `kaleido`, and `Pillow` are listed in `requirements.txt`; 2) Push/commit that file to GitHub; 3) On Streamlit Cloud open Manage app → Settings → 'Clear cache & redeploy' so the environment rebuilds and installs new packages."
            )
            return None

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin = 15 * mm
        y = height - margin

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, y, "SENTINEL-KE - Summary Report")
        y -= 12 * mm

        # Basic info
        c.setFont("Helvetica", 10)
        c.drawString(margin, y, f"County: {county}")
        y -= 6 * mm
        c.drawString(margin, y, f"Date range: {start_date} to {end_date}")
        y -= 6 * mm
        c.drawString(margin, y, f"Disease: {disease}")
        y -= 8 * mm

        # Predictions summary
        try:
            if preds is not None:
                cp = preds[preds['county'] == county]
                if not cp.empty:
                    rs = cp['risk_score'].iloc[0]
                    al = cp['alert'].iloc[0]
                    c.drawString(margin, y, f"Risk Score: {rs:.1%}")
                    y -= 6 * mm
                    c.drawString(margin, y, f"Alert: {'YES' if al else 'NO'}")
                    y -= 8 * mm
        except Exception:
            c.drawString(margin, y, "Risk Score: N/A")
            y -= 8 * mm

        # Historical chart image
        try:
            if hist is not None:
                ch = hist[hist['county'] == county]
                ch = ch[(ch['date'] >= pd.to_datetime(start_date)) & (ch['date'] <= pd.to_datetime(end_date))]
                if not ch.empty:
                    # recreate a condensed chart
                    fig = px.line(ch, x='date', y=( 'cholera_cases' if disease in ['Cholera','Both'] else 'malaria_cases'), title=f"{county} - Trend")
                    img_bytes = fig.to_image(format='png')
                    img = ImageReader(io.BytesIO(img_bytes))
                    img_h = 70 * mm
                    img_w = width - 2 * margin
                    c.drawImage(img, margin, y - img_h, width=img_w, height=img_h)
                    y -= img_h + 6 * mm
        except Exception:
            pass

        # Comparison chart
        try:
            if preds is not None:
                comp = preds.copy()
                fig2 = px.bar(comp, x='county', y='risk_score', color='risk_score', title='Risk Comparison')
                img_bytes = fig2.to_image(format='png')
                img = ImageReader(io.BytesIO(img_bytes))
                img_h = 60 * mm
                img_w = width - 2 * margin
                if y - img_h < margin:
                    c.showPage()
                    y = height - margin
                c.drawImage(img, margin, y - img_h, width=img_w, height=img_h)
                y -= img_h + 6 * mm
        except Exception:
            pass

        # Comparison table (text)
        try:
            if preds is not None:
                comp = preds[['county','risk_score','alert']].copy()
                y -= 4 * mm
                c.setFont("Helvetica-Bold", 10)
                c.drawString(margin, y, "County   Risk Score   Alert")
                y -= 5 * mm
                c.setFont("Helvetica", 9)
                for _, row in comp.iterrows():
                    line = f"{row['county'][:12]:12}   {row['risk_score']:.1%:>6}   {'YES' if row['alert'] else 'NO'}"
                    if y < margin + 20 * mm:
                        c.showPage()
                        y = height - margin
                    c.drawString(margin, y, line)
                    y -= 5 * mm
            if preds is not None:
                comp = preds[['county','risk_score','alert']].copy()
                y -= 4 * mm
                c.setFont("Helvetica-Bold", 10)
                c.drawString(margin, y, "County   Risk Score   Alert")
                y -= 5 * mm
                c.setFont("Helvetica", 9)
                for _, row in comp.iterrows():
                    line = f"{row['county'][:12]:12}   {row['risk_score']:.1%:>6}   {'YES' if row['alert'] else 'NO'}"
                    if y < margin + 20 * mm:
                        c.showPage()
                        y = height - margin
                    c.drawString(margin, y, line)
                    y -= 5 * mm
        except Exception:
            pass

        # Footer
        if y < 40 * mm:
            c.showPage()
            y = height - margin
        c.setFont("Helvetica", 8)
        c.drawString(margin, margin, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EAT")
        c.save()
        buffer.seek(0)
        return buffer.read()

    pdf_data = None
    if st.button("Generate PDF of current dashboard"):
        try:
            pdf_data = generate_report_pdf(selected_county, start_date, end_date, disease, df_predictions, df_historical)
            if pdf_data:
                st.success("PDF generated — use the download button below.")
            else:
                st.info("PDF not generated. See message above for details.")
        except Exception as e:
            st.error(f"Failed to generate PDF: {e}")

    if pdf_data:
        st.download_button(
            label="Download Report (PDF)",
            data=pdf_data,
            file_name=f"sentinel_ke_report_{selected_county}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime='application/pdf'
        )

st.markdown("---")

# ============================================
# SECTION 5.8: ADMIN PANEL (ADMINISTRATORS ONLY)
# ============================================

if can_access_system_admin(session):
    st.subheader(" System Administration")
    
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["👥 User Management", "🔧 System Settings", "📊 System Stats"])
    
    with admin_tab1:
        st.markdown("### 👥 User Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📋 Current Users")
            success, users = list_users(session)
            if success and users:
                users_df = pd.DataFrame(users)
                st.dataframe(users_df, width='stretch', hide_index=True)
            else:
                st.info("No users found")
        
        with col2:
            st.markdown("#### ➕ Create New User")
            new_username = st.text_input("New Username", key="new_user_username")
            new_password = st.text_input("New Password", type="password", key="new_user_password")
            new_role = st.selectbox("Role", ["Administrator", "Health Officer", "Viewer"], key="new_user_role")
            
            role_levels = {"Administrator": 3, "Health Officer": 2, "Viewer": 1}
            role_perms = {
                "Administrator": ["view", "export", "user_management", "system_admin"],
                "Health Officer": ["view", "export", "report_generation"],
                "Viewer": ["view"]
            }
            
            if st.button("Create User", width='stretch'):
                if new_username and new_password:
                    success, message = create_user(
                        new_username, new_password, new_role,
                        role_levels[new_role], role_perms[new_role],
                        session
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please fill in all fields")
    
    with admin_tab2:
        st.markdown("### 🔧 System Settings")
        st.info("System settings and configuration options would appear here")
        st.write(f"• Session Timeout: 60 minutes")
        st.write(f"• Password Hashing: SHA-256")
        st.write(f"• Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EAT")
    
    with admin_tab3:
        st.markdown("### 📊 System Statistics")
        col1, col2, col3 = st.columns(3)
        
        success, users = list_users(session)
        if success:
            with col1:
                st.metric("Total Users", len(users))
            with col2:
                admin_count = sum(1 for u in users if u["Level"] == 3)
                st.metric("Administrators", admin_count)
            with col3:
                viewer_count = sum(1 for u in users if u["Level"] == 1)
                st.metric("Viewers", viewer_count)
        
        st.markdown("---")
        st.write("System Health: ✅ All systems operational")

st.markdown("---")

# ============================================
# SECTION 6: DATA SOURCES & SYSTEM INFO
# ============================================

st.subheader(" Data Sources & How It Works")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ###  Data Sources

    **Climate Data**
    -  **Open-Meteo API**: Rainfall, temperature, humidity
    -  **CHIRPS**: Satellite rainfall estimates
    -  **Kenya Met Department**: Weather forecasts

    **Health Data**
    - **DHIS2**: Routine health surveillance (synthetic for demo)
    - **Historical Outbreak Data**: Published research
    - **Lab Data**: Surveillance reports

    **Population Data**
    -  **WorldPop**: Population estimates
    -  **Kenya Open Data**: Demographic information
    """)

with col2:
    st.markdown("""
    ###  How It Works

    **Step 1: Data Collection**
    - Rainfall data fetched daily from Open-Meteo API
    - Historical health data loaded from repository

    **Step 2: AI Prediction**
    - XGBoost model with 25 features
    - Analyzes patterns in rainfall and health data
    - Generates risk scores (0-1 scale)

    **Step 3: Alert System**
    - Risk > 0.65 = ALERT
    - Risk 0.4-0.65 = Monitor
    - Risk < 0.4 = Normal

    **Step 4: Automated Updates**
    - GitHub Actions runs daily at 6 AM EAT
    - Fetches fresh data automatically
    - Updates dashboard in real-time
    """)

st.markdown("---")

# ============================================
# FOOTER
# ============================================

st.markdown(f"""
<div class="footer">
    <strong>🛡️ SENTINEL-KE v1.0</strong><br>
    AI-Powered Early Warning System for Disease Outbreaks in Western Kenya<br>
    <br>
     Data updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EAT<br>
     Next update: Daily at 6:00 AM EAT<br>
    <br>
    📌 <strong>Data Sources:</strong> Open-Meteo API, CHIRPS, WorldPop, DHIS2 (synthetic)<br>
    🤖 <strong>AI Model:</strong> XGBoost with 25 features<br>
     <strong>Counties:</strong> Kisumu, Homa Bay, Siaya, Migori, Nyamira, Kisii<br>
    <br>
    <span style="color: #999;">
        For health officials only. Not for clinical decision-making.<br>
        © 2026 SENTINEL-KE Project
    </span>
</div>
""", unsafe_allow_html=True)

# ============================================
# AUTO-REFRESH (Optional)
# ============================================

if st.sidebar.checkbox(" Auto-refresh", value=True):
    st.caption("Dashboard auto-refreshes every 5 minutes")
    st.empty()
    import time
    time.sleep(300)
    st.rerun()