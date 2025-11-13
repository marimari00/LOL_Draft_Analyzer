# GitHub Copilot Instructions for Draft Analyzer Project

## Project Overview
**Goal**: Build a web-based draft analyzer that recommends champions for specific team compositions based on attributes and archetypes (similar to iTero/DPMLOL but theory-driven, not winrate-driven). Focus on reaching new and unexpected conclusions about picks and bans through archetype synergies and counters.

---

## File Organization Rules

### 1. Debug & Temporary Files
**ALWAYS use the `DEBUG_TEMP/` folder for:**
- Debug scripts (e.g., `check_*.py`, `debug_*.py`, `test_*.py`)
- Validation scripts (e.g., `validate_*.py`, `quick_*.py`)
- Analysis scratch files (e.g., `analyze_*.py` that aren't part of main pipeline)
- Temporary output files
- Investigation scripts (e.g., `investigate_*.py`, `trace_*.py`)

**Exception**: Core pipeline scripts stay in `data_pipeline/`

### 2. Documentation Structure
**Use a SINGLE `PROJECT_STATUS.md` file with clear sections:**

```markdown
# Draft Analyzer Project Status

## 1. Project Vision
[Final goal, use cases, key features]

## 2. Current Progress
[What's working, what's done]

## 3. Architecture
[System design, data flow]

## 4. Pipeline Status
[Each pipeline stage with status: ✅ Done, 🔄 In Progress, ⏳ Pending]

## 5. Known Issues
[Bugs, limitations, technical debt]

## 6. Next Steps
[Prioritized action items]

## 7. Recent Changes
[Latest updates with dates]
```

**Delete these files** (consolidate into PROJECT_STATUS.md):
- DEEP_AUDIT_FINDINGS.md
- MATHEMATICAL_FINDINGS.md
- SCIENTIFIC_FINDINGS.md
- DATA_SOURCES_STRATEGY.md
- SESSION_PROGRESS.md
- GIT_SETUP.md

---

## Development Workflow

### Before Making Changes
1. **Check git status**: `git status` to see uncommitted work
2. **Read PROJECT_STATUS.md**: Understand current state
3. **Update todo list**: Mark tasks as in-progress

### After Making Changes
1. **Move debug files**: Any new debug scripts → `DEBUG_TEMP/`
2. **Update PROJECT_STATUS.md**: Document what changed
3. **Commit with clear message**: Describe WHAT and WHY
4. **Mark todos complete**: Update status in PROJECT_STATUS.md

### Git Commit Message Format
```
[Component] Brief description

- Bullet point of change 1
- Bullet point of change 2
- Impact: What this enables/fixes
```

Examples:
- `[Pipeline] Fix attack speed scaling bug - Divided by 100, marksmen DPS now correct`
- `[Data] Add effect_burn extraction - 63 new abilities, improves marksman detection`
- `[Archetypes] Implement fuzzy scoring algorithm - Enables multi-archetype membership`

---

## Project Goals (Prioritized)

### Phase 1: Core Data Pipeline ✅ (90% Complete)
**Goal**: Accurate champion attribute extraction from game data

- [x] Extract champion stats from Data Dragon
- [x] Extract spell damage/CC/cooldowns from champion.bin
- [x] Supplement missing data from effect_burn arrays
- [x] Compute spell-based attributes (burst, sustained, CC, mobility)
- [x] Integrate auto-attack damage into DPS calculations
- [ ] Validate all 171 champions have complete data
- [ ] Manual patches for complex champions (Aphelios, Sylas, etc.)

**Blockers**: 
- 14/18 marksmen misclassified due to incomplete spell data
- Some utility abilities incorrectly marked as damage

---

### Phase 2: Archetype Classification System 🔄 (70% Complete)
**Goal**: Assign strategic archetypes based on champion attributes

- [x] Define 13 archetypes with data-driven thresholds
- [x] Implement fuzzy scoring algorithm
- [x] Assign primary archetypes to all champions
- [ ] Fix marksman classification (currently 4/18 correct)
- [ ] Validate burst_assassin count (should be 15-20)
- [ ] Add secondary archetype detection (score > 0.7)
- [ ] Create archetype similarity matrix

**Current Metrics**:
- 171 champions classified
- 11/18 marksmen above DPS threshold (but only 4 classified correctly)
- 15 burst_assassins detected (target: 18-20)

**Blockers**:
- Need better spell damage data for marksmen
- False positives from effect_burn extraction (utility abilities)

---

### Phase 3: Archetype Synergies & Counters ⏳ (Not Started)
**Goal**: Define which archetypes synergize and counter each other

**Tasks**:
- [ ] Research team composition theory (front-to-back, dive, poke, etc.)
- [ ] Define synergy rules (e.g., engage_tank + marksman, diver + enchanter)
- [ ] Define counter rules (e.g., burst_assassin counters enchanter)
- [ ] Create synergy scoring matrix (13x13)
- [ ] Weight by importance (primary counter > soft counter)
- [ ] Validate against known team comps (e.g., "Protect the Kog'Maw")

**Data Structure**:
```json
{
  "burst_assassin": {
    "synergizes_with": ["engage_tank", "diver"],
    "counters": ["enchanter", "artillery_mage"],
    "countered_by": ["juggernaut", "warden"]
  }
}
```

---

### Phase 4: Draft Recommendation Engine ⏳ (Not Started)
**Goal**: Recommend champions for specific draft positions

**Features**:
1. **Input**: Current team composition (0-4 picked champions)
2. **Analysis**:
   - Missing archetype coverage (need engage? poke? sustain DPS?)
   - Enemy team archetype detection
   - Synergy scoring with existing picks
   - Counter-pick opportunities
3. **Output**: Ranked list of recommended champions with reasoning

**Algorithm Outline**:
```python
def recommend_champion(ally_picks, enemy_picks, position):
    # 1. Identify missing archetypes on team
    needed_archetypes = analyze_team_gaps(ally_picks)
    
    # 2. Find counter opportunities
    counter_targets = find_counterable_enemies(enemy_picks)
    
    # 3. Score all available champions
    for champion in champion_pool:
        score = (
            synergy_score(champion, ally_picks) * 0.4 +
            counter_score(champion, enemy_picks) * 0.3 +
            archetype_coverage(champion, needed_archetypes) * 0.3
        )
    
    # 4. Return top N with explanations
    return sorted_recommendations_with_reasoning
```

---

### Phase 5: Web Interface ⏳ (Not Started)
**Goal**: Interactive web app for draft analysis

**Tech Stack** (Suggested):
- Frontend: React + TypeScript
- Backend: FastAPI (Python)
- Data: JSON files (no database needed initially)
- Deployment: Vercel/Netlify (frontend) + Render/Railway (backend)

**UI Components**:
1. **Draft Board**: 5v5 champion selection grid
2. **Recommendation Panel**: Top 10 champions with reasoning
3. **Team Analysis**: Archetype coverage visualization
4. **Champion Detail**: Stats, archetypes, synergies on hover
5. **Filter Panel**: By role, archetype, attribute ranges

**Mockup Priority**:
- [ ] Sketch basic UI layout
- [ ] Define API endpoints
- [ ] Create backend API structure
- [ ] Build frontend components
- [ ] Connect frontend to backend

---

## Current Technical Debt

### Critical (Fix Before Phase 3)
1. **Incomplete spell damage data**: 14/18 marksmen below DPS threshold
   - Solution: Manual patch file for missing abilities
   - Affected: Ashe, Vayne, Lucian, Varus, Tristana, etc.

2. **False positive damage extraction**: Utility abilities marked as damage
   - Solution: Filter effect_burn by ability description keywords
   - Affected: Twitch Q, Caitlyn W, Draven W, etc.

3. **No secondary archetype assignment**: Champions fit multiple archetypes
   - Solution: Track all scores > 0.7
   - Needed for: Hybrid picks like Ezreal (marksman + burst_assassin)

### Medium (Fix During Phase 3-4)
1. **Global ability range cap**: Janna/Shen/GP have 25000-50000 range
   - Solution: Cap at 5000 for classification purposes
   - Impact: Marksman detection slightly skewed

2. **No ability synergies modeled**: Spell combos not captured
   - Example: Yasuo needs knock-ups, Orianna ball synergies
   - Solution: Add "requires" / "enables" tags to abilities

3. **Attack speed growth not perfectly modeled**: Linear approximation
   - Impact: Minor DPS calculation errors late-game
   - Solution: Use actual AS curves from Data Dragon

### Low (Nice to Have)
1. **No item build integration**: Assumes generic builds
   - Impact: Can't model on-hit vs crit marksmen
   - Future: Add common builds per archetype

2. **No rune/summoner spell modeling**: Flash/Ignite not considered
   - Impact: Miss some engage/kill pressure nuances
   - Future: Add as optional input

---

## Data Pipeline Architecture

```
Raw Data Sources
├── Data Dragon API (stats, abilities, cooldowns)
├── champion.bin (damage formulas, ratios)
└── effect_burn extraction (missing damage values)
                    ↓
        [build_spell_database.py]
                    ↓
        complete_spell_database.json (684 spells)
                    ↓
        [compute_spell_attributes.py]
                    ↓
        spell_based_attributes.json (171 champions)
                    ↓
        [assign_archetypes.py]
                    ↓
        archetype_assignments.json (13 archetypes)
                    ↓
        [Future: synergy_engine.py]
                    ↓
        [Future: recommendation_api.py]
                    ↓
        Web Interface (Draft Analyzer)
```

---

## When Working on This Project

### Always Ask Yourself:
1. **Does this move us toward the final goal?** (Draft recommendation web app)
2. **Is this debug/temp code?** → Put in `DEBUG_TEMP/`
3. **Does this need documentation?** → Update `PROJECT_STATUS.md`
4. **Can users understand why this change matters?** → Clear commit message

### Avoid:
- Creating multiple progress/findings markdown files (use 1 file)
- Leaving debug scripts in root directory
- Committing without updating PROJECT_STATUS.md
- Working on low-priority tasks when critical blockers exist

### Prioritize:
- Fixing marksman classification (blocks Phase 2 completion)
- Completing archetype validation (enables Phase 3)
- Clear documentation (helps user understand progress)
- Clean file structure (reduces confusion)

---

## Quick Reference Commands

### Git Workflow
```bash
git status                  # Check what changed
git diff                    # See file differences
git add -A                  # Stage all changes
git commit -m "Message"     # Commit with message
git log --oneline -10       # View recent commits
git checkout HEAD -- file   # Restore file from last commit
```

### Pipeline Execution
```bash
# Rebuild full pipeline
python data_pipeline/build_spell_database.py
python data_pipeline/compute_spell_attributes.py
python data_pipeline/assign_archetypes.py

# Quick validation
python DEBUG_TEMP/validate_marksmen.py
python DEBUG_TEMP/check_archetype_distribution.py
```

### File Organization
```bash
# Move debug files
Move-Item check_*.py DEBUG_TEMP/
Move-Item debug_*.py DEBUG_TEMP/
Move-Item validate_*.py DEBUG_TEMP/

# Clean up temp files
Remove-Item DEBUG_TEMP/*.json
```

---

## Success Metrics

### Phase 1 (Data Pipeline): DONE when
- ✅ All 171 champions have attributes computed
- ✅ 95%+ of abilities have damage/CC data
- ✅ Marksmen DPS values are realistic (100-300 range)
- [ ] No false positives in damage extraction (<5% error rate)

### Phase 2 (Archetypes): DONE when
- [ ] 16+/18 marksmen classified correctly (90%+)
- [ ] 18-20 burst_assassins detected
- [ ] All expected archetypes have 5+ champions
- [ ] Secondary archetypes tracked for hybrids

### Phase 3 (Synergies): DONE when
- [ ] 13x13 synergy matrix created
- [ ] Validated against 10+ known team comps
- [ ] Counter relationships defined
- [ ] Synergy scoring algorithm implemented

### Phase 4 (Recommendations): DONE when
- [ ] API returns top 10 champions with reasoning
- [ ] Explanations are human-readable
- [ ] Recommendations match theory (e.g., suggest engage vs poke comp)
- [ ] Performance: <100ms response time

### Phase 5 (Web App): DONE when
- [ ] Users can input draft state (10 champions)
- [ ] Real-time recommendations displayed
- [ ] Team composition analysis visible
- [ ] Deployed and accessible via URL

---

## Notes for Future Copilot Sessions

- **Marksman classification** is the current blocker - needs manual damage patches
- **effect_burn extraction** has false positives - needs filtering
- **Auto-attack damage** is working correctly after attack speed fix
- **Git is set up** - always commit before major refactors
- **User wants theory-based analysis** - no need for game winrate data
- **Final product is a web app** - keep this in mind for all design decisions

---

*Last Updated: November 13, 2025*
*Current Phase: 2 (Archetype Classification)*
*Next Milestone: Fix marksman classification to 16+/18 accuracy*
