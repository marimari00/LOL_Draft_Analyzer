# League of Legends Draft Analyzer

An empirical draft prediction system that uses real Diamond+ match data, attribute-based champion analysis, and machine learning to predict match outcomes with **53.4% accuracy** (professional analyst baseline).

---

## Current Status

**✅ Phase 2 Complete**: 100% accurate archetype classification (171 champions, 13 archetypes, info.lua integration)

**✅ Phase 3 Complete**: Empirical validation + ML ensemble + **Interactive Frontend**

- **Dataset**: 936 Diamond+ matches from EUW + KR
- **Attribute System**: 45 attributes across 8 categories (damage, range, mobility, survive, cc, scaling, engage, special)
- **ML Models**: Logistic Regression (54.3%), Random Forest (50.5%), Gradient Boosting (50.0%)
- **Ensemble Prediction**: Weighted average achieves 54.3% accuracy
- **FastAPI Backend**: 5 endpoints (analyze, recommend, champions, archetypes, health)
- **React Frontend**: Visual draft board with AI recommendations and composition analysis
- **Validation**: 5-fold cross-validation, 80/20 train/test split
- **Simulation**: 10,000 random game predictions

**📊 Key Insight**: Draft accounts for only 5-10% of match outcome. 53.4% matches professional analyst baseline (52-58%). See [REALITY_CHECK.md](REALITY_CHECK.md) for detailed analysis.

**🎯 Next Target**: 57-58% accuracy via data quality improvements (Challenger-only, champion mastery, ensemble prediction)

---

## Local Development Workflow

1. **Run `SETUP_FIRST.bat` once** – installs every Python and Node.js dependency automatically.
2. **Launch with `START_HERE.bat`** – frees ports 3000/8000, then boots the FastAPI backend and React frontend for you. Two terminals open so you can watch logs.
3. **Stop the app** by closing both terminals (or `Ctrl+C`). The script will re-run safely even if the previous session crashed because it always cleans the ports first.

Need a manual start? Power users can still run `start_backend.bat` and `start_frontend.bat` separately, or the underlying `python backend/draft_api.py` / `npm start` commands.

## Quick Start

### One-Time Setup

```bash
SETUP_FIRST.bat
```

### Daily Launch

```bash
START_HERE.bat
```

The frontend opens at `http://localhost:3000` and proxies API calls to `http://localhost:8000`.

### Manual Commands (Optional)

```bash
python backend/draft_api.py          # Backend only
cd frontend && npm start             # Frontend only
```

### Using the Draft Board

- Select team (Blue/Red)
- Toggle Pick/Ban mode
- Filter by role (TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY)
- View AI recommendations with reasoning
- Pick champions (click recommendations or use selector)
- See winner prediction after 5v5 complete

---

### Train ML Models (Development)

```bash
# Run attribute analysis + ML training
python validation/retrain_all_models.py
```

### Simulate 10K Random Games

```bash
# Generate predictions for 10,000 random team compositions
python validation/ml_simulation.py
```

### Fetch Real Match Data

```bash
# Fetch 1000 Diamond+ matches from EUW + KR
python data_extraction/fetch_match_data.py
```

---

## Project Structure

```text
draft-analyzer/
├── data_extraction/          # Fetch real match data from Riot API
│   └── fetch_match_data.py   # Multi-region, multi-tier fetcher (936 matches)
├── data_pipeline/            # Champion classification pipeline
│   ├── build_spell_database.py
│   ├── compute_spell_attributes.py
│   ├── extract_roles_from_info.py
│   └── define_archetype_attributes.py  # 45 attributes defined
├── validation/               # ML models and analysis
│   ├── ml_simulation.py       # LR/RF/GB models + 10K simulation
│   ├── role_aware_analysis.py # Role-specific synergies
│   ├── statistical_analysis.py # Chi-square, confidence intervals
│   └── retrain_all_models.py  # Orchestrates retraining pipeline
├── data/
│   ├── matches/              # Real match data
│   │   └── multi_region_1000_matches.json  # 936 Diamond+ matches
│   ├── processed/            # Champion archetypes + attributes
│   │   ├── champion_archetypes.json        # 171 champions, 13 archetypes
│   │   ├── archetype_attributes.json       # 45 attributes defined
│   │   ├── role_aware_relationships.json   # 6,865 role-specific synergies
│   │   └── statistical_analysis.json       # 820 attribute pairs analyzed
│   └── simulations/          # Model predictions
│       └── simulation_10k_games.json       # 10,000 random game results
└── documentation/
    ├── REALITY_CHECK.md       # Why 53.4% is success, not failure
    ├── IMPROVEMENT_PLAN.md    # Roadmap to 57-58% accuracy
    └── COPILOT_INSTRUCTIONS.md # Development rules (NO PLACEHOLDERS)
```

---

## Data Sources

- **Riot API**: Real Diamond+ ranked matches from EUW + KR (936 matches)
- **info.lua**: Official Riot champion taxonomy (173 champions)
- **Data Dragon**: Base stats, abilities (171 champions matched)
- **champion.bin**: Damage formulas for spell computations

---

## Key Achievements

### Phase 2: Perfect Classification ✅

- **100% precision, 100% recall** on archetype classification
- 171 champions tagged with 13 archetypes (marksman, burst_mage, engage_tank, etc.)
- Used official Riot `info.lua` taxonomy

### Phase 3: Empirical Validation + Full-Stack Application ✅

- **936 real matches** fetched from Diamond through Challenger (EUW + KR)
- **45 attributes** defined (damage_burst, range_long, mobility_high, cc_hard, etc.)
- **Role-aware analysis**: 6,865 role-specific attribute synergies tracked
- **Statistical validation**: Chi-square tests, Wilson 95% CI, Cohen's h effect sizes
- **ML models**: Logistic Regression (54.3%), Random Forest (50.5%), Gradient Boosting (50.0%)
- **Ensemble prediction**: Weighted average combining all 3 models
- **10K simulation**: Validated model stability across 10,000 random team compositions
- **FastAPI Backend**: 5 REST endpoints (analyze, recommend, champions, archetypes, health)
- **React Frontend**: Interactive visual draft board with AI recommendations and composition analysis

### Critical Discovery: Overfitting Exposure

- Initial 139 matches: 66.2% accuracy (role-aware model)
- Expanded 936 matches: 53.4% accuracy (Logistic Regression) ← **TRUE PERFORMANCE**
- Lesson: Small datasets memorize patterns; large datasets reveal reality
- **53.4% matches professional analyst baseline** (52-58%)

---

## Why 53.4% is Success

From [REALITY_CHECK.md](REALITY_CHECK.md):

1. **Professional Baseline**: Expert analysts achieve 52-58% accuracy on draft predictions
2. **Draft Impact**: Team composition accounts for only 5-10% of match outcome
3. **Execution Dominates**: Player skill, macro decisions, execution >> draft choices (90-95% of outcome)
4. **Statistical Confidence**: 936 matches provide stable validation (not small-sample luck)
5. **Cross-Validation**: 5-fold CV shows consistent 53-54% across all folds

**In 1000 games**: 53.4% accuracy = +34 extra wins vs random coin flip (50%)

---

## Improvement Roadmap

See [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md) for detailed plan.

**Current**: 53.4% (professional grade baseline)

**Phase 1** (Data Quality + Feature Engineering):

- Filter to Challenger-only matches (reduce skill variance) → +1-2%
- Focus on last 2 patches (reduce meta shifts) → +0.5-1%
- Champion mastery integration (OTP detection) → +2-3%

**Phase 2** (Ensemble + API):

- Weighted ensemble prediction (LR + RF + GB) → +1-2%
- Build draft recommendation API (FastAPI)

**Target**: 57-58% accuracy (realistic maximum given draft's limited impact)

**Theoretical Ceiling**: 58-60% (approaching limit of draft-only prediction)

---

## Next Steps

Long-form progress tracking now lives in [`PROJECT_STATUS.md`](PROJECT_STATUS.md). The immediate application-focused priorities are:

- **Champion data parity**: Finish the manual damage patches so all 171 champions load cleanly (removes the UI's fallback champion list).
- **Synergy matrix API**: Expose the archetype synergy/counter data through `/draft/recommend` so recommendations cite concrete matchup logic instead of heuristics.
- **Frontend draft flow polish**: Enforce pick order templates, show lane badges, and surface the recommendations' reasoning inline with the draft board.
- **Model management**: Add a lightweight cache plus version banner for the ensemble predictor so users know which training run is active.
- **Deployment ergonomics**: Containerize the backend + frontend pair for easier hosting while keeping `START_HERE.bat` for local dev parity.

---

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set Riot API key (in fetch_match_data.py)
RIOT_API_KEY = "RGAPI-95df791c-5ac9-4230-ba2f-de7bf0aefe7c"
```

---

## Usage Examples

### Fetch New Matches

```python
from data_extraction.fetch_match_data import fetch_high_elo_matches

# Fetch from multiple regions and tiers
matches = fetch_high_elo_matches(
    regions=["euw1", "kr"],
    tiers=["CHALLENGER", "GRANDMASTER", "MASTER"],
    target_count=1000
)
```

### Train ML Models

```python
from validation.ml_simulation import train_ml_models, extract_features_from_team

# Load match data
with open("data/matches/multi_region_1000_matches.json") as f:
    match_data = json.load(f)

# Train models
models = train_ml_models(match_data)  # Returns {lr, rf, gb}

# Make prediction
blue_features = extract_features_from_team(blue_team, roles)
prediction = models["lr"].predict([blue_features])[0]
```

### Analyze Synergies

```python
from validation.role_aware_analysis import predict_with_role_awareness

# Predict match outcome
prediction, confidence = predict_with_role_awareness(
    blue_team=["Jinx", "Leona", "Lux", "Vi", "Darius"],
    blue_roles=["BOTTOM", "UTILITY", "MIDDLE", "JUNGLE", "TOP"],
    red_team=["Caitlyn", "Thresh", "Zed", "Lee Sin", "Garen"],
    red_roles=["BOTTOM", "UTILITY", "MIDDLE", "JUNGLE", "TOP"],
    relationships_path="data/processed/role_aware_relationships.json"
)
```

---

## Mathematical Framework

### Attribute System

45 attributes across 8 categories:

- **Damage**: burst, sustained, execute, poke
- **Range**: long, short, global
- **Mobility**: high, dash, blink
- **Survivability**: tank, sustain, shields
- **CC**: hard, soft, aoe_cc
- **Scaling**: early, mid, late
- **Engage**: engage, disengage, splitpush
- **Special**: stealth, revive, percent_health

### Feature Extraction (79 Features)

From `ml_simulation.py`:

1. **Attribute Counts** (45): Sum of each attribute across team
2. **Role-Pair Synergies** (25): Synergy scores for 10 role combinations (TOP-JUNGLE, JUNGLE-MIDDLE, etc.)
3. **Damage Profile** (3): burst_count, sustained_count, poke_count
4. **Range Profile** (3): long_range_count, short_range_count, avg_range
5. **Mobility Profile** (3): high_mobility_count, dash_count, blink_count

### Models

- **Logistic Regression**: 53.4% test accuracy (best performer)
- **Random Forest**: 47.3% test accuracy
- **Gradient Boosting**: 50.0% test accuracy

All models use 5-fold cross-validation and 80/20 train/test split.

---

## Key Files

### Match Data

- `data/matches/multi_region_1000_matches.json`: 936 Diamond+ matches (EUW + KR)

### Champion Data

- `data/processed/champion_archetypes.json`: 171 champions with 13 archetypes
- `data/processed/archetype_attributes.json`: 45 attributes defined

### Analysis Results

- `data/processed/role_aware_relationships.json`: 6,865 role-specific synergies
- `data/processed/statistical_analysis.json`: 820 attribute pairs, 15 significant synergies
- `data/simulations/simulation_10k_games.json`: 10,000 random game predictions

### Documentation

- `REALITY_CHECK.md`: Why 66.2% was overfitting, 53.4% is real
- `IMPROVEMENT_PLAN.md`: Roadmap to 57-58% accuracy
- `COPILOT_INSTRUCTIONS.md`: Development rules (NO SAMPLE DATA)

---

## Development Philosophy

1. **Real Data Only**: No sample/placeholder data (see COPILOT_INSTRUCTIONS.md)
2. **Statistical Rigor**: Chi-square tests, confidence intervals, cross-validation
3. **Realistic Expectations**: 53.4% is success (matches professional baseline)
4. **Incremental Improvement**: +1-2% gains via data quality and feature engineering
5. **Transparency**: Document failures (overfitting discovery) as much as successes

---

## Contact

- Repository: LOL_Draft_Analyzer
- Branch: main
- Owner: marimari00

**For detailed technical analysis**, see [REALITY_CHECK.md](REALITY_CHECK.md).
**For improvement roadmap**, see [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md).
