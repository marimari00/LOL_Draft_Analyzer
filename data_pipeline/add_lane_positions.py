"""Extract lane positions from info.lua and add to champion data.

This adds:
- primary_position: Most common/recommended lane
- viable_positions: All positions champion can play
"""

import json
import re
from pathlib import Path


def parse_info_lua_positions(filepath: str) -> dict:
    """Parse info.lua to extract champion positions."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by champion entries
    champion_blocks = re.split(r'\n  \[\"([^"]+)\"\] = \{', content)[1:]
    
    champion_positions = {}
    name_mapping = {}
    
    for i in range(0, len(champion_blocks), 2):
        if i+1 >= len(champion_blocks):
            break
            
        champ_name = champion_blocks[i]
        champ_data = champion_blocks[i+1]
        
        # Extract apiname
        apiname_match = re.search(r'\["apiname"\]\s*=\s*"([^"]+)"', champ_data)
        apiname = apiname_match.group(1) if apiname_match else champ_name
        
        # Extract positions
        client_pos_match = re.search(r'\["client_positions"\]\s*=\s*\{([^}]+)\}', champ_data)
        external_pos_match = re.search(r'\["external_positions"\]\s*=\s*\{([^}]+)\}', champ_data)
        
        client_positions = []
        if client_pos_match:
            positions_str = client_pos_match.group(1)
            client_positions = [p.strip().strip('"') for p in positions_str.split(',')]
        
        external_positions = []
        if external_pos_match:
            positions_str = external_pos_match.group(1)
            external_positions = [p.strip().strip('"') for p in positions_str.split(',')]
        
        # Use external positions (more complete), fallback to client
        positions = external_positions if external_positions else client_positions
        
        champion_positions[apiname] = {
            'primary_position': positions[0] if positions else 'Unknown',
            'viable_positions': positions
        }
        
        # Track name mapping
        if champ_name != apiname:
            name_mapping[champ_name] = apiname
    
    return champion_positions, name_mapping


def normalize_champion_name(name: str, manual_mappings: dict) -> str:
    """Normalize champion name to match our database."""
    # Manual mappings for special cases
    if name.lower() in manual_mappings:
        return manual_mappings[name.lower()]
    
    # Remove spaces and apostrophes
    normalized = name.replace("'", "").replace(" ", "")
    return normalized


def main():
    print("="*70)
    print("EXTRACTING LANE POSITIONS FROM INFO.LUA")
    print("="*70)
    
    # Manual name mappings
    manual_mappings = {
        'kaisa': 'Kaisa',
        "kai'sa": 'Kaisa',
        'kogmaw': 'KogMaw',
        "kog'maw": 'KogMaw',
        'missfortune': 'MissFortune',
        'miss fortune': 'MissFortune',
        'belveth': 'Belveth',
        "bel'veth": 'Belveth',
        'monkeyking': 'MonkeyKing',
        'wukong': 'MonkeyKing',
        'drmundo': 'DrMundo',
        'dr. mundo': 'DrMundo',
        'jarvaniv': 'JarvanIV',
        'jarvan iv': 'JarvanIV',
        'khazix': 'Khazix',
        "kha'zix": 'Khazix',
        'leesin': 'LeeSin',
        'masteryi': 'MasterYi',
        'reksai': 'RekSai',
        "rek'sai": 'RekSai',
        'tahmkench': 'TahmKench',
        'twistedfate': 'TwistedFate',
        'xinzhao': 'XinZhao',
        'nunu': 'Nunu',
        'nunu & willump': 'Nunu',
        'renata': 'Renata',
        'renata glasc': 'Renata'
    }
    
    # Parse info.lua
    info_file = Path('validation/info.lua')
    champion_positions, lua_name_mapping = parse_info_lua_positions(info_file)
    
    print(f"\nExtracted positions for {len(champion_positions)} champions")
    
    # Load current champion data
    with open('data/processed/champion_archetypes.json', 'r', encoding='utf-8') as f:
        champion_data = json.load(f)
    
    # Add positions to each champion
    matched = 0
    unmatched = []
    position_stats = {}
    
    for champ_name, champ_info in champion_data['assignments'].items():
        normalized = normalize_champion_name(champ_name, manual_mappings)
        
        if normalized in champion_positions:
            pos_data = champion_positions[normalized]
            champ_info['primary_position'] = pos_data['primary_position']
            champ_info['viable_positions'] = pos_data['viable_positions']
            matched += 1
            
            # Track position stats
            primary_pos = pos_data['primary_position']
            position_stats[primary_pos] = position_stats.get(primary_pos, 0) + 1
        else:
            champ_info['primary_position'] = 'Unknown'
            champ_info['viable_positions'] = []
            unmatched.append(champ_name)
    
    # Update metadata
    champion_data['metadata']['positions_added'] = True
    champion_data['metadata']['matched_positions'] = matched
    
    # Save updated data
    with open('data/processed/champion_archetypes.json', 'w', encoding='utf-8') as f:
        json.dump(champion_data, f, indent=2)
    
    print(f"\n✓ Matched {matched}/{len(champion_data['assignments'])} champions with positions")
    
    if unmatched:
        print(f"\n⚠ Unmatched champions ({len(unmatched)}):")
        for name in sorted(unmatched):
            print(f"  - {name}")
    
    print("\nPosition Distribution:")
    for pos, count in sorted(position_stats.items(), key=lambda x: -x[1]):
        pct = 100.0 * count / matched
        print(f"  {pos:10s}: {count:3d} ({pct:5.1f}%)")
    
    print("\n✓ Updated: data/processed/champion_archetypes.json")
    
    # Show examples
    print("\nExample Champions:")
    examples = ['Jinx', 'Yasuo', 'LeeSin', 'Thresh', 'Darius']
    for champ in examples:
        if champ in champion_data['assignments']:
            info = champion_data['assignments'][champ]
            print(f"  {champ:12s}: {info['primary_position']:7s} "
                  f"(can play: {', '.join(info['viable_positions'])})")


if __name__ == '__main__':
    main()
