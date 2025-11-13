"""
Scrape all 171 champions from League Wiki.
This will take ~3 hours with 1 second rate limiting.
"""

import json
from pathlib import Path
from scrape_wiki import WikiScraper

def main():
    # Load champion list
    archetype_file = Path('data/processed/champion_archetypes.json')
    with open(archetype_file, encoding='utf-8') as f:
        data = json.load(f)
    
    champion_names = sorted(data['assignments'].keys())
    print(f"Found {len(champion_names)} champions")
    print(f"Estimated time: ~{len(champion_names)} seconds (~{len(champion_names)/60:.1f} minutes)")
    
    # Create scraper
    scraper = WikiScraper()
    
    # Output file
    output_file = Path('data/processed/wiki_champion_data.json')
    
    # Scrape all champions
    scraper.scrape_all_champions(champion_names, str(output_file))
    
    print("\nDone! Wiki scraping complete.")
    print(f"Saved to: {output_file}")

if __name__ == '__main__':
    main()
