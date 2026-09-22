#sokoban_map.py
from typing import List, Tuple


class SokobanMap:
    """
    Represents a Sokoban map and provides methods for updating and visualizing it.
    """

    # Constants for symbols
    SYMBOL_WALL = '#'
    SYMBOL_CRATE = 'C'
    SYMBOL_GOAL = 'X'
    SYMBOL_SOKOBAN = 'S'
    SYMBOL_SOKOBAN_GOAL = 's'
    SYMBOL_CRATE_GOAL = 'c'

    def __init__(self, map_str: str):
        """
        Initializes SokobanMap.

        Args:
            map_str: String representation of the Sokoban map.
        """
        self.map_grid: List[List[str]] = [list(line) for line in map_str.split('\n') if line.strip()]
        self.height = len(self.map_grid)
        self.width = max(len(row) for row in self.map_grid) if self.map_grid else 0
    

    @classmethod
    def read_map_file(cls, file_path: str) -> str:
        """
        Reads the content of a map file and returns it as a string.

        Args:
            file_path: Path to the map file.

        Returns:
            A string containing the map.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Map file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading map file {file_path}: {e}")

    @staticmethod
    def write_map_file(file_path: str, map_str: str) -> None:
        """
        Writes the map string to a file.

        Args:
            file_path: Path to the output map file.
            map_str: String representation of the Sokoban map.
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(map_str)
        except Exception as e:
            raise Exception(f"Error writing map file {file_path}: {e}")
        
    def to_string(self) -> str:
        """
        Converts the current map grid to a string representation.

        Returns:
            A string representing the current state of the map.
        """
        return '\n'.join(''.join(row) for row in self.map_grid)

    def is_solved(self) -> bool:
        """Return whether every crate is currently on a goal."""
        return all(self.SYMBOL_CRATE not in row for row in self.map_grid)

    def get_map_steps(self, steps: List[str]) -> List[str]:
        """
        Applies a list of steps to the map and returns the map state after each step.

        Args:
            steps: A list of step actions.

        Returns:
            A list of map strings representing the state after each step.
        """
        map_states = [self.to_string()]  # Initial state
        for step in steps:
            self.apply_step(step)
            map_str = self.to_string()
            map_states.append(map_str)
        return map_states
    
    def _set_cell(self, from_r, from_c, symbol): 
        self.map_grid[from_r][from_c] = symbol

    def apply_step(self, step: str) -> None:
        """
        Applies one step to update the map.

        Args:
            step: Action in the format of ASP literals (e.g., do(push(...)), do(move(...)), do(moveRight(...))).
        """
        if step.startswith("do(push"):
            self._apply_push(step)
        elif step.startswith("do(move"):
            self._apply_move(step)
        else:
            print(f"Unknown step format: {step}")

    def _apply_push(self, step: str) -> None:
        """
        Applies a push action to the map.

        Args:
            step: Push action literal, e.g., do(pushRight(sokoban,l1_4,l1_5,l1_6,crate_01), 3).
        """
        inside = step[step.find('(')+1 : step.rfind(')')]
        action_str, _ = self._split_step_arguments(inside, expected=2)

        action_name_start = action_str.find('(')
        if action_name_start == -1:
            raise ValueError(f"Incorrect action format: {action_str}")
        action_inside = action_str[action_name_start + 1 : -1]
        _, from_l, to_l, crate_to, _ = self._split_step_arguments(
            action_inside, expected=5
        )

        crate_r, crate_c = self._cell_id_to_coords(to_l)
        crate_to_r, crate_to_c = self._cell_id_to_coords(crate_to)
        self._move_crate(crate_r, crate_c, crate_to_r, crate_to_c)

        from_r, from_c = self._cell_id_to_coords(from_l)
        to_r, to_c = self._cell_id_to_coords(to_l)
        self._move_sokoban(from_r, from_c, to_r, to_c)

    def _apply_move(self, step: str) -> None:
        """
        Applies a move action to the map.

        Args:
            step: Move action literal (e.g., do(move(...), step_num), do(moveRight(...), step_num)).
        """
        start = step.find('(') + 1
        end = step.rfind(')')
        inside = step[start:end]
        action_str, _ = self._split_step_arguments(inside, expected=2)

        action_name_start = action_str.find('(')
        if action_name_start == -1:
            raise ValueError(f"Incorrect action format: {action_str}")
        action_inside = action_str[action_name_start + 1:-1]
        _, from_l, to_l = self._split_step_arguments(action_inside, expected=3)

        from_r, from_c = self._cell_id_to_coords(from_l)
        to_r, to_c = self._cell_id_to_coords(to_l)
        self._move_sokoban(from_r, from_c, to_r, to_c)

    def _move_sokoban(self, from_r: int, from_c: int, to_r: int, to_c: int) -> None:
        """
        Moves Sokoban from one cell to another.

        Args:
            from_r: Starting row.
            from_c: Starting column.
            to_r: Target row.
            to_c: Target column.
        """
        current_symbol = self.map_grid[from_r][from_c]
        if current_symbol not in (self.SYMBOL_SOKOBAN, self.SYMBOL_SOKOBAN_GOAL):
            raise ValueError(f"There is no Sokoban at position ({from_r}, {from_c}).")
        
        # Clear the original cell
        if current_symbol == self.SYMBOL_SOKOBAN:
            self._set_cell(from_r, from_c, ' ')
        elif current_symbol == self.SYMBOL_SOKOBAN_GOAL:
            self._set_cell(from_r, from_c, self.SYMBOL_GOAL)
        
        # Update the target cell
        if self.map_grid[to_r][to_c] == self.SYMBOL_GOAL:
            self.map_grid[to_r][to_c] = self.SYMBOL_SOKOBAN_GOAL
        else:
            self.map_grid[to_r][to_c] = self.SYMBOL_SOKOBAN

    def _move_crate(self, from_r: int, from_c: int, to_r: int, to_c: int) -> None:
        """
        Moves a crate from one cell to another.

        Args:
            from_r: Starting row.
            from_c: Starting column.
            to_r: Target row.
            to_c: Target column.
        """
        current_symbol = self.map_grid[from_r][from_c]
        if current_symbol not in (self.SYMBOL_CRATE, self.SYMBOL_CRATE_GOAL):
            raise ValueError(f"There is no crate at position ({from_r}, {from_c}).")
        
        # Clear the original cell
        if current_symbol == self.SYMBOL_CRATE:
            self._set_cell(from_r, from_c, ' ')
        elif current_symbol == self.SYMBOL_CRATE_GOAL:
            self._set_cell(from_r, from_c, self.SYMBOL_GOAL)
        
        # Update the target cell
        if self.map_grid[to_r][to_c] == self.SYMBOL_GOAL:
            self.map_grid[to_r][to_c] = self.SYMBOL_CRATE_GOAL
        else:
            self.map_grid[to_r][to_c] = self.SYMBOL_CRATE


    def _cell_id_to_coords(self, cell_id: str) -> Tuple[int, int]:
        """
        Converts a cell identifier to row and column coordinates.

        Args:
            cell_id: Cell identifier in string format, e.g., 'l0_1'.

        Returns:
            A tuple of two integers (row, column).

        Raises:
            ValueError: If the cell identifier format is incorrect.
        """
        try:
            if cell_id.startswith('l'):
                cell_id = cell_id[1:]
            row_str, col_str = cell_id.split('_')
            row = int(row_str)
            col = int(col_str)
            return row, col
        except Exception as e:
            raise ValueError(f"Incorrect cell_id format: {cell_id}") from e

    def _split_step_arguments(self, step_str: str, expected: int) -> List[str]:
        """
        Splits step arguments, considering nested parentheses.

        Args:
            step_str: String inside do(push(...)) or do(move(...)).
            expected: Expected number of arguments.

        Returns:
            List of arguments.

        Raises:
            ValueError: If the number of arguments does not match the expected.
        """
        args = []
        current = ''
        depth = 0
        for char in step_str:
            if char == ',' and depth == 0:
                args.append(current.strip())
                current = ''
            else:
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                current += char
        if current:
            args.append(current.strip())
        if len(args) != expected:
            raise ValueError(f"Expected {expected} arguments, got {len(args)} in step: {step_str}")
        return args

    def visualize(self) -> None:
        """
        Prints the current state of the Sokoban map.
        """
        for row in self.map_grid:
            print(''.join(row))

