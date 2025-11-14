# Draft Analyzer Project Status

## 1. Project Vision

Theory-forward League of Legends draft assistant that reasons about archetype coverage, role balance, and synergies rather than raw win rates. The product should let coaches enter a partial draft, surface gaps (frontline, engage, damage profile), and recommend the next pick with transparent justification powered by archetype + attribute analysis.

## 2. Current Progress

- **Data & ML**: 936 Diamond+/Challenger matches processed, 45 champion attributes maintained, ensemble predictor (LR/RF/GB) loaded via `validation/ensemble_prediction.py`.
- **Backend**: FastAPI service (`backend/draft_api.py`) online with `/draft/recommend`, `/draft/analyze`, `/champions/{name}`, `/archetypes`, and `/` health endpoints. Loads ensemble predictor plus archetype data on startup.
- **Frontend**: React draft board (`frontend/`) providing pick/ban flow, role filters, recommendation panel, and composition insights. Pulls recommendations from the FastAPI proxy through CRA's `proxy` config.
- **Tooling**: `SETUP_FIRST.bat` installs dependencies once; `START_HERE.bat` now frees ports 3000/8000 automatically before launching backend + frontend.

## 3. Architecture

```text
Data Pipeline -> Processed JSON (champion_archetypes.json, archetype_attributes.json)
        │
        ├── FastAPI backend (recommend/analyze/champion/archetype endpoints)
        │       └── Loads ensemble predictor + archetype metadata
        │
        └── React frontend (Draft board UI)
                └── Axios -> FastAPI @ localhost:8000
```

Supporting scripts (`start_backend.bat`, `start_frontend.bat`) allow manual control, while `START_HERE.bat` orchestrates the full stack for local dev.

## 4. Pipeline Status

- **Phase 1 – Core Data Pipeline**: ✅ 171 champions processed, spell database + attribute computation complete. Remaining validation pass for edge champions (Aphelios/Sylas) still open.
- **Phase 2 – Archetype Classification**: 🔄 Primary archetypes assigned for all champions; marksman misclassification and secondary archetype surfacing remain TODO.
- **Phase 3 – Synergies & Counters**: ⏳ Archetype synergy matrix not yet persisted; recommendation endpoint currently uses heuristic reasoning instead of matrix-driven math.
- **Phase 4 – Recommendation Engine**: 🔄 FastAPI endpoints online, but scoring lacks stored reasoning artifacts, caching, and pick-order awareness.
- **Phase 5 – Web Interface**: 🔄 React UI usable for demos; needs lane badges, pick-order templates, and richer feedback from the backend.

## 5. Known Issues

1. **Marksman data gaps**: 14/18 marksmen still under-report DPS because certain spell ratios are missing → cascades into misclassified archetypes.
2. **effect_burn false positives**: Utility abilities occasionally flagged as damage, inflating attribute counts.
3. **Frontend fallback list**: When `/champion_archetypes.json` fails to load, the UI falls back to a hard-coded roster; need to bundle the real JSON inside `public/` and ensure cache busting.
4. **Recommendation heuristics**: `_score_champion_for_draft` lacks explicit synergy matrix input; reasoning strings repeat and cannot cite concrete matchups.
5. **Predictor lifecycle**: No version banner or cache invalidation when retraining models, risking stale outputs in long-running sessions.

## 6. Next Steps

1. **Champion data parity** – Finish manual patches for marksman damage + re-run the attribute pipeline so frontend never hits the fallback list.
2. **Synergy matrix serialization** – Produce a 13x13 synergy/counter JSON and inject it into both backend scoring and frontend explanations.
3. **Draft flow polish** – Enforce pick/band phases, lane assignments, and show available slots with badges to reduce input errors.
4. **Recommendation reasoning audit** – Return structured reasons (synergy, counter, composition balance) so the UI can badge them instead of showing raw sentences.
5. **Packaging & deploy** – Add Dockerfiles (or uvicorn + CRA build instructions) so the combined app can ship to Render/Railway + Netlify with the same configuration used locally.

## 7. Recent Changes

- **2025-11-14**: Added automatic port cleanup to `START_HERE.bat`, documented the new workflow in `README.md`, removed redundant `frontend_backup/` copies, and created this consolidated status file.
