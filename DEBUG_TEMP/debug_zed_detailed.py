import json
import re

with open('data/raw/data_dragon_champions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Manual CC calculation for Zed
zed = data['champions']['Zed']['abilities']

print("ZED ABILITIES - DETAILED BREAKDOWN")
print("="*60)

for key in ['Q', 'W', 'E', 'R']:
    ability = zed[key]
    desc = ability['description'].lower()
    cd = ability['cooldown'][-1] if ability['cooldown'] else 10
    
    print(f"\n{key} ({ability['name']}) - CD: {cd}s")
    print(f"  Description: {desc[:150]}...")
    
    # Check for CC keywords
    keywords = ['stun', 'root', 'bind', 'charm', 'slow', 'knock', 'fear', 'taunt', 'suppress']
    found = [kw for kw in keywords if kw in desc]
    
    if found:
        print(f"  CC KEYWORDS FOUND: {found}")
        
        # Calculate expected contribution
        if 'slow' in found:
            cc_weight = 0.2
            duration = 2.0
            reliability = 0.6
            target_count = 2.0 if 'nearby' in desc or 'area' in desc else 1.0
            uptime = 1.0 / (cd + 0.25)
            contrib = cc_weight * duration * reliability * target_count * uptime
            print(f"  Expected contribution: {contrib:.4f}")
            print(f"    (weight={cc_weight} × duration={duration} × reliability={reliability} × targets={target_count} × uptime={uptime:.4f})")
    else:
        print(f"  No CC detected")

print("\n" + "="*60)
print("EXPECTED TOTAL: ~0.0738 (from E slow only)")
print("ACTUAL TOTAL: 0.2462")
print("DISCREPANCY: 3.34x too high!")
