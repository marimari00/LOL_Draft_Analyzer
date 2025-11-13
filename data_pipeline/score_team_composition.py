"""Score team compositions based on synergy and counter relationships.

This module provides functions to evaluate draft picks by analyzing:
1. Internal team synergy (how well champions work together)
2. Counter advantage vs enemy team (favorable matchups)
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple


def load_relationships() -> Tuple[Dict, Dict]:
    """Load synergy and counter matrices."""
    rel_path = Path('data/processed/archetype_relationships.json')
    with open(rel_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['synergies'], data['counters']


def load_champion_archetypes() -> Dict:
    """Load champion archetype assignments."""
    arch_path = Path('data/processed/champion_archetypes.json')
    with open(arch_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['assignments']


def get_archetype(champion_name: str, archetypes: Dict) -> str:
    """Get primary archetype for a champion."""
    if champion_name not in archetypes:
        return None
    return archetypes[champion_name]['primary_archetype']


def score_team_synergy(team_archetypes: List[str], synergy_matrix: Dict) -> float:
    """Calculate total synergy score for a team.
    
    Args:
        team_archetypes: List of archetype names (e.g., ['marksman', 'engage_tank'])
        synergy_matrix: Dict mapping archetype pairs to synergy scores
        
    Returns:
        Total synergy score (sum of all pairwise synergies)
    """
    if len(team_archetypes) < 2:
        return 0.0
    
    total_score = 0.0
    pair_count = 0
    
    for i, arch1 in enumerate(team_archetypes):
        for arch2 in team_archetypes[i+1:]:
            if arch1 in synergy_matrix and arch2 in synergy_matrix[arch1]:
                total_score += synergy_matrix[arch1][arch2]
                pair_count += 1
    
    # Return average synergy per pair
    return total_score / pair_count if pair_count > 0 else 0.0


def score_counter_advantage(our_archetypes: List[str], 
                            enemy_archetypes: List[str],
                            counter_matrix: Dict) -> float:
    """Calculate counter advantage vs enemy team.
    
    Args:
        our_archetypes: Our team's archetype list
        enemy_archetypes: Enemy team's archetype list
        counter_matrix: Dict mapping archetype matchups to counter scores
        
    Returns:
        Average counter advantage (positive = we counter them, negative = they counter us)
    """
    if not our_archetypes or not enemy_archetypes:
        return 0.0
    
    total_score = 0.0
    matchup_count = 0
    
    for our_arch in our_archetypes:
        for enemy_arch in enemy_archetypes:
            if our_arch in counter_matrix and enemy_arch in counter_matrix[our_arch]:
                total_score += counter_matrix[our_arch][enemy_arch]
                matchup_count += 1
    
    # Return average counter advantage per matchup
    return total_score / matchup_count if matchup_count > 0 else 0.0


def score_pick(candidate_champion: str,
               our_team: List[str],
               enemy_team: List[str],
               archetypes: Dict,
               synergy_matrix: Dict,
               counter_matrix: Dict,
               synergy_weight: float = 0.6,
               counter_weight: float = 0.4) -> Dict:
    """Score a potential champion pick.
    
    Args:
        candidate_champion: Champion name to evaluate
        our_team: List of champion names already on our team
        enemy_team: List of champion names on enemy team
        archetypes: Dict of champion archetype assignments
        synergy_matrix: Synergy relationships
        counter_matrix: Counter relationships
        synergy_weight: Weight for synergy score (default 0.6)
        counter_weight: Weight for counter score (default 0.4)
        
    Returns:
        Dict with scores and breakdown
    """
    # Get archetypes
    candidate_arch = get_archetype(candidate_champion, archetypes)
    if not candidate_arch:
        return {
            'champion': candidate_champion,
            'total_score': 0.0,
            'synergy_score': 0.0,
            'counter_score': 0.0,
            'error': 'Champion not found in database'
        }
    
    our_archetypes = [get_archetype(c, archetypes) for c in our_team]
    our_archetypes = [a for a in our_archetypes if a]  # Filter None
    our_archetypes_with_pick = our_archetypes + [candidate_arch]
    
    enemy_archetypes = [get_archetype(c, archetypes) for c in enemy_team]
    enemy_archetypes = [a for a in enemy_archetypes if a]  # Filter None
    
    # Calculate scores
    synergy_score = score_team_synergy(our_archetypes_with_pick, synergy_matrix)
    counter_score = score_counter_advantage([candidate_arch], enemy_archetypes, counter_matrix)
    
    # Weighted total
    total_score = (synergy_weight * synergy_score + 
                   counter_weight * counter_score)
    
    return {
        'champion': candidate_champion,
        'archetype': candidate_arch,
        'total_score': round(total_score, 3),
        'synergy_score': round(synergy_score, 3),
        'counter_score': round(counter_score, 3),
        'weights': {
            'synergy': synergy_weight,
            'counter': counter_weight
        }
    }


def recommend_picks(our_team: List[str],
                   enemy_team: List[str],
                   available_champions: List[str] = None,
                   top_n: int = 10,
                   synergy_weight: float = 0.6,
                   counter_weight: float = 0.4) -> List[Dict]:
    """Recommend champion picks based on draft state.
    
    Args:
        our_team: List of champion names already picked
        enemy_team: List of enemy champion names
        available_champions: List of champions to consider (None = all)
        top_n: Number of recommendations to return
        synergy_weight: Weight for team synergy (default 0.6)
        counter_weight: Weight for countering enemy (default 0.4)
        
    Returns:
        List of scored picks, sorted by total_score descending
    """
    # Load data
    synergy_matrix, counter_matrix = load_relationships()
    archetypes = load_champion_archetypes()
    
    # Default to all champions if not specified
    if available_champions is None:
        available_champions = list(archetypes.keys())
    
    # Filter out already picked champions
    picked_champions = set(our_team + enemy_team)
    available_champions = [c for c in available_champions if c not in picked_champions]
    
    # Score each candidate
    scores = []
    for champion in available_champions:
        score_result = score_pick(
            champion, our_team, enemy_team,
            archetypes, synergy_matrix, counter_matrix,
            synergy_weight, counter_weight
        )
        if 'error' not in score_result:
            scores.append(score_result)
    
    # Sort by total score descending
    scores.sort(key=lambda x: x['total_score'], reverse=True)
    
    return scores[:top_n]


def analyze_team_composition(team_champions: List[str]) -> Dict:
    """Analyze a complete team composition.
    
    Args:
        team_champions: List of 5 champion names
        
    Returns:
        Dict with composition analysis
    """
    archetypes = load_champion_archetypes()
    synergy_matrix, _ = load_relationships()
    
    # Get archetypes
    team_archetypes = [get_archetype(c, archetypes) for c in team_champions]
    team_archetypes = [a for a in team_archetypes if a]
    
    # Calculate synergy
    synergy_score = score_team_synergy(team_archetypes, synergy_matrix)
    
    # Identify composition type
    arch_counts = {}
    for arch in team_archetypes:
        arch_counts[arch] = arch_counts.get(arch, 0) + 1
    
    comp_type = identify_composition_type(team_archetypes)
    
    return {
        'champions': team_champions,
        'archetypes': team_archetypes,
        'archetype_distribution': arch_counts,
        'synergy_score': round(synergy_score, 3),
        'composition_type': comp_type
    }


def identify_composition_type(archetypes: List[str]) -> str:
    """Identify team composition archetype.
    
    Args:
        archetypes: List of champion archetypes
        
    Returns:
        Composition type name
    """
    arch_set = set(archetypes)
    
    # Front-to-back
    if ('engage_tank' in arch_set or 'warden' in arch_set) and 'marksman' in arch_set:
        return "Front-to-Back (Teamfight)"
    
    # Dive
    if ('diver' in arch_set or 'burst_assassin' in arch_set) and 'engage_tank' in arch_set:
        return "Dive Composition"
    
    # Poke
    if 'artillery_mage' in arch_set and ('catcher' in arch_set or 'enchanter' in arch_set):
        return "Poke Composition"
    
    # Split push
    if 'skirmisher' in arch_set or 'juggernaut' in arch_set:
        if 'specialist' in arch_set or 'battle_mage' in arch_set:
            return "Split Push Composition"
    
    # Pick
    if 'catcher' in arch_set and ('burst_assassin' in arch_set or 'burst_mage' in arch_set):
        return "Pick Composition"
    
    # Default
    return "Balanced Composition"


if __name__ == '__main__':
    # Example usage
    print("="*70)
    print("TEAM COMPOSITION SCORING - EXAMPLES")
    print("="*70)
    
    # Example 1: Front-to-back composition
    print("\n1. Front-to-Back Composition")
    print("-" * 70)
    our_team = ['Leona', 'Jinx', 'Lulu', 'Orianna']
    enemy_team = ['Darius', 'Zed', 'Xerath']
    
    print(f"Our team: {', '.join(our_team)}")
    print(f"Enemy team: {', '.join(enemy_team)}")
    print(f"\nTop 5 recommendations:")
    
    recommendations = recommend_picks(our_team, enemy_team, top_n=5)
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec['champion']:15s} ({rec['archetype']:15s}) | "
              f"Total: {rec['total_score']:5.2f} | "
              f"Synergy: {rec['synergy_score']:5.2f} | "
              f"Counter: {rec['counter_score']:5.2f}")
    
    # Example 2: Dive composition
    print("\n\n2. Dive Composition")
    print("-" * 70)
    our_team = ['Vi', 'Zed', 'Yasuo']
    enemy_team = ['Caitlyn', 'Lux', 'Janna']
    
    print(f"Our team: {', '.join(our_team)}")
    print(f"Enemy team: {', '.join(enemy_team)}")
    print(f"\nTop 5 recommendations:")
    
    recommendations = recommend_picks(our_team, enemy_team, top_n=5)
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec['champion']:15s} ({rec['archetype']:15s}) | "
              f"Total: {rec['total_score']:5.2f} | "
              f"Synergy: {rec['synergy_score']:5.2f} | "
              f"Counter: {rec['counter_score']:5.2f}")
    
    # Example 3: Team analysis
    print("\n\n3. Team Composition Analysis")
    print("-" * 70)
    team = ['Leona', 'Jinx', 'Lulu', 'Orianna', 'Braum']
    analysis = analyze_team_composition(team)
    
    print(f"Team: {', '.join(analysis['champions'])}")
    print(f"Archetypes: {', '.join(analysis['archetypes'])}")
    print(f"Composition Type: {analysis['composition_type']}")
    print(f"Synergy Score: {analysis['synergy_score']:.3f}")
    print(f"Archetype Distribution: {analysis['archetype_distribution']}")
