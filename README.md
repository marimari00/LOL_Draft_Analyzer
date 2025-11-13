# League of Legends Draft Analyzer

A compositional draft analysis tool that uses archetype-based reasoning rather than pure win-rate statistics to suggest optimal champion picks.

## Philosophy

Traditional draft tools use historical win rates from solo queue games. This analyzer takes a different approach:

- **Archetype-based analysis**: Champions are analyzed by their strategic archetypes (burst, sustain, engage, etc.)
- **Compositional reasoning**: Evaluates team synergies and enemy counter-patterns
- **Theoretical grounding**: Uses champion abilities and stats to infer power curves, not just historical data
- **Role flexibility**: Accounts for champions viable in multiple roles with different attribute profiles

## Quick Start

### Run Production Pipeline

```bash
# Run complete pipeline (3 stages)
python run_pipeline.py

# Output: data/processed/champion_archetypes.json
```

### Validate Results

```bash
# Check against ground truth
python validation/validate_against_source_of_truth.py

# Verify Braum + all marksmen
python validation/final_check.py

# View before/after comparison
python validation/comprehensive_report.py
```

## Project Structure

```text
draft-analyzer/
├── data_pipeline/     # ETL: fetch, scrape, compute, validate
├── data/
│   ├── raw/          # Scraped/fetched raw data
│   ├── processed/    # Cleaned, computed champion data
│   └── database/     # Professional match data
├── config/           # Archetype definitions, settings
├── backend/          # API and core logic (future)
└── notebooks/        # Analysis and exploration
```

## Data Sources

- **Riot Data Dragon**: Base stats, abilities
- **League of Legends Wiki**: Detailed ability information
- **Oracle's Elixir**: Professional match statistics

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Phase 1: Data Collection (Current)

```bash
# Fetch champion data from Riot
python data_pipeline/fetch_data_dragon.py

# Scrape detailed abilities from wiki
python data_pipeline/scrape_wiki.py

# Compute champion attributes
python data_pipeline/compute_attributes.py
```

## Mathematical Framework

Champions are represented as feature vectors with attributes including:

- Damage timing curves (0-15, 15-25, 25-40 min)
- Survivability index (EHP × threat evasion × sustain)
- CC score (Σ duration × reliability × AOE × uptime)
- Mobility, range profiles, waveclear, gold dependency

Archetypes use fuzzy membership - champions can belong to multiple archetypes with different degrees.

## Development Status

**Phase 1**: Foundation and data pipeline ✅ COMPLETE

- [x] Project structure
- [x] Data Dragon fetcher
- [x] Wiki scraper (abandoned - info.lua used instead)
- [x] Attribute computation
- [x] Archetype definitions

**Phase 2**: Archetype Classification ✅ COMPLETE

- [x] info.lua integration (official Riot roles)
- [x] Role mapping (13 archetypes)
- [x] Production pipeline (`run_pipeline.py`)
- [x] **Perfect accuracy: 100% precision, 100% recall**
- [x] Validation suite

**Phase 3**: Core engine (In Progress)

**Phase 3**: Professional match data integration (Planned)

**Phase 4**: Web interface (Planned)
