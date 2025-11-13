"""
Scrape champion ability data from League of Legends Wiki.

Wiki has the most accurate, human-verified damage numbers and ratios.
This will be our single source of truth instead of mixing champion.bin + Data Dragon.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional


class WikiScraper:
    """Scrape champion ability data from League Wiki."""
    
    BASE_URL = "https://leagueoflegends.fandom.com/wiki"
    
    # Special name mappings for champions with unusual formatting
    NAME_OVERRIDES = {
        'AurelionSol': 'Aurelion_Sol',
        'Chogath': "Cho'Gath",
        'DrMundo': 'Dr._Mundo',
        'JarvanIV': 'Jarvan_IV',
        'KaiSa': "Kai'Sa",
        'Khazix': "Kha'Zix",
        'KogMaw': "Kog'Maw",
        'KSante': "K'Sante",
        'Leblanc': 'LeBlanc',
        'LeeSin': 'Lee_Sin',
        'MasterYi': 'Master_Yi',
        'MissFortune': 'Miss_Fortune',
        'MonkeyKing': 'Wukong',
        'Nunu': 'Nunu_&_Willump',
        'RekSai': "Rek'Sai",
        'Renata': 'Renata_Glasc',
        'TahmKench': 'Tahm_Kench',
        'TwistedFate': 'Twisted_Fate',
        'Velkoz': "Vel'Koz",
        'XinZhao': 'Xin_Zhao',
    }
    
    # Champions without /LoL suffix
    NO_LOL_SUFFIX = {'Yunara'}
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_champion_page(self, champion_name: str) -> Optional[BeautifulSoup]:
        """Fetch champion wiki page."""
        # Check if there's a special name override
        if champion_name in self.NAME_OVERRIDES:
            formatted_name = self.NAME_OVERRIDES[champion_name]
            suffix = "" if champion_name in self.NO_LOL_SUFFIX else "/LoL"
            url = f"{self.BASE_URL}/{formatted_name}{suffix}"
            print(f"Fetching {url}")
            
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                print(f"  Failed: {e}")
                return None
        
        # Check if this champion doesn't use /LoL suffix
        if champion_name in self.NO_LOL_SUFFIX:
            url = f"{self.BASE_URL}/{champion_name}"
            print(f"Fetching {url}")
            
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                print(f"  Failed: {e}")
                return None
        
        # Try multiple URL formats for champions with spaces
        # e.g., "Aurelion Sol" -> try "Aurelion_Sol" and "AurelionSol"
        # e.g., "Xin Zhao" -> try "Xin_Zhao" and "XinZhao"
        
        url_variants = []
        
        # Remove apostrophes first
        clean_name = champion_name.replace("'", "")
        
        # Try with underscore
        url_variants.append(clean_name.replace(" ", "_"))
        
        # Try without space (concatenated)
        url_variants.append(clean_name.replace(" ", ""))
        
        for formatted_name in url_variants:
            url = f"{self.BASE_URL}/{formatted_name}/LoL"
            print(f"Fetching {url}")
            
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                print(f"  Failed: {e}")
                continue
        
        print(f"Error: Could not fetch {champion_name} with any URL variant")
        return None
    
    def parse_ability_data(self, soup: BeautifulSoup, champion_name: str) -> Dict:
        """
        Parse ability data from wiki page.
        
        Wiki structure:
        - Each ability in a div with classes 'skill skill_q', 'skill skill_w', etc.
        - Ability name in span with class 'mw-headline'
        - Damage values in dl elements with class 'skill-tabs'
        - Cooldown in portable-infobox with data-source='cooldown'
        """
        abilities = {}
        
        # Find all skill divs (look for class containing 'skill')
        skill_divs = soup.find_all('div', class_=lambda x: x and 'skill' in x)
        
        for skill_div in skill_divs:
            # Get ability key (Q, W, E, R, P) from class names
            ability_key = None
            classes = skill_div.get('class', [])
            for cls in classes:
                if 'skill_q' in cls:
                    ability_key = 'Q'
                elif 'skill_w' in cls:
                    ability_key = 'W'
                elif 'skill_e' in cls:
                    ability_key = 'E'
                elif 'skill_r' in cls:
                    ability_key = 'R'
                elif 'skill_innate' in cls:
                    ability_key = 'P'
                if ability_key:
                    break
            
            if not ability_key:
                continue
            
            # Get ability name from h3 with class mw-headline
            name_tag = skill_div.find('span', class_='mw-headline')
            ability_name = name_tag.get_text(strip=True) if name_tag else "Unknown"
            
            # Initialize ability data
            ability_data = {
                'name': ability_name,
                'base_damage': [],
                'ad_ratio': 0.0,
                'bonus_ad_ratio': 0.0,
                'ap_ratio': 0.0,
                'cooldown': []
            }
            
            # Find the skill_leveling div which contains damage/stat tables
            leveling_divs = skill_div.find_all('div', class_='skill_leveling')
            
            for leveling_div in leveling_divs:
                # Get all dl elements with class skill-tabs
                skill_tabs = leveling_div.find_all('dl', class_='skill-tabs')
                
                for tab in skill_tabs:
                    dt = tab.find('dt')
                    dd = tab.find('dd')
                    
                    if not dt or not dd:
                        continue
                    
                    label = dt.get_text(strip=True).lower()
                    value_text = dd.get_text(strip=True)
                    
                    # Extract base damage (look for any type of damage: magic, physical, true)
                    if 'damage:' in label:
                        # Extract numbers separated by /
                        damage_values = re.findall(r'(\d+(?:\.\d+)?)\s*(?=/|$)', value_text)
                        if damage_values:
                            ability_data['base_damage'] = [float(x) for x in damage_values[:5]]
                        
                        # Extract AP ratio (can be percentage or decimal)
                        # Pattern: "+ 60% AP" or "+ 0.6 AP"
                        ap_match = re.search(r'\+\s*([\d./\s]+)%\s*(?:of\s+)?(?:ability power|AP)', value_text, re.IGNORECASE)
                        if ap_match:
                            ap_text = ap_match.group(1).strip()
                            ap_value = float(ap_text.split('/')[0].strip())
                            # If > 10, it's a percentage, convert to decimal
                            if ap_value > 10:
                                ap_value = ap_value / 100
                            ability_data['ap_ratio'] = ap_value
                        
                        # Extract total AD ratio (can be percentage or decimal)
                        # Pattern: "+ 125% AD" or "+ 1.25 AD" or "+ 125% total AD"
                        # Make sure it's NOT bonus AD
                        ad_match = re.search(r'\+\s*([\d./\s]+)%\s*(?:total\s+)?(?:attack damage|AD)(?!\s*per)', value_text, re.IGNORECASE)
                        if ad_match:
                            # Check if "bonus" appears before this match
                            if 'bonus' not in value_text[:ad_match.start()].lower():
                                ad_text = ad_match.group(1).strip()
                                # If there's a /, take the first value (rank 1)
                                ad_value = float(ad_text.split('/')[0].strip())
                                # If > 10, it's a percentage
                                if ad_value > 10:
                                    ad_value = ad_value / 100
                                ability_data['ad_ratio'] = ad_value
                        
                        # Extract bonus AD ratio
                        bonus_ad_match = re.search(r'\+\s*([\d./\s]+)%\s*bonus\s+(?:attack damage|AD)', value_text, re.IGNORECASE)
                        if bonus_ad_match:
                            bonus_text = bonus_ad_match.group(1).strip()
                            bonus_value = float(bonus_text.split('/')[0].strip())
                            if bonus_value > 10:
                                bonus_value = bonus_value / 100
                            ability_data['bonus_ad_ratio'] = bonus_value
            
            # Get cooldown from portable-infobox
            infobox = skill_div.find('aside', class_='portable-infobox')
            if infobox:
                cooldown_div = infobox.find('div', {'data-source': 'cooldown'})
                if cooldown_div:
                    cooldown_value = cooldown_div.find('div', class_='pi-data-value')
                    if cooldown_value:
                        cooldown_text = cooldown_value.get_text(strip=True)
                        cooldown_values = re.findall(r'(\d+(?:\.\d+)?)', cooldown_text)
                        if cooldown_values:
                            ability_data['cooldown'] = [float(x) for x in cooldown_values[:5]]
            
            abilities[ability_key] = ability_data
        
        return abilities
    
    def scrape_champion(self, champion_name: str) -> Optional[Dict]:
        """Scrape complete ability data for one champion."""
        soup = self.get_champion_page(champion_name)
        if not soup:
            return None
        
        abilities = self.parse_ability_data(soup, champion_name)
        
        return {
            'champion': champion_name,
            'abilities': abilities
        }
    
    def scrape_all_champions(self, champion_list: List[str], output_file: str):
        """Scrape all champions and save to JSON."""
        results = {}
        failed = []
        
        for i, champion in enumerate(champion_list, 1):
            print(f"\n[{i}/{len(champion_list)}] Scraping {champion}...")
            
            # Try up to 3 times for network errors
            for attempt in range(3):
                try:
                    data = self.scrape_champion(champion)
                    if data:
                        results[champion] = data
                        break
                    else:
                        failed.append(champion)
                        break
                except Exception as e:
                    if attempt < 2:
                        print(f"  Attempt {attempt + 1} failed: {e}, retrying...")
                        time.sleep(2)
                    else:
                        print(f"  All attempts failed: {e}")
                        failed.append(champion)
            
            # Rate limiting
            time.sleep(1)
            
            # Save periodically (every 20 champions)
            if i % 20 == 0:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                print(f"  [Checkpoint: Saved {len(results)} champions]")
        
        # Final save
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"Saved {len(results)} champions to {output_path}")
        if failed:
            print(f"Failed to scrape {len(failed)} champions: {failed}")
        print(f"{'='*60}")


def main():
    """Test scraper with a few champions."""
    scraper = WikiScraper()
    
    # Test with regular and space-name champions
    test_champions = ['Braum', 'Xin Zhao', 'Aurelion Sol']
    
    print("Testing Wiki scraper...")
    for champ in test_champions:
        result = scraper.scrape_champion(champ)
        if result:
            print(f"\n{champ} abilities:")
            for key, ability in result['abilities'].items():
                print(f"  {key}: {ability['name']}")
                print(f"     Base damage: {ability['base_damage']}")
                print(f"     AD: {ability['ad_ratio']}, Bonus AD: {ability['bonus_ad_ratio']}, AP: {ability['ap_ratio']}")


if __name__ == '__main__':
    main()
