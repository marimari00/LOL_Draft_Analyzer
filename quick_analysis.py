"""Quick analysis of key patterns."""
import json

# Load data
with open('data/processed/champion_archetypes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('data/processed/enhanced_attributes.json', 'r', encoding='utf-8') as f:
    attrs = json.load(f)

print("=" * 80)
print("KEY FINDINGS")
print("=" * 80)

# 1. Who has burst_assassin scores?
print("\n1. CHAMPIONS WITH BURST_ASSASSIN SCORES (top 20):")
assassin_scores = []
for champ, info in data['assignments'].items():
    if champ not in attrs:
        continue
    for arch in info['all_archetypes']:
        if arch['name'] == 'burst_assassin':
            assassin_scores.append((champ, arch['score'], attrs[champ].get('cc_score', 0)))
assassin_scores.sort(key=lambda x: x[1], reverse=True)
for champ, score, cc in assassin_scores[:20]:
    print(f"  {champ:20s} score={score:.3f}  CC={cc:.3f}  {'✓ PRIMARY' if data['assignments'][champ]['primary_archetype'] == 'burst_assassin' else ''}")

# 2. Marksman classification issues
print("\n2. MARKSMAN THAT BECAME POKE_CHAMPION:")
marksmen = ['Jinx', 'Ashe', 'Jhin', 'Draven', 'MissFortune', 'Sivir', 'Caitlyn', 'Tristana', 'Vayne', 'Lucian']
for champ in marksmen:
    if champ in data['assignments']:
        primary = data['assignments'][champ]['primary_archetype']
        if primary != 'marksman':
            # Find marksman score
            mm_score = 0
            primary_score = data['assignments'][champ]['primary_score']
            for arch in data['assignments'][champ]['all_archetypes']:
                if arch['name'] == 'marksman':
                    mm_score = arch['score']
                    break
            print(f"  {champ:20s} {primary:20s} ({primary_score:.3f}) vs marksman ({mm_score:.3f})")

# 3. Engage tanks with low CC
print("\n3. ENGAGE_TANKS (checking CC scores):")
for champ, info in data['assignments'].items():
    if champ not in attrs:
        continue
    if info['primary_archetype'] == 'engage_tank':
        cc = attrs[champ].get('cc_score', 0)
        print(f"  {champ:20s} CC={cc:.3f}")

# 4. Burst values - are they all the same?
print("\n4. BURST_PATTERN DISTRIBUTION:")
burst_values = {}
for champ, attr in attrs.items():
    burst = attr.get('burst_pattern', 0)
    burst_values[burst] = burst_values.get(burst, 0) + 1
for burst, count in sorted(burst_values.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  Burst={burst:.3f}: {count} champions")

# 5. Why is Rengar CC=4.0?
print("\n5. RENGAR CC INVESTIGATION:")
if 'Rengar' in attrs:
    print(f"  Raw CC score: {attrs['Rengar'].get('cc_score', 0)}")
    print(f"  Attributes: {json.dumps({k:v for k,v in attrs['Rengar'].items() if 'cc' in k.lower() or 'stun' in k.lower() or 'root' in k.lower() or 'slow' in k.lower()}, indent=4)}")
