import json
import statistics

d = json.load(open('data/processed/enhanced_attributes.json'))

cc_scores = [c['cc_score'] for c in d.values()]
gold_deps = [c['gold_dependency'] for c in d.values()]

print('CC Score Distribution:')
print(f'  Min: {min(cc_scores):.4f}, Max: {max(cc_scores):.4f}')
print(f'  Mean: {statistics.mean(cc_scores):.4f}, Median: {statistics.median(cc_scores):.4f}')

print('\nGold Dependency Distribution:')
print(f'  Min: {min(gold_deps):.4f}, Max: {max(gold_deps):.4f}')
print(f'  Mean: {statistics.mean(gold_deps):.4f}, Median: {statistics.median(gold_deps):.4f}')

print('\nSample CC scores:')
for name in ['Zed', 'Ahri', 'Malphite', 'Leona', 'Soraka', 'Morgana']:
    print(f'  {name:12s}: {d[name]["cc_score"]:.4f}')

print('\nSample Gold Dependency:')
for name in ['Jinx', 'Caitlyn', 'Vayne', 'Pantheon', 'LeeSin', 'Garen']:
    print(f'  {name:12s}: {d[name]["gold_dependency"]:.4f}')
