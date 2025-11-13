"""
Add Yunara data manually from wiki screenshots.
"""

import json
from pathlib import Path

# Yunara abilities from screenshots
yunara_data = {
    'champion': 'Yunara',
    'abilities': {
        'P': {
            'name': 'Vow of the First Lands',
            'base_damage': [],
            'ad_ratio': 0.0,
            'bonus_ad_ratio': 0.0,
            'ap_ratio': 1.0,  # 10% (+ 10% per 100 AP) = 0.1 + 0.1 = base is 10% with 1.0 ratio
            'cooldown': []
        },
        'Q': {
            'name': 'Cultivation of Spirit',
            'base_damage': [5.0, 10.0, 15.0, 20.0, 25.0],  # Passive bonus magic damage
            'ad_ratio': 0.0,
            'bonus_ad_ratio': 0.0,
            'ap_ratio': 0.2,  # (+ 20% AP)
            'cooldown': []
        },
        'W': {
            'name': 'Arc of Judgment',
            'base_damage': [55.0, 95.0, 135.0, 175.0, 215.0],  # Initial magic damage
            'ad_ratio': 0.0,
            'bonus_ad_ratio': 0.85,  # (+ 85% bonus AD) - initial hit
            'ap_ratio': 0.5,  # (+ 50% AP) - initial hit
            'cooldown': [10.0]
        },
        'E': {
            'name': "Kanmei's Steps",
            'base_damage': [],  # No damage, just movement
            'ad_ratio': 0.0,
            'bonus_ad_ratio': 0.0,
            'ap_ratio': 0.0,
            'cooldown': [9.0]
        },
        'R': {
            'name': "Arc of Ruin",
            'base_damage': [175.0, 350.0, 525.0],  # Base damage at ranks 1/2/3
            'ad_ratio': 0.0,
            'bonus_ad_ratio': 1.5,  # (+ 150% bonus AD)
            'ap_ratio': 0.75,  # (+ 75% AP)
            'cooldown': [100.0, 90.0, 80.0]
        }
    }
}

# Load existing wiki data
wiki_data_file = Path('data/processed/wiki_champion_data.json')
with open(wiki_data_file, 'r', encoding='utf-8') as f:
    wiki_data = json.load(f)

# Add Yunara
wiki_data['Yunara'] = yunara_data

# Save updated data
with open(wiki_data_file, 'w', encoding='utf-8') as f:
    json.dump(wiki_data, f, indent=2)

print(f"✓ Added Yunara manually")
print(f"Total champions: {len(wiki_data)}/171")
print("\nYunara abilities:")
for key, ability in yunara_data['abilities'].items():
    print(f"  {key}: {ability['name']}")
    print(f"     Base damage: {ability['base_damage']}")
    print(f"     AD: {ability['ad_ratio']}, Bonus AD: {ability['bonus_ad_ratio']}, AP: {ability['ap_ratio']}")
