
import pandas as pd
import numpy as np

# ============================================
# HEALTH FACILITY CAPACITY MODULE
# ============================================

class HealthCapacityModule:
    """
    Tracks health system capacity for outbreak response
    """
    
    def __init__(self):
        self.facility_data = {
            'Kisumu': {
                'hospitals': 5,
                'health_centers': 12,
                'total_beds': 350,
                'isolation_beds': 20,
                'health_workers': 280,
                'cholera_kits': 50,
                'iv_fluids': 200,
                'response_readiness': 0.75
            },
            'Homa Bay': {
                'hospitals': 4,
                'health_centers': 10,
                'total_beds': 280,
                'isolation_beds': 15,
                'health_workers': 220,
                'cholera_kits': 35,
                'iv_fluids': 150,
                'response_readiness': 0.68
            },
            'Siaya': {
                'hospitals': 3,
                'health_centers': 8,
                'total_beds': 200,
                'isolation_beds': 10,
                'health_workers': 180,
                'cholera_kits': 25,
                'iv_fluids': 100,
                'response_readiness': 0.60
            },
            'Migori': {
                'hospitals': 4,
                'health_centers': 9,
                'total_beds': 240,
                'isolation_beds': 12,
                'health_workers': 200,
                'cholera_kits': 30,
                'iv_fluids': 120,
                'response_readiness': 0.65
            },
            'Nyamira': {
                'hospitals': 2,
                'health_centers': 6,
                'total_beds': 150,
                'isolation_beds': 8,
                'health_workers': 140,
                'cholera_kits': 20,
                'iv_fluids': 80,
                'response_readiness': 0.72
            },
            'Kisii': {
                'hospitals': 3,
                'health_centers': 7,
                'total_beds': 180,
                'isolation_beds': 10,
                'health_workers': 160,
                'cholera_kits': 25,
                'iv_fluids': 90,
                'response_readiness': 0.70
            }
        }
        
        # Population for per-capita calculations
        self.population = {
            'Kisumu': 1200000,
            'Homa Bay': 1150000,
            'Siaya': 1000000,
            'Migori': 1150000,
            'Nyamira': 650000,
            'Kisii': 1350000
        }
    
    def get_capacity_metrics(self, county):
        """Get health system capacity metrics"""
        data = self.facility_data.get(county)
        pop = self.population.get(county, 1000000)
        
        if not data:
            return None
        
        # Calculate per-capita metrics
        beds_per_100k = (data['total_beds'] / pop) * 100000
        workers_per_100k = (data['health_workers'] / pop) * 100000
        
        return {
            'county': county,
            'hospitals': data['hospitals'],
            'health_centers': data['health_centers'],
            'total_beds': data['total_beds'],
            'isolation_beds': data['isolation_beds'],
            'health_workers': data['health_workers'],
            'cholera_kits': data['cholera_kits'],
            'iv_fluids': data['iv_fluids'],
            'beds_per_100k': round(beds_per_100k, 1),
            'workers_per_100k': round(workers_per_100k, 1),
            'response_readiness': data['response_readiness'],
            'readiness_level': 'HIGH' if data['response_readiness'] > 0.7 else 'MEDIUM' if data['response_readiness'] > 0.5 else 'LOW'
        }
    
    def get_outbreak_capacity_explanation(self, county):
        """Explain if health system can handle an outbreak"""
        data = self.get_capacity_metrics(county)
        if not data:
            return "No capacity data available"
        
        issues = []
        
        if data['beds_per_100k'] < 30:
            issues.append(f"Only {data['beds_per_100k']:.0f} beds per 100k (below recommended)")
        
        if data['workers_per_100k'] < 20:
            issues.append(f"Only {data['workers_per_100k']:.0f} health workers per 100k")
        
        if data['isolation_beds'] < 15:
            issues.append(f"Limited isolation capacity ({data['isolation_beds']} beds)")
        
        if data['cholera_kits'] < 30:
            issues.append("Limited cholera kit supply")
        
        if not issues:
            return "Good capacity to handle outbreaks"
        
        return " | ".join(issues)

# Test
if __name__ == "__main__":
    cap = HealthCapacityModule()
    print("🏥 HEALTH FACILITY CAPACITY")
    print("=" * 50)
    
    for county in cap.facility_data.keys():
        data = cap.get_capacity_metrics(county)
        explanation = cap.get_outbreak_capacity_explanation(county)
        print(f"\n{county}:")
        print(f"  Beds per 100k: {data['beds_per_100k']:.1f}")
        print(f"  Health Workers: {data['health_workers']}")
        print(f"  Isolation Beds: {data['isolation_beds']}")
        print(f"  Readiness: {data['readiness_level']}")
        print(f"  Explanation: {explanation}")
