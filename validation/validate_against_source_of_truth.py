"""Extract marksman role assignments from info.lua (absolute source of truth)."""

import re
import json

with open('validation/info.lua', encoding='utf-8') as f:
    content = f.read()

# Parse champion blocks - each starts with ["ChampName"] = {
champion_blocks = re.split(r'\n  \[\"([^"]+)\"\] = \{', content)[1:]  # Skip header

marksmen = []
all_roles = {}

# Process pairs of (champion_name, champion_data)
for i in range(0, len(champion_blocks), 2):
    if i+1 >= len(champion_blocks):
        break
    
    champion = champion_blocks[i]
    data_block = champion_blocks[i+1]
    
    # Find role line: ["role"] = {"Role1", "Role2"},
    role_match = re.search(r'\["role"\]\s*=\s*\{([^}]+)\}', data_block)
    
    if role_match:
        roles_str = role_match.group(1)
        # Extract role names from quotes
        roles = re.findall(r'"([^"]+)"', roles_str)
        all_roles[champion] = roles
        
        if 'Marksman' in roles:
            marksmen.append(champion)

print("="*70)
print("MARKSMEN FROM INFO.LUA (ABSOLUTE SOURCE OF TRUTH)")
print("="*70)
print(f"\nTotal champions with 'Marksman' role: {len(marksmen)}\n")

for champ in sorted(marksmen):
    roles = all_roles.get(champ, [])
    print(f"  {champ:20s} - Roles: {', '.join(roles)}")

print("\n" + "="*70)
print("VALIDATION AGAINST CURRENT CLASSIFICATION")
print("="*70)

# Load our current assignments
import json
with open('data/processed/champion_archetypes.json') as f:
    our_data = json.load(f)

our_marksmen = [name for name, info in our_data['assignments'].items() 
                if info['primary_archetype'] == 'marksman']

true_positives = set(marksmen) & set(our_marksmen)
false_positives = set(our_marksmen) - set(marksmen)
false_negatives = set(marksmen) - set(our_marksmen)

print(f"\nTrue Positives ({len(true_positives)}):")
for champ in sorted(true_positives):
    print(f"  ✓ {champ}")

print(f"\nFalse Positives ({len(false_positives)}) - We classified as marksman, but info.lua says no:")
for champ in sorted(false_positives):
    actual_roles = all_roles.get(champ, ['Unknown'])
    print(f"  ✗ {champ:20s} (actual: {', '.join(actual_roles)})")

print(f"\nFalse Negatives ({len(false_negatives)}) - info.lua says marksman, we missed:")
for champ in sorted(false_negatives):
    if champ in our_data['assignments']:
        our_arch = our_data['assignments'][champ]['primary_archetype']
        our_dps = our_data['assignments'][champ]['attributes']['sustained_dps']
        our_ad = our_data['assignments'][champ]['attributes']['total_ad_ratio']
        print(f"  ! {champ:20s} - We classified as: {our_arch:15s} (DPS={our_dps:.1f}, AD={our_ad:.2f})")
    else:
        print(f"  ! {champ:20s} - Not in our data")

precision = len(true_positives) / len(our_marksmen) if our_marksmen else 0
recall = len(true_positives) / len(marksmen) if marksmen else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

print(f"\n{'='*70}")
print(f"METRICS")
print(f"{'='*70}")
print(f"Precision: {precision*100:.1f}% ({len(true_positives)}/{len(our_marksmen)})")
print(f"Recall:    {recall*100:.1f}% ({len(true_positives)}/{len(marksmen)})")
print(f"F1 Score:  {f1*100:.1f}%")

if precision >= 0.90:
    print(f"\n✓ Precision {precision*100:.1f}% is excellent!")
elif precision >= 0.80:
    print(f"\n✓ Precision {precision*100:.1f}% is good")
else:
    print(f"\n⚠️  Precision {precision*100:.1f}% needs improvement")
