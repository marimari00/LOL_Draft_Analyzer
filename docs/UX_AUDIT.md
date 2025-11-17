# UX/UI Gap Audit (November 16, 2025)

This audit focuses on interaction pain points observed across `DraftBoard`, `RecommendationPanel`, `AnalysisPanel`, and the Health/Coach Training surfaces. Each gap is paired with a tactical improvement idea so we can prioritize implementation sprints. Items are ordered roughly by impact and grouped into the requested fifteen-point list.

| # | Gap Description | Impact | Suggested Remedy |
| --- | --- | --- | --- |
| 1 | **No global pick progression indicator** – coaches cannot see how many locks remain in the draft without counting slots manually. | Medium | Add a progress meter + next-turn copy atop `DraftBoard`, auto-updated as `blue_picks`/`red_picks` change. |
| 2 | **Ban row only shows text labels** – bans render as bare text buttons, making it hard to scan or recall iconography. | High | Swap ban slots to champion portraits with tooltips + remove button affordance unless the slot contains a ban. |
| 3 | **Slot role pills share identical styling** – TOP/JG/MID/BOT/UTIL look the same, so coaches cannot parse lane ownership quickly. | Medium | Introduce color-coded role badges (WCAG-friendly) in `DraftBoard` and `RecommendationPanel`. |
| 4 | **No upcoming pick timeline** – the order of future picks is hidden once slots are rearranged, creating uncertainty. | Medium | Render a left-to-right timeline (or pill list) that mirrors `pickOrder` and highlights the current + two upcoming slots. |
| 5 | **Inline champion search chips lack context** – `SlotChampionInput` suggestion chips are raw text without lane tags or icon previews. | Low | Add mini icons + role badges per suggestion so coaches can differentiate flex picks from mono-lane champs. |
| 6 | **Recommendation panel lacks quick filters** – users can’t filter cards by rationale (e.g., “need engage”). | Medium | Add filter chips bound to rationale tags to temporarily hide irrelevant cards. |
| 7 | **Projected win delta buried** – the difference each recommendation makes is only shown if `projected_team_winrate` exists, with no delta vs current state. | Medium | Display `+X.X%` delta next to each card so coaches instantly know the swing. |
| 8 | **Analysis panel overflows on small screens** – the composition snapshot grid does not collapse gracefully below ~1200px. | High | ✅ **Nov 16**: Added responsive breakpoints + default-collapsed sections so the composition grids, pick-debt tracker, and narratives stack cleanly on tablets/phones. |
| 9 | **No “pick debt” checklist** – teams lose track of unresolved composition needs (engage, peel, damage mix). | Medium | Surface a persistent checklist derived from `analysis` gaps, updating live as picks change. |
| 10 | **Coach Training lacks pick history** – analysts can’t review previous drills (ties into roadmap item #10). | Medium | Add a “Recent runs” tray with outcome deltas and timestamp. |
| 11 | **Health tab lacks per-metric sparklines** – telemetry trends require reading numbers line-by-line. | Low | Embed tiny sparklines for backlog size + calibration ECE in `HealthDashboard`. |
| 12 | **No colorblind-safe contrast cues** – focus/active indicators rely heavily on color alone (red vs blue). | High | ✅ **Nov 16**: Added glyph-coded role badges plus pattern overlays and high-contrast outlines in `RecommendationPanel` + slot headers so cues no longer rely on color alone. |
| 13 | **Pick slots allow reordering even when locked** – arrow buttons stay visible/active, creating confusion (though disabled). | Low | Hide reorder controls on filled slots and display a tooltip explaining ordering is locked. |
| 14 | **Recommendation cards have no hover affordance** – clickable area lacks hover/focus styling, so users don’t realize cards are interactive. | Medium | ✅ **Nov 16**: Cards now animate outline/background, show a persistent "Lock In" CTA, and expose focus-visible states so the interaction is obvious via mouse or keyboard. |
| 15 | **No global undo/redo for mistaken picks** – undo lives in backend? currently need manual delete. | Medium | Provide quick “Undo last pick/ban” buttons near the board header tied to draft state history. |

Next steps: ship two of the high-impact fixes (global progression indicator + ban avatars) immediately, then schedule the remaining backlog according to roadmap priority.
