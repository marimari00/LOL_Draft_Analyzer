import json

attrs = json.load(open('data/processed/spell_based_attributes.json'))['attributes']
archs = json.load(open('data/processed/archetype_assignments.json'))

expected_marksmen = [
    'Aphelios', 'Ashe', 'Caitlyn', 'Draven', 'Ezreal', 'Jhin', 'Jinx', 
    'Kaisa', 'Kalista', 'KogMaw', 'Lucian', 'MissFortune', 'Quinn', 
    'Samira', 'Sivir', 'Tristana', 'Twitch', 'Varus', 'Vayne', 'Xayah', 'Zeri'
]

print("=" * 80)
print("MARKSMAN DPS ANALYSIS (sorted by DPS)")
print("=" * 80)

data = []
for c in expected_marksmen:
    if c in attrs:
        a = attrs[c]
        arch = archs['assignments'][c]['primary_archetype'] if c in archs['assignments'] else 'N/A'
        score = archs['assignments'][c]['primary_score'] if c in archs['assignments'] else 0
        data.append((c, a['sustained_dps'], arch, score))

data.sort(key=lambda x: x[1], reverse=True)

for c, dps, arch, score in data:
    status = "✓" if arch == "marksman" else "✗"
    print(f"{status} {c:12s} DPS: {dps:6.1f} | Arch: {arch:16s} | Score: {score:.3f}")

print("\n" + "=" * 80)
print("THRESHOLD ANALYSIS")
print("=" * 80)
print(f"Champions above 119.2 threshold: {sum(1 for _, dps, _, _ in data if dps >= 119.2)}/{len(data)}")
print(f"Correctly classified: {sum(1 for _, _, arch, _ in data if arch == 'marksman')}/{len(data)}")
