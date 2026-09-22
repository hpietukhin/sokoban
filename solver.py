# solver.py

import clingo
import argparse
import math
from typing import List, Tuple, Set, Optional, Dict

from sokoban_map import SokobanMap


class SokobanSolver:
    """
    A solver for Sokoban puzzles using the Clingo ASP solver.
    """

    def __init__(
        self,
        domain_asp_file: str,
        max_steps: int = 50,
        optimize: bool = True,
    ):
        """
        Initializes the SokobanSolver.

        Args:
            domain_asp_file: Path to the ASP domain rules file.
            max_steps: Maximum number of steps to search for a solution.
            optimize: Whether to prove that the returned plan uses the fewest actions.
        """
        self.domain_asp_file = domain_asp_file
        self.max_steps = max_steps
        self.optimize = optimize

    @staticmethod
    def cell_index(row: int, col: int) -> str:
        """Generates a unique cell identifier based on row and column."""
        return f"{row}_{col}"

    def generate_facts_from_map(self, map_str: str) -> str:
        """
        Converts the Sokoban map into ASP facts.

        Args:
            map_str: String representation of the Sokoban map.
            max_steps: Maximum number of steps for the solver.

        Returns:
            A string containing ASP facts derived from the map.
        """
        lines = [line for line in map_str.splitlines() if line.strip()]
        height = len(lines)
        width = max(len(row) for row in lines) if lines else 0

        sokoban_pos: Optional[Tuple[int, int]] = None
        crate_positions: Set[Tuple[int, int]] = set()
        walls: Set[Tuple[int, int]] = set()
        goal_positions: Set[Tuple[int, int]] = set()

        for r, row in enumerate(lines):
            for c, ch in enumerate(row):
                pos = (r, c)
                if ch == '#':
                    walls.add(pos)
                elif ch in ('S', 's'):
                    sokoban_pos = pos
                    if ch == 's' and pos not in walls:
                        goal_positions.add(pos)
                elif ch in ('C', 'c'):
                    crate_positions.add(pos)
                    if ch == 'c' and pos not in walls:
                        goal_positions.add(pos)
                elif ch == 'X' and pos not in walls:
                    goal_positions.add(pos)

        facts = ["sokoban(sokoban)."]
        for i, _ in enumerate(sorted(crate_positions), start=1):
            facts.append(f"crate(crate_{i:02d}).")

        location_list, goal_list, non_goal_list, walls_list = self._categorize_cells(
            lines, height, width, goal_positions, walls
        )

        facts.extend(self._format_facts(location_list, goal_list, non_goal_list, walls_list))
        facts.extend(self._define_relations(lines, height, width))
        facts.extend(self._define_initial_positions(sokoban_pos, crate_positions, height, width, lines, walls))
        #facts.append(f"#const maxsteps={max_steps}.")
        facts.append("time(0..maxsteps).")

        return "\n".join(facts)

    def _categorize_cells(
        self,
        lines: List[str],
        height: int,
        width: int,
        goal_positions: Set[Tuple[int, int]],
        walls: Set[Tuple[int, int]],
    ) -> Tuple[List[str], List[str], List[str], List[str]]:
        """Categorizes cells into locations, goals, non-goals, and walls."""
        location_list, goal_list, non_goal_list, walls_list = [], [], [], []
        for r in range(height):
            row_length = len(lines[r])
            for c in range(row_length):
                cell_id = f"l{self.cell_index(r, c)}"
                pos = (r, c)
                if pos in walls:
                    walls_list.append(cell_id)
                    continue
                location_list.append(cell_id)
                if pos in goal_positions:
                    goal_list.append(cell_id)
                else:
                    non_goal_list.append(cell_id)
        assert not set(goal_list) & set(non_goal_list), "Conflict: Cells in both isgoal and isnongoal"
        return location_list, goal_list, non_goal_list, walls_list

    @staticmethod
    def _format_facts(
        locations: List[str],
        goals: List[str],
        non_goals: List[str],
        walls: List[str],
    ) -> List[str]:
        """Formats the categorized cells into ASP facts."""
        facts = []
        if locations:
            facts.append(f"location({';'.join(locations)}).")
        if goals:
            facts.append(f"isgoal({';'.join(goals)}).")
        if non_goals:
            facts.append(f"isnongoal({';'.join(non_goals)}).")
        if walls:
            facts.append(f"wall({';'.join(walls)}).")
        return facts

    def _define_relations(self, lines: List[str], height: int, width: int) -> List[str]:
        """Defines spatial relations (leftOf, below) between cells."""
        relations = []
        for r in range(height):
            row_length = len(lines[r])
            for c in range(row_length):
                current_id = self.cell_index(r, c)
                if c + 1 < row_length:
                    right_id = self.cell_index(r, c + 1)
                    relations.append(f"leftOf(l{current_id}, l{right_id}).")
                if r + 1 < height and c < len(lines[r + 1]):
                    below_id = self.cell_index(r + 1, c)
                    relations.append(f"below(l{below_id}, l{current_id}).")
        return relations

    def _define_initial_positions(
        self,
        sokoban_pos: Optional[Tuple[int, int]],
        crate_positions: Set[Tuple[int, int]],
        height: int,
        width: int,
        lines: List[str],
        walls: Set[Tuple[int, int]],
    ) -> List[str]:
        """Defines the initial positions of the Sokoban and crates."""
        initial_positions = []
        if sokoban_pos:
            sokoban_id = self.cell_index(*sokoban_pos)
            initial_positions.append(f"at(sokoban, l{sokoban_id}, 0).")

        for i, (r, c) in enumerate(sorted(crate_positions), start=1):
            crate_name = f"crate_{i:02d}"
            crate_id = self.cell_index(r, c)
            initial_positions.append(f"at({crate_name}, l{crate_id}, 0).")

        occupied = crate_positions.union({sokoban_pos} if sokoban_pos else set())
        for r in range(height):
            row_length = len(lines[r])
            for c in range(row_length):
                pos = (r, c)
                if pos not in occupied and pos not in walls:
                    cell_id = self.cell_index(r, c)
                    initial_positions.append(f"clear(l{cell_id}, 0).")
        return initial_positions

    def solve(self, map_str: str) -> str:
        """
        Solves the Sokoban puzzle based on the provided map.

        Args:
            map_str: String representation of the Sokoban map.

        Returns:
            A formatted string with the solution steps or "No solution found".
        """
        instance_facts = self.generate_facts_from_map(map_str)
        solution_steps: Optional[List[str]] = None
        solve_arguments = (
            ["--models=0", "--opt-mode=opt"]
            if self.optimize
            else ["--models=1", "--opt-mode=ignore"]
        )
        solve_arguments.extend(["--const", f"maxsteps={self.max_steps}"])
        ctl = clingo.Control(arguments=solve_arguments)
        ctl.load(self.domain_asp_file)
        ctl.add("base", [], instance_facts)
        ctl.ground([("base", [])])

        def handle_model(model: clingo.Model) -> None:
            nonlocal solution_steps
            atoms = [str(atom) for atom in model.symbols(shown=True)]
            solution_steps = [atom for atom in atoms if atom.startswith("do(")]

        result = ctl.solve(on_model=handle_model)
        if result.satisfiable and solution_steps is not None:
            return self._format_solution(solution_steps)
        return f"No solution found within {self.max_steps} steps"

    def _format_solution(self, steps: List[str]) -> str:
        """
        Formats the solution steps into a readable string.

        Args:
            steps: List of action literals.

        Returns:
            A formatted solution string.
        """
        step_to_action: Dict[int, str] = {}
        for action_literal in steps:
            inside = action_literal[len("do("):-1]
            last_comma = inside.rfind(",")
            step_str = inside[last_comma + 1:].strip()
            try:
                step_num = int(step_str)
                action_text = inside[:last_comma].strip()
                step_to_action[step_num] = action_text
            except ValueError:
                continue

        if step_to_action:
            max_step = max(step_to_action.keys())
            result_lines = [f"Solution found in {max_step + 1} steps (0..{max_step}):"]
            for t in sorted(step_to_action.keys()):
                result_lines.append(f"Step {t}: do({step_to_action[t]}, {t})")
            return "\n".join(result_lines)
        return "Solution found in 0 steps."

    @staticmethod
    def _estimate_min_steps(map_str: str) -> int:
        """
        Estimates the minimum number of steps required based on the map size.

        Args:
            map_str: String representation of the Sokoban map.

        Returns:
            An estimated minimum number of steps.
        """
        lines = [line for line in map_str.splitlines() if line.strip()]
        height = len(lines)
        width = max(len(row) for row in lines) if lines else 0
        return math.ceil(math.sqrt(height**2 + width**2))

    
def main():
    parser = argparse.ArgumentParser(description="Solve Sokoban puzzles using Clingo.")
    parser.add_argument("domain_file", help="Path to the ASP domain rules file.")
    parser.add_argument("map_file", help="Path to the Sokoban map file.")
    parser.add_argument("--max_steps", type=int, default=50, help="Maximum number of steps to search.")
    args = parser.parse_args()

    with open(args.map_file, 'r') as f:
        map_str = f.read()

    solver = SokobanSolver(domain_asp_file=args.domain_file, max_steps=args.max_steps)
    solution = solver.solve(map_str)

    print(solution)

    # Optional visualization
    # If you want to visualize each step, you can parse the solution and update the map accordingly
    map_obj = SokobanMap(map_str)
    print("initial map state")
    print(map_str)
    solution_steps = [line for line in solution.splitlines() if line.startswith("Step")]
    solution_steps = [line.split(": ", 1)[1] for line in solution_steps]

    for i, step in enumerate(solution_steps):
        map_obj.apply_step(step)
        print(f"\nAfter step {i}:")
        map_obj.visualize()


if __name__ == "__main__":
    main()
