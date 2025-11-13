"""
Scrape detailed ability information from League of Legends Wiki (Fandom).

Simple, robust version with ASCII-safe output for Windows PowerShell.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class WikiScraper:
    """Scrapes champion ability data from League of Legends Fandom wiki."""
    
    BASE_URL = "https://leagueoflegends.fandom.com"
    
    # Champion name mappings (Data Dragon -> Wiki)
    NAME_MAPPINGS = {
        'MonkeyKing': 'Wukong',
        'Nunu': 'Nunu & Willump',
        'AurelionSol': 'Aurelion Sol',
        'ChoGath': "Cho'Gath",
        'DrMundo': 'Dr. Mundo',
        'JarvanIV': 'Jarvan IV',
        'KogMaw': "Kog'Maw",
        'Khazix': "Kha'Zix",
        'KSante': "K'Sante",
        'LeeSin': 'Lee Sin',
        'MasterYi': 'Master Yi',
        'MissFortune': 'Miss Fortune',
        'RekSai': "Rek'Sai",
        'TahmKench': 'Tahm Kench',
        'TwistedFate': 'Twisted Fate',
        'Velkoz': "Vel'Koz",
        'XinZhao': 'Xin Zhao'
    }
    
    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = 'LeagueAnalyzer/1.0 (Educational Project)'
        self.request_delay = 1.0
        
    def get_champion_page(self, champion_name: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse champion wiki page with retry logic."""
        # Apply name mapping
        wiki_name = self.NAME_MAPPINGS.get(champion_name, champion_name)
        formatted_name = wiki_name.replace(' ', '_')
        url = f"{self.BASE_URL}/wiki/{formatted_name}/LoL"
        
        headers = {'User-Agent': self.user_agent}
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"  Retry {attempt}/{max_retries}...", end=' ')
                else:
                    print(f"Fetching {url}...", end=' ')
                
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                print("[OK]")
                
                time.sleep(self.request_delay)
                return BeautifulSoup(response.content, 'lxml')
                
            except requests.exceptions.Timeout:
                print("[TIMEOUT]")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"  Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"  Failed after {max_retries} attempts")
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"[ERROR: {e}]")
                if attempt < max_retries - 1 and '404' not in str(e):
                    time.sleep(2)
                else:
                    return None
        
        return None
    
    def extract_ability_info(self, soup: BeautifulSoup, champion_name: str) -> Dict:
        """Extract ability information from parsed HTML."""
        abilities = {}
        
        # Find ability sections - wiki structure varies
        skill_sections = soup.find_all('div', class_=re.compile('skill|ability'))
        
        if not skill_sections:
            skill_sections = soup.find_all('table', class_='wikitable')
        
        if not skill_sections:
            skill_sections = soup.find_all('div', attrs={'data-skill': True})
        
        for section in skill_sections:
            try:
                # Try to extract ability key (Q, W, E, R, P)
                ability_key = None
                
                # Look for headings with ability keys
                heading = section.find(['h3', 'h4', 'span'], class_=re.compile('mw-headline|skill-name'))
                if heading:
                    text = heading.get_text()
                    # Match "Ability Name" or "Q - Ability Name" or similar
                    key_match = re.search(r'\b([QWERP])\b', text)
                    if key_match:
                        ability_key = key_match.group(1)
                
                if not ability_key:
                    continue
                
                # Extract ability name and description
                ability_name = heading.get_text().strip() if heading else ''
                
                # Find description
                description_elem = section.find('div', class_='description')
                if not description_elem:
                    description_elem = section.find('p')
                
                description = description_elem.get_text().strip() if description_elem else ''
                
                # Extract cooldown, cost, range from tables
                cooldown = None
                cost = None
                ability_range = None
                
                # Look for data rows
                data_rows = section.find_all('tr')
                for row in data_rows:
                    row_text = row.get_text().lower()
                    
                    if 'cooldown' in row_text:
                        cooldown_match = re.search(r'([\d\.]+(?:\s*/\s*[\d\.]+)*)', row.get_text())
                        if cooldown_match:
                            cooldown = cooldown_match.group(1)
                    
                    if 'cost' in row_text or 'mana' in row_text:
                        cost_match = re.search(r'([\d]+(?:\s*/\s*[\d]+)*)', row.get_text())
                        if cost_match:
                            cost = cost_match.group(1)
                    
                    if 'range' in row_text:
                        range_match = re.search(r'([\d]+)', row.get_text())
                        if range_match:
                            ability_range = range_match.group(1)
                
                # Store ability data
                abilities[ability_key] = {
                    'name': ability_name,
                    'description': description[:500],  # Limit description length
                    'cooldown': cooldown,
                    'cost': cost,
                    'range': ability_range
                }
                
            except Exception as e:
                # Skip this ability on error
                continue
        
        return abilities
    
    def scrape_champion(self, champion_name: str) -> Optional[Dict]:
        """Scrape all ability data for a champion."""
        soup = self.get_champion_page(champion_name)
        if not soup:
            return None
        
        abilities = self.extract_ability_info(soup, champion_name)
        
        if not abilities:
            print(f"  Warning: No abilities found for {champion_name}")
            return None
        
        return {
            'champion_id': champion_name,
            'abilities': abilities
        }
    
    def scrape_all_champions(
        self,
        champion_list: List[str],
        force_refresh: bool = False
    ) -> Dict:
        """Scrape abilities for all champions in list."""
        output_file = self.output_dir / "wiki_scraped_abilities.json"
        
        # Check if we already have the data
        if output_file.exists() and not force_refresh:
            print(f"Loading existing wiki data from {output_file}")
            with open(output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        all_data = {}
        failed_champions = []
        
        print(f"Scraping abilities for {len(champion_list)} champions...")
        print("Note: This will take ~3 minutes due to rate limiting.")
        print("Note: Newer champions (Mel, Ambessa, etc.) will likely fail.\n")
        
        for i, champion_name in enumerate(champion_list, 1):
            print(f"[{i}/{len(champion_list)}] {champion_name}:")
            
            try:
                champion_data = self.scrape_champion(champion_name)
                if champion_data:
                    all_data[champion_name] = champion_data
                    ability_count = len(champion_data.get('abilities', {}))
                    print(f"  SUCCESS: Scraped {ability_count} abilities")
                else:
                    print(f"  FAILED: No data retrieved")
                    failed_champions.append(champion_name)
                
            except Exception as e:
                print(f"  ERROR: {e}")
                failed_champions.append(champion_name)
                continue
        
        # Save results
        metadata = {
            'scrape_date': datetime.now().isoformat(),
            'champion_count': len(all_data),
            'failed_count': len(failed_champions),
            'failed_champions': failed_champions,
            'source': 'leagueoflegends.fandom.com',
            'note': 'Wiki data may be incomplete for newest champions'
        }
        
        output_data = {
            'metadata': metadata,
            'champions': all_data
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "=" * 60)
        print("Scraping Complete!")
        print("=" * 60)
        print(f"Successfully scraped: {len(all_data)} champions")
        if failed_champions:
            print(f"Failed to scrape: {len(failed_champions)} champions")
            print(f"  Failed: {', '.join(failed_champions[:15])}")
            if len(failed_champions) > 15:
                print(f"  ... and {len(failed_champions) - 15} more")
        print(f"Output: {output_file}")
        print("=" * 60)
        
        return all_data


def main():
    """Main execution."""
    print("=" * 60)
    print("Wiki Scraper - League of Legends Ability Data")
    print("=" * 60)
    print()
    
    # Load champion list from Data Dragon
    data_dragon_file = Path("data/raw/data_dragon_champions.json")
    if not data_dragon_file.exists():
        print(f"ERROR: {data_dragon_file} not found")
        print("Please run fetch_data_dragon.py first.")
        return
    
    with open(data_dragon_file, 'r', encoding='utf-8') as f:
        data_dragon = json.load(f)
    
    champion_list = list(data_dragon['champions'].keys())
    print(f"Loaded {len(champion_list)} champions from Data Dragon.\n")
    
    # Create scraper and run
    scraper = WikiScraper()
    scraper.scrape_all_champions(champion_list)


if __name__ == "__main__":
    main()
