import json

attrs = json.load(open('data/processed/spell_based_attributes.json', encoding='utf-8'))['attributes']
archs = json.load(open('data/processed/archetype_assignments.json', encoding='utf-8'))
spells = json.load(open('data/processed/complete_spell_database.json', encoding='utf-8'))['spells']

# False positives: non-marksmen classified as marksman
false_positives = ['Sejuani', 'Azir', 'Chogath', 'Malphite', 'Anivia', 'Karthus', 
                   'Ziggs', 'Nunu', 'Lux', 'Braum', 'Kennen', 'Gragas']

print("=" * 80)
print("FALSE POSITIVE ANALYSIS: Why are these classified as marksmen?")
print("=" * 80)

for champ in false_positives[:6]:  # Check first 6
    if champ not in attrs or champ not in spells:
        continue
    
    a = attrs[champ]
    print(f"\n{champ}:")
    print(f"  sustained_dps: {a['sustained_dps']:.1f} (threshold: 119.2)")
    print(f"  max_range: {a['max_range']}")
    print(f"  mobility_score: {a['mobility_score']:.1f}")
    print(f"  Spell damage breakdown:")
    
    for spell_key in ['Q', 'W', 'E', 'R']:
        if spell_key in spells[champ]:
            spell = spells[champ][spell_key]
            base = spell.get('base_damage')
            cd = spell.get('cooldown', 10)
            dps = (base / cd) if base and cd > 0 else 0
            base_str = f"{base:.1f}" if base is not None else "None"
            print(f"    {spell_key} ({spell['name'][:30]:30s}): {base_str:>6s} dmg / {cd:4.1f}s CD = {dps:5.1f} DPS")
            if dps > 30:  # Suspiciously high DPS for a single ability
                desc = spell.get('description', '')[:100]
                print(f"        Description: {desc}...")

print("\n" + "=" * 80)
print("PATTERN DETECTION")
print("=" * 80)
print("Look for keywords indicating utility rather than damage:")
print("- 'frost', 'chill', 'freeze', 'slow' (CC values, not damage)")
print("- 'stealth', 'invisible', 'hidden' (durations, not damage)")
print("- 'speed', 'movement', 'accelerate' (buffs, not damage)")
print("- 'stack', 'charge', 'resource' (mechanics, not damage)")
