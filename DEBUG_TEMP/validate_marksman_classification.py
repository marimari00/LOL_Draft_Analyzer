import json

attrs = json.load(open('data/processed/spell_based_attributes.json'))['attributes']
archs = json.load(open('data/processed/archetype_assignments.json'))

expected_marksmen = {
    'Aphelios', 'Ashe', 'Caitlyn', 'Draven', 'Ezreal', 'Jhin', 'Jinx', 
    'Kaisa', 'Kalista', 'KogMaw', 'Lucian', 'MissFortune', 'Quinn', 
    'Samira', 'Sivir', 'Tristana', 'Twitch', 'Varus', 'Vayne', 'Xayah', 
    'Zeri', 'Corki', 'Kindred'
}

all_marksmen = [c for c, a in archs['assignments'].items() if a['primary_archetype'] == 'marksman']

true_positives = [c for c in all_marksmen if c in expected_marksmen]
false_positives = [c for c in all_marksmen if c not in expected_marksmen]

print("=" * 80)
print("MARKSMAN CLASSIFICATION REPORT")
print("=" * 80)
print(f"Total classified as marksman: {len(all_marksmen)}")
print(f"Expected marksmen: {len(expected_marksmen)}")
print(f"True positives: {len(true_positives)} ({len(true_positives)/len(expected_marksmen)*100:.1f}% recall)")
print(f"False positives: {len(false_positives)}")
print(f"Precision: {len(true_positives)/len(all_marksmen)*100:.1f}%")

print("\n" + "=" * 80)
print("TRUE POSITIVES (Correct Marksmen)")
print("=" * 80)
for c in sorted(true_positives):
    dps = attrs[c]['sustained_dps']
    print(f"✓ {c:12s} DPS: {dps:6.1f}")

print("\n" + "=" * 80)
print("FALSE POSITIVES (Non-marksmen classified as marksman)")
print("=" * 80)
print("(Showing first 20, sorted by DPS)")
false_with_dps = [(c, attrs[c]['sustained_dps']) for c in false_positives]
false_with_dps.sort(key=lambda x: x[1], reverse=True)

for c, dps in false_with_dps[:20]:
    print(f"✗ {c:12s} DPS: {dps:6.1f}")

if len(false_with_dps) > 20:
    print(f"... and {len(false_with_dps) - 20} more")

print("\n" + "=" * 80)
print("MISSED MARKSMEN (Below 119.2 DPS threshold)")
print("=" * 80)
missed = expected_marksmen - set(true_positives)
for c in sorted(missed):
    dps = attrs[c]['sustained_dps']
    arch = archs['assignments'][c]['primary_archetype']
    print(f"✗ {c:12s} DPS: {dps:6.1f} | Classified as: {arch}")
