"""Debug Rengar CC=4.0 by tracing the actual calculation."""
import json
import re

# Load Data Dragon
with open('data/raw/data_dragon_champions.json', encoding='utf-8') as f:
    dd_data = json.load(f)

rengar = dd_data['champions']['Rengar']

print("=" * 80)
print("RENGAR CC CALCULATION DEBUG")
print("=" * 80)

CC_TYPE_WEIGHT = {
    'stun': 1.0, 'root': 1.0, 'knock up': 1.0,
    'charm': 1.0, 'fear': 1.0, 'taunt': 1.0,
    'suppress': 1.0, 'snare': 1.0,
    'slow': 0.2, 'silence': 0.4
}

CC_RELIABILITY = {
    'point_click': 1.0,
    'easy_skillshot': 0.6,
    'hard_skillshot': 0.3,
    'conditional': 0.5
}

CC_TARGET_MULTIPLIER = {
    'single': 1.0,
    'small_aoe': 1.5,
    'medium_aoe': 2.0,
    'large_aoe': 2.5
}

total_cc = 0.0

for ability_key in ['Q', 'W', 'E', 'R']:
    if ability_key not in rengar['abilities']:
        continue
    
    ability = rengar['abilities'][ability_key]
    description = ability.get('description', '').lower()
    
    print(f"\n{ability_key} - {ability.get('name', 'Unknown')}:")
    print(f"  Description: {description[:300]}...")
    
    # Check for CC keywords
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
    
    cc_found = []
    for cc_type, pattern in cc_patterns.items():
        matches = list(re.finditer(pattern, description, re.IGNORECASE))
        if matches:
            cc_found.append((cc_type, len(matches)))
    
    if cc_found:
        print(f"  CC DETECTED: {cc_found}")
        
        # BUG: The code processes EACH MATCH, not each CC type!
        for cc_type, match_count in cc_found:
            cc_weight = CC_TYPE_WEIGHT.get(cc_type, 0.5)
            duration = 2.0  # typical
            
            # Check for skillshot
            if any(word in description for word in ['skillshot', 'line', 'projectile', 'throws']):
                reliability = CC_RELIABILITY['easy_skillshot']
            else:
                reliability = CC_RELIABILITY['point_click']
            
            # Check for AOE
            if any(word in description for word in ['all', 'enemies', 'area', 'around', 'nearby']):
                target_count = CC_TARGET_MULTIPLIER['medium_aoe']
            else:
                target_count = CC_TARGET_MULTIPLIER['single']
            
            # Get cooldown
            cooldown = ability.get('cooldown', [10])
            if isinstance(cooldown, list):
                cooldown = cooldown[-1] if cooldown else 10
            
            uptime = 1.0 / (cooldown + 0.25) if cooldown > 0 else 0
            
            cc_contribution = cc_weight * duration * reliability * target_count * uptime
            
            print(f"    {cc_type}: weight={cc_weight}, dur={duration}, rel={reliability}, "
                  f"targets={target_count}, CD={cooldown}, uptime={uptime:.4f}")
            print(f"    Contribution: {cc_contribution:.4f} (×{match_count} matches = {cc_contribution * match_count:.4f})")
            
            # BUG: Should only add once per ability, not once per regex match!
            total_cc += cc_contribution
    else:
        print(f"  No CC detected")

print(f"\n{'=' * 80}")
print(f"TOTAL CC SCORE: {total_cc:.4f}")
print(f"{'=' * 80}")
