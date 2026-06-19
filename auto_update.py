#!/usr/bin/env python3
"""
SENTINEL-KE AI-POWERED AUTO UPDATE
Uses trained XGBoost model with exactly 25 features
"""

import pandas as pd
import numpy as np
import requests
import joblib
import xgboost as xgb
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

# Your 6 counties
COUNTIES = {
    'Kisumu': {'lat': -0.1022, 'lon': 34.7617},
    'Homa Bay': {'lat': -0.5273, 'lon': 34.4571},
    'Siaya': {'lat': 0.0600, 'lon': 34.2800},
    'Migori': {'lat': -1.0634, 'lon': 34.4732},
    'Nyamira': {'lat': -0.5667, 'lon': 34.9333},
    'Kisii': {'lat': -0.6773, 'lon': 34.7666}
}

def load_ai_model():
    """Load the trained XGBoost model and artifacts"""
    try:
        model = xgb.XGBClassifier()
        model.load_model('models/xgboost_model.json')
        scaler = joblib.load('models/scaler.pkl')
        with open('models/features.txt', 'r') as f:
            features = [line.strip() for line in f.readlines()]
        with open('models/optimal_threshold.txt', 'r') as f:
            threshold = float(f.read().strip())
        print(f"✅ AI Model loaded successfully (expects {len(features)} features)")
        return model, scaler, features, threshold
    except Exception as e:
        print(f"⚠️ Could not load AI model: {e}")
        return None, None, None, 0.65

def fetch_rainfall():
    """Fetch rainfall data for last 30 days"""
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

def prepare_features_for_prediction(rainfall_df, county, all_features):
    """Prepare EXACTLY 25 features for AI prediction"""

    # Get county-specific rainfall
    county_rain = rainfall_df[rainfall_df['county'] == county].sort_values('date')

    if len(county_rain) < 14:
        return None

    # Create feature dictionary with ALL features initialized to 0
    features_dict = {feat: 0 for feat in all_features}

    # --- Fill in the 19 core features ---
    # 1-6: Lag features (using rainfall as proxy for cases)
    features_dict['cholera_lag_3'] = county_rain['rainfall_mm'].shift(3).tail(1).values[0] if len(county_rain) > 3 else 0
    features_dict['cholera_lag_5'] = county_rain['rainfall_mm'].shift(5).tail(1).values[0] if len(county_rain) > 5 else 0
    features_dict['cholera_lag_7'] = county_rain['rainfall_mm'].shift(7).tail(1).values[0] if len(county_rain) > 7 else 0
    features_dict['malaria_lag_3'] = county_rain['rainfall_mm'].shift(3).tail(1).values[0] if len(county_rain) > 3 else 0
    features_dict['malaria_lag_5'] = county_rain['rainfall_mm'].shift(5).tail(1).values[0] if len(county_rain) > 5 else 0
    features_dict['malaria_lag_7'] = county_rain['rainfall_mm'].shift(7).tail(1).values[0] if len(county_rain) > 7 else 0

    # 7-11: Rainfall features
    features_dict['rainfall_mm'] = county_rain['rainfall_mm'].tail(1).values[0]
    features_dict['rain_7day_avg'] = county_rain['rainfall_mm'].tail(7).mean()
    features_dict['rain_7day_lag'] = county_rain['rainfall_mm'].shift(7).tail(1).values[0] if len(county_rain) > 7 else 0
    features_dict['rain_14day_lag'] = county_rain['rainfall_mm'].shift(14).tail(1).values[0] if len(county_rain) > 14 else 0
    features_dict['rain_21day_lag'] = county_rain['rainfall_mm'].shift(21).tail(1).values[0] if len(county_rain) > 21 else 0

    # 12-14: Temporal features
    current_date = datetime.now()
    features_dict['week_of_year'] = current_date.isocalendar().week
    features_dict['month'] = current_date.month
    features_dict['is_rainy_season'] = 1 if current_date.month in [4,5,6,10,11] else 0

    # 15-17: Data quality features
    features_dict['cholera_missing'] = 0
    features_dict['malaria_missing'] = 0
    features_dict['report_delay_days'] = 5

    # 18-19: Population features
    population_data = {
        'Kisumu': 1200000, 'Homa Bay': 1150000, 'Siaya': 1000000,
        'Migori': 1150000, 'Nyamira': 650000, 'Kisii': 1350000
    }
    cholera_rates = {
        'Kisumu': 5.2, 'Homa Bay': 6.8, 'Siaya': 3.9,
        'Migori': 4.5, 'Nyamira': 0.8, 'Kisii': 1.2
    }
    features_dict['population'] = population_data.get(county, 1000000)
    features_dict['cholera_rate_per_100k'] = cholera_rates.get(county, 3.0)

    # 20-25: County indicators (one-hot encoding)
    for c in COUNTIES.keys():
        features_dict[f'county_{c}'] = 1 if county == c else 0

    # Verify we have all 25 features
    if len(features_dict) != 25:
        print(f"⚠️ {county}: Expected 25 features, got {len(features_dict)}")

    return features_dict

def calculate_risk_ai(rainfall_df, model, scaler, feature_list, threshold):
    """Use AI model to predict outbreak risk for all counties"""
    results = []
    successful_ai = 0

    for county in COUNTIES.keys():
        # Prepare all features for this county
        feature_dict = prepare_features_for_prediction(rainfall_df, county, feature_list)

        if feature_dict is None:
            print(f"⚠️ Not enough data for {county}, using fallback")
            county_rain = rainfall_df[rainfall_df['county'] == county]
            rain_7day = county_rain['rainfall_mm'].tail(7).sum()
            risk_score = min(0.95, max(0.05, rain_7day / 80))
            ai_used = False
        else:
            try:
                # Create DataFrame with features in the correct order
                feature_df = pd.DataFrame([feature_dict])[feature_list]

                # Scale features
                feature_scaled = scaler.transform(feature_df)

                # Get AI prediction
                risk_score = model.predict_proba(feature_scaled)[0][1]
                ai_used = True
                successful_ai += 1
                print(f"✅ {county}: AI prediction = {risk_score:.3f}")

            except Exception as e:
                print(f"⚠️ AI failed for {county}: {e}")
                # Fallback to simple calculation
                county_rain = rainfall_df[rainfall_df['county'] == county]
                rain_7day = county_rain['rainfall_mm'].tail(7).sum()
                risk_score = min(0.95, max(0.05, rain_7day / 80))
                ai_used = False

        results.append({
            'county': county,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'risk_score': round(risk_score, 3),
            'alert': risk_score > threshold,
            'ai_prediction': ai_used
        })

    if successful_ai > 0:
        print(f"\n🧠 AI used for {successful_ai}/{len(COUNTIES)} counties")
    return pd.DataFrame(results)

def calculate_risk_simple(rainfall_df):
    """Fallback simple risk calculation"""
    results = []
    for county in COUNTIES.keys():
        county_rain = rainfall_df[rainfall_df['county'] == county]
        if len(county_rain) > 0:
            rain_7day = county_rain['rainfall_mm'].tail(7).sum()
            rain_14day = county_rain['rainfall_mm'].tail(14).sum()
            risk_score = min(0.95, max(0.05, (rain_7day / 80) + (rain_14day / 150)))

            results.append({
                'county': county,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'risk_score': round(risk_score, 3),
                'alert': risk_score > 0.65,
                'ai_prediction': False
            })
    return pd.DataFrame(results)

if __name__ == "__main__":
    print("=" * 50)
    print("🛡️ SENTINEL-KE AI UPDATE")
    print("=" * 50)

    # Try to load AI model
    model, scaler, features, threshold = load_ai_model()

    # Fetch rainfall
    print("\n📡 Fetching rainfall data...")
    rainfall_df = fetch_rainfall()

    if len(rainfall_df) == 0:
        print("❌ No rainfall data fetched")
        exit(1)

    # Save rainfall
    os.makedirs('data/raw', exist_ok=True)
    rainfall_df.to_csv('data/raw/latest_rainfall.csv', index=False)

    # Use AI if available
    if model is not None and scaler is not None and features is not None:
        print(f"\n🧠 Running AI model with {len(features)} features...")
        predictions = calculate_risk_ai(rainfall_df, model, scaler, features, threshold)
    else:
        print("\n⚠️ Using simplified calculation (AI model not available)")
        predictions = calculate_risk_simple(rainfall_df)

    # Save predictions
    os.makedirs('data/processed', exist_ok=True)
    predictions.to_csv('data/processed/latest_predictions.csv', index=False)

    print(f"\n✅ Predictions saved")
    print("\n📊 Results:")
    print(predictions.to_string(index=False))

    # Show alerts
    alerts = predictions[predictions['alert'] == True]
    if len(alerts) > 0:
        print(f"\n🚨 ALERTS: {', '.join(alerts['county'].tolist())}")
    else:
        print("\n✅ No active alerts")
