"""Analyze synergies at the attribute level instead of archetype level.

This discovers WHY certain combinations work by looking at underlying properties:
- damage_physical + damage_magic = mixed damage (harder to itemize against)
- mobility_high + engage_dive = effective backline access
- cc_hard + damage_burst = lockdown combos
- survive_range + utility_peel = protect-the-carry compositions

Provides much more granular and transferable insights than archetype-only analysis.
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


def load_champion_data() -> Dict:
    """Load champion data with attributes."""
    with open('data/processed/champion_archetypes.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['assignments']


def get_team_attributes(team: Dict, champions: Dict) -> List[str]:
    """Get list of all attributes present in a team composition.
    
    Args:
        team: Dict mapping position to champion name
        champions: Champion database with attributes
        
    Returns:
        List of all attribute names (with duplicates for emphasis)
    """
    attributes = []
    for position, champion in team.items():
        if champion in champions and 'attributes' in champions[champion]:
            attributes.extend(champions[champion]['attributes'])
    return attributes


def calculate_attribute_pair_winrates(matches: List[Dict],
                                      champions: Dict) -> Dict[Tuple[str, str], Dict]:
    """Calculate win rates for attribute pairs on same team.
    
    This reveals which fundamental properties synergize.
    
    Args:
        matches: List of match data
        champions: Champion database
        
    Returns:
        Dict mapping (attr1, attr2) pairs to {wins, games, winrate}
    """
    pair_stats = defaultdict(lambda: {'wins': 0, 'games': 0})
    
    for match in matches:
        winner = match.get('winner')
        if not winner:
            continue
        
        # Analyze blue team
        blue_attrs = get_team_attributes(match['blue_team'], champions)
        # Get unique attribute pairs (don't count same attr twice)
        unique_attrs = list(set(blue_attrs))
        for i, attr1 in enumerate(unique_attrs):
            for attr2 in unique_attrs[i+1:]:
                pair = tuple(sorted([attr1, attr2]))
                pair_stats[pair]['games'] += 1
                if winner == 'blue':
                    pair_stats[pair]['wins'] += 1
        
        # Analyze red team
        red_attrs = get_team_attributes(match['red_team'], champions)
        unique_attrs = list(set(red_attrs))
        for i, attr1 in enumerate(unique_attrs):
            for attr2 in unique_attrs[i+1:]:
                pair = tuple(sorted([attr1, attr2]))
                pair_stats[pair]['games'] += 1
                if winner == 'red':
                    pair_stats[pair]['wins'] += 1
    
    # Calculate win rates
    for pair in pair_stats:
        stats = pair_stats[pair]
        stats['winrate'] = stats['wins'] / stats['games'] if stats['games'] > 0 else 0.0
    
    return dict(pair_stats)


def calculate_attribute_matchup_advantage(matches: List[Dict],
                                          champions: Dict) -> Dict[Tuple[str, str], Dict]:
    """Calculate advantage when one attribute faces another.
    
    This reveals which properties counter others.
    
    Args:
        matches: List of match data
        champions: Champion database
        
    Returns:
        Dict mapping (attr1, attr2) to {wins, games, advantage}
    """
    matchup_stats = defaultdict(lambda: {'wins': 0, 'games': 0})
    
    for match in matches:
        winner = match.get('winner')
        if not winner:
            continue
        
        blue_attrs = set(get_team_attributes(match['blue_team'], champions))
        red_attrs = set(get_team_attributes(match['red_team'], champions))
        
        # For each blue attribute vs each red attribute
        for blue_attr in blue_attrs:
            for red_attr in red_attrs:
                matchup = (blue_attr, red_attr)
                matchup_stats[matchup]['games'] += 1
                if winner == 'blue':
                    matchup_stats[matchup]['wins'] += 1
    
    # Calculate advantage
    for matchup in matchup_stats:
        stats = matchup_stats[matchup]
        winrate = stats['wins'] / stats['games'] if stats['games'] > 0 else 0.5
        stats['advantage'] = (winrate - 0.5) * 2
        stats['winrate'] = winrate
    
    return dict(matchup_stats)


def discover_synergies_from_attributes(pair_winrates: Dict,
                                       min_games: int = 30) -> Dict[Tuple[str, str], int]:
    """Convert attribute pair win rates to synergy scores.
    
    Args:
        pair_winrates: Attribute pair win rates
        min_games: Minimum games for statistical significance
        
    Returns:
        Dict mapping (attr1, attr2) to synergy score (-2 to +2)
    """
    synergies = {}
    
    for pair, stats in pair_winrates.items():
        if stats['games'] < min_games:
            continue
        
        winrate = stats['winrate']
        
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


def discover_counters_from_attributes(matchup_advantages: Dict,
                                      min_games: int = 30) -> Dict[Tuple[str, str], int]:
    """Convert attribute matchup advantages to counter scores.
    
    Args:
        matchup_advantages: Attribute matchup advantages
        min_games: Minimum games for statistical significance
        
    Returns:
        Dict mapping (attr1, attr2) to counter score (-2 to +2)
    """
    counters = {}
    
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
    print("ATTRIBUTE-LEVEL SYNERGY DISCOVERY")
    print("="*70)
    print("\nAnalyzing fundamental champion properties instead of archetypes...")
    
    # Load data
    matches_file = 'data/matches/euw1_matches.json'
    if not Path(matches_file).exists():
        print(f"\n✗ No match data found at {matches_file}")
        print("  Run: python data_extraction/fetch_match_data.py --region euw1 --count 1000")
        sys.exit(1)
    
    matches = load_match_data(matches_file)
    champions = load_champion_data()
    
    # Check if attributes are present
    sample_champ = next(iter(champions.values()))
    if 'attributes' not in sample_champ:
        print("\n✗ Champions don't have attributes yet")
        print("  Run: python data_pipeline/define_archetype_attributes.py")
        sys.exit(1)
    
    print(f"\nLoaded {len(matches)} matches")
    print(f"Loaded {len(champions)} champions with attributes")
    
    # Analyze synergies
    print("\n" + "-"*70)
    print("ANALYZING ATTRIBUTE PAIR WIN RATES...")
    print("-"*70)
    
    pair_winrates = calculate_attribute_pair_winrates(matches, champions)
    
    # Show top synergies
    sorted_pairs = sorted(pair_winrates.items(),
                         key=lambda x: (x[1]['games'], x[1]['winrate']),
                         reverse=True)
    
    print("\nTop 30 most common attribute pairs:")
    for i, (pair, stats) in enumerate(sorted_pairs[:30], 1):
        attr1, attr2 = pair
        wr = stats['winrate'] * 100
        status = "✓" if stats['winrate'] > 0.52 else "✗" if stats['winrate'] < 0.48 else "="
        print(f"{i:2d}. {attr1:25s} + {attr2:25s} | "
              f"{stats['games']:4d} games | {wr:5.1f}% WR | {status}")
    
    # Analyze counters
    print("\n" + "-"*70)
    print("ANALYZING ATTRIBUTE MATCHUP ADVANTAGES...")
    print("-"*70)
    
    matchup_advantages = calculate_attribute_matchup_advantage(matches, champions)
    
    # Show strongest counter relationships
    sorted_matchups = sorted(matchup_advantages.items(),
                            key=lambda x: (x[1]['games'], abs(x[1]['advantage'])),
                            reverse=True)
    
    print("\nTop 30 strongest counter relationships:")
    for i, (matchup, stats) in enumerate(sorted_matchups[:30], 1):
        attr1, attr2 = matchup
        adv = stats['advantage']
        wr = stats['winrate'] * 100
        
        if adv > 0.1:
            direction = ">"
            status = "✓"
        elif adv < -0.1:
            direction = "<"
            status = "✗"
        else:
            direction = "vs"
            status = "="
        
        print(f"{i:2d}. {attr1:25s} {direction:3s} {attr2:25s} | "
              f"{stats['games']:4d} games | {wr:5.1f}% WR | Adv: {adv:+.2f} | {status}")
    
    # Discover data-driven synergies
    print("\n" + "-"*70)
    print("DISCOVERED ATTRIBUTE SYNERGIES (min 30 games):")
    print("-"*70)
    
    discovered_synergies = discover_synergies_from_attributes(pair_winrates, min_games=30)
    
    strong_synergies = [(p, s) for p, s in discovered_synergies.items() if s == 2]
    anti_synergies = [(p, s) for p, s in discovered_synergies.items() if s == -2]
    
    strong_synergies.sort(key=lambda x: pair_winrates[x[0]]['winrate'], reverse=True)
    anti_synergies.sort(key=lambda x: pair_winrates[x[0]]['winrate'])
    
    print(f"\nStrong positive synergies (+2): {len(strong_synergies)}")
    for pair, score in strong_synergies[:15]:
        stats = pair_winrates[pair]
        print(f"  {pair[0]:25s} + {pair[1]:25s} | {stats['winrate']*100:5.1f}% WR | {stats['games']:3d} games")
    
    print(f"\nStrong anti-synergies (-2): {len(anti_synergies)}")
    for pair, score in anti_synergies[:15]:
        stats = pair_winrates[pair]
        print(f"  {pair[0]:25s} + {pair[1]:25s} | {stats['winrate']*100:5.1f}% WR | {stats['games']:3d} games")
    
    # Discover data-driven counters
    print("\n" + "-"*70)
    print("DISCOVERED ATTRIBUTE COUNTERS (min 30 games):")
    print("-"*70)
    
    discovered_counters = discover_counters_from_attributes(matchup_advantages, min_games=30)
    
    hard_counters = [(m, c) for m, c in discovered_counters.items() if c == 2]
    hard_countered = [(m, c) for m, c in discovered_counters.items() if c == -2]
    
    hard_counters.sort(key=lambda x: matchup_advantages[x[0]]['advantage'], reverse=True)
    hard_countered.sort(key=lambda x: matchup_advantages[x[0]]['advantage'])
    
    print(f"\nHard counters (+2): {len(hard_counters)}")
    for matchup, score in hard_counters[:15]:
        stats = matchup_advantages[matchup]
        print(f"  {matchup[0]:25s} > {matchup[1]:25s} | {stats['winrate']*100:5.1f}% WR | {stats['games']:3d} games")
    
    print(f"\nHard countered (-2): {len(hard_countered)}")
    for matchup, score in hard_countered[:15]:
        stats = matchup_advantages[matchup]
        print(f"  {matchup[0]:25s} < {matchup[1]:25s} | {stats['winrate']*100:5.1f}% WR | {stats['games']:3d} games")
    
    # Save results
    output = {
        'metadata': {
            'matches_analyzed': len(matches),
            'min_games_threshold': 30,
            'analysis_date': '2025-11-13',
            'analysis_type': 'attribute-based'
        },
        'synergies': {
            f"{p[0]}+{p[1]}": {
                'score': s,
                'winrate': pair_winrates[p]['winrate'],
                'games': pair_winrates[p]['games']
            }
            for p, s in discovered_synergies.items()
        },
        'counters': {
            f"{m[0]}>{m[1]}": {
                'score': c,
                'advantage': matchup_advantages[m]['advantage'],
                'games': matchup_advantages[m]['games']
            }
            for m, c in discovered_counters.items()
        }
    }
    
    output_path = 'data/processed/attribute_relationships.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Saved attribute analysis to: {output_path}")
    print("\nKey insights:")
    print("- Attribute-level analysis reveals WHY combinations work")
    print("- More transferable than archetype-only analysis")
    print("- Can be applied to new champions by tagging their attributes")


if __name__ == '__main__':
    main()
