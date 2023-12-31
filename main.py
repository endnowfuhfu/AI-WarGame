from __future__ import annotations
import argparse
import copy
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from time import sleep
from typing import Tuple, TypeVar, Type, Iterable, ClassVar
import random


# maximum and minimum values for our heuristic scores (usually represents an end of game condition)
MAX_HEURISTIC_SCORE = 2000000000
MIN_HEURISTIC_SCORE = -2000000000

filename = ""

class UnitType(Enum):
    """Every unit type."""
    AI = 0
    Tech = 1
    Virus = 2
    Program = 3
    Firewall = 4

class Player(Enum):
    """The 2 players."""
    Attacker = 0
    Defender = 1

    def next(self) -> Player:
        """The next (other) player."""
        if self is Player.Attacker:
            return Player.Defender
        else:
            return Player.Attacker

class GameType(Enum):
    AttackerVsDefender = 0
    AttackerVsComp = 1
    CompVsDefender = 2
    CompVsComp = 3

##############################################################################################################

@dataclass(slots=True)
class Unit:
    player: Player = Player.Attacker
    type: UnitType = UnitType.Program
    health : int = 9
    # class variable: damage table for units (based on the unit type constants in order)
    damage_table : ClassVar[list[list[int]]] = [
        [3,3,3,3,1], # AI
        [1,1,6,1,1], # Tech
        [9,6,1,6,1], # Virus
        [3,3,3,3,1], # Program
        [1,1,1,1,1], # Firewall
    ]
    # class variable: repair table for units (based on the unit type constants in order)
    repair_table : ClassVar[list[list[int]]] = [
        [0,1,1,0,0], # AI
        [3,0,0,3,3], # Tech
        [0,0,0,0,0], # Virus
        [0,0,0,0,0], # Program
        [0,0,0,0,0], # Firewall
    ]

    def is_alive(self) -> bool:
        """Are we alive ?"""
        return self.health > 0

    def mod_health(self, health_delta : int):
        """Modify this unit's health by delta amount."""
        self.health += health_delta
        if self.health < 0:
            self.health = 0
        elif self.health > 9:
            self.health = 9

    def to_string(self) -> str:
        """Text representation of this unit."""
        p = self.player.name.lower()[0]
        t = self.type.name.upper()[0]
        return f"{p}{t}{self.health}"
    
    def __str__(self) -> str:
        """Text representation of this unit."""
        return self.to_string()
    
    def damage_amount(self, target: Unit) -> int:
        """How much can this unit damage another unit."""
        amount = self.damage_table[self.type.value][target.type.value]
        #if target.health - amount < 0:
            #return target.health
        return amount

    def repair_amount(self, target: Unit) -> int:
        """How much can this unit repair another unit."""
        amount = self.repair_table[self.type.value][target.type.value]
        if target.health + amount > 9:
            return 9 - target.health
        return amount

##############################################################################################################

@dataclass(slots=True)
class Coord:
    """Representation of a game cell coordinate (row, col)."""
    row : int = 0
    col : int = 0

    def col_string(self) -> str:
        """Text representation of this Coord's column."""
        coord_char = '?'
        if self.col < 16:
                coord_char = "0123456789abcdef"[self.col]
        return str(coord_char)

    def row_string(self) -> str:
        """Text representation of this Coord's row."""
        coord_char = '?'
        if self.row < 26:
                coord_char = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[self.row]
        return str(coord_char)

    def to_string(self) -> str:
        """Text representation of this Coord."""
        return self.row_string()+self.col_string()
    
    def __str__(self) -> str:
        """Text representation of this Coord."""
        return self.to_string()
    
    def clone(self) -> Coord:
        """Clone a Coord."""
        return copy.copy(self)

    def iter_range(self, dist: int) -> Iterable[Coord]:
        """Iterates over Coords inside a rectangle centered on our Coord."""
        for row in range(self.row-dist,self.row+1+dist):
            for col in range(self.col-dist,self.col+1+dist):
                yield Coord(row,col)

    def iter_adjacent(self) -> Iterable[Coord]:
        """Iterates over adjacent Coords."""
        yield Coord(self.row-1,self.col)
        yield Coord(self.row,self.col-1)
        yield Coord(self.row+1,self.col)
        yield Coord(self.row,self.col+1)

    @classmethod
    def from_string(cls, s : str) -> Coord | None:
        """Create a Coord from a string. ex: D2."""
        s = s.strip()
        for sep in " ,.:;-_":
                s = s.replace(sep, "")
        if (len(s) == 2):
            coord = Coord()
            coord.row = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".find(s[0:1].upper())
            coord.col = "0123456789abcdef".find(s[1:2].lower())
            return coord
        else:
            return None

##############################################################################################################

@dataclass(slots=True)
class CoordPair:
    """Representation of a game move or a rectangular area via 2 Coords."""
    src : Coord = field(default_factory=Coord)
    dst : Coord = field(default_factory=Coord)

    def to_string(self) -> str:
        """Text representation of a CoordPair."""
        return self.src.to_string()+" "+self.dst.to_string()
    
    def __str__(self) -> str:
        """Text representation of a CoordPair."""
        return self.to_string()

    def clone(self) -> CoordPair:
        """Clones a CoordPair."""
        return copy.copy(self)

    def iter_rectangle(self) -> Iterable[Coord]:
        """Iterates over cells of a rectangular area."""
        for row in range(self.src.row,self.dst.row+1):
            for col in range(self.src.col,self.dst.col+1):
                yield Coord(row,col)

    @classmethod
    def from_quad(cls, row0: int, col0: int, row1: int, col1: int) -> CoordPair:
        """Create a CoordPair from 4 integers."""
        return CoordPair(Coord(row0,col0),Coord(row1,col1))
    
    @classmethod
    def from_dim(cls, dim: int) -> CoordPair:
        """Create a CoordPair based on a dim-sized rectangle."""
        return CoordPair(Coord(0,0),Coord(dim-1,dim-1))
    
    @classmethod
    def from_string(cls, s : str) -> CoordPair | None:
        """Create a CoordPair from a string. ex: A3 B2"""
        s = s.strip()
        for sep in " ,.:;-_":
                s = s.replace(sep, "")
        if (len(s) == 4):
            coords = CoordPair()
            coords.src.row = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".find(s[0:1].upper())
            coords.src.col = "0123456789abcdef".find(s[1:2].lower())
            coords.dst.row = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".find(s[2:3].upper())
            coords.dst.col = "0123456789abcdef".find(s[3:4].lower())
            return coords
        else:
            return None

##############################################################################################################

@dataclass(slots=True)
class Options:
    """Representation of the game options."""
    dim: int = 5
    max_depth : int | None = 4
    min_depth : int | None = 2
    max_time : float | None = 5.0
    game_type : GameType = GameType.AttackerVsDefender
    alpha_beta : bool = True
    max_turns : int | None = 100
    randomize_moves : bool = True
    broker : str | None = None

##############################################################################################################

@dataclass(slots=True)
class Stats:
    """Representation of the global game statistics."""
    evaluations_per_depth : dict[int,int] = field(default_factory=dict)
    total_seconds: float = 0.0

##############################################################################################################

@dataclass(slots=True)
class Game:
    """Representation of the game state."""
    board: list[list[Unit | None]] = field(default_factory=list)
    next_player: Player = Player.Attacker
    turns_played : int = 0
    options: Options = field(default_factory=Options)
    stats: Stats = field(default_factory=Stats)
    _attacker_has_ai : bool = True
    _defender_has_ai : bool = True

    def __post_init__(self):
        """Automatically called after class init to set up the default board state."""
        dim = self.options.dim
        self.board = [[None for _ in range(dim)] for _ in range(dim)]
        md = dim-1
        self.set(Coord(0,0),Unit(player=Player.Defender,type=UnitType.AI))
        self.set(Coord(1,0),Unit(player=Player.Defender,type=UnitType.Tech))
        self.set(Coord(0,1),Unit(player=Player.Defender,type=UnitType.Tech))
        self.set(Coord(2,0),Unit(player=Player.Defender,type=UnitType.Firewall))
        self.set(Coord(0,2),Unit(player=Player.Defender,type=UnitType.Firewall))
        self.set(Coord(1,1),Unit(player=Player.Defender,type=UnitType.Program))
        self.set(Coord(md,md),Unit(player=Player.Attacker,type=UnitType.AI))
        self.set(Coord(md-1,md),Unit(player=Player.Attacker,type=UnitType.Virus))
        self.set(Coord(md,md-1),Unit(player=Player.Attacker,type=UnitType.Virus))
        self.set(Coord(md-2,md),Unit(player=Player.Attacker,type=UnitType.Program))
        self.set(Coord(md,md-2),Unit(player=Player.Attacker,type=UnitType.Program))
        self.set(Coord(md-1,md-1),Unit(player=Player.Attacker,type=UnitType.Firewall))

    def clone(self) -> Game:
        """Make a new copy of a game for minimax recursion.

        Shallow copy of everything except the board (options and stats are shared).
        """
        new = copy.copy(self)
        new.board = copy.deepcopy(self.board)
        return new

    def is_empty(self, coord : Coord) -> bool:
        """Check if contents of a board cell of the game at Coord is empty (must be valid coord)."""
        return self.board[coord.row][coord.col] is None

    def get(self, coord : Coord) -> Unit | None:
        """Get contents of a board cell of the game at Coord."""
        if self.is_valid_coord(coord):
            return self.board[coord.row][coord.col]
        else:
            return None

    def set(self, coord : Coord, unit : Unit | None):
        """Set contents of a board cell of the game at Coord."""
        if self.is_valid_coord(coord):
            self.board[coord.row][coord.col] = unit

    def remove_dead(self, coord: Coord):
        """Remove unit at Coord if dead."""
        unit = self.get(coord)
        if unit is not None and not unit.is_alive():
            print(f'{unit.player.name}\'s {unit.type.name} ELIMINATED')
            self.set(coord,None)
            if unit.type == UnitType.AI:
                if unit.player == Player.Attacker:
                    self._attacker_has_ai = False
                else:
                    self._defender_has_ai = False

    def mod_health(self, coord : Coord, health_delta : int):
        """Modify health of unit at Coord (positive or negative delta)."""
        target = self.get(coord)
        if target is not None:
            target.mod_health(health_delta)
            self.remove_dead(coord)

    def is_valid_move(self, coords : CoordPair) -> bool:
        """Validate a move expressed as a CoordPair. TODO: WRITE MISSING CODE!!!"""
        unit = self.get(coords.src)
        if unit is None or unit.player != self.next_player:
            return False
                        
        adjU = self.get(Coord(coords.src.row-1,coords.src.col)) #tile on top of selected unit
        adjR = self.get(Coord(coords.src.row,coords.src.col+1)) #tile on right of selected unit
        adjD = self.get(Coord(coords.src.row+1,coords.src.col)) #tile on bottom of selected unit
        adjL = self.get(Coord(coords.src.row,coords.src.col-1)) #tile on left of selected unit

        #restrict attacker's movement
        if unit.player==Player.Attacker:
            #restrict movement to up or left for Program, AI, Firewall
            if unit.type==UnitType.Program or unit.type==UnitType.AI or unit.type==UnitType.Firewall:
                if coords.dst.col > coords.src.col or coords.dst.row > coords.src.row:
                    return False
                #check if the unit is adjacent to an enemy unit
                if adjU != None:
                    if adjU.player==Player.Defender:
                        return False
                if adjR != None:
                    if adjR.player==Player.Defender:
                        return False
                if adjD != None:
                    if adjD.player==Player.Defender:
                        return False
                if adjL != None:
                    if adjL.player==Player.Defender:
                        return False
            #units can only move 1 tile
            if ((coords.src.col - coords.dst.col >=2 or coords.src.row - coords.dst.row >=2) or (coords.src.col - coords.dst.col >=1 and coords.src.row - coords.dst.row >=1)):
                return False
           
        #restrict defender's movement
        if unit.player==Player.Defender:
            #restrict movement to down or right for Program, AI and Firewall
            if unit.type==UnitType.Program or unit.type==UnitType.AI or unit.type==UnitType.Firewall:
                if coords.dst.col < coords.src.col or coords.dst.row < coords.src.row:
                    return False
                #check if the unit is adjacent to an enemy unit
                if adjU != None:
                    if adjU.player==Player.Attacker:
                        return False
                if adjR != None:
                    if adjR.player==Player.Attacker:
                        return False
                if adjD != None:
                    if adjD.player==Player.Attacker:
                        return False
                if adjL != None:
                    if adjL.player==Player.Attacker:
                        return False
            #units can only move 1 tile
            if (coords.src.col - coords.dst.col <=-2 or coords.src.row - coords.dst.row <=-2) or (coords.src.col - coords.dst.col <=-1 and coords.src.row - coords.dst.row <=-1) :
                return False

        
        unit = self.get(coords.dst)
        return (unit is None)
    
    def is_tile_adjacent(self, coords: CoordPair) -> bool :
        return (coords.dst == Coord(coords.src.row-1,coords.src.col) or coords.dst == Coord(coords.src.row,coords.src.col+1) or coords.dst == Coord(coords.src.row+1,coords.src.col) or coords.dst == Coord(coords.src.row,coords.src.col-1))
        
    def is_target_adversary(self, coords: CoordPair) -> bool:
        myUnit = self.get(coords.src)
        if myUnit is None or myUnit.player != self.next_player:
            return False
        
        targetUnit = self.get(coords.dst)
        if targetUnit != None:
            if targetUnit.player!=myUnit.player:
                return True
        return False
    
    def is_target_ally(self, coords : CoordPair) -> bool:
        myUnit = self.get(coords.src)
        targetUnit = self.get(coords.dst)

        if targetUnit != None and myUnit != None:
            if targetUnit.player==myUnit.player:
                return True
        return False
    
    def is_src_tile_dst(self, coords : CoordPair) -> bool:
        unit = self.get(coords.src)
        if unit is None or unit.player != self.next_player:
            return False
        
        srcRow = coords.src.row
        srcCol = coords.src.col
        targetRow = coords.dst.row
        targetCol = coords.dst.col

        if srcRow == targetRow and srcCol == targetCol:
                return True
        return False
    
    def attack_target_adversary(self, coords : CoordPair, unit: Unit, targetUnit : Unit) -> bool:
        dmgToTargetUnit = unit.damage_amount(targetUnit)
        dmgToOwnUnit = targetUnit.damage_amount(unit)
        self.mod_health(coords.src, -abs(dmgToOwnUnit))
        self.mod_health(coords.dst, -abs(dmgToTargetUnit))
        print(f'{unit.player.name} DAMAGE {unit.type.name} TO {targetUnit.type.name}: {-abs(dmgToTargetUnit)}')
        print(f'{targetUnit.player.name} DAMAGE {targetUnit.type.name} TO {unit.type.name}: {-abs(dmgToOwnUnit)}')

    def repairing (self, coords : CoordPair, unit: Unit, targetUnit : Unit) -> bool:
        healToTargetUnit = unit.repair_amount(targetUnit)
        self.mod_health(coords.dst, +abs(healToTargetUnit))
        print(f'{unit.player.name}\'s {unit.type.name} HEAL TO {targetUnit.type.name}: +{healToTargetUnit}')

    def repairable (self, coords : CoordPair, unit: Unit, targetUnit : Unit) -> bool:
        healToTargetUnit = unit.repair_amount(targetUnit)
        if healToTargetUnit >0:
            return True
        
    def self_destruct(self, coord: Coord):
        """Apply the self-destruct move for a unit at the given coordinate."""
        # List of all possible surrounding coordinates
        surrounding_coords = [
            Coord(row=coord.row - 1, col=coord.col - 1),  # top-left
            Coord(row=coord.row - 1, col=coord.col),      # top
            Coord(row=coord.row - 1, col=coord.col + 1),  # top-right
            Coord(row=coord.row, col=coord.col - 1),      # left
            Coord(row=coord.row, col=coord.col + 1),      # right
            Coord(row=coord.row + 1, col=coord.col - 1),  # bottom-left
            Coord(row=coord.row + 1, col=coord.col),      # bottom
            Coord(row=coord.row + 1, col=coord.col + 1)   # bottom-right
        ]
        
        # Retrieve the self-destructing unit
        self_destruct_unit = self.get(coord)
        
        for sur_coord in surrounding_coords:
            if self.is_valid_coord(sur_coord):
                target_unit = self.get(sur_coord)
                if target_unit:
                    # Damage amount to the target unit (you may adjust the damage value)
                    damage_to_target = 2
                    # Modify the health of the target unit
                    self.mod_health(sur_coord, -abs(damage_to_target))
                    # Print out the damage message
                    print(f'{self_destruct_unit.player.name} DAMAGE {self_destruct_unit.type.name} TO {target_unit.type.name}: {-abs(damage_to_target)}')
        
        # Reduce the health of the self-destructing unit to 0
        self.mod_health(coord, -abs(self.get(coord).health))

        # After performing the self-destruction, if successful
        return (True, f"{self_destruct_unit.type.name} self-destructed successfully.")


        
    def perform_move(self, coords : CoordPair) -> Tuple[bool,str]:
        if not self.is_valid_coord(coords.src) or not self.is_valid_coord(coords.dst):
            return (False, "")
        
        f = open(filename, "a")

        """Validate and perform a move expressed as a CoordPair. TODO: WRITE MISSING CODE!!!"""
        if self.is_valid_move(coords):
            self.set(coords.dst,self.get(coords.src))
            self.set(coords.src,None)

            # write to file
            f.write(f"\nMove from {coords.src} to {coords.dst}\n")
            f.close()
            return (True, "")
        #if the dst tile is an adversary and is adjacent, perform an attack
        elif self.is_tile_adjacent(coords) and self.is_target_adversary(coords):
            print('Attacking adversary')
            self.attack_target_adversary(coords, self.get(coords.src), self.get(coords.dst))

            # write to file
            f.write(f"\nAttack from {coords.src} to {coords.dst}\n")
            f.close()
            return (True, "")
        #if the dst tile is an ally and is adjacent, perform a repair 
        elif self.is_tile_adjacent(coords) and self.is_target_ally(coords):
            if self.repairable(coords, self.get(coords.src), self.get(coords.dst)):
                print('Repairing unit')
                self.repairing(coords, self.get(coords.src), self.get(coords.dst))

                # write to file
                f.write(f"\nHeal from {coords.src} to {coords.dst}\n")
                f.close()
                return (True, "")   
        elif self.is_src_tile_dst(coords):
            print('Self-destructing')
            self.self_destruct(coords.src)

            # write to file
            f.write(f"\n{coords.src} unit self-destructs\n")
            f.close()
            return (True, "")
        return (False,"invalid move")

    def next_turn(self):
        """Transitions game to the next turn."""
        self.next_player = self.next_player.next()
        self.turns_played += 1

    def to_string(self) -> str:
        """Pretty text representation of the game."""
        dim = self.options.dim
        output = ""
        output += f"Next player: {self.next_player.name}\n"
        output += f"Turns played: {self.turns_played}\n"
        coord = Coord()
        output += "\n   "
        for col in range(dim):
            coord.col = col
            label = coord.col_string()
            output += f"{label:^3} "
        output += "\n"
        for row in range(dim):
            coord.row = row
            label = coord.row_string()
            output += f"{label}: "
            for col in range(dim):
                coord.col = col
                unit = self.get(coord)
                if unit is None:
                    output += " .  "
                else:
                    output += f"{str(unit):^3} "
            output += "\n"

        # Write to file the current state of the game
        if not filename == "":
            f = open(filename, "a")
            f.write("\n"+output)
            f.close()
        return output

    def __str__(self) -> str:
        """Default string representation of a game."""
        return self.to_string()
    
    def is_valid_coord(self, coord: Coord) -> bool:
        """Check if a Coord is valid within out board dimensions."""
        dim = self.options.dim
        if coord.row < 0 or coord.row >= dim or coord.col < 0 or coord.col >= dim:
            return False
        return True

    def read_move(self) -> CoordPair:
        """Read a move from keyboard and return as a CoordPair."""
        while True:
            s = input(F'Player {self.next_player.name}, enter your move: ')
            coords = CoordPair.from_string(s)
            if coords is not None and self.is_valid_coord(coords.src) and self.is_valid_coord(coords.dst):
                return coords
            else:
                print('Invalid coordinates! Try again.')
    
    def human_turn(self):
        """Human player plays a move (or get via broker)."""
        if self.options.broker is not None:
            print("Getting next move with auto-retry from game broker...")
            while True:
                mv = self.get_move_from_broker()
                if mv is not None:
                    (success,result) = self.perform_move(mv)
                    print(f"Broker {self.next_player.name}: ",end='')
                    print(result)
                    if success:
                        self.next_turn()
                        break
                sleep(0.1)
        else:
            while True:
                mv = self.read_move()
                (success,result) = self.perform_move(mv)
                if success:
                    print(f"Player {self.next_player.name}: ",end='')
                    print(result)
                    self.next_turn()
                    break
                else:
                    print("The move is not valid! Try again.")


    def computer_turn(self) -> CoordPair | None:
        """Computer plays a move."""
        mv = self.suggest_move()
        if mv is not None:
            (success,result) = self.perform_move(mv)
            if success:
                print(f"Computer {self.next_player.name}: ",end='')
                print(result)
                self.next_turn()
        return mv

    def player_units(self, player: Player) -> Iterable[Tuple[Coord,Unit]]:
        """Iterates over all units belonging to a player."""
        for coord in CoordPair.from_dim(self.options.dim).iter_rectangle():
            unit = self.get(coord)
            if unit is not None and unit.player == player:
                yield (coord,unit)

    def is_finished(self) -> bool:
        """Check if the game is over."""
        return self.has_winner() is not None

    def has_winner(self) -> Player | None:
        """Check if the game is over and returns winner"""
        if self.options.max_turns is not None and self.turns_played >= self.options.max_turns:
            return Player.Defender
        elif self._attacker_has_ai:
            if self._defender_has_ai:
                return None
            else:
                return Player.Attacker    
        elif self._defender_has_ai:
            return Player.Defender
        #if both AIs die at the same time, the defender wins
        elif not self._defender_has_ai and not self._attacker_has_ai:
            return Player.Defender

    def move_candidates(self) -> Iterable[CoordPair]:
        """Generate valid move candidates for the next player."""
        move = CoordPair()
        for (src,_) in self.player_units(self.next_player):
            move.src = src
            for dst in src.iter_adjacent():
                move.dst = dst
                print(f'move: {move}')
                if self.is_valid_move(move):
                    yield move.clone()
            move.dst = src
            yield move.clone()

    def random_move(self) -> Tuple[int, CoordPair | None, float]:
        """Returns a random move."""
        move_candidates = list(self.move_candidates())
        random.shuffle(move_candidates)
        if len(move_candidates) > 0:
            return (0, move_candidates[0], 1)
        else:
            return (0, None, 0)

    def suggest_move(self) -> CoordPair | None:
        """Suggest the next move using minimax alpha beta. TODO: REPLACE RANDOM_MOVE WITH PROPER GAME LOGIC!!!"""
        start_time = datetime.now()
        (score, move, avg_depth) = self.random_move()
        elapsed_seconds = (datetime.now() - start_time).total_seconds()
        self.stats.total_seconds += elapsed_seconds
        print(f"Heuristic score: {score}")
        print(f"Average recursive depth: {avg_depth:0.1f}")
        print(f"Evals per depth: ",end='')
        for k in sorted(self.stats.evaluations_per_depth.keys()):
            print(f"{k}:{self.stats.evaluations_per_depth[k]} ",end='')
        print()
        total_evals = sum(self.stats.evaluations_per_depth.values())
        if self.stats.total_seconds > 0:
            print(f"Eval perf.: {total_evals/self.stats.total_seconds/1000:0.1f}k/s")
        print(f"Elapsed time: {elapsed_seconds:0.1f}s")
        return move

    def post_move_to_broker(self, move: CoordPair):
        """Send a move to the game broker."""
        if self.options.broker is None:
            return
        data = {
            "from": {"row": move.src.row, "col": move.src.col},
            "to": {"row": move.dst.row, "col": move.dst.col},
            "turn": self.turns_played
        }
        try:
            r = requests.post(self.options.broker, json=data)
            if r.status_code == 200 and r.json()['success'] and r.json()['data'] == data:
                # print(f"Sent move to broker: {move}")
                pass
            else:
                print(f"Broker error: status code: {r.status_code}, response: {r.json()}")
        except Exception as error:
            print(f"Broker error: {error}")

    def get_move_from_broker(self) -> CoordPair | None:
        """Get a move from the game broker."""
        if self.options.broker is None:
            return None
        headers = {'Accept': 'application/json'}
        try:
            r = requests.get(self.options.broker, headers=headers)
            if r.status_code == 200 and r.json()['success']:
                data = r.json()['data']
                if data is not None:
                    if data['turn'] == self.turns_played+1:
                        move = CoordPair(
                            Coord(data['from']['row'],data['from']['col']),
                            Coord(data['to']['row'],data['to']['col'])
                        )
                        print(f"Got move from broker: {move}")
                        return move
                    else:
                        # print("Got broker data for wrong turn.")
                        # print(f"Wanted {self.turns_played+1}, got {data['turn']}")
                        pass
                else:
                    # print("Got no data from broker")
                    pass
            else:
                print(f"Broker error: status code: {r.status_code}, response: {r.json()}")
        except Exception as error:
            print(f"Broker error: {error}")
        return None
    
def read_max_time_allowed() -> float:
    while True:
        time_input = input('Enter the maximum time (in seconds) allowed for the AI to return its move: ')
        try:
            max_time = float(time_input)
            return max_time
        except ValueError:
            print("Incorrect Input. Please provide a number.")

def read_max_turns() -> float:
    while True:
        turn_input = input('Enter the maximum number of turns: ')
        try:
            max_turns = float(turn_input)
            return max_turns
        except ValueError:
            print("Incorrect Input. Please provide a number.")

def read_is_alphabeta() -> str:
    while True:
        bool_input = input('Enter an algorithm: alpha-beta (T) or minimax (F): ')
        if bool_input.upper() == 'T':
            return 'true'
        elif bool_input.upper() == 'F':
            return 'false'
        else:
            print('Invalid input. Please put T for alpha-beta and F for minimax.')

def read_playmodes() -> str:
    while True:
        p_input = input('Enter the play mode: 1. Human vs. Human | 2. Human vs. AI | 3. AI vs. Human | 4. AI vs. AI: ')
        if p_input == '1':
            return "manual"
        elif p_input == '2':
            return "attacker"
        elif p_input == '3':
            return "defender"
        elif p_input == '4':
            return "comp"
        else:
            print('Invalid input. Please choose a play mode [1-4].')

def formatFloat(num):
  if num % 1 == 0:
    return int(num)
  else:
    return num

##############################################################################################################

def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(
        prog='ai_wargame',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--max_depth', type=int, help='maximum search depth')
    parser.add_argument('--max_time', type=float, help='maximum search time')
    parser.add_argument('--game_type', type=str, default="manual", help='game type: auto|attacker|defender|manual')
    parser.add_argument('--broker', type=str, help='play via a game broker')
    args = parser.parse_args()

    # parse the game type
    if args.game_type == "attacker":
        game_type = GameType.AttackerVsComp
    elif args.game_type == "defender":
        game_type = GameType.CompVsDefender
    elif args.game_type == "manual":
        game_type = GameType.AttackerVsDefender
    else:
        game_type = GameType.CompVsComp

    # set up game options
    options = Options(game_type=game_type)

    # Game Parameters
    max_time = formatFloat(read_max_time_allowed()) #NOT USED IN D1
    args.max_time = max_time
    print(f'max time: {max_time}')

    max_turns = formatFloat(read_max_turns())
    options.max_turns = max_turns
    print(f'max turns: {max_turns}')

    is_alphabeta = read_is_alphabeta() #NOT USED IN D1
    playmode = read_playmodes() #NOT USED IN D1

    # Create Output file gameTrace-<b>-<t>-<m>.txt
    global filename
    filename = "gameTrace-{}-{}-{}.txt".format(is_alphabeta, max_time, max_turns)
    f = open(filename, "w")

    # Game params to write to file
    #params = 'Timeout in seconds: '+{str(max_time)}+'\n'+'Max number of turns: '+{str(max_turns)}+'\n'+'Alphabeta: '+{is_alphabeta}+'\n'+'Play mode: '+{str(playmode)}
    params = f'Timeout in seconds: {max_time} \nMax number of turns: {max_turns} \nAlpha-beta: {is_alphabeta} \n'
    f.write(params)     
    fileparam_playmode = ""

    # to use later
    if playmode == "manual":
        fileparam_playmode = "Player 1 = H & Player 2 = H\n"
    elif playmode == "attacker":
        fileparam_playmode = "Player 1 = H & Player 2 = AI\n"
    elif playmode == "defender":
        fileparam_playmode = "Player 1 = AI & Player 2 = H\n"
    elif playmode == "comp":
        fileparam_playmode = "Player 1 = AI & Player 2 = AI\n"

    # for now, only H-H can be done
    fileparam_playmode = "Player 1 = H & Player 2 = H\n"

    f.write(fileparam_playmode)
    f.close()


    # override class defaults via command line options
    if args.max_depth is not None:
        options.max_depth = args.max_depth
    if args.max_time is not None:
        options.max_time = args.max_time
    if args.broker is not None:
        options.broker = args.broker

    # create a new game
    game = Game(options=options)

    # the main game loop
    while True:
        print()
        print(game)
        winner = game.has_winner()
        if winner is not None:
            f = open(filename, "a")
            f.write(f"{winner.name} wins in {game.turns_played} turns!")
            f.close()
            print(f"{winner.name} wins in {game.turns_played} turns!")
            break
        if game.options.game_type == GameType.AttackerVsDefender:
            game.human_turn()
        elif game.options.game_type == GameType.AttackerVsComp and game.next_player == Player.Attacker:
            game.human_turn()
        elif game.options.game_type == GameType.CompVsDefender and game.next_player == Player.Defender:
            game.human_turn()
        else:
            player = game.next_player
            move = game.computer_turn()
            if move is not None:
                game.post_move_to_broker(move)
            else:
                print("Computer doesn't know what to do!!!")
                exit(1)

##############################################################################################################

if __name__ == '__main__':
    main()
