"""
Retrain All Models with Expanded Dataset

Uses 936 matches (vs previous 139) to retrain:
1. Role-aware attribute analysis
2. ML models (Logistic Regression, Random Forest, Gradient Boosting)
3. Statistical validation
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime


def main():
    print("=" * 80)
    print("RETRAINING ALL MODELS WITH EXPANDED DATASET (936 MATCHES)")
    print("=" * 80)
    print()
    
    # Load new match data
    match_path = Path("data/matches/multi_region_1000_matches.json")
    with open(match_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ Loaded {data['metadata']['total_matches']} matches")
    print(f"  Source: {data['metadata']['source']}")
    print(f"  Tiers: {', '.join(data['metadata']['tiers'])}")
    print(f"  Regions: {', '.join([r.upper() for r in data['metadata']['regions']])}")
    print()
    
    # Update attribute relationships with new data
    print("=" * 80)
    print("STEP 1: Role-Aware Attribute Analysis")
    print("=" * 80)
    print()
    
    # Copy new matches to working directory
    import shutil
    working_match_path = Path("data/matches/euw1_matches.json")
    shutil.copy(match_path, working_match_path)
    print(f"✓ Copied match data to {working_match_path}")
    print()
    
    print("Running role-aware analysis...")
    result = subprocess.run(
        ["python", "validation/role_aware_analysis.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(result.stdout)
        
        # Extract accuracy from output
        for line in result.stdout.split('\n'):
            if 'MODEL ACCURACY:' in line:
                print(f"\n🎯 {line.strip()}")
    else:
        print(f"✗ Error running role-aware analysis:")
        print(result.stderr)
        return
    
    # Re-run ML simulation with new models
    print("\n" + "=" * 80)
    print("STEP 2: ML Model Training and 10K Simulation")
    print("=" * 80)
    print()
    
    print("Training ML models and simulating 10,000 games...")
    result = subprocess.run(
        ["python", "validation/ml_simulation.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(result.stdout)
        
        # Extract key metrics
        for line in result.stdout.split('\n'):
            if 'Model Accuracy:' in line or 'ACCURACY:' in line:
                print(f"\n📊 {line.strip()}")
    else:
        print(f"✗ Error running ML simulation:")
        print(result.stderr)
        return
    
    # Statistical analysis
    print("\n" + "=" * 80)
    print("STEP 3: Statistical Validation")
    print("=" * 80)
    print()
    
    print("Running statistical analysis...")
    result = subprocess.run(
        ["python", "validation/statistical_analysis.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(result.stdout)
        
        # Extract accuracy
        for line in result.stdout.split('\n'):
            if 'MODEL ACCURACY:' in line:
                print(f"\n📈 {line.strip()}")
    else:
        print(f"✗ Error running statistical analysis:")
        print(result.stderr)
        return
    
    # Summary
    print("\n" + "=" * 80)
    print("RETRAINING COMPLETE")
    print("=" * 80)
    print()
    print(f"✓ All models retrained with {data['metadata']['total_matches']} matches")
    print(f"✓ Previous dataset: 139 Challenger matches (EUW only)")
    print(f"✓ New dataset: 936 matches (Diamond+ from EUW + KR)")
    print(f"✓ Improvement: 6.7x more training data")
    print()
    print("Next steps:")
    print("  1. Review accuracy improvements in role_aware_relationships.json")
    print("  2. Check ML model performance in simulation_10k_games.json")
    print("  3. Analyze statistical significance in statistical_analysis.json")
    print()


if __name__ == "__main__":
    main()
