"""
Patch spell attributes to fix Braum false positive using wiki data.
Keeps existing attributes but corrects known bad data.
"""

import json

def main():
    print("="*60)
    print("Patching Spell Attributes (Braum Fix)")
    print("="*60)
    
    # Load existing attributes
    with open('data/processed/spell_based_attributes.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    attributes = data['attributes']
    
    # Load wiki spell database for reference
    with open('data/processed/spell_database_wiki.json', 'r', encoding='utf-8') as f:
        wiki_spells = json.load(f)
    
    # Get Braum's wiki data
    braum_spells = {k: v for k, v in wiki_spells.items() if k.startswith('Braum_')}
    braum_total_ad = sum(s.get('ad_ratio', 0) + s.get('bonus_ad_ratio', 0) 
                         for s in braum_spells.values())
    
    print(f"\nBraum fix:")
    print(f"  Old total_ad_ratio: {attributes['Braum']['total_ad_ratio']}")
    print(f"  Wiki total_ad_ratio: {braum_total_ad}")
    
    # Apply fix: Update Braum's total_ad_ratio to 0.0
    if 'Braum' in attributes:
        attributes['Braum']['total_ad_ratio'] = 0.0
        
        # Recalculate sustained_dps without the bad AD scaling
        # Braum's DPS comes from autos only (no AD ratios on spells)
        aa_damage = 130.0  # Mid-game AD
        attack_speed = 0.65
        aa_sustained_count = attack_speed * 10.0 * 0.6
        aa_sustained_damage = aa_sustained_count * aa_damage
        
        attributes['Braum']['sustained_damage'] = round(aa_sustained_damage, 2)
        attributes['Braum']['sustained_dps'] = round(aa_sustained_damage / 10.0, 2)
        
        print(f"  New total_ad_ratio: {attributes['Braum']['total_ad_ratio']}")
        print(f"  New sustained_dps: {attributes['Braum']['sustained_dps']}")
    
    # Update metadata
    data['metadata']['note'] += " | Braum patched with wiki data (0.0 AD ratio, not 4.0)"
    
    # Save patched version
    with open('data/processed/spell_based_attributes_patched.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Saved patched attributes to: data/processed/spell_based_attributes_patched.json")
    print(f"✓ Total champions: {len(attributes)}")


if __name__ == '__main__':
    main()
