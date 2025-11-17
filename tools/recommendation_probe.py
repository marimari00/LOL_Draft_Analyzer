"""Quick CLI to inspect backend recommendation scores for given role/draft."""

import argparse
import csv
import json
import random
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
        sys.path.append(str(ROOT_DIR))

from backend import draft_api

CSV_COLUMNS = [
    "sample_id",
    "focus_team",
    "requested_role",
    "our_pick_count",
    "enemy_pick_count",
    "rec_rank",
    "champion",
    "primary_archetype",
    "recommended_role",
    "score",
    "component_synergy",
    "component_counters",
    "component_role_fit",
    "component_balance",
    "component_comfort"
]


def load_data():
    with open(ROOT_DIR / "data" / "processed" / "champion_archetypes.json", "r", encoding="utf-8") as f:
        draft_api.champion_data = json.load(f)


def build_role_index():
    assignments = draft_api.champion_data["assignments"]
    role_index = {role: [] for role in draft_api.ROLE_ORDER}
    for champ, info in assignments.items():
        for pos in info.get("viable_positions", []):
            normalized = draft_api.POSITION_TO_ROLE.get(pos, pos.upper())
            if normalized in role_index:
                role_index[normalized].append(champ)
    return role_index


def pick_champion_for_role(role, role_index, used):
    pool = [c for c in role_index.get(role, []) if c not in used]
    if not pool:
        pool = [c for c in draft_api.champion_data["assignments"] if c not in used]
    choice = random.choice(pool)
    used.add(choice)
    return choice


def generate_full_team(role_index, used):
    picks = []
    for role in draft_api.ROLE_ORDER:
        picks.append(pick_champion_for_role(role, role_index, used))
    return picks


def sample_draft_state(role_index):
    used = set()
    blue_full = generate_full_team(role_index, used)
    red_full = generate_full_team(role_index, used)
    return blue_full, red_full


def choose_requested_role(locked_roles, override):
    if override and override.upper() != "AUTO":
        return override.upper()
    remaining = [role for role in draft_api.ROLE_ORDER if role not in locked_roles]
    return random.choice(remaining) if remaining else None


def log_samples(samples, requested_role_override, top_k, output_path):
    load_data()
    assignments = draft_api.champion_data["assignments"]
    role_index = build_role_index()
    all_champions = set(assignments.keys())

    rows = []

    for sample_id in range(1, samples + 1):
        blue_full, red_full = sample_draft_state(role_index)
        focus_team = random.choice(["blue", "red"])
        our_full = blue_full if focus_team == "blue" else red_full
        enemy_full = red_full if focus_team == "blue" else blue_full

        our_pick_count = random.randint(0, len(our_full))
        enemy_pick_count = random.randint(max(0, our_pick_count - 1), len(enemy_full))

        our_team = our_full[:our_pick_count]
        enemy_team = enemy_full[:enemy_pick_count]
        our_roles = draft_api.ROLE_ORDER[:our_pick_count]

        requested_role = choose_requested_role(our_roles, requested_role_override)

        available = all_champions - set(our_team + enemy_team)
        if not available or requested_role is None:
            continue

        recs = draft_api._generate_recommendations_for_slot(
            available_champions=available,
            our_team=our_team,
            enemy_team=enemy_team,
            our_roles=our_roles,
            requested_role=requested_role,
            limit=top_k
        )

        for rank, rec in enumerate(recs, start=1):
            breakdown = rec.score_breakdown or {}
            rows.append({
                "sample_id": sample_id,
                "focus_team": focus_team,
                "requested_role": requested_role,
                "our_pick_count": len(our_team),
                "enemy_pick_count": len(enemy_team),
                "rec_rank": rank,
                "champion": rec.champion,
                "primary_archetype": rec.archetype,
                "recommended_role": rec.recommended_role or "",
                "score": round(rec.score, 4),
                "component_synergy": round(breakdown.get("synergy", 0.0), 4),
                "component_counters": round(breakdown.get("counters", 0.0), 4),
                "component_role_fit": round(breakdown.get("role_fit", 0.0), 4),
                "component_balance": round(breakdown.get("balance", 0.0), 4),
                "component_comfort": round(breakdown.get("comfort", 0.0), 4)
            })

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✓ Wrote {len(rows)} recommendation rows to {output_path}")


def probe(role: str, limit: int):
    load_data()
    available = set(draft_api.champion_data["assignments"].keys())
    recs = draft_api._generate_recommendations_for_slot(
        available_champions=available,
        our_team=[],
        enemy_team=[],
        our_roles=[],
        requested_role=role,
        limit=limit
    )
    print(f"Top {limit} recommendations for empty draft ({role}):")
    for rec in recs:
        reasons = "; ".join(rec.reasoning[:2])
        print(f"- {rec.champion:12} score={rec.score:.3f} role={rec.recommended_role or 'flex'} | {reasons}")


def main():
    parser = argparse.ArgumentParser(description="Inspect recommendation heuristics")
    parser.add_argument("--role", default="UTILITY", help="Target role to inspect")
    parser.add_argument("--limit", type=int, default=10, help="How many champions to show")
    parser.add_argument("--sample-drafts", type=int, default=0, help="If >0, sample this many random draft states")
    parser.add_argument("--sample-role", default="AUTO", help="Override requested role during sampling (AUTO to infer)")
    parser.add_argument("--top-k", type=int, default=5, help="Top-K recommendations to log per sample")
    parser.add_argument("--sample-output", default=str(ROOT_DIR / "data" / "simulations" / "recommendation_bias_samples.csv"), help="CSV output path for sampled recommendations")
    args = parser.parse_args()
    if args.sample_drafts > 0:
        log_samples(args.sample_drafts, args.sample_role, args.top_k, args.sample_output)
    else:
        probe(args.role.upper(), args.limit)


if __name__ == "__main__":
    main()
