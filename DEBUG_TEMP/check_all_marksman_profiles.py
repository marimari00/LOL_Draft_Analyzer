import json

attrs = json.load(open('data/processed/spell_based_attributes.json'))
assignments = json.load(open('data/processed/archetype_assignments.json'))

marksmen_expected = [
    'Aphelios', 'Ashe', 'Caitlyn', 'Corki', 'Draven', 'Ezreal', 'Jhin', 'Jinx',
    'Kaisa', 'Kalista', 'Kindred', 'KogMaw', 'Lucian', 'MissFortune', 'Quinn',
    'Samira', 'Senna', 'Sivir', 'Tristana', 'Twitch', 'Varus', 'Vayne', 'Xayah', 'Zeri'
]

print("MARKSMEN DAMAGE PROFILES & ARCHETYPES")
print("=" * 80)
for champ in sorted(marksmen_expected):
    if champ in attrs and champ in assignments:
        profile = attrs[champ].get('damage_profile', 'MISSING')
        archetype = assignments[champ]['archetype']
        dps = attrs[champ].get('sustained_dps', 0)
        burst_idx = attrs[champ].get('burst_index', 0)
        
        marker = "✓" if archetype == 'marksman' else "✗"
        print(f"{marker} {champ:12} profile={profile:8} archetype={archetype:16} DPS={dps:6.1f} burst_idx={burst_idx:.3f}")
