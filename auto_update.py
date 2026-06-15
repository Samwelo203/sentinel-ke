#!/usr/bin/env python3
"""
SENTINEL-KE Auto Data Updater
Runs daily to fetch latest rainfall and update predictions
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import json
import os

# Your 6 counties
COUNTIES = {
    'Kisumu': {'lat': -0.1022, 'lon': 34.7617},
    'Homa Bay': {'lat': -0.5273, 'lon': 34.4571},
    'Siaya': {'lat': 0.0600, 'lon': 34.2800},
    'Migori': {'lat': -1.0634, 'lon': 34.4732},
    'Nyamira': {'lat': -0.5667, 'lon': 34.9333},
    'Kisii': {'lat': -0.6773, 'lon': 34.7666}
}

def fetch_rainfall():
    """Fetch latest 30 days of rainfall data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
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

def calculate_risk(rainfall_df):
    """Calculate outbreak risk based on rainfall patterns"""
    results = []
    
    for county in COUNTIES.keys():
        county_rain = rainfall_df[rainfall_df['county'] == county]
        if len(county_rain) > 0:
            # 7-day rainfall total
            rain_7day = county_rain['rainfall_mm'].tail(7).sum()
            # 14-day rainfall total  
            rain_14day = county_rain['rainfall_mm'].tail(14).sum()
            
            # Risk calculation (simplified - replace with your model)
            # Higher rain = higher risk, with 7-day lag effect
            risk_score = min(0.95, max(0.05, (rain_7day / 80) + (rain_14day / 150)))
            
            results.append({
                'county': county,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'risk_score': round(risk_score, 3),
                'rainfall_7day': round(rain_7day, 1),
                'rainfall_14day': round(rain_14day, 1),
                'alert': risk_score > 0.65  # Alert threshold
            })
    
    return pd.DataFrame(results)

def save_predictions():
    """Main function to save predictions"""
    print("=" * 50)
    print(f"SENTINEL-KE Auto Update - {datetime.now()}")
    print("=" * 50)
    
    # Fetch latest rainfall
    print("\n📡 Fetching rainfall data...")
    rainfall_df = fetch_rainfall()
    
    if len(rainfall_df) == 0:
        print("❌ No rainfall data fetched")
        return False
    
    # Save rainfall data
    os.makedirs('data/raw', exist_ok=True)
    rainfall_df.to_csv('data/raw/latest_rainfall.csv', index=False)
    print(f"\n✅ Saved {len(rainfall_df)} rainfall records")
    
    # Calculate risks
    print("\n🔄 Calculating outbreak risks...")
    predictions = calculate_risk(rainfall_df)
    
    # Save predictions
    os.makedirs('data/processed', exist_ok=True)
    predictions.to_csv('data/processed/latest_predictions.csv', index=False)
    
    print("\n📊 Latest Predictions:")
    print(predictions.to_string(index=False))
    
    # Check for alerts
    alerts = predictions[predictions['alert'] == True]
    if len(alerts) > 0:
        print(f"\n🚨 ALERTS for: {', '.join(alerts['county'].tolist())}")
    else:
        print("\n✅ No active alerts")
    
    print("\n✅ Update complete!")
    return True

if __name__ == "__main__":
    save_predictions()
