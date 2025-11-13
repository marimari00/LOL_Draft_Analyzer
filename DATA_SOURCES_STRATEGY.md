# Data Sources Strategy for Champion Information

## Problem

The Fandom wiki only has data up to champions released before Mel (Oct 2024). This means 5-6 newer champions lack detailed ability information needed for accurate archetype classification.

## Solution: Hybrid Multi-Source Approach

### Data Source Priority (Best to Fallback)

1. **Wiki (Fandom)** - Most detailed, but outdated
   - Coverage: ~166 champions (pre-Mel)
   - Strengths: Very detailed ability descriptions, CC info, ratios
   - Weaknesses: No Mel, Ambessa, Aurora, Yunara, Smolder
   - File: `data/raw/wiki_scraped_abilities.json`

2. **Community Dragon** - Current and comprehensive
   - Coverage: 191 champions (ALL current + some test champions)
   - Strengths: Always up-to-date, detailed ability mechanics
   - Weaknesses: Less narrative description than wiki
   - URL: `https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/`
   - File: `data/raw/community_dragon_champions.json`

3. **Data Dragon (Riot Official)** - Baseline fallback
   - Coverage: 171 champions (current patch)
   - Strengths: Official, reliable, basic stats
   - Weaknesses: Limited ability detail, no CC durations
   - File: `data/raw/data_dragon_champions.json`

## Implementation

### Hybrid Computation (`compute_attributes_enhanced.py`)

```python
# For each champion:
if champion in wiki_data:
    use wiki_data  # Best detail for older champions
elif champion in community_dragon_data:
    use community_dragon_data  # Newer champions
else:
    use data_dragon_only  # Absolute fallback
```

### Coverage Breakdown

| Champions | Data Source | Examples |
|-----------|-------------|----------|
| ~166      | Wiki        | Ahri, Zed, Jinx, Yasuo, etc. |
| ~5        | Community Dragon | Mel, Ambessa, Aurora, Yunara, Smolder |
| 0 (ideally) | Data Dragon only | (fallback only) |

## Workflow

### Step 1: Scrape Wiki (Already Running)

```bash
python data_pipeline/scrape_wiki.py
# Expected: 166 successful, 5 failed (newer champions)
```

### Step 2: Fetch Community Dragon Data

```bash
python data_pipeline/fetch_community_dragon.py
# Fetches Mel, Ambessa, Aurora, Yunara, Smolder + others
```

### Step 3: Compute Enhanced Attributes

```bash
python data_pipeline/compute_attributes_enhanced.py
# Uses hybrid approach: Wiki (166) + Community Dragon (5) + Data Dragon baseline
```

### Step 4: Reassign Archetypes

```bash
python data_pipeline/assign_archetypes_enhanced.py
# Uses enhanced attributes with better damage patterns
```

## Expected Improvements

### Damage Pattern Accuracy

- **Ahri**: sustained → burst (wiki data shows burst combo)
- **Xerath**: better poke detection (long range + low CD)
- **Mel**: Proper classification (Community Dragon data)
- **Ambessa**: Proper classification (Community Dragon data)

### Complete Coverage

- All 171 champions will have enhanced data
- No gaps for newer champions
- Consistent quality across all champions

## Alternative Future Sources

If Community Dragon becomes unavailable:

1. **Manual Curation JSON**
   - Create `data/manual/newer_champions.json`
   - Hand-code Mel, Ambessa, etc.
   - Priority: Community Dragon > Manual > Data Dragon

2. **Direct API Scraping**
   - Scrape League Client API (requires running client)
   - More complex, but most current

3. **Community Databases**
   - LoLWiki alternative sites
   - Community-maintained databases
   - leagueoflegends.fandom.com/api.php (if accessible)

## Files Created

- `data_pipeline/fetch_community_dragon.py` - Fetches Community Dragon data
- `data_pipeline/compute_attributes_enhanced.py` - Hybrid computation
- `check_wiki_coverage.py` - Identifies coverage gaps
- `test_cdragon.py` - Tests Community Dragon API

## Next Steps

1. ✅ Wait for wiki scraper to complete
2. ⏭️ Run Community Dragon fetcher
3. ⏭️ Compute enhanced attributes
4. ⏭️ Reassign archetypes with better data
5. ⏭️ Proceed to role viability system
