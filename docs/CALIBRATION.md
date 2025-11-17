# Calibration & Telemetry CLI Guide

This guide documents the lightweight command line tools that convert raw matchmaking telemetry into calibration reports and shareable dashboards. Follow these steps any time you want to validate the models win-probability outputs or publish an updated reliability snapshot for stakeholders.

## 1. Prerequisites

- Python 3.10+ with the project requirements installed (`pip install -r requirements.txt`).
- Recorded telemetry in `data/telemetry/prediction_log.jsonl` (written automatically by the FastAPI backend when duel labels are submitted from Coach Training or live matches are logged).
- At least 200 labeled entries (the calibration script enforces `--min-samples 200` by default).
- Optional: `data/telemetry/` directory checked into `.gitignore` so large logs stay out of version control.

> **Tip:** Encourage coaches to log actual winners in Coach Training (duel labels now persist locally), otherwise the telemetry file will contain predictions without ground-truth outcomes and the calibration script will exit early.

## 2. Running the Calibration CLI

The calibration CLI consumes the JSONL telemetry log and emits a JSON report containing reliability bins, Expected Calibration Error (ECE), and Brier score.

```powershell
# From the repo root
python -m validation.calibrate_predictions \
  --log data/telemetry/prediction_log.jsonl \
  --output data/telemetry/calibration_report.json \
  --bins 15 \
  --min-samples 250
```

### Arguments

| Flag | Description |
| --- | --- |
| `--log` | Path to the telemetry JSONL file (defaults to `data/telemetry/prediction_log.jsonl`). |
| `--output` | Where to write the calibration report (defaults to `data/telemetry/calibration_report.json`). |
| `--bins` | Number of equally sized probability buckets to use for the reliability curve. Increase this only when you have thousands of samples. |
| `--min-samples` | Guardrail that prevents publishing misleading reports with too few labels. |

### Output Schema (`calibration_report.json`)

```json
{
  "samples": 612,
  "bins": 15,
  "ece": 0.0324,
  "brier": 0.1821,
  "reliability": [
    {"bin": 0, "count": 18, "predicted": 0.09, "observed": 0.11},
    ...
  ]
}
```

- `samples`: labeled predictions ingested.
- `ece`: Expected Calibration Error 3.2% indicates the average absolute deviation between predicted and observed win rates.
- `brier`: Mean-squared error of the probability forecast (lower is better).
- `reliability`: Per-bin breakdown suitable for charting in notebooks, dashboards, or Confluence.

## 3. Generating the Telemetry Dashboard

After calibrating, render a Markdown snapshot to share volume, confidence, and recent label accuracy data.

```powershell
python -m validation.telemetry_dashboard \
  --log data/telemetry/prediction_log.jsonl \
  --output data/telemetry/dashboard.md \
  --calibration data/telemetry/calibration_report.json
```

The dashboard includes:
- Total predictions, labeled outcomes, average model confidence, and label accuracy.
- Favored side counts and daily volume (last 7 days).
- The 10 most recent predictions with actual results (if labeled).
- Calibration summary sourced from the JSON file above.

Commit or upload `dashboard.md` when you need asynchronous status updates; otherwise keep it local for analyst review.

## 4. Interpreting the Metrics

| Metric | How to read it | Healthy threshold |
| --- | --- | --- |
| **ECE** | Weighted mean of |predicted  observed| per bin. Lower means the forecast line hugs the y=x diagonal. | `< 0.05` = good, `0.05 0.10` = monitor, `> 0.10` = recalibrate. |
| **Brier score** | Mean squared error of the probability predictions. | `< 0.20` for balanced datasets; compare relative changes over time. |
| **Reliability bins** | Each row shows the average predicted win rate and the observed win rate for similar confidence levels. | Ideally, predicted and observed columns stay within a few percentage points. |
| **Label accuracy** | % of labeled samples where the predicted winner (argmax) matched reality. | Only meaningful when label volume is high; use it to spot major drift. |

If ECE spikes or bins drift apart, investigate recent champion pool updates or rerun ensemble calibration.

## 5. Troubleshooting

- **"Telemetry log not found"**: Ensure the API server has write permissions to `data/telemetry/` and that the path matches the CLI flag. The default path is relative to the repo root.
- **"Not enough labeled telemetry points"**: Collect more duel labels, or temporarily lower `--min-samples` if you want a quick-but-noisy readout (not recommended for publication).
- **Corrupt JSONL entries**: The CLI skips malformed lines automatically, but you can purge them by running `validation/tools/clean_jsonl.py` (coming soon) or manually removing them.
- **Different Python interpreter**: On Windows, match the environment used for the backend: `C:/Users/<you>/AppData/.../Python313/python.exe -m validation.calibrate_predictions ...`.

## 6. Workflow Checklist

1. Sync the latest telemetry logs from the server if you run the CLI locally.
2. Run `calibrate_predictions` with your desired bin count.
3. Inspect the printed metrics; spot-check the JSON reliability curve.
4. Run `telemetry_dashboard.py` to update `dashboard.md`.
5. Share both files (or screenshots) with the analytics channel; archive them in `data/telemetry/archives/` if you need historical comparisons.

Keep this guide nearby whenever you roll a new model version or after significant gameplay patches to ensure our theoretical reads are still trustworthy.
