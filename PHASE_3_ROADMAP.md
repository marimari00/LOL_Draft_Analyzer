# Phase 3: Synergy Matrix & Counter Relationships

## Objective

Build a 13x13 matrix defining:
1. **Synergies**: Which archetypes work well together
2. **Counters**: Which archetypes counter others
3. **Importance Weights**: How critical each relationship is

This enables the recommendation engine to:
- Identify team composition gaps
- Suggest counter-picks
- Explain strategic reasoning

---

## Archetype List (13 Total)

From `champion_archetypes.json` (171 champions):

| # | Archetype | Count | % | Examples |
|---|-----------|-------|---|----------|
| 1 | marksman | 26 | 15.2% | Jinx, Ashe, Caitlyn |
| 2 | burst_mage | 17 | 9.9% | Lux, Syndra, Zoe |
| 3 | burst_assassin | 17 | 9.9% | Zed, Talon, Katarina |
| 4 | diver | 16 | 9.4% | Vi, Xin Zhao, Jarvan IV |
| 5 | engage_tank | 15 | 8.8% | Leona, Nautilus, Alistar |
| 6 | juggernaut | 14 | 8.2% | Darius, Garen, Illaoi |
| 7 | specialist | 14 | 8.2% | Azir, Singed, Heimerdinger |
| 8 | skirmisher | 13 | 7.6% | Fiora, Yasuo, Riven |
| 9 | battle_mage | 11 | 6.4% | Swain, Vladimir, Ryze |
| 10 | enchanter | 9 | 5.3% | Lulu, Janna, Soraka |
| 11 | catcher | 7 | 4.1% | Thresh, Blitzcrank, Nautilus |
| 12 | warden | 6 | 3.5% | Braum, Tahm Kench, Taric |
| 13 | artillery_mage | 6 | 3.5% | Xerath, Vel'Koz, Ziggs |

---

## Team Composition Archetypes

### 1. Front-to-Back (Classic Teamfight)

**Core Identity**: Protect the backline carry, fight with frontline peel

**Required Roles:**
- engage_tank OR warden (frontline)
- marksman OR burst_mage (primary DPS)
- enchanter (peel/sustain)

**Optional:**
- diver (secondary engage)
- catcher (picks before fight)

**Strengths:**
- Scales well into late game
- Strong 5v5 teamfighting
- Clear role assignments

**Weaknesses:**
- Weak to poke (can't engage safely)
- Vulnerable to split push
- Needs good positioning

**Example**: Leona + Jinx + Lulu

---

### 2. Dive Composition

**Core Identity**: Engage onto backline, assassinate carries

**Required Roles:**
- diver OR burst_assassin (primary dive)
- engage_tank (engage tool)
- enchanter OR warden (protect diver on exit)

**Optional:**
- skirmisher (clean-up fights)
- battle_mage (sustained damage in chaos)

**Strengths:**
- Forces enemy into disadvantageous fights
- Strong mid-game power spikes
- Punishes immobile carries

**Weaknesses:**
- Requires execution skill
- Falls off if behind
- Weak to disengage/peel

**Example**: Vi + Zed + Lulu (dive backline)

---

### 3. Poke Composition

**Core Identity**: Whittle down enemy before they can engage

**Required Roles:**
- artillery_mage (primary poke)
- catcher OR enchanter (disengage)
- marksman OR burst_mage (follow-up if poke succeeds)

**Optional:**
- warden (zone control)
- burst_assassin (punish enemy retreat)

**Strengths:**
- Controls space, denies objectives
- No-risk damage
- Forces enemy to engage unfavorably

**Weaknesses:**
- Weak if poke lands poorly
- Vulnerable to hard engage
- Scales worse than front-to-back

**Example**: Xerath + Janna + Caitlyn

---

### 4. Split Push Composition

**Core Identity**: Draw enemy away, win side lanes

**Required Roles:**
- skirmisher OR juggernaut (primary split pusher - wins 1v1)
- specialist (waveclear to stall)
- catcher OR engage_tank (create picks during stall)

**Optional:**
- marksman (safe waveclear mid)
- enchanter (sustain for split pusher)

**Strengths:**
- Map pressure forces enemy choices
- Wins via macro, not teamfights
- Punishes uncoordinated teams

**Weaknesses:**
- Requires team coordination
- Weak to hard engage 5v4
- Vulnerable if split pusher caught

**Example**: Fiora (split) + Heimerdinger (waveclear) + Thresh (pick)

---

### 5. Pick Composition

**Core Identity**: Get picks, snowball via numbers advantage

**Required Roles:**
- catcher (primary engage tool - hook/bind)
- burst_assassin OR burst_mage (kill target quickly)
- diver (follow-up engage if 5v4)

**Optional:**
- warden (zone after pick)
- enchanter (sustain between picks)

**Strengths:**
- Forces enemy to play safe
- Snowballs via vision control
- Strong in coordinated play

**Weaknesses:**
- Useless if picks fail
- Weak to 5-man grouping
- Falls off late game

**Example**: Thresh + Zed + Vi

---

## Synergy Matrix (13x13)

**Scale**: 
- **+2**: Strong synergy (enables each other)
- **+1**: Moderate synergy (works well together)
- **0**: Neutral (no special interaction)
- **-1**: Anti-synergy (overlap or conflict)
- **-2**: Strong anti-synergy (actively hurts each other)

### Marksman Synergies

| With | Score | Reasoning |
|------|-------|-----------|
| engage_tank | +2 | Frontline protects marksman, enables positioning |
| warden | +2 | Direct peel for marksman |
| enchanter | +2 | Shields/heals enable marksman to DPS safely |
| catcher | +1 | CC helps marksman kite |
| diver | +1 | Divers draw attention away from marksman |
| artillery_mage | 0 | Both are backline DPS (no special synergy) |
| burst_mage | -1 | Overlap in damage timing (both want to burst) |
| burst_assassin | -1 | Both are squishy, need peel (overlap) |
| skirmisher | 0 | Neutral (skirmisher is side lane) |
| juggernaut | 0 | Neutral (juggernaut is top lane) |
| battle_mage | +1 | Battle mage is frontline DPS (complements backline) |
| specialist | 0 | Depends on specialist (too varied) |

### Engage Tank Synergies

| With | Score | Reasoning |
|------|-------|-----------|
| marksman | +2 | Protects marksman, enables positioning |
| burst_mage | +2 | CC locks targets for burst combo |
| burst_assassin | +1 | Engage creates chaos for assassin |
| diver | +2 | Chain CC, multiple engage threats |
| skirmisher | +1 | Engage creates targets for skirmisher |
| enchanter | +1 | Enchanter keeps engage tank alive |
| warden | -1 | Overlap (both are tanks, one is redundant) |
| catcher | 0 | Both have CC (some overlap) |
| juggernaut | 0 | Neutral (juggernaut is top lane) |
| battle_mage | +1 | Battle mage follows up on engage |
| artillery_mage | +1 | Artillery pokes before engage |
| specialist | 0 | Depends on specialist |

### Burst Assassin Synergies

| With | Score | Reasoning |
|------|-------|-----------|
| engage_tank | +1 | Engage creates chaos for assassin to enter |
| diver | +2 | Multiple dive threats split enemy peel |
| catcher | +2 | Pick enables guaranteed assassination |
| burst_mage | +1 | Burst threat forces enemy to cluster (easier dive) |
| warden | -1 | Assassin doesn't benefit from peel (wants to dive) |
| enchanter | 0 | Assassin doesn't need sustain (in-out playstyle) |
| marksman | -1 | Both are squishy, need peel (overlap) |
| artillery_mage | 0 | Neutral (different fight zones) |
| skirmisher | 0 | Neutral (both are side lane) |
| juggernaut | 0 | Neutral (juggernaut is top lane) |
| battle_mage | 0 | Neutral |
| specialist | 0 | Depends on specialist |

### Enchanter Synergies

| With | Score | Reasoning |
|------|-------|-----------|
| marksman | +2 | Shields/heals enable marksman to DPS safely |
| skirmisher | +2 | Enchanter keeps skirmisher alive in extended fights |
| diver | +1 | Shields enable diver to survive exit |
| engage_tank | +1 | Keeps engage tank alive longer |
| burst_assassin | 0 | Assassin doesn't need sustain (in-out) |
| warden | -1 | Overlap (both are defensive supports) |
| catcher | -1 | Overlap (both are supports) |
| burst_mage | 0 | Neutral (enchanter doesn't enable burst) |
| artillery_mage | +1 | Sustain enables poke war |
| juggernaut | +1 | Sustain enables juggernaut to stay in fight |
| battle_mage | +1 | Sustain enables battle mage to DPS |
| specialist | 0 | Depends on specialist |

*(Continue for all 13 archetypes...)*

---

## Counter Matrix (13x13)

**Scale**:
- **+2**: Hard counter (strongly favored)
- **+1**: Soft counter (slightly favored)
- **0**: Neutral matchup
- **-1**: Soft countered
- **-2**: Hard countered

### Marksman Counters

| Counters | Score | Reasoning |
|----------|-------|-----------|
| warden | -2 | Warden directly denies marksman DPS with shields/peel |
| burst_assassin | -2 | Assassin deletes immobile marksman |
| diver | -1 | Diver can reach marksman backline |
| catcher | -1 | Hook/bind = death for immobile marksman |
| skirmisher | -1 | Skirmisher wins 1v1 vs marksman |
| engage_tank | -1 | Hard engage can reach marksman |
| juggernaut | 0 | Marksman kites juggernaut (neutral) |
| burst_mage | 0 | Skill matchup (whoever bursts first) |
| artillery_mage | 0 | Poke war (neutral) |
| battle_mage | +1 | Marksman outranges battle mage |
| enchanter | +2 | Marksman zones enchanter easily |
| specialist | 0 | Depends on specialist |

### Burst Assassin Counters

| Counters | Score | Reasoning |
|----------|-------|-----------|
| marksman | +2 | Assassin deletes immobile marksman |
| burst_mage | +2 | Assassin deletes immobile burst mage |
| artillery_mage | +2 | Assassin deletes immobile artillery mage |
| enchanter | +1 | Assassin can kill enchanter (but gets peeled) |
| warden | -2 | Warden negates assassin burst with shields/peel |
| engage_tank | -1 | Tank has too much HP for assassin |
| catcher | -1 | CC denies assassin mobility |
| juggernaut | -1 | Juggernaut too tanky for assassin |
| skirmisher | 0 | Skill matchup (both are mobile fighters) |
| diver | 0 | Neutral (both dive backline) |
| battle_mage | 0 | Battle mage has sustain (assassin can't one-shot) |
| specialist | 0 | Depends on specialist |

*(Continue for all 13 archetypes...)*

---

## Implementation Plan

### Step 1: Define Synergy/Counter Matrices

Create `data/processed/archetype_relationships.json`:

```json
{
  "synergies": {
    "marksman": {
      "engage_tank": 2,
      "warden": 2,
      "enchanter": 2,
      "catcher": 1,
      ...
    },
    ...
  },
  "counters": {
    "marksman": {
      "warden": -2,
      "burst_assassin": -2,
      "diver": -1,
      ...
    },
    ...
  },
  "metadata": {
    "scale": {
      "synergy": {"2": "strong", "1": "moderate", "0": "neutral", "-1": "anti-synergy", "-2": "strong anti-synergy"},
      "counter": {"2": "hard counter", "1": "soft counter", "0": "neutral", "-1": "soft countered", "-2": "hard countered"}
    }
  }
}
```

### Step 2: Create Scoring Function

`data_pipeline/score_team_composition.py`:

```python
def score_team_synergy(team_archetypes, synergy_matrix):
    """Calculate total synergy score for a team."""
    score = 0
    for i, arch1 in enumerate(team_archetypes):
        for arch2 in team_archetypes[i+1:]:
            score += synergy_matrix[arch1].get(arch2, 0)
    return score

def score_counter_advantage(our_archetypes, enemy_archetypes, counter_matrix):
    """Calculate counter advantage vs enemy team."""
    score = 0
    for our_arch in our_archetypes:
        for enemy_arch in enemy_archetypes:
            score += counter_matrix[our_arch].get(enemy_arch, 0)
    return score
```

### Step 3: Validate Against Known Compositions

Test cases:
- **Front-to-back**: engage_tank + marksman + enchanter = high synergy
- **Dive**: diver + burst_assassin + warden = high synergy
- **Counter**: burst_assassin vs marksman = +2 (assassin favored)
- **Anti-synergy**: warden + catcher = -1 (overlap)

### Step 4: Build Recommendation Engine (Phase 4)

Use synergy + counter scores to suggest picks:

```python
def recommend_picks(our_team, enemy_team, available_champions):
    """Recommend next pick based on synergy + counters."""
    scores = {}
    for champ in available_champions:
        champ_arch = get_archetype(champ)
        
        # Synergy with our team
        synergy_score = score_team_synergy(our_team + [champ_arch], synergy_matrix)
        
        # Counter advantage vs enemy
        counter_score = score_counter_advantage([champ_arch], enemy_team, counter_matrix)
        
        # Total score (weighted)
        scores[champ] = 0.6 * synergy_score + 0.4 * counter_score
    
    return sorted(scores.items(), key=lambda x: -x[1])[:10]
```

---

## Research Tasks

1. **Review professional meta compositions**
   - What archetypes appear together frequently?
   - What are the win conditions for each comp?

2. **Validate counter relationships**
   - Marksman vs burst_assassin (-2 seems right)
   - Warden vs burst_assassin (+2 seems right)
   - Check edge cases (specialist archetypes)

3. **Weight importance**
   - Is synergy more important than counters? (probably 60/40)
   - Should early game vs late game matter? (phase 4)

4. **Test with known compositions**
   - Protect the Kog'Maw (warden + marksman + enchanter)
   - Assassin dive (burst_assassin + diver + enchanter)
   - Poke comp (artillery_mage + catcher + marksman)

---

## Timeline

- **Week 1**: Define synergy/counter matrices (manual)
- **Week 2**: Implement scoring functions
- **Week 3**: Validate against known comps
- **Week 4**: Build recommendation engine (Phase 4)

---

## Success Metrics

- Synergy matrix should prefer known strong compositions
- Counter matrix should match common sense (assassin > marksman)
- Recommendation engine suggests reasonable picks (validated by players)

---

*Ready to start Phase 3? Let's define the synergy matrix first!*
