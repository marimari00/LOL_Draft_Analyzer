import json

with open('data/raw/data_dragon_champions.json', encoding='utf-8') as f:
    dd = json.load(f)['champions']

# Check Ashe's W (Volley) in detail
ashe = dd.get('Ashe', {})
abilities = ashe.get('abilities', {})

print("=== ASHE W (VOLLEY) - DATA DRAGON ===\n")
if 'W' in abilities:
    w = abilities['W']
    print(f"Name: {w.get('name')}")
    print(f"Description: {w.get('description')}")
    print(f"Cooldown: {w.get('cooldown', [])}")
    print(f"Cost: {w.get('cost', [])}")
    print(f"Range: {w.get('range', [])}")
    
    # Check all fields
    print("\nAll fields:")
    for key, value in w.items():
        if key not in ['name', 'description']:
            print(f"  {key}: {value}")
else:
    print("W not found")

# Check a few other marksmen
print("\n" + "="*70)
print("CHECKING OTHER MARKSMEN")
print("="*70)

for champ_name in ['Jinx', 'Caitlyn', 'Vayne', 'Lucian']:
    champ = dd.get(champ_name, {})
    abilities = champ.get('abilities', {})
    
    print(f"\n{champ_name}:")
    for key in ['Q', 'W', 'E', 'R']:
        if key in abilities:
            ability = abilities[key]
            desc = ability.get('description', '')
            # Check if description mentions damage
            has_damage_mention = any(word in desc.lower() for word in ['damage', 'deals', 'physical', 'magic'])
            print(f"  {key}: {ability.get('name', 'N/A')} - Mentions damage: {has_damage_mention}")
