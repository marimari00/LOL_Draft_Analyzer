"""Calibrate ensemble predictions to remove global blue/red bias.

Reads a mass simulation summary (random drafts), computes the average
blue-win probability, and derives a logit shift that recenters future
predictions around the desired target (default 50%).
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

EPSILON = 1e-6


def _logit(value: float) -> float:
    clipped = min(max(value, EPSILON), 1 - EPSILON)
    return math.log(clipped / (1 - clipped))


def _load_summary(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    try:
        return data["summary"]["overall"]
    except (KeyError, TypeError) as exc:
        raise ValueError("Summary JSON is missing overall metrics") from exc


def _compute_shift(avg_blue: float, target: float) -> float:
    target_logit = _logit(target)
    current_logit = _logit(avg_blue)
    return current_logit - target_logit


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate logit calibration shift from random-draft summary")
    parser.add_argument("--summary", type=Path, required=True, help="Path to mass simulation summary JSON")
    parser.add_argument("--output", type=Path, default=Path("data/simulations/calibration.json"), help="Destination for calibration metadata")
    parser.add_argument("--target", type=float, default=0.5, help="Desired blue-win probability after calibration (default: 0.5)")
    args = parser.parse_args()

    if not 0 < args.target < 1:
        raise ValueError("--target must be in (0, 1)")

    overall = _load_summary(args.summary)
    try:
        avg_blue = float(overall["avg_blue_win_probability"])
        total_games = int(overall.get("total_games", 0))
        ci_half_width = float(overall.get("confidence_half_width", 0.0))
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError("Summary missing numeric fields") from exc

    shift = _compute_shift(avg_blue, args.target)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary_path": str(args.summary),
        "total_games": total_games,
        "avg_blue_win_probability": avg_blue,
        "target_probability": args.target,
        "confidence_half_width": ci_half_width,
        "logit_shift": shift
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    print(
        f"Stored logit shift {shift:.6f} (avg blue {avg_blue:.4%} vs target {args.target:.2%}) in {args.output}"
    )


if __name__ == "__main__":
    main()
