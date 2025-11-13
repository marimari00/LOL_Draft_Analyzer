import json

with open('data/raw/data_dragon_champions.json', encoding='utf-8') as f:
    dd = json.load(f)['champions']

lucian = dd.get('Lucian', {})
lucian_q = lucian.get('abilities', {}).get('Q', {})

print("=== LUCIAN Q ===")
print(f"Name: {lucian_q.get('name')}")
print(f"Description: {lucian_q.get('description')}")
print(f"effect_burn: {lucian_q.get('effect_burn', [])}")

# Check if description mentions damage
desc = lucian_q.get('description', '').lower()
damage_keywords = ['damage', 'physical', 'magic', 'deals', 'inflicts']
mentions = [kw for kw in damage_keywords if kw in desc]
print(f"Damage keywords found: {mentions}")
