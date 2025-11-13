"""Check raw CC scores BEFORE normalization to understand the range."""
import json
import re
from pathlib import Path

# Load data
with open('data/raw/data_dragon_champions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

champions = data['champions']

# CC type weights
CC_TYPE_WEIGHT = {
    'knock up': 1.0,
    'suppress': 1.2,
    'stun': 1.0,
    'root': 1.0,
    'snare': 1.0,
    'charm': 1.0,
    'fear': 1.0,
    'taunt': 1.0,
    'silence': 0.4,
    'slow': 0.2,
}

CC_RELIABILITY = {
    'point_click': 1.0,
    'conditional': 0.7,
    'easy_skillshot': 0.6,
    'hard_skillshot': 0.3
}

CC_TARGET_MULTIPLIER = {
    'single': 1.0,
    'small_aoe': 1.5,
    'medium_aoe': 2.0,
    'large_aoe': 2.5
}

typical_durations = {
    'stun': 1.5, 'root': 2.0, 'knock up': 1.0,
    'charm': 1.5, 'fear': 1.5, 'taunt': 1.5,
    'silence': 2.0, 'slow': 2.0, 'suppress': 2.5, 'snare': 2.0
}

cc_patterns = {
    'knock up': r'knock(?:s|ing|ed)?.*?(?:up|into\s+the\s+air|airborne)',
    'suppress': r'suppress(?:es|ing|ed)?',
    'stun': r'stun(?:s|ning|ned)?',
    'root': r'(?:root|bind)(?:s|ing|ed)?',
    'snare': r'snare(?:s|ing|ed)?',
    'charm': r'charm(?:s|ing|ed)?',
    'fear': r'fear(?:s|ing|ed)?',
    'taunt': r'taunt(?:s|ing|ed)?',
    'silence': r'silence(?:s|d)?',
    'slow': r'slow(?:s|ing|ed)?',
}

def detect_cc(description):
    desc_lower = description.lower()
    for cc_type, pattern in cc_patterns.items():
        match = re.search(pattern, desc_lower, re.IGNORECASE)
        if match:
            duration = typical_durations.get(cc_type, 1.5)
            return (cc_type, duration)
    return None

def estimate_reliability(description):
    desc_lower = description.lower()
    if any(word in desc_lower for word in ['skillshot', 'line', 'projectile']):
        if 'narrow' in desc_lower or 'fast' in desc_lower:
            return CC_RELIABILITY['hard_skillshot']
        return CC_RELIABILITY['easy_skillshot']
    if any(word in desc_lower for word in ['if', 'when', 'after', 'marked']):
        return CC_RELIABILITY['conditional']
    return CC_RELIABILITY['point_click']

def estimate_target_count(description):
    desc_lower = description.lower()
    if any(word in desc_lower for word in ['all', 'enemies', 'area', 'around', 'nearby']):
        if 'large' in desc_lower or 'all' in desc_lower:
            return CC_TARGET_MULTIPLIER['large_aoe']
        elif 'small' in desc_lower:
            return CC_TARGET_MULTIPLIER['small_aoe']
        return CC_TARGET_MULTIPLIER['medium_aoe']
    return CC_TARGET_MULTIPLIER['single']

# Compute raw CC scores
raw_scores = {}
for champ_name, champ_data in champions.items():
    abilities = champ_data['abilities']
    total_cc = 0.0
    
    for ability_key in ['Q', 'W', 'E', 'R']:
        if ability_key not in abilities:
            continue
        
        ability = abilities[ability_key]
        description = ability.get('description', '').lower()
        
        cc_info = detect_cc(description)
        
        if cc_info:
            cc_type, duration = cc_info
            cc_weight = CC_TYPE_WEIGHT.get(cc_type, 0.5)
            reliability = estimate_reliability(description)
            target_count = estimate_target_count(description)
            
            cooldown = ability.get('cooldown', [10])[-1] if ability.get('cooldown') else 10
            uptime = 1.0 / (cooldown + 0.25) if cooldown > 0 else 0
            
            cc_contribution = cc_weight * duration * reliability * target_count * uptime
            total_cc += cc_contribution
    
    raw_scores[champ_name] = total_cc

# Sort and display
sorted_scores = sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)

print("RAW CC SCORES (BEFORE NORMALIZATION)")
print("="*60)
print("\nTop 10 CC champions:")
for name, score in sorted_scores[:10]:
    print(f"  {name:20s}: {score:.4f}")

print("\n\nBottom 10 CC champions:")
for name, score in sorted_scores[-10:]:
    print(f"  {name:20s}: {score:.4f}")

print("\n\nKey test cases:")
test_champs = ['Zed', 'Ahri', 'Malphite', 'Leona', 'Morgana', 'Akshan']
for name in test_champs:
    score = raw_scores.get(name, 0)
    print(f"  {name:20s}: {score:.4f}")

print("\n\nStatistics:")
scores_list = list(raw_scores.values())
print(f"  Min:    {min(scores_list):.4f}")
print(f"  Max:    {max(scores_list):.4f}")
print(f"  Mean:   {sum(scores_list)/len(scores_list):.4f}")
print(f"  Median: {sorted(scores_list)[len(scores_list)//2]:.4f}")
