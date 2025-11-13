"""
Comprehensive archetype analysis - identify unexpected classifications.
"""
import json
from collections import defaultdict

# Load data
with open('data/processed/champion_archetypes.json', 'r', encoding='utf-8') as f:
    archetypes_data = json.load(f)

with open('data/processed/computed_attributes.json', 'r', encoding='utf-8') as f:
    attrs_data = json.load(f)

with open('data/processed/enhanced_attributes.json', 'r', encoding='utf-8') as f:
    enhanced_data = json.load(f)

assignments = archetypes_data['assignments']
attrs = attrs_data['champions']
enhanced = enhanced_data  # Direct access, no 'champions' key

# Expected archetypes based on common knowledge
EXPECTED_ARCHETYPES = {
    'Zed': 'burst_assassin',
    'Talon': 'burst_assassin',
    'Katarina': 'burst_assassin',
    'Akali': 'burst_assassin',
    'Fizz': 'burst_assassin',
    'Leblanc': 'burst_assassin',
    'Qiyana': 'burst_assassin',
    'Rengar': 'burst_assassin',
    'Khazix': 'burst_assassin',
    'Evelynn': 'burst_assassin',
    
    'Jinx': 'marksman',
    'Caitlyn': 'marksman',
    'Ashe': 'marksman',
    'Tristana': 'marksman',
    'Vayne': 'marksman',
    'Jhin': 'marksman',
    'MissFortune': 'marksman',
    'Draven': 'marksman',
    'Ezreal': 'marksman',
    'Lucian': 'marksman',
    
    'Malphite': 'engage_tank',
    'Leona': 'engage_tank',
    'Nautilus': 'engage_tank',
    'Alistar': 'engage_tank',
    'Ornn': 'engage_tank',
    'Zac': 'engage_tank',
    'Amumu': 'engage_tank',
    
    'Orianna': 'control_mage',
    'Anivia': 'control_mage',
    'Viktor': 'control_mage',
    'Azir': 'control_mage',
    'Syndra': 'control_mage',
    
    'Lulu': 'enchanter',
    'Janna': 'enchanter',
    'Soraka': 'enchanter',
    'Yuumi': 'enchanter',
    'Nami': 'enchanter',
}

print("="*80)
print("ARCHETYPE ANALYSIS - UNEXPECTED CLASSIFICATIONS")
print("="*80)

# Check for mismatches
mismatches = []
for champ, expected in EXPECTED_ARCHETYPES.items():
    actual = assignments[champ]['primary_archetype']
    if actual != expected:
        score = assignments[champ]['primary_score']
        # Find expected archetype score in all_archetypes list
        expected_score = 0
        for arch_data in assignments[champ]['all_archetypes']:
            if arch_data['name'] == expected:
                expected_score = arch_data['score']
                break
        
        mismatches.append({
            'champion': champ,
            'expected': expected,
            'actual': actual,
            'actual_score': score,
            'expected_score': expected_score,
            'cc_score': attrs[champ]['cc_score'],
            'burst_pattern': enhanced[champ]['burst_pattern'],
            'mobility': attrs[champ]['mobility_score']
        })

if mismatches:
    print(f"\n{len(mismatches)} UNEXPECTED CLASSIFICATIONS:")
    print("-"*80)
    for m in sorted(mismatches, key=lambda x: x['champion']):
        print(f"\n{m['champion']}:")
        print(f"  Expected: {m['expected']} (score: {m['expected_score']:.3f})")
        print(f"  Actual:   {m['actual']} (score: {m['actual_score']:.3f})")
        print(f"  Attributes: CC={m['cc_score']:.3f}, Burst={m['burst_pattern']:.3f}, Mobility={m['mobility']:.3f}")
else:
    print("\n✓ All checked champions match expected archetypes!")

# Check each archetype for suspicious members
print("\n" + "="*80)
print("ARCHETYPE MEMBERSHIP REVIEW")
print("="*80)

by_archetype = defaultdict(list)
for champ, data in assignments.items():
    primary = data['primary_archetype']
    score = data['primary_score']
    by_archetype[primary].append((champ, score))

# Sort and display each archetype
for archetype in sorted(by_archetype.keys()):
    members = sorted(by_archetype[archetype], key=lambda x: x[1], reverse=True)
    print(f"\n{archetype.upper().replace('_', ' ')} ({len(members)} champions):")
    
    for champ, score in members:
        # Get key attributes
        cc = attrs[champ]['cc_score']
        burst = enhanced[champ]['burst_pattern']
        sustained = enhanced[champ]['sustained_pattern']
        mobility = attrs[champ]['mobility_score']
        damage_late = enhanced[champ]['damage_late']
        
        # Flag suspicious
        suspicious = ""
        
        if archetype == 'burst_assassin' and burst < 0.7:
            suspicious = " ⚠️ Low burst"
        elif archetype == 'burst_assassin' and mobility < 0.7:
            suspicious = " ⚠️ Low mobility"
        elif archetype == 'burst_assassin' and cc > 0.15:
            suspicious = " ⚠️ High CC"
            
        elif archetype == 'marksman' and damage_late < 0.3:
            suspicious = " ⚠️ Weak late game"
            
        elif archetype == 'engage_tank' and cc < 0.25:
            suspicious = " ⚠️ Low CC"
            
        elif archetype == 'control_mage' and cc < 0.25:
            suspicious = " ⚠️ Low CC for control mage"
            
        print(f"  {champ:20s} {score:.3f}  [CC:{cc:.2f} B:{burst:.2f} M:{mobility:.2f}]{suspicious}")

# Interesting counter-intuitive results
print("\n" + "="*80)
print("INTERESTING DUAL-ARCHETYPE CHAMPIONS")
print("="*80)

for champ, data in sorted(assignments.items()):
    # Find champions with multiple high scores
    high_scores = [(arch_data['name'], arch_data['score']) 
                   for arch_data in data['all_archetypes'] 
                   if arch_data['score'] >= 0.9]
    
    if len(high_scores) >= 2:
        print(f"\n{champ}:")
        for arch, score in sorted(high_scores, key=lambda x: x[1], reverse=True):
            print(f"  {arch:30s}: {score:.3f}")

print("\n" + "="*80)
