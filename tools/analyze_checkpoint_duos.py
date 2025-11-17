"""Analyze checkpoint samples to identify red-leaning lane and duo matchups."""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

ROLE_ORDER = ["Top", "Jungle", "Middle", "Bottom", "Support"]
DUO_SYNERGY_PAIRS: List[Tuple[str, str]] = [
    ("Top", "Jungle"),
    ("Jungle", "Middle"),
    ("Bottom", "Support"),
    ("Support", "Jungle"),
]


def _load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _lane_entry(lane_stats: Dict, role: str, blue_champ: str, red_champ: str) -> Dict:
    role_data = lane_stats.get(role, {})
    return role_data.get(f"{blue_champ}|{red_champ}")


def _duo_entry(duo_stats: Dict, pair_key: str, champs: Tuple[str, str]) -> Dict:
    return duo_stats.get(pair_key, {}).get("|".join(champs))


def analyze_checkpoint(checkpoint_path: Path, stats_path: Path, top_n: int) -> Dict:
    checkpoint = _load_json(checkpoint_path)
    stats = _load_json(stats_path)
    lane_stats = stats.get("lane_matchups", {})
    duo_stats = stats.get("duo_matchups", {})

    samples = checkpoint.get("analysis", {}).get("samples", [])
    if not samples:
        raise ValueError("Checkpoint does not contain sample games; run simulation with sample collection enabled.")

    lane_counter = defaultdict(lambda: {"occurrences": 0, "weight": 0.0, "blue_win_rate": None, "games": 0})
    duo_counter = defaultdict(lambda: {"occurrences": 0, "weight": 0.0, "win_rate": None, "games": 0})

    for game in samples:
        prediction = game.get("prediction", {})
        blue_prob = float(prediction.get("blue_probability", 0.5))
        winner = "blue" if blue_prob >= 0.5 else "red"
        if winner != "red":
            continue
        weight = (0.5 - blue_prob) + 1e-6  # prefer confident red predictions
        blue_team = game.get("blue_team", {})
        red_team = game.get("red_team", {})

        # Lane matchups
        for role in ROLE_ORDER:
            blue_champ = blue_team.get(role)
            red_champ = red_team.get(role)
            if not blue_champ or not red_champ:
                continue
            entry = lane_counter[(role, blue_champ, red_champ)]
            entry["occurrences"] += 1
            entry["weight"] += weight
            lane_info = _lane_entry(lane_stats, role, blue_champ, red_champ)
            if lane_info:
                games = lane_info.get("games", 0)
                blue_rate = lane_info.get("blue_win_rate", 0.5)
                entry["blue_win_rate"] = blue_rate
                entry["games"] = games

        # Duo synergies (red side pairs only)
        for role_a, role_b in DUO_SYNERGY_PAIRS:
            champ_a = red_team.get(role_a)
            champ_b = red_team.get(role_b)
            if not champ_a or not champ_b:
                continue
            key = (f"{role_a}_{role_b}", champ_a, champ_b)
            entry = duo_counter[key]
            entry["occurrences"] += 1
            entry["weight"] += weight
            pair_info = _duo_entry(duo_stats, key[0], (champ_a, champ_b))
            if pair_info:
                games = pair_info.get("games", 0)
                win_rate = pair_info.get("win_rate", 0.5)
                entry["win_rate"] = win_rate
                entry["games"] = games

    def _top_entries(counter):
        return sorted(counter.items(), key=lambda item: item[1]["weight"], reverse=True)[:top_n]

    return {
        "checkpoint": checkpoint_path.as_posix(),
        "total_samples": len(samples),
        "top_red_lanes": [
            {
                "role": role,
                "blue_champion": blue,
                "red_champion": red,
                **stats
            }
            for (role, blue, red), stats in _top_entries(lane_counter)
        ],
        "top_red_duos": [
            {
                "pair": pair,
                "red_champions": [champ_a, champ_b],
                **stats
            }
            for (pair, champ_a, champ_b), stats in _top_entries(duo_counter)
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze checkpoint samples for red-leaning matchups")
    parser.add_argument("--checkpoint", default="data/simulations/checkpoints/simulation_checkpoint_1000000.json", help="Checkpoint JSON to inspect")
    parser.add_argument("--stats", default="data/matches/lane_duo_stats.json", help="Lane/duo stats JSON path")
    parser.add_argument("--top", type=int, default=10, help="Number of entries to display per category")
    parser.add_argument("--output", help="Optional path to dump the structured summary as JSON")
    args = parser.parse_args()

    checkpoint_path = Path(args.checkpoint)
    stats_path = Path(args.stats)

    summary = analyze_checkpoint(checkpoint_path, stats_path, args.top)

    print("Top red-leaning lane matchups:")
    for lane in summary["top_red_lanes"]:
        role = lane["role"]
        blue = lane["blue_champion"]
        red = lane["red_champion"]
        weight = lane["weight"]
        blue_rate = lane.get("blue_win_rate")
        games = lane.get("games")
        blue_rate_str = f"{blue_rate:.2%}" if blue_rate is not None else "N/A"
        print(f"  {role}: {blue} vs {red} -> weight {weight:.3f}, blue_win_rate={blue_rate_str}, games={games}")

    print("\nTop red-leaning duos:")
    for duo in summary["top_red_duos"]:
        pair = duo["pair"]
        champs = "/".join(duo["red_champions"])
        weight = duo["weight"]
        win_rate = duo.get("win_rate")
        games = duo.get("games")
        win_rate_str = f"{win_rate:.2%}" if win_rate is not None else "N/A"
        print(f"  {pair}: {champs} -> weight {weight:.3f}, win_rate={win_rate_str}, games={games}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
        print(f"\nSummary written to {output_path}")


if __name__ == "__main__":
    main()
