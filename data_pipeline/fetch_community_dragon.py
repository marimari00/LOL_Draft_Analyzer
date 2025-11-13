"""
Community Dragon Data Fetcher

Community Dragon provides enhanced champion data with more detail than Data Dragon.
This is especially useful for newer champions not yet on the wiki.

Provides:
- Detailed ability mechanics
- CC durations and types
- Damage values and ratios
- Ability interactions
"""

import requests
import json
from pathlib import Path
from typing import Dict, Optional
import time


class CommunityDragonFetcher:
    """Fetches enhanced champion data from Community Dragon."""
    
    # Community Dragon raw content CDN
    BASE_URL = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1"
    
    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_champion_summary(self) -> Optional[Dict]:
        """
        Fetch champion summary data.
        
        Returns:
            Dictionary of all champions with IDs
        """
        url = f"{self.BASE_URL}/champion-summary.json"
        
        try:
            print(f"Fetching champion summary from Community Dragon...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            print(f"✓ Found {len(data)} champions")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching champion summary: {e}")
            return None
    
    def fetch_champion_data(self, champion_id: int) -> Optional[Dict]:
        """
        Fetch detailed data for a specific champion.
        
        Args:
            champion_id: Numeric champion ID
            
        Returns:
            Detailed champion data
        """
        url = f"{self.BASE_URL}/champions/{champion_id}.json"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error: {e}")
            return None
    
    def parse_ability_data(self, spell_data: Dict) -> Dict:
        """
        Parse ability data from Community Dragon format.
        
        Args:
            spell_data: Spell data from Community Dragon
            
        Returns:
            Parsed ability information
        """
        ability_info = {
            'name': spell_data.get('name', ''),
            'description': spell_data.get('description', ''),
        }
        
        # Extract cooldown
        if 'cooldown' in spell_data:
            cooldown = spell_data['cooldown']
            if isinstance(cooldown, list):
                ability_info['cooldown'] = cooldown
            else:
                ability_info['cooldown'] = [cooldown]
        
        # Extract cost
        if 'cost' in spell_data:
            ability_info['cost'] = spell_data['cost']
        
        # Extract range
        if 'range' in spell_data:
            range_val = spell_data['range']
            if isinstance(range_val, list):
                ability_info['range'] = range_val
            else:
                ability_info['range'] = [range_val]
        
        # Extract effect amounts (damage, CC duration, etc.)
        if 'effectAmount' in spell_data:
            ability_info['effects'] = spell_data['effectAmount']
        
        # Extract damage type
        if 'damageType' in spell_data:
            ability_info['damage_type'] = spell_data['damageType']
        
        return ability_info
    
    def fetch_all_champions(self, champion_list: Optional[list] = None) -> Dict:
        """
        Fetch enhanced data for all champions or a specific list.
        
        Args:
            champion_list: Optional list of champion names to fetch
            
        Returns:
            Dictionary of champion data
        """
        print("=" * 70)
        print("Community Dragon Data Fetcher")
        print("=" * 70)
        
        # Get champion summary to map names to IDs
        summary = self.fetch_champion_summary()
        if not summary:
            return {}
        
        # Create name -> ID mapping (filter out test champions)
        name_to_id = {}
        for champ in summary:
            name = champ.get('alias', '').replace(' ', '')  # Remove spaces
            champ_id = champ.get('id')
            
            # Skip test/internal champions (Ruby prefix, None, negative IDs)
            if not name or not champ_id:
                continue
            if name.startswith('Ruby_') or name == 'None' or champ_id < 0:
                continue
            
            name_to_id[name] = champ_id
        
        print(f"\nFetching detailed data for champions...")
        
        all_data = {}
        champions_to_fetch = champion_list if champion_list else list(name_to_id.keys())
        
        for i, champ_name in enumerate(champions_to_fetch, 1):
            if champ_name not in name_to_id:
                print(f"[{i}/{len(champions_to_fetch)}] {champ_name}: ✗ Not found in summary")
                continue
            
            champ_id = name_to_id[champ_name]
            print(f"[{i}/{len(champions_to_fetch)}] {champ_name} (ID: {champ_id})...", end=' ')
            
            data = self.fetch_champion_data(champ_id)
            if data:
                # Parse abilities
                abilities = {}
                spells = data.get('spells', [])
                
                # Map spells to Q, W, E, R
                spell_keys = ['Q', 'W', 'E', 'R']
                for j, spell in enumerate(spells[:4]):  # First 4 are basic abilities
                    key = spell_keys[j] if j < len(spell_keys) else f"Ability{j}"
                    abilities[key] = self.parse_ability_data(spell)
                
                all_data[champ_name] = {
                    'champion_id': champ_name,
                    'name': data.get('name', champ_name),
                    'abilities': abilities,
                    'passive': self.parse_ability_data(data.get('passive', {})) if 'passive' in data else None
                }
                
                print(f"✓ ({len(abilities)} abilities)")
            
            # Rate limiting
            time.sleep(0.2)
        
        # Save to disk
        output_file = self.output_dir / "community_dragon_champions.json"
        output_data = {
            'metadata': {
                'source': 'Community Dragon',
                'champion_count': len(all_data),
                'url': self.BASE_URL
            },
            'champions': all_data
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved Community Dragon data to {output_file}")
        print(f"Successfully fetched: {len(all_data)} champions")
        
        return all_data


def main():
    """Fetch data for all champions or specific list."""
    import sys
    
    fetcher = CommunityDragonFetcher()
    
    # Check if we should fetch all or just newer champions
    if '--all' in sys.argv:
        print("\nFetching data for ALL champions from Community Dragon...")
        print("This will take ~1 minute for 171 champions.\n")
        fetcher.fetch_all_champions()  # Fetch all
    else:
        # Default: Just fetch newer champions likely missing from wiki
        newer_champions = [
            'Mel',
            'Yunara', 
            'Ambessa',
            'Aurora',
            'Smolder',
            'Hwei',
            'Briar',
            'Naafiri',
            'Milio'
        ]
        
        print("\nFetching data for newer champions...")
        print(f"Target champions: {', '.join(newer_champions)}")
        print("(Use --all flag to fetch all 171 champions)\n")
        
        fetcher.fetch_all_champions(newer_champions)


if __name__ == "__main__":
    main()
