import json

attrs = json.load(open('data/processed/spell_based_attributes.json', encoding='utf-8'))['attributes']
archs = json.load(open('data/processed/archetype_assignments.json', encoding='utf-8'))

# Get all current marksmen classifications
all_marksmen = [c for c, a in archs['assignments'].items() if a['primary_archetype'] == 'marksman']

print("=" * 80)
print("DAMAGE PROFILE ANALYSIS")
print("=" * 80)

true_marksmen = [
    'Ashe', 'Caitlyn', 'Corki', 'Draven', 'Ezreal', 'Jhin', 'Jinx', 
    'Kaisa', 'Kalista', 'KogMaw', 'Lucian', 'MissFortune', 'Quinn', 
    'Samira', 'Sivir', 'Tristana', 'Twitch', 'Varus', 'Vayne', 'Xayah', 'Zeri'
]

false_positives = [c for c in all_marksmen if c not in true_marksmen]

print(f"\nTRUE MARKSMEN damage profiles (N={len([c for c in true_marksmen if c in attrs])}):")
profiles = {}
for c in true_marksmen:
    if c in attrs:
        prof = attrs[c]['damage_profile']
        profiles[prof] = profiles.get(prof, 0) + 1
        if profiles[prof] <= 3:  # Show first 3 examples
            print(f"  {c:12s}: {prof}")

print(f"\nSummary: {profiles}")

print(f"\nFALSE POSITIVES damage profiles (N={len(false_positives)}):")
fp_profiles = {}
for c in false_positives:
    if c in attrs:
        prof = attrs[c]['damage_profile']
        fp_profiles[prof] = fp_profiles.get(prof, 0) + 1
        print(f"  {c:12s}: {prof}")

print(f"\nSummary: {fp_profiles}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("TRUE marksmen: Mix of 'ap', 'physical', 'neutral'")
print(f"FALSE positives: Mostly '{max(fp_profiles, key=fp_profiles.get)}'" if fp_profiles else "")
print("\ndamage_profile filter NOT effective - marksmen are AP/physical/neutral")
print("Need different approach: Likely combination of attributes")
