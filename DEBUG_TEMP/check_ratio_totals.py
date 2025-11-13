import json

spells = json.load(open('data/processed/complete_spell_database.json', encoding='utf-8'))['spells']
attrs = json.load(open('data/processed/spell_based_attributes.json', encoding='utf-8'))['attributes']

marksmen = ['Caitlyn', 'Jhin', 'Ezreal', 'Ashe', 'Jinx', 'Tristana', 'Draven', 'Lucian']

print("=" * 80)
print("RATIO TOTALS FOR MARKSMEN")
print("=" * 80)

for champ in marksmen:
    if champ in spells and champ in attrs:
        total_ap = 0.0
        total_ad = 0.0
        
        for spell_key in ['Q', 'W', 'E', 'R']:
            if spell_key in spells[champ]:
                s = spells[champ][spell_key]
                total_ap += s.get('ap_ratio', 0.0)
                total_ad += s.get('ad_ratio', 0.0) + s.get('bonus_ad_ratio', 0.0)
        
        profile = attrs[champ]['damage_profile']
        
        # Determine what profile SHOULD be
        if total_ap == 0 and total_ad == 0:
            expected = "neutral"
        elif total_ap >= total_ad * 1.2:
            expected = "ap"
        elif total_ad >= total_ap * 1.2:
            expected = "ad"
        else:
            expected = "hybrid"
        
        match = "✓" if profile == expected else "✗"
        print(f"{match} {champ:12s}: AP={total_ap:.2f}, AD={total_ad:.2f} | profile={profile:8s} (expected={expected})")

print("\n" + "=" * 80)
print("INSIGHT")
print("=" * 80)
print("Caitlyn: AP=0.80 vs AD=0.00 → Classified as 'ap' because NO AD ratios extracted!")
print("Jhin: AP=3.30 vs AD=0.00 → Same issue!")
print("\nProblem: champion.bin extraction missed AD ratios for these champions.")
print("They likely have bonus_ad ratios that weren't captured in effect_burn.")
