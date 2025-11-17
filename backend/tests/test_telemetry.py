import json

import numpy as np
import pytest

from backend import telemetry


def test_coerce_value_handles_numpy_scalars():
    result_float = telemetry._coerce_value(np.float32(0.75))
    result_int = telemetry._coerce_value(np.int32(5))

    assert pytest.approx(result_float, rel=1e-6) == 0.75
    assert result_int == 5


class ImmediateQueue:
    def __init__(self, writer):
        self._writer = writer

    def put_nowait(self, item):
        _, entry = item
        self._writer(entry)


def test_log_prediction_event_writes_jsonl(tmp_path, monkeypatch):
    log_dir = tmp_path / "telemetry"
    log_path = log_dir / "prediction_log.jsonl"

    monkeypatch.setattr(telemetry, "_TELEMETRY_DIR", log_dir, raising=False)
    monkeypatch.setattr(telemetry, "_LOG_PATH", log_path, raising=False)
    monkeypatch.setattr(telemetry, "_ensure_worker", lambda: None, raising=False)
    monkeypatch.setattr(
        telemetry,
        "_queue",
        ImmediateQueue(lambda entry: telemetry._attempt_write(entry)),
        raising=False,
    )

    payload = {
        "probabilities": [np.float32(0.66), np.float64(0.34)],
        "metadata": {"role": "JUNGLE", "score": np.int32(7)},
        "tags": {"dive", "front_to_back"},
        "nested": (np.float32(0.11), np.float64(0.89)),
    }

    telemetry.log_prediction_event("unit_test_event", payload)

    telemetry.shutdown_telemetry_worker()

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["event"] == "unit_test_event"
    assert isinstance(entry["probabilities"][0], float)
    assert entry["metadata"]["score"] == 7
    assert sorted(entry["tags"]) == ["dive", "front_to_back"]
    assert entry["nested"][0] == pytest.approx(0.11, rel=1e-6)
