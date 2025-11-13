""""""

Archetype Assignment using Fuzzy ScoringArchetype Assignment Algorithm



Assigns champions to archetypes based on spell-derived attributes usingImplements fuzzy membership calculation to assign strategic archetypes to champions

fuzzy membership scoring (0-1 range) with trapezoidal functions.based on their computed attributes. Uses trapezoidal membership functions for

"""smooth transitions between archetypes.



import jsonMathematical approach:

from pathlib import Path- Each champion can belong to multiple archetypes with different membership scores

from typing import Dict, Tuple- Membership score in [0, 1] where:

  - 1.0 = perfect match (all attributes in optimal range)

  - 0.6-1.0 = strong archetype membership

def fuzzy_score(value: float, requirement: Dict) -> float:  - 0.4-0.6 = moderate membership

    """  - 0-0.4 = weak/no membership

    Calculate fuzzy membership score for a value against a requirement."""

    

    Uses trapezoidal membership function:import json

    - Below min_threshold: 0.0from pathlib import Path

    - Between min and (min + fuzzy_range): linear 0.0 → 1.0from typing import Dict, List, Tuple, Any

    - Between (min + fuzzy_range) and (max - fuzzy_range): 1.0

    - Between (max - fuzzy_range) and max: linear 1.0 → 0.0

    - Above max: 0.0class ArchetypeAssigner:

        def __init__(self, attributes_file: Path, definitions_file: Path):

    Args:        """

        value: Attribute value to score

        requirement: Dict with 'min_threshold', 'max_threshold', 'fuzzy_range'        Initialize archetype assigner."""

    

    Returns:        

        Membership score in [0.0, 1.0]

    """        Args:import json

    min_thresh = requirement.get('min_threshold', float('-inf'))

    max_thresh = requirement.get('max_threshold', float('inf'))            attributes_file: Path to spell_based_attributes.jsonimport numpy as np

    fuzzy_range = requirement.get('fuzzy_range', 0.0)

                definitions_file: Path to archetype_definitions.jsonfrom pathlib import Path

    # Below minimum

    if value < min_thresh:        """from typing import Dict, List, Tuple, Optional

        if fuzzy_range > 0 and value >= min_thresh - fuzzy_range:

            # Fuzzy lower boundary        # Load champion attributesfrom dataclasses import dataclass, asdict

            return (value - (min_thresh - fuzzy_range)) / fuzzy_range

        return 0.0        with open(attributes_file, 'r', encoding='utf-8') as f:

    

    # Above maximum            data = json.load(f)

    if value > max_thresh:

        if fuzzy_range > 0 and value <= max_thresh + fuzzy_range:            self.champion_attrs = data['attributes']@dataclass

            # Fuzzy upper boundary

            return (max_thresh + fuzzy_range - value) / fuzzy_range        class ArchetypeMatch:

        return 0.0

            # Load archetype definitions    """Represents a champion's membership in an archetype."""

    # Within range

    return 1.0        with open(definitions_file, 'r', encoding='utf-8') as f:    champion_id: str



            defs = json.load(f)    archetype_name: str

def score_archetype(champion_attrs: Dict, archetype_def: Dict) -> Tuple[float, Dict[str, float]]:

    """            self.archetypes = defs['archetypes']    membership_score: float

    Score a champion's fit to an archetype.

                self.scoring_rules = defs.get('scoring_rules', {})    attribute_scores: Dict[str, float]

    Returns:

        (overall_score, attribute_scores)        strategic_role: str

    """

    requirements = archetype_def.get('requirements', {})    def fuzzy_score(self, value: float, requirement: Dict[str, float]) -> float:

    weights = archetype_def.get('weights', {})

            """

    attribute_scores = {}

    weighted_sum = 0.0        Compute fuzzy score [0, 1] for a single requirement.class ArchetypeAssigner:

    total_weight = 0.0

                """Assigns strategic archetypes to champions using fuzzy logic."""

    for attr_name, requirement in requirements.items():

        value = champion_attrs.get(attr_name, 0.0)        Args:    

        score = fuzzy_score(value, requirement)

        weight = weights.get(attr_name, 1.0)            value: Champion's attribute value    PENALTY_FACTOR = 2.0  # How quickly score decays outside optimal range

        

        attribute_scores[attr_name] = score            requirement: Dict with min/max/equals and fuzzy_range    STRONG_THRESHOLD = 0.6

        weighted_sum += score * weight

        total_weight += weight            MODERATE_THRESHOLD = 0.4

    

    overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0        Returns:    

    return overall_score, attribute_scores

            Score from 0 (doesn't meet) to 1 (fully meets)    def __init__(



def assign_archetypes(attributes_file: str, definitions_file: str, output_file: str):        """        self,

    """Assign archetypes to all champions."""

            fuzzy_range = requirement.get('fuzzy_range', 0.0)        attributes_path: str = "data/processed/enhanced_attributes.json",

    # Load data

    with open(attributes_file, 'r', encoding='utf-8') as f:                archetypes_path: str = "config/archetypes_v2.json"

        attrs_data = json.load(f)

        champion_attrs = attrs_data['attributes']        # Handle equals (for categorical attributes like damage_profile)    ):

    

    with open(definitions_file, 'r', encoding='utf-8') as f:        if 'equals' in requirement:        """

        defs_data = json.load(f)

        archetypes = defs_data['archetypes']            return 1.0 if value == requirement['equals'] else 0.0        Initialize the archetype assigner.

    

    # Score each champion against each archetype                

    results = {}

    archetype_counts = {name: 0 for name in archetypes.keys()}        # Handle min threshold        Args:

    

    print("=" * 70)        if 'min' in requirement and 'max' not in requirement:            attributes_path: Path to computed champion attributes

    print("Assigning Archetypes")

    print("=" * 70)            min_val = requirement['min']            archetypes_path: Path to archetype definitions

    

    for champ_name, champ_attrs in champion_attrs.items():            if value >= min_val:        """

        scores = {}

                        return 1.0        # Load computed attributes

        for archetype_name, archetype_def in archetypes.items():

            overall_score, attr_scores = score_archetype(champ_attrs, archetype_def)            elif value <= min_val - fuzzy_range:        with open(attributes_path, 'r', encoding='utf-8') as f:

            scores[archetype_name] = {

                'score': overall_score,                return 0.0            attr_data = json.load(f)

                'attribute_scores': attr_scores

            }            else:        # Enhanced attributes JSON is flat, old format had 'champions' wrapper

        

        # Assign primary archetype (highest score)                # Linear interpolation in fuzzy zone        if 'champions' in attr_data:

        primary_archetype = max(scores.items(), key=lambda x: x[1]['score'])

        primary_name = primary_archetype[0]                return (value - (min_val - fuzzy_range)) / fuzzy_range            self.champion_attributes = attr_data['champions']

        primary_score = primary_archetype[1]['score']

                        else:

        # Find secondary archetypes (score > 0.7)

        secondary = [        # Handle max threshold            self.champion_attributes = attr_data

            name for name, data in scores.items()

            if data['score'] > 0.7 and name != primary_name        if 'max' in requirement and 'min' not in requirement:        

        ]

                    max_val = requirement['max']        # Load archetype definitions

        results[champ_name] = {

            'primary_archetype': primary_name,            if value <= max_val:        with open(archetypes_path, 'r', encoding='utf-8') as f:

            'primary_score': primary_score,

            'secondary_archetypes': secondary,                return 1.0            arch_data = json.load(f)

            'all_scores': {name: data['score'] for name, data in scores.items()},

            'attributes': champ_attrs            elif value >= max_val + fuzzy_range:        self.archetypes = arch_data['archetypes']

        }

                        return 0.0        

        archetype_counts[primary_name] += 1

                else:        print(f"Loaded {len(self.champion_attributes)} champions")

    # Save results

    output_data = {                # Linear interpolation in fuzzy zone        print(f"Loaded {len(self.archetypes)} archetypes")

        'metadata': {

            'total_champions': len(results),                return 1.0 - (value - max_val) / fuzzy_range    

            'archetypes': list(archetypes.keys())

        },            def _trapezoidal_membership(

        'distribution': archetype_counts,

        'assignments': results        # Handle min AND max (range requirement)        self, 

    }

            if 'min' in requirement and 'max' in requirement:        value: float, 

    with open(output_file, 'w', encoding='utf-8') as f:

        json.dump(output_data, f, indent=2)            min_val = requirement['min']        optimal_range: List[float]

    

    # Print summary            max_val = requirement['max']    ) -> float:

    print(f"\nAssigned {len(results)} champions")

    print("\nArchetype Distribution:")                    """

    for archetype, count in sorted(archetype_counts.items(), key=lambda x: -x[1]):

        pct = 100.0 * count / len(results)            # Check if in range        Calculate membership score using trapezoidal function.

        print(f"  {archetype:20s}: {count:3d} ({pct:5.1f}%)")

                if min_val <= value <= max_val:        

    print(f"\nSaved to: {output_file}")

                return 1.0        Returns 1.0 if value is within optimal_range,



if __name__ == '__main__':                    gradually decreases to 0 as value moves away from range.

    assign_archetypes(

        attributes_file='data/processed/spell_based_attributes.json',            # Below range        

        definitions_file='data/processed/archetype_definitions.json',

        output_file='data/processed/archetype_assignments.json'            elif value < min_val:        if value <= min_val - fuzzy_range:

    )

                    return 0.0            return (value - (min_val - fuzzy_range)) / fuzzy_range

                else:            

                    return (value - (min_val - fuzzy_range)) / fuzzy_range        Returns:

                        Membership score ∈ [0, 1]

            # Above range        """

            else:  # value > max_val        min_val, max_val = optimal_range

                if value >= max_val + fuzzy_range:        

                    return 0.0        # Perfect membership if in range

                else:        if min_val <= value <= max_val:

                    return 1.0 - (value - max_val) / fuzzy_range            return 1.0

                

        return 0.0        # Calculate distance outside range

            if value < min_val:

    def score_archetype(self, champion_name: str, archetype_name: str) -> Tuple[float, Dict[str, float]]:            distance = min_val - value

        """        else:

        Calculate overall score for a champion matching an archetype.            distance = value - max_val

                

        Args:        # Exponential falloff

            champion_name: Champion to score        score = max(0.0, 1.0 - (distance * self.PENALTY_FACTOR))

            archetype_name: Archetype to score against        

                return score

        Returns:    

            (overall_score, requirement_scores_dict)    def _score_numeric_attribute(

        """        self,

        champion = self.champion_attrs[champion_name]        champion_value: float,

        archetype = self.archetypes[archetype_name]        archetype_range: List[float]

            ) -> float:

        requirements = archetype.get('requirements', {})        """

                Score a single numeric attribute.

        # Fallback archetype (specialist) - always scores 0.1 as baseline        

        if requirements.get('fallback', False):        Args:

            return 0.1, {}            champion_value: Champion's value for this attribute

                    archetype_range: Optimal [min, max] range for archetype

        # Calculate weighted score            

        total_weight = 0.0        Returns:

        weighted_sum = 0.0            Score ∈ [0, 1]

        req_scores = {}        """

                return self._trapezoidal_membership(champion_value, archetype_range)

        for attr_name, requirement in requirements.items():    

            # Skip non-attribute requirements    def _score_categorical_attribute(

            if attr_name in ['fallback']:        self,

                continue        champion_value: str,

                    archetype_values: List[str]

            # Get champion's attribute value    ) -> float:

            attr_value = champion.get(attr_name)        """

            if attr_value is None:        Score a categorical attribute (e.g., damage_pattern).

                # Missing attribute - treat as fail (0 score)        

                req_scores[attr_name] = 0.0        Args:

                continue            champion_value: Champion's category value

                        archetype_values: List of acceptable values for archetype

            # Calculate fuzzy score for this requirement            

            score = self.fuzzy_score(attr_value, requirement)        Returns:

            weight = requirement.get('weight', 1.0)            1.0 if match, 0.0 if no match

                    """

            req_scores[attr_name] = score        return 1.0 if champion_value in archetype_values else 0.0

            weighted_sum += score * weight    

            total_weight += weight    def _score_range_constraint(

                self,

        # Overall score is weighted average        champion_range: int,

        if total_weight > 0:        constraint_range: List[int]

            overall_score = weighted_sum / total_weight    ) -> float:

        else:        """

            overall_score = 0.0        Score a range constraint (e.g., auto_attack range).

                

        return overall_score, req_scores        Args:

                champion_range: Champion's range value

    def assign_archetypes(self, champion_name: str, min_score: float = 0.3,             constraint_range: [min, max] acceptable range

                          secondary_threshold: float = 0.7) -> Dict[str, Any]:            

        """        Returns:

        Assign primary and secondary archetypes to a champion.            Score ∈ [0, 1]

                """

        Args:        min_range, max_range = constraint_range

            champion_name: Champion to classify        

            min_score: Minimum score to consider an archetype (default 0.3)        if min_range <= champion_range <= max_range:

            secondary_threshold: Fraction of primary score for secondary archetypes            return 1.0

                

        Returns:        # Distance-based penalty

            Dict with primary_archetype, secondary_archetypes, all_scores        if champion_range < min_range:

        """            distance = min_range - champion_range

        # Calculate scores for all archetypes        all_scores = {}            distance = champion_range - max_range

        all_details = {}        

                # Normalize distance (assume max meaningful distance is 500)

        for archetype_name in self.archetypes.keys():        normalized_distance = distance / 500.0

            score, req_scores = self.score_archetype(champion_name, archetype_name)        score = max(0.0, 1.0 - (normalized_distance * self.PENALTY_FACTOR))

            all_scores[archetype_name] = round(score, 3)        

            all_details[archetype_name] = req_scores        return score

            

        # Find primary archetype (highest score)    def calculate_archetype_membership(

        sorted_archetypes = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)        self,

                champion_id: str,

        primary_archetype = None        archetype_name: str

        primary_score = 0.0        archetype_def: Dict

            ) -> ArchetypeMatch:

        for archetype, score in sorted_archetypes:        """

            # Skip specialist unless it's the only option        Calculate champion's membership in a specific archetype.

            if archetype == 'specialist' and score < max(all_scores.values()):        

                continue        Args:

                        champion_id: Champion identifier

            if score >= min_score:            archetype_name: Name of archetype to check

                primary_archetype = archetype            archetype_def: Archetype definition dictionary

                primary_score = score            

                break        Returns:

                    ArchetypeMatch object with membership score and breakdown

        # Fallback to specialist if no archetype meets min_score        """

        if primary_archetype is None:        champion_attrs = self.champion_attributes[champion_id]

            primary_archetype = 'specialist'        primary_attrs = archetype_def.get('primary_attributes', {})

            primary_score = all_scores['specialist']        

                attribute_scores = {}

        # Find secondary archetypes (score >= threshold * primary_score)        total_score = 0.0

        secondary_archetypes = []        secondary_threshold_score = primary_score * secondary_threshold        

                # Score each primary attribute

        for archetype, score in sorted_archetypes:        for attr_name, attr_range in primary_attrs.items():

            if archetype == primary_archetype:            # All attributes are now numeric (burst_pattern, sustained_pattern, damage_early, etc.)

                continue            champion_value = champion_attrs.get(attr_name, 0.5)

            if archetype == 'specialist':            score = self._score_numeric_attribute(champion_value, attr_range)

                continue            

            if score >= secondary_threshold_score:            attribute_scores[attr_name] = score

                secondary_archetypes.append({            total_score += score

                    'archetype': archetype,            attribute_count += 1

                    'score': score        

                })        # Check range constraints if present

                range_constraints = archetype_def.get('range_constraints', {})

        return {        for range_type, range_bounds in range_constraints.items():

            'champion': champion_name,            # Access range from range_profile dict structure

            'primary_archetype': primary_archetype,            range_profile = champion_attrs.get('range_profile', {})

            'primary_score': round(primary_score, 3),            champion_range = range_profile.get(range_type, 0)

            'secondary_archetypes': secondary_archetypes,            score = self._score_range_constraint(champion_range, range_bounds)

            'all_scores': all_scores,            

            'requirement_details': all_details.get(primary_archetype, {})            attribute_scores[f'range_{range_type}'] = score

        }            total_score += score

                attribute_count += 1

    def assign_all(self, output_file: Path):        

        """        # Check exclusions (negative constraints)

        Assign archetypes to all champions and save results.        exclusions = archetype_def.get('exclusions', {})

                for excl_type, excl_bounds in exclusions.items():

        Args:            if excl_type == 'auto_attack_range':

            output_file: Path to save archetype assignments                # Access range from range_profile dict structure

        """                range_profile = champion_attrs.get('range_profile', {})

        results = []                champion_range = range_profile.get('auto_attack', 0)

        archetype_counts = {}                # Reverse logic: if champion is IN the exclusion range, penalize

                        if excl_bounds[0] <= champion_range <= excl_bounds[1]:

        print("=" * 70)                    # Apply penalty

        print("Assigning archetypes to all champions...")                    attribute_scores[f'exclusion_{excl_type}'] = 0.0

        print("=" * 70)                    total_score += 0.0

                            attribute_count += 1

        for champion_name in sorted(self.champion_attrs.keys()):                else:

            assignment = self.assign_archetypes(champion_name)                    # Not in exclusion range, perfect score

            results.append(assignment)                    attribute_scores[f'exclusion_{excl_type}'] = 1.0

                                total_score += 1.0

            # Count primary archetypes                    attribute_count += 1

            primary = assignment['primary_archetype']        

            archetype_counts[primary] = archetype_counts.get(primary, 0) + 1        # Calculate average membership score

                membership_score = total_score / attribute_count if attribute_count > 0 else 0.0

        # Save full results        

        output_data = {        # Apply archetype weight (boost specific archetypes)

            'metadata': {        weight = archetype_def.get('weight', 1.0)

                'source': 'spell_based_attributes.json + archetype_definitions.json',        weighted_score = min(1.0, membership_score * weight)

                'total_champions': len(results),        

                'archetype_counts': archetype_counts        return ArchetypeMatch(

            },            champion_id=champion_id,

            'assignments': results            archetype_name=archetype_name,

        }            membership_score=weighted_score,

                    attribute_scores=attribute_scores,

        with open(output_file, 'w', encoding='utf-8') as f:            strategic_role=archetype_def.get('strategic_role', 'unknown')

            json.dump(output_data, f, indent=2)        )

            

        print(f"\nAssignments saved to: {output_file}")    def assign_archetypes_to_champion(

        print("\n" + "=" * 70)        self,

        print("ARCHETYPE DISTRIBUTION")        champion_id: str,

        print("=" * 70)        min_threshold: float = 0.4

            ) -> List[ArchetypeMatch]:

        for archetype, count in sorted(archetype_counts.items(), key=lambda x: x[1], reverse=True):        """

            pct = 100 * count / len(results)        Assign all relevant archetypes to a champion.

            print(f"  {archetype:20s}: {count:3d} ({pct:5.1f}%)")        

                Args:

        # Show some examples            champion_id: Champion identifier

        print("\n" + "=" * 70)            min_threshold: Minimum membership score to include

        print("EXAMPLE ASSIGNMENTS")            

        print("=" * 70)        Returns:

                    List of ArchetypeMatch objects, sorted by membership score

        example_champions = ['Zed', 'Ahri', 'Leona', 'Jinx', 'Yasuo', 'Lux']        """

        for champ in example_champions:        matches = []

            if champ in self.champion_attrs:        

                assignment = next(r for r in results if r['champion'] == champ)        for archetype_name, archetype_def in self.archetypes.items():

                primary = assignment['primary_archetype']            match = self.calculate_archetype_membership(

                score = assignment['primary_score']                champion_id,

                secondaries = ', '.join([s['archetype'] for s in assignment['secondary_archetypes']])                archetype_name,

                if secondaries:                archetype_def

                    print(f"  {champ:12s}: {primary:20s} (score: {score:.2f}) [also: {secondaries}]")            )

                else:            

                    print(f"  {champ:12s}: {primary:20s} (score: {score:.2f})")            # Only include matches above threshold

            if match.membership_score >= min_threshold:

                matches.append(match)

def main():        

    """Main execution."""        # Sort by membership score (descending)

    data_dir = Path(__file__).parent.parent / 'data' / 'processed'        matches.sort(key=lambda m: m.membership_score, reverse=True)

    pipeline_dir = Path(__file__).parent        

            return matches

    attributes_file = data_dir / 'spell_based_attributes.json'    

    definitions_file = pipeline_dir / 'archetype_definitions.json'    def assign_all_champions(

    output_file = data_dir / 'archetype_assignments.json'        self,

            output_path: str = "data/processed/champion_archetypes.json",

    assigner = ArchetypeAssigner(attributes_file, definitions_file)        min_threshold: float = 0.4

    assigner.assign_all(output_file)    ) -> Dict:

        """

        Assign archetypes to all champions and save results.

if __name__ == '__main__':        

    main()        Args:

            output_path: Path to save output
            min_threshold: Minimum membership score to include
            
        Returns:
            Dictionary of all assignments
        """
        print(f"\nAssigning archetypes to {len(self.champion_attributes)} champions...")
        print(f"Minimum threshold: {min_threshold}")
        
        all_assignments = {}
        
        for champion_id in self.champion_attributes:
            print(f"Analyzing {champion_id}...", end=' ')
            
            matches = self.assign_archetypes_to_champion(champion_id, min_threshold)
            
            # Convert to serializable format
            all_assignments[champion_id] = {
                'primary_archetype': matches[0].archetype_name if matches else 'unclassified',
                'primary_score': matches[0].membership_score if matches else 0.0,
                'all_archetypes': [
                    {
                        'name': m.archetype_name,
                        'score': m.membership_score,
                        'role': m.strategic_role,
                        'strength': self._classify_strength(m.membership_score)
                    }
                    for m in matches
                ]
            }
            
            print(f"OK ({len(matches)} archetypes)")
        
        # Save to disk
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        result = {
            'metadata': {
                'champion_count': len(all_assignments),
                'archetype_count': len(self.archetypes),
                'min_threshold': min_threshold,
                'strong_threshold': self.STRONG_THRESHOLD,
                'moderate_threshold': self.MODERATE_THRESHOLD
            },
            'assignments': all_assignments
        }
        
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved archetype assignments to {output}")
        
        # Print summary statistics
        self._print_summary(all_assignments)
        
        return all_assignments
    
    def _classify_strength(self, score: float) -> str:
        """Classify membership strength."""
        if score >= self.STRONG_THRESHOLD:
            return 'strong'
        elif score >= self.MODERATE_THRESHOLD:
            return 'moderate'
        else:
            return 'weak'
    
    def _print_summary(self, assignments: Dict):
        """Print summary statistics of archetype assignments."""
        print("\n" + "=" * 70)
        print("Archetype Assignment Summary")
        print("=" * 70)
        
        # Count primary archetypes
        from collections import Counter
        primary_archetypes = [a['primary_archetype'] for a in assignments.values()]
        archetype_counts = Counter(primary_archetypes)
        
        print(f"\nPrimary Archetype Distribution:")
        for archetype, count in archetype_counts.most_common():
            print(f"  {archetype:25s}: {count:3d} champions")
        
        # Average membership scores
        avg_scores = {}
        for archetype_name in self.archetypes:
            scores = [
                m['score']
                for a in assignments.values()
                for m in a['all_archetypes']
                if m['name'] == archetype_name
            ]
            if scores:
                avg_scores[archetype_name] = np.mean(scores)
        
        print(f"\nAverage Membership Scores (when > {self.MODERATE_THRESHOLD}):")
        for archetype, avg_score in sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {archetype:25s}: {avg_score:.3f}")


def main():
    """Main execution function."""
    print("=" * 70)
    print("Archetype Assignment Algorithm")
    print("=" * 70)
    
    assigner = ArchetypeAssigner()
    assigner.assign_all_champions()
    
    print("\n" + "=" * 70)
    print("Assignment complete!")
    print("Output: data/processed/champion_archetypes.json")
    print("=" * 70)


if __name__ == "__main__":
    main()
