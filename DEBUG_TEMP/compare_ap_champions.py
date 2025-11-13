import json

attrs = json.load(open('data/processed/spell_based_attributes.json', encoding='utf-8'))['attributes']

# AP champions classified as marksman
false_pos_ap = ['Anivia', 'Brand', 'Galio', 'Kennen', 'Malphite', 'Shyvana', 'Skarner', 'Sona', 'Syndra', 'TahmKench', 'Vex']
true_marksmen_ap = ['Caitlyn', 'Ezreal', 'Jhin']

print("=" * 80)
print("AP FALSE POSITIVES vs AP TRUE MARKSMEN")
print("=" * 80)

print("\nFALSE POSITIVES (AP mages misclassified as marksmen):")
for c in false_pos_ap:
    if c in attrs:
        a = attrs[c]
        print(f"{c:12s}: DPS={a['sustained_dps']:6.1f}, burst_index={a['burst_index']:.3f}, mobility={a['mobility_score']:.1f}, cc={a['cc_score']:.3f}, range={a['max_range']}")

print("\nTRUE MARKSMEN (AP marksmen correctly classified):")
for c in true_marksmen_ap:
    if c in attrs:
        a = attrs[c]
        print(f"{c:12s}: DPS={a['sustained_dps']:6.1f}, burst_index={a['burst_index']:.3f}, mobility={a['mobility_score']:.1f}, cc={a['cc_score']:.3f}, range={a['max_range']}")

print("\n" + "=" * 80)
print("KEY DIFFERENCES")
print("=" * 80)

false_cc = [attrs[c]['cc_score'] for c in false_pos_ap if c in attrs]
true_cc = [attrs[c]['cc_score'] for c in true_marksmen_ap if c in attrs]

print(f"False positive avg CC: {sum(false_cc)/len(false_cc):.3f}")
print(f"True marksmen avg CC: {sum(true_cc)/len(true_cc):.3f}")
print(f"\nHypothesis: False positives have higher CC (they're AP mages/tanks with CC)")
print(f"Recommendation: Add 'cc_score < 0.5' constraint to marksman archetype")
