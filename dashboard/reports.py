"""
SENTINEL-KE Report Generation Module
Generates PDF reports for outbreak risk assessment and analysis.
"""

import pandas as pd
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import numpy as np

# ============================================
# UTILITY FUNCTIONS
# ============================================

def create_header_table(title, subtitle, user_role):
    """Create a styled header table for the report."""
    header_data = [
        ["🛡️ SENTINEL-KE", f"User Role: {user_role}"],
        [title, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
        [subtitle, ""]
    ]
    
    header_table = Table(header_data, colWidths=[3.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E88E5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    return header_table

def get_risk_color_name(risk_score):
    """Get risk level name based on score."""
    if risk_score > 0.7:
        return "🚨 CRITICAL", "HIGH RISK"
    elif risk_score > 0.4:
        return "⚠️ MODERATE", "MODERATE RISK"
    else:
        return "✅ LOW", "LOW RISK"

def format_percentage(value):
    """Format a value as percentage string."""
    if isinstance(value, (int, float)):
        return f"{value:.1%}"
    return str(value)

# ============================================
# COMPREHENSIVE RISK ASSESSMENT REPORT
# ============================================

def generate_outbreak_risk_report(df_predictions, df_historical, selected_county, 
                                  user_role, alert_threshold=0.65):
    """
    Generate a comprehensive outbreak risk assessment report.
    
    Args:
        df_predictions: DataFrame with current risk predictions
        df_historical: DataFrame with historical trend data
        selected_county: County name to report on
        user_role: User role for the report header
        alert_threshold: Risk score threshold for alerts
    
    Returns:
        BytesIO object containing the PDF
    """
    
    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1E88E5'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1E88E5'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )
    
    # Header
    elements.append(create_header_table(
        f"Outbreak Risk Assessment Report - {selected_county}",
        "Comprehensive Risk Analysis & Recommendations",
        user_role
    ))
    elements.append(Spacer(1, 0.3*inch))
    
    # Get county data
    county_data = df_predictions[df_predictions['county'] == selected_county]
    
    if county_data.empty:
        buffer.seek(0)
        return buffer
    
    # Extract data
    risk_score = county_data['risk_score'].iloc[0]
    alert_status = county_data['alert'].iloc[0]
    risk_emoji, risk_level = get_risk_color_name(risk_score)
    
    # ============================================
    # SECTION 1: EXECUTIVE SUMMARY
    # ============================================
    
    elements.append(Paragraph(f"📋 Executive Summary", section_style))
    
    summary_data = [
        ["Metric", "Value", "Status"],
        ["Risk Score", format_percentage(risk_score), risk_emoji],
        ["Alert Status", "🚨 ALERT" if alert_status else "✅ NORMAL", "Active" if alert_status else "Normal"],
        ["Assessment Date", datetime.now().strftime("%Y-%m-%d"), "Current"],
        ["Risk Level", risk_level, "Classified"],
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E88E5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # ============================================
    # SECTION 2: DOMAIN BREAKDOWN
    # ============================================
    
    domain_columns = ['rainfall_risk', 'environmental_risk', 'wash_risk', 'mobility_risk', 'capacity_risk', 'data_quality_score']
    has_domains = all(col in df_predictions.columns for col in domain_columns)
    
    if has_domains:
        elements.append(Paragraph(f"📊 Multi-Domain Risk Breakdown", section_style))
        
        domain_data = [
            ["Domain", "Risk Score", "Assessment"],
            ["🌧️ Rainfall Risk", format_percentage(county_data['rainfall_risk'].iloc[0]), 
             "High" if county_data['rainfall_risk'].iloc[0] > 0.5 else "Moderate" if county_data['rainfall_risk'].iloc[0] > 0.3 else "Low"],
            ["🌿 Environmental Risk (NDVI)", format_percentage(county_data['environmental_risk'].iloc[0]), 
             "High" if county_data['environmental_risk'].iloc[0] > 0.5 else "Moderate" if county_data['environmental_risk'].iloc[0] > 0.3 else "Low"],
            ["💧 WASH Risk", format_percentage(county_data['wash_risk'].iloc[0]), 
             "High" if county_data['wash_risk'].iloc[0] > 0.5 else "Moderate" if county_data['wash_risk'].iloc[0] > 0.3 else "Low"],
            ["🚶 Mobility Risk", format_percentage(county_data['mobility_risk'].iloc[0]), 
             "High" if county_data['mobility_risk'].iloc[0] > 0.5 else "Moderate" if county_data['mobility_risk'].iloc[0] > 0.3 else "Low"],
            ["🏥 Health Capacity Risk", format_percentage(county_data['capacity_risk'].iloc[0]), 
             "High" if county_data['capacity_risk'].iloc[0] > 0.5 else "Moderate" if county_data['capacity_risk'].iloc[0] > 0.3 else "Low"],
            ["📊 Data Quality", format_percentage(county_data['data_quality_score'].iloc[0]), 
             "Excellent" if county_data['data_quality_score'].iloc[0] > 0.8 else "Good" if county_data['data_quality_score'].iloc[0] > 0.6 else "Fair"],
        ]
        
        domain_table = Table(domain_data, colWidths=[2.2*inch, 1.8*inch, 2*inch])
        domain_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E88E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F8F8')]),
        ]))
        
        elements.append(domain_table)
        elements.append(Spacer(1, 0.2*inch))
    
    # ============================================
    # SECTION 3: RISK ANALYSIS
    # ============================================
    
    elements.append(Paragraph(f"🔍 Risk Analysis & Contributing Factors", section_style))
    
    analysis_text = ""
    if alert_status:
        analysis_text = f"""
        <b>ALERT STATUS: {risk_emoji} CRITICAL</b><br/>
        The AI model has detected a CRITICAL RISK of disease outbreak in {selected_county} County.
        Immediate action is required to prevent spread.
        """
    elif risk_score > 0.4:
        analysis_text = f"""
        <b>STATUS: ⚠️ MODERATE RISK</b><br/>
        The AI model has detected moderate risk conditions in {selected_county} County.
        Enhanced surveillance and preparedness are recommended.
        """
    else:
        analysis_text = f"""
        <b>STATUS: ✅ LOW RISK</b><br/>
        Current conditions in {selected_county} County show low outbreak risk.
        Routine surveillance protocols should continue.
        """
    
    if has_domains:
        analysis_text += "<br/><br/><b>Key Contributing Factors:</b><br/>"
        if county_data['rainfall_risk'].iloc[0] > 0.5:
            analysis_text += "• High rainfall levels increase waterborne disease risk<br/>"
        if county_data['environmental_risk'].iloc[0] > 0.5:
            analysis_text += "• Environmental conditions favorable for mosquito breeding<br/>"
        if county_data['wash_risk'].iloc[0] > 0.5:
            analysis_text += "• WASH infrastructure challenges present<br/>"
        if county_data['mobility_risk'].iloc[0] > 0.5:
            analysis_text += "• High human mobility may accelerate disease spread<br/>"
        if county_data['capacity_risk'].iloc[0] > 0.5:
            analysis_text += "• Health system capacity constraints identified<br/>"
        if county_data['data_quality_score'].iloc[0] < 0.6:
            analysis_text += "• Data quality is below optimal levels<br/>"
    
    elements.append(Paragraph(analysis_text, styles['BodyText']))
    elements.append(Spacer(1, 0.2*inch))
    
    # ============================================
    # SECTION 4: HISTORICAL TRENDS
    # ============================================
    
    if df_historical is not None:
        county_hist = df_historical[df_historical['county'] == selected_county]
        
        if not county_hist.empty:
            elements.append(Paragraph(f"📈 Historical Trends (Last 30 Days)", section_style))
            
            recent_data = county_hist.tail(30)
            
            trends_data = [
                ["Metric", "Current (7-day avg)", "Previous (7-day avg)", "Trend"],
                ["Cholera Cases", 
                 f"{recent_data['cholera_cases'].tail(7).mean():.0f}",
                 f"{recent_data['cholera_cases'].iloc[:-7].tail(7).mean():.0f}",
                 "📈 Rising" if recent_data['cholera_cases'].tail(7).mean() > recent_data['cholera_cases'].iloc[:-7].tail(7).mean() else "📉 Falling"],
                ["Malaria Cases", 
                 f"{recent_data['malaria_cases'].tail(7).mean():.0f}",
                 f"{recent_data['malaria_cases'].iloc[:-7].tail(7).mean():.0f}",
                 "📈 Rising" if recent_data['malaria_cases'].tail(7).mean() > recent_data['malaria_cases'].iloc[:-7].tail(7).mean() else "📉 Falling"],
                ["Rainfall (mm)", 
                 f"{recent_data['rainfall_mm'].tail(7).mean():.1f}",
                 f"{recent_data['rainfall_mm'].iloc[:-7].tail(7).mean():.1f}",
                 "📈 Increasing" if recent_data['rainfall_mm'].tail(7).mean() > recent_data['rainfall_mm'].iloc[:-7].tail(7).mean() else "📉 Decreasing"],
            ]
            
            trends_table = Table(trends_data, colWidths=[1.8*inch, 1.7*inch, 1.7*inch, 1.8*inch])
            trends_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E88E5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F8F8')]),
            ]))
            
            elements.append(trends_table)
            elements.append(Spacer(1, 0.2*inch))
    
    # ============================================
    # SECTION 5: RECOMMENDED ACTIONS
    # ============================================
    
    elements.append(Paragraph(f"📋 Recommended Actions", section_style))
    
    actions_text = ""
    if alert_status:
        actions_text = """
        <b>IMMEDIATE ACTIONS (Critical Priority):</b><br/>
        • Activate emergency response protocols<br/>
        • Notify all health facilities immediately<br/>
        • Mobilize rapid response teams<br/>
        • Increase case investigation and confirmation<br/>
        • Implement community alert and sensitization<br/>
        • Enhance surveillance in border areas<br/>
        • Prepare supplies and equipment stockpiles<br/>
        """
    elif risk_score > 0.4:
        actions_text = """
        <b>ENHANCED SURVEILLANCE (Medium Priority):</b><br/>
        • Increase case reporting frequency to daily<br/>
        • Deploy additional surveillance teams to high-risk areas<br/>
        • Conduct awareness campaigns in affected areas<br/>
        • Pre-position response supplies and equipment<br/>
        • Strengthen laboratory testing capacity<br/>
        • Establish inter-facility communication protocols<br/>
        • Monitor neighboring counties for early warning signs<br/>
        """
    else:
        actions_text = """
        <b>ROUTINE SURVEILLANCE (Standard Priority):</b><br/>
        • Continue standard case reporting protocols<br/>
        • Maintain regular facility inspections<br/>
        • Conduct routine community awareness activities<br/>
        • Monitor data quality and completeness<br/>
        • Prepare contingency response plans<br/>
        • Train health workers on early detection<br/>
        • Build community health worker capacity<br/>
        """
    
    elements.append(Paragraph(actions_text, styles['BodyText']))
    elements.append(Spacer(1, 0.2*inch))
    
    # ============================================
    # SECTION 6: MODEL INFORMATION
    # ============================================
    
    elements.append(Paragraph(f"🤖 AI Model Information", section_style))
    
    model_text = f"""
    <b>Model Details:</b><br/>
    • Type: XGBoost Gradient Boosting<br/>
    • Features: 25 epidemiological and environmental variables<br/>
    • Training Data: Historical disease and environmental data<br/>
    • Accuracy: Cross-validated on held-out test set<br/>
    • Data Quality Score: {format_percentage(county_data['data_quality_score'].iloc[0])}<br/>
    • Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
    <br/>
    <b>Data Sources:</b><br/>
    • Rainfall: Open-Meteo API<br/>
    • Environmental: CHIRPS satellite data<br/>
    • Population: WorldPop estimates<br/>
    • Health: County-level surveillance reports<br/>
    """
    
    elements.append(Paragraph(model_text, styles['BodyText']))
    elements.append(Spacer(1, 0.2*inch))
    
    # ============================================
    # FOOTER
    # ============================================
    
    footer_text = f"""
    <b>Report Disclaimer:</b><br/>
    This report is generated by the SENTINEL-KE AI system and is intended for health officials and public health planners only. 
    It should not be used for individual clinical decision-making. The predictions are based on environmental and epidemiological 
    data and should be used in conjunction with case investigation and laboratory confirmation. For questions or to report issues, 
    contact the SENTINEL-KE project team.<br/>
    <br/>
    Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | User Role: {user_role}
    """
    
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer


# ============================================
# QUICK SUMMARY REPORT
# ============================================

def generate_summary_report(df_predictions, selected_county, user_role):
    """
    Generate a quick one-page summary report.
    
    Args:
        df_predictions: DataFrame with current risk predictions
        selected_county: County name to report on
        user_role: User role for the report header
    
    Returns:
        BytesIO object containing the PDF
    """
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1E88E5'),
        spaceAfter=6,
        spaceBefore=6,
        fontName='Helvetica-Bold'
    )
    
    # Header
    elements.append(create_header_table(
        f"Quick Risk Summary - {selected_county}",
        "One-Page Overview",
        user_role
    ))
    elements.append(Spacer(1, 0.2*inch))
    
    # Get data
    county_data = df_predictions[df_predictions['county'] == selected_county]
    if county_data.empty:
        buffer.seek(0)
        return buffer
    
    risk_score = county_data['risk_score'].iloc[0]
    alert_status = county_data['alert'].iloc[0]
    risk_emoji, risk_level = get_risk_color_name(risk_score)
    
    # Quick Stats
    elements.append(Paragraph(f"Quick Assessment", section_style))
    
    quick_data = [
        ["Risk Score", format_percentage(risk_score), ""],
        ["Status", "🚨 ALERT" if alert_status else "✅ NORMAL", ""],
        ["Date", datetime.now().strftime("%Y-%m-%d"), ""],
    ]
    
    quick_table = Table(quick_data, colWidths=[2*inch, 2*inch, 2*inch])
    quick_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E88E5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(quick_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Recommendation
    elements.append(Paragraph(f"Recommendation", section_style))
    
    if alert_status:
        recommendation = "🚨 <b>CRITICAL:</b> Immediate action required. Activate emergency response protocols."
    elif risk_score > 0.4:
        recommendation = "⚠️ <b>MODERATE:</b> Enhanced surveillance recommended. Prepare response resources."
    else:
        recommendation = "✅ <b>LOW RISK:</b> Continue routine surveillance. Monitor for changes."
    
    elements.append(Paragraph(recommendation, styles['BodyText']))
    elements.append(Spacer(1, 0.15*inch))
    
    # Key Factors
    elements.append(Paragraph(f"Key Risk Factors", section_style))
    
    domain_columns = ['rainfall_risk', 'environmental_risk', 'wash_risk', 'mobility_risk', 'capacity_risk']
    factors_text = "<br/>".join([
        f"• {name}: {format_percentage(county_data[col].iloc[0])}"
        for col, name in zip(domain_columns, ["Rainfall", "Environmental", "WASH", "Mobility", "Capacity"])
        if col in county_data.columns
    ])
    
    elements.append(Paragraph(factors_text, styles['BodyText']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ============================================
# COMPARATIVE REPORT
# ============================================

def generate_comparative_report(df_predictions, user_role):
    """
    Generate a report comparing all counties.
    
    Args:
        df_predictions: DataFrame with current risk predictions
        user_role: User role for the report header
    
    Returns:
        BytesIO object containing the PDF
    """
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1E88E5'),
        spaceAfter=6,
        spaceBefore=6,
        fontName='Helvetica-Bold'
    )
    
    # Header
    elements.append(create_header_table(
        f"County Comparison Report",
        "Risk Assessment Across All Counties",
        user_role
    ))
    elements.append(Spacer(1, 0.2*inch))
    
    # All counties data
    elements.append(Paragraph(f"County Risk Comparison", section_style))
    
    comparison_data = [["County", "Risk Score", "Status", "Rainfall Risk", "WASH Risk", "Capacity Risk"]]
    
    for _, row in df_predictions.iterrows():
        comparison_data.append([
            row['county'],
            format_percentage(row['risk_score']),
            "🚨 ALERT" if row['alert'] else "✅ OK",
            format_percentage(row.get('rainfall_risk', 0)),
            format_percentage(row.get('wash_risk', 0)),
            format_percentage(row.get('capacity_risk', 0)),
        ])
    
    comparison_table = Table(comparison_data, colWidths=[1.3*inch, 1.2*inch, 1*inch, 1.3*inch, 1.3*inch, 1.3*inch])
    comparison_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E88E5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F8F8')]),
    ]))
    
    elements.append(comparison_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
