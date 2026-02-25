#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
Autoguess CLI - Automated Guess-and-Determine and Key-Bridging attacks.

Copyright (C) 2021 Hosein Hadipour
Contact: hsn.hadipour@gmail.com
License: GPL-3.0-or-later
"""

from autoguess.core import search
from argparse import ArgumentParser, RawTextHelpFormatter
import os
from autoguess.config import TEMP_DIR, ensure_minizinc_driver

try:
    from importlib.metadata import version as _version
    __version__ = _version("autoguess")
except Exception:
    __version__ = "1.0.0"


def _get_available_cp_solvers():
    """Return list of available MiniZinc CP solvers, or a default list if MiniZinc is not installed."""
    try:
        ensure_minizinc_driver()
        import minizinc
        driver = minizinc.default_driver
        if driver is not None:
            return list(driver.available_solvers().keys())
    except (ImportError, Exception):
        pass
    # Default choices when MiniZinc is not available
    return ["cp-sat", "gecode", "chuffed"]


def _default_cp_solver():
    """Pick the best available CP solver (prefer cp-sat > gecode > chuffed)."""
    available = _get_available_cp_solvers()
    for preferred in ("cp-sat", "gecode", "chuffed"):
        if preferred in available:
            return preferred
    return available[0] if available else "gecode"


def _get_available_sat_solvers():
    """Return list of available SAT solver names."""
    try:
        from pysat import solvers
        return [s for s in solvers.SolverNames.__dict__.keys() if not s.startswith('__')]
    except ImportError:
        return ["cadical153", "glucose4", "minisat22"]


def _get_available_smt_solvers():
    """Return list of installed pySMT solver names."""
    try:
        from pysmt.environment import get_env
        return sorted(get_env().factory._all_solvers.keys())
    except Exception:
        return ['z3']


def _resolve_dynamic_defaults(params):
    """
    If maxguess or maxsteps were not supplied by the user, derive sensible
    defaults from the input file:
      maxguess  -> number of target variables
      maxsteps  -> number of all variables (before preprocessing)
    A lightweight parse (preprocess=0) is used so this is fast.
    """
    if params['maxguess'] is not None and params['maxsteps'] is not None:
        return
    from .core.inputparser import read_relation_file
    parsed = read_relation_file(params['inputfile'], preprocess=0, D=2, log=0)
    if params['maxguess'] is None:
        params['maxguess'] = len(parsed['target_variables'])
    if params['maxsteps'] is None:
        params['maxsteps'] = len(parsed['variables'])

def start_search(params):
    """
    Starts the search tool for the given parameters
    """
    _resolve_dynamic_defaults(params)
    solver = params["solver"]
    search_methods = {
        'milp': search.search_using_milp,
        'sat': search.search_using_sat,
        'smt': search.search_using_smt,
        'cp': search.search_using_cp,
        'groebner': search.search_using_groebnerbasis,
        'propagate': search.search_using_propagate,
    }

    if solver in search_methods:
        search_methods[solver](params)
    else:
        print('Choose the solver from the following options: cp, milp, sat, smt, groebner, propagate')


def check_environment():
    """
    Basic checks if the environment is set up correctly
    """
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)


def load_parameters(args):
    """
    Get parameters from the argument list and input file.
    """
    params = {
        "inputfile": "./ciphers/Example4/algebraic_relations.txt",
        "outputfile": "output",
        "maxguess": None,
        "maxsteps": None,
        "solver": 'cp',
        "milpdirection": 'min',
        "timelimit": -1,
        "cpsolver": _default_cp_solver(),
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
        "drawgraph": True,
        "findmin": False,
        "reducebasis": False,
        "threads": 0,
        "log": 1,
        "known": None
    }

    for key in params:
        val = getattr(args, key, None)
        if val is not None and not isinstance(val, bool):
            params[key] = val[0] if isinstance(val, list) else val

    if getattr(args, 'nograph', False):
        params['drawgraph'] = False

    if getattr(args, 'findmin', False):
        params['findmin'] = True

    if getattr(args, 'reducebasis', False):
        params['reducebasis'] = True

    return params


def main():
    """
    Parse the arguments and start the request functionality with the provided parameters.
    """
    parser = ArgumentParser(
        description="This tool automates the Guess-and-Determine"
                    " and Key-Bridging techniques"
                    " using a variety of CP, MILP, SMT and SAT solvers, as well as"
                    " the algebraic method based on Groebner basis",
        formatter_class=RawTextHelpFormatter)
    parser.add_argument('-i', '--inputfile', nargs=1, help="Use an input file in plain text format")
    parser.add_argument('-o', '--outputfile', nargs=1, help="Use an output file to write the output into it")
    parser.add_argument('-mg', '--maxguess', nargs=1, type=int, help="An upper bound for the number of guessed variables\n(default: number of target variables)")
    parser.add_argument('-ms', '--maxsteps', nargs=1, type=int, help="An integer number specifying the depth of search\n(default: number of variables before preprocessing)")
    parser.add_argument('-s', '--solver', nargs=1,
                        choices=['cp', 'milp', 'sat', 'smt', 'groebner', 'propagate'],
                        help="Solver choice")
    parser.add_argument('-milpd', '--milpdirection', nargs=1, choices=['min', 'max'], help="MILP direction")
    parser.add_argument('-cps', '--cpsolver', nargs=1, type=str,
                        choices=_get_available_cp_solvers(),
                        help="CP solver choice", default=[_default_cp_solver()])
    parser.add_argument('-sats', '--satsolver', nargs=1, type=str,
                        choices=_get_available_sat_solvers(),
                        help="SAT solver choice")
    parser.add_argument('-smts', '--smtsolver', nargs=1, type=str,
                        choices=_get_available_smt_solvers(), help="SMT solver choice")
    parser.add_argument('-cpopt', '--cpoptimization', nargs=1, type=int, choices=[0, 1], help="CP optimization")
    parser.add_argument('-tl', '--timelimit', nargs=1, type=int, help="Time limit for the search in seconds")
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
                        choices=['simple', 'blockwise'], help="CNF to ANF conversion method")
    parser.add_argument('-dgl', '--dglayout', nargs=1, type=str,
                        choices=["dot", "circo", "twopi", "fdp", "neato", "nop", "nop1", "nop2",
                                 "osage", "patchwork", "sfdp"],
                        help="Layout of determination flow graph")
    parser.add_argument('-log', '--log', nargs=1, type=int, choices=[0, 1],
                        help="Store intermediate generated files and results", default=[0])
    parser.add_argument('-kn', '--known', nargs=1, type=str,
                        help="Comma-separated list of additionally known variables")
    parser.add_argument('-t', '--threads', nargs=1, type=int,
                        help="Number of threads for CP/MILP solvers\n(default: 0 = use all available cores)")
    parser.add_argument('--nograph', action='store_true', default=False,
                        help="Skip generating the determination flow graph (faster)")
    parser.add_argument('--findmin', action='store_true', default=False,
                        help="Iteratively decrease max_guess to find the minimum number of guesses (SAT/SMT only)")
    parser.add_argument('--reducebasis', action='store_true', default=False,
                        help="Reduce a known guess basis via propagation: test subsets of\n"
                             "decreasing size (requires -s propagate and -kn)")

    # MiniZinc installer command
    parser.add_argument('--install-minizinc', action='store_true',
                        help="Download and install MiniZinc binary to ~/.autoguess/minizinc/")
    parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + __version__)

    args = parser.parse_args()

    # Handle --install-minizinc
    if args.install_minizinc:
        from autoguess.utils.minizinc_installer import install_minizinc
        install_minizinc()
        return

    params = load_parameters(args)
    check_environment()
    start_search(params)


if __name__ == '__main__':
    main()
