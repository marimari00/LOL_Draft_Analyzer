"""Quick check of Braum and marksmen in final classification."""

import json

with open('data/processed/champion_archetypes.json') as f:
    data = json.load(f)

print("="*70)
print("BRAUM FINAL STATUS")
print("="*70)

braum = data['assignments']['Braum']
print(f"Primary archetype: {braum['primary_archetype']}")
print(f"Riot roles: {', '.join(braum['riot_roles'])}")
print(f"Sustained DPS: {braum['attributes']['sustained_dps']}")
print(f"Total AD ratio: {braum['attributes']['total_ad_ratio']}")
print(f"Source: {braum['source']}")
print(f"Confidence: {braum['confidence']}")

print("\n" + "="*70)
print("ALL MARKSMEN IN FINAL CLASSIFICATION")
print("="*70)

marksmen = [(name, info) for name, info in data['assignments'].items()
            if info['primary_archetype'] == 'marksman']

print(f"\nTotal: {len(marksmen)} marksmen\n")

for name, info in sorted(marksmen):
    attrs = info['attributes']
    roles = ', '.join(info['riot_roles'])
    print(f"{name:15s} | DPS={attrs['sustained_dps']:6.1f} | AD={attrs['total_ad_ratio']:4.2f} | {roles}")

print("\n" + "="*70)
print("METADATA")
print("="*70)
print(f"Source: {data['metadata']['source']}")
print(f"Total champions: {data['metadata']['total_champions']}")
print(f"Matched with info.json: {data['metadata']['matched_with_info_json']}")
print(f"Unmatched: {data['metadata']['unmatched']}")
