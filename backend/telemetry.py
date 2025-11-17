"""Utility helpers for lightweight telemetry logging."""

from __future__ import annotations

import json
import queue
import threading
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional, Tuple

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - numpy optional
    np = None

_TELEMETRY_DIR = Path(__file__).resolve().parents[1] / "data" / "telemetry"
_LOG_PATH = _TELEMETRY_DIR / "prediction_log.jsonl"
_lock = Lock()
_queue: "queue.Queue[Tuple[str, Dict[str, Any]]]" = queue.Queue(maxsize=1000)
_worker_thread: Optional[threading.Thread] = None
_worker_running = threading.Event()


def _coerce_value(value: Any) -> Any:
    """Convert non-JSON-safe values (e.g., numpy types) into primitives."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value

    if np is not None and isinstance(value, np.generic):  # type: ignore[attr-defined]
        return value.item()

    if isinstance(value, (list, tuple)):
        return [_coerce_value(item) for item in value]

    if isinstance(value, dict):
        return {str(key): _coerce_value(val) for key, val in value.items()}

    if isinstance(value, set):
        return [_coerce_value(item) for item in value]

    try:
        return float(value)
    except Exception:
        return str(value)


def log_prediction_event(event_type: str, payload: Dict[str, Any]) -> None:
    """Append a telemetry entry to the JSONL log.

    Parameters
    ----------
    event_type:
        Logical label for the event (e.g., "draft_analyze").
    payload:
        Dictionary with serializable data to persist.
    """
    entry = {
        "ts": time.time(),
        "event": event_type,
        **{key: _coerce_value(value) for key, value in payload.items()}
    }

    _ensure_worker()

    try:
        _queue.put_nowait((event_type, entry))
    except queue.Full:  # pragma: no cover - queue size low enough not to block API
        print("Telemetry queue full; dropping event")


def _ensure_worker() -> None:
    global _worker_thread
    if _worker_thread and _worker_thread.is_alive():
        return

    _worker_running.set()
    _worker_thread = threading.Thread(target=_telemetry_worker, name="telemetry-writer", daemon=True)
    _worker_thread.start()


def _telemetry_worker() -> None:
    while _worker_running.is_set():
        try:
            event_type, entry = _queue.get(timeout=1.0)
        except queue.Empty:
            continue

        _attempt_write(entry)
        _queue.task_done()


def _attempt_write(entry: Dict[str, Any]) -> None:
    attempts = 0
    while attempts < 3:
        attempts += 1
        try:
            _TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
            with _lock:
                with _LOG_PATH.open("a", encoding="utf-8") as handle:
                    json.dump(entry, handle, ensure_ascii=True)
                    handle.write("\n")
            return
        except Exception as exc:
            backoff = min(0.5 * attempts, 2.0)
            print(f"Telemetry write failed (attempt {attempts}): {exc}")
            time.sleep(backoff)
def shutdown_telemetry_worker(timeout: float = 2.0) -> None:
    _worker_running.clear()
    if _worker_thread and _worker_thread.is_alive():
        _worker_thread.join(timeout=timeout)
