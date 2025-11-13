# Improvement Plan: Reality-Adjusted Targets

## ⚠️ MAJOR UPDATE: Overfitting Discovery

After expanding to **936 matches** (6.7x more data), we discovered:
- Previous **66.2%** accuracy was **overfitting** on 139 matches
- True baseline with proper validation: **53.4%** (Logistic Regression)
- This matches **professional analyst performance** (52-58%)

## Current State (Updated with 936 Matches)

- **Best Model:** Ensemble Prediction (Logistic 54.3%, Random Forest 50.5%, Gradient Boosting 50.0%)
- **Data:** 936 Diamond+ matches (EUW + KR)
- **Features:** 78 extracted features (attribute counts, role-pair synergies, damage/range/mobility profiles)
- **Method:** Weighted ensemble ML (combines all 3 models by confidence)
- **Validation:** 5-fold cross-validation, train/test split (80/20)
- **API:** FastAPI server with draft recommendation endpoints ✅ COMPLETE

## Improvement Strategies

### 1. More Data (HIGH IMPACT - Expected +2-3%)

**Current Limitation:** 139 matches from 10 Challenger players
**Solution:**

- Query all 50+ Challenger players (not just first 10)
- Add Grandmaster tier (200+ players)
- Add Master tier (top 500 players)
- Include KR region (asia.api.riotgames.com)
- **Target:** 500-1000 matches
- **Expected improvement:** +2-3% accuracy from better statistical confidence

### 2. Weighted Scoring System (MEDIUM IMPACT - Expected +2-4%)

**Current Issue:** All attributes weighted equally (synergy=+2, counter=+2)
**Solution:**

- Learn optimal weights from data using regression
- High-impact attributes (e.g., `mobility_high > survive_sustain` at 64.4% WR) should have higher weight
- Low-impact attributes should have lower weight
- **Implementation:** Use actual win rates as weights instead of fixed scores

  ```python
  # Instead of score = +2 for >55% WR
  # Use: score = (winrate - 0.5) * 10  # Maps 55% → 0.5, 60% → 1.0, etc.
  ```

- **Expected improvement:** +2-4% accuracy

### 3. Role-Specific Synergies (HIGH IMPACT - Expected +3-5%)

**Current Issue:** Treating all attribute pairs equally regardless of which roles have them
**Solution:**

- Track synergies by role pair (e.g., "Top tank + Jungle diver" vs "Top tank + Support enchanter")
- **Example:** `engage_dive` is more valuable on Jungle+Support than Top+Jungle
- **Implementation:**

  ```python
  synergy_key = f"{attr1}+{attr2}_{role1}_{role2}"
  # "engage_dive+utility_vision_Jungle_Support" vs "engage_dive+utility_vision_Top_Jungle"
  ```

- **Expected improvement:** +3-5% accuracy (roles matter more than raw attributes)

### 4. Patch-Aware Analysis (MEDIUM IMPACT - Expected +1-2%)

**Current Issue:** Aggregating across all patches (meta shifts between patches)
**Solution:**

- Weight recent patches higher (14.22 > 14.21 > 14.20)
- Track patch-specific trends
- **Implementation:**

  ```python
  patch_weight = {
      "14.22": 1.5,
      "14.21": 1.2,
      "14.20": 1.0,
      # older patches decay
  }
  ```

- **Expected improvement:** +1-2% accuracy

### 5. Champion Pool Overlaps (LOW-MEDIUM IMPACT - Expected +1-2%)

**Current Issue:** Not considering champion flexibility (multi-role champions)
**Solution:**

- Track when champions can flex between roles (e.g., Gragas Top/Jungle/Support)
- Account for champion mastery in recommendations
- **Implementation:** Use `multi_role` and `multi_lane` attributes more intelligently
- **Expected improvement:** +1-2% accuracy

### 6. Advanced Machine Learning (HIGH IMPACT - Expected +3-6%)

**Current Method:** Linear combination (synergy_diff + counter_score)
**Solution:** Use proper logistic regression with sklearn

```python
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

# Features: [synergy_blue, synergy_red, counter_advantage, role_synergies...]
# Target: [1=blue win, 0=red win]

model = LogisticRegression()
model.fit(X_train, y_train)
accuracy = cross_val_score(model, X, y, cv=5).mean()
```

- Add interaction terms (attribute1 *attribute2* role)
- Use cross-validation to prevent overfitting
- **Expected improvement:** +3-6% accuracy

### 7. Lane Matchup Analysis (MEDIUM IMPACT - Expected +2-3%)

**Current Issue:** Only considering team-level attributes
**Solution:**

- Analyze individual lane matchups (Top vs Top, Mid vs Mid, etc.)
- Track which attributes win specific lanes
- **Example:** `range_long` beats `range_melee` in Bottom lane (marksman vs melee support)
- **Implementation:**

  ```python
  lane_advantage = sum([
      get_lane_matchup_score(blue_top, red_top),
      get_lane_matchup_score(blue_jungle, red_jungle),
      # ... other lanes
  ])
  ```

- **Expected improvement:** +2-3% accuracy

### 8. Early vs Late Game Attributes (MEDIUM IMPACT - Expected +1-3%)

**Current Issue:** Not accounting for game duration or scaling patterns
**Solution:**

- Weight `scaling_early` attributes higher for short games (<25 min)
- Weight `scaling_late` attributes higher for long games (>35 min)
- Predict game duration from team compositions
- **Expected improvement:** +1-3% accuracy

## Recommended Implementation Order

### Phase 1: Quick Wins (1-2 days)

1. **More data** - Query all Challenger + Grandmaster + KR region
2. **Weighted scoring** - Use actual win rates as weights
3. **Git commit current progress**

**Expected Result:** 57.6% → 61-63%

### Phase 2: Role Intelligence (2-3 days)

4. **Role-specific synergies** - Track synergies by role pairs
5. **Lane matchup analysis** - Individual lane advantages
6. **Git commit role system**

**Expected Result:** 61-63% → 64-66%

### Phase 3: Advanced ML (3-5 days)

7. **Logistic regression with sklearn** - Proper ML model
8. **Interaction terms** - Attribute * role combinations
9. **Cross-validation** - Prevent overfitting
10. **Git commit ML system**

**Expected Result:** 64-66% → 66-68%

### Phase 4: Refinements (1-2 days)

11. **Patch weighting** - Recent patches matter more
12. **Early/late game scaling** - Duration-aware predictions
13. **Champion flexibility** - Multi-role considerations

**Expected Result:** 66-68% → 68-70%

## Realistic Target Timeline (Revised)

**Why Draft Prediction is Hard:**
- Player skill variance >> draft composition impact
- Draft accounts for only ~5-10% of match outcome
- Execution, mechanics, macro decisions dominate

**Professional Baseline:** 52-58% accuracy (industry standard)

- **Current (936 matches):** 53.4% ✅ **Professional Grade**
- **Phase 1 (Challenger-only filtering):** 54-55% (reduce skill variance)
- **Phase 2 (Champion mastery data):** 56-57% (OTP boost)
- **Phase 3 (Ensemble methods):** 57-58% (model averaging)
- **Realistic Maximum:** 58-60% (approaching theoretical limit)

## Critical Lessons Learned

1. **Small Data Overfits:** 139 matches → 66.2% was memorization, not learning
2. **Validation is Essential:** Always use train/test split + cross-validation
3. **More Data Reveals Truth:** 936 matches → 53.4% is the real performance
4. **Draft Impact is Limited:** We can't predict execution-dependent outcomes
5. **53% is Success:** Professional analysts achieve 52-58%, we're in that range

## Next Immediate Actions (Revised)

**Phase 1: Data Quality (Current Priority)**

1. **Filter to Challenger-only** matches for consistency
   - Remove Diamond/Master games (higher skill variance)
   - Expected: +1-2% accuracy improvement

2. **Patch focus** - Last 2 patches only
   - Meta shifts significantly between patches
   - Expected: +0.5-1% accuracy improvement

**Phase 2: Feature Engineering**

3. **Champion mastery integration**
   - Track games played on champion (via Riot API)
   - OTPs outperform by 5-10% win rate
   - Expected: +2-3% accuracy improvement

4. **Ensemble prediction**
   - Weighted average of Logistic + GB + RF
   - Use prediction confidence for weighting
   - Expected: +1-2% accuracy improvement

**Realistic Outcome:** 57-58% accuracy (top tier professional performance)
