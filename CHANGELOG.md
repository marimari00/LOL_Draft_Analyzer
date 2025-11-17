# Changelog

All notable changes to this project will be documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2025-11-17

<!-- markdownlint-disable-next-line MD024 -->
### Added

- Ban phase toggle in the Draft Board lets coaches swap between official PRO turn order and SoloQ-style simultaneous bans without leaving the flow.
- Draft board documentation now calls out the recommended 75% browser zoom on 1920×1080 displays so analysts know how to view the full grid.
- GitHub Actions workflow enforces `pip install`, backend syntax compilation, frontend `npm test`, and production builds on every push/PR.
- Telemetry regression tests (`backend/tests/test_telemetry.py`) validate numpy coercion and JSONL writes so telemetry never regresses silently.
- Recommendation engine diversity penalties down-rank repeated archetype families and lane roles before round-robin sampling, eliminating triple-clone suggestion lists.
- Draft board UI gained a live pick progression meter plus icon-based ban chips to improve situational awareness.
- Draft board now shows a horizontal pick timeline with slot status badges and locks lane reordering once a pick is made so coaches can see the entire flow at a glance.
- Recommendation cards now include glyph + pattern role badges plus a persistent "Lock In" CTA with hover/focus outlines, clearing colorblind safety + affordance gaps (UX audit #12/#14).
- Analysis Panel now collapses its composition columns, pick-debt tracker, and insight grids on tablets/phones while tightening typography so UX audit #8 is closed.
- `tools/telemetry_report.py` summarizes `prediction_log.jsonl` into event counts, confidence buckets, and Brier scores so analysts can sanity-check calibration without opening notebooks.
- `VERIFY.md` documents the exact pip/pytest/Jest/build commands contributors must run so local verification stays in lockstep with CI.
- Recommendation panel exposes rationale filter chips ("need engage", "want peel", etc.) that instantly prune the card stack while keeping projected win deltas visible.
- Analysis panel introduces a pick-debt checklist that calls out missing engage, damage mix, peel, or range so coaches know the remaining composition asks.
- Authored `docs/UX_AUDIT.md` to capture fifteen UX/UI improvements and guide upcoming polish sprints.

## [1.1.0] - 2025-11-16

<!-- markdownlint-disable-next-line MD024 -->
### Added

- FastAPI `/health` endpoint now surfaces model load state, telemetry backlog counts, and calibration report metadata.
- Draft Board accessibility polish: keyboard focus sync per slot, ARIA labels across pick/bans, and higher-contrast theming.
- README + PROJECT_STATUS refreshed to describe diagnostics and accessibility behavior.
- Frontend Health tab visualizes `/health` metrics and auto-refreshes for lightweight monitoring.

### Changed

- Draft Board styles updated to improve focus outlines and readability without altering overall layout.

## [1.0.1] - 2025-11-14

<!-- markdownlint-disable-next-line MD024 -->
### Added

- `START_HERE.bat` cleans ports 3000/8000 before launching services, preventing stale dev sessions.
- `PROJECT_STATUS.md` created to summarize current progress and roadmap.

### Fixed

- Removed redundant `frontend_backup/` artifacts to reduce repo clutter.

## [1.0.0] - 2025-10-01

<!-- markdownlint-disable-next-line MD024 -->
### Added

- Initial public release with data pipeline, FastAPI backend (`/draft/recommend`, `/draft/analyze`, `/champions/{name}`, `/archetypes`, `/`), and React Draft Board UI.
- Telemetry logging scaffolding plus calibration CLI scripts.
- Setup scripts (`SETUP_FIRST.bat`, `START_HERE.bat`) for one-click local development.

[1.1.0]: https://github.com/marimari00/LOL_Draft_Analyzer/releases/tag/v1.1.0
[1.1.1]: https://github.com/marimari00/LOL_Draft_Analyzer/releases/tag/v1.1.1
[1.0.1]: https://github.com/marimari00/LOL_Draft_Analyzer/releases/tag/v1.0.1
[1.0.0]: https://github.com/marimari00/LOL_Draft_Analyzer/releases/tag/v1.0.0
