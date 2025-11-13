"""
Analyze champion archetype assignments and identify questionable classifications.
"""

import json
from collections import defaultdict

# Load archetype assignments
with open('data/processed/champion_archetypes.json', 'r') as f:
    data = json.load(f)

assignments = data['assignments']

# Find questionable assignments
questionable = []

# 1. Marksman/ADCs not classified as marksman or hypercarry
traditional_adcs = ['Jinx', 'Caitlyn', 'Ashe', 'Sivir', 'Tristana', 'Twitch', 'Vayne', 
                     'KogMaw', 'Xayah', 'Kalista', 'Draven', 'Lucian', 'Ezreal', 'MissFortune', 'Aphelios']

# 2. Traditional assassins not classified as burst_assassin
traditional_assassins = ['Zed', 'Talon', 'Katarina', 'Akali', 'Fizz', 'Kassadin', 'Leblanc', 'Qiyana']

# 3. Traditional tanks not classified as engage_tank or juggernaut
traditional_tanks = ['Malphite', 'Ornn', 'Maokai', 'Nautilus', 'Leona', 'Alistar', 'Braum', 
                     'Sejuani', 'Sion', 'Chogath', 'Rammus', 'Zac']

# 4. Enchanters classified incorrectly
traditional_enchanters = ['Lulu', 'Janna', 'Nami', 'Soraka', 'Yuumi', 'Sona']

# 5. Control mages classified incorrectly
traditional_control_mages = ['Orianna', 'Syndra', 'Azir', 'Viktor', 'Anivia', 'Velkoz']

print("="*80)
print("QUESTIONABLE ARCHETYPE ASSIGNMENTS")
print("="*80)

# Check each category
categories = {
    "ADCs/Marksmen (expected marksman/hypercarry)": traditional_adcs,
    "Assassins (expected burst_assassin)": traditional_assassins,
    "Tanks (expected engage_tank/juggernaut)": traditional_tanks,
    "Enchanters (expected enchanter)": traditional_enchanters,
    "Control Mages (expected control_mage)": traditional_control_mages
}

for category, champions in categories.items():
    print(f"\n{category}")
    print("-" * 80)
    
    for champ in champions:
        if champ in assignments:
            info = assignments[champ]
            primary = info['primary_archetype']
            score = info['primary_score']
            
            # Check if misclassified
            if category == "ADCs/Marksmen (expected marksman/hypercarry)":
                if primary not in ['marksman', 'hypercarry']:
                    print(f"  ⚠ {champ}: {primary} (score: {score:.3f}) - Expected marksman/hypercarry")
                    
            elif category == "Assassins (expected burst_assassin)":
                if primary != 'burst_assassin':
                    print(f"  ⚠ {champ}: {primary} (score: {score:.3f}) - Expected burst_assassin")
                    
            elif category == "Tanks (expected engage_tank/juggernaut)":
                if primary not in ['engage_tank', 'juggernaut']:
                    print(f"  ⚠ {champ}: {primary} (score: {score:.3f}) - Expected engage_tank/juggernaut")
                    
            elif category == "Enchanters (expected enchanter)":
                if primary != 'enchanter':
                    print(f"  ⚠ {champ}: {primary} (score: {score:.3f}) - Expected enchanter")
                    
            elif category == "Control Mages (expected control_mage)":
                if primary != 'control_mage':
                    print(f"  ⚠ {champ}: {primary} (score: {score:.3f}) - Expected control_mage")

# Look for surprising primary archetypes
print("\n" + "="*80)
print("MOST SURPRISING ASSIGNMENTS")
print("="*80)

surprising = [
    ('Jinx', 'enchanter', 'Expected marksman/hypercarry'),
    ('Xerath', 'catch_champion', 'Expected poke_champion'),
    ('Orianna', 'early_game_bully', 'Expected control_mage'),
    ('Viktor', 'early_game_bully', 'Expected control_mage'),
    ('Malphite', 'early_game_bully', 'Expected engage_tank'),
    ('Syndra', 'diver', 'Expected control_mage/burst_assassin'),
]

for champ, got, expected in surprising:
    if champ in assignments:
        info = assignments[champ]
        primary = info['primary_archetype']
        score = info['primary_score']
        
        # Find expected archetype score
        expected_score = 0
        for arch in info['all_archetypes']:
            if expected.lower() in arch['name']:
                expected_score = arch['score']
                break
        
        if primary == got:
            print(f"\n{champ}:")
            print(f"  Got: {primary} (score: {score:.3f})")
            print(f"  Expected: {expected}")
            if expected_score > 0:
                print(f"  Expected score: {expected_score:.3f}")
            print(f"  Top 3 archetypes:")
            for arch in info['all_archetypes'][:3]:
                print(f"    - {arch['name']}: {arch['score']:.3f}")

# Show archetype distribution
print("\n" + "="*80)
print("ARCHETYPE DISTRIBUTION ANALYSIS")
print("="*80)

distribution = defaultdict(int)
for champ, info in assignments.items():
    distribution[info['primary_archetype']] += 1

print("\nCurrent distribution:")
for arch, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
    print(f"  {arch:25s}: {count:3d} champions")

print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)
print("\nPotential issues to investigate:")
print("1. Many ADCs classified as 'enchanter' or 'early_game_bully' instead of 'marksman'")
print("2. Control mages often classified as 'early_game_bully' or 'diver'")
print("3. Some tanks classified as 'early_game_bully' instead of 'engage_tank'")
print("4. The archetype definitions may need adjustment for:")
print("   - Marksman (too strict on gold_dependency?)")
print("   - Control_mage (may need better definition)")
print("   - Engage_tank (may need clearer tank identifiers)")
