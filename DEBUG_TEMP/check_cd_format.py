import json

with open('data/raw/community_dragon_champions.json', encoding='utf-8') as f:
    cd = json.load(f)['champions']

ashe = cd.get('Ashe', {})
print("=== ASHE ABILITIES (Community Dragon) ===\n")

for key in ['Q', 'W', 'E', 'R']:
    if key in ashe.get('abilities', {}):
        ability = ashe['abilities'][key]
        print(f"{key}: {ability.get('name', 'N/A')}")
        print(f"Description: {ability.get('description', 'N/A')[:300]}")
        print()

# Also check what champion.bin has
with open('data/raw/champion_damage_data.json', encoding='utf-8') as f:
    bin_data = json.load(f)['champions']

ashe_bin = bin_data.get('Ashe', {}).get('spells', {})
print("\n=== ASHE SPELLS (champion.bin) ===\n")
for key in ['Q', 'W', 'E', 'R']:
    if key in ashe_bin:
        spell = ashe_bin[key]
        print(f"{key}: base_damage={spell.get('base_damage', [])}, ad_ratio={spell.get('ad_ratio', 0)}, ap_ratio={spell.get('ap_ratio', 0)}")
    else:
        print(f"{key}: NOT FOUND")
