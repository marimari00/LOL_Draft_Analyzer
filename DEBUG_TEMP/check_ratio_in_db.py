import json

db = json.load(open('data/processed/complete_spell_database.json', encoding='utf-8'))

marksmen = ['Jhin', 'Jinx', 'Lucian', 'Twitch', 'Varus', 'Vayne']

for champ in marksmen:
    if champ in db:
        total_ad = 0
        total_ap = 0
        
        for spell_key, spell in db[champ].items():
            ad = spell.get('ad_ratio', 0) + spell.get('bonus_ad_ratio', 0)
            ap = spell.get('ap_ratio', 0)
            total_ad += ad
            total_ap += ap
        
        profile = 'ad' if total_ad > total_ap else ('hybrid' if total_ad > 0 and total_ap > 0 else ('ap' if total_ap > 0 else 'neutral'))
        print(f"{champ:12} AD={total_ad:.2f} AP={total_ap:.2f} → profile={profile}")
