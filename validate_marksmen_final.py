import json

with open('data/processed/archetype_assignments.json', encoding='utf-8') as f:
    assignments = json.load(f)['assignments']

expected_marksmen = ['Ashe', 'Vayne', 'Caitlyn', 'Jinx', 'Lucian', 'Jhin', 'Twitch', 
                     'KogMaw', 'Varus', 'Sivir', 'Tristana', 'MissFortune', 'Draven',
                     'Kalista', 'Ezreal', 'Aphelios', 'Corki', 'Xayah']

print("=== MARKSMEN CLASSIFICATION (After Merged Data) ===\n")

correctly_classified = []
misclassified = []

for champ in expected_marksmen:
    if champ in assignments:
        primary = assignments[champ]['primary_archetype']
        primary_score = assignments[champ]['primary_score']
        attrs = assignments[champ]['attributes']
        sustained_dps = attrs.get('sustained_dps', 0)
        
        is_correct = primary == 'marksman'
        status = "✓" if is_correct else "✗"
        
        print(f"{status} {champ:15s}: {primary:20s} (score={primary_score:.2f}, DPS={sustained_dps:.1f})")
        
        if is_correct:
            correctly_classified.append(champ)
        else:
            misclassified.append((champ, primary, sustained_dps))

print(f"\n{'='*70}")
print(f"Correctly classified: {len(correctly_classified)}/{len(expected_marksmen)}")
print(f"Misclassified: {len(misclassified)}")

if misclassified:
    print("\nMisclassifications (need more spell damage):")
    for champ, archetype, dps in sorted(misclassified, key=lambda x: x[2]):
        print(f"  {champ:15s} → {archetype:20s} (DPS={dps:.1f}, threshold=119.2)")
