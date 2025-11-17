"""
Mass Draft Simulation Orchestrator

Samples millions of random drafts, scores them with the trained ensemble, and
aggregates archetype matchup statistics (e.g., Protect-the-Carry vs Dive).
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from statistics import NormalDist
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple, Optional

import joblib
import numpy as np
from sklearn.linear_model import SGDClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from validation.ensemble_prediction import load_ensemble_predictor, PredictionResult
from validation.ml_simulation import extract_features_from_team, features_to_vector
from validation.sampling_utils import build_role_pools_indices, sample_teams_numpy

ROLE_ORDER = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
POSITION_MAP = {
    "Top": "TOP",
    "Jungle": "JUNGLE",
    "Middle": "MIDDLE",
    "Mid": "MIDDLE",
    "Bottom": "BOTTOM",
    "Bot": "BOTTOM",
    "Carry": "BOTTOM",
    "Support": "UTILITY",
    "Utility": "UTILITY"
}

ROLE_TO_POSITION = {
    "TOP": "Top",
    "JUNGLE": "Jungle",
    "MIDDLE": "Middle",
    "BOTTOM": "Bottom",
    "UTILITY": "Support"
}

_WORKER_STATE_CACHE: Dict[str, Dict[str, Any]] = {}


def _warm_predictor(predictor, role_pools: Dict[str, List[str]]) -> None:
    """Run a single trivial inference to pre-load models in this process."""
    dummy_blue = []
    dummy_red = []
    for role in ROLE_ORDER:
        pool = role_pools.get(role, [])
        if not pool:
            continue
        dummy_blue.append(pool[0])
        dummy_red.append(pool[-1])
    if not dummy_blue or not dummy_red:
        return
    feature_vector, _ = predictor.build_feature_vector(
        dummy_blue,
        ROLE_ORDER,
        dummy_red,
        ROLE_ORDER,
        include_feature_breakdown=False
    )
    predictor.batch_predict_from_vectors([feature_vector])


def _get_worker_state(matchups_path: str) -> Dict[str, Any]:
    state = _WORKER_STATE_CACHE.get(matchups_path)
    if state is not None:
        return state
    champion_data = load_champion_data()
    role_pools = build_role_pools(champion_data)
    role_arrays, idx_to_champion = build_role_pools_indices(role_pools, ROLE_ORDER)
    predictor = load_ensemble_predictor(matchups_path=matchups_path)
    _warm_predictor(predictor, role_pools)
    state = {
        "champion_data": champion_data,
        "role_pools": role_pools,
        "predictor": predictor,
        "role_arrays": role_arrays,
        "idx_to_champion": idx_to_champion
    }
    _WORKER_STATE_CACHE[matchups_path] = state
    return state


def _simulate_chunk_process(chunk_size: int, seed: int, training_sample_rate: float, matchups_path: str):
    state = _get_worker_state(matchups_path)
    worker_stats = _create_empty_stats()
    payload = [] if training_sample_rate > 0 else None
    simulate_chunk(
        chunk_size,
        state["champion_data"],
        state["role_pools"],
        state["predictor"],
        rng=None,
        stats=worker_stats,
        trainer=None,
        training_payload=payload,
        training_sample_rate=training_sample_rate,
        seed=seed,
        role_arrays=state["role_arrays"],
        idx_to_champion=state["idx_to_champion"]
    )
    return worker_stats, payload


def _format_duration(seconds: Optional[float]) -> Optional[str]:
    if seconds is None or not math.isfinite(seconds) or seconds < 0:
        return None
    remaining = int(round(seconds))
    hours, rem = divmod(remaining, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"~{hours}h {minutes:02d}m"
    if minutes:
        return f"~{minutes}m {secs:02d}s"
    return f"~{secs}s"


def _create_empty_stats() -> Dict[str, Any]:
    return {
        "total_games": 0,
        "blue_win_prob_sum": 0.0,
        "blue_win_prob_sq_sum": 0.0,
        "confidence_sum": 0.0,
        "confidence_sq_sum": 0.0,
        "matchups": {},
        "composition_totals": {}
    }


def _merge_stats(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    scalar_keys = [
        "total_games",
        "blue_win_prob_sum",
        "blue_win_prob_sq_sum",
        "confidence_sum",
        "confidence_sq_sum"
    ]
    for key in scalar_keys:
        target[key] += source.get(key, 0)

    for matchup_key, entry in source.get("matchups", {}).items():
        dest_entry = target["matchups"].setdefault(matchup_key, {
            "games": 0,
            "blue_win_prob_sum": 0.0,
            "blue_win_prob_sq_sum": 0.0,
            "red_win_prob_sum": 0.0,
            "red_win_prob_sq_sum": 0.0,
            "blue_pred_wins": 0,
            "favored_counts": {"blue": 0, "red": 0}
        })
        dest_entry["games"] += entry["games"]
        dest_entry["blue_win_prob_sum"] += entry["blue_win_prob_sum"]
        dest_entry["blue_win_prob_sq_sum"] += entry["blue_win_prob_sq_sum"]
        dest_entry["red_win_prob_sum"] += entry["red_win_prob_sum"]
        dest_entry["red_win_prob_sq_sum"] += entry["red_win_prob_sq_sum"]
        dest_entry["blue_pred_wins"] += entry["blue_pred_wins"]
        for color in ("blue", "red"):
            dest_entry["favored_counts"][color] += entry["favored_counts"].get(color, 0)

    for comp_key, entry in source.get("composition_totals", {}).items():
        dest_entry = target["composition_totals"].setdefault(comp_key, {
            "games": 0,
            "blue_prob_sum": 0.0,
            "blue_prob_sq_sum": 0.0
        })
        dest_entry["games"] += entry["games"]
        dest_entry["blue_prob_sum"] += entry["blue_prob_sum"]
        dest_entry["blue_prob_sq_sum"] += entry["blue_prob_sq_sum"]


def _apply_training_payload(trainer: Optional[SimulationTrainer], payload: Optional[List[Dict[str, Any]]]) -> None:
    if trainer is None or not payload:
        return
    for sample in payload:
        stub_result = SimpleNamespace(blue_win_probability=sample["blue_prob"])
        trainer.process_game(sample["blue_team"], sample["red_team"], stub_result)


def _split_chunk_sizes(total: int, workers: int) -> List[int]:
    if workers <= 1 or total <= 0:
        return [max(total, 0)]
    base = total // workers
    remainder = total % workers
    sizes = []
    for i in range(workers):
        part = base + (1 if i < remainder else 0)
        if part > 0:
            sizes.append(part)
    return sizes


def load_champion_data() -> Dict:
    with open("data/processed/champion_archetypes.json", "r", encoding="utf-8") as f:
        return json.load(f)


def _compute_mean_and_margin(sum_val: float, sum_sq: float, n: int, confidence: float) -> Tuple[float, float | None]:
    if n == 0:
        return 0.0, None
    mean = sum_val / n
    if n < 2:
        return mean, None
    variance = (sum_sq - (sum_val * sum_val) / n) / (n - 1)
    variance = max(variance, 0.0)
    std_error = math.sqrt(variance / n)
    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    return mean, z * std_error


def build_role_pools(champion_data: Dict) -> Dict[str, List[str]]:
    assignments = champion_data.get("assignments", {})
    pools: Dict[str, List[str]] = {role: [] for role in ROLE_ORDER}
    for champ, info in assignments.items():
        positions = []
        if info.get("primary_position"):
            positions.append(info["primary_position"])
        positions.extend(info.get("viable_positions", []))
        for pos in positions:
            role = POSITION_MAP.get(pos, pos.upper())
            if role in pools and champ not in pools[role]:
                pools[role].append(champ)
    return pools


def load_match_data() -> List[Dict]:
    matches_path = Path("data/matches/euw1_matches.json")
    if not matches_path.exists():
        raise FileNotFoundError("Expected match data at data/matches/euw1_matches.json")
    with open(matches_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("matches", [])


def build_feature_names(champion_data: Dict, matches: List[Dict]) -> List[str]:
    feature_set = set()
    for match in matches:
        blue_team = match.get("blue_team", {})
        red_team = match.get("red_team", {})
        blue_features = extract_features_from_team(blue_team, champion_data)
        red_features = extract_features_from_team(red_team, champion_data)
        feature_set.update(blue_features.keys())
        feature_set.update(red_features.keys())
    return sorted(feature_set)


def team_list_to_position_dict(team: List[str]) -> Dict[str, str]:
    return {ROLE_TO_POSITION[role]: champ for role, champ in zip(ROLE_ORDER, team)}


class SimulationTrainer:
    def __init__(
        self,
        champion_data: Dict,
        feature_names: List[str],
        sample_rate: float,
        model_path: Path,
        report_path: Optional[Path],
        rng: random.Random
    ) -> None:
        self.champion_data = champion_data
        self.feature_names = feature_names
        self.sample_rate = max(0.0, min(sample_rate, 1.0))
        self.model_path = model_path
        self.report_path = report_path
        self.rng = rng
        self.model = SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4, random_state=42)
        self.classes = np.array([0, 1], dtype=int)
        self._initialized = False
        self.samples = 0
        self.label_sum = 0.0
        self.pred_sum = 0.0
        self.ensemble_prob_sum = 0.0
        self.calibration_loss = 0.0
        self.brier_sum = 0.0

    def _vectorize(self, team: Dict[str, str]) -> List[float]:
        features = extract_features_from_team(team, self.champion_data)
        return features_to_vector(features, self.feature_names)

    def process_game(self, blue_team_list: List[str], red_team_list: List[str], result: PredictionResult) -> None:
        if self.sample_rate == 0.0 or self.rng.random() > self.sample_rate:
            return

        blue_team = team_list_to_position_dict(blue_team_list)
        red_team = team_list_to_position_dict(red_team_list)
        blue_vec = self._vectorize(blue_team)
        red_vec = self._vectorize(red_team)
        diff = np.array([[b - r for b, r in zip(blue_vec, red_vec)]], dtype=float)

        blue_prob = float(result.blue_win_probability)
        label = 1 if self.rng.random() < blue_prob else 0
        y = np.array([label], dtype=int)

        if not self._initialized:
            self.model.partial_fit(diff, y, classes=self.classes)
            self._initialized = True
        else:
            self.model.partial_fit(diff, y)

        pred_prob = float(self.model.predict_proba(diff)[0][1])
        self.samples += 1
        self.label_sum += label
        self.pred_sum += pred_prob
        self.ensemble_prob_sum += blue_prob
        self.calibration_loss += (pred_prob - blue_prob) ** 2
        self.brier_sum += (pred_prob - label) ** 2

    def _build_report(self) -> Dict:
        return {
            "samples": self.samples,
            "sample_rate": self.sample_rate,
            "avg_label": self.label_sum / self.samples,
            "avg_prediction": self.pred_sum / self.samples,
            "avg_ensemble_prob": self.ensemble_prob_sum / self.samples,
            "calibration_mse_vs_ensemble": self.calibration_loss / self.samples,
            "brier_score": self.brier_sum / self.samples
        }

    def get_partial_report(self) -> Optional[Dict]:
        if self.samples == 0:
            return None
        return self._build_report()

    def snapshot_model(self, snapshot_path: Path) -> Optional[str]:
        if not self._initialized:
            return None
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "model": self.model,
            "feature_names": self.feature_names
        }, snapshot_path)
        return str(snapshot_path)

    def finalize(self) -> Dict:
        if self.samples == 0:
            return {}

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "model": self.model,
            "feature_names": self.feature_names
        }, self.model_path)

        report = self._build_report()
        report["model_path"] = str(self.model_path)

        if self.report_path:
            self.report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

        return report


def _infer_composition_type(champions: List[str], champion_data: Dict) -> str:
    assignments = champion_data.get("assignments", {})
    archetypes = [assignments.get(champ, {}).get("primary_archetype") for champ in champions]
    archetypes = [a for a in archetypes if a]

    def _champ_attributes(champion: str) -> List[str]:
        info = assignments.get(champion, {})
        attrs = info.get("archetype_attributes")
        if attrs is None:
            attrs = info.get("attributes", [])
        return list(attrs or [])

    if sum(1 for a in archetypes if "diver" in a or "assassin" in a) >= 2:
        return "dive"
    if "artillery_mage" in archetypes:
        ranges = 0
        for champ in champions:
            attrs = _champ_attributes(champ)
            if any(attr.startswith("range_") for attr in attrs):
                ranges += 1
        if ranges >= 2:
            return "poke"
    has_tank = any("tank" in a or "warden" in a for a in archetypes)
    has_marksman = "marksman" in archetypes
    has_enchanter = "enchanter" in archetypes
    if has_tank and has_marksman and has_enchanter:
        return "protect_the_carry"
    if sum(1 for a in archetypes if "skirmisher" in a or "juggernaut" in a) >= 2:
        return "bruiser"
    return "mixed"


def build_team(role_pools: Dict[str, List[str]], rng: random.Random) -> List[str]:
    assignments = []
    used = set()
    for role in ROLE_ORDER:
        pool = [c for c in role_pools[role] if c not in used]
        if not pool:
            pool = [c for champs in role_pools.values() for c in champs if c not in used]
        champ = rng.choice(pool)
        assignments.append(champ)
        used.add(champ)
    return assignments


def simulate_chunk(
    chunk_size: int,
    champion_data: Dict,
    role_pools: Dict[str, List[str]],
    predictor,
    rng: Optional[random.Random],
    stats: Dict,
    trainer: Optional[SimulationTrainer] = None,
    training_payload: Optional[List[Dict[str, Any]]] = None,
    training_sample_rate: float = 0.0,
    seed: Optional[int] = None,
    role_arrays: Optional[Dict[str, np.ndarray]] = None,
    idx_to_champion: Optional[List[str]] = None
) -> None:
    local_rng = rng if rng is not None else random.Random(seed)
    np_rng = None
    use_numpy_sampling = role_arrays is not None and idx_to_champion is not None
    if use_numpy_sampling:
        np_rng = np.random.default_rng(seed)
    batch_vectors: List[List[float]] = []
    batch_metadata: List[Dict[str, Any]] = []
    BATCH_SIZE = min(1024, chunk_size)

    def _flush_batch() -> None:
        nonlocal batch_vectors, batch_metadata
        if not batch_vectors:
            return
        blue_probs, red_probs, confidences = predictor.batch_predict_from_vectors(batch_vectors)
        for idx, meta in enumerate(batch_metadata):
            blue_prob = float(blue_probs[idx])
            red_prob = float(red_probs[idx])
            confidence = float(confidences[idx])
            winner = "blue" if blue_prob > 0.5 else "red"

            stats["total_games"] += 1
            stats["blue_win_prob_sum"] += blue_prob
            stats["blue_win_prob_sq_sum"] += blue_prob ** 2
            stats["confidence_sum"] += confidence
            stats["confidence_sq_sum"] += confidence ** 2

            match_key = f"{meta['blue_comp']}__vs__{meta['red_comp']}"
            entry = stats["matchups"].setdefault(match_key, {
                "games": 0,
                "blue_win_prob_sum": 0.0,
                "blue_win_prob_sq_sum": 0.0,
                "red_win_prob_sum": 0.0,
                "red_win_prob_sq_sum": 0.0,
                "blue_pred_wins": 0,
                "favored_counts": {"blue": 0, "red": 0}
            })
            entry["games"] += 1
            entry["blue_win_prob_sum"] += blue_prob
            entry["blue_win_prob_sq_sum"] += blue_prob ** 2
            entry["red_win_prob_sum"] += red_prob
            entry["red_win_prob_sq_sum"] += red_prob ** 2
            entry["blue_pred_wins"] += 1 if winner == "blue" else 0
            entry["favored_counts"][winner] += 1

            stats["composition_totals"].setdefault(meta['blue_comp'], {"games": 0, "blue_prob_sum": 0.0, "blue_prob_sq_sum": 0.0})
            stats["composition_totals"].setdefault(meta['red_comp'], {"games": 0, "blue_prob_sum": 0.0, "blue_prob_sq_sum": 0.0})
            stats["composition_totals"][meta['blue_comp']]["games"] += 1
            stats["composition_totals"][meta['blue_comp']]["blue_prob_sum"] += blue_prob
            stats["composition_totals"][meta['blue_comp']]["blue_prob_sq_sum"] += blue_prob ** 2
            stats["composition_totals"][meta['red_comp']]["games"] += 1
            stats["composition_totals"][meta['red_comp']]["blue_prob_sum"] += red_prob
            stats["composition_totals"][meta['red_comp']]["blue_prob_sq_sum"] += red_prob ** 2

            if trainer is not None:
                stub_result = SimpleNamespace(
                    blue_win_probability=blue_prob,
                    red_win_probability=red_prob,
                    winner=winner,
                    confidence=confidence
                )
                trainer.process_game(meta["blue_team"], meta["red_team"], stub_result)
            elif training_payload is not None and training_sample_rate > 0:
                if local_rng.random() <= training_sample_rate:
                    training_payload.append({
                        "blue_team": list(meta["blue_team"]),
                        "red_team": list(meta["red_team"]),
                        "blue_prob": blue_prob
                    })

        batch_vectors = []
        batch_metadata = []

    remaining = chunk_size
    while remaining > 0:
        sample_size = min(BATCH_SIZE, remaining)
        if use_numpy_sampling and np_rng is not None:
            blue_batch, red_batch = sample_teams_numpy(np_rng, role_arrays, idx_to_champion, ROLE_ORDER, sample_size)
        else:
            blue_batch = [build_team(role_pools, local_rng) for _ in range(sample_size)]
            red_batch = [build_team(role_pools, local_rng) for _ in range(sample_size)]
        for blue_team, red_team in zip(blue_batch, red_batch):
            feature_vector, _ = predictor.build_feature_vector(
                blue_team,
                ROLE_ORDER,
                red_team,
                ROLE_ORDER,
                include_feature_breakdown=False
            )
            blue_comp = _infer_composition_type(blue_team, champion_data)
            red_comp = _infer_composition_type(red_team, champion_data)
            batch_vectors.append(feature_vector)
            batch_metadata.append({
                "blue_team": list(blue_team),
                "red_team": list(red_team),
                "blue_comp": blue_comp,
                "red_comp": red_comp
            })
            if len(batch_vectors) >= BATCH_SIZE:
                _flush_batch()
        remaining -= sample_size

    _flush_batch()


def summarize(stats: Dict, top_k: int, confidence: float) -> Dict:
    total_games = stats["total_games"]
    avg_confidence = stats["confidence_sum"] / total_games if total_games else 0.0
    avg_blue, overall_margin = _compute_mean_and_margin(
        stats["blue_win_prob_sum"],
        stats["blue_win_prob_sq_sum"],
        total_games,
        confidence
    )
    overall = {
        "total_games": total_games,
        "avg_blue_win_probability": avg_blue,
        "avg_confidence": avg_confidence,
        "confidence_half_width": overall_margin,
        "confidence_level": confidence
    }

    matchup_summaries = []
    raw_matchups = {}
    for key, entry in stats["matchups"].items():
        blue_comp, red_comp = key.split("__vs__")
        games = entry["games"]
        blue_avg, blue_margin = _compute_mean_and_margin(
            entry["blue_win_prob_sum"], entry["blue_win_prob_sq_sum"], games, confidence
        )
        red_avg, red_margin = _compute_mean_and_margin(
            entry["red_win_prob_sum"], entry["red_win_prob_sq_sum"], games, confidence
        )
        matchup_summaries.append({
            "blue_comp": blue_comp,
            "red_comp": red_comp,
            "games": games,
            "avg_blue_win_prob": blue_avg,
            "avg_red_win_prob": red_avg,
            "blue_ci_half_width": blue_margin,
            "red_ci_half_width": red_margin,
            "blue_pred_win_rate": entry["blue_pred_wins"] / games,
            "blue_favored_fraction": entry["favored_counts"].get("blue", 0) / games
        })
        raw_matchups[key] = {
            "blue_comp": blue_comp,
            "red_comp": red_comp,
            "games": games,
            "avg_blue_win_prob": blue_avg,
            "avg_red_win_prob": red_avg,
            "blue_ci_half_width": blue_margin,
            "red_ci_half_width": red_margin,
            "blue_pred_win_rate": entry["blue_pred_wins"] / games,
            "favored_blue": entry["favored_counts"].get("blue", 0),
            "favored_red": entry["favored_counts"].get("red", 0)
        }

    matchup_summaries.sort(key=lambda m: m["avg_blue_win_prob"], reverse=True)
    top_matchups = matchup_summaries[:top_k]
    bottom_matchups = matchup_summaries[-top_k:]

    comp_totals = []
    raw_compositions = {}
    for comp, entry in stats["composition_totals"].items():
        blue_avg, blue_margin = _compute_mean_and_margin(
            entry["blue_prob_sum"], entry["blue_prob_sq_sum"], entry["games"], confidence
        )
        comp_totals.append({
            "composition": comp,
            "games": entry["games"],
            "avg_blue_probability": blue_avg,
            "ci_half_width": blue_margin
        })
        raw_compositions[comp] = {
            "games": entry["games"],
            "avg_blue_probability": blue_avg,
            "ci_half_width": blue_margin
        }
    comp_totals.sort(key=lambda c: c["avg_blue_probability"], reverse=True)

    return {
        "overall": overall,
        "top_matchups": top_matchups,
        "bottom_matchups": bottom_matchups,
        "composition_totals": comp_totals,
        "raw_matchups": raw_matchups,
        "raw_compositions": raw_compositions
    }


def _write_summary_file(
    output_path: Path,
    summary: Dict,
    stats: Dict,
    args: argparse.Namespace,
    games_to_run: int,
    auto_mode: bool,
    target_margin: Optional[float],
    achieved_margin: Optional[float],
    training_report: Optional[Dict],
    interrupted: bool,
    extra_metadata: Optional[Dict] = None
) -> None:
    metadata = {
        "games": stats["total_games"],
        "max_games": games_to_run,
        "chunk_size": args.chunk_size,
        "seed": args.seed,
        "confidence": args.confidence,
        "target_margin": target_margin,
        "achieved_margin": achieved_margin,
        "auto_mode": auto_mode,
        "training_report": training_report,
        "interrupted": interrupted
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": metadata,
            "summary": summary
        }, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Mass draft simulation pipeline")
    parser.add_argument("--games", type=int, default=100000, help="Total number of drafts to simulate (or default max if --target-margin is used)")
    parser.add_argument("--max-games", type=int, help="Hard ceiling when using --target-margin; defaults to --games")
    parser.add_argument("--chunk-size", type=int, default=5000, help="Games per progress chunk")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker threads for simulation (predictor shared in-process)")
    parser.add_argument("--progress-interval", type=int, default=5000, help="How many simulated games between heartbeat logs (0 disables)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--top-k", type=int, default=15, help="Number of matchup rows to keep per extremity")
    parser.add_argument("--confidence", type=float, default=0.95, help="Two-sided confidence level for reported WR deltas")
    parser.add_argument("--target-margin", type=float, help="Desired half-width (in probability units) for the overall WR confidence interval, e.g., 0.01 for ±1%")
    parser.add_argument("--train-model-path", type=Path, help="Optional path to save an SGD model trained on simulated games")
    parser.add_argument("--train-report", type=Path, help="Optional path to write training metrics JSON")
    parser.add_argument("--train-sample-rate", type=float, default=1.0, help="Fraction of simulated games to feed into training (0-1)")
    parser.add_argument("--checkpoint-dir", type=Path, help="Directory where periodic checkpoint summaries/models will be written")
    parser.add_argument("--checkpoint-ci-step", type=float, help="Save a checkpoint whenever the CI half-width improves by at least this amount (e.g., 0.01 for ±1pp)")
    parser.add_argument("--checkpoint-ci-decimals", type=int, help="Save a checkpoint whenever the CI half-width (percentage) decreases when rounded to this many decimals")
    parser.add_argument("--checkpoint-min-games", type=int, default=0, help="Minimum completed games before checkpointing can trigger")
    parser.add_argument("--output", type=Path, default=Path("data/simulations/mass_simulation_summary.json"))
    args = parser.parse_args()

    checkpoint_flags = [args.checkpoint_ci_step, args.checkpoint_ci_decimals]
    if args.checkpoint_dir is None and any(flag is not None for flag in checkpoint_flags):
        parser.error("--checkpoint-dir is required when specifying checkpoint options")
    if args.checkpoint_dir is not None and all(flag is None for flag in checkpoint_flags):
        parser.error("Provide either --checkpoint-ci-step or --checkpoint-ci-decimals when using --checkpoint-dir")
    if args.checkpoint_ci_step is not None and args.checkpoint_ci_step <= 0:
        parser.error("--checkpoint-ci-step must be positive")
    if args.checkpoint_ci_decimals is not None and args.checkpoint_ci_decimals < 0:
        parser.error("--checkpoint-ci-decimals cannot be negative")
    if args.checkpoint_ci_step is not None and args.checkpoint_ci_decimals is not None:
        parser.error("Specify only one of --checkpoint-ci-step or --checkpoint-ci-decimals")
    if args.checkpoint_min_games < 0:
        parser.error("--checkpoint-min-games cannot be negative")

    rng = random.Random(args.seed)
    matchups_path = "data/matches/lane_duo_stats.json"
    champion_data = load_champion_data()
    role_pools = build_role_pools(champion_data)
    role_arrays, idx_to_champion = build_role_pools_indices(role_pools, ROLE_ORDER)
    predictor = load_ensemble_predictor(matchups_path=matchups_path)
    _warm_predictor(predictor, role_pools)
    trainer: Optional[SimulationTrainer] = None

    if args.train_model_path:
        matches = load_match_data()
        feature_names = build_feature_names(champion_data, matches)
        trainer = SimulationTrainer(
            champion_data,
            feature_names,
            args.train_sample_rate,
            args.train_model_path,
            args.train_report,
            rng
        )

    stats = _create_empty_stats()

    chunk = max(1, args.chunk_size)
    auto_mode = args.target_margin is not None
    target_margin = args.target_margin
    max_games = args.max_games or args.games
    games_to_run = max_games if auto_mode else args.games
    checkpoint_enabled = args.checkpoint_dir is not None
    checkpoint_dir = args.checkpoint_dir
    checkpoint_ci_step = args.checkpoint_ci_step
    checkpoint_ci_decimals = args.checkpoint_ci_decimals
    checkpoint_min_games = args.checkpoint_min_games
    if checkpoint_enabled and checkpoint_dir is not None:
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
    last_checkpoint_margin = None
    last_checkpoint_percent = None
    checkpoint_index = 0
    progress_interval = max(0, args.progress_interval)
    next_progress_mark = progress_interval if progress_interval else None
    start_time = time.perf_counter()

    workers = max(1, args.workers)
    executor: Optional[ProcessPoolExecutor] = None
    if workers > 1:
        executor = ProcessPoolExecutor(max_workers=workers)
    collect_training = trainer is not None and args.train_sample_rate > 0

    def _format_progress_status(current_margin: Optional[float], include_heartbeat: bool = False) -> str:
        status = f"Simulated {stats['total_games']:,}/{games_to_run:,} games"
        if current_margin is not None:
            status += f" | current ±{current_margin * 100:.2f}%"
            if auto_mode and target_margin is not None:
                status += f" (target ±{target_margin * 100:.2f}%)"
        if include_heartbeat and progress_interval:
            status += f" | progress heartbeat every {progress_interval:,} games"
        elapsed = time.perf_counter() - start_time
        if stats["total_games"] > 0 and elapsed > 0:
            speed = stats["total_games"] / elapsed
            status += f" | speed {speed:,.1f} games/s"
            remaining = max(games_to_run - stats["total_games"], 0)
            eta_seconds = (remaining / speed) if speed > 0 else None
            eta_label = _format_duration(eta_seconds)
            if eta_label:
                status += f" | ETA {eta_label}"
        return status

    def _report_progress_checkpoint():
        nonlocal next_progress_mark
        if not progress_interval or next_progress_mark is None:
            return
        while stats["total_games"] >= next_progress_mark:
            _, current_margin = _compute_mean_and_margin(
                stats["blue_win_prob_sum"],
                stats["blue_win_prob_sq_sum"],
                stats["total_games"],
                args.confidence
            )
            status = _format_progress_status(current_margin, include_heartbeat=True)
            print(status + "...", flush=True)
            next_progress_mark += progress_interval

    interrupted = False
    try:
        while stats["total_games"] < games_to_run:
            remaining = games_to_run - stats["total_games"]
            size = min(chunk, remaining)
            if executor is None:
                simulate_chunk(
                    size,
                    champion_data,
                    role_pools,
                    predictor,
                    rng,
                    stats,
                    trainer,
                    training_payload=None,
                    training_sample_rate=0.0,
                    role_arrays=role_arrays,
                    idx_to_champion=idx_to_champion
                )
                _report_progress_checkpoint()
            else:
                work_sizes = _split_chunk_sizes(size, workers)
                futures = []
                for work_size in work_sizes:
                    seed = rng.randrange(1, 2 ** 63)
                    training_rate = args.train_sample_rate if collect_training else 0.0
                    futures.append(
                        executor.submit(
                            _simulate_chunk_process,
                            work_size,
                            seed,
                            training_rate,
                            matchups_path
                        )
                    )
                for future in as_completed(futures):
                    worker_stats, payload = future.result()
                    _merge_stats(stats, worker_stats)
                    if collect_training:
                        _apply_training_payload(trainer, payload)
                    _report_progress_checkpoint()
            _, current_margin = _compute_mean_and_margin(
                stats["blue_win_prob_sum"],
                stats["blue_win_prob_sq_sum"],
                stats["total_games"],
                args.confidence
            )
            status = _format_progress_status(current_margin)
            print(status + "...", flush=True)

            if (
                checkpoint_enabled
                and current_margin is not None
                and stats["total_games"] >= checkpoint_min_games
            ):
                should_checkpoint = False
                current_margin_percent = None
                if checkpoint_ci_step is not None:
                    if last_checkpoint_margin is None:
                        should_checkpoint = True
                    elif (last_checkpoint_margin - current_margin) >= checkpoint_ci_step:
                        should_checkpoint = True
                elif checkpoint_ci_decimals is not None:
                    current_margin_percent = round(current_margin * 100, checkpoint_ci_decimals)
                    epsilon = 10 ** (-(checkpoint_ci_decimals + 2))
                    if last_checkpoint_percent is None:
                        should_checkpoint = True
                    elif current_margin_percent + epsilon < last_checkpoint_percent:
                        should_checkpoint = True
                else:
                    should_checkpoint = False

                if should_checkpoint:
                    checkpoint_index += 1
                    checkpoint_summary = summarize(stats, args.top_k, args.confidence)
                    checkpoint_path = checkpoint_dir / f"checkpoint_{checkpoint_index:04d}.json"
                    extra_meta = {
                        "checkpoint_index": checkpoint_index,
                        "checkpoint_games": stats["total_games"],
                        "checkpoint_margin": current_margin,
                        "checkpoint_margin_percent": current_margin_percent if checkpoint_ci_decimals is not None else None,
                        "checkpoint_ci_step": checkpoint_ci_step,
                        "checkpoint_ci_decimals": checkpoint_ci_decimals,
                        "checkpoint_min_games": checkpoint_min_games,
                        "checkpoint_dir": str(checkpoint_dir)
                    }
                    partial_report = trainer.get_partial_report() if trainer is not None else None
                    _write_summary_file(
                        checkpoint_path,
                        checkpoint_summary,
                        stats,
                        args,
                        games_to_run,
                        auto_mode,
                        target_margin,
                        current_margin,
                        partial_report,
                        interrupted=False,
                        extra_metadata=extra_meta
                    )
                    if trainer is not None and args.train_model_path is not None:
                        snapshot_name = f"checkpoint_{checkpoint_index:04d}_{args.train_model_path.name}"
                        trainer.snapshot_model(checkpoint_dir / snapshot_name)
                    last_checkpoint_margin = current_margin
                    if checkpoint_ci_decimals is not None:
                        last_checkpoint_percent = current_margin_percent

            if auto_mode and current_margin is not None and target_margin is not None and current_margin <= target_margin:
                print("Target confidence margin reached; stopping early.")
                break
    except KeyboardInterrupt:
        interrupted = True
        print("\nSimulation interrupted by user; finalizing partial results...")
    finally:
        if executor is not None:
            executor.shutdown(wait=True)

    summary = summarize(stats, args.top_k, args.confidence)
    _, achieved_margin = _compute_mean_and_margin(
        stats["blue_win_prob_sum"],
        stats["blue_win_prob_sq_sum"],
        stats["total_games"],
        args.confidence
    )

    if auto_mode and (achieved_margin is None or achieved_margin > target_margin):
        print("Warning: Max games reached before hitting target margin.")

    training_report = trainer.finalize() if trainer is not None else None

    _write_summary_file(
        args.output,
        summary,
        stats,
        args,
        games_to_run,
        auto_mode,
        target_margin,
        achieved_margin,
        training_report,
        interrupted
    )
    print(f"Saved summary to {args.output}")


if __name__ == "__main__":
    main()
