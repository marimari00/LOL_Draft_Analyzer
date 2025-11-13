import json

attrs = json.load(open('data/processed/spell_based_attributes.json', encoding='utf-8'))['attributes']

marksmen = ['Ashe', 'Jinx', 'Caitlyn', 'Draven', 'Jhin', 'MissFortune', 'Tristana', 'Varus', 'KogMaw', 'Lucian', 'Twitch', 'Quinn', 'Corki', 'Samira']

print("=" * 70)
print("BURST_RATIO ANALYSIS FOR TRUE MARKSMEN")
print("=" * 70)

data = []
for c in marksmen:
    if c in attrs:
        a = attrs[c]
        data.append((c, a['burst_ratio'], a['sustained_dps'], a['burst_index']))

data.sort(key=lambda x: x[1])  # Sort by burst_ratio

for c, br, dps, bi in data:
    status = "✓ LOW" if br < 0.5 else "✗ HIGH"
    print(f"{status} {c:12s}: burst_ratio={br:.3f}, burst_index={bi:.3f}, sustained_dps={dps:6.1f}")

print("\n" + "=" * 70)
print("STATISTICS")
print("=" * 70)
low_br = sum(1 for _, br, _, _ in data if br < 0.5)
print(f"Marksmen with burst_ratio < 0.5: {low_br}/{len(data)} ({low_br/len(data)*100:.1f}%)")
print(f"Median burst_ratio: {sorted([br for _, br, _, _ in data])[len(data)//2]:.3f}")
print(f"\nConclusion: burst_ratio < 0.5 is TOO STRICT!")
print(f"Recommended threshold: burst_ratio < 0.7 (captures more marksmen)")
