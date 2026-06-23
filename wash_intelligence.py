
import pandas as pd
import numpy as np

# ============================================
# WASH DATA MODULE
# ============================================

class WASHModule:
    """Water, Sanitation, and Hygiene intelligence for disease prediction"""
    
    def __init__(self):
        # County-level WASH indicators (based on Kenya data)
        # In production, fetch from Kenya Open Data or HDX
        self.wash_data = {
            'Kisumu': {
                'safe_water_access': 0.62,      # 62% have access
                'improved_sanitation': 0.55,    # 55% have improved sanitation
                'open_defecation': 0.18,        # 18% practice open defecation
                'water_treatment': 0.35,        # 35% treat water
                'cholera_risk': 'high'
            },
            'Homa Bay': {
                'safe_water_access': 0.58,
                'improved_sanitation': 0.48,
                'open_defecation': 0.22,
                'water_treatment': 0.30,
                'cholera_risk': 'high'
            },
            'Siaya': {
                'safe_water_access': 0.55,
                'improved_sanitation': 0.45,
                'open_defecation': 0.25,
                'water_treatment': 0.28,
                'cholera_risk': 'medium'
            },
            'Migori': {
                'safe_water_access': 0.60,
                'improved_sanitation': 0.50,
                'open_defecation': 0.20,
                'water_treatment': 0.32,
                'cholera_risk': 'medium'
            },
            'Nyamira': {
                'safe_water_access': 0.75,
                'improved_sanitation': 0.65,
                'open_defecation': 0.10,
                'water_treatment': 0.45,
                'cholera_risk': 'low'
            },
            'Kisii': {
                'safe_water_access': 0.72,
                'improved_sanitation': 0.62,
                'open_defecation': 0.12,
                'water_treatment': 0.42,
                'cholera_risk': 'low'
            }
        }
    
    def get_wash_risk_score(self, county):
        """Calculate WASH-based risk score for waterborne diseases"""
        data = self.wash_data.get(county)
        if not data:
            return None
        
        # Risk factors:
        # - Low safe water access = higher risk
        # - Low sanitation = higher risk
        # - High open defecation = higher risk
        # - Low water treatment = higher risk
        
        water_risk = 1 - data['safe_water_access']
        sanitation_risk = 1 - data['improved_sanitation']
        defecation_risk = data['open_defecation']
        treatment_risk = 1 - data['water_treatment']
        
        # Weighted combination
        risk_score = (
            water_risk * 0.35 +
            sanitation_risk * 0.30 +
            defecation_risk * 0.20 +
            treatment_risk * 0.15
        )
        
        return {
            'county': county,
            'safe_water_access': data['safe_water_access'],
            'improved_sanitation': data['improved_sanitation'],
            'open_defecation': data['open_defecation'],
            'water_treatment': data['water_treatment'],
            'wash_risk_score': round(risk_score, 3),
            'cholera_risk_level': data['cholera_risk']
        }
    
    def get_wash_explanation(self, county):
        """Get human-readable explanation of WASH risks"""
        data = self.get_wash_risk_score(county)
        if not data:
            return "No WASH data available"
        
        explanations = []
        if data['safe_water_access'] < 0.6:
            explanations.append(f"Only {data['safe_water_access']:.0%} have safe water access")
        if data['improved_sanitation'] < 0.5:
            explanations.append(f"Only {data['improved_sanitation']:.0%} have improved sanitation")
        if data['open_defecation'] > 0.2:
            explanations.append(f"{data['open_defecation']:.0%} practice open defecation")
        if data['water_treatment'] < 0.3:
            explanations.append(f"Only {data['water_treatment']:.0%} treat drinking water")
        
        if not explanations:
            return "Good WASH conditions - low risk"
        
        return " | ".join(explanations)

# Test
if __name__ == "__main__":
    wash = WASHModule()
    print("💧 WASH INTELLIGENCE")
    print("=" * 50)
    
    for county in ['Kisumu', 'Nyamira']:
        data = wash.get_wash_risk_score(county)
        explanation = wash.get_wash_explanation(county)
        print(f"\n{county}:")
        print(f"  WASH Risk Score: {data['wash_risk_score']:.1%}")
        print(f"  Cholera Risk Level: {data['cholera_risk_level'].upper()}")
        print(f"  Explanation: {explanation}")
