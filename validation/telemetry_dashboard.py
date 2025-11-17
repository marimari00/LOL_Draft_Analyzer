"""Generate a lightweight telemetry dashboard summarizing prediction logs."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Optional, Tuple

DEFAULT_LOG_PATH = Path("data/telemetry/prediction_log.jsonl")
DEFAULT_DASHBOARD_PATH = Path("data/telemetry/dashboard.md")
DEFAULT_CALIBRATION_PATH = Path("data/telemetry/calibration_report.json")

DateKey = Tuple[int, int, int]


def _iter_entries(path: Path) -> Iterable[Dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _format_date(ts: float) -> Tuple[DateKey, str]:
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return (dt.year, dt.month, dt.day), dt.strftime("%Y-%m-%d")


def _summarize(entries: Iterable[Dict]) -> Dict[str, any]:
    entries = list(entries)
    summary = {
        "total": len(entries),
        "labeled": 0,
        "correct_labels": 0,
        "avg_confidence": None,
        "avg_win_prob": None,
        "confidence_values": [],
        "win_prob_values": [],
        "recent": [],
        "per_day": Counter(),
        "favored_counts": Counter(),
    }

    for entry in entries:
        ts = entry.get("ts")
        if isinstance(ts, (int, float)):
            day_key, label = _format_date(ts)
            summary["per_day"][label] += 1
        prediction = entry.get("prediction") or {}
        matchup = entry.get("favored_context") or {}
        favored = matchup.get("favored") or prediction.get("winner") or "unknown"
        summary["favored_counts"][favored] += 1

        confidence = matchup.get("confidence")
        if isinstance(confidence, (int, float)):
            summary["confidence_values"].append(confidence)

        prob = prediction.get("blue_win_probability")
        if isinstance(prob, (int, float)):
            summary["win_prob_values"].append(prob)

        actual = entry.get("actual_winner")
        if actual in {"blue", "red"}:
            summary["labeled"] += 1
            predicted = prediction.get("winner")
            if isinstance(prediction.get("blue_win_probability"), (int, float)) and isinstance(
                prediction.get("red_win_probability"), (int, float)
            ):
                predicted = "blue" if prediction["blue_win_probability"] >= prediction["red_win_probability"] else "red"
            if actual == predicted:
                summary["correct_labels"] += 1

        summary["recent"].append(
            {
                "timestamp": ts,
                "favored": favored,
                "favored_winrate": matchup.get("favored_winrate_pct"),
                "actual": entry.get("actual_winner"),
            }
        )

    summary["recent"] = [row for row in summary["recent"] if row["timestamp"] is not None][-10:]
    if summary["confidence_values"]:
        summary["avg_confidence"] = mean(summary["confidence_values"]) * 100.0
    if summary["win_prob_values"]:
        summary["avg_win_prob"] = mean(summary["win_prob_values"]) * 100.0
    summary["label_accuracy"] = (
        (summary["correct_labels"] / summary["labeled"] * 100.0) if summary["labeled"] else None
    )
    return summary


def _load_calibration(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _render_table(rows: List[Tuple[str, str]]) -> str:
    if not rows:
        return "No data."
    header = "| Metric | Value |\n| --- | --- |"
    body = "\n".join(f"| {key} | {value} |" for key, value in rows)
    return f"{header}\n{body}"


def _render_recent(rows: List[Dict]) -> str:
    if not rows:
        return "No recent requests."
    lines = ["| Timestamp (UTC) | Favored | Favored WR | Actual |", "| --- | --- | --- | --- |"]
    for row in rows:
        ts = row["timestamp"]
        ts_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if ts else "-"
        fav = row.get("favored") or "-"
        wr = row.get("favored_winrate")
        wr_str = f"{wr:.1f}%" if isinstance(wr, (int, float)) else "-"
        act = row.get("actual") or "-"
        lines.append(f"| {ts_str} | {fav} | {wr_str} | {act} |")
    return "\n".join(lines)


def _render_dashboard(summary: Dict, calibration: Optional[Dict]) -> str:
    metrics = []
    metrics.append(("Total predictions", str(summary["total"])) )
    metrics.append(("Labeled outcomes", str(summary["labeled"])) )
    if summary.get("label_accuracy") is not None:
        metrics.append(("Label accuracy", f"{summary['label_accuracy']:.2f}%"))
    if summary.get("avg_confidence") is not None:
        metrics.append(("Avg model confidence", f"{summary['avg_confidence']:.2f}%"))
    if summary.get("avg_win_prob") is not None:
        metrics.append(("Avg blue win prob", f"{summary['avg_win_prob']:.2f}%"))

    fav_rows = sorted(summary["favored_counts"].items(), key=lambda x: x[0])
    favored_table = _render_table([(side.title(), str(count)) for side, count in fav_rows])

    day_rows = sorted(summary["per_day"].items())[-7:]
    day_table = _render_table(day_rows)

    calibration_section = "No calibration report found."
    if calibration:
        calibration_section = _render_table([
            ("Samples", str(calibration.get("samples", 0))),
            ("ECE", f"{calibration.get('ece', 0.0):.4f}"),
            ("Brier Score", f"{calibration.get('brier', 0.0):.4f}"),
            ("Bins", str(calibration.get("bins", 0)))
        ])

    content = [
        "# Telemetry Dashboard",
        "## At-a-glance",
        _render_table(metrics),
        "## Favored Side Counts",
        favored_table,
        "## Daily Volume (last 7 days)",
        day_table,
        "## Recent Requests",
        _render_recent(summary["recent"]),
        "## Calibration",
        calibration_section,
    ]
    return "\n\n".join(content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG_PATH, help="Telemetry log JSONL path")
    parser.add_argument("--output", type=Path, default=DEFAULT_DASHBOARD_PATH, help="Dashboard output markdown path")
    parser.add_argument("--calibration", type=Path, default=DEFAULT_CALIBRATION_PATH, help="Calibration JSON path")
    args = parser.parse_args()

    entries = list(_iter_entries(args.log))
    summary = _summarize(entries)
    calibration = _load_calibration(args.calibration)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(_render_dashboard(summary, calibration), encoding="utf-8")
    print(f"Dashboard written to {args.output} • {summary['total']} predictions summarized")


if __name__ == "__main__":
    main()
