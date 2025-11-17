# Verification Guide

Use this checklist before opening a pull request or tagging a release. It mirrors the GitHub Actions workflow (pip install ➜ backend tests ➜ frontend tests/build) so local and CI signals stay in sync.

## 1. Environment Prep

Run once when you clone or whenever dependencies change:

```powershell
SETUP_FIRST.bat
```

If you prefer the manual route:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

> Tip: `START_HERE.bat` still launches both servers for exploratory testing, but it should follow (not replace) the verification steps below.

## 2. Backend Checks

```powershell
pip install -r requirements.txt
pytest backend/tests/test_telemetry.py
```

- `requirements.txt` ensures FastAPI + validation deps are current.
- `pytest backend/tests/test_telemetry.py` guards the filesystem/numpy coercion logic that historically broke telemetry logging.

## 3. Frontend Checks

From the `frontend/` folder:

```powershell
cd frontend
npm ci
npm test -- --watchAll=false
npm run build
cd ..
```

- `npm ci` guarantees a clean dependency tree (same command CI uses).
- `npm test -- --watchAll=false` runs all Jest/RTL suites, including the accessibility snapshots.
- `npm run build` exercises the production React bundle to catch bundler or type issues that tests might miss.

## 4. Optional Deep Dives

These take longer but are useful before large merges or releases:

```powershell
# Retrain ML models & rerun simulations
python validation/retrain_all_models.py
python validation/ml_simulation.py
```

```powershell
# Smoke-test the FastAPI stack manually
START_HERE.bat
# or run services individually
start_backend.bat
start_frontend.bat
```

Document any deviations (skipped tests, failing suites, custom datasets) directly in your PR description so reviewers know what was and wasn’t run.
