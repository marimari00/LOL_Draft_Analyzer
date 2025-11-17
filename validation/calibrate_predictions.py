"""Calibrate win-probability predictions using stored telemetry logs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Tuple

DEFAULT_LOG_PATH = Path("data/telemetry/prediction_log.jsonl")
DEFAULT_OUTPUT_PATH = Path("data/telemetry/calibration_report.json")


def _iter_entries(path: Path) -> Iterable[Tuple[float, int]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            actual_winner = record.get("actual_winner")
            if actual_winner not in {"blue", "red"}:
                continue
            prediction_block = record.get("prediction") or {}
            blue_prob = prediction_block.get("blue_win_probability")
            red_prob = prediction_block.get("red_win_probability")
            if isinstance(blue_prob, (int, float)):
                prob = float(blue_prob)
            elif isinstance(red_prob, (int, float)):
                prob = 1.0 - float(red_prob)
            else:
                continue
            yield prob, 1 if actual_winner == "blue" else 0


def _build_bins(pairs: List[Tuple[float, int]], bins: int) -> List[Dict[str, float]]:
    bucket_totals = [0.0] * bins
    bucket_hits = [0.0] * bins
    bucket_counts = [0] * bins

    for prob, outcome in pairs:
        clamped = min(max(prob, 0.0), 1.0 - 1e-9)
        idx = min(int(clamped * bins), bins - 1)
        bucket_counts[idx] += 1
        bucket_totals[idx] += clamped
        bucket_hits[idx] += outcome

    reliability: List[Dict[str, float]] = []
    for index in range(bins):
        count = bucket_counts[index]
        if count == 0:
            reliability.append({
                "bin": index,
                "count": 0,
                "predicted": (index + 0.5) / bins,
                "observed": 0.0
            })
            continue
        reliability.append({
            "bin": index,
            "count": count,
            "predicted": bucket_totals[index] / count,
            "observed": bucket_hits[index] / count
        })
    return reliability


def _compute_metrics(pairs: List[Tuple[float, int]], bins: int) -> Dict[str, float]:
    reliability = _build_bins(pairs, bins)
    total = len(pairs)
    brier = mean(((prob - outcome) ** 2) for prob, outcome in pairs)
    ece = 0.0
    for bucket in reliability:
        weight = bucket["count"] / total if total else 0.0
        ece += weight * abs(bucket["predicted"] - bucket["observed"])
    return {
        "samples": total,
        "bins": bins,
        "ece": ece,
        "brier": brier,
        "reliability": reliability,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG_PATH, help="Telemetry JSONL log path")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Where to save calibration report JSON")
    parser.add_argument("--bins", type=int, default=12, help="Number of reliability bins")
    parser.add_argument("--min-samples", type=int, default=200, help="Minimum labeled samples required before emitting report")
    args = parser.parse_args()

    if not args.log.exists():
        raise SystemExit(f"Telemetry log not found: {args.log}")

    labeled_pairs = list(_iter_entries(args.log))
    if len(labeled_pairs) < args.min_samples:
        raise SystemExit(
            f"Not enough labeled telemetry points ({len(labeled_pairs)}) — need at least {args.min_samples}."
        )

    metrics = _compute_metrics(labeled_pairs, max(2, args.bins))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)

    print(
        f"Calibration report saved to {args.output} | samples={metrics['samples']} ece={metrics['ece']:.4f} brier={metrics['brier']:.4f}"
    )


if __name__ == "__main__":
    main()
