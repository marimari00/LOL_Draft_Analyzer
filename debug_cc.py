import json
import re

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

# Typical durations
typical_durations = {
    'stun': 1.5, 'root': 2.0, 'knock up': 1.0,
    'charm': 1.5, 'fear': 1.5, 'taunt': 1.5,
    'silence': 2.0, 'slow': 2.0, 'suppress': 2.5, 'snare': 2.0
}

# Patterns (hard CC first)
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
    """Detect CC in description."""
    desc_lower = description.lower()
    for cc_type, pattern in cc_patterns.items():
        match = re.search(pattern, desc_lower, re.IGNORECASE)
        if match:
            duration = typical_durations.get(cc_type, 1.5)
            return (cc_type, duration)
    return None

# Test champions
test_champs = ['Zed', 'Ahri', 'Malphite', 'Morgana']

for champ_name in test_champs:
    print(f"\n{'='*60}")
    print(f"{champ_name}")
    print(f"{'='*60}")
    
    abilities = champions[champ_name]['abilities']
    
    for ability_key in ['Q', 'W', 'E', 'R']:
        if ability_key not in abilities:
            continue
        
        ability = abilities[ability_key]
        description = ability.get('description', '')
        
        cc_info = detect_cc(description)
        
        if cc_info:
            cc_type, duration = cc_info
            cc_weight = CC_TYPE_WEIGHT.get(cc_type, 0.5)
            cooldown = ability.get('cooldown', [10])[-1]
            uptime = 1.0 / (cooldown + 0.25)
            
            # Estimate reliability and target count (simplified)
            reliability = 0.6  # assume skillshot
            target_count = 1.0  # assume single target
            
            contribution = cc_weight * duration * reliability * target_count * uptime
            
            print(f"{ability_key} ({ability['name']}):")
            print(f"  Description: {description[:80]}...")
            print(f"  CC Type: {cc_type} (weight={cc_weight})")
            print(f"  Duration: {duration}s")
            print(f"  Cooldown: {cooldown}s")
            print(f"  Contribution: {contribution:.4f}")
        else:
            print(f"{ability_key} ({ability['name']}): No CC detected")
