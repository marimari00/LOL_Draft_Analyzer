import json

with open('data/processed/computed_attributes.json') as f:
    data = json.load(f)

attrs = data['champions']

# Find champions
zed = attrs['Zed']
ahri = attrs['Ahri']
leona = attrs['Leona']
malphite = attrs['Malphite']
morgana = attrs['Morgana']

print("CC Scores (normalized 0-1):")
print(f"  Zed      : {zed['cc_score']:.4f}")
print(f"  Ahri     : {ahri['cc_score']:.4f}")
print(f"  Leona    : {leona['cc_score']:.4f}")
print(f"  Malphite : {malphite['cc_score']:.4f}")
print(f"  Morgana  : {morgana['cc_score']:.4f}")

# Find min/max
cc_scores = [c['cc_score'] for c in attrs.values()]
print(f"\nCC Score Range: {min(cc_scores):.4f} to {max(cc_scores):.4f}")

# Find who has min/max
min_champ = min(attrs.items(), key=lambda x: x[1]['cc_score'])
max_champ = max(attrs.items(), key=lambda x: x[1]['cc_score'])
print(f"Min CC: {min_champ[0]} ({min_champ[1]['cc_score']:.4f})")
print(f"Max CC: {max_champ[0]} ({max_champ[1]['cc_score']:.4f})")
