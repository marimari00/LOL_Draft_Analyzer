"""Aggregate lane-vs-lane and duo matchup performance stats from real matches."""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

LANE_ROLES: List[str] = ["Top", "Jungle", "Middle", "Bottom", "Support"]
DUO_PAIRS: List[Tuple[str, str]] = [
    ("Top", "Jungle"),
    ("Jungle", "Middle"),
    ("Bottom", "Support"),
    ("Support", "Jungle"),
]


def _init_lane_containers() -> Dict[str, Dict[str, Dict[str, int]]]:
    return {role: defaultdict(lambda: {"games": 0, "blue_wins": 0}) for role in LANE_ROLES}


def _init_duo_containers() -> Dict[str, Dict[str, Dict[str, int]]]:
    return {
        f"{role_a}_{role_b}": defaultdict(lambda: {"games": 0, "wins": 0})
        for role_a, role_b in DUO_PAIRS
    }


def aggregate_matchups(matches: List[Dict]) -> Dict[str, Dict]:
    lane_stats = _init_lane_containers()
    duo_stats = _init_duo_containers()

    for match in matches:
        winner = match.get("winner")
        blue_team = match.get("blue_team", {})
        red_team = match.get("red_team", {})

        # Lane vs lane matchups (order matters: blue champ vs red champ)
        for role in LANE_ROLES:
            blue_champ = blue_team.get(role)
            red_champ = red_team.get(role)
            if not blue_champ or not red_champ:
                continue

            key = f"{blue_champ}|{red_champ}"
            entry = lane_stats[role][key]
            entry["games"] += 1
            if winner == "blue":
                entry["blue_wins"] += 1

        # Duo synergies per side (order follows DUO_PAIRS definition)
        for role_a, role_b in DUO_PAIRS:
            pair_name = f"{role_a}_{role_b}"
            for side, team in (("blue", blue_team), ("red", red_team)):
                champ_a = team.get(role_a)
                champ_b = team.get(role_b)
                if not champ_a or not champ_b:
                    continue

                key = f"{champ_a}|{champ_b}"
                entry = duo_stats[pair_name][key]
                entry["games"] += 1
                if winner == side:
                    entry["wins"] += 1

    # Finalize with derived metrics
    for role_stats in lane_stats.values():
        for entry in role_stats.values():
            games = entry["games"]
            blue_wins = entry["blue_wins"]
            red_wins = games - blue_wins
            entry["red_wins"] = red_wins
            entry["blue_win_rate"] = blue_wins / games if games else 0.5
            entry["red_win_rate"] = red_wins / games if games else 0.5

    for pair_stats in duo_stats.values():
        for entry in pair_stats.values():
            games = entry["games"]
            entry["win_rate"] = entry["wins"] / games if games else 0.5

    return {
        "lane_matchups": {role: dict(stats) for role, stats in lane_stats.items()},
        "duo_matchups": {pair: dict(stats) for pair, stats in duo_stats.items()},
    }


def main():
    parser = argparse.ArgumentParser(description="Compute lane and duo matchup statistics from real matches")
    parser.add_argument(
        "--matches-path",
        default="data/matches/multi_region_10k.json",
        help="Path to the real match dataset JSON",
    )
    parser.add_argument(
        "--output-path",
        default="data/matches/lane_duo_stats.json",
        help="Where to store the aggregated matchup stats JSON",
    )
    args = parser.parse_args()

    matches_path = Path(args.matches_path)
    output_path = Path(args.output_path)

    if not matches_path.exists():
        raise FileNotFoundError(f"Matches file not found: {matches_path}")

    with matches_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    matches = payload.get("matches", [])
    if not matches:
        raise ValueError(f"No matches found in {matches_path}")

    metadata = payload.get("metadata", {})
    print(f"Loaded {len(matches):,} matches from {matches_path}")

    stats = aggregate_matchups(matches)
    stats["metadata"] = {
        "source_matches": matches_path.as_posix(),
        "total_matches": len(matches),
        "lane_roles": LANE_ROLES,
        "duo_pairs": [f"{a}_{b}" for a, b in DUO_PAIRS],
    }
    stats["metadata"].update({k: v for k, v in metadata.items() if k not in stats["metadata"]})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(stats, handle, indent=2)

    print(f"Saved lane/duo matchup stats to {output_path}")


if __name__ == "__main__":
    main()
