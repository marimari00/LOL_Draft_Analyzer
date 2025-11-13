import json

# Check if merged spell data improved marksmen attributes
with open('data/processed/spell_based_attributes.json', encoding='utf-8') as f:
    attrs = json.load(f)['attributes']

marksmen = ['Ashe', 'Vayne', 'Caitlyn', 'Jinx', 'Lucian', 'Jhin', 'Twitch']

print("=== MARKSMEN SUSTAINED DPS (After Merge) ===\n")
for champ in marksmen:
    if champ in attrs:
        sustained_dps = attrs[champ].get('sustained_dps', 0)
        burst_index = attrs[champ].get('burst_index', 0)
        print(f"{champ:12s}: sustained_dps={sustained_dps:6.1f}, burst_index={burst_index:.3f}")

print("\n=== THRESHOLDS ===")
print("Marksman threshold: sustained_dps > 119.2 (p75)")
print("Burst assassin threshold: burst_index > 0.66 (p75)")
