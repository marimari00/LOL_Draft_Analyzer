"""Draft simulator with role validation.

Simulates a full draft pick/ban phase with:
- 5 positions: Top, Jungle, Middle, Bottom, Support
- Ban phase (10 bans total)
- Pick phase (10 picks total, alternating)
- Role assignment validation
- Team composition analysis
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from enum import Enum


class DraftPhase(Enum):
    """Draft phase states."""
    BAN_1 = "ban_phase_1"
    PICK_1 = "pick_phase_1"
    BAN_2 = "ban_phase_2"
    PICK_2 = "pick_phase_2"
    BAN_3 = "ban_phase_3"
    PICK_3 = "pick_phase_3"
    COMPLETE = "complete"


class Team(Enum):
    """Team identifiers."""
    BLUE = "blue"
    RED = "red"


POSITIONS = ["Top", "Jungle", "Middle", "Bottom", "Support"]


class DraftState:
    """Represents current draft state."""
    
    def __init__(self):
        self.bans = {Team.BLUE: [], Team.RED: []}
        self.picks = {
            Team.BLUE: {pos: None for pos in POSITIONS},
            Team.RED: {pos: None for pos in POSITIONS}
        }
        self.phase = DraftPhase.BAN_1
        self.current_team = Team.BLUE
        
        # Load champion data
        with open('data/processed/champion_archetypes.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.champions = data['assignments']
    
    def get_available_champions(self) -> List[str]:
        """Get list of champions that haven't been picked or banned."""
        all_bans = self.bans[Team.BLUE] + self.bans[Team.RED]
        all_picks = []
        for team in [Team.BLUE, Team.RED]:
            all_picks.extend([c for c in self.picks[team].values() if c])
        
        unavailable = set(all_bans + all_picks)
        return [c for c in self.champions.keys() if c not in unavailable]
    
    def can_play_position(self, champion: str, position: str) -> bool:
        """Check if champion can play a specific position."""
        if champion not in self.champions:
            return False
        
        viable_positions = self.champions[champion].get('viable_positions', [])
        return position in viable_positions
    
    def get_unfilled_positions(self, team: Team) -> List[str]:
        """Get list of positions that haven't been filled yet."""
        return [pos for pos, champ in self.picks[team].items() if champ is None]
    
    def ban_champion(self, champion: str, team: Team) -> bool:
        """Ban a champion. Returns True if successful."""
        if champion not in self.get_available_champions():
            return False
        
        self.bans[team].append(champion)
        return True
    
    def pick_champion(self, champion: str, position: str, team: Team) -> Tuple[bool, str]:
        """Pick a champion for a position. Returns (success, error_message)."""
        # Check if champion is available
        if champion not in self.get_available_champions():
            return False, f"{champion} is already picked or banned"
        
        # Check if position is valid
        if position not in POSITIONS:
            return False, f"Invalid position: {position}"
        
        # Check if position is already filled
        if self.picks[team][position] is not None:
            return False, f"{position} is already filled by {self.picks[team][position]}"
        
        # Check if champion can play this position
        if not self.can_play_position(champion, position):
            viable = self.champions[champion].get('viable_positions', [])
            return False, f"{champion} cannot play {position} (viable: {', '.join(viable)})"
        
        # Make the pick
        self.picks[team][position] = champion
        return True, ""
    
    def get_team_composition(self, team: Team) -> Dict:
        """Get team composition with archetypes and synergy analysis."""
        team_champs = [c for c in self.picks[team].values() if c]
        
        if not team_champs:
            return {'champions': [], 'archetypes': [], 'synergy_score': 0.0}
        
        archetypes = []
        for champ in team_champs:
            if champ in self.champions:
                archetypes.append(self.champions[champ]['primary_archetype'])
        
        return {
            'champions': team_champs,
            'positions': {pos: champ for pos, champ in self.picks[team].items() if champ},
            'archetypes': archetypes
        }
    
    def is_draft_complete(self) -> bool:
        """Check if draft is complete (all positions filled)."""
        for team in [Team.BLUE, Team.RED]:
            if any(c is None for c in self.picks[team].values()):
                return False
        return True
    
    def display(self):
        """Display current draft state."""
        print("\n" + "="*70)
        print("DRAFT STATE")
        print("="*70)
        
        # Bans
        print("\nBANS:")
        print(f"  Blue: {', '.join(self.bans[Team.BLUE]) if self.bans[Team.BLUE] else 'None'}")
        print(f"  Red:  {', '.join(self.bans[Team.RED]) if self.bans[Team.RED] else 'None'}")
        
        # Picks
        print("\nPICKS:")
        for pos in POSITIONS:
            blue_pick = self.picks[Team.BLUE][pos] or "---"
            red_pick = self.picks[Team.RED][pos] or "---"
            print(f"  {pos:8s}: {blue_pick:15s} | {red_pick:15s}")
        
        # Unfilled positions
        blue_unfilled = self.get_unfilled_positions(Team.BLUE)
        red_unfilled = self.get_unfilled_positions(Team.RED)
        
        if blue_unfilled or red_unfilled:
            print("\nUNFILLED POSITIONS:")
            if blue_unfilled:
                print(f"  Blue: {', '.join(blue_unfilled)}")
            if red_unfilled:
                print(f"  Red:  {', '.join(red_unfilled)}")


def simulate_draft_interactive():
    """Run an interactive draft simulation."""
    draft = DraftState()
    
    print("="*70)
    print("INTERACTIVE DRAFT SIMULATOR")
    print("="*70)
    print("\nCommands:")
    print("  ban <champion> <team>         - Ban a champion (team: blue/red)")
    print("  pick <champion> <position> <team>  - Pick champion for position")
    print("  show                          - Show current draft state")
    print("  available                     - Show available champions")
    print("  done                          - Finish draft")
    print("  help                          - Show this help")
    
    draft.display()
    
    while not draft.is_draft_complete():
        try:
            cmd = input("\n> ").strip().lower().split()
            
            if not cmd:
                continue
            
            if cmd[0] == "ban" and len(cmd) == 3:
                champion = cmd[1].title()
                team = Team.BLUE if cmd[2] == "blue" else Team.RED
                
                if draft.ban_champion(champion, team):
                    print(f"✓ {team.value.title()} banned {champion}")
                    draft.display()
                else:
                    print(f"✗ Cannot ban {champion} (not available)")
            
            elif cmd[0] == "pick" and len(cmd) == 4:
                champion = cmd[1].title()
                position = cmd[2].title()
                team = Team.BLUE if cmd[3] == "blue" else Team.RED
                
                success, error = draft.pick_champion(champion, position, team)
                if success:
                    print(f"✓ {team.value.title()} picked {champion} for {position}")
                    draft.display()
                else:
                    print(f"✗ {error}")
            
            elif cmd[0] == "show":
                draft.display()
            
            elif cmd[0] == "available":
                available = draft.get_available_champions()
                print(f"\nAvailable champions ({len(available)}):")
                for i in range(0, len(available), 8):
                    print("  " + ", ".join(available[i:i+8]))
            
            elif cmd[0] == "done":
                break
            
            elif cmd[0] == "help":
                print("\nCommands:")
                print("  ban <champion> <team>")
                print("  pick <champion> <position> <team>")
                print("  show, available, done, help")
            
            else:
                print("Unknown command. Type 'help' for commands.")
        
        except KeyboardInterrupt:
            print("\n\nDraft cancelled.")
            return
    
    # Final display
    print("\n" + "="*70)
    print("DRAFT COMPLETE!")
    print("="*70)
    draft.display()
    
    # Analyze compositions
    print("\n" + "="*70)
    print("TEAM COMPOSITIONS")
    print("="*70)
    
    for team in [Team.BLUE, Team.RED]:
        comp = draft.get_team_composition(team)
        print(f"\n{team.value.title()} Team:")
        for pos, champ in comp['positions'].items():
            if champ in draft.champions:
                archetype = draft.champions[champ]['primary_archetype']
                print(f"  {pos:8s}: {champ:15s} ({archetype})")
        
        print(f"\nArchetypes: {', '.join(comp['archetypes'])}")


def simulate_draft_example():
    """Run a pre-defined example draft."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from score_team_composition import analyze_team_composition
    
    draft = DraftState()
    
    print("="*70)
    print("EXAMPLE DRAFT SIMULATION")
    print("="*70)
    
    # Example draft sequence
    actions = [
        ("ban", "Zed", Team.BLUE),
        ("ban", "Yasuo", Team.RED),
        ("pick", "Darius", "Top", Team.BLUE),
        ("pick", "Jinx", "Bottom", Team.RED),
        ("pick", "Thresh", "Support", Team.RED),
        ("pick", "LeeSin", "Jungle", Team.BLUE),
        ("pick", "Ahri", "Middle", Team.BLUE),
        ("pick", "Vi", "Jungle", Team.RED),
        ("pick", "Syndra", "Middle", Team.RED),
        ("pick", "Caitlyn", "Bottom", Team.BLUE),
        ("pick", "Leona", "Support", Team.BLUE),
        ("pick", "Garen", "Top", Team.RED),
    ]
    
    for action in actions:
        if action[0] == "ban":
            _, champion, team = action
            draft.ban_champion(champion, team)
            print(f"✓ {team.value.title()} banned {champion}")
        else:
            _, champion, position, team = action
            success, error = draft.pick_champion(champion, position, team)
            if success:
                print(f"✓ {team.value.title()} picked {champion} for {position}")
            else:
                print(f"✗ {error}")
    
    # Final display
    draft.display()
    
    # Analyze compositions
    print("\n" + "="*70)
    print("TEAM ANALYSIS")
    print("="*70)
    
    for team in [Team.BLUE, Team.RED]:
        comp = draft.get_team_composition(team)
        print(f"\n{team.value.title()} Team:")
        print("-" * 70)
        for pos, champ in comp['positions'].items():
            if champ in draft.champions:
                champ_info = draft.champions[champ]
                archetype = champ_info['primary_archetype']
                roles = ', '.join(champ_info.get('riot_roles', []))
                print(f"  {pos:8s}: {champ:15s} | {archetype:15s} | Riot: {roles}")
        
        arch_counts = {}
        for arch in comp['archetypes']:
            arch_counts[arch] = arch_counts.get(arch, 0) + 1
        
        print(f"\nArchetype Distribution:")
        for arch, count in arch_counts.items():
            print(f"  {arch:20s}: {count}")
        
        # Add synergy analysis
        team_champs = [c for c in comp['positions'].values()]
        analysis = analyze_team_composition(team_champs)
        print(f"\nComposition Type: {analysis['composition_type']}")
        print(f"Team Synergy Score: {analysis['synergy_score']:.3f}")
        
        if analysis['synergy_score'] >= 0.7:
            print("  → Excellent synergy!")
        elif analysis['synergy_score'] >= 0.4:
            print("  → Good synergy")
        elif analysis['synergy_score'] >= 0.0:
            print("  → Acceptable synergy")
        else:
            print("  → Poor synergy (conflicting roles)")



if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        simulate_draft_interactive()
    else:
        simulate_draft_example()
