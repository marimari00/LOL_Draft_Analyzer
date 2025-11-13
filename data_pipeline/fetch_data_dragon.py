"""
Fetch champion data from Riot's Data Dragon CDN.

Data Dragon provides:
- Champion base stats (HP, AD, armor, MR, movement speed, attack range)
- Per-level stat growth
- Ability descriptions, cooldowns, costs, ranges
- Damage ratios (AP/AD/bonus scaling)

This is our primary source of truth for champion statistics.
"""

import requests
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class DataDragonFetcher:
    """Fetches and processes champion data from Riot Data Dragon CDN."""
    
    BASE_URL = "https://ddragon.leagueoflegends.com"
    
    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.version: Optional[str] = None
        self.champion_list: List[str] = []
        
    def get_latest_version(self) -> str:
        """
        Fetch the latest Data Dragon version.
        
        Returns:
            Version string (e.g., "13.24.1")
        """
        url = f"{self.BASE_URL}/api/versions.json"
        response = requests.get(url)
        response.raise_for_status()
        versions = response.json()
        self.version = versions[0]  # First item is latest
        print(f"Latest Data Dragon version: {self.version}")
        return self.version
    
    def get_champion_list(self) -> List[str]:
        """
        Fetch list of all champion IDs.
        
        Returns:
            List of champion IDs (e.g., ["Aatrox", "Ahri", ...])
        """
        if not self.version:
            self.get_latest_version()
            
        url = f"{self.BASE_URL}/cdn/{self.version}/data/en_US/champion.json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Extract champion keys
        self.champion_list = list(data['data'].keys())
        print(f"Found {len(self.champion_list)} champions")
        return self.champion_list
    
    def fetch_champion_data(self, champion_id: str) -> Dict:
        """
        Fetch detailed data for a specific champion.
        
        Args:
            champion_id: Champion ID (e.g., "Ahri")
            
        Returns:
            Champion data dictionary with stats, abilities, etc.
        """
        if not self.version:
            self.get_latest_version()
            
        url = f"{self.BASE_URL}/cdn/{self.version}/data/en_US/champion/{champion_id}.json"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['data'][champion_id]
    
    def process_champion_stats(self, champion_data: Dict) -> Dict:
        """
        Extract and process base stats and growth from raw champion data.
        
        Args:
            champion_data: Raw champion data from Data Dragon
            
        Returns:
            Processed stats dictionary
        """
        stats = champion_data['stats']
        
        return {
            'id': champion_data['id'],
            'key': champion_data['key'],
            'name': champion_data['name'],
            'title': champion_data['title'],
            'base_stats': {
                'hp': stats['hp'],
                'hp_per_level': stats['hpperlevel'],
                'mp': stats['mp'],
                'mp_per_level': stats['mpperlevel'],
                'move_speed': stats['movespeed'],
                'armor': stats['armor'],
                'armor_per_level': stats['armorperlevel'],
                'magic_resist': stats['spellblock'],
                'magic_resist_per_level': stats['spellblockperlevel'],
                'attack_damage': stats['attackdamage'],
                'attack_damage_per_level': stats['attackdamageperlevel'],
                'attack_speed': stats['attackspeed'],
                'attack_speed_per_level': stats['attackspeedperlevel'],
                'attack_range': stats['attackrange'],
                'hp_regen': stats['hpregen'],
                'hp_regen_per_level': stats['hpregenperlevel'],
                'mp_regen': stats['mpregen'],
                'mp_regen_per_level': stats['mpregenperlevel'],
                'crit': stats['crit'],
                'crit_per_level': stats['critperlevel']
            },
            'tags': champion_data.get('tags', []),
            'partype': champion_data.get('partype', 'Mana')
        }
    
    def process_champion_abilities(self, champion_data: Dict) -> Dict:
        """
        Extract ability information including damage, cooldowns, ranges.
        
        Args:
            champion_data: Raw champion data from Data Dragon
            
        Returns:
            Abilities dictionary
        """
        abilities = {}
        
        # Passive
        passive = champion_data['passive']
        abilities['Passive'] = {
            'name': passive['name'],
            'description': passive['description'],
            'image': passive['image']['full']
        }
        
        # Q, W, E, R
        spell_keys = ['Q', 'W', 'E', 'R']
        for i, spell in enumerate(champion_data['spells']):
            key = spell_keys[i]
            abilities[key] = {
                'name': spell['name'],
                'description': spell['description'],
                'cooldown': spell['cooldown'],
                'cost': spell['cost'],
                'range': spell['range'],
                'image': spell['image']['full'],
                # Many of these can be None or empty lists
                'max_rank': spell.get('maxrank', 5),
                'effect_burn': spell.get('effectBurn', []),
                'vars': spell.get('vars', []),  # Scaling coefficients
                'resource': spell.get('resource', '')
            }
        
        return abilities
    
    def fetch_all_champions(self, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Fetch data for all champions and save to disk.
        
        Args:
            force_refresh: If True, re-fetch even if data exists
            
        Returns:
            Dictionary mapping champion_id -> champion_data
        """
        output_file = self.output_dir / "data_dragon_champions.json"
        
        # Check if we already have the data
        if output_file.exists() and not force_refresh:
            print(f"Loading existing data from {output_file}")
            with open(output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Get champion list
        if not self.champion_list:
            self.get_champion_list()
        
        all_champions = {}
        print(f"Fetching data for {len(self.champion_list)} champions...")
        
        for i, champion_id in enumerate(self.champion_list, 1):
            try:
                print(f"[{i}/{len(self.champion_list)}] Fetching {champion_id}...", end=' ')
                raw_data = self.fetch_champion_data(champion_id)
                
                # Process data
                processed_data = {
                    'stats': self.process_champion_stats(raw_data),
                    'abilities': self.process_champion_abilities(raw_data)
                }
                
                all_champions[champion_id] = processed_data
                print("✓")
                
            except Exception as e:
                print(f"✗ Error: {e}")
                continue
        
        # Save to disk
        metadata = {
            'version': self.version,
            'fetch_date': datetime.now().isoformat(),
            'champion_count': len(all_champions)
        }
        
        output_data = {
            'metadata': metadata,
            'champions': all_champions
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved {len(all_champions)} champions to {output_file}")
        return all_champions
    
    def get_champion_image_url(self, champion_id: str, image_type: str = "splash") -> str:
        """
        Get URL for champion image.
        
        Args:
            champion_id: Champion ID
            image_type: 'splash', 'loading', or 'square'
            
        Returns:
            Image URL
        """
        if not self.version:
            self.get_latest_version()
        
        if image_type == "splash":
            return f"{self.BASE_URL}/cdn/img/champion/splash/{champion_id}_0.jpg"
        elif image_type == "loading":
            return f"{self.BASE_URL}/cdn/img/champion/loading/{champion_id}_0.jpg"
        elif image_type == "square":
            return f"{self.BASE_URL}/cdn/{self.version}/img/champion/{champion_id}.png"
        else:
            raise ValueError(f"Unknown image_type: {image_type}")


def main():
    """Main execution function."""
    print("=" * 60)
    print("Data Dragon Fetcher - League of Legends Champion Data")
    print("=" * 60)
    
    fetcher = DataDragonFetcher()
    
    # Fetch all champion data
    champions = fetcher.fetch_all_champions(force_refresh=True)
    
    print("\n" + "=" * 60)
    print("Fetch complete!")
    print(f"Version: {fetcher.version}")
    print(f"Champions: {len(champions)}")
    print(f"Output: data/raw/data_dragon_champions.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
