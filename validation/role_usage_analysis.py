"""Role usage and off-meta performance analysis for League of Legends draft data."""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def _load_matches(path: Path) -> List[Dict]:
    with path.open('r', encoding='utf-8') as handle:
        payload = json.load(handle)
    return payload.get('matches', [])


def _load_champions(path: Path) -> Dict:
    with path.open('r', encoding='utf-8') as handle:
        payload = json.load(handle)
    return payload.get('assignments', {})


def _ordered_roles(info: Dict) -> List[str]:
    order: List[str] = []
    primary = info.get('primary_position')
    if primary:
        order.append(primary)
    for pos in info.get('viable_positions', []):
        if pos and pos not in order:
            order.append(pos)
    return order


def _category_for_role(role: str, ordered_roles: List[str]) -> str:
    if not ordered_roles:
        return 'unknown'
    if role == ordered_roles[0]:
        return 'primary'
    if len(ordered_roles) > 1 and role == ordered_roles[1]:
        return 'secondary'
    if role in ordered_roles[2:]:
        return 'tertiary'
    return 'off_meta'


def analyze_role_usage(matches_path: Path, champions_path: Path) -> Dict:
    matches = _load_matches(matches_path)
    champions = _load_champions(champions_path)

    champ_stats: Dict[str, Dict] = defaultdict(lambda: defaultdict(lambda: {'games': 0, 'wins': 0}))
    bucket_totals = defaultdict(lambda: {'games': 0, 'wins': 0})

    side_lookup = {
        'blue_team': 'blue',
        'red_team': 'red'
    }

    for match in matches:
        winner = match.get('winner')
        for side_key, side in side_lookup.items():
            team = match.get(side_key, {})
            for position, champion in team.items():
                if not champion:
                    continue
                entry = champ_stats[champion][position]
                entry['games'] += 1
                if winner == side:
                    entry['wins'] += 1

    report = {
        'metadata': {
            'matches_analyzed': len(matches)
        },
        'champions': {},
        'buckets': {}
    }

    for champion, positions in champ_stats.items():
        info = champions.get(champion, {})
        ordered_roles = _ordered_roles(info)
        champ_entry = {
            'primary_position': ordered_roles[0] if ordered_roles else None,
            'role_stats': {}
        }

        for position, stats in positions.items():
            games = stats['games']
            wins = stats['wins']
            if games == 0:
                continue
            category = _category_for_role(position, ordered_roles)
            bucket_totals[category]['games'] += games
            bucket_totals[category]['wins'] += wins
            champ_entry['role_stats'][position] = {
                'games': games,
                'wins': wins,
                'winrate': wins / games,
                'category': category
            }
        report['champions'][champion] = champ_entry

    for bucket, totals in bucket_totals.items():
        games = totals['games']
        wins = totals['wins']
        report['buckets'][bucket] = {
            'games': games,
            'wins': wins,
            'winrate': wins / games if games else None
        }

    meta_games = sum(report['buckets'].get(key, {}).get('games', 0) for key in ('primary', 'secondary'))
    meta_wins = sum(report['buckets'].get(key, {}).get('wins', 0) for key in ('primary', 'secondary'))
    off_meta = report['buckets'].get('off_meta', {'games': 0, 'wins': 0})
    report['meta_vs_offmeta'] = {
        'meta_games': meta_games,
        'meta_winrate': meta_wins / meta_games if meta_games else None,
        'off_meta_games': off_meta['games'],
        'off_meta_winrate': off_meta['wins'] / off_meta['games'] if off_meta['games'] else None
    }

    return report


def main():
    parser = argparse.ArgumentParser(description='Analyze role usage and off-meta performance.')
    parser.add_argument('--matches-path', default='data/matches/euw1_matches.json', help='Match dataset JSON path')
    parser.add_argument('--champions-path', default='data/processed/champion_archetypes.json', help='Champion archetype JSON path')
    parser.add_argument('--output', default='data/analysis/role_usage_report.json', help='Where to write the report JSON')
    args = parser.parse_args()

    report = analyze_role_usage(Path(args.matches_path), Path(args.champions_path))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2)

    print(f"✓ Role usage report saved to {output_path}")


if __name__ == '__main__':
    main()
