# test_solver.py

import re
from asp_validator import validate_asp_encoding  # Ensure this module is available
import pytest
import difflib
from typing import Dict, Set, List, Tuple
from tabulate import tabulate
import os

from solver import SokobanSolver, SokobanMap  # Updated import to reflect class-based structure


# Directories for maps and expected outputs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPS_DIR = os.path.join(BASE_DIR, 'maps')
EXPECTED_DIR = os.path.join(BASE_DIR, 'expected')
MAPS_OUT_DIR = os.path.join(BASE_DIR, 'maps_out')


def read_file(file_path: str) -> str:
    """Reads the content of a file and returns it as a string."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def format_facts_by_type(facts: Set[str]) -> str:
    """Groups facts by predicates and formats them for output."""
    facts_by_type: Dict[str, List[str]] = {}
    for fact in facts:
        predicate = fact.split('(')[0]
        facts_by_type.setdefault(predicate, []).append(fact)

    result = []
    for predicate, fact_list in sorted(facts_by_type.items()):
        result.append(f"\n{predicate} facts:")
        result.extend(f"  {fact}" for fact in sorted(fact_list))
    return '\n'.join(result)


def compare_facts_side_by_side(expected: Set[str], actual: Set[str]) -> str:
    """
    Compares expected and actual facts and returns a table with their comparison.
    Missing facts are marked as 'Missing', extra facts as 'Extra'.
    """
    common_facts = expected.intersection(actual)
    missing_facts = sorted(expected - actual)
    extra_facts = sorted(actual - expected)

    table: List[Tuple[str, str, str]] = []

    for fact in sorted(common_facts):
        table.append((fact, fact, ""))
    for fact in missing_facts:
        table.append((fact, "", "Missing"))
    for fact in extra_facts:
        table.append(("", fact, "Extra"))

    header = ["Expected", "Actual", "Status"]
    table_str = tabulate(table, headers=header, tablefmt="grid", stralign="left")

    return table_str


def compare_facts_detailed(expected: str, actual: str) -> str:
    """
    Compares expected and actual facts, sorted, and returns a detailed diff with line lengths.
    """
    expected_lines = sorted(line.strip() for line in expected.strip().splitlines() if line.strip())
    actual_lines = sorted(line.strip() for line in actual.strip().splitlines() if line.strip())

    diff = difflib.unified_diff(
        expected_lines, actual_lines,
        fromfile='expected', tofile='actual',
        lineterm=''
    )

    diff_output = []
    for line in diff:
        if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
            diff_output.append(line)
        elif line.startswith('+') or line.startswith('-'):
            fact = line[1:].strip()
            diff_output.append(f"{line} (length: {len(fact)})")
        else:
            fact = line.strip()
            diff_output.append(f"{line} (length: {len(fact)})")
    return "\n".join(diff_output)



def test_generate_sokoban_lp(map_file: str, expected_file: str) :
    """
    Parameterized test for the SokobanSolver's generate_facts_from_map method,
    which checks various maps and their expected ASP facts.
    """
    map_path = os.path.join(MAPS_DIR, map_file)
    #expected_path = os.path.join(EXPECTED_DIR, expected_file)

    map_str = read_file(map_path)
    #expected_output = read_file(expected_path)

    solver = SokobanSolver(domain_asp_file=os.path.join(BASE_DIR, "sokoban.lp"))
    actual_output = solver.generate_facts_from_map(map_str) 

    os.makedirs(MAPS_OUT_DIR, exist_ok=True)

    generated_map_path = os.path.join(MAPS_OUT_DIR, f"generated_{map_file}")
    try:
        SokobanMap.write_map_file(generated_map_path, actual_output)
    except Exception as e:
        pytest.fail(f"Failed to write generated map file: {e}")

    # def filter_facts(output: str) -> Set[str]:
    #     """Filters out lines starting with 'step(' and '#const maxsteps'."""
    #     return set(
    #         line.strip() for line in output.strip().split('\n')
    #         if line.strip() and not (line.strip().startswith("step(") or line.strip().startswith("#const maxsteps"))
    #     )

    # expected_facts = filter_facts(expected_output)
    # actual_facts = filter_facts(actual_output)

    # assert expected_facts == actual_facts, (
    #     f"\nTest failed for {map_file}! Differences found:\n\n"
    #     f"{compare_facts_side_by_side(expected_facts, actual_facts)}"
    # )
    # print("MAP GENERATED CORRECTLY")

    # Run solver and print solution
    print(f"\nSolving Sokoban on map {map_file}\n")
    solution = solver.solve(map_str)
    print("\nSolution steps:")
    print(solution)

    # Parse solution steps
    solution_steps = [line for line in solution.splitlines() if line.startswith("Step")]
    solution_steps = [line.split(": ", 1)[1] for line in solution_steps]

    # Visualize solution
    map_obj = SokobanMap(map_str)
    print("\ninitial map state:")
    print(map_str)

    for i, step in enumerate(solution_steps):
        map_obj.apply_step(step)
        print(f"\nAfter step {i}: {step}")
        map_obj.visualize()
