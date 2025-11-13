"""
Large-Scale Draft Simulation with Machine Learning

Generates 10,000 random valid team compositions and uses trained ML models
to predict outcomes, analyze patterns, and validate model performance.
"""

import json
import random
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set
import math

# Try to import sklearn, provide helpful error if not available
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import cross_val_score, train_test_split
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠ scikit-learn not installed. Will use simple scoring method.")
    print("To install: pip install scikit-learn numpy")


def load_data():
    """Load all necessary data"""
    # Champion data with attributes
    champions_path = Path("data/processed/champion_archetypes.json")
    with open(champions_path, 'r', encoding='utf-8') as f:
        champ_data = json.load(f)
    
    # Real match data
    matches_path = Path("data/matches/euw1_matches.json")
    with open(matches_path, 'r', encoding='utf-8') as f:
        match_data = json.load(f)
    
    # Role-aware relationships
    relationships_path = Path("data/processed/role_aware_relationships.json")
    with open(relationships_path, 'r', encoding='utf-8') as f:
        relationships = json.load(f)
    
    return champ_data, match_data['matches'], relationships


def get_champion_by_position(champ_data: Dict, position: str) -> List[str]:
    """Get all champions that can play a specific position"""
    champions = []
    assignments = champ_data.get('assignments', {})
    
    for champ_name, champ_info in assignments.items():
        viable_positions = champ_info.get('viable_positions', [])
        if position in viable_positions:
            champions.append(champ_name)
    
    return champions


def get_champion_attributes(champ_name: str, champ_data: Dict) -> List[str]:
    """Get attributes for a champion"""
    assignments = champ_data.get('assignments', {})
    return assignments.get(champ_name, {}).get('attributes', [])


def generate_random_team(champ_data: Dict) -> Dict[str, str]:
    """Generate a random valid team composition"""
    team = {}
    used_champions = set()
    
    positions = ['Top', 'Jungle', 'Middle', 'Bottom', 'Support']
    
    for position in positions:
        available = get_champion_by_position(champ_data, position)
        # Remove already used champions
        available = [c for c in available if c not in used_champions]
        
        if available:
            champion = random.choice(available)
            team[position] = champion
            used_champions.add(champion)
    
    return team


def extract_features_from_team(team: Dict[str, str], champ_data: Dict) -> Dict[str, float]:
    """
    Extract feature vector from team composition.
    
    Features include:
    - Attribute counts (how many champs have each attribute)
    - Role-pair synergies
    - Damage type distribution
    - Scaling profile
    """
    features = defaultdict(float)
    assignments = champ_data.get('assignments', {})
    
    # Get all attributes for team
    all_attributes = []
    role_attrs = {}
    
    for role, champion in team.items():
        attrs = assignments.get(champion, {}).get('attributes', [])
        all_attributes.extend(attrs)
        role_attrs[role] = attrs
    
    # Count attribute frequencies (normalized by 5)
    for attr in all_attributes:
        features[f"attr_{attr}"] += 1.0 / 5.0
    
    # Role-pair synergies (check all role pairs)
    roles = list(role_attrs.keys())
    for i in range(len(roles)):
        for j in range(i + 1, len(roles)):
            role1, role2 = roles[i], roles[j]
            attrs1, attrs2 = role_attrs[role1], role_attrs[role2]
            
            # Count shared attributes between roles
            shared = set(attrs1) & set(attrs2)
            features[f"role_pair_{role1}_{role2}_shared"] = len(shared) / 10.0
    
    # Damage type distribution
    damage_types = ['damage_physical', 'damage_magic', 'damage_mixed', 'damage_true']
    for dt in damage_types:
        features[f"damage_{dt}"] = all_attributes.count(dt) / 5.0
    
    # Range distribution
    ranges = ['range_melee', 'range_short', 'range_medium', 'range_long']
    for r in ranges:
        features[f"range_{r}"] = all_attributes.count(r) / 5.0
    
    # Mobility profile
    mobilities = ['mobility_high', 'mobility_medium', 'mobility_low']
    for m in mobilities:
        features[f"mobility_{m}"] = all_attributes.count(m) / 5.0
    
    # Scaling profile
    scalings = ['scaling_early', 'scaling_mid', 'scaling_late']
    for s in scalings:
        features[f"scaling_{s}"] = all_attributes.count(s) / 5.0
    
    # CC profile
    cc_types = ['cc_hard', 'cc_soft', 'cc_aoe', 'cc_single']
    for cc in cc_types:
        features[f"cc_{cc}"] = all_attributes.count(cc) / 5.0
    
    return features


def features_to_vector(features: Dict[str, float], feature_names: List[str]) -> List[float]:
    """Convert feature dict to ordered vector"""
    return [features.get(name, 0.0) for name in feature_names]


def train_ml_models(matches: List[Dict], champ_data: Dict):
    """
    Train multiple ML models on real match data
    
    Returns trained models and feature names
    """
    print("Extracting features from real matches...")
    
    X_blue = []
    X_red = []
    y = []  # 1 for blue win, 0 for red win
    
    for match in matches:
        blue_team = match['blue_team']
        red_team = match['red_team']
        winner = match['winner']
        
        # Extract features for both teams
        blue_features = extract_features_from_team(blue_team, champ_data)
        red_features = extract_features_from_team(red_team, champ_data)
        
        X_blue.append(blue_features)
        X_red.append(red_features)
        y.append(1 if winner == 'blue' else 0)
    
    # Get all feature names (union of all features seen)
    all_feature_names = set()
    for features in X_blue + X_red:
        all_feature_names.update(features.keys())
    feature_names = sorted(all_feature_names)
    
    print(f"✓ Extracted {len(feature_names)} features from {len(matches)} matches")
    
    # Convert to vectors
    X_blue_vectors = [features_to_vector(f, feature_names) for f in X_blue]
    X_red_vectors = [features_to_vector(f, feature_names) for f in X_red]
    
    # Create feature differences (blue - red)
    X = []
    for blue_vec, red_vec in zip(X_blue_vectors, X_red_vectors):
        diff = [b - r for b, r in zip(blue_vec, red_vec)]
        X.append(diff)
    
    if not SKLEARN_AVAILABLE:
        return None, feature_names, X, y
    
    X = np.array(X)
    y = np.array(y)
    
    print("\nTraining ML models...")
    
    # Train multiple models
    models = {}
    
    # 1. Logistic Regression
    print("  Training Logistic Regression...")
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X, y)
    models['logistic'] = lr
    
    # 2. Random Forest
    print("  Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf.fit(X, y)
    models['random_forest'] = rf
    
    # 3. Gradient Boosting
    print("  Training Gradient Boosting...")
    gb = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
    gb.fit(X, y)
    models['gradient_boosting'] = gb
    
    print("\n✓ Trained 3 models")
    
    # Cross-validation scores
    print("\nCross-Validation Scores (5-fold):")
    for name, model in models.items():
        scores = cross_val_score(model, X, y, cv=5)
        print(f"  {name}: {scores.mean():.3f} (±{scores.std():.3f})")
    
    return models, feature_names, X, y


def predict_match_ml(blue_team: Dict, red_team: Dict, models: Dict, 
                    feature_names: List[str], champ_data: Dict) -> Dict:
    """Predict match outcome using ML models"""
    
    # Extract features
    blue_features = extract_features_from_team(blue_team, champ_data)
    red_features = extract_features_from_team(red_team, champ_data)
    
    # Convert to vectors
    blue_vec = features_to_vector(blue_features, feature_names)
    red_vec = features_to_vector(red_features, feature_names)
    
    # Feature difference
    diff = [b - r for b, r in zip(blue_vec, red_vec)]
    
    if SKLEARN_AVAILABLE and models:
        X = np.array([diff])
        
        predictions = {}
        probabilities = {}
        
        for name, model in models.items():
            pred = model.predict(X)[0]
            prob = model.predict_proba(X)[0]
            
            predictions[name] = 'blue' if pred == 1 else 'red'
            probabilities[name] = {
                'blue': float(prob[1]),
                'red': float(prob[0])
            }
        
        # Ensemble prediction (majority vote)
        blue_votes = sum(1 for p in predictions.values() if p == 'blue')
        ensemble_pred = 'blue' if blue_votes >= 2 else 'red'
        
        # Average probabilities
        avg_blue_prob = np.mean([p['blue'] for p in probabilities.values()])
        
        return {
            'ensemble_prediction': ensemble_pred,
            'blue_probability': float(avg_blue_prob),
            'red_probability': float(1 - avg_blue_prob),
            'individual_predictions': predictions,
            'individual_probabilities': probabilities
        }
    else:
        # Simple fallback: sum of feature differences
        total_diff = sum(diff)
        prediction = 'blue' if total_diff > 0 else 'red'
        
        # Convert to pseudo-probability using sigmoid
        prob = 1 / (1 + math.exp(-total_diff))
        
        return {
            'ensemble_prediction': prediction,
            'blue_probability': prob,
            'red_probability': 1 - prob,
            'individual_predictions': {'simple': prediction},
            'individual_probabilities': {'simple': {'blue': prob, 'red': 1 - prob}}
        }


def generate_and_predict_games(n_games: int, champ_data: Dict, models: Dict, 
                              feature_names: List[str]) -> List[Dict]:
    """Generate n random games and predict outcomes"""
    
    print(f"\nGenerating {n_games:,} random games...")
    
    games = []
    
    for i in range(n_games):
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1:,}/{n_games:,} games...")
        
        # Generate two random teams
        blue_team = generate_random_team(champ_data)
        red_team = generate_random_team(champ_data)
        
        # Predict outcome
        prediction = predict_match_ml(blue_team, red_team, models, feature_names, champ_data)
        
        games.append({
            'game_id': i + 1,
            'blue_team': blue_team,
            'red_team': red_team,
            'prediction': prediction
        })
    
    print(f"✓ Generated and predicted {n_games:,} games")
    
    return games


def analyze_predictions(games: List[Dict]) -> Dict:
    """Analyze prediction patterns across all games"""
    
    print("\nAnalyzing predictions...")
    
    # Overall prediction distribution
    blue_wins = sum(1 for g in games if g['prediction']['ensemble_prediction'] == 'blue')
    red_wins = len(games) - blue_wins
    
    # Confidence distribution
    confidences = [max(g['prediction']['blue_probability'], 
                      g['prediction']['red_probability']) for g in games]
    
    avg_confidence = sum(confidences) / len(confidences)
    high_confidence = sum(1 for c in confidences if c >= 0.6)
    medium_confidence = sum(1 for c in confidences if 0.55 <= c < 0.6)
    low_confidence = sum(1 for c in confidences if c < 0.55)
    
    # Probability distribution
    blue_probs = [g['prediction']['blue_probability'] for g in games]
    
    # Find interesting games (high confidence)
    most_confident_blue = sorted(games, key=lambda g: g['prediction']['blue_probability'], reverse=True)[:5]
    most_confident_red = sorted(games, key=lambda g: g['prediction']['red_probability'], reverse=True)[:5]
    closest_games = sorted(games, key=lambda g: abs(g['prediction']['blue_probability'] - 0.5))[:5]
    
    return {
        'total_games': len(games),
        'blue_wins_predicted': blue_wins,
        'red_wins_predicted': red_wins,
        'blue_win_rate': blue_wins / len(games),
        'average_confidence': avg_confidence,
        'confidence_distribution': {
            'high_confidence_60_plus': high_confidence,
            'medium_confidence_55_60': medium_confidence,
            'low_confidence_below_55': low_confidence
        },
        'avg_blue_probability': sum(blue_probs) / len(blue_probs),
        'most_confident_blue': most_confident_blue,
        'most_confident_red': most_confident_red,
        'closest_games': closest_games
    }


def main():
    print("=" * 80)
    print("LARGE-SCALE DRAFT SIMULATION WITH MACHINE LEARNING")
    print("=" * 80)
    print()
    
    # Load data
    print("Loading data...")
    champ_data, matches, relationships = load_data()
    print(f"✓ Loaded {len(matches)} real matches")
    print(f"✓ Loaded {len(champ_data.get('assignments', {}))} champions")
    print()
    
    # Train ML models
    models, feature_names, X, y = train_ml_models(matches, champ_data)
    
    if SKLEARN_AVAILABLE and models:
        # Evaluate on real match data
        print("\n" + "=" * 80)
        print("MODEL PERFORMANCE ON REAL MATCHES")
        print("=" * 80)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        for name, model in models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            accuracy = (y_pred == y_test).mean()
            
            print(f"\n{name.upper()}:")
            print(f"  Test Accuracy: {accuracy:.1%}")
            
            # Classification report
            print(f"\n{classification_report(y_test, y_pred, target_names=['Red Win', 'Blue Win'])}")
    
    # Generate and predict 10,000 games
    print("\n" + "=" * 80)
    print("SIMULATING 10,000 RANDOM GAMES")
    print("=" * 80)
    
    n_games = 10000
    games = generate_and_predict_games(n_games, champ_data, models, feature_names)
    
    # Analyze predictions
    print("\n" + "=" * 80)
    print("PREDICTION ANALYSIS")
    print("=" * 80)
    
    analysis = analyze_predictions(games)
    
    print(f"\nTotal games simulated: {analysis['total_games']:,}")
    print(f"\nPrediction Distribution:")
    print(f"  Blue wins predicted: {analysis['blue_wins_predicted']:,} ({analysis['blue_win_rate']:.1%})")
    print(f"  Red wins predicted: {analysis['red_wins_predicted']:,} ({1 - analysis['blue_win_rate']:.1%})")
    print(f"\nAverage Confidence: {analysis['average_confidence']:.1%}")
    print(f"\nConfidence Distribution:")
    print(f"  High confidence (≥60%): {analysis['confidence_distribution']['high_confidence_60_plus']:,} games")
    print(f"  Medium confidence (55-60%): {analysis['confidence_distribution']['medium_confidence_55_60']:,} games")
    print(f"  Low confidence (<55%): {analysis['confidence_distribution']['low_confidence_below_55']:,} games")
    
    print("\n" + "-" * 80)
    print("Sample High-Confidence Blue Wins:")
    print("-" * 80)
    for i, game in enumerate(analysis['most_confident_blue'][:3], 1):
        print(f"\n{i}. Game #{game['game_id']} - Blue {game['prediction']['blue_probability']:.1%}")
        print(f"   Blue: {', '.join(f'{role}={champ}' for role, champ in game['blue_team'].items())}")
        print(f"   Red:  {', '.join(f'{role}={champ}' for role, champ in game['red_team'].items())}")
    
    print("\n" + "-" * 80)
    print("Sample Closest Games (Most Balanced):")
    print("-" * 80)
    for i, game in enumerate(analysis['closest_games'][:3], 1):
        print(f"\n{i}. Game #{game['game_id']} - Blue {game['prediction']['blue_probability']:.1%}")
        print(f"   Blue: {', '.join(f'{role}={champ}' for role, champ in game['blue_team'].items())}")
        print(f"   Red:  {', '.join(f'{role}={champ}' for role, champ in game['red_team'].items())}")
    
    # Save results
    print("\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)
    
    # Save full results (first 1000 games with details)
    output = {
        'metadata': {
            'total_games': n_games,
            'real_matches_used_for_training': len(matches),
            'features_extracted': len(feature_names),
            'models_used': list(models.keys()) if models else ['simple_scoring']
        },
        'analysis': {
            'prediction_distribution': {
                'blue_wins': analysis['blue_wins_predicted'],
                'red_wins': analysis['red_wins_predicted'],
                'blue_win_rate': analysis['blue_win_rate']
            },
            'confidence_metrics': {
                'average_confidence': analysis['average_confidence'],
                'high_confidence_games': analysis['confidence_distribution']['high_confidence_60_plus'],
                'medium_confidence_games': analysis['confidence_distribution']['medium_confidence_55_60'],
                'low_confidence_games': analysis['confidence_distribution']['low_confidence_below_55']
            }
        },
        'sample_games': {
            'high_confidence_blue': analysis['most_confident_blue'][:10],
            'high_confidence_red': analysis['most_confident_red'][:10],
            'closest_games': analysis['closest_games'][:10]
        }
    }
    
    output_path = Path("data/simulations/simulation_10k_games.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Saved simulation results to: {output_path}")
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"✓ Trained ML models on {len(matches)} real Challenger matches")
    print(f"✓ Generated {n_games:,} random valid team compositions")
    print(f"✓ Predicted outcomes with {analysis['average_confidence']:.1%} average confidence")
    print(f"✓ Model shows {analysis['blue_win_rate']:.1%} vs {1 - analysis['blue_win_rate']:.1%} split")
    print(f"✓ {analysis['confidence_distribution']['high_confidence_60_plus']:,} games with ≥60% confidence")
    print()
    
    if abs(analysis['blue_win_rate'] - 0.5) < 0.05:
        print("✅ Model is well-balanced (within 5% of 50/50)")
    else:
        print(f"⚠ Model shows {abs(analysis['blue_win_rate'] - 0.5):.1%} deviation from balance")
    
    print()


if __name__ == "__main__":
    main()
