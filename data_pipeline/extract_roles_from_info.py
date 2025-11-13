"""
Extract champion roles from info.json (absolute source of truth).
This replaces computed archetype assignments with official Riot role data.
"""

import json
import re
from pathlib import Path

def parse_info_lua(filepath: str) -> dict:
    """Parse info.lua Lua table format to extract champion roles."""
    
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    
    # Parse champion blocks - each starts with ["ChampName"] = {
    champion_blocks = re.split(r'\n  \[\"([^"]+)\"\] = \{', content)[1:]
    
    champion_roles = {}
    name_mapping = {}
    
    # Process pairs of (champion_name, champion_data)
    for i in range(0, len(champion_blocks), 2):
        if i+1 >= len(champion_blocks):
            break
        
        champion = champion_blocks[i]
        data_block = champion_blocks[i+1]
        
        # Extract apiname (normalized name)
        apiname_match = re.search(r'\["apiname"\]\s*=\s*"([^"]+)"', data_block)
        apiname = apiname_match.group(1) if apiname_match else champion
        
        # Extract role line: ["role"] = {"Role1", "Role2"},
        role_match = re.search(r'\["role"\]\s*=\s*\{([^}]+)\}', data_block)
        
        if role_match:
            roles_str = role_match.group(1)
            roles = re.findall(r'"([^"]+)"', roles_str)
            
            champion_roles[apiname] = {
                'display_name': champion,
                'apiname': apiname,
                'primary_role': roles[0] if roles else 'Unknown',
                'all_roles': roles
            }
            
            # Store name mapping for lookup
            name_mapping[champion.lower()] = apiname
            name_mapping[apiname.lower()] = apiname
    
    return champion_roles, name_mapping

def normalize_champion_name(name: str, name_mapping: dict) -> str:
    """Normalize champion name to match info.json format."""
    # Try exact match
    if name in name_mapping:
        return name_mapping[name]
    
    # Try lowercase match
    lower_name = name.lower()
    if lower_name in name_mapping:
        return name_mapping[lower_name]
    
    # Try removing spaces and apostrophes
    clean_name = name.replace(' ', '').replace("'", '')
    if clean_name.lower() in name_mapping:
        return name_mapping[clean_name.lower()]
    
    # Manual name mappings for known mismatches
    manual_mappings = {
        'kaisa': 'Kaisa',
        "kai'sa": 'Kaisa',
        'kogmaw': 'KogMaw',
        "kog'maw": 'KogMaw',
        'missfortune': 'MissFortune',
        'miss fortune': 'MissFortune',
    }
    
    check_name = name.lower()
    if check_name in manual_mappings:
        return manual_mappings[check_name]
    
    return name

def map_riot_role_to_archetype(riot_role: str) -> str:
    """Map Riot's role taxonomy to our archetype system."""
    
    role_mapping = {
        # Direct mappings
        'Marksman': 'marksman',
        'Assassin': 'burst_assassin',
        'Burst': 'burst_mage',
        'Battlemage': 'battle_mage',
        'Artillery': 'artillery_mage',
        'Catcher': 'catcher',
        'Enchanter': 'enchanter',
        'Juggernaut': 'juggernaut',
        'Diver': 'diver',
        'Vanguard': 'engage_tank',
        'Warden': 'warden',
        'Skirmisher': 'skirmisher',
        'Specialist': 'specialist',
        
        # Additional mappings
        'Tank': 'engage_tank',
        'Fighter': 'skirmisher',
        'Mage': 'burst_mage',
        'Support': 'enchanter',
    }
    
    return role_mapping.get(riot_role, 'specialist')

def main():
    print("="*70)
    print("EXTRACTING ROLES FROM INFO.LUA (ABSOLUTE SOURCE OF TRUTH)")
    print("="*70)
    
    # Parse info.lua
    info_file = Path('validation/info.lua')
    champion_roles, name_mapping = parse_info_lua(info_file)
    
    print(f"\nExtracted roles for {len(champion_roles)} champions")
    
    # Load our current attribute data
    attr_file = Path('data/processed/spell_based_attributes_patched.json')
    with open(attr_file) as f:
        attr_data = json.load(f)
    
    attributes = attr_data['attributes']
    
    # Create new assignments using info.json roles
    assignments = {}
    archetype_counts = {}
    matched = 0
    unmatched = []
    
    for champ_name in attributes.keys():
        # Normalize name to match info.json
        normalized_name = normalize_champion_name(champ_name, name_mapping)
        
        if normalized_name in champion_roles:
            role_info = champion_roles[normalized_name]
            primary_riot_role = role_info['primary_role']
            all_riot_roles = role_info['all_roles']
            
            # Map to our archetype system
            primary_archetype = map_riot_role_to_archetype(primary_riot_role)
            secondary_archetypes = [map_riot_role_to_archetype(r) for r in all_riot_roles[1:]]
            
            # Get attributes
            attrs = attributes[champ_name]
            
            assignments[champ_name] = {
                'primary_archetype': primary_archetype,
                'secondary_archetypes': secondary_archetypes,
                'riot_roles': all_riot_roles,
                'source': 'info.json',
                'confidence': 1.0,  # Official data = 100% confidence
                'attributes': attrs
            }
            
            archetype_counts[primary_archetype] = archetype_counts.get(primary_archetype, 0) + 1
            matched += 1
        else:
            # No match in info.json - keep as specialist
            assignments[champ_name] = {
                'primary_archetype': 'specialist',
                'secondary_archetypes': [],
                'riot_roles': ['Unknown'],
                'source': 'fallback',
                'confidence': 0.0,
                'attributes': attributes[champ_name]
            }
            archetype_counts['specialist'] = archetype_counts.get('specialist', 0) + 1
            unmatched.append(champ_name)
    
    # Save to file
    output = {
        'metadata': {
            'source': 'info.lua (Riot official role taxonomy)',
            'total_champions': len(assignments),
            'matched_with_info_json': matched,
            'unmatched': len(unmatched),
            'note': 'Roles assigned directly from info.lua, attributes from patched data'
        },
        'distribution': archetype_counts,
        'assignments': assignments
    }
    
    output_file = Path('data/processed/champion_archetypes.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Matched {matched}/{len(attributes)} champions with info.lua")
    
    if unmatched:
        print(f"\n⚠️  Unmatched champions ({len(unmatched)}):")
        for name in sorted(unmatched):
            print(f"  - {name}")
    
    print(f"\nArchetype Distribution:")
    for archetype, count in sorted(archetype_counts.items(), key=lambda x: -x[1]):
        pct = 100.0 * count / len(assignments)
        print(f"  {archetype:20s}: {count:3d} ({pct:5.1f}%)")
    
    # Show marksmen specifically
    marksmen = [name for name, data in assignments.items() 
                if data['primary_archetype'] == 'marksman']
    
    print(f"\n{'='*70}")
    print(f"MARKSMEN ({len(marksmen)}):")
    print('='*70)
    for marksman in sorted(marksmen):
        data = assignments[marksman]
        attrs = data['attributes']
        riot_roles = ', '.join(data['riot_roles'])
        print(f"  {marksman:15s} | DPS={attrs['sustained_dps']:6.1f} | AD={attrs['total_ad_ratio']:4.2f} | Roles: {riot_roles}")
    
    print(f"\n✓ Saved to: {output_file}")


if __name__ == '__main__':
    main()
