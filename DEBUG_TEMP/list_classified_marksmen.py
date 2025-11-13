import json

assignments = json.load(open('data/processed/archetype_assignments.json'))

marksmen = []
for champ, data in assignments.items():
    if champ == 'metadata' or champ == 'distribution':
        continue
    if data.get('primary_archetype') == 'marksman':
        marksmen.append(champ)

print(f"CHAMPIONS CLASSIFIED AS MARKSMAN ({len(marksmen)}):")
print("=" * 80)
for c in sorted(marksmen):
    print(f"  {c}")
