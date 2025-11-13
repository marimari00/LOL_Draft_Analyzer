"""
Role-Aware Attribute Synergy Analysis

Analyzes attribute synergies by role pairs to capture contextual importance.
Example: engage_dive + utility_vision on Jungle+Support is different than Top+Jungle.
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set
import math


# Role mappings from Riot API to our system
ROLE_MAP = {
    "TOP": "Top",
    "JUNGLE": "Jungle",
    "MIDDLE": "Middle",
    "BOTTOM": "Bottom",
    "UTILITY": "Support"
}

MIN_SAMPLES = 20  # Lower threshold for role-specific pairs


def load_data():
    """Load match data and champion attributes"""
    matches_path = Path("data/matches/euw1_matches.json")
    champions_path = Path("data/processed/champion_archetypes.json")
    
    with open(matches_path, 'r', encoding='utf-8') as f:
        match_data = json.load(f)
    
    with open(champions_path, 'r', encoding='utf-8') as f:
        champ_data = json.load(f)
    
    # Create champion lookup
    champion_attrs = {}
    if 'assignments' in champ_data:
        for champ_name, champ_info in champ_data['assignments'].items():
            champion_attrs[champ_name] = champ_info.get('attributes', [])
    
    return match_data['matches'], champion_attrs


def get_champion_attributes(champion: str, champion_attrs: Dict) -> List[str]:
    """Get attributes for a champion"""
    return champion_attrs.get(champion, [])


def analyze_role_pair_synergies(matches: List[Dict], champion_attrs: Dict) -> Dict:
    """
    Analyze attribute synergies between specific role pairs.
    
    Tracks: attribute1 + attribute2 + role1 + role2 → win_rate
    """
    # Track synergies by role pair
    synergy_stats = defaultdict(lambda: {"wins": 0, "games": 0})
    
    for match in matches:
        winner = match['winner']
        
        # Analyze both teams
        for team_name in ['blue_team', 'red_team']:
            team_comp = match[team_name]
            won = (team_name == 'blue_team' and winner == 'blue') or \
                  (team_name == 'red_team' and winner == 'red')
            
            # Get all role-attribute pairs for this team
            role_attrs = []
            for role, champion in team_comp.items():
                attrs = get_champion_attributes(champion, champion_attrs)
                role_attrs.append((role, attrs))
            
            # Analyze all role pairs
            for i in range(len(role_attrs)):
                role1, attrs1 = role_attrs[i]
                for j in range(i + 1, len(role_attrs)):
                    role2, attrs2 = role_attrs[j]
                    
                    # Create role pair key (alphabetically sorted)
                    role_pair = tuple(sorted([role1, role2]))
                    
                    # Track all attribute combinations between these roles
                    for attr1 in attrs1:
                        for attr2 in attrs2:
                            # Create attribute pair key (alphabetically sorted)
                            attr_pair = tuple(sorted([attr1, attr2]))
                            
                            # Full key: attribute_pair + role_pair
                            key = f"{attr_pair[0]}+{attr_pair[1]}__{role_pair[0]}-{role_pair[1]}"
                            
                            synergy_stats[key]["games"] += 1
                            if won:
                                synergy_stats[key]["wins"] += 1
    
    # Convert to results format
    results = []
    for key, stats in synergy_stats.items():
        if stats["games"] < MIN_SAMPLES:
            continue
        
        wins = stats["wins"]
        games = stats["games"]
        winrate = wins / games
        
        # Parse key back
        parts = key.split("__")
        attr_pair = parts[0]
        role_pair = parts[1]
        
        results.append({
            "attribute_pair": attr_pair,
            "role_pair": role_pair,
            "wins": wins,
            "games": games,
            "winrate": round(winrate, 3),
            "score": round((winrate - 0.5) * 10, 2)  # Win rate-based scoring
        })
    
    # Sort by win rate deviation from 50%
    results.sort(key=lambda x: abs(x["winrate"] - 0.5), reverse=True)
    
    return results


def analyze_lane_matchups(matches: List[Dict], champion_attrs: Dict) -> Dict:
    """
    Analyze individual lane matchups.
    
    Tracks: blue_lane_attributes vs red_lane_attributes → blue_win_rate
    """
    # Track by lane
    lane_matchups = defaultdict(lambda: defaultdict(lambda: {"blue_wins": 0, "games": 0}))
    
    for match in matches:
        winner = match['winner']
        blue_team = match['blue_team']
        red_team = match['red_team']
        
        # Analyze each lane
        for lane in ['Top', 'Jungle', 'Middle', 'Bottom', 'Support']:
            blue_champ = blue_team.get(lane)
            red_champ = red_team.get(lane)
            
            if not blue_champ or not red_champ:
                continue
            
            blue_attrs = get_champion_attributes(blue_champ, champion_attrs)
            red_attrs = get_champion_attributes(red_champ, champion_attrs)
            
            # Track all attribute matchups in this lane
            for blue_attr in blue_attrs:
                for red_attr in red_attrs:
                    matchup_key = f"{blue_attr} vs {red_attr}"
                    lane_matchups[lane][matchup_key]["games"] += 1
                    if winner == 'blue':
                        lane_matchups[lane][matchup_key]["blue_wins"] += 1
    
    # Convert to results format
    results = {}
    for lane, matchups in lane_matchups.items():
        lane_results = []
        for matchup_key, stats in matchups.items():
            if stats["games"] < MIN_SAMPLES:
                continue
            
            blue_wins = stats["blue_wins"]
            games = stats["games"]
            blue_winrate = blue_wins / games
            advantage = blue_winrate - 0.5
            
            lane_results.append({
                "matchup": matchup_key,
                "blue_wins": blue_wins,
                "games": games,
                "blue_winrate": round(blue_winrate, 3),
                "advantage": round(advantage, 3),
                "score": round(advantage * 10, 2)
            })
        
        # Sort by absolute advantage
        lane_results.sort(key=lambda x: abs(x["advantage"]), reverse=True)
        results[lane] = lane_results
    
    return results


def calculate_weighted_scores(matches: List[Dict], champion_attrs: Dict) -> Dict:
    """
    Calculate win rate-based weighted scores for all attribute relationships.
    
    Uses actual win rates as weights instead of fixed +2/-2 scores.
    """
    # Synergy pairs within teams
    synergy_scores = defaultdict(lambda: {"wins": 0, "games": 0})
    
    # Counter matchups between teams
    counter_scores = defaultdict(lambda: {"blue_wins": 0, "games": 0})
    
    for match in matches:
        winner = match['winner']
        blue_attrs = set()
        red_attrs = set()
        
        # Get team attributes
        for champion in match['blue_team'].values():
            blue_attrs.update(get_champion_attributes(champion, champion_attrs))
        for champion in match['red_team'].values():
            red_attrs.update(get_champion_attributes(champion, champion_attrs))
        
        # Track synergies
        for team_name, attrs, won in [('blue', blue_attrs, winner == 'blue'), 
                                       ('red', red_attrs, winner == 'red')]:
            attr_list = sorted(attrs)
            for i in range(len(attr_list)):
                for j in range(i + 1, len(attr_list)):
                    pair = f"{attr_list[i]}+{attr_list[j]}"
                    synergy_scores[pair]["games"] += 1
                    if won:
                        synergy_scores[pair]["wins"] += 1
        
        # Track counters
        for blue_attr in blue_attrs:
            for red_attr in red_attrs:
                matchup = f"{blue_attr}>{red_attr}"
                counter_scores[matchup]["games"] += 1
                if winner == 'blue':
                    counter_scores[matchup]["blue_wins"] += 1
    
    # Calculate weighted scores
    synergy_weights = {}
    for pair, stats in synergy_scores.items():
        if stats["games"] >= MIN_SAMPLES:
            winrate = stats["wins"] / stats["games"]
            # Map 50% → 0, 55% → 0.5, 60% → 1.0, 45% → -0.5, etc.
            weight = (winrate - 0.5) * 10
            synergy_weights[pair] = {
                "winrate": round(winrate, 3),
                "games": stats["games"],
                "weight": round(weight, 2)
            }
    
    counter_weights = {}
    for matchup, stats in counter_scores.items():
        if stats["games"] >= MIN_SAMPLES:
            blue_winrate = stats["blue_wins"] / stats["games"]
            advantage = blue_winrate - 0.5
            # Map 50% → 0, 60% → 1.0, 70% → 2.0, etc.
            weight = advantage * 10
            counter_weights[matchup] = {
                "blue_winrate": round(blue_winrate, 3),
                "games": stats["games"],
                "weight": round(weight, 2)
            }
    
    return {
        "synergies": synergy_weights,
        "counters": counter_weights
    }


def predict_with_role_awareness(matches: List[Dict], champion_attrs: Dict,
                                role_synergies: List[Dict], 
                                weighted_scores: Dict,
                                lane_matchups: Dict) -> Dict:
    """
    Predict match outcomes using role-aware features.
    """
    correct = 0
    total = len(matches)
    
    # Create lookup dictionaries
    role_synergy_lookup = {}
    for syn in role_synergies:
        key = f"{syn['attribute_pair']}__{syn['role_pair']}"
        role_synergy_lookup[key] = syn['score']
    
    synergy_weights = weighted_scores['synergies']
    counter_weights = weighted_scores['counters']
    
    for match in matches:
        blue_team = match['blue_team']
        red_team = match['red_team']
        
        # Calculate role-aware synergy scores
        blue_synergy = 0
        red_synergy = 0
        
        # Blue team role synergies
        blue_role_attrs = []
        for role, champion in blue_team.items():
            attrs = get_champion_attributes(champion, champion_attrs)
            blue_role_attrs.append((role, attrs))
        
        for i in range(len(blue_role_attrs)):
            role1, attrs1 = blue_role_attrs[i]
            for j in range(i + 1, len(blue_role_attrs)):
                role2, attrs2 = blue_role_attrs[j]
                role_pair = tuple(sorted([role1, role2]))
                
                for attr1 in attrs1:
                    for attr2 in attrs2:
                        attr_pair = tuple(sorted([attr1, attr2]))
                        key = f"{attr_pair[0]}+{attr_pair[1]}__{role_pair[0]}-{role_pair[1]}"
                        
                        if key in role_synergy_lookup:
                            blue_synergy += role_synergy_lookup[key]
        
        # Red team role synergies
        red_role_attrs = []
        for role, champion in red_team.items():
            attrs = get_champion_attributes(champion, champion_attrs)
            red_role_attrs.append((role, attrs))
        
        for i in range(len(red_role_attrs)):
            role1, attrs1 = red_role_attrs[i]
            for j in range(i + 1, len(red_role_attrs)):
                role2, attrs2 = red_role_attrs[j]
                role_pair = tuple(sorted([role1, role2]))
                
                for attr1 in attrs1:
                    for attr2 in attrs2:
                        attr_pair = tuple(sorted([attr1, attr2]))
                        key = f"{attr_pair[0]}+{attr_pair[1]}__{role_pair[0]}-{role_pair[1]}"
                        
                        if key in role_synergy_lookup:
                            red_synergy += role_synergy_lookup[key]
        
        # Calculate counter advantages with weighted scores
        counter_score = 0
        blue_attrs = set()
        red_attrs = set()
        
        for champion in blue_team.values():
            blue_attrs.update(get_champion_attributes(champion, champion_attrs))
        for champion in red_team.values():
            red_attrs.update(get_champion_attributes(champion, champion_attrs))
        
        for blue_attr in blue_attrs:
            for red_attr in red_attrs:
                matchup_key = f"{blue_attr}>{red_attr}"
                if matchup_key in counter_weights:
                    counter_score += counter_weights[matchup_key]['weight']
                
                reverse_key = f"{red_attr}>{blue_attr}"
                if reverse_key in counter_weights:
                    counter_score -= counter_weights[reverse_key]['weight']
        
        # Calculate lane advantages
        lane_advantage = 0
        for lane in ['Top', 'Jungle', 'Middle', 'Bottom', 'Support']:
            blue_champ = blue_team.get(lane)
            red_champ = red_team.get(lane)
            
            if not blue_champ or not red_champ:
                continue
            
            blue_lane_attrs = get_champion_attributes(blue_champ, champion_attrs)
            red_lane_attrs = get_champion_attributes(red_champ, champion_attrs)
            
            # Find matchups in our lane data
            if lane in lane_matchups:
                for matchup_data in lane_matchups[lane]:
                    matchup = matchup_data['matchup']
                    parts = matchup.split(' vs ')
                    if len(parts) == 2:
                        blue_attr, red_attr = parts
                        if blue_attr in blue_lane_attrs and red_attr in red_lane_attrs:
                            lane_advantage += matchup_data['score']
        
        # Combined prediction
        synergy_diff = blue_synergy - red_synergy
        total_score = synergy_diff + counter_score + lane_advantage
        
        predicted_blue = total_score > 0
        actual_blue = match['winner'] == 'blue'
        
        if predicted_blue == actual_blue:
            correct += 1
    
    accuracy = correct / total if total > 0 else 0
    
    return {
        "total_matches": total,
        "correct_predictions": correct,
        "accuracy": round(accuracy, 3),
        "baseline": 0.5,
        "improvement": round(accuracy - 0.5, 3)
    }


def main():
    print("=" * 80)
    print("ROLE-AWARE ATTRIBUTE SYNERGY ANALYSIS")
    print("=" * 80)
    print()
    
    # Load data
    print("Loading data...")
    matches, champion_attrs = load_data()
    print(f"✓ Loaded {len(matches)} matches")
    print(f"✓ Loaded {len(champion_attrs)} champions")
    print()
    
    # Analyze role-pair synergies
    print("Analyzing role-pair synergies...")
    role_synergies = analyze_role_pair_synergies(matches, champion_attrs)
    print(f"✓ Found {len(role_synergies)} role-specific synergies (20+ games)")
    print()
    
    print("Top 15 Role-Specific Synergies:")
    print("-" * 80)
    for i, syn in enumerate(role_synergies[:15], 1):
        print(f"{i}. {syn['attribute_pair']} on {syn['role_pair']}")
        print(f"   Win Rate: {syn['winrate']:.1%}, Games: {syn['games']}, Score: {syn['score']}")
        print()
    
    # Analyze lane matchups
    print("=" * 80)
    print("Analyzing lane matchups...")
    lane_matchups = analyze_lane_matchups(matches, champion_attrs)
    
    for lane in ['Top', 'Jungle', 'Middle', 'Bottom', 'Support']:
        if lane in lane_matchups:
            print(f"\n{lane} Lane - Top 5 Matchups:")
            print("-" * 60)
            for i, matchup in enumerate(lane_matchups[lane][:5], 1):
                direction = matchup['matchup'].split(' vs ')
                adv = matchup['advantage']
                winner = direction[0] if adv > 0 else direction[1]
                print(f"{i}. {winner} advantage: {abs(adv):.1%}")
                print(f"   {matchup['matchup']}")
                print(f"   Games: {matchup['games']}, Score: {matchup['score']}")
    
    # Calculate weighted scores
    print("\n" + "=" * 80)
    print("Calculating win rate-based weighted scores...")
    weighted_scores = calculate_weighted_scores(matches, champion_attrs)
    print(f"✓ {len(weighted_scores['synergies'])} synergies with weights")
    print(f"✓ {len(weighted_scores['counters'])} counters with weights")
    print()
    
    # Show top weighted synergies
    print("Top 10 Weighted Synergies:")
    print("-" * 60)
    sorted_synergies = sorted(weighted_scores['synergies'].items(), 
                             key=lambda x: abs(x[1]['weight']), reverse=True)
    for i, (pair, data) in enumerate(sorted_synergies[:10], 1):
        print(f"{i}. {pair}")
        print(f"   Win Rate: {data['winrate']:.1%}, Games: {data['games']}, Weight: {data['weight']}")
    
    print("\nTop 10 Weighted Counters:")
    print("-" * 60)
    sorted_counters = sorted(weighted_scores['counters'].items(),
                            key=lambda x: abs(x[1]['weight']), reverse=True)
    for i, (matchup, data) in enumerate(sorted_counters[:10], 1):
        parts = matchup.split('>')
        print(f"{i}. {parts[0]} > {parts[1]}")
        print(f"   Blue WR: {data['blue_winrate']:.1%}, Games: {data['games']}, Weight: {data['weight']}")
    
    # Predict with role awareness
    print("\n" + "=" * 80)
    print("PREDICTIVE MODEL WITH ROLE AWARENESS")
    print("=" * 80)
    prediction_results = predict_with_role_awareness(
        matches, champion_attrs, role_synergies, weighted_scores, lane_matchups
    )
    
    print(f"\nTotal matches: {prediction_results['total_matches']}")
    print(f"Correct predictions: {prediction_results['correct_predictions']}")
    print(f"\n{'='*80}")
    print(f"MODEL ACCURACY: {prediction_results['accuracy']:.1%}")
    print(f"{'='*80}")
    print(f"Baseline (random): {prediction_results['baseline']:.1%}")
    print(f"Improvement: +{prediction_results['improvement']:.1%} (+{prediction_results['improvement']*100:.1f}%)")
    print()
    
    # Save results
    output = {
        "metadata": {
            "matches_analyzed": len(matches),
            "min_samples": MIN_SAMPLES,
            "features": ["role_pair_synergies", "lane_matchups", "weighted_scores"]
        },
        "role_synergies": role_synergies[:50],  # Top 50
        "lane_matchups": {lane: matchups[:20] for lane, matchups in lane_matchups.items()},
        "weighted_scores": {
            "synergies": dict(sorted_synergies[:100]),
            "counters": dict(sorted_counters[:100])
        },
        "prediction_results": prediction_results
    }
    
    output_path = Path("data/processed/role_aware_relationships.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Saved role-aware analysis to: {output_path}")
    print()
    
    # Compare with baseline
    baseline_accuracy = 0.576  # From statistical_analysis.py
    improvement = prediction_results['accuracy'] - baseline_accuracy
    
    print("=" * 80)
    print("IMPROVEMENT OVER BASELINE")
    print("=" * 80)
    print(f"Previous model (attribute-only): {baseline_accuracy:.1%}")
    print(f"New model (role-aware): {prediction_results['accuracy']:.1%}")
    print(f"Improvement: +{improvement:.1%} (+{improvement*100:.1f}%)")
    print()
    
    if prediction_results['accuracy'] >= 0.65:
        print("🎯 TARGET ACHIEVED! Model accuracy ≥ 65%")
    else:
        remaining = 0.65 - prediction_results['accuracy']
        print(f"Progress toward 65% target: {remaining:.1%} remaining")
    print()


if __name__ == "__main__":
    main()
