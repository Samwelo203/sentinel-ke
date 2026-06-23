
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================
# DATA QUALITY MODULE
# ============================================

class DataQualityModule:
    """
    Tracks data completeness and reporting delays
    This is your unique contribution - most systems ignore this
    """
    
    def __init__(self):
        self.counties = ['Kisumu', 'Homa Bay', 'Siaya', 'Migori', 'Nyamira', 'Kisii']
        
        # Simulate reporting patterns (in production, track actual reporting)
        # Some facilities report late, some miss reports entirely
        self.reporting_patterns = {
            'Kisumu': {'completeness': 0.85, 'avg_delay': 3},
            'Homa Bay': {'completeness': 0.78, 'avg_delay': 5},
            'Siaya': {'completeness': 0.82, 'avg_delay': 4},
            'Migori': {'completeness': 0.80, 'avg_delay': 4},
            'Nyamira': {'completeness': 0.92, 'avg_delay': 2},
            'Kisii': {'completeness': 0.90, 'avg_delay': 2}
        }
    
    def get_reporting_quality(self, county):
        """Get reporting quality metrics for a county"""
        pattern = self.reporting_patterns.get(county)
        if not pattern:
            return None
        
        # Add some randomness to simulate real-world variation
        completeness = pattern['completeness'] + np.random.normal(0, 0.05)
        completeness = max(0.5, min(1.0, completeness))
        
        delay = pattern['avg_delay'] + np.random.randint(-1, 2)
        delay = max(0, delay)
        
        # Quality score (higher is better)
        quality_score = (completeness * 0.7) + (1 - (delay / 10) * 0.3)
        quality_score = max(0, min(1, quality_score))
        
        return {
            'county': county,
            'completeness': round(completeness, 3),
            'avg_reporting_delay': delay,
            'quality_score': round(quality_score, 3),
            'data_trust_level': 'HIGH' if quality_score > 0.8 else 'MEDIUM' if quality_score > 0.6 else 'LOW'
        }
    
    def get_model_confidence_adjustment(self, county):
        """Adjust model confidence based on data quality"""
        quality = self.get_reporting_quality(county)
        if not quality:
            return 1.0
        
        # Lower data quality = lower confidence in predictions
        if quality['quality_score'] > 0.8:
            return 1.0  # Full confidence
        elif quality['quality_score'] > 0.6:
            return 0.85  # Slightly reduced
        else:
            return 0.6  # Significantly reduced
    
    def get_delayed_reporting_correction(self, county):
        """Factor for correcting predictions when reports are delayed"""
        quality = self.get_reporting_quality(county)
        if not quality:
            return 1.0
        
        # If reports are delayed, we may be underestimating cases
        delay = quality['avg_reporting_delay']
        if delay <= 2:
            return 1.0  # No correction needed
        elif delay <= 4:
            return 1.15  # 15% correction
        else:
            return 1.3  # 30% correction
    
    def get_data_quality_explanation(self, county):
        """Human-readable explanation of data quality"""
        quality = self.get_reporting_quality(county)
        if not quality:
            return "No data quality information available"
        
        explanations = []
        if quality['completeness'] < 0.7:
            explanations.append(f"Only {quality['completeness']:.0%} reports submitted")
        else:
            explanations.append(f"{quality['completeness']:.0%} reporting completeness")
        
        if quality['avg_reporting_delay'] > 3:
            explanations.append(f"{quality['avg_reporting_delay']}-day average delay")
        else:
            explanations.append(f"Low reporting delay ({quality['avg_reporting_delay']} days)")
        
        trust = quality['data_trust_level']
        if trust == 'HIGH':
            explanations.append("High data trust level")
        elif trust == 'MEDIUM':
            explanations.append("Medium data trust - use with caution")
        else:
            explanations.append("Low data trust - significant uncertainty")
        
        return " | ".join(explanations)

# Test
if __name__ == "__main__":
    dq = DataQualityModule()
    print("📊 DATA QUALITY INTELLIGENCE")
    print("=" * 50)
    
    for county in dq.counties:
        quality = dq.get_reporting_quality(county)
        explanation = dq.get_data_quality_explanation(county)
        correction = dq.get_delayed_reporting_correction(county)
        confidence = dq.get_model_confidence_adjustment(county)
        
        print(f"\n{county}:")
        print(f"  Completeness: {quality['completeness']:.0%}")
        print(f"  Reporting Delay: {quality['avg_reporting_delay']} days")
        print(f"  Quality Score: {quality['quality_score']:.1%}")
        print(f"  Confidence Adjustment: {confidence:.0%}")
        print(f"  Case Correction Factor: {correction:.2f}")
        print(f"  Explanation: {explanation}")
