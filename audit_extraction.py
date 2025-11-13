"""
Audit champion.bin extraction to understand what we're actually getting.
Check why some spells are missing and validate data quality.
"""
import json
import pprint

print("=" * 80)
print("CHAMPION.BIN EXTRACTION AUDIT")
print("=" * 80)

# 1. Check what we extracted
with open('data/raw/champion_damage_data.json', 'r', encoding='utf-8') as f:
    damage_data = json.load(f)

print(f"\nTotal champions: {damage_data['metadata']['champion_count']}")
print(f"Failed: {damage_data['metadata']['failed_count']}")

# 2. Check a few champions to understand data structure
test_champions = ['Zed', 'Rengar', 'Ahri', 'Leona', 'Jinx']

for champ_name in test_champions:
    if champ_name not in damage_data['champions']:
        print(f"\n{champ_name}: NOT FOUND")
        continue
    
    champ = damage_data['champions'][champ_name]
    print(f"\n{champ_name}:")
    print(f"  Spells extracted: {list(champ['spells'].keys())}")
    
    # Show detailed info for first spell
    if champ['spells']:
        first_spell_key = list(champ['spells'].keys())[0]
        first_spell = champ['spells'][first_spell_key]
        print(f"\n  Example spell ({first_spell_key}):")
        print(f"    Keys available: {list(first_spell.keys())}")
        if 'cooldown' in first_spell:
            print(f"    Cooldown: {first_spell['cooldown']}")
        if 'damage_effects' in first_spell:
            print(f"    Damage effects: {len(first_spell['damage_effects'])} found")
            if first_spell['damage_effects']:
                print(f"    First damage effect:")
                pprint.pprint(first_spell['damage_effects'][0], indent=6, depth=2)

# 3. Check Community Dragon raw data to see what's available
print("\n" + "=" * 80)
print("COMMUNITY DRAGON RAW DATA CHECK")
print("=" * 80)

with open('data/raw/community_dragon_champions.json', 'r', encoding='utf-8') as f:
    cd_data = json.load(f)

print(f"\nTotal champions in Community Dragon: {len(cd_data)}")

# Check Zed in Community Dragon
if 'Zed' in cd_data:
    zed_cd = cd_data['Zed']
    print(f"\nZed in Community Dragon:")
    print(f"  Top-level keys: {list(zed_cd.keys())[:10]}")
    
    # Look for spells
    if 'spells' in zed_cd:
        print(f"  Spells: {len(zed_cd['spells'])} found")
        for i, spell in enumerate(zed_cd['spells'][:5]):
            spell_name = spell.get('name', 'Unknown')
            spell_id = spell.get('id', 'Unknown')
            cooldowns = spell.get('cooldown', [])
            print(f"    Spell {i}: {spell_name} (ID: {spell_id})")
            print(f"      Cooldown: {cooldowns}")

# 4. Check Data Dragon for comparison
print("\n" + "=" * 80)
print("DATA DRAGON COMPARISON")
print("=" * 80)

with open('data/raw/data_dragon_champions.json', 'r', encoding='utf-8') as f:
    dd_data = json.load(f)

zed_dd = dd_data['champions']['Zed']
print(f"\nZed in Data Dragon:")
print(f"  Abilities: {list(zed_dd['abilities'].keys())}")

for ability_key in ['Q', 'W', 'E', 'R']:
    if ability_key in zed_dd['abilities']:
        ability = zed_dd['abilities'][ability_key]
        cooldown = ability.get('cooldown', [])
        print(f"\n  {ability_key} - {ability.get('name', 'Unknown')}:")
        print(f"    Cooldown: {cooldown}")

# 5. Summary of issues
print("\n" + "=" * 80)
print("SUMMARY OF EXTRACTION ISSUES")
print("=" * 80)

issues = []
for champ_name, champ_data in damage_data['champions'].items():
    spell_count = len(champ_data['spells'])
    if spell_count < 4:  # Should have Q, W, E, R at minimum
        issues.append(f"{champ_name}: only {spell_count} spells extracted")

print(f"\nChampions with missing spells: {len(issues)}")
for issue in issues[:20]:  # Show first 20
    print(f"  - {issue}")

if len(issues) > 20:
    print(f"  ... and {len(issues) - 20} more")
