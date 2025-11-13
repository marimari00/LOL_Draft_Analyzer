import json

# Load with proper encoding
with open('data/raw/data_dragon_champions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check Ahri
print("=== AHRI ===")
for key in ['Q', 'W', 'E', 'R']:
    if key in data['Ahri']['abilities']:
        ability = data['Ahri']['abilities'][key]
        desc = ability.get('description', '')
        print(f"\n{key}: {ability.get('name', 'Unknown')}")
        print(f"Description: {desc[:200]}")

# Check Zed
print("\n\n=== ZED ===")
for key in ['Q', 'W', 'E', 'R']:
    if key in data['Zed']['abilities']:
        ability = data['Zed']['abilities'][key]
        desc = ability.get('description', '')
        print(f"\n{key}: {ability.get('name', 'Unknown')}")
        print(f"Description: {desc[:200]}")

# Check Morgana for comparison (known CC champion)
print("\n\n=== MORGANA (for comparison) ===")
for key in ['Q', 'W', 'E', 'R']:
    if key in data['Morgana']['abilities']:
        ability = data['Morgana']['abilities'][key]
        desc = ability.get('description', '')
        print(f"\n{key}: {ability.get('name', 'Unknown')}")
        print(f"Description: {desc[:200]}")
