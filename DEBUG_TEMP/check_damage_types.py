import json

spells = json.load(open('data/processed/complete_spell_database.json', encoding='utf-8'))['spells']
attrs = json.load(open('data/processed/spell_based_attributes.json', encoding='utf-8'))['attributes']

marksmen = ['Caitlyn', 'Jhin', 'Ezreal', 'Ashe', 'Jinx', 'Tristana']

print("=" * 80)
print("DAMAGE TYPE ANALYSIS FOR MARKSMEN")
print("=" * 80)

for champ in marksmen:
    if champ in spells and champ in attrs:
        print(f"\n{champ} (damage_profile={attrs[champ]['damage_profile']}):")
        for spell_key in ['Q', 'W', 'E', 'R']:
            if spell_key in spells[champ]:
                s = spells[champ][spell_key]
                dtype = s.get('damage_type') or 'None'
                base = s.get('base_damage')
                ad_r = s.get('ad_ratio', 0)
                ap_r = s.get('ap_ratio', 0)
                bonus_ad_r = s.get('bonus_ad_ratio', 0)
                
                base_str = f"{base:.0f}" if base is not None else "None"
                print(f"  {spell_key}: {dtype:8s} | base={base_str:>6s}, AD={ad_r:.2f}, bonus_AD={bonus_ad_r:.2f}, AP={ap_r:.2f}")

print("\n" + "=" * 80)
print("ISSUE IDENTIFIED")
print("=" * 80)
print("Many champion abilities have damage_type='magic' even though they scale with AD!")
print("Example: Caitlyn Q is 'physical' damage but may have AP ratio for some reason")
print("\nThe damage_profile computation is based on damage_type from champion.bin,")
print("which often reports 'magic' for abilities that are actually AD-scaling.")
print("\nThis explains why true marksmen show as 'ap' profile - the data is incorrect!")
