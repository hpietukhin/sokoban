# test_solver.py

from pathlib import Path

import clingo

from conftest import MapCase
from sokoban_map import SokobanMap
from solver import SokobanSolver


BASE_DIR = Path(__file__).parent
DOMAIN_FILE = BASE_DIR / "sokoban.lp"


def solution_steps(solution: str) -> list[str]:
    return [
        line.split(": ", 1)[1]
        for line in solution.splitlines()
        if line.startswith("Step")
    ]


def reference_steps(map_text: str, plan: str) -> list[str]:
    lines = map_text.splitlines()
    player = next(
        (row, column)
        for row, line in enumerate(lines)
        for column, symbol in enumerate(line)
        if symbol in {"S", "s"}
    )
    box_positions = sorted(
        (row, column)
        for row, line in enumerate(lines)
        for column, symbol in enumerate(line)
        if symbol in {"C", "c"}
    )
    boxes = {
        position: f"crate_{index:02d}"
        for index, position in enumerate(box_positions, start=1)
    }
    directions = {
        "U": (-1, 0, "Up"),
        "D": (1, 0, "Down"),
        "L": (0, -1, "Left"),
        "R": (0, 1, "Right"),
    }
    steps = []

    for time, direction in enumerate(plan):
        row_delta, column_delta, name = directions[direction.upper()]
        target = (player[0] + row_delta, player[1] + column_delta)
        player_cell = f"l{player[0]}_{player[1]}"
        target_cell = f"l{target[0]}_{target[1]}"

        if direction.islower():
            crate_target = (
                target[0] + row_delta,
                target[1] + column_delta,
            )
            crate_name = boxes.pop(target)
            boxes[crate_target] = crate_name
            steps.append(
                f"do(push{name}(sokoban,{player_cell},{target_cell},"
                f"l{crate_target[0]}_{crate_target[1]},{crate_name}), {time})"
            )
        else:
            steps.append(
                f"do(move{name}(sokoban,{player_cell},{target_cell}), {time})"
            )
        player = target

    return steps


def test_map_encoding_preserves_coordinates(map_case: MapCase) -> None:
    map_text = map_case.path.read_text()
    facts = SokobanSolver(str(DOMAIN_FILE)).generate_facts_from_map(map_text)

    players = [
        (row, column)
        for row, line in enumerate(map_text.splitlines())
        for column, symbol in enumerate(line)
        if symbol in {"S", "s"}
    ]

    assert len(players) == 1
    row, column = players[0]
    assert f"at(sokoban, l{row}_{column}, 0)." in facts


def test_asp_accepts_each_reference_outcome(map_case: MapCase) -> None:
    map_text = map_case.path.read_text()
    solver = SokobanSolver(str(DOMAIN_FILE))

    if map_case.reference_plan is None:
        solution = SokobanSolver(
            domain_asp_file=str(DOMAIN_FILE),
            max_steps=map_case.search_limit,
            optimize=False,
        ).solve(map_text)
        assert solution == (
            f"No solution found within {map_case.search_limit} steps"
        )
        return

    steps = reference_steps(map_text, map_case.reference_plan)
    control = clingo.Control(
        ["--models=1", "--opt-mode=ignore", "--const", f"maxsteps={len(steps)}"]
    )
    control.load(str(DOMAIN_FILE))
    control.add("base", [], solver.generate_facts_from_map(map_text))
    control.add("reference", [], "\n".join(f"{step}." for step in steps))
    control.ground([("base", []), ("reference", [])])

    assert control.solve().satisfiable
    board = SokobanMap(map_text)
    for step in steps:
        board.apply_step(step)
    assert board.is_solved()


def test_solver_reports_when_limit_is_too_low() -> None:
    map_text = (BASE_DIR / "maps" / "map7.txt").read_text()

    solution = SokobanSolver(
        domain_asp_file=str(DOMAIN_FILE),
        max_steps=20,
        optimize=False,
    ).solve(map_text)

    assert solution == "No solution found within 20 steps"
