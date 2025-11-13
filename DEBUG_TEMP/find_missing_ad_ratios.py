import json

spells = json.load(open('data/processed/complete_spell_database.json', encoding='utf-8'))['spells']

# Expected marksmen who should have AD ratios
marksmen = [
    'Aphelios', 'Ashe', 'Caitlyn', 'Draven', 'Ezreal', 'Jhin', 'Jinx',
    'Kaisa', 'Kalista', 'Kindred', 'KogMaw', 'Lucian', 'MissFortune',
    'Quinn', 'Samira', 'Senna', 'Sivir', 'Tristana', 'Twitch',
    'Varus', 'Vayne', 'Xayah', 'Zeri', 'Corki'
]

print("=" * 80)
print("MARKSMEN MISSING AD RATIOS")
print("=" * 80)

for champ in sorted(marksmen):
    if champ not in spells:
        print(f"✗ {champ}: NOT IN DATABASE")
        continue
    
    total_ad = 0.0
    total_bonus_ad = 0.0
    
    for spell_key in ['Q', 'W', 'E', 'R']:
        if spell_key in spells[champ]:
            s = spells[champ][spell_key]
            total_ad += s.get('ad_ratio', 0.0)
            total_bonus_ad += s.get('bonus_ad_ratio', 0.0)
    
    total = total_ad + total_bonus_ad
    
    if total < 0.5:  # Suspiciously low for a marksman
        print(f"✗ {champ:12s}: total AD scaling = {total:.2f} (MISSING DATA!)")
    else:
        print(f"✓ {champ:12s}: total AD scaling = {total:.2f}")

print("\n" + "=" * 80)
print("ACTION NEEDED")
print("=" * 80)
print("Champions with <0.5 total AD scaling need manual patches added.")
print("These are AD-scaling marksmen but extraction missed their ratios.")
