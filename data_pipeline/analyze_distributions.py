"""
Analyze attribute distributions to understand natural clustering and set data-driven thresholds.
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


class DistributionAnalyzer:
    """Analyze spell-based attribute distributions across all champions."""
    
    def __init__(self, data_dir: str = "data/processed"):
        self.data_dir = Path(data_dir)
        
        with open(self.data_dir / "spell_based_attributes.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.attributes = data["attributes"]
    
    def compute_statistics(self, values: List[float]) -> Dict:
        """Compute descriptive statistics for a distribution."""
        arr = np.array(values)
        return {
            "count": len(arr),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "std": float(np.std(arr)),
            "p25": float(np.percentile(arr, 25)),
            "p50": float(np.percentile(arr, 50)),
            "p75": float(np.percentile(arr, 75)),
            "p90": float(np.percentile(arr, 90)),
            "p95": float(np.percentile(arr, 95)),
        }
    
    def analyze_all_attributes(self) -> Dict:
        """Analyze distributions for all numeric attributes."""
        # Collect values for each attribute
        distributions = defaultdict(list)
        
        for champion, attrs in self.attributes.items():
            for key, value in attrs.items():
                if isinstance(value, (int, float)):
                    distributions[key].append(value)
        
        # Compute statistics
        stats = {}
        for attr_name, values in distributions.items():
            stats[attr_name] = self.compute_statistics(values)
        
        return stats
    
    def identify_outliers(self, attr_name: str, threshold_std: float = 2.0) -> List[Tuple[str, float]]:
        """Identify champions with extreme values (>threshold_std standard deviations from mean)."""
        values = [(champ, attrs[attr_name]) for champ, attrs in self.attributes.items() 
                  if attr_name in attrs]
        
        arr = np.array([v[1] for v in values])
        mean = np.mean(arr)
        std = np.std(arr)
        
        outliers = []
        for champ, value in values:
            z_score = abs((value - mean) / std) if std > 0 else 0
            if z_score > threshold_std:
                outliers.append((champ, value))
        
        return sorted(outliers, key=lambda x: x[1], reverse=True)
    
    def create_histogram(self, attr_name: str, bins: int = 20) -> Dict:
        """Create histogram data for an attribute."""
        values = [attrs[attr_name] for attrs in self.attributes.values() if attr_name in attrs]
        
        hist, bin_edges = np.histogram(values, bins=bins)
        
        return {
            "bins": bins,
            "counts": hist.tolist(),
            "edges": bin_edges.tolist(),
            "total": len(values)
        }
    
    def suggest_thresholds(self, attr_name: str) -> Dict:
        """Suggest classification thresholds based on percentiles."""
        values = [attrs[attr_name] for attrs in self.attributes.values() if attr_name in attrs]
        arr = np.array(values)
        
        return {
            "very_low": float(np.percentile(arr, 10)),   # Bottom 10%
            "low": float(np.percentile(arr, 25)),        # Bottom quartile
            "medium": float(np.percentile(arr, 50)),     # Median
            "high": float(np.percentile(arr, 75)),       # Top quartile
            "very_high": float(np.percentile(arr, 90)),  # Top 10%
        }
    
    def find_champions_by_attribute(self, attr_name: str, min_value: float = None, 
                                   max_value: float = None, top_n: int = None) -> List[Tuple[str, float]]:
        """Find champions matching attribute criteria."""
        results = []
        
        for champ, attrs in self.attributes.items():
            if attr_name not in attrs:
                continue
            
            value = attrs[attr_name]
            
            if min_value is not None and value < min_value:
                continue
            if max_value is not None and value > max_value:
                continue
            
            results.append((champ, value))
        
        results.sort(key=lambda x: x[1], reverse=True)
        
        if top_n is not None:
            results = results[:top_n]
        
        return results
    
    def generate_report(self) -> None:
        """Generate comprehensive distribution analysis report."""
        print("=" * 80)
        print("ATTRIBUTE DISTRIBUTION ANALYSIS")
        print("=" * 80)
        
        stats = self.analyze_all_attributes()
        
        # Key attributes for archetypes
        key_attributes = [
            "burst_index",
            "burst_damage", 
            "sustained_dps",
            "cc_score",
            "mobility_score",
            "max_range"
        ]
        
        for attr_name in key_attributes:
            if attr_name not in stats:
                continue
            
            print(f"\n{attr_name.upper().replace('_', ' ')}")
            print("-" * 80)
            
            stat = stats[attr_name]
            print(f"  Range: [{stat['min']:.2f}, {stat['max']:.2f}]")
            print(f"  Mean: {stat['mean']:.2f} ± {stat['std']:.2f}")
            print(f"  Median: {stat['median']:.2f}")
            print(f"  Quartiles: Q1={stat['p25']:.2f}, Q2={stat['p50']:.2f}, Q3={stat['p75']:.2f}")
            print(f"  Top 10%: >{stat['p90']:.2f}")
            print(f"  Top 5%: >{stat['p95']:.2f}")
            
            # Suggested thresholds
            thresholds = self.suggest_thresholds(attr_name)
            print(f"\n  Suggested Classification Thresholds:")
            print(f"    Very Low: <{thresholds['very_low']:.2f}")
            print(f"    Low:      <{thresholds['low']:.2f}")
            print(f"    Medium:   <{thresholds['medium']:.2f}")
            print(f"    High:     <{thresholds['high']:.2f}")
            print(f"    Very High: >={thresholds['high']:.2f}")
            
            # Top 10 champions
            top_10 = self.find_champions_by_attribute(attr_name, top_n=10)
            print(f"\n  Top 10 Champions:")
            for i, (champ, value) in enumerate(top_10, 1):
                print(f"    {i:2d}. {champ:20s} {value:.2f}")
            
            # Outliers
            outliers = self.identify_outliers(attr_name, threshold_std=2.5)
            if outliers:
                print(f"\n  Outliers (>2.5 std dev):")
                for champ, value in outliers[:5]:
                    print(f"    {champ:20s} {value:.2f}")
        
        # Damage profile distribution
        print("\n" + "=" * 80)
        print("DAMAGE PROFILE DISTRIBUTION")
        print("-" * 80)
        profile_counts = defaultdict(int)
        for attrs in self.attributes.values():
            profile = attrs.get("damage_profile", "neutral")
            profile_counts[profile] += 1
        
        for profile, count in sorted(profile_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(self.attributes)) * 100
            print(f"  {profile:10s}: {count:3d} ({pct:5.1f}%)")
        
        # Save detailed report
        output_file = self.data_dir / "attribute_distributions.json"
        report_data = {
            "statistics": stats,
            "thresholds": {attr: self.suggest_thresholds(attr) for attr in key_attributes if attr in stats},
            "histograms": {attr: self.create_histogram(attr) for attr in key_attributes if attr in stats},
            "damage_profiles": dict(profile_counts)
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n{'=' * 80}")
        print(f"Detailed report saved to: {output_file}")
        print("=" * 80)


def main():
    analyzer = DistributionAnalyzer()
    analyzer.generate_report()


if __name__ == "__main__":
    main()
