# Draft Analyzer API Documentation

**Philosophy**: Theoretical archetypal analysis, not live data competition. This API provides draft recommendations based on champion archetypes, attribute synergies, and compositional balance - not meta trends or win rates.

---

## Quick Start

### 1. Start the API Server

```bash
python backend/draft_api.py
```

Server runs on: `http://localhost:8000`

### 2. Test the API

```bash
python test_api.py
```

---

## Architecture

### Ensemble Prediction System

Combines 3 ML models with weighted averaging:

- **Logistic Regression** (54.3% accuracy) - Best performer, highest weight
- **Random Forest** (50.5% accuracy)  
- **Gradient Boosting** (50.0% accuracy)

**Weighting Strategy**: Models weighted by base performance × prediction confidence. High-confidence predictions from strong models get more weight.

**Feature Extraction**: 78 features from team compositions:

- 45 attribute counts (damage, range, mobility, cc, etc.)
- 10 role-pair synergy scores
- Damage/range/mobility/scaling distributions

**Training Data**: 936 Diamond+ matches from EUW + KR (Challenger through Diamond tiers)

---

## API Endpoints

### 1. Health Check

```http
GET /
```

**Response:**

```json
{
  "status": "online",
  "version": "1.0.0",
  "philosophy": "Archetypal draft analysis - theory over meta"
}
```

---

### 2. Analyze Team Compositions

```http
POST /draft/analyze
```

Analyzes complete 5v5 team compositions and predicts match outcome.

**Request Body:**

```json
{
  "blue_team": ["Jinx", "Leona", "Orianna", "Vi", "Darius"],
  "blue_roles": ["BOTTOM", "UTILITY", "MIDDLE", "JUNGLE", "TOP"],
  "red_team": ["Caitlyn", "Thresh", "Zed", "Lee Sin", "Renekton"],
  "red_roles": ["BOTTOM", "UTILITY", "MIDDLE", "JUNGLE", "TOP"]
}
```

**Response:**

```json
{
  "prediction": {
    "winner": "red",
    "confidence": 0.394,
    "blue_win_probability": 0.275,
    "red_win_probability": 0.725,
    "model_breakdown": {
      "logistic": 0.361,
      "random_forest": 0.445,
      "gradient_boosting": 0.103
    }
  },
  "blue_analysis": {
    "archetypes": ["marksman", "engage_tank", "burst_mage", "diver", "juggernaut"],
    "archetype_distribution": {
      "marksman": 1,
      "engage_tank": 1,
      "burst_mage": 1,
      "diver": 1,
      "juggernaut": 1
    },
    "damage_types": ["damage_physical", "damage_magic"],
    "range_profile": ["range_long", "range_melee"],
    "mobility_profile": ["mobility_medium", "mobility_low"],
    "cc_profile": ["cc_hard", "cc_aoe"],
    "composition_type": "front_to_back"
  },
  "red_analysis": {
    "archetypes": ["marksman", "catcher", "burst_assassin", "diver", "juggernaut"],
    "composition_type": "dive"
  },
  "archetypal_insights": [
    "All models agree on outcome (strong consensus)"
  ]
}
```

**Analysis:**

- **prediction**: Ensemble model prediction with individual model breakdowns
- **blue_analysis**: Archetypal composition analysis for blue team
- **red_analysis**: Archetypal composition analysis for red team
- **archetypal_insights**: Theoretical reasoning for prediction

**Composition Types:**

- `front_to_back`: Tank + Marksman + Enchanter (protect the carry)
- `dive`: Multiple divers/assassins (jump backline)
- `poke`: Artillery mage + long range (whittle down before fight)
- `skirmish`: Multiple fighters (extended teamfights)
- `mixed`: No clear pattern

---

### 3. Recommend Champions

```http
POST /draft/recommend
```

Recommends champions for current draft state based on:

1. **Team Composition Needs**: Filling missing archetypes (damage, tank, support)
2. **Counter-Pick Opportunities**: Countering enemy threats
3. **Role Synergies**: Attributes that synergize with existing picks
4. **Archetypal Balance**: Maintaining compositional coherence

**Request Body:**

```json
{
  "draft_state": {
    "blue_picks": ["Jinx", "Leona"],
    "blue_bans": ["Yasuo", "Zed"],
    "red_picks": ["Caitlyn", "Thresh"],
    "red_bans": ["Darius", "Vi"],
    "next_pick": "blue"
  },
  "role": "MIDDLE",
  "limit": 5
}
```

**Parameters:**

- `draft_state.blue_picks`: List of blue team champions (0-5)
- `draft_state.blue_bans`: List of blue team bans (0-5)
- `draft_state.red_picks`: List of red team champions (0-5)
- `draft_state.red_bans`: List of red team bans (0-5)
- `draft_state.next_pick`: `"blue"` or `"red"` (which team picks next)
- `role`: Optional role filter (`"TOP"`, `"JUNGLE"`, `"MIDDLE"`, `"BOTTOM"`, `"UTILITY"`)
- `limit`: Number of recommendations to return (default: 5, max: 20)

**Response:**

```json
{
  "recommendations": [
    {
      "champion": "Orianna",
      "score": 0.73,
      "archetype": "burst_mage",
      "reasoning": [
        "Fills critical damage dealer gap",
        "Engage synergizes with team's burst damage",
        "Optimal for MIDDLE role"
      ]
    },
    {
      "champion": "Syndra",
      "score": 0.71,
      "archetype": "burst_mage",
      "reasoning": [
        "Fills critical damage dealer gap",
        "Engage synergizes with team's burst damage"
      ]
    }
  ],
  "draft_analysis": {
    "our_composition": {
      "picks": 2,
      "archetypes": ["marksman", "engage_tank"],
      "missing_roles": ["damage_dealer", "support"]
    },
    "enemy_composition": {
      "picks": 2,
      "archetypes": ["marksman", "catcher"],
      "threats": []
    }
  }
}
```

**Win Probability Context:**

- `win_projection`: Baseline ensemble forecast for the current (possibly incomplete) draft. Contains blue/red win rates, favored side, consensus confidence, and short reasoning notes.
- Each `recommendation` entry also exposes `projected_team_winrate` (team's win chance if that pick is locked) plus the global `projected_blue_winrate` reference so both sides can display their updated odds without baseline comparisons.

**Scoring Factors:**

1. **Fills Missing Archetypes** (+0.15):
   - Critical damage dealer gap
   - Missing frontline presence
   - No support utility

2. **Attribute Synergies** (+0.08 to +0.12):
   - Engage + burst damage
   - Poke/range + engage
   - Enchanter + marksman

3. **Counter Enemy Threats** (+0.08 to +0.15):
   - Warden counters assassins
   - Hard CC counters mobility
   - Engage counters poke

4. **Role Appropriateness** (+0.05):
   - Champion optimal for selected role

---

### 4. Get Champion Info

```http
GET /champions/{champion_name}
```

Returns detailed information about a specific champion.

**Example:**

```http
GET /champions/Jinx
```

**Response:**

```json
{
  "name": "Jinx",
  "archetype": "marksman",
  "secondary_archetypes": [],
  "riot_roles": ["Marksman"],
  "positions": {
    "BOTTOM": "primary"
  },
  "attributes": [
    "damage_physical",
    "damage_sustained",
    "range_long",
    "scaling_late",
    "scaling_items",
    "damage_aoe",
    "cc_soft",
    "utility_vision"
  ],
  "description": "Ranged sustained damage dealer, scales with items, vulnerable but high DPS"
}
```

---

### 5. List All Archetypes

```http
GET /archetypes
```

Returns taxonomy of all 13 archetypes used for analysis.

**Response:**

```json
{
  "marksman": {
    "name": "marksman",
    "description": "Ranged sustained damage dealer, scales with items, vulnerable but high DPS",
    "key_attributes": ["damage_physical", "damage_sustained", "range_long", "scaling_items"],
    "example_champions": ["Jinx", "Ashe", "Caitlyn"]
  },
  "burst_mage": {
    "name": "burst_mage",
    "description": "High burst magic damage, skill-shot dependent, fragile but threatening",
    "key_attributes": ["damage_magic", "damage_burst", "range_long"],
    "example_champions": ["Lux", "Syndra", "Zoe"]
  }
}
```

**All 13 Archetypes:**

- `marksman`: Ranged sustained DPS
- `burst_mage`: High burst magic damage
- `burst_assassin`: High mobility single-target burst
- `engage_tank`: Initiates teamfights with hard CC
- `warden`: Protective tank, peels for carries
- `diver`: Jumps onto backline
- `juggernaut`: Low mobility high durability fighter
- `skirmisher`: Sustained damage fighter, 1v1 specialist
- `battle_mage`: Short-range sustained magic damage
- `enchanter`: Heals and shields allies
- `catcher`: Long-range CC, pick specialist
- `artillery_mage`: Long-range poke, siege specialist
- `specialist`: Unique mechanics

---

## Example Use Cases

### Use Case 1: Draft Simulator

Build a draft simulator that shows real-time recommendations as each champion is picked/banned.

```python
import requests

base_url = "http://localhost:8000"

# Draft state after 2 picks per side
draft_state = {
    "blue_picks": ["Jinx", "Leona"],
    "blue_bans": ["Yasuo", "Zed"],
    "red_picks": ["Caitlyn", "Thresh"],
    "red_bans": ["Darius", "Vi"],
    "next_pick": "blue"
}

# Get recommendations for mid lane
response = requests.post(f"{base_url}/draft/recommend", json={
    "draft_state": draft_state,
    "role": "MIDDLE",
    "limit": 10
})

recommendations = response.json()["recommendations"]
for rec in recommendations:
    print(f"{rec['champion']} ({rec['score']:.2f}): {rec['reasoning'][0]}")
```

### Use Case 2: Post-Draft Analysis

Analyze a completed draft to explain win probability.

```python
# Analyze complete teams
response = requests.post(f"{base_url}/draft/analyze", json={
    "blue_team": ["Jinx", "Leona", "Orianna", "Vi", "Darius"],
    "blue_roles": ["BOTTOM", "UTILITY", "MIDDLE", "JUNGLE", "TOP"],
    "red_team": ["Caitlyn", "Thresh", "Zed", "Lee Sin", "Renekton"],
    "red_roles": ["BOTTOM", "UTILITY", "MIDDLE", "JUNGLE", "TOP"]
})

analysis = response.json()
print(f"Predicted winner: {analysis['prediction']['winner']}")
print(f"Confidence: {analysis['prediction']['confidence']:.1%}")
print(f"Blue composition: {analysis['blue_analysis']['composition_type']}")
print(f"Red composition: {analysis['red_analysis']['composition_type']}")
```

### Use Case 3: Champion Explorer

Build a champion database with archetypal information.

```python
# Get all champion details
champions = ["Jinx", "Thresh", "Zed", "Vi", "Orianna"]

for champ in champions:
    response = requests.get(f"{base_url}/champions/{champ}")
    info = response.json()
    print(f"{info['name']}: {info['archetype']} ({', '.join(info['attributes'][:3])})")
```

---

## Philosophy & Design Principles

### 1. Theory Over Meta

This API analyzes drafts from a **theoretical archetypal perspective**, not historical win rates.

**Why?**

- Win rates are meta-dependent (patches change constantly)
- Solo queue data is noisy (player skill variance >> draft impact)
- Archetypes are timeless (engage counters poke, regardless of patch)

**What This Means:**

- Recommendations are based on compositional balance, not "what's meta"
- Analysis explains *why* a pick is good (archetypal reasoning)
- No champion tier lists - context matters

### 2. Archetypal Analysis

Champions are classified by their strategic role:

#### Example: Leona vs Janna

- **Leona** (engage_tank): Initiates fights, locks down targets
- **Janna** (enchanter): Disengages fights, protects carries

**Synergies:**

- Leona + Jinx = engage enables marksman positioning (+0.12 score)
- Janna + Jinx = peel keeps marksman alive (+0.12 score)

**Counters:**

- Leona vs Zed = tank absorbs assassin burst (-0.15 for Zed)
- Janna vs Leona = disengage counters engage (+0.08 for Janna)

### 3. Ensemble Intelligence

Uses 3 models instead of 1 for robustness:

- **Logistic Regression**: Linear relationships, interpretable
- **Random Forest**: Non-linear patterns, handles interactions
- **Gradient Boosting**: Sequential learning, corrects errors

**Consensus Matters:**

- All 3 agree → High confidence
- 2/3 agree → Moderate confidence
- 1/2 split → Low confidence (close matchup)

### 4. Explainable Predictions

Every recommendation includes reasoning:

```json
{
  "champion": "Orianna",
  "reasoning": [
    "Fills critical damage dealer gap",
    "Engage synergizes with team's burst damage",
    "Optimal for MIDDLE role"
  ]
}
```

**No Black Boxes**: Users understand *why* the API recommends each pick.

---

## Technical Specifications

### Performance

- **Response Time**: <100ms for recommendations, <200ms for analysis
- **Model Accuracy**: 54.3% (Logistic Regression baseline, professional analyst tier)
- **Training Data**: 936 real Diamond+ matches
- **Features**: 78 extracted per team composition

### Dependencies

```text
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
scikit-learn>=1.3.0
numpy>=1.24.0
```

### Data Files Required

- `data/simulations/trained_models.pkl` (ML models + feature names)
- `data/processed/champion_archetypes.json` (171 champions, 13 archetypes)
- `data/processed/archetype_attributes.json` (45 attributes defined)
- `data/processed/role_aware_relationships.json` (6,865 role synergies)

### Error Handling

**400 Bad Request**: Invalid champion names or malformed request

```json
{
  "detail": "Invalid champion names: InvalidChamp"
}
```

**404 Not Found**: Champion not in database

```json
{
  "detail": "Champion 'InvalidName' not found"
}
```

**503 Service Unavailable**: Models not loaded (run `ml_simulation.py` first)

```json
{
  "detail": "Models not loaded"
}
```

---

## Testing

```bash
# Run test suite
python test_api.py
```

**Tests:**

1. Ensemble prediction (no server required)
2. API endpoints (requires server running)

**Expected Output:**

```text
✓ Ensemble Prediction: PASSED
✓ API Endpoints: PASSED (or SKIPPED if server not running)
```

---

## Roadmap

### Completed ✅

- Ensemble prediction system
- FastAPI server with 5 endpoints
- Archetypal composition analysis
- Draft recommendation with scoring

### Planned

- WebSocket support for live draft updates
- React frontend for visual draft board
- Champion mastery integration (OTP boost)
- Multi-language support

---

## Contact

- Repository: LOL_Draft_Analyzer  
- Branch: main  
- Owner: marimari00

**For technical details**, see [REALITY_CHECK.md](REALITY_CHECK.md) and [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md).
