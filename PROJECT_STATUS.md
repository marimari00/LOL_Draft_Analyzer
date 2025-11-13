# Draft Analyzer Project Status

*Last Updated: November 13, 2025*

---

## 1. Project Vision

**Goal**: Build a web-based draft analyzer that recommends champions based on attributes and archetypes—similar to iTero/DPMLOL but **theory-driven, not winrate-driven**. The system should reveal unexpected pick/ban strategies through archetype synergies and counters.

**Key Principles**:
- **Attribute-Based**: Champions classified by computed attributes (burst, sustain, CC, mobility)
- **Theory-Driven**: No winrate data—purely strategic analysis
- **Archetype-Focused**: 13 strategic archetypes (burst_assassin, marksman, engage_tank, etc.)
- **Synergy-Aware**: Recommend based on team composition and enemy counters

**Use Cases**:
1. Team building: "We have engage tank + marksman, what's missing?"
2. Counter-picking: "Enemy picked Kog'Maw, suggest counters"
3. Ban strategy: "Which bans hurt enemy team comp most?"
4. Learning: "What makes a good dive composition?"

---

## 2. Current Progress

### ✅ Completed
- **Data extraction pipeline**: 171 champions, 684 spells processed
- **Spell database**: 389 abilities with damage data (was 329)
- **Attribute computation**: Burst, sustained DPS, CC, mobility scores
- **Auto-attack integration**: Fixed attack speed bug, added AA damage to DPS
- **Archetype definitions**: 13 archetypes with data-driven thresholds
- **Fuzzy scoring algorithm**: Implemented trapezoidal membership functions
- **Initial classification**: All 171 champions assigned primary archetype
- **Git version control**: Repository initialized with clean commits

### 🔄 In Progress
- **Marksman classification accuracy**: Currently 4/18 correct (target: 16+/18)
- **Spell damage completeness**: 14 marksmen missing key ability damage
- **False positive filtering**: Some utility abilities incorrectly marked as damage

### ⏳ Pending (Not Started)
- Phase 3: Archetype synergies & counter matrix
- Phase 4: Draft recommendation engine
- Phase 5: Web interface (React + FastAPI)

---

## 3. Architecture

### Data Flow
```
┌─────────────────────────────────────────────────────────────────┐
│ Raw Data Sources                                                │
│ ├── Data Dragon API (stats, abilities, cooldowns)              │
│ ├── champion.bin (damage formulas, ratios)                     │
│ └── effect_burn arrays (supplemental damage values)            │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
        ┌────────────────────────────┐
        │ build_spell_database.py    │
        │ - Merge damage + metadata  │
        │ - Detect CC types          │
        │ - Normalize ranges         │
        └────────────┬───────────────┘
                     ↓
        complete_spell_database.json (684 spells)
                     ↓
        ┌────────────────────────────┐
        │ compute_spell_attributes.py│
        │ - Calculate burst/sustained│
        │ - Aggregate CC scores      │
        │ - Compute mobility         │
        │ - Add auto-attack damage   │
        └────────────┬───────────────┘
                     ↓
        spell_based_attributes.json (171 champions)
                     ↓
        ┌────────────────────────────┐
        │ assign_archetypes.py       │
        │ - Fuzzy scoring            │
        │ - Primary archetype        │
        │ - Multi-membership         │
        └────────────┬───────────────┘
                     ↓
        archetype_assignments.json (13 archetypes)
                     ↓
        ┌─────────────────────────────────────────────┐
        │ Future: synergy_engine.py                   │
        │ - Synergy matrix (13x13)                    │
        │ - Counter relationships                     │
        └────────────┬────────────────────────────────┘
                     ↓
        ┌─────────────────────────────────────────────┐
        │ Future: recommendation_api.py (FastAPI)     │
        │ - Draft state input                         │
        │ - Champion recommendations                  │
        │ - Reasoning explanations                    │
        └────────────┬────────────────────────────────┘
                     ↓
        ┌─────────────────────────────────────────────┐
        │ Web Interface (React)                       │
        │ - Draft board (5v5 grid)                    │
        │ - Recommendation panel                      │
        │ - Team analysis visualizations              │
        └─────────────────────────────────────────────┘
```

### Technology Stack
- **Data Processing**: Python 3.11+
- **Backend API**: FastAPI (planned)
- **Frontend**: React + TypeScript (planned)
- **Data Storage**: JSON files (no database needed)
- **Deployment**: Vercel/Netlify (frontend), Render/Railway (backend)

---

## 4. Pipeline Status

### Phase 1: Core Data Pipeline ✅ 90%

| Stage | Status | Details |
|-------|--------|---------|
| Data Dragon fetch | ✅ Done | 171 champions, base stats, abilities |
| champion.bin extraction | ✅ Done | Damage formulas, ratios for 329 abilities |
| effect_burn supplementation | ✅ Done | +60 abilities extracted from Data Dragon |
| Spell database build | ✅ Done | 684 spells merged with metadata |
| Attribute computation | ✅ Done | Burst, sustained, CC, mobility scores |
| Auto-attack integration | ✅ Done | Fixed attack speed bug, added AA DPS |
| Data validation | 🔄 70% | 14 marksmen still incomplete |
| Manual patches | ⏳ Pending | Need damage for Vayne Q, Ashe W, etc. |

**Current Metrics**:
- 171 champions processed
- 684 spells (389 with damage data)
- 254 spells with CC
- 0 missing cooldowns

**Known Issues**:
- 14/18 marksmen below DPS threshold (119.2)
- False positives: utility abilities marked as damage (Twitch Q, Caitlyn W)
- Global abilities (Janna R, Shen R) have 25000+ range

---

### Phase 2: Archetype Classification 🔄 70%

| Stage | Status | Details |
|-------|--------|---------|
| Define archetypes | ✅ Done | 13 archetypes identified |
| Compute thresholds | ✅ Done | Percentile-based (p25/p50/p75/p90) |
| Implement fuzzy scoring | ✅ Done | Trapezoidal membership functions |
| Assign primary archetypes | ✅ Done | All 171 champions classified |
| Validate classifications | 🔄 40% | Marksmen only 22% accurate |
| Secondary archetypes | ⏳ Pending | Track scores > 0.7 |
| Similarity matrix | ⏳ Pending | Champion-to-champion comparison |

**Current Distribution**:
```
burst_mage          : 28 (16.4%)
battle_mage         : 26 (15.2%)
juggernaut          : 22 (12.9%)
skirmisher          : 18 (10.5%)
specialist          : 18 (10.5%)
burst_assassin      : 15 ( 8.8%)
marksman            : 11 ( 6.4%)  ← Should be 18 (10.5%)
enchanter           : 11 ( 6.4%)
engage_tank         :  8 ( 4.7%)
diver               :  8 ( 4.7%)
artillery_mage      :  3 ( 1.8%)
catcher             :  3 ( 1.8%)
warden              :  0 ( 0.0%)  ← Should have 2-3
```

**Validation Results** (Marksmen: 4/18 correct):
- ✅ Correct: Jinx, Jhin, MissFortune, Corki
- ✗ Misclassified: Ashe, Vayne, Caitlyn, Lucian, Ezreal, etc.

**Issues**:
- Most marksmen below sustained_dps threshold (119.2)
- Ezreal classified as burst_assassin (actually correct due to mobility)
- Caitlyn has inflated DPS from trap damage (false positive)

---

### Phase 3: Synergies & Counters ⏳ 0%

| Task | Status | Priority |
|------|--------|----------|
| Research team comp theory | ⏳ Pending | High |
| Define synergy rules | ⏳ Pending | High |
| Define counter rules | ⏳ Pending | High |
| Create 13x13 matrix | ⏳ Pending | Medium |
| Weight importance | ⏳ Pending | Medium |
| Validate against known comps | ⏳ Pending | High |

**Blocked By**: Phase 2 validation must reach 90%+ accuracy first

---

### Phase 4: Recommendation Engine ⏳ 0%

| Component | Status | Priority |
|-----------|--------|----------|
| API design | ⏳ Pending | High |
| Team gap analysis | ⏳ Pending | High |
| Counter-pick detection | ⏳ Pending | High |
| Synergy scoring | ⏳ Pending | High |
| Reasoning generator | ⏳ Pending | Medium |
| Performance optimization | ⏳ Pending | Low |

**Blocked By**: Phase 3 synergy matrix required

---

### Phase 5: Web Interface ⏳ 0%

| Component | Status | Priority |
|-----------|--------|----------|
| UI mockup/design | ⏳ Pending | High |
| React app scaffolding | ⏳ Pending | High |
| Draft board component | ⏳ Pending | High |
| Recommendation panel | ⏳ Pending | High |
| Team analysis view | ⏳ Pending | Medium |
| Backend API integration | ⏳ Pending | High |
| Deployment setup | ⏳ Pending | Low |

**Blocked By**: Phase 4 API must be functional

---

## 5. Known Issues

### Critical (Blocks Phase 2 Completion)

**Issue #1: Marksman Classification Accuracy (22%)**
- **Problem**: Only 4/18 marksmen classified correctly
- **Root Cause**: Missing spell damage data from champion.bin
- **Examples**: 
  - Ashe W (Volley): Only 5-13 base damage extracted (should have AD ratio)
  - Vayne Q (Tumble): Not in champion.bin (AA modifier)
  - Lucian E: Missing entirely
- **Impact**: Can't validate archetype system, blocks Phase 3
- **Solution**: Create `manual_damage_patches.json` with correct values for top 15 marksmen
- **Effort**: 2-3 hours (research + implementation)

**Issue #2: False Positive Damage Extraction**
- **Problem**: Utility abilities incorrectly marked as damage
- **Examples**:
  - Twitch Q (Ambush): Stealth ability, no damage
  - Caitlyn W (Trap): Extracted 35-215 damage (inflates her DPS)
  - Draven W (Blood Rush): Movement speed buff
- **Impact**: Inflates DPS for some champions (Caitlyn: 251 instead of ~120)
- **Solution**: Filter effect_burn by description keywords (avoid "stealth", "speed", "bonus")
- **Effort**: 1 hour

**Issue #3: No Secondary Archetype Tracking**
- **Problem**: Champions only assigned 1 archetype (misses hybrids)
- **Examples**:
  - Ezreal: Both marksman AND burst_assassin (high mobility)
  - Senna: Both marksman AND enchanter (heal/shield)
  - Pyke: Both burst_assassin AND catcher (hook)
- **Impact**: Recommendations miss hybrid playstyles
- **Solution**: Track all archetype scores > 0.7 threshold
- **Effort**: 30 minutes

### Medium (Fix During Phase 3)

**Issue #4: Global Ability Range Cap**
- **Problem**: Janna/Shen/GP ults have 25000-50000 range
- **Impact**: Skews marksman detection (max_range filter)
- **Solution**: Cap range at 5000 for classification
- **Effort**: 15 minutes

**Issue #5: No Champion-Specific Mechanics**
- **Problem**: Unique mechanics not modeled
- **Examples**:
  - Yasuo requires knock-ups (not in data)
  - Aphelios has 5 weapons (only averaged)
  - Sylas ult depends on enemy team
- **Impact**: Can't give nuanced recommendations
- **Solution**: Add "requires" and "enables" tags to champions
- **Effort**: 3-4 hours (manual tagging)

### Low (Nice to Have)

**Issue #6: No Item Build Modeling**
- **Problem**: Assumes generic builds (60 bonus AD, 100 AP)
- **Impact**: Can't distinguish on-hit vs crit marksmen
- **Solution**: Add archetype-specific builds
- **Effort**: 2 hours

**Issue #7: No Rune/Summoner Spell Consideration**
- **Problem**: Flash/Ignite/Exhaust not in analysis
- **Impact**: Miss some kill pressure / engage scenarios
- **Solution**: Optional input in recommendation API
- **Effort**: 1 hour

---

## 6. Next Steps

### Immediate (Today/Tomorrow)
1. **Fix marksman classification** → 16+/18 accuracy
   - [ ] Create `manual_damage_patches.json` with correct values for:
     - Ashe W (Volley): 20-100 + 1.0 AD ratio
     - Vayne Q (Tumble): 50% AD modifier on next attack
     - Lucian E (Dash): 30-70 magic damage
     - Varus Q (Arrow): 10-150 + 1.6 AD ratio
     - Tristana E (Bomb): 70-190 + 0.5 AP + 0.5-0.9 AD
   - [ ] Apply patches and regenerate attributes
   - [ ] Validate: 16+/18 marksmen correct

2. **Filter false positive damage**
   - [ ] Add keyword blacklist: "stealth", "speed", "invisible", "bonus movement"
   - [ ] Rerun effect_burn extraction
   - [ ] Verify: Caitlyn DPS drops to ~120, Twitch to ~120

3. **Enable secondary archetypes**
   - [ ] Modify `assign_archetypes.py` to track all scores > 0.7
   - [ ] Add `secondary_archetypes` field to output
   - [ ] Validate: Ezreal shows [marksman, burst_assassin]

### This Week
4. **Complete Phase 2 validation**
   - [ ] Check burst_assassin count (should be 18-20)
   - [ ] Verify all archetypes have 3+ champions except warden (0-2 is OK)
   - [ ] Create validation report with metrics

5. **Start Phase 3: Synergy research**
   - [ ] Document team composition archetypes:
     - Front-to-back (engage + marksman + peel)
     - Dive (diver + burst_assassin + enchanter)
     - Poke (artillery_mage + catcher + disengage)
     - Split push (skirmisher + waveclear + global)
   - [ ] Define synergy rules (which archetypes work together)
   - [ ] Define counter rules (which archetypes counter others)

### Next Week
6. **Implement synergy engine**
   - [ ] Create `synergy_definitions.json` with 13x13 matrix
   - [ ] Implement `synergy_engine.py` to score team comps
   - [ ] Validate against known comps (Protect Kog, Juggermaw, etc.)

7. **Design recommendation API**
   - [ ] Sketch API endpoints (`POST /recommend`, `GET /archetypes`, etc.)
   - [ ] Define request/response formats
   - [ ] Create FastAPI skeleton

### This Month
8. **Build recommendation engine**
   - [ ] Implement team gap analysis
   - [ ] Implement counter-pick detection
   - [ ] Create reasoning generator
   - [ ] Add champion filtering (by role, archetype)

9. **Create web interface mockup**
   - [ ] Sketch UI layout (draft board, recommendations, analysis)
   - [ ] Design component hierarchy
   - [ ] Choose color scheme / styling

10. **Deploy MVP**
    - [ ] Build React frontend
    - [ ] Deploy backend API
    - [ ] Connect frontend to backend
    - [ ] Test with real draft scenarios

---

## 7. Recent Changes

### November 13, 2025

**[Data Pipeline] Fixed attack speed scaling bug**
- Problem: Attack speed stored as percentage (33.65 = 0.3365 AS) in Data Dragon
- Fix: Divided by 100 in `compute_spell_attributes.py`
- Impact: Marksmen DPS now realistic (was 16k, now 150)
- Commit: `9b01624`

**[Data Pipeline] Integrated auto-attack damage**
- Added AA damage to burst/sustained calculations
- Formula: Burst = AS × 3 × AD, Sustained = AS × 10 × 0.6 × AD
- Impact: Marksmen count improved from 3 → 11 (raw data, not classification)
- Commit: `9b01624`

**[Data Pipeline] Extracted spell damage from effect_burn**
- Created `extract_effect_burn_damage.py` to parse Data Dragon arrays
- Extracted 63 abilities across 46 champions
- Merged into `champion_damage_data_merged.json`
- Impact: Spell database now 389 abilities (was 329)
- Issues: Some false positives (utility abilities)
- Commit: `9b01624`

**[Archetypes] Implemented fuzzy scoring assignment**
- Created `assign_archetypes.py` with trapezoidal membership
- All 171 champions assigned primary archetype
- Current accuracy: Marksmen 4/18 (22%)
- Commit: `4d42d8e`

**[Project] Set up Git version control**
- Initialized repository
- Created `.gitignore`
- Committed initial state
- Fixes file corruption issues
- Commit: `9b01624`, `4d42d8e`

**[Project] Organized file structure**
- Created `DEBUG_TEMP/` folder for temporary scripts
- Created `COPILOT_INSTRUCTIONS.md` with workflow guide
- Consolidated progress docs into `PROJECT_STATUS.md`

---

## 8. Validation Metrics

### Data Quality
- **Champion coverage**: 171/171 (100%)
- **Spell coverage**: 684/684 (100%)
- **Damage data completeness**: 389/684 (56.9%)
- **CC data completeness**: 254/684 (37.1%)
- **Marksmen with sufficient DPS**: 11/18 (61%)

### Classification Accuracy
- **Marksmen**: 4/18 (22%) ← **CRITICAL ISSUE**
- **Burst assassins**: ~15/20 (75% estimated)
- **Tanks**: Not validated yet
- **Mages**: Not validated yet
- **Overall**: Unknown (need validation suite)

### Performance
- **Spell database build**: ~2 seconds
- **Attribute computation**: ~1 second
- **Archetype assignment**: <1 second
- **Total pipeline**: ~5 seconds

---

## 9. File Structure

```
Draft_Analyzer_Project/
├── data/
│   ├── raw/
│   │   ├── data_dragon_champions.json        # Base stats, abilities
│   │   ├── community_dragon_champions.json   # Additional metadata
│   │   └── champion_damage_data.json         # Extracted from champion.bin
│   └── processed/
│       ├── champion_damage_data_merged.json  # Raw + effect_burn combined
│       ├── complete_spell_database.json      # 684 spells with all data
│       ├── spell_based_attributes.json       # 171 champions, computed attrs
│       ├── archetype_definitions.json        # 13 archetypes, thresholds
│       └── archetype_assignments.json        # Classifications
├── data_pipeline/
│   ├── build_spell_database.py               # Merge damage + metadata
│   ├── compute_spell_attributes.py           # Calculate burst/sustain/CC
│   ├── assign_archetypes.py                  # Fuzzy scoring classifier
│   ├── extract_effect_burn_damage.py         # Supplement missing damage
│   └── merge_damage_patches.py               # Apply manual patches
├── DEBUG_TEMP/                               # ← Temporary/debug scripts go here
│   └── (various test/validation scripts)
├── backend/                                  # Future: FastAPI app
├── notebooks/                                # Jupyter analysis notebooks
├── config/                                   # Configuration files
├── .gitignore                                # Git ignore rules
├── requirements.txt                          # Python dependencies
├── README.md                                 # Project overview
├── COPILOT_INSTRUCTIONS.md                   # This file's guide
└── PROJECT_STATUS.md                         # This file
```

---

## 10. Quick Commands

### Run Full Pipeline
```bash
cd c:\Users\marin\Desktop\Draft_Analyzer_Project

# Rebuild everything
python data_pipeline/build_spell_database.py
python data_pipeline/compute_spell_attributes.py
python data_pipeline/assign_archetypes.py
```

### Validation
```bash
# Check marksmen classification
python DEBUG_TEMP/validate_marksmen.py

# Check archetype distribution
python DEBUG_TEMP/check_archetype_distribution.py
```

### Git Workflow
```bash
git status                          # What changed?
git diff                            # Show changes
git add -A                          # Stage everything
git commit -m "Descriptive message" # Commit
git log --oneline -10               # View history
git checkout HEAD -- filename       # Restore file
```

### File Organization
```bash
# Move debug files to DEBUG_TEMP
Move-Item check_*.py DEBUG_TEMP\
Move-Item debug_*.py DEBUG_TEMP\
Move-Item validate_*.py DEBUG_TEMP\

# Clean temp files
Remove-Item DEBUG_TEMP\*.json
```

---

*For detailed workflow instructions, see `COPILOT_INSTRUCTIONS.md`*
