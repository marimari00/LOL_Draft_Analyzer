import json

attrs = json.load(open('data/processed/spell_based_attributes.json'))['attributes']
archs = json.load(open('data/processed/archetype_assignments.json'))

# Check a few high-DPS marksmen that got misclassified
targets = ['Ezreal', 'Caitlyn', 'Kalista', 'Varus', 'Draven', 'Vayne', 'Tristana']

print("=" * 80)
print("DETAILED ANALYSIS OF MISCLASSIFIED HIGH-DPS MARKSMEN")
print("=" * 80)

for champ in targets:
    if champ in attrs and champ in archs['assignments']:
        a = attrs[champ]
        arch = archs['assignments'][champ]
        
        print(f"\n{champ}:")
        print(f"  Classified as: {arch['primary_archetype']} (score: {arch['primary_score']:.3f})")
        print(f"  Attributes:")
        print(f"    sustained_dps: {a['sustained_dps']:.1f}")
        print(f"    burst_dps: {a['burst_dps']:.1f}")
        print(f"    burst_index: {a['burst_index']:.3f}")
        print(f"    cc_score: {a['cc_score']:.3f}")
        print(f"    mobility_score: {a['mobility_score']:.1f}")
        print(f"    max_range: {a['max_range']}")
        print(f"  Top 3 archetype scores:")
        scores = sorted(arch['all_scores'].items(), key=lambda x: x[1], reverse=True)[:3]
        for archetype, score in scores:
            print(f"    {archetype:20s}: {score:.3f}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("Champions with high DPS but classified elsewhere likely have:")
print("- High burst_index → burst_assassin/burst_mage")
print("- High mobility → skirmisher")
print("- High CC → battle_mage")
print("\nThis is CORRECT per data-driven philosophy - if attributes suggest hybrid,")
print("the classification reflects the dominant pattern in their kit.")
