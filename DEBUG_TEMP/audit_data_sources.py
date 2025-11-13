"""Audit what data we actually have and what's being computed."""
import json
import pprint

print("=" * 80)
print("DATA SOURCE AUDIT")
print("=" * 80)

# 1. Check raw damage data
print("\n1. CHAMPION_DAMAGE_DATA.JSON (from champion.bin):")
with open('data/raw/champion_damage_data.json') as f:
    damage_data = json.load(f)
    
print(f"  Total champions: {damage_data['metadata']['champion_count']}")
print(f"  Failed: {damage_data['metadata']['failed_count']}")

# Check Zed's extracted data
zed_damage = damage_data['champions']['Zed']
print("\n  ZED EXTRACTED DATA:")
print(f"    Champion ID: {zed_damage['champion_id']}")
print(f"    Spells available: {list(zed_damage['spells'].keys())}")

# Show Q spell in detail
if 'ZedQ' in zed_damage['spells']:
    q_spell = zed_damage['spells']['ZedQ']
    print("\n    ZedQ (Razor Shuriken):")
    print(f"      Cooldown: {q_spell.get('cooldown', 'N/A')}")
    print(f"      Damage effects: {len(q_spell.get('damage_effects', []))} found")
    if q_spell.get('damage_effects'):
        print(f"      First effect: {q_spell['damage_effects'][0]}")

# 2. Check computed attributes
print("\n2. COMPUTED_ATTRIBUTES.JSON:")
with open('data/processed/computed_attributes.json') as f:
    computed = json.load(f)
    
zed_computed = computed['champions']['Zed']
print(f"  Zed attributes: {list(zed_computed.keys())}")
print(f"    CC Score: {zed_computed['cc_score']}")
print(f"    Mobility: {zed_computed['mobility_score']}")

# 3. Check enhanced attributes  
print("\n3. ENHANCED_ATTRIBUTES.JSON:")
with open('data/processed/enhanced_attributes.json') as f:
    enhanced = json.load(f)
    
zed_enhanced = enhanced['Zed']
print(f"  Zed enhanced attributes: {list(zed_enhanced.keys())}")
print(f"    CC Score: {zed_enhanced['cc_score']}")
print(f"    Burst Pattern: {zed_enhanced.get('burst_pattern', 'N/A')}")
print(f"    Damage Pattern: {zed_enhanced.get('damage_pattern', 'N/A')}")

# 4. Check Data Dragon (descriptions)
print("\n4. DATA_DRAGON_CHAMPIONS.JSON:")
with open('data/raw/data_dragon_champions.json', encoding='utf-8') as f:
    dd_data = json.load(f)
    
zed_dd = dd_data['champions']['Zed']
print(f"  Zed abilities: {list(zed_dd['abilities'].keys())}")
print(f"\n  Zed E (Shadow Slash):")
print(f"    Description: {zed_dd['abilities']['E']['description'][:200]}...")

# 5. Show burst_pattern distribution
print("\n5. BURST_PATTERN DISTRIBUTION:")
burst_counts = {}
for champ, attrs in enhanced.items():
    burst = attrs.get('burst_pattern', 0)
    burst_counts[burst] = burst_counts.get(burst, 0) + 1

print("  Top 10 most common burst_pattern values:")
for burst, count in sorted(burst_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"    {burst:.4f}: {count} champions")

# 6. Check Rengar
print("\n6. RENGAR CC INVESTIGATION:")
rengar_computed = computed['champions']['Rengar']
rengar_enhanced = enhanced['Rengar']
print(f"  Computed CC: {rengar_computed['cc_score']}")
print(f"  Enhanced CC: {rengar_enhanced['cc_score']}")

rengar_dd = dd_data['champions']['Rengar']
print(f"\n  Rengar abilities from Data Dragon:")
for ability_key in ['Q', 'W', 'E', 'R']:
    if ability_key in rengar_dd['abilities']:
        ability = rengar_dd['abilities'][ability_key]
        print(f"    {ability_key} - {ability.get('name', 'Unknown')}:")
        desc = ability.get('description', '').lower()
        if 'stun' in desc or 'root' in desc or 'slow' in desc or 'snare' in desc:
            print(f"      CC FOUND: {desc[:150]}...")
