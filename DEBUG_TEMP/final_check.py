import json

with open('data/processed/champion_archetypes.json') as f:
    data = json.load(f)

zed = data['assignments']['Zed']
ahri = data['assignments']['Ahri']
leona = data['assignments']['Leona']
malphite = data['assignments']['Malphite']

print("Champion Classifications:")
print(f"  Zed      : {zed['primary_archetype']}")
print(f"  Ahri     : {ahri['primary_archetype']}")
print(f"  Leona    : {leona['primary_archetype']}")
print(f"  Malphite : {malphite['primary_archetype']}")

# Check raw CC scores
with open('data/processed/computed_attributes.json') as f:
    attrs = json.load(f)['champions']

print("\nRaw CC Scores:")
print(f"  Zed      : {attrs['Zed']['cc_score']:.4f}")
print(f"  Ahri     : {attrs['Ahri']['cc_score']:.4f}")
print(f"  Leona    : {attrs['Leona']['cc_score']:.4f}")
print(f"  Malphite : {attrs['Malphite']['cc_score']:.4f}")
