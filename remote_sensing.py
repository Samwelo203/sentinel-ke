
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================
# NDVI DATA FROM NASA MODIS (via API)
# ============================================

class RemoteSensingModule:
    """Fetches and processes satellite data for disease prediction"""

    def __init__(self):
        self.counties = {
            'Kisumu': {'lat': -0.1022, 'lon': 34.7617},
            'Homa Bay': {'lat': -0.5273, 'lon': 34.4571},
            'Siaya': {'lat': 0.0600, 'lon': 34.2800},
            'Migori': {'lat': -1.0634, 'lon': 34.4732},
            'Nyamira': {'lat': -0.5667, 'lon': 34.9333},
            'Kisii': {'lat': -0.6773, 'lon': 34.7666}
        }

    def fetch_ndvi(self, county, date):
        """
        Fetch NDVI (Normalized Difference Vegetation Index)
        Higher NDVI = more vegetation = more mosquitoes
        """
        # For demo, generate realistic NDVI values
        # In production, use NASA MODIS API or Google Earth Engine
        np.random.seed(hash(county + str(date)) % 2**32)

        # NDVI ranges from -1 to 1, but vegetation areas are 0.3-0.8
        base_ndvi = {
            'Kisumu': 0.45,
            'Homa Bay': 0.50,
            'Siaya': 0.42,
            'Migori': 0.48,
            'Nyamira': 0.55,  # Highland - more vegetation
            'Kisii': 0.52
        }

        # Add seasonal variation (rainy season = more vegetation)
        month = date.month
        if month in [4,5,6,10,11]:  # Rainy seasons
            seasonal_factor = 1.2
        else:
            seasonal_factor = 0.9

        # Add random noise
        ndvi = base_ndvi.get(county, 0.45) * seasonal_factor + np.random.normal(0, 0.05)
        return max(0.1, min(0.8, ndvi))

    def fetch_land_surface_temperature(self, county, date):
        """LST - Land Surface Temperature"""
        # Higher temperature = faster mosquito breeding
        base_temp = {
            'Kisumu': 28.5,
            'Homa Bay': 27.8,
            'Siaya': 27.2,
            'Migori': 28.0,
            'Nyamira': 22.5,  # Highland - cooler
            'Kisii': 23.0
        }

        # Add seasonal variation
        month = date.month
        if month in [1,2,12]:  # Hot season
            seasonal_factor = 1.1
        elif month in [6,7,8]:  # Cool season
            seasonal_factor = 0.9
        else:
            seasonal_factor = 1.0

        temp = base_temp.get(county, 26) * seasonal_factor + np.random.normal(0, 1)
        return max(18, min(35, temp))

    def get_malaria_risk_factor(self, county, date):
        """Calculate malaria risk from environmental data"""
        ndvi = self.fetch_ndvi(county, date)
        lst = self.fetch_land_surface_temperature(county, date)

        # Mosquito breeding conditions:
        # - High NDVI (>0.4) = good vegetation
        # - Temperature 20-30°C = optimal for mosquito breeding
        vegetation_score = min(1, max(0, (ndvi - 0.2) / 0.4))

        if 20 <= lst <= 30:
            temp_score = 1 - abs(lst - 25) / 10
        else:
            temp_score = 0.3

        risk_factor = (vegetation_score * 0.6) + (temp_score * 0.4)
        return {
            'ndvi': round(ndvi, 3),
            'lst': round(lst, 1),
            'vegetation_risk': round(vegetation_score, 3),
            'temperature_risk': round(temp_score, 3),
            'combined_risk': round(risk_factor, 3)
        }

# Test the module
if __name__ == "__main__":
    rs = RemoteSensingModule()
    today = datetime.now()

    print("🛰️  REMOTE SENSING DATA")
    print("=" * 50)

    for county in rs.counties.keys():
        data = rs.get_malaria_risk_factor(county, today)
        print(f"\n{county}:")
        print(f"  NDVI: {data['ndvi']:.3f} (Vegetation density)")
        print(f"  LST: {data['lst']:.1f}°C (Land temp)")
        print(f"  Malaria Risk: {data['combined_risk']:.1%}")
