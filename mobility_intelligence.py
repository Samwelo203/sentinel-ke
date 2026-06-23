
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================
# MOBILITY MODULE
# ============================================

class MobilityModule:
    """
    Tracks human movement patterns that influence disease spread
    """
    
    def __init__(self):
        # Kenya border crossings and major transport routes
        self.border_crossings = {
            'Busia': {'county': 'Busia', 'daily_traffic': 5000, 'is_border': True},
            'Malaba': {'county': 'Busia', 'daily_traffic': 3000, 'is_border': True},
            'Isebania': {'county': 'Migori', 'daily_traffic': 2000, 'is_border': True},
            'Kisumu': {'county': 'Kisumu', 'daily_traffic': 15000, 'is_border': False}
        }
        
        # Population centers and movement patterns
        self.movement_patterns = {
            'Kisumu': {
                'incoming_traffic': 15000,
                'outgoing_traffic': 12000,
                'busy_markets': 3,
                'fishing_communities': 1,
                'mobility_risk': 0.75
            },
            'Homa Bay': {
                'incoming_traffic': 8000,
                'outgoing_traffic': 7000,
                'busy_markets': 2,
                'fishing_communities': 2,
                'mobility_risk': 0.70
            },
            'Siaya': {
                'incoming_traffic': 5000,
                'outgoing_traffic': 6000,
                'busy_markets': 2,
                'fishing_communities': 1,
                'mobility_risk': 0.55
            },
            'Migori': {
                'incoming_traffic': 7000,
                'outgoing_traffic': 6500,
                'busy_markets': 2,
                'fishing_communities': 0,
                'mobility_risk': 0.60,
                'has_border': True
            },
            'Nyamira': {
                'incoming_traffic': 3000,
                'outgoing_traffic': 4000,
                'busy_markets': 1,
                'fishing_communities': 0,
                'mobility_risk': 0.30
            },
            'Kisii': {
                'incoming_traffic': 4000,
                'outgoing_traffic': 5000,
                'busy_markets': 2,
                'fishing_communities': 0,
                'mobility_risk': 0.40
            }
        }
    
    def get_mobility_risk(self, county):
        """Calculate disease spread risk based on mobility patterns"""
        pattern = self.movement_patterns.get(county)
        if not pattern:
            return None
        
        # Calculate risk factors
        traffic_risk = (pattern['incoming_traffic'] + pattern['outgoing_traffic']) / 30000
        traffic_risk = min(1, traffic_risk)
        
        market_risk = pattern['busy_markets'] / 5
        fishing_risk = pattern['fishing_communities'] / 3
        
        # Border crossing adds significant risk
        border_risk = 1.3 if pattern.get('has_border', False) else 1.0
        
        # Combined risk
        mobility_risk = (
            traffic_risk * 0.4 +
            market_risk * 0.3 +
            fishing_risk * 0.2
        ) * border_risk
        
        mobility_risk = min(1, max(0, mobility_risk))
        
        return {
            'county': county,
            'daily_incoming': pattern['incoming_traffic'],
            'daily_outgoing': pattern['outgoing_traffic'],
            'busy_markets': pattern['busy_markets'],
            'fishing_communities': pattern['fishing_communities'],
            'has_border': pattern.get('has_border', False),
            'mobility_risk_score': round(mobility_risk, 3),
            'spread_potential': 'HIGH' if mobility_risk > 0.6 else 'MEDIUM' if mobility_risk > 0.3 else 'LOW'
        }
    
    def get_mobility_explanation(self, county):
        """Human-readable explanation of mobility risks"""
        data = self.get_mobility_risk(county)
        if not data:
            return "No mobility data available"
        
        explanations = []
        if data['daily_incoming'] > 10000:
            explanations.append(f"High incoming traffic ({data['daily_incoming']:,} daily)")
        elif data['daily_incoming'] > 5000:
            explanations.append(f"Moderate incoming traffic ({data['daily_incoming']:,} daily)")
        
        if data['busy_markets'] > 2:
            explanations.append(f"{data['busy_markets']} busy markets")
        
        if data['fishing_communities'] > 0:
            explanations.append(f"{data['fishing_communities']} fishing communities")
        
        if data['has_border']:
            explanations.append("Border crossing present")
        
        if not explanations:
            return "Low mobility - limited spread risk"
        
        return " | ".join(explanations)

# Test
if __name__ == "__main__":
    mob = MobilityModule()
    print("🚶 MOBILITY INTELLIGENCE")
    print("=" * 50)
    
    for county in mob.movement_patterns.keys():
        data = mob.get_mobility_risk(county)
        explanation = mob.get_mobility_explanation(county)
        print(f"\n{county}:")
        print(f"  Mobility Risk: {data['mobility_risk_score']:.1%}")
        print(f"  Spread Potential: {data['spread_potential']}")
        print(f"  Explanation: {explanation}")
