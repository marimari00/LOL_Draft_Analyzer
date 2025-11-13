import json

attrs = json.load(open('data/processed/spell_based_attributes.json'))

marksmen_expected = [
    'Aphelios', 'Ashe', 'Caitlyn', 'Corki', 'Draven', 'Ezreal', 'Jhin', 'Jinx',
    'Kaisa', 'Kalista', 'Kindred', 'KogMaw', 'Lucian', 'MissFortune', 'Quinn',
    'Samira', 'Senna', 'Sivir', 'Tristana', 'Twitch', 'Varus', 'Vayne', 'Xayah', 'Zeri'
]

profile_counts = {'ad': 0, 'ap': 0, 'hybrid': 0, 'neutral': 0}

print("ALL EXPECTED MARKSMEN - DAMAGE PROFILES:")
print("=" * 60)

for champ in sorted(marksmen_expected):
    if champ in attrs['attributes']:
        profile = attrs['attributes'][champ]['damage_profile']
        profile_counts[profile] += 1
        print(f"{champ:14} {profile}")

print(f"\nSUMMARY:")
for profile, count in profile_counts.items():
    pct = 100 * count / len(marksmen_expected)
    print(f"  {profile:8} {count:2d} ({pct:4.1f}%)")
