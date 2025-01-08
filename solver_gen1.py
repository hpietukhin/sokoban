import clingo
import argparse

def generate_sokoban_lp_from_map(map_str, max_steps: int = 20):
    """
    Принимает карту Sokoban в виде строк (с символами #, S, C, X, s, c),
    и возвращает строку с фактами ASP (в формате .lp)
    """
    lines = map_str.splitlines()
    # Удалим пустые строчки и ведущие/хвостовые пробелы
    lines = [ln.strip() for ln in lines if ln.strip() != ""]

    def cell_name(r, c):
        # Генерируем имя клетки как pos_{column+1}_{row+1}
        return f"pos_{c+1}_{r+1}"

    facts = []
    
    # Фиксированные имена объектов
    facts.append("player(player_01).")
    
    # Для хранения позиций
    player_pos = None
    stone_positions = []  # список всех позиций камней
    free_cells = []  # клетки, не являющиеся стенами
    goal_cells = []  # клетки-цели
    wall_cells = []  # клетки-стены

    all_possible_positions = set() 
    rows = len(lines)
    for r in range(rows):
        for c in range(len(lines[r])):
            all_possible_positions.add((r, c))

    # Парсим карту
    for r in range(len(lines)):
        for c in range(len(lines[r])):
            ch = lines[r][c]
            
            # Собираем стены для добавления их в isnongoal
            if ch == '#':
                wall_cells.append((r, c))
                continue
                
            # Это "свободная" клетка
            free_cells.append((r, c))
            
            if ch in ('X', 's', 'c'):
                goal_cells.append((r, c))
            if ch in ('S', 's'):
                player_pos = (r, c)
            if ch in ('C', 'c'):
                stone_positions.append((r, c))

    # Добавляем факты для каждого камня
    for i, pos in enumerate(stone_positions, 1):
        stone_name = f"stone_{str(i).zfill(2)}"  # stone_01, stone_02, etc.
        facts.append(f"stone({stone_name}).")

    # Добавляем isgoal/isnongoal, включая стены
    all_cells = free_cells + wall_cells
    cells_with_goal_facts = set()
    for (r, c) in all_cells:
        cell = cell_name(r, c)
        if (r, c) in goal_cells:
            facts.append(f"isgoal({cell}).")
        else:
            facts.append(f"isnongoal({cell}).")
            if (r,c) in wall_cells:
               pass #print (f"adding wall cell {(r+1,c+1)}")
        cells_with_goal_facts.add((r,c))
    
    assert cells_with_goal_facts == all_possible_positions, \
    f"Missing isgoal/isnongoal facts for positions: {all_possible_positions - cells_with_goal_facts}"

    # Добавляем цель для каждого камня
    for i in range(1, len(stone_positions) + 1):
        stone_name = f"stone_{str(i).zfill(2)}"
        facts.append(f"goal({stone_name}).")

    # Добавляем начальную позицию игрока
    if player_pos:
        facts.append(f"at(player_01,{cell_name(*player_pos)}).")

    # Добавляем начальные позиции всех камней
    for i, pos in enumerate(stone_positions, 1):
        stone_name = f"stone_{str(i).zfill(2)}"
        facts.append(f"at({stone_name},{cell_name(*pos)}).")

    # Отмечаем свободные клетки
    occupied = set()
    if player_pos:
        occupied.add(player_pos)
    occupied = occupied.union(set(stone_positions))
    for (r, c) in free_cells:
        if (r, c) not in occupied:
            facts.append(f"clear({cell_name(r,c)}).")

    # Добавляем горизонтальные и вертикальные перемещения между свободными клетками
    for (r, c) in free_cells:
        for (dr, dc, dname) in [(0,1,"dir_right"), (0,-1,"dir_left"),
                               (-1,0,"dir_down"), (1,0,"dir_up")]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in free_cells:
                facts.append(f"movedir({cell_name(r,c)},{cell_name(nr,nc)},{dname}).")
    
     # Add step facts
    facts.append(f"#const maxsteps = {max_steps}.")
    facts.extend(f"step({i})." for i in range(1, max_steps + 1))

    return "\n".join(facts)


def run_and_format_solution(domain_asp_file: str, map_str: str, max_steps: int = 20) -> str:
    """
    Runs the Sokoban solver using Clingo and formats its output.
    
    Args:
        domain_asp_file: Path to the ASP logic file with Sokoban rules
        map_str: Input map string
        max_steps: Maximum number of steps for solution
        
    Returns:
        Formatted string with solution steps or message if no solution found
    """
    
    def on_model(model):
        nonlocal solution_found, solution_steps
        solution_found = True
        print("Found solution:", model)  # Print raw model for debugging
        # Get all symbolic atoms from the model
        atoms = [str(atom) for atom in model.symbols(shown=True)]
        # Filter only movement predicates
        moves = [atom for atom in atoms if any(
            atom.startswith(pred) for pred in ['move', 'pushtogoal', 'pushtonongoal']
        )]
        solution_steps.extend(moves)

    # Initialize solution tracking
    solution_found = False
    solution_steps = []
    
    # Set up Clingo control
    ctl = clingo.Control()
    ctl.configuration.solve.models = 1  # Find first model
    
    print("Solving Sokoban...\n")
    print(f"encoder file:\n {domain_asp_file}")
    print(f"instance:\n {map_str}")
    
    try:
        # 1. Load domain (Sokoban rules)
        ctl.load(domain_asp_file)
        
        # 2. Generate facts from map
        instance_lp = generate_sokoban_lp_from_map(map_str, max_steps=max_steps)
        
        # 3. Add facts as base part
        ctl.add("base", [], instance_lp)
        
        # 4. Ground
        ctl.ground([("base", [])])
        
        # 5. Run solver
        result = ctl.solve(on_model=on_model)
        print("Solving finished with:", result)
        
        if not solution_found:
            return "No solution found"
        
        # Parse steps and sort them
        step_dict = {}
        for step in solution_steps:
            # Extract step number from the end of the predicate
            step_num = int(step.split(',')[-1].rstrip(').'))
            step_dict[step_num] = step
        
        # Format output
        formatted_solution = []
        formatted_solution.append(f"Solution found in {max(step_dict.keys())} steps:")
        for step_num in sorted(step_dict.keys()):
            action = step_dict[step_num]
            # Make it more readable by adding spaces after commas
            action = action.replace(',', ', ').replace('  ', ' ')
            formatted_solution.append(f"Step {step_num}: {action}")
        
        return "\n".join(formatted_solution)
        
    except Exception as e:
        return f"Error solving map: {str(e)}"


    
