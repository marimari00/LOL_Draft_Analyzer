import json

db = json.load(open('data/processed/complete_spell_database.json', encoding='utf-8'))

champ = 'Jhin'
print(f"\n{champ} WEIGHTED DAMAGE PROFILE:")
print("=" * 80)

weighted_ad = 0
weighted_ap = 0

for key, spell in db['spells'][champ].items():
    base = spell.get('base_damage', 0) or 0
    ad = spell.get('ad_ratio', 0)
    bonus_ad = spell.get('bonus_ad_ratio', 0)
    ap = spell.get('ap_ratio', 0)
    
    weight = max(base, 50)
    
    weighted_ad += (ad + bonus_ad) * weight
    weighted_ap += ap * weight
    
    print(f"{key}: base={base:6.1f} weight={weight:6.1f} | ad={ad:.2f} bonus_ad={bonus_ad:.2f} ap={ap:.2f}")
    print(f"   → weighted_ad={((ad+bonus_ad)*weight):8.1f} weighted_ap={(ap*weight):8.1f}")

print(f"\nTOTAL weighted_ad={weighted_ad:.1f} weighted_ap={weighted_ap:.1f}")
print(f"Ratio: ad/ap = {weighted_ad/weighted_ap if weighted_ap > 0 else 'inf':.2f}")
print(f"Profile: {'ad' if weighted_ad >= weighted_ap * 1.2 else ('hybrid' if weighted_ad >= weighted_ap * 0.8 else 'ap')}")
