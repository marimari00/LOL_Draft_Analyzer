# Product Roadmap (Q4 2025)

This roadmap translates the current feedback backlog into fifteen concrete engineering initiatives, grouped by theme. Each item maps to the active todo list so we can execute sequentially while keeping scope visible.

## 1. Observability & Accuracy

1. **Telemetry Dashboard Script** – ✅ `tools/telemetry_report.py` ingests `data/telemetry/prediction_log.jsonl`, emits event counts + accuracy/Brier stats, and gives analysts a quick drift snapshot.
2. **Calibration CLI Docs** – Document how to run the telemetry + calibration scripts, prerequisites, and how to interpret ECE/Brier plots.
3. **Backend Health Metrics** – Extend the FastAPI health endpoint with model load state, telemetry backlog size, and last calibration timestamp.
4. **Regression Tests for Telemetry** – Add unit tests that mock filesystem writes to ensure telemetry logging never crashes the API and that coersion logic handles numpy types.

## 2. Recommendation Quality

5. **Recommendation Diversity Penalties** – Penalize repeated archetypes/roles beyond thresholds to avoid top-3 clones.
6. **Round-Robin Sampler** – After scoring, perform archetype-aware sampling so displayed recs cover distinct strategies.
7. **Rationale Badges** – Surface score breakdown tags ("Fixes engage gap", "Adds mixed damage") on each recommendation tile.
8. **Recommendation Unit Tests** – Snapshot tests covering new penalties/sampler to prevent regressions when tweaking weights.

## 3. Coach Training Experience

9. **Confidence Chips in Draft Assistant** – Mirror Coach Training’s favored/confidence chips inside `AnalysisPanel` so users trust projections everywhere.
10. **Pick History Log** – Track recent Pick Challenge attempts with score deltas, enabling quick review loops similar to duel history.
11. **Persist Duel Labels Locally** – Cache the last N label submissions in `localStorage` so telemetry survives reloads/offline moments.

## 4. Accessibility & UX Polish

12. **DraftBoard Accessibility** – Add ARIA labels, keyboard focus management, and color-contrast tweaks for the draft board grid.
13. **Verification Commands** – ✅ `VERIFY.md` now documents the pip/pytest/Jest/build steps every PR must run so QA stays consistent with CI.

## 5. Documentation & Communication

14. **README Roadmap Section** – Summarize these initiatives plus status badges so newcomers grasp active focus areas.
15. **Product Status Rollup** – Update `PROJECT_STATUS.md` (or equivalent) after each major deliverable to broadcast progress to stakeholders.

## Execution Notes

- Implement sequentially to keep diffs reviewable.
- After each batch (e.g., Observability, Recommendations, UX), pause for stakeholder review before continuing.
- Keep telemetry feature flags off in production until validation passes.
- Add verification commands to CI after manual vetting.
