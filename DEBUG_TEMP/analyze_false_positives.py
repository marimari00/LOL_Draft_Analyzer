import json

assignments = json.load(open('data/processed/archetype_assignments.json'))
definitions = json.load(open('data/processed/archetype_definitions.json'))

print("MARKSMAN REQUIREMENTS:")
print("=" * 80)
for req_name, req_data in definitions['archetypes']['marksman']['requirements'].items():
    print(f"{req_name:20} {req_data}")

print("\n\nFALSE POSITIVES (Non-marksmen classified as marksman):")
print("=" * 80)

false_positives = ['Amumu', 'Anivia', 'Azir', 'Braum', 'Brand', 'Galio', 'Kennen', 
                   'Malphite', 'Shyvana', 'Skarner', 'Sona', 'Syndra', 'TahmKench', 'Vex']

for champ in false_positives:
    if champ in assignments:
        attrs = assignments[champ]['attributes']
        score = assignments[champ]['all_scores']['marksman']
        print(f"\n{champ} (score={score:.3f}):")
        print(f"  sustained_dps: {attrs['sustained_dps']:.1f} (min: 119.2)")
        print(f"  max_range: {attrs['max_range']:.0f} (min: 900)")
        print(f"  mobility: {attrs['mobility_score']:.1f} (max: 1.2)")
        print(f"  burst_index: {attrs['burst_index']:.3f} (max: 0.7)")
        print(f"  damage_profile: {attrs['damage_profile']}")
