import json

with open('data/raw/champion_damage_data.json', encoding='utf-8') as f:
    bin_data = json.load(f)['champions']

lucian_spells = bin_data.get('Lucian', {}).get('spells', {})

print("=== LUCIAN CHAMPION.BIN SPELLS ===\n")
for key in ['Q', 'W', 'E', 'R']:
    if key in lucian_spells:
        spell = lucian_spells[key]
        base = spell.get('base_damage', [])
        ad_ratio = spell.get('ad_ratio', 0)
        ap_ratio = spell.get('ap_ratio', 0)
        
        has_damage = len(base) > 0 or ad_ratio != 0 or ap_ratio != 0
        
        print(f"{key}: has_damage={has_damage}")
        print(f"   base={base}, ad_ratio={ad_ratio}, ap_ratio={ap_ratio}")
    else:
        print(f"{key}: NOT FOUND")
