import json

attrs = json.load(open('data/processed/spell_based_attributes.json'))

marksmen = ['Caitlyn', 'Jhin', 'Ezreal', 'Jinx', 'Corki', 'Quinn', 'Kindred', 'Senna', 'Twitch']

print("Checking damage_profile for newly patched marksmen:\n")
for c in marksmen:
    if c in attrs:
        profile = attrs[c]['damage_profile']
        print(f"{c:12} damage_profile={profile}")
