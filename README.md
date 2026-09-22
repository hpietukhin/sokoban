
# README

## Sokoban solver and visualizer

### Overview

This project provides a solution to the classic Sokoban puzzle using Answer Set Programming (ASP) with Clingo. It includes a Python-based graphical user interface (GUI) that allows users to load Sokoban maps, solve them, and visualize the solution steps.

### Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Directory Structure](#directory-structure)
- [Usage](#usage)
  - [Running the Solver](#running-the-solver)
  - [Using the Visualizer](#using-the-visualizer)
- [Control Switches](#control-switches)
- [Sample Input and Output](#sample-input-and-output)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

### Prerequisites

Ensure that you have the following installed on your system:

- **Python 3.7 or higher**
- **Clingo ASP Solver**
- **pip** (Python package installer)

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/sokoban-asp-solver.git
   cd sokoban-asp-solver
   ```

2. **Install Python Dependencies**

   It's recommended to use a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install Clingo**

   Follow the installation instructions from the [Clingo website](https://potassco.org/clingo/).

### Directory Structure

```
sokoban-asp-solver/
├── maps/
│   ├── map1.txt
│   ├── map2.txt
│   └── ...
├── expected/
│   ├── expected1.txt
│   ├── expected2.txt
│   └── ...
├── maps_out/
│   └── generated_map1.txt
├──sokoban_map.py
├── conftest.py
├── test_solver.py
├── solver.py
└── visualizer.py
├── sokoban.lp
├── requirements.txt
├── README.md
└── Documentation.md
```

### Usage

#### Running the solver

To solve a Sokoban puzzle using the ASP solver:

```bash
python solver.py sokoban.lp maps/map1.txt --max_steps=50
```

**Arguments:**

- `sokoban.lp`: Path to the ASP domain rules file.
- `maps/map1.txt`: Path to the Sokoban map file.
- `--max_steps`: (Optional) Maximum number of steps to search for a solution. Default is 50.

**Example:**

```bash
python solver.py sokoban.lp maps/map1.txt --max_steps=30
```

**Output:**

```
Solving Sokoban on map map1.txt

Solution steps:
do(moveRight(sokoban,l1_2,l1_3), 1)
do(pushRight(sokoban,l1_3,l1_4,l1_5,crate_01), 2)
...

initial map state:
#########
#S  C  X#
#########

After step 1: moveRight(sokoban,l1_2,l1_3)
#########
# S C  X#
#########

After step 2: pushRight(sokoban,l1_3,l1_4,l1_5,crate_01)
#########
#  S C X#
#########
```

#### Using the Visualizer

To launch the GUI visualizer:

```bash
python visualizer.py
```

**Features:**

- **Map Selection:** Choose from available Sokoban maps.
- **Run Test:** Solve the selected map and visualize the solution.
- **Visualization:** Step through each move to see the Sokoban puzzle being solved.
- **ASP Map Display:** View the generated ASP facts for the selected map.
- **Pytest Output:** Review test results and solver output. All generated maps are stored in maps_out folder. You can provide them as a second argument for clingo directly:
```bash
clingo sokoban.lp maps/map1.txt -c max_steps=10
```  
but python solver does essentialy same thing:  
```bash
python solver.py sokoban.lp maps/map1.txt --max_steps=10
```

### Control Switches

- `--map=<map_file>`: Specify a single map to test (e.g., `--map=map1.txt`). If not provided, all maps are tested.
(by commenting out tests from get_test_cases in conftest.py you can force to run several selected tests with "pytest" command)

### Sample Input and Output

**Sample Map (`maps/map4.txt`):**

```
#########
#S  C  X#
#########
```

**Running the Solver:**

```bash
python solver.py sokoban.lp maps/map1.txt --max_steps=10
```

**Sample Output:**

```
Solving Sokoban on map map1.txt

Solution steps:
do(moveRight(sokoban,l1_2,l1_3), 1)
do(pushRight(sokoban,l1_3,l1_4,l1_5,crate_01), 2)

initial map state:
#########
#S  C  X#
#########

After step 1: moveRight(sokoban,l1_2,l1_3)
#########
# S C  X#
#########

After step 2: pushRight(sokoban,l1_3,l1_4,l1_5,crate_01)
#########
#  S C X#
#########
```

### Testing

The project includes automated tests using `pytest`. To run the tests:

```bash
pytest test_solver.py --map=map1.txt --tb=short -v -s
```

**Options:**

- `--map=<map_file>`: Run tests for a specific map. If omitted, all maps are tested.  
Note: On basic maps like map #1, #8, #4-#6 the encoding finds an optimal plan in a fraction of a second. Maps #2, #3 and #7 are the hard ones — they need a larger step horizon and the optimizer spends most of its time proving optimality (e.g. map #2 at 20 steps used to take ~27s just to prove UNSAT).

### Performance: streamliner constraints

Following the *"Streamliners for Answer Set Programming"* approach ([arXiv:2604.19251](https://arxiv.org/abs/2604.19251); [paper code on Zenodo](https://zenodo.org/records/18378760)), the hard maps are sped up by adding **streamliner constraints** — symmetry-breaking / implied constraints that prune the search space without removing any optimal solution.

A gap-free-prefix symmetry break is now built into `sokoban.lp` (actions may only occupy a contiguous prefix `0,1,2,…` of the horizon, so idle steps can only be a suffix):

```prolog
:- do(_,T), T > 0, not do(_,T-1).
```

Measured effect (optimal plan length unchanged everywhere):

| map | horizon | base | with streamliner |
| --- | --- | --- | --- |
| map7 (SAT) | 32 | 1.86s | **0.60s** (−68%) |
| map2 (UNSAT proof) | 20 | 27.0s | **17.8s** (−34%) |
| map1/4/5/6/8 | 20 | fast | faster / equal |

Additional, *instance-dependent* streamliners live in `streamliners/` and can be layered on top of the base encoding (this mirrors the paper's *virtual best encoding*: no single variant is fastest on every instance):

- `contiguous.lp` — the gap-free prefix break (already baked into `sokoban.lp`).
- `stopatgoal.lp` — `:- do(_,T), goal_achieved(T).` Much faster at *finding* plans on SAT maps (map7: ~0.38s), but *slower* at proving UNSAT, so it is kept optional.
- `norev.lp` — forbids immediately reversing a sokoban move; measurably hurt UNSAT proving, kept for reference only.
- `recommended.lp` — `contiguous` + `stopatgoal` combined.

Benchmark any combination with `bench.py`:

```bash
uv run --with clingo==5.7.1 python bench.py streamliners/stopatgoal.lp \
    --maps map7.txt,map2.txt --steps 32 --timeout 90
```
