import json

with open('data/processed/effect_burn_damage_patches.json', encoding='utf-8') as f:
    patches = json.load(f)['patches']

marksmen = ['Ashe', 'Vayne', 'Caitlyn', 'Jinx', 'Lucian', 'Kalista', 'Ezreal', 
            'Jhin', 'Twitch', 'KogMaw', 'Varus', 'Sivir', 'Tristana', 'MissFortune', 'Draven']

print("=== MARKSMEN WITH EFFECT_BURN PATCHES ===\n")

found_marksmen = []
for champ in marksmen:
    if champ in patches:
        found_marksmen.append(champ)
        print(f"{champ}:")
        for spell_key, spell_data in patches[champ].items():
            base = spell_data.get('base_damage', [])
            ad_ratio = spell_data.get('ad_ratio', 0)
            name = spell_data.get('name', spell_key)
            
            if base:
                print(f"  {spell_key} ({name}): {base[0]:.0f} -> {base[-1]:.0f} damage", end='')
                if ad_ratio:
                    print(f" + {ad_ratio:.2f} AD ratio", end='')
                print()

print(f"\nTotal: {len(found_marksmen)}/{len(marksmen)} marksmen have patches")
print(f"Missing: {[m for m in marksmen if m not in patches]}")
