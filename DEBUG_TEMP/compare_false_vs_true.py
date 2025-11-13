import json

assignments = json.load(open('data/processed/archetype_assignments.json'))

# From previous validation
false_positives = ['Amumu', 'Anivia', 'Azir', 'Braum', 'Brand', 'Galio', 'Kennen', 
                   'Malphite', 'Shyvana', 'Skarner', 'Sona', 'Syndra', 'TahmKench', 'Vex']

true_marksmen = ['Ashe', 'Caitlyn', 'Corki', 'Jhin', 'KogMaw', 'Lucian', 'MissFortune', 
                 'Quinn', 'Samira', 'Twitch']

print("FALSE POSITIVES vs TRUE MARKSMEN:")
print("=" * 80)
print("\nFALSE POSITIVES:")
for champ in false_positives[:10]:
    if champ in assignments:
        attrs = assignments[champ]['attributes']
        print(f"{champ:12} DPS={attrs['sustained_dps']:6.1f} range={attrs['max_range']:5.0f} " +
              f"mobility={attrs['mobility_score']:.1f} burst={attrs['burst_index']:.3f} " +
              f"profile={attrs['damage_profile']}")

print("\nTRUE MARKSMEN:")
for champ in true_marksmen[:10]:
    if champ in assignments:
        attrs = assignments[champ]['attributes']
        print(f"{champ:12} DPS={attrs['sustained_dps']:6.1f} range={attrs['max_range']:5.0f} " +
              f"mobility={attrs['mobility_score']:.1f} burst={attrs['burst_index']:.3f} " +
              f"profile={attrs['damage_profile']}")
