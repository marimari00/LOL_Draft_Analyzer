"""
Validate marksman classification after Braum fix.
"""

import json

def main():
    with open('data/processed/archetype_assignments.json', 'r') as f:
        data = json.load(f)
    
    assignments = data['assignments']
    
    # Get all marksmen
    marksmen = [(name, info) for name, info in assignments.items() 
                if info['primary_archetype'] == 'marksman']
    
    print("="*70)
    print(f"MARKSMEN CLASSIFICATION ({len(marksmen)} champions)")
    print("="*70)
    
    for name, info in sorted(marksmen):
        attrs = info['attributes']
        score = info['primary_score']
        print(f"{name:15s} - DPS: {attrs['sustained_dps']:6.1f}, "
              f"AD_ratio: {attrs['total_ad_ratio']:4.2f}, Score: {score:.3f}")
    
    # Check Braum
    print("\n" + "="*70)
    print("BRAUM STATUS (Should NOT be marksman)")
    print("="*70)
    
    if 'Braum' in assignments:
        braum = assignments['Braum']
        print(f"Primary archetype: {braum['primary_archetype']}")
        print(f"Sustained DPS: {braum['attributes']['sustained_dps']}")
        print(f"Total AD ratio: {braum['attributes']['total_ad_ratio']}")
        print(f"Archetype score: {braum['primary_score']:.3f}")
        
        if braum['primary_archetype'] == 'marksman':
            print("\n❌ FAILED: Braum still classified as marksman!")
        else:
            print(f"\n✓ SUCCESS: Braum correctly classified as {braum['primary_archetype']}")
    
    # Precision check: known true marksmen
    true_marksmen = [
        'Caitlyn', 'Jinx', 'Ashe', 'Tristana', 'Vayne', 'Ezreal', 
        'Lucian', 'Jhin', 'Miss Fortune', 'Sivir', 'Twitch', 'Kog\'Maw'
    ]
    
    print("\n" + "="*70)
    print("PRECISION CHECK")
    print("="*70)
    
    classified_marksmen = [name for name, _ in marksmen]
    true_positives = [name for name in true_marksmen if name in classified_marksmen]
    false_positives = [name for name in classified_marksmen if name not in true_marksmen]
    false_negatives = [name for name in true_marksmen if name not in classified_marksmen]
    
    precision = len(true_positives) / len(classified_marksmen) if classified_marksmen else 0
    recall = len(true_positives) / len(true_marksmen) if true_marksmen else 0
    
    print(f"True positives: {len(true_positives)} {true_positives}")
    print(f"False positives: {len(false_positives)} {false_positives}")
    print(f"False negatives: {len(false_negatives)} {false_negatives}")
    print(f"\nPrecision: {precision*100:.1f}%")
    print(f"Recall: {recall*100:.1f}%")
    
    if precision >= 0.95:
        print("\n✓ Target precision (95%+) achieved!")
    else:
        print(f"\n⚠️  Precision {precision*100:.1f}% below target 95%")


if __name__ == '__main__':
    main()
