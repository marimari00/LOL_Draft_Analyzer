import json

with open('data/raw/data_dragon_champions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

zed = data['champions']['Zed']['abilities']

for k in ['Q', 'W', 'E', 'R']:
    print(f"\n{k} ({zed[k]['name']}):")
    print(f"  {zed[k]['description']}")
