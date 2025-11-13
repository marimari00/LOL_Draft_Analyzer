import json

attrs = json.load(open('data/processed/spell_based_attributes.json'))
assignments = json.load(open('data/processed/archetype_assignments.json'))

missed = ['Jhin', 'Jinx', 'Lucian', 'MissFortune', 'Twitch', 'Varus', 'Vayne', 'Xayah', 'Draven', 'Tristana']

print("MISSED MARKSMEN - DAMAGE PROFILE ANALYSIS")
print("=" * 80)

for champ in sorted(missed):
    if champ in attrs:
        profile = attrs[champ].get('damage_profile', 'MISSING')
        archetype = assignments[champ]['primary_archetype']
        marksman_score = assignments[champ]['all_scores'].get('marksman', 0)
        dps = attrs[champ].get('sustained_dps', 0)
        burst_idx = attrs[champ].get('burst_index', 0)
        
        print(f"{champ:14} profile={profile:8} archetype={archetype:16} marksman_score={marksman_score:.3f}")
        print(f"               DPS={dps:6.1f} burst_idx={burst_idx:.3f}")
        print()
