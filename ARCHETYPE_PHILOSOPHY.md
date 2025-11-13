# Archetype Classification Philosophy

## Core Principle: Data-Driven Truth

**The attributes determine the archetype, NOT the other way around.**

If a champion's computed attributes (sustained_dps, burst_index, mobility_score, cc_score, max_range) place them in an unexpected archetype, that classification is CORRECT. We don't force champions into mainstream labels.

Example: If Ezreal has high burst_index (0.746) + high mobility (1.5) + high sustained_dps (290.4), and this scores highest for burst_assassin, then Ezreal IS a burst_assassin in terms of gameplay pattern, regardless of what players call him.

---

## The False Positive Problem

**Current Issue:** 33 non-marksmen (mages, tanks, enchanters) are classified as marksmen because they have sustained_dps >= 119.2.

**Root Cause:** The marksman archetype definition is TOO PERMISSIVE. High sustained_dps alone does NOT make a champion a marksman.

---

## What Actually Defines Each Archetype?

### 1. **MARKSMAN** - Ranged DPS Carries
**Defining characteristics:**
- **Primary:** Sustained DPS from basic attacks (auto-attack focused)
- **Secondary:** Long range, low mobility, low CC
- **Key insight:** Marksmen deal damage through CONTINUOUS auto-attacks, not spell rotations

**Current problem:** Mages with low-CD spells (Lux Q/E, Ziggs Q/E, Karthus Q) have high sustained_dps from SPELL rotations, but they're NOT auto-attack focused.

**Solution:** Marksman definition needs ADDITIONAL constraint:
- Require LOW burst_ratio (<0.5) - their damage should be SUSTAINED, not bursty
- OR require LOW spell_count/high auto-focus indicator
- OR require damage_profile = 'physical' or 'neutral' (NOT 'ap' pure mages)

---

### 2. **BURST MAGE** - High Damage Magic Nukers
**Defining characteristics:**
- **Primary:** High burst damage from AP ratios
- **Secondary:** Medium range, CC for setup, AP scaling
- **Key insight:** One rotation kills, then cooldowns

**Current problem:** Getting overshadowed by marksman in tied scores

**Solution:** Burst mages should have:
- High burst_index (>0.6)
- AP damage profile
- Medium-high sustained_dps from spell spam

---

### 3. **BATTLE MAGE** - Sustained Magic DPS
**Defining characteristics:**
- **Primary:** High sustained magic DPS (spell rotations)
- **Secondary:** Durability, close-medium range, some CC
- **Key insight:** Like mage version of bruisers - consistent DPS + tankiness

**Current problem:** Some (like Vayne at 122.7 DPS) classified here incorrectly

**Solution:** Battle mages should require:
- AP damage profile OR hybrid
- NOT pure physical damage
- Medium mobility (need to get in range)

---

### 4. **BURST ASSASSIN** - High Mobility Burst Killers
**Defining characteristics:**
- **Primary:** High burst damage + high mobility
- **Secondary:** Low CC, single-target focus, in-out playstyle
- **Key insight:** Get in, delete target, get out

**Current status:** Ezreal correctly classified (high burst + mobility)

---

### 5. **SKIRMISHER** - Mobile Sustained Fighters
**Defining characteristics:**
- **Primary:** High mobility + sustained DPS
- **Secondary:** Single-target focus, medium survivability
- **Key insight:** Stick to targets and duel

**Current problem:** Kalista (161.5 DPS, 1.5 mobility) classified here - this might be CORRECT per data

---

## Proposed Solutions for False Positives

### Option 1: Stricter Marksman Definition (RECOMMENDED)
Add constraint: `burst_ratio < 0.5` (sustained damage, not bursty)
- Filters out burst mages (Lux, Ziggs, Karthus) who have high burst_ratio
- Keeps true marksmen (Jinx, Ashe, Caitlyn) who have low burst_ratio
- Philosophy: "Marksmen are defined by CONSISTENT damage, not burst windows"

### Option 2: Damage Profile Filter
Add constraint: `damage_profile != 'ap'` (marksmen are physical/hybrid)
- Filters out pure AP champions (mages)
- Risk: Misses hybrid marksmen (Kaisa, Kog'Maw)

### Option 3: Multi-Factor Scoring Weight Adjustment
Increase weight of `mobility_score <= 1.2` requirement
- Emphasizes that marksmen are IMMOBILE
- Filters out mobile mages
- Risk: Misses mobile marksmen (Lucian, Ezreal, Kalista)

### Option 4: Accept Hybrids + Add Secondary Archetypes
Don't filter false positives - instead track ALL archetypes with score > 0.7
- Champion can be [marksman, burst_mage] if both score high
- Philosophy: "Hybrids exist - capture them, don't force choices"
- Example: Varus is BOTH marksman (sustained_dps) AND burst_mage (R nuke)

---

## Recommended Approach

**Phase 1:** Implement Option 1 (burst_ratio < 0.5 for marksmen)
- Quick filter that aligns with marksman identity
- Should remove ~20-25 false positives (burst mages)

**Phase 2:** Add Option 4 (secondary archetypes)
- Capture hybrids that legitimately fit multiple roles
- Provides richer classification data

**Phase 3:** Manual review of remaining edge cases
- Champions like Senna, Graves (marksman-ish but unique)
- Accept some misclassifications as "legitimate hybrids"

---

## Success Metrics

**Precision target:** 70%+ (down from 29.8%)
- Acceptable if some mages remain (e.g., Azir is basically a ranged DPS mage)

**Recall target:** 80%+ (up from 60.9%)
- Accept that some marksmen ARE hybrids (Ezreal = burst_assassin is CORRECT)

**Philosophy alignment:** 100%
- Every classification must be defensible from attributes
- No forcing champions into boxes they don't fit

---

## Edge Cases to Accept

1. **Ezreal as burst_assassin** - Correct (burst_index 0.746, mobility 1.5)
2. **Kalista as skirmisher** - Correct (high mobility 1.5, dueling focus)
3. **Senna as marksman** - Borderline (support/marksman hybrid)
4. **Graves as marksman** - Borderline (bruiser/marksman hybrid)
5. **Azir as marksman** - Borderline (mage/marksman DPS hybrid)

These are DATA-DRIVEN truths, not errors.

---

## Implementation Plan

1. Read current archetype definitions
2. Add `burst_ratio < 0.5` constraint to marksman requirements
3. Rebuild archetype assignments
4. Validate: Check precision/recall
5. If precision < 70%, add damage_profile filter
6. If recall < 80%, review missed marksmen individually

Let the data guide us.
