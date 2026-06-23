#!/usr/bin/env python3
"""
SENTINEL-KE COMPLETE AUTO UPDATE
Includes all 5 intelligence domains
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import os
import sys
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.append('/content/drive/My Drive/sentinel-ke')

# Import all domains
from remote_sensing import RemoteSensingModule
from wash_intelligence import WASHModule
from data_quality import DataQualityModule
from mobility_intelligence import MobilityModule
from health_capacity import HealthCapacityModule

# ============================================
# CONFIGURATION
# ============================================

COUNTIES = {
    'Kisumu': {'lat': -0.1022, 'lon': 34.7617},
    'Homa Bay': {'lat': -0.5273, 'lon': 34.4571},
    'Siaya': {'lat': 0.0600, 'lon': 34.2800},
    'Migori': {'lat': -1.0634, 'lon': 34.4732},
    'Nyamira': {'lat': -0.5667, 'lon': 34.9333},
    'Kisii': {'lat': -0.6773, 'lon': 34.7666}
}

# ============================================
# INITIALIZE DOMAINS
# ============================================

def initialize_domains():
    """Initialize all intelligence modules"""
    try:
        remote = RemoteSensingModule()
        wash = WASHModule()
        quality = DataQualityModule()
        mobility = MobilityModule()
        capacity = HealthCapacityModule()
        return remote, wash, quality, mobility, capacity
    except Exception as e:
        print(f"⚠️ Error loading modules: {e}")
        return None, None, None, None, None

# ============================================
# FETCH RAINFALL DATA
# ============================================

def fetch_rainfall():
    """Fetch rainfall data for last 45 days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=45)
    all_data = []
    
    for county, coords in COUNTIES.items():
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            'latitude': coords['lat'],
            'longitude': coords['lon'],
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'daily': 'rain_sum',
            'timezone': 'Africa/Nairobi'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                for date, rain in zip(data['daily']['time'], data['daily']['rain_sum']):
                    all_data.append({
                        'county': county,
                        'date': date,
                        'rainfall_mm': rain
                    })
                print(f"✅ {county}: {len(data['daily']['time'])} days")
            else:
                print(f"❌ {county}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {county}: {e}")
    
    return pd.DataFrame(all_data)

# ============================================
# CALCULATE COMPREHENSIVE RISK
# ============================================

def calculate_risk(rainfall_df, remote, wash, quality, mobility, capacity):
    """Calculate risk using all domains"""
    results = []
    
    for county in COUNTIES.keys():
        # Get rainfall data for this county
        county_rain = rainfall_df[rainfall_df['county'] == county]
        rain_14day = county_rain['rainfall_mm'].tail(14).mean() if len(county_rain) >= 14 else 0
        rain_30day = county_rain['rainfall_mm'].tail(30).mean() if len(county_rain) >= 30 else 0
        
        # Base rainfall risk (0-1)
        rainfall_risk = min(0.95, max(0.05, rain_14day / 25))
        
        # Get domain-specific risks
        try:
            ndvi_data = remote.get_malaria_risk_factor(county, datetime.now())
            env_risk = ndvi_data['combined_risk']
        except:
            env_risk = 0.3
        
        try:
            wash_data = wash.get_wash_risk_score(county)
            wash_risk = wash_data['wash_risk_score'] if wash_data else 0.3
        except:
            wash_risk = 0.3
        
        try:
            quality_data = quality.get_reporting_quality(county)
            quality_score = quality_data['quality_score'] if quality_data else 0.7
        except:
            quality_score = 0.7
        
        try:
            mobility_data = mobility.get_mobility_risk(county)
            mobility_risk = mobility_data['mobility_risk_score'] if mobility_data else 0.3
        except:
            mobility_risk = 0.3
        
        try:
            capacity_data = capacity.get_capacity_metrics(county)
            capacity_risk = 1 - capacity_data['response_readiness'] if capacity_data else 0.3
        except:
            capacity_risk = 0.3
        
        # Weighted combination
        weights = {
            'rainfall': 0.25,
            'environmental': 0.20,
            'wash': 0.20,
            'mobility': 0.15,
            'capacity': 0.10,
            'data_quality': 0.10
        }
        
        combined_risk = (
            rainfall_risk * weights['rainfall'] +
            env_risk * weights['environmental'] +
            wash_risk * weights['wash'] +
            mobility_risk * weights['mobility'] +
            capacity_risk * weights['capacity'] +
            (1 - quality_score) * weights['data_quality']
        )
        
        combined_risk = min(0.95, max(0.05, combined_risk))
        
        results.append({
            'county': county,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'risk_score': round(combined_risk, 3),
            'alert': combined_risk > 0.65,
            'rainfall_risk': round(rainfall_risk, 3),
            'environmental_risk': round(env_risk, 3),
            'wash_risk': round(wash_risk, 3),
            'mobility_risk': round(mobility_risk, 3),
            'capacity_risk': round(capacity_risk, 3),
            'data_quality_score': round(quality_score, 3)
        })
    
    return pd.DataFrame(results)

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("🛡️ SENTINEL-KE COMPLETE UPDATE")
    print("   (All 5 Intelligence Domains)")
    print("=" * 60)
    
    # Initialize domains
    print("\n📦 Loading intelligence modules...")
    remote, wash, quality, mobility, capacity = initialize_domains()
    
    # Fetch rainfall
    print("\n📡 Fetching rainfall data...")
    rainfall_df = fetch_rainfall()
    
    if len(rainfall_df) == 0:
        print("❌ No rainfall data fetched")
        exit(1)
    
    # Save rainfall
    os.makedirs('data/raw', exist_ok=True)
    rainfall_df.to_csv('data/raw/latest_rainfall.csv', index=False)
    
    # Calculate comprehensive risk
    print("\n🧠 Calculating comprehensive risk...")
    predictions = calculate_risk(rainfall_df, remote, wash, quality, mobility, capacity)
    
    # Save predictions
    os.makedirs('data/processed', exist_ok=True)
    predictions.to_csv('data/processed/latest_predictions.csv', index=False)
    
    print("\n📊 RESULTS:")
    print("-" * 60)
    print(predictions[['county', 'risk_score', 'alert']].to_string(index=False))
    
    # Show alerts
    alerts = predictions[predictions['alert'] == True]
    if len(alerts) > 0:
        print(f"\n🚨 ALERTS: {', '.join(alerts['county'].tolist())}")
    else:
        print("\n✅ No active alerts")
    
    print("\n✅ Update complete!")
