"""
Scrape the 4 missing champions and merge into wiki_champion_data.json
"""

import json
from pathlib import Path
from scrape_wiki import WikiScraper
import time

def main():
    # Missing champions
    missing_champions = ['Leblanc', 'MissFortune', 'Viego', 'Yunara']
    
    print(f"Scraping {len(missing_champions)} missing champions...")
    
    # Create scraper
    scraper = WikiScraper()
    
    # Load existing data
    data_file = Path('data/processed/wiki_champion_data.json')
    with open(data_file, encoding='utf-8') as f:
        existing_data = json.load(f)
    
    print(f"Loaded {len(existing_data)} existing champions")
    
    # Scrape missing champions
    for i, champion in enumerate(missing_champions, 1):
        print(f"\n[{i}/{len(missing_champions)}] Scraping {champion}...")
        
        # Try up to 3 times
        for attempt in range(3):
            try:
                result = scraper.scrape_champion(champion)
                if result:
                    existing_data[champion] = result
                    print(f"  ✓ Success!")
                    break
                else:
                    print(f"  ✗ Failed to fetch")
                    break
            except Exception as e:
                if attempt < 2:
                    print(f"  Attempt {attempt + 1} failed: {e}, retrying in 2s...")
                    time.sleep(2)
                else:
                    print(f"  ✗ All attempts failed: {e}")
        
        time.sleep(1)
    
    # Save updated data
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Updated data saved to {data_file}")
    print(f"Total champions: {len(existing_data)}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
