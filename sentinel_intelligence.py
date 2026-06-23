
import pandas as pd
import numpy as np
from datetime import datetime

# Import all modules
from remote_sensing import RemoteSensingModule
from wash_intelligence import WASHModule
from data_quality import DataQualityModule
from mobility_intelligence import MobilityModule
from health_capacity import HealthCapacityModule

class SentinelKEIntelligence:
    """
    Master intelligence module combining all 5 domains
    """
    
    def __init__(self):
        self.remote_sensing = RemoteSensingModule()
        self.wash = WASHModule()
        self.data_quality = DataQualityModule()
        self.mobility = MobilityModule()
        self.health_capacity = HealthCapacityModule()
        self.counties = ['Kisumu', 'Homa Bay', 'Siaya', 'Migori', 'Nyamira', 'Kisii']
    
    def get_comprehensive_risk(self, county, date=None):
        """Get risk assessment from all domains"""
        if date is None:
            date = datetime.now()
        
        # Get data from each domain
        ndvi_data = self.remote_sensing.get_malaria_risk_factor(county, date)
        wash_data = self.wash.get_wash_risk_score(county)
        quality_data = self.data_quality.get_reporting_quality(county)
        mobility_data = self.mobility.get_mobility_risk(county)
        capacity_data = self.health_capacity.get_capacity_metrics(county)
        
        # Calculate weighted risk
        weights = {
            'wash_risk': 0.25,
            'environmental_risk': 0.25,
            'mobility_risk': 0.20,
            'data_quality': 0.15,
            'capacity_risk': 0.15
        }
        
        # Base risk from environmental data
        environmental_risk = ndvi_data['combined_risk'] if ndvi_data else 0.3
        wash_risk = wash_data['wash_risk_score'] if wash_data else 0.3
        mobility_risk = mobility_data['mobility_risk_score'] if mobility_data else 0.3
        
        # Data quality affects confidence
        confidence_adj = quality_data['quality_score'] if quality_data else 0.7
        
        # Capacity affects risk (low capacity = higher risk)
        capacity_risk = (1 - capacity_data['response_readiness']) if capacity_data else 0.3
        
        # Weighted combination
        combined_risk = (
            wash_risk * weights['wash_risk'] +
            environmental_risk * weights['environmental_risk'] +
            mobility_risk * weights['mobility_risk'] +
            capacity_risk * weights['capacity_risk']
        ) * confidence_adj
        
        combined_risk = min(0.95, max(0.05, combined_risk))
        
        return {
            'county': county,
            'date': date.strftime('%Y-%m-%d'),
            'combined_risk': round(combined_risk, 3),
            'environmental_risk': round(environmental_risk, 3),
            'wash_risk': round(wash_risk, 3),
            'mobility_risk': round(mobility_risk, 3),
            'capacity_risk': round(capacity_risk, 3),
            'confidence': round(confidence_adj, 3),
            'alert': combined_risk > 0.65,
            'recommended_action': self._get_recommendation(combined_risk, county)
        }
    
    def _get_recommendation(self, risk, county):
        """Get specific recommendations based on risk level"""
        if risk > 0.8:
            return f"CRITICAL: Immediate action required in {county}"
        elif risk > 0.65:
            return f"HIGH ALERT: Enhanced surveillance needed in {county}"
        elif risk > 0.4:
            return f"MODERATE RISK: Monitor {county} closely"
        else:
            return f"LOW RISK: Routine surveillance in {county}"
    
    def get_county_summary(self, county):
        """Get a comprehensive summary for a county"""
        risk_data = self.get_comprehensive_risk(county)
        
        if risk_data:
            return {
                'county': county,
                'risk_level': 'CRITICAL' if risk_data['combined_risk'] > 0.8 else 'HIGH' if risk_data['combined_risk'] > 0.65 else 'MODERATE' if risk_data['combined_risk'] > 0.4 else 'LOW',
                'risk_score': f"{risk_data['combined_risk']:.1%}",
                'confidence': f"{risk_data['confidence']:.1%}",
                'alert': '🚨' if risk_data['alert'] else '✅',
                'recommendation': risk_data['recommended_action']
            }
        return None

# Test the integration
if __name__ == "__main__":
    print("🛡️  SENTINEL-KE COMPREHENSIVE INTELLIGENCE")
    print("=" * 70)
    
    sentinel = SentinelKEIntelligence()
    today = datetime.now()
    
    # Get comprehensive risk for all counties
    results = []
    for county in sentinel.counties:
        data = sentinel.get_comprehensive_risk(county, today)
        summary = sentinel.get_county_summary(county)
        if summary:
            results.append(summary)
    
    # Display results
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    
    # Show domain breakdown for first county
    print("\n" + "=" * 70)
    print("DOMAIN BREAKDOWN - KISUMU")
    print("=" * 70)
    
    kisumu_data = sentinel.get_comprehensive_risk('Kisumu', today)
    print(f"Combined Risk: {kisumu_data['combined_risk']:.1%}")
    print(f"  - Environmental (NDVI, LST): {kisumu_data['environmental_risk']:.1%}")
    print(f"  - WASH (Water/Sanitation): {kisumu_data['wash_risk']:.1%}")
    print(f"  - Mobility (People Movement): {kisumu_data['mobility_risk']:.1%}")
    print(f"  - Capacity (Health System): {kisumu_data['capacity_risk']:.1%}")
    print(f"Data Confidence: {kisumu_data['confidence']:.1%}")
    print(f"Alert: {'🚨' if kisumu_data['alert'] else '✅'}")
    print(f"Recommendation: {kisumu_data['recommended_action']}")
