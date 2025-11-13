"""Analyze match data to discover real archetype synergies.

This analyzes actual team compositions and win rates to determine:
1. Which archetype combinations win more often (positive synergy)
2. Which archetype matchups favor one side (counter relationships)
3. Validation of theoretical synergy matrix

This is EMPIRICAL data - no assumptions, just observed patterns.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_match_data(matches_file: str) -> List[Dict]:
    """Load match data from JSON file."""
    with open(matches_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['matches']


def load_champion_archetypes() -> Dict:
    """Load champion archetype assignments."""
    with open('data/processed/champion_archetypes.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['assignments']


def get_team_archetypes(team: Dict, champions: Dict) -> List[str]:
    """Get list of archetypes for a team composition.
    
    Args:
        team: Dict mapping position to champion name
        champions: Champion database with archetypes
        
    Returns:
        List of archetype names
    """
    archetypes = []
    for position, champion in team.items():
        if champion in champions:
            arch = champions[champion]['primary_archetype']
            archetypes.append(arch)
    return archetypes


def calculate_archetype_pair_winrates(matches: List[Dict], 
                                      champions: Dict) -> Dict[Tuple[str, str], Dict]:
    """Calculate win rates for archetype pairs on same team.
    
    Args:
        matches: List of match data
        champions: Champion database
        
    Returns:
        Dict mapping (arch1, arch2) pairs to {wins, games, winrate}
    """
    pair_stats = defaultdict(lambda: {'wins': 0, 'games': 0})
    
    for match in matches:
        winner = match.get('winner')
        if not winner:
            continue
        
        # Analyze blue team
        blue_archs = get_team_archetypes(match['blue_team'], champions)
        for i, arch1 in enumerate(blue_archs):
            for arch2 in blue_archs[i+1:]:
                pair = tuple(sorted([arch1, arch2]))
                pair_stats[pair]['games'] += 1
                if winner == 'blue':
                    pair_stats[pair]['wins'] += 1
        
        # Analyze red team
        red_archs = get_team_archetypes(match['red_team'], champions)
        for i, arch1 in enumerate(red_archs):
            for arch2 in red_archs[i+1:]:
                pair = tuple(sorted([arch1, arch2]))
                pair_stats[pair]['games'] += 1
                if winner == 'red':
                    pair_stats[pair]['wins'] += 1
    
    # Calculate win rates
    for pair in pair_stats:
        stats = pair_stats[pair]
        stats['winrate'] = stats['wins'] / stats['games'] if stats['games'] > 0 else 0.0
    
    return dict(pair_stats)


def calculate_archetype_matchup_advantage(matches: List[Dict],
                                          champions: Dict) -> Dict[Tuple[str, str], Dict]:
    """Calculate counter relationships between archetypes.
    
    For each matchup (arch1 vs arch2), track:
    - How often arch1's team wins when facing arch2
    - This reveals counter relationships
    
    Args:
        matches: List of match data
        champions: Champion database
        
    Returns:
        Dict mapping (arch1, arch2) to {wins, games, advantage}
    """
    matchup_stats = defaultdict(lambda: {'wins': 0, 'games': 0})
    
    for match in matches:
        winner = match.get('winner')
        if not winner:
            continue
        
        blue_archs = get_team_archetypes(match['blue_team'], champions)
        red_archs = get_team_archetypes(match['red_team'], champions)
        
        # For each blue archetype vs each red archetype
        for blue_arch in blue_archs:
            for red_arch in red_archs:
                matchup = (blue_arch, red_arch)
                matchup_stats[matchup]['games'] += 1
                if winner == 'blue':
                    matchup_stats[matchup]['wins'] += 1
    
    # Calculate advantage (positive = arch1 counters arch2, negative = countered by arch2)
    for matchup in matchup_stats:
        stats = matchup_stats[matchup]
        winrate = stats['wins'] / stats['games'] if stats['games'] > 0 else 0.5
        # Convert to advantage score: 60% WR = +0.2, 40% WR = -0.2
        stats['advantage'] = (winrate - 0.5) * 2
        stats['winrate'] = winrate
    
    return dict(matchup_stats)


def discover_synergies_from_data(pair_winrates: Dict, 
                                 min_games: int = 50) -> Dict[Tuple[str, str], int]:
    """Convert win rate data to synergy scores.
    
    Args:
        pair_winrates: Archetype pair win rates
        min_games: Minimum games required for valid data
        
    Returns:
        Dict mapping (arch1, arch2) to synergy score (-2 to +2)
    """
    synergies = {}
    
    # Expected baseline is 50% win rate (random)
    # Strong synergy: 55%+ win rate
    # Weak synergy: 45%- win rate
    
    for pair, stats in pair_winrates.items():
        if stats['games'] < min_games:
            continue
        
        winrate = stats['winrate']
        
        # Convert to synergy score
        if winrate >= 0.55:
            synergy = 2  # Strong positive synergy
        elif winrate >= 0.52:
            synergy = 1  # Moderate positive synergy
        elif winrate <= 0.45:
            synergy = -2  # Strong anti-synergy
        elif winrate <= 0.48:
            synergy = -1  # Moderate anti-synergy
        else:
            synergy = 0  # Neutral
        
        synergies[pair] = synergy
    
    return synergies


def discover_counters_from_data(matchup_advantages: Dict,
                                min_games: int = 50) -> Dict[Tuple[str, str], int]:
    """Convert matchup advantage to counter scores.
    
    Args:
        matchup_advantages: Archetype matchup advantages
        min_games: Minimum games required for valid data
        
    Returns:
        Dict mapping (arch1, arch2) to counter score (-2 to +2)
    """
    counters = {}
    
    # Advantage > 0.2 = hard counter (+2)
    # Advantage > 0.1 = soft counter (+1)
    # Advantage < -0.2 = hard countered (-2)
    # Advantage < -0.1 = soft countered (-1)
    
    for matchup, stats in matchup_advantages.items():
        if stats['games'] < min_games:
            continue
        
        advantage = stats['advantage']
        
        if advantage >= 0.2:
            counter = 2  # Hard counter
        elif advantage >= 0.1:
            counter = 1  # Soft counter
        elif advantage <= -0.2:
            counter = -2  # Hard countered
        elif advantage <= -0.1:
            counter = -1  # Soft countered
        else:
            counter = 0  # Neutral
        
        counters[matchup] = counter
    
    return counters


def main():
    print("="*70)
    print("EMPIRICAL SYNERGY DISCOVERY")
    print("="*70)
    print("\nAnalyzing match data to discover REAL archetype interactions...")
    
    # Load data from real matches
    matches_file = 'data/matches/euw1_matches.json'
    if not Path(matches_file).exists():
        print(f"\n✗ No match data found at {matches_file}")
        print("  Run: python data_extraction/fetch_match_data.py --region euw1 --count 100")
        sys.exit(1)
    
    matches = load_match_data(matches_file)
    champions = load_champion_archetypes()
    
    print(f"\nLoaded {len(matches)} matches")
    print(f"Loaded {len(champions)} champions")
    
    # Analyze synergies
    print("\n" + "-"*70)
    print("ANALYZING ARCHETYPE PAIR WIN RATES...")
    print("-"*70)
    
    pair_winrates = calculate_archetype_pair_winrates(matches, champions)
    
    # Show top synergies
    sorted_pairs = sorted(pair_winrates.items(), 
                         key=lambda x: (x[1]['games'], x[1]['winrate']), 
                         reverse=True)
    
    print("\nTop 20 most common archetype pairs:")
    for i, (pair, stats) in enumerate(sorted_pairs[:20], 1):
        arch1, arch2 = pair
        wr = stats['winrate'] * 100
        status = "✓" if stats['winrate'] > 0.52 else "✗" if stats['winrate'] < 0.48 else "="
        print(f"{i:2d}. {arch1:15s} + {arch2:15s} | "
              f"{stats['games']:4d} games | {wr:5.1f}% WR | {status}")
    
    # Analyze counters
    print("\n" + "-"*70)
    print("ANALYZING ARCHETYPE MATCHUP ADVANTAGES...")
    print("-"*70)
    
    matchup_advantages = calculate_archetype_matchup_advantage(matches, champions)
    
    # Show strongest counter relationships
    sorted_matchups = sorted(matchup_advantages.items(),
                            key=lambda x: (x[1]['games'], abs(x[1]['advantage'])),
                            reverse=True)
    
    print("\nTop 20 strongest counter relationships:")
    for i, (matchup, stats) in enumerate(sorted_matchups[:20], 1):
        arch1, arch2 = matchup
        adv = stats['advantage']
        wr = stats['winrate'] * 100
        
        if adv > 0.1:
            direction = "counters"
            status = "✓"
        elif adv < -0.1:
            direction = "countered by"
            status = "✗"
        else:
            direction = "vs"
            status = "="
        
        print(f"{i:2d}. {arch1:15s} {direction:12s} {arch2:15s} | "
              f"{stats['games']:4d} games | {wr:5.1f}% WR | Adv: {adv:+.2f} | {status}")
    
    # Discover data-driven synergies
    print("\n" + "-"*70)
    print("DISCOVERED SYNERGIES (min 30 games):")
    print("-"*70)
    
    discovered_synergies = discover_synergies_from_data(pair_winrates, min_games=30)
    
    strong_synergies = [(p, s) for p, s in discovered_synergies.items() if s == 2]
    anti_synergies = [(p, s) for p, s in discovered_synergies.items() if s == -2]
    
    print(f"\nStrong positive synergies (+2): {len(strong_synergies)}")
    for pair, score in strong_synergies[:10]:
        stats = pair_winrates[pair]
        print(f"  {pair[0]:15s} + {pair[1]:15s} | {stats['winrate']*100:5.1f}% WR | {stats['games']:3d} games")
    
    print(f"\nStrong anti-synergies (-2): {len(anti_synergies)}")
    for pair, score in anti_synergies[:10]:
        stats = pair_winrates[pair]
        print(f"  {pair[0]:15s} + {pair[1]:15s} | {stats['winrate']*100:5.1f}% WR | {stats['games']:3d} games")
    
    # Discover data-driven counters
    print("\n" + "-"*70)
    print("DISCOVERED COUNTERS (min 30 games):")
    print("-"*70)
    
    discovered_counters = discover_counters_from_data(matchup_advantages, min_games=30)
    
    hard_counters = [(m, c) for m, c in discovered_counters.items() if c == 2]
    hard_countered = [(m, c) for m, c in discovered_counters.items() if c == -2]
    
    print(f"\nHard counters (+2): {len(hard_counters)}")
    for matchup, score in hard_counters[:10]:
        stats = matchup_advantages[matchup]
        print(f"  {matchup[0]:15s} > {matchup[1]:15s} | {stats['winrate']*100:5.1f}% WR | {stats['games']:3d} games")
    
    print(f"\nHard countered (-2): {len(hard_countered)}")
    for matchup, score in hard_countered[:10]:
        stats = matchup_advantages[matchup]
        print(f"  {matchup[0]:15s} < {matchup[1]:15s} | {stats['winrate']*100:5.1f}% WR | {stats['games']:3d} games")
    
    # Save results
    output = {
        'metadata': {
            'matches_analyzed': len(matches),
            'min_games_threshold': 30,
            'analysis_date': '2025-11-13'
        },
        'synergies': {
            f"{p[0]}+{p[1]}": {'score': s, 'winrate': pair_winrates[p]['winrate'], 'games': pair_winrates[p]['games']}
            for p, s in discovered_synergies.items()
        },
        'counters': {
            f"{m[0]}>{m[1]}": {'score': c, 'advantage': matchup_advantages[m]['advantage'], 'games': matchup_advantages[m]['games']}
            for m, c in discovered_counters.items()
        }
    }
    
    output_path = 'data/processed/empirical_relationships.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Saved empirical data to: {output_path}")
    print("\nNext: Compare with theoretical synergy matrix to validate/refine")


if __name__ == '__main__':
    main()
