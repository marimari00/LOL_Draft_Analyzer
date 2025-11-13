"""Debug Rengar's CC=4.0 issue."""
import json

# Load computed data
with open('data/processed/computed_attributes.json', 'r') as f:
    computed = json.load(f)

print("Rengar attributes:")
rengar = computed['champions']['Rengar']
for key, value in rengar.items():
    if 'cc' in key.lower() or 'stun' in key.lower() or 'root' in key.lower():
        print(f"  {key}: {value}")

# Check if there's a detailed breakdown
print("\nAll Rengar keys:", list(rengar.keys()))

# Let's also check a normal champion for comparison
print("\nLeona CC (should be ~0.35):", computed['champions']['Leona']['cc_score'])
print("Zed CC (should be ~0.25):", computed['champions']['Zed']['cc_score'])
print("Katarina CC (should be 0):", computed['champions']['Katarina']['cc_score'])
