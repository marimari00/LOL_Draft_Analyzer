import json

attrs = json.load(open('data/processed/spell_based_attributes.json'))

marksmen = ['Jhin', 'Jinx', 'Lucian', 'MissFortune', 'Twitch', 'Varus', 'Vayne', 'Xayah']

print("MARKSMEN DAMAGE PROFILES (with base-damage weighting):")
print("=" * 60)

for champ in marksmen:
    if champ in attrs['attributes']:
        profile = attrs['attributes'][champ]['damage_profile']
        print(f"{champ:14} {profile}")
