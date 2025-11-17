"""Generate calibration summaries from telemetry JSONL logs."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List

DEFAULT_LOG_PATH = Path(__file__).resolve().parents[1] / "data" / "telemetry" / "prediction_log.jsonl"
CONFIDENCE_BUCKETS = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]


@dataclass
class EventEntry:
    """Strongly typed telemetry entry."""
    timestamp: float
    event: str
    raw: Dict

    @property
    def iso_timestamp(self) -> str:
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat()


def iter_entries(path: Path) -> Iterator[EventEntry]:
    if not path.exists():
        raise FileNotFoundError(f"Telemetry log not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Malformed JSON on line {line_number}: {exc}") from exc

            ts = float(payload.get("ts", 0))
            event = str(payload.get("event", "unknown"))
            yield EventEntry(timestamp=ts, event=event, raw=payload)


def bucket_label(value: float) -> str:
    for lower, upper in CONFIDENCE_BUCKETS:
        if value <= upper + 1e-9:
            return f"{int(lower * 100)}–{int(upper * 100)}%"
    return "100%+"


def summarize(path: Path) -> str:
    entries = list(iter_entries(path))
    if not entries:
        return f"No telemetry entries found in {path}"

    total_events = len(entries)
    event_counter = Counter(entry.event for entry in entries)
    first_ts = min(entry.timestamp for entry in entries)
    last_ts = max(entry.timestamp for entry in entries)

    prediction_stats = _summarize_predictions(entry for entry in entries if entry.event == "draft_analyze")

    lines: List[str] = []
    lines.append("Telemetry Report")
    lines.append("================")
    lines.append(f"Source file : {path}")
    lines.append(f"Total events: {total_events}")
    lines.append(f"Range       : {datetime.fromtimestamp(first_ts, tz=timezone.utc).isoformat()} ➜ "
                 f"{datetime.fromtimestamp(last_ts, tz=timezone.utc).isoformat()}")
    lines.append("\nEvent Breakdown")
    lines.append("----------------")
    for event, count in event_counter.most_common():
        pct = (count / total_events) * 100
        lines.append(f"- {event}: {count} ({pct:.1f}%)")

    if prediction_stats:
        lines.append("\nDraft Analyze Metrics")
        lines.append("----------------------")
        stats = prediction_stats
        lines.append(f"Total predictions     : {stats['total']}")
        lines.append(f"Predictions w/ results: {stats['with_actual']}")
        if stats['with_actual']:
            accuracy = (stats['correct'] / stats['with_actual']) * 100
            lines.append(f"Accuracy              : {accuracy:.2f}%")
            lines.append(f"Brier score           : {stats['brier']:.4f}")
        if stats['confidence_count']:
            avg_conf = (stats['confidence_sum'] / stats['confidence_count']) * 100
            lines.append(f"Avg confidence        : {avg_conf:.2f}%")
        if stats['blue_prob_count']:
            lines.append(f"Avg blue probability  : {stats['avg_blue']:.4f}")

        if stats['confidence_buckets']:
            lines.append("\nConfidence Buckets (predicted winner probability)")
            for bucket, info in stats['confidence_buckets']:
                bucket_total = info['total']
                correct = info['correct']
                hit_rate = (correct / bucket_total * 100) if bucket_total else 0.0
                lines.append(f"- {bucket}: {bucket_total} picks, {hit_rate:.1f}% accuracy")

    recent_tail = entries[-5:]
    lines.append("\nRecent Events")
    lines.append("--------------")
    for entry in recent_tail:
        lines.append(f"{entry.iso_timestamp} | {entry.event}")

    return "\n".join(lines)


def _summarize_predictions(entries: Iterable[EventEntry]) -> Dict[str, Any]:
    total = 0
    with_actual = 0
    correct = 0
    brier_sum = 0.0
    brier_count = 0
    confidence_sum = 0.0
    confidence_count = 0
    blue_prob_sum = 0.0
    blue_prob_count = 0
    confidence_buckets: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "correct": 0})

    for entry in entries:
        total += 1
        prediction = entry.raw.get("prediction", {})
        predicted_winner = prediction.get("winner")
        blue_probability = prediction.get("blue_win_probability")
        confidence = prediction.get("confidence")

        if isinstance(blue_probability, (int, float)):
            blue_prob_sum += float(blue_probability)
            blue_prob_count += 1
        if isinstance(confidence, (int, float)):
            confidence_sum += float(confidence)
            confidence_count += 1

        if not isinstance(blue_probability, (int, float)) or predicted_winner not in {"blue", "red"}:
            continue

        actual = entry.raw.get("actual_winner")

        if actual in {"blue", "red"}:
            with_actual += 1
            predicted_prob = blue_probability if predicted_winner == "blue" else (1.0 - blue_probability)
            bucket = bucket_label(predicted_prob)
            confidence_buckets[bucket]["total"] += 1
            actual_value = 1.0 if actual == "blue" else 0.0
            brier_sum += (blue_probability - actual_value) ** 2
            brier_count += 1
            if predicted_winner == actual:
                correct += 1
                confidence_buckets[bucket]["correct"] += 1

    if total == 0:
        return {}

    brier = (brier_sum / brier_count) if brier_count else 0.0
    avg_blue = blue_prob_sum / blue_prob_count if blue_prob_count else 0.0

    ordered_buckets: List[tuple[str, Dict[str, int]]] = []
    for lower, upper in CONFIDENCE_BUCKETS:
        label = f"{int(lower * 100)}–{int(upper * 100)}%"
        if label in confidence_buckets:
            ordered_buckets.append((label, confidence_buckets[label]))
    # Add any unexpected labels (e.g., 100%+) at the end
    seen_labels = {item[0] for item in ordered_buckets}
    for label, info in confidence_buckets.items():
        if label not in seen_labels:
            ordered_buckets.append((label, info))

    return {
        "total": total,
        "with_actual": with_actual,
        "correct": correct,
        "brier": brier,
        "confidence_sum": confidence_sum,
        "confidence_count": confidence_count,
        "avg_blue": avg_blue,
        "blue_prob_count": blue_prob_count,
        "confidence_buckets": ordered_buckets,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize telemetry JSONL into human-readable stats")
    parser.add_argument("log_path", nargs="?", default=str(DEFAULT_LOG_PATH), help="Path to prediction_log.jsonl")
    args = parser.parse_args()

    path = Path(args.log_path).expanduser().resolve()
    try:
        report = summarize(path)
    except Exception as exc:  # pragma: no cover - CLI surfacing
        raise SystemExit(f"telemetry_report failed: {exc}") from exc

    print(report)


if __name__ == "__main__":
    main()
