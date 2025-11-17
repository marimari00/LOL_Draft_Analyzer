# Draft Analyzer Project Status

## 1. Project Vision

Theory-forward League of Legends draft assistant that reasons about archetype coverage, role balance, and synergies rather than raw win rates. The product should let coaches enter a partial draft, surface gaps (frontline, engage, damage profile), and recommend the next pick with transparent justification powered by archetype + attribute analysis.

## 2. Current Progress

- **Data & ML**: 936 Diamond+/Challenger matches processed, 45 champion attributes maintained, ensemble predictor (LR/RF/GB) loaded via `validation/ensemble_prediction.py`.
- **Backend**: FastAPI service (`backend/draft_api.py`) online with `/draft/recommend`, `/draft/analyze`, `/champions/{name}`, `/archetypes`, `/` ping, and `/health` diagnostics (model load, telemetry backlog, calibration freshness). Loads ensemble predictor plus archetype data on startup.
- **Recommendation Engine**: `/draft/recommend` now penalizes stacked archetype families and repeated lanes before the round-robin sampler runs, so top suggestions mix distinct win conditions instead of surfacing three clones.
- **Frontend**: React draft board (`frontend/`) providing pick/ban flow, role filters, a global draft progress tracker, a full pick-order timeline, color-coded role badges, ban portraits, rationale filter chips, recommendation deltas, pick-debt checklists, composition insights, accessible keyboard/ARIA navigation, plus a Health tab that visualizes `/health` metrics without leaving the app. Pulls recommendations from the FastAPI proxy through CRA's `proxy` config.
- **Tooling**: `SETUP_FIRST.bat` installs dependencies once; `START_HERE.bat` now frees ports 3000/8000 automatically before launching backend + frontend; GitHub Actions CI (`.github/workflows/ci.yml`) runs backend syntax checks plus frontend tests/builds on every push; targeted `pytest backend/tests/test_telemetry.py` coverage ensures telemetry logging stays resilient; and `tools/telemetry_report.py` generates calibration snapshots from `data/telemetry/prediction_log.jsonl` so analysts can inspect drift offline.
- **Docs & Releases**: `CHANGELOG.md` logs feature drops per semantic version, `docs/VERSIONS.md` maps each release to the documentation files updated that cycle, `docs/UX_AUDIT.md` tracks the UX/UI gap backlog, and `VERIFY.md` codifies the local verification commands that mirror CI.

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

- **2025-11-17**: Introduced GitHub Actions CI that compiles the backend and runs the frontend test/build suite so regressions are caught before merge.
- **2025-11-17**: Recommendation diversity penalties ensure `/draft/recommend` surfaces mixed archetypes/roles before the round-robin sampler, preventing triple-marksman lists.
- **2025-11-17**: Draft board now features a live pick progression meter and ban portrait chips so coaches immediately see how many locks remain and which bans are in play.
- **2025-11-17**: Pick order timeline, color-coded role badges across the board and recommendations, inline win-rate deltas, and lane reorder locking shipped to close UX audit items #3, #4, #7, and #13.
- **2025-11-17**: Recommendation panel rationale filters plus the live Pick Debt checklist give coaches instant control over which needs to solve next (UX audit items #6 and #9).
- **2025-11-17**: Added telemetry regression tests (`backend/tests/test_telemetry.py`) to verify numpy coercion and JSONL writes behave under pytest.
- **2025-11-16**: Recommendation cards now include glyph + pattern role badges, role-accent bars, and an explicit "Lock In" CTA with responsive hover/focus affordances, closing UX audit items #12 and #14 for colorblind safety across desktop + mobile widths.
- **2025-11-16**: Analysis Panel gained tablet/phone breakpoints that stack composition columns, pick-debt trackers, and insight grids so UX audit item #8 (small-screen overflow) is resolved.
- **2025-11-16**: Ban workflow now auto-advances through the LCS turn order with live phase chips and a ban queue indicator so users can’t get stuck manually flipping sides mid-draft.
- **2025-11-16**: Added `/health` metrics (model load, telemetry backlog, calibration timestamps) plus high-contrast, screen-reader-friendly Draft Board navigation (`frontend/src/components/DraftBoard*`).
- **2025-11-14**: Added automatic port cleanup to `START_HERE.bat`, documented the new workflow in `README.md`, removed redundant `frontend_backup/` copies, and created this consolidated status file.
