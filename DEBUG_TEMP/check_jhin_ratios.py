import json

db = json.load(open('data/processed/complete_spell_database.json', encoding='utf-8'))

champ = 'Jhin'
print(f"\n{champ} SPELL RATIOS:")
print("=" * 60)

total_ad = 0
total_ap = 0

for key, spell in db['spells'][champ].items():
    ad = spell.get('ad_ratio', 0)
    bonus_ad = spell.get('bonus_ad_ratio', 0)
    ap = spell.get('ap_ratio', 0)
    
    total_ad += ad + bonus_ad
    total_ap += ap
    
    print(f"{key}: ad={ad:.2f} bonus_ad={bonus_ad:.2f} ap={ap:.2f}")

print(f"\nTOTAL: AD={total_ad:.2f} AP={total_ap:.2f}")
print(f"Profile: {'ad' if total_ad >= total_ap * 1.2 else ('hybrid' if total_ad >= total_ap * 0.8 else 'ap')}")
