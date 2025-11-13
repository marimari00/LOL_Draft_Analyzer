import json

with open('data/raw/data_dragon_champions.json', encoding='utf-8') as f:
    dd = json.load(f)['champions']

# Check Ashe W
ashe_w = dd['Ashe']['abilities']['W']
print("=== ASHE W (Volley) ===")
print(f"effect_burn: {ashe_w['effect_burn']}")
print(f"Description: {ashe_w['description']}")

# Check a few more marksmen
print("\n" + "="*70)
for champ_name in ['Vayne', 'Caitlyn', 'Lucian', 'Jinx']:
    champ = dd.get(champ_name, {})
    abilities = champ.get('abilities', {})
    
    print(f"\n{champ_name}:")
    for key in ['Q', 'W', 'R']:
        if key in abilities:
            ability = abilities[key]
            effect_burn = ability.get('effect_burn', [])
            
            # Find non-zero values
            non_zero = [f"{idx}:{val}" for idx, val in enumerate(effect_burn) if val and val != '0' and val != 'None']
            
            desc = ability.get('description', '')[:80]
            has_damage = 'damage' in desc.lower()
            
            print(f"  {key} ({ability['name']}): damage_mention={has_damage}, effect_burn slots: {non_zero}")
