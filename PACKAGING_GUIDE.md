# Complete Guide: Converting Autoguess to a pip-installable Package

## Executive Summary

**Status:** ✅ **FEASIBLE** - Autoguess can be successfully packaged as a pip-installable package.

**Key Enabler:** The [passagemath project](https://github.com/passagemath/passagemath) now provides SageMath as modularized pip-installable packages, making it possible to include SageMath as a standard Python dependency.

---

## Current Dependency Analysis

### Python Dependencies (pip-installable)
- ✅ `python-sat[pblib,aiger]` - SAT solver (PySAT)
- ✅ `pysmt` - SMT solver interface
- ✅ `z3-solver` - Z3 SMT solver
- ✅ `minizinc` - Python interface to MiniZinc
- ✅ `graphviz` - Graph visualization library
- ✅ `dot2tex` - LaTeX graph rendering
- ⚠️  `gurobipy` - Gurobi optimizer (commercial, but pip-installable)

### System Dependencies
- ✅ **SageMath** - NOW available via passagemath pip packages
- ✅ MiniZinc - Has Python package with bundled solver
- ✅ Graphviz - Python package available (pure Python or with binary wheels)
- ✅ OR-Tools - Available as pip package

### License Considerations
- **Autoguess**: MIT License ✅
- **Most dependencies**: Open source (MIT, Apache, BSD)
- **Gurobi**: Commercial with free academic licenses
  - Users need to install license separately
  - `gurobipy` package is freely installable
  - Can be made an optional dependency

---

## Step-by-Step Implementation Plan

### Phase 1: Project Structure Setup

#### 1.1 Create `pyproject.toml` (Modern Python Packaging)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "autoguess"
version = "1.0.0"
authors = [
    {name = "Hosein Hadipour", email = "hsn.hadipour@gmail.com"}
]
description = "A generic tool for solving the guess-and-determine problem using CP, MILP, SAT, SMT, and algebraic methods"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
keywords = ["cryptanalysis", "constraint-programming", "milp", "sat", "smt", "groebner-basis", "guess-and-determine"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Mathematics",
    "Topic :: Security :: Cryptography",
]

dependencies = [
    "python-sat[pblib,aiger]>=0.1.7",
    "pysmt>=0.9.5",
    "z3-solver>=4.8.0",
    "minizinc>=0.9.0",
    "graphviz>=0.20",
    "passagemath-symbolics>=10.6",  # Core SageMath functionality for symbolic operations
    "passagemath-polyhedra>=10.6",  # For polynomial operations
]

[project.optional-dependencies]
# Gurobi is optional - users with academic licenses can install it
gurobi = [
    "gurobipy>=11.0",
]

# Full installation with all optional dependencies
full = [
    "gurobipy>=11.0",
    "dot2tex>=2.11",
]

# Development dependencies
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "flake8>=6.0",
    "mypy>=1.0",
    "sphinx>=5.0",
    "sphinx-rtd-theme>=1.0",
]

[project.urls]
Homepage = "https://github.com/hadipourh/autoguess"
Documentation = "https://github.com/hadipourh/autoguess/blob/main/README.md"
Repository = "https://github.com/hadipourh/autoguess"
Issues = "https://github.com/hadipourh/autoguess/issues"

[project.scripts]
autoguess = "autoguess.cli:main"

[tool.setuptools]
packages = ["autoguess", "autoguess.core"]

[tool.setuptools.package-data]
autoguess = ["configfiles/*.msc"]

[tool.black]
line-length = 100
target-version = ['py310']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

#### 1.2 Reorganize Project Structure

**Current Structure:**
```
autoguess/
├── autoguess.py          # Main script
├── config.py             # Configuration
├── core/                 # Core modules
│   ├── gdcp.py
│   ├── gdmilp.py
│   ├── gdsat.py
│   ├── gdsmt.py
│   ├── gdgroebner.py
│   ├── ...
├── ciphers/              # Example cipher files
├── configfiles/          # Configuration files
└── requirements.txt
```

**New Package Structure:**
```
autoguess/
├── pyproject.toml        # NEW: Modern packaging configuration
├── setup.py              # NEW: Minimal setup.py for compatibility
├── README.md
├── LICENSE.txt
├── MANIFEST.in           # NEW: Include non-Python files
├── autoguess/            # NEW: Main package directory
│   ├── __init__.py       # NEW: Package initialization
│   ├── __version__.py    # NEW: Version information
│   ├── cli.py            # NEW: Command-line interface (renamed from autoguess.py)
│   ├── config.py         # MOVED: Configuration
│   ├── core/             # MOVED: Core modules
│   │   ├── __init__.py   # NEW: Core package init
│   │   ├── gdcp.py
│   │   ├── gdmilp.py
│   │   ├── gdsat.py
│   │   ├── gdsmt.py
│   │   ├── gdgroebner.py
│   │   ├── ...
│   ├── configfiles/      # MOVED: Configuration files
│   └── utils/            # NEW: Utility functions
│       ├── __init__.py
│       └── helpers.py
├── examples/             # RENAMED from ciphers/
│   ├── AES/
│   ├── ChaCha/
│   └── ...
├── tests/                # NEW: Test directory
│   ├── __init__.py
│   ├── test_basic.py
│   ├── test_cp.py
│   ├── test_sat.py
│   └── ...
└── docs/                 # NEW: Documentation
    ├── conf.py
    └── index.rst
```

### Phase 2: Code Modifications

#### 2.1 Create `autoguess/__init__.py`

```python
"""
Autoguess: A generic tool for solving the guess-and-determine problem.

This package provides tools for automated guess-and-determine and key-bridging
techniques using constraint programming, MILP, SAT, SMT solvers, and algebraic
methods based on Groebner basis computation.
"""

from autoguess.__version__ import __version__
from autoguess.core import search

__all__ = [
    '__version__',
    'search',
]

# Check for optional dependencies and warn if missing
def _check_optional_dependencies():
    """Check for optional dependencies and provide helpful messages."""
    warnings = []
    
    try:
        import gurobipy
    except ImportError:
        warnings.append(
            "Gurobi (gurobipy) not found. MILP-based solving will not be available. "
            "Install with: pip install autoguess[gurobi]"
        )
    
    try:
        import dot2tex
    except ImportError:
        warnings.append(
            "dot2tex not found. LaTeX graph rendering will not be available. "
            "Install with: pip install autoguess[full]"
        )
    
    return warnings

# Store warnings to show on first import
_optional_warnings = _check_optional_dependencies()
```

#### 2.2 Create `autoguess/__version__.py`

```python
"""Version information for autoguess."""

__version__ = "1.0.0"
```

#### 2.3 Create `autoguess/cli.py` (renamed from `autoguess.py`)

```python
#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Command-line interface for Autoguess.

Created on Aug 23, 2020
@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com
"""

from autoguess.core import search
from argparse import ArgumentParser, RawTextHelpFormatter
import os
from autoguess.config import TEMP_DIR
import minizinc
from pysat import solvers


def start_search(params):
    """Start the search tool for the given parameters."""
    solver = params["solver"]
    search_methods = {
        'milp': search.search_using_milp,
        'sat': search.search_using_sat,
        'smt': search.search_using_smt,
        'cp': search.search_using_cp,
        'groebner': search.search_using_groebnerbasis,
        'mark': search.search_using_mark,
        'elim': search.search_using_elim
    }

    if solver in search_methods:
        # Check if Gurobi is available for MILP
        if solver == 'milp':
            try:
                import gurobipy
            except ImportError:
                print("ERROR: Gurobi (gurobipy) is required for MILP solving.")
                print("Install with: pip install autoguess[gurobi]")
                print("Note: You also need a valid Gurobi license.")
                return
        
        search_methods[solver](params)
    else:
        print('Choose the solver from the following options: cp, milp, sat, smt, groebner, mark, elim')


def check_environment():
    """Basic checks if the environment is set up correctly."""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)


def load_parameters(args):
    """Get parameters from the argument list and input file."""
    params = {
        "inputfile": "./examples/Example4/algebraic_relations.txt",
        "outputfile": "output",
        "maxguess": 50,
        "maxsteps": 5,
        "solver": 'cp',
        "milpdirection": 'min',
        "timelimit": -1,
        "cpsolver": "cp-sat",
        "satsolver": 'cadical153',
        "smtsolver": 'z3',
        "cpoptimization": 1,
        "tikz": 0,
        "preprocess": 1,
        "D": 2,
        "term_ordering": 'degrevlex',
        "overlapping_number": 2,
        "cnf_to_anf_conversion": 'simple',
        "dglayout": "dot",
        "log": 1
    }

    for key in params:
        if getattr(args, key, None):
            params[key] = getattr(args, key)[0]

    return params


def main():
    """Parse the arguments and start the request functionality."""
    parser = ArgumentParser(
        description="This tool automates the Guess-and-Determine and Key-Bridging techniques "
                   "using a variety of CP, MILP, SMT and SAT solvers, as well as "
                   "the algebraic method based on Groebner basis",
        formatter_class=RawTextHelpFormatter
    )
    
    parser.add_argument('-i', '--inputfile', nargs=1, 
                       help="Use an input file in plain text format")
    parser.add_argument('-o', '--outputfile', nargs=1, 
                       help="Use an output file to write the output into it")
    parser.add_argument('-mg', '--maxguess', nargs=1, type=int, 
                       help="An upper bound for the number of guessed variables")
    parser.add_argument('-ms', '--maxsteps', nargs=1, type=int, 
                       help="An integer number specifying the depth of search")
    parser.add_argument('-s', '--solver', nargs=1, 
                       choices=['cp', 'milp', 'sat', 'smt', 'groebner'], 
                       help="Solver choice")
    parser.add_argument('-milpd', '--milpdirection', nargs=1, 
                       choices=['min', 'max'], 
                       help="MILP direction")
    parser.add_argument('-cps', '--cpsolver', nargs=1, type=str,
                       choices=[solver_name for solver_name in minizinc.default_driver.available_solvers().keys()],
                       help="CP solver choice", default=["cp-sat"])
    parser.add_argument('-sats', '--satsolver', nargs=1, type=str,
                       choices=[solver for solver in solvers.SolverNames.__dict__.keys() 
                               if not solver.startswith('__')],
                       help="SAT solver choice")
    parser.add_argument('-smts', '--smtsolver', nargs=1, type=str,
                       choices=['msat', 'cvc4', 'z3', 'yices', 'bdd'],
                       help="SMT solver choice")
    parser.add_argument('-cpopt', '--cpoptimization', nargs=1, type=int,
                       choices=[0, 1], help="CP optimization")
    parser.add_argument('-tl', '--timelimit', nargs=1, type=int,
                       help="Time limit for the search in seconds")
    parser.add_argument('-tk', '--tikz', nargs=1, type=int,
                       help="Generate the tikz code of the determination flow graph")
    parser.add_argument('-prep', '--preprocess', nargs=1, type=int,
                       help="Enable the preprocessing phase")
    parser.add_argument('-D', '--D', nargs=1, type=int,
                       help="Degree of Macaulay matrix generated in preprocessing phase")
    parser.add_argument('-tord', '--term_ordering', nargs=1, type=str,
                       help="Term ordering such as 'degrevlex' or 'deglex'")
    parser.add_argument('-oln', '--overlapping_number', nargs=1, type=int,
                       help="Overlapping number in block-wise CNF to ANF conversion")
    parser.add_argument('-cnf2anf', '--cnf_to_anf_conversion', nargs=1, type=str,
                       choices=['simple', 'blockwise'],
                       help="CNF to ANF conversion method")
    parser.add_argument('-dgl', '--dglayout', nargs=1, type=str,
                       choices=["dot", "circo", "twopi", "fdp", "neato", "nop", 
                               "nop1", "nop2", "osage", "patchwork", "sfdp"],
                       help="Layout of determination flow graph")
    parser.add_argument('-log', '--log', nargs=1, type=int,
                       choices=[0, 1],
                       help="Store intermediate generated files and results", default=[0])

    args = parser.parse_args()
    params = load_parameters(args)

    check_environment()
    start_search(params)


if __name__ == '__main__':
    main()
```

#### 2.4 Update `autoguess/config.py`

```python
"""Configuration settings for Autoguess."""

import os
import platform
import subprocess
import sys


def find_sage_path():
    """
    Automatically detect SageMath installation path.
    
    Note: With passagemath, SageMath is available as a Python package,
    so this function is primarily for backwards compatibility.
    """
    # Check if we're in a passagemath environment
    try:
        import sage
        # If sage imports successfully, we're using passagemath
        # Return a dummy path to indicate it's available as a package
        return "passagemath"
    except ImportError:
        pass
    
    # Fallback to traditional SageMath detection
    common_paths = []
    
    system = platform.system()
    if system == "Darwin":  # macOS
        common_paths = [
            '/usr/local/bin/sage',
            '/opt/homebrew/bin/sage',
            '/Applications/SageMath.app/Contents/MacOS/sage',
            '/Applications/SageMath/sage',
        ]
    elif system == "Linux":
        common_paths = [
            '/usr/bin/sage',
            '/usr/local/bin/sage',
            '/opt/sage/sage',
        ]
    elif system == "Windows":
        common_paths = [
            'C:\\Program Files\\SageMath\\sage.exe',
            'C:\\SageMath\\sage.exe',
        ]
    
    # First try to find sage in PATH
    try:
        result = subprocess.run(['which', 'sage'], 
                              capture_output=True, text=True, check=True)
        sage_path = result.stdout.strip()
        if os.path.isfile(sage_path):
            return sage_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # If not in PATH, check common installation paths
    for path in common_paths:
        if os.path.isfile(path):
            return path
    
    # If still not found, return None (passagemath will be used)
    return None


# Automatically detect SageMath path
PATH_SAGE = find_sage_path()

# Temp directory for intermediate files
TEMP_DIR = os.path.join(os.path.expanduser('~'), '.autoguess', 'temp')

# Create temp directory if it doesn't exist
os.makedirs(TEMP_DIR, exist_ok=True)
```

#### 2.5 Update `autoguess/core/gdgroebner.py` to use passagemath

```python
"""
Reduce Guess-and-Determine problem to Groebner basis computation.

This module uses SageMath (via passagemath) to solve the guess-and-determine
problem using algebraic methods.
"""

# Import from passagemath (works whether installed via pip or traditional SageMath)
try:
    from sage.all import *
    from sage.rings.polynomial.multi_polynomial_sequence import PolynomialSequence
except ImportError as e:
    raise ImportError(
        "SageMath is required for Groebner basis computation. "
        "Install with: pip install passagemath-symbolics passagemath-polyhedra"
    ) from e

# Rest of the code remains the same...
```

#### 2.6 Create `setup.py` (Minimal for backwards compatibility)

```python
"""
Minimal setup.py for backwards compatibility.

Modern packaging uses pyproject.toml. This file is provided for
compatibility with older tools.
"""

from setuptools import setup

# Read version from __version__.py
with open('autoguess/__version__.py') as f:
    exec(f.read())

setup(
    version=__version__
)
```

#### 2.7 Create `MANIFEST.in`

```
# Include important files in the distribution
include README.md
include LICENSE.txt
include pyproject.toml
include requirements.txt

# Include configuration files
recursive-include autoguess/configfiles *.msc

# Include examples
recursive-include examples *.py *.txt

# Exclude unnecessary files
global-exclude __pycache__
global-exclude *.py[co]
global-exclude .git*
global-exclude .DS_Store
```

### Phase 3: Documentation Updates

#### 3.1 Update README.md

Add a new installation section at the top:

````markdown
## Installation

### Quick Install (Recommended)

Install autoguess directly from PyPI:

```bash
pip install autoguess
```

For full functionality including Gurobi support:

```bash
pip install autoguess[full]
```

**Note about Gurobi:** Gurobi is a commercial optimizer with free academic licenses. 
If you plan to use MILP-based solving:

1. Install Gurobi: `pip install autoguess[gurobi]`
2. Obtain a license from [Gurobi](https://www.gurobi.com/academia/academic-program-and-licenses/)
3. Activate your license following Gurobi's instructions

### Install from Source

```bash
git clone https://github.com/hadipourh/autoguess.git
cd autoguess
pip install -e .
```

### Verify Installation

```bash
autoguess --help
```

Or in Python:

```python
import autoguess
print(autoguess.__version__)
```

## Quick Start

```bash
# Run with an example
autoguess -i examples/Example1/relationfile.txt -s cp -ms 5

# Or using Python API
python -c "from autoguess import search; search.search_using_cp({'inputfile': 'examples/Example1/relationfile.txt', 'maxsteps': 5})"
```
````

### Phase 4: Testing Infrastructure

#### 4.1 Create `tests/test_basic.py`

```python
"""Basic tests for autoguess package."""

import pytest
import autoguess


def test_import():
    """Test that the package imports correctly."""
    assert autoguess.__version__


def test_version():
    """Test version string format."""
    version = autoguess.__version__
    assert isinstance(version, str)
    assert len(version.split('.')) >= 2


def test_optional_dependency_check():
    """Test optional dependency checking."""
    warnings = autoguess._check_optional_dependencies()
    assert isinstance(warnings, list)


def test_sage_availability():
    """Test that SageMath (passagemath) is available."""
    try:
        from sage.all import ZZ
        assert ZZ is not None
    except ImportError:
        pytest.skip("SageMath (passagemath) not installed")
```

#### 4.2 Create `tests/test_cp.py`

```python
"""Tests for constraint programming solver."""

import pytest
import os
from autoguess.core import search


@pytest.fixture
def sample_input_file(tmp_path):
    """Create a sample input file for testing."""
    content = """
# Sample test file
algebraic relations
X1 + X2
connection relations
X1, X2
known
X1
target
X2
end
"""
    input_file = tmp_path / "test_input.txt"
    input_file.write_text(content)
    return str(input_file)


def test_cp_solver_basic(sample_input_file):
    """Test basic CP solver functionality."""
    params = {
        'inputfile': sample_input_file,
        'outputfile': 'test_output',
        'maxguess': 10,
        'maxsteps': 3,
        'cpsolver': 'cp-sat',
        'cpoptimization': 1,
        'tikz': 0,
        'preprocess': 1,
        'D': 2,
        'dglayout': 'dot',
        'log': 0,
        'timelimit': -1
    }
    
    # This should not raise an exception
    try:
        search.search_using_cp(params)
    except Exception as e:
        pytest.fail(f"CP solver failed: {e}")
```

### Phase 5: Publishing Preparation

#### 5.1 Create `.gitignore` updates

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
autoguess_env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Autoguess specific
temp/
.autoguess/
output/
*.log

# Distribution
*.whl
```

#### 5.2 Create `CONTRIBUTING.md`

```markdown
# Contributing to Autoguess

Thank you for your interest in contributing to Autoguess!

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install in development mode with all dependencies:
   ```bash
   pip install -e ".[dev,full]"
   ```

## Running Tests

```bash
pytest tests/
```

## Code Style

We use Black for code formatting:
```bash
black autoguess/
```

## Submitting Changes

1. Create a new branch for your feature
2. Make your changes
3. Add tests for new functionality
4. Run tests and ensure they pass
5. Submit a pull request
```

### Phase 6: Building and Publishing

#### 6.1 Build the Package

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# This creates:
# - dist/autoguess-1.0.0.tar.gz (source distribution)
# - dist/autoguess-1.0.0-py3-none-any.whl (wheel)
```

#### 6.2 Test the Package Locally

```bash
# Create a new virtual environment for testing
python -m venv test_env
source test_env/bin/activate

# Install from the built wheel
pip install dist/autoguess-1.0.0-py3-none-any.whl

# Test it
autoguess --help
python -c "import autoguess; print(autoguess.__version__)"
```

#### 6.3 Upload to Test PyPI

```bash
# Upload to Test PyPI first
python -m twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ autoguess
```

#### 6.4 Upload to PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*

# Now users can install with:
# pip install autoguess
```

---

## Migration Path for Users

### For Docker Users
Docker images can continue to work but can be simplified:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y graphviz && \
    rm -rf /var/lib/apt/lists/*

# Install autoguess
RUN pip install autoguess[full]

# Set working directory
WORKDIR /workspace

# Command
CMD ["autoguess", "--help"]
```

### For Current Users (Migration Guide)

**Old way:**
```bash
cd /path/to/autoguess
source autoguess_env/bin/activate
python autoguess.py -i ciphers/Example1/relationfile.txt -s cp -ms 5
```

**New way:**
```bash
pip install autoguess
autoguess -i examples/Example1/relationfile.txt -s cp -ms 5
```

Or in Python:
```python
from autoguess.core import search

params = {
    'inputfile': 'examples/Example1/relationfile.txt',
    'solver': 'cp',
    'maxsteps': 5,
    # ... other parameters
}

search.start_search(params)
```

---

## Dependency License Summary

| Dependency | License | Notes |
|------------|---------|-------|
| passagemath-* | GPL-2.0+ | Open source, required |
| python-sat | MIT | Open source, required |
| pysmt | Apache-2.0 | Open source, required |
| z3-solver | MIT | Open source, required |
| minizinc | MPL-2.0 | Open source, required |
| graphviz | MIT | Open source, required |
| gurobipy | Commercial | Optional, academic licenses available |

---

## Benefits of pip Package

1. **Easy Installation**: `pip install autoguess` vs complex setup scripts
2. **Dependency Management**: Automatic handling of all dependencies
3. **Version Control**: Users can pin specific versions
4. **Virtual Environment Support**: Works seamlessly with venv/conda
5. **Integration**: Easy to use in other Python projects
6. **Distribution**: Reach wider audience via PyPI
7. **CI/CD**: Easier to integrate in automated workflows
8. **Updates**: Simple `pip install --upgrade autoguess`

---

## Checklist for Release

- [ ] Update version in `autoguess/__version__.py`
- [ ] Update README.md with installation instructions
- [ ] Add/update CHANGELOG.md
- [ ] Ensure all tests pass
- [ ] Build package: `python -m build`
- [ ] Test locally: `pip install dist/*.whl`
- [ ] Upload to Test PyPI
- [ ] Test from Test PyPI
- [ ] Upload to PyPI
- [ ] Create GitHub release
- [ ] Update documentation
- [ ] Announce release

---

## Conclusion

Converting Autoguess to a pip package is **definitely feasible** thanks to passagemath. 
The main work involves restructuring the code into a proper Python package layout and 
creating the necessary packaging files. The actual functionality can remain largely 
unchanged.

**Estimated Effort**: 1-2 days for initial conversion + testing
**Maintenance**: Minimal ongoing effort

This will significantly improve the accessibility and usability of Autoguess for 
the research community.
