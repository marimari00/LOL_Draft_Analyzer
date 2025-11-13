# Deep Audit Results: Attribute Computation Problems

## Executive Summary

After deep analysis of the data pipeline, I've identified **FUNDAMENTAL FLAWS** in how attributes are computed that make archetype classification unreliable.

## Critical Problems

### 1. BURST_PATTERN: Completely Useless for Differentiation

**Problem**: 122/171 champions (71%) have IDENTICAL burst_pattern = 0.7692

**Root Cause**: Binary indicator system in `compute_enhanced_attributes.py:153-169`

```python
burst_indicators = 0
if mid_damage > 1500:  # High rotation damage
    burst_indicators += 1
if avg_cooldown > 8:  # Long cooldowns
    burst_indicators += 1
if damage_concentration > 0.4:  # Damage concentrated in one spell
    burst_indicators += 1

burst_score = burst_indicators / 3.0  # Results: 0, 0.33, 0.67, or 1.0
```

**Result Distribution**:

- 0.7692 (10/13): 122 champions (71%)
- 1.0000: 20 champions (12%)
- 0.6250: 19 champions (11%)
- Other: 10 champions (6%)

**Why This Fails**:

- Only 4 possible burst scores (0, 1/3, 2/3, 1)
- After normalization with sustained_score, creates extreme clustering
- Cannot differentiate Zed (true assassin) from Orianna (mage)
- Makes burst threshold meaningless

**What Should Happen**: Use actual damage numbers in continuous scale

- Burst potential = (max_rotation_damage / time_to_execute)
- Use real damage formulas from champion.bin data
- Compare to DPS over 10 seconds for sustained pattern

---

### 2. CC_SCORE: Multiple Calculation Bugs

#### Bug 2a: Rengar CC = 4.0 (Should be ~0.4)

**Problem**: Rengar E has CC score 10x too high

**Root Cause**: Data Dragon has **WRONG COOLDOWN**

```text
Rengar E (Bola Strike):
- Data Dragon cooldown: [0.25, 0.25, 0.25, 0.25, 0.25]
- ACTUAL cooldown: ~10 seconds
```

**CC Formula**:

```python
cc_contribution = cc_weight × duration × reliability × target_count × uptime
uptime = 1 / (cooldown + 0.25)

# With wrong data:
rengar_e_root = 1.0 × 2.0 × 0.6 × 1.0 × (1/0.5) = 2.4
rengar_e_slow = 0.2 × 2.0 × 0.6 × 1.0 × (1/0.5) = 0.48
Total = 2.88 (then enhanced to 4.0 somewhere)

# With correct data:
rengar_e_root = 1.0 × 2.0 × 0.6 × 1.0 × (1/10.25) = 0.117
rengar_e_slow = 0.2 × 2.0 × 0.6 × 1.0 × (1/10.25) = 0.023
Total = 0.14 ✓
```

**Solution**: Need to source cooldowns from champion.bin or wiki, NOT Data Dragon

#### Bug 2b: E ability Only Extracted from champion.bin

**Problem**: Zed has spells Q, E, R extracted but missing W

From `audit_data_sources.py`:

```text
ZED EXTRACTED DATA:
  Champion ID: Zed
  Spells available: ['Q', 'E', 'R']
```

**Impact**: Missing abilities means incomplete damage calculations

---

### 3. DATA SOURCE INCONSISTENCIES

#### Available Data

1. **champion_damage_data.json** (from champion.bin):
   - 171/171 champions (100%)
   - Real damage formulas, ratios, scalings
   - BUT: Missing some abilities (e.g., Zed W)

2. **data_dragon_champions.json** (from Riot CDN):
   - All abilities with descriptions
   - BUT: Incorrect cooldowns (Rengar E = 0.25s)
   - BUT: Text descriptions unreliable for parsing

3. **community_dragon_champions.json**:
   - Not currently used
   - May have better data quality

#### Current Pipeline Failures

- `compute_attributes.py`: Uses Data Dragon descriptions (unreliable)
- `compute_enhanced_attributes.py`: Uses champion.bin damage (good) but binary indicators (bad)
- No validation between sources
- No fallback when data is wrong

---

### 4. ARCHETYPE CLASSIFICATION FAILURES

From `quick_analysis.py` results:

**Burst Assassins (Expected: 15-20, Actual: 5)**:

- Only: Katarina, Graves, Fizz, Nasus, Shyvana
- Missing: Zed (0.246 CC), Akali (0.229 CC), Khazix (0.308 CC), Talon, Qiyana, LeBlanc
- Reason: CC threshold 0.15 too strict + AOE multiplier inflates scores

**Marksmen → Poke Champions**:

- Jinx, Ashe, Jhin, Draven, MF all classified as poke_champion
- Vayne, Lucian → enchanter (wrong!)
- Reason: Marksman archetype poorly defined

**Engage Tanks Include Assassins**:

- Zed, Khazix, Yasuo, Yone are engage_tanks
- Reason: High mobility + some CC = tank by current rules

---

## Recommended Solutions

### Phase 1: Fix Data Extraction (CRITICAL)

1. **Extract ALL abilities from champion.bin** (not just Q/E/R)
2. **Source cooldowns from champion.bin**, not Data Dragon
3. **Validate data quality**: Flag abilities with CD < 1s or > 200s
4. **Use Community Dragon** as fallback for missing data

### Phase 2: Rebuild Attribute Computation

1. **Burst Pattern** → Use continuous damage metrics:

   ```python
   burst_potential = max_rotation_damage / rotation_time
   sustained_dps = damage_over_10s / 10
   burst_ratio = burst_potential / sustained_dps  # Continuous scale
   ```

2. **CC Score** → Fix formula:

   ```python
   # Only count STRONGEST CC per ability (not both slow AND root)
   # Use real cooldowns from champion.bin
   # Cap uptime contribution (don't multiply by match_count)
   ```

3. **Mobility** → Use real dash distances from champion.bin

4. **Range** → Use actual attack range + spell ranges from champion.bin

### Phase 3: Redesign Archetypes

1. **Use REAL THRESHOLDS based on actual data distribution**
2. **Define archetypes by PRIMARY characteristics**:
   - Burst Assassin: burst_ratio > 2.0, mobility > 0.5, survivability < 0.6
   - Marksman: range > 500, sustained_dps high, auto_attack_focused
   - Engage Tank: cc_score > 0.3, survivability > 0.7, engage_range > 600

3. **Remove arbitrary 0-1 normalization** where it destroys information
4. **Validate against ground truth** (100 hand-labeled champions)

---

## Why This Matters

The current system has:

- ❌ 71% of champions with identical burst scores
- ❌ Only 5 burst assassins (should be 15-20)
- ❌ ADCs classified as enchanters/poke
- ❌ Assassins classified as tanks
- ❌ CC scores 10x wrong (Rengar)
- ❌ Missing ability data (Zed W)

**Bottom line**: We're trying to classify champions using garbage data and broken formulas. No amount of threshold tweaking will fix this.

We need to:

1. Fix data extraction (get ALL abilities, correct cooldowns)
2. Rebuild attribute computation (continuous metrics, not binary)
3. Redesign archetypes based on real data distributions
4. Validate against known ground truth

This is a fundamental rebuild, not a tweak.
