'''
Created on Aug 24, 2020

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

In case you use this tool please include the above copyright informations (name, contact, license)
'''

from logging import log
import subprocess
import sys
import io
import time
from autoguess.config import PATH_SAGE, SAGE_IMPORTABLE, TEMP_DIR


def _parse_extra_known(parameters):
    """Parse --known CLI string into a list of variable names, or None."""
    known_str = parameters.get('known', None)
    if not known_str:
        return None
    return [v.strip() for v in known_str.split(',') if v.strip()]


def _findmin_descent(parameters, solver_type):
    """
    Shared helper for --findmin: iteratively decrease max_guess from the
    user-supplied bound until the model becomes UNSAT, then re-solve at
    the optimal value with full output.

    SAT uses incremental solving (ITotalizer + assumption-based bounds)
    so the solver is created once and learned clauses are reused across
    iterations.  SMT falls back to per-iteration construction.
    """
    if solver_type == 'sat':
        from .gdsat import ReduceGDtoSAT as SolverClass
    else:
        from .gdsmt import ReduceGDtoSMT as SolverClass

    def _build_and_solve(mg, quiet=False):
        """Create solver, build model, solve.  Returns (result, solver_instance)."""
        _ek = _parse_extra_known(parameters)
        if solver_type == 'sat':
            solver = SolverClass(
                inputfile_name=parameters['inputfile'],
                outputfile_name=parameters['outputfile'],
                max_guess=mg,
                max_steps=parameters['maxsteps'],
                sat_solver=parameters['satsolver'],
                tikz=parameters['tikz'],
                preprocess=parameters['preprocess'],
                D=parameters['D'],
                dglayout=parameters['dglayout'],
                drawgraph=parameters.get('drawgraph', True),
                log=parameters['log'],
                extra_known=_ek)
        else:
            solver = SolverClass(
                inputfile_name=parameters['inputfile'],
                outputfile_name=parameters['outputfile'],
                max_guess=mg,
                max_steps=parameters['maxsteps'],
                smt_solver_name=parameters['smtsolver'],
                tikz=parameters['tikz'],
                preprocess=parameters['preprocess'],
                D=parameters['D'],
                dglayout=parameters['dglayout'],
                drawgraph=parameters.get('drawgraph', True),
                log=parameters['log'],
                extra_known=_ek)
        if quiet:
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
        try:
            solver.make_model()
            solver.time_limit = parameters['timelimit']
            if solver_type == 'sat':
                result = solver.solve_via_satsolver()
            else:
                result = solver.solve_via_smtsolver()
        finally:
            if quiet:
                sys.stdout = old_stdout
        return result, solver

    current_mg = parameters['maxguess']
    print('=' * 60)
    print(f'FIND-MIN MODE: searching for minimum guesses (starting from {current_mg})')
    print('=' * 60)

    total_start = time.time()
    _w = len(str(current_mg))  # width for aligned number columns

    if solver_type == 'sat':
        optimal = _findmin_sat_incremental(parameters, current_mg, _w)
    else:
        # SMT: per-iteration construction (no incremental support yet)
        optimal = None
        while current_mg >= 0:
            iter_start = time.time()
            result, solver = _build_and_solve(current_mg, quiet=True)
            iter_elapsed = time.time() - iter_start
            if result is True:
                n_guessed = len(solver.guessed_vars)
                print(f'  max_guess = {current_mg:{_w}d}:  SAT  — a guess basis of size {n_guessed:{_w}d} exists  ({iter_elapsed:.2f}s)')
                optimal = n_guessed
                if n_guessed < current_mg:
                    current_mg = n_guessed
                else:
                    current_mg -= 1
            elif result is False:
                print(f'  max_guess = {current_mg:{_w}d}:  UNSAT  ({iter_elapsed:.2f}s)')
                break
            else:
                print(f'  max_guess = {current_mg:{_w}d}:  TIMEOUT  ({iter_elapsed:.2f}s)')
                break

    total_elapsed = time.time() - total_start

    if optimal is None:
        print('\n' + '#' * 60)
        print('FIND-MIN RESULT: no feasible solution found')
        print(f'Total findmin time: {total_elapsed:.2f}s')
        print('Increase max_guess or max_steps and try again.')
        print('#' * 60)
        return

    if optimal == 0:
        print('\n' + '#' * 60)
        print('FIND-MIN RESULT: minimum number of guesses = 0')
        print(f'Total findmin time: {total_elapsed:.2f}s')
        print('#' * 60)
        return

    # Re-solve at optimal with full output
    print('\n' + '#' * 60)
    print(f'FIND-MIN RESULT: minimum number of guesses = {optimal}')
    print(f'Total findmin time: {total_elapsed:.2f}s')
    print('#' * 60)
    print(f'\nRe-solving with max_guess = {optimal} for detailed output ...\n')
    print('(Note: the timings below are for this single verification')
    print(' solve only, not for the entire findmin search.)\n')
    _build_and_solve(optimal, quiet=False)
    print(f'\nTotal findmin search time: {total_elapsed:.2f}s')


def _findmin_sat_incremental(parameters, start_mg, _w):
    """
    Incremental SAT-based findmin.

    For unweighted problems: uses PySAT's ITotalizer with assumption-based
    bounds.  The SAT solver is created once; structural constraints and
    totalizer encoding are added once.  Each iteration only changes the
    assumption literal, so the solver reuses all previously learned clauses.

    For weighted problems: the input is parsed once and structural
    constraints are generated once, but the PB cardinality constraint
    is rebuilt per iteration (still saves parsing + constraint generation).
    """
    from .gdsat import ReduceGDtoSAT
    from pysat import solvers as pysat_solvers
    from pysat.card import ITotalizer
    from pysat import pb

    # Create solver object ONCE (parses input, generates deductions) — quietly
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        solver_obj = ReduceGDtoSAT(
            inputfile_name=parameters['inputfile'],
            outputfile_name=parameters['outputfile'],
            max_guess=start_mg,
            max_steps=parameters['maxsteps'],
            sat_solver=parameters['satsolver'],
            tikz=parameters['tikz'],
            preprocess=parameters['preprocess'],
            D=parameters['D'],
            dglayout=parameters['dglayout'],
            drawgraph=False,
            log=0,
            extra_known=_parse_extra_known(parameters))
        solver_obj.generate_sat_constraints()
        solver_obj.generate_boundary_no_cardinality()
    finally:
        sys.stdout = old_stdout

    lits, weights = solver_obj.get_cardinality_lits()
    has_weights = weights is not None
    n_lits = len(lits)
    current_mg = start_mg
    optimal = None

    if not has_weights:
        # ── Unweighted: ITotalizer + assumptions (fully incremental) ──
        ubound = min(start_mg + 1, n_lits)
        itot = ITotalizer(lits=lits, ubound=ubound,
                          top_id=solver_obj.top_variable_identifier_so_far)

        sat = pysat_solvers.Solver(name=parameters['satsolver'])
        sat.append_formula(solver_obj.cnf_formula)
        for cl in itot.cnf.clauses:
            sat.add_clause(cl)

        while current_mg >= 0:
            # Enforce sum(lits) <= current_mg via assumption
            if current_mg < len(itot.rhs):
                assumptions = [-itot.rhs[current_mg]]
            else:
                assumptions = []

            iter_start = time.time()
            result = sat.solve(assumptions=assumptions)
            iter_elapsed = time.time() - iter_start

            if result:
                model = sat.get_model()
                n_guessed = sum(1 for l in lits if model[l - 1] > 0)
                print(f'  max_guess = {current_mg:{_w}d}:  SAT  — a guess basis of size {n_guessed:{_w}d} exists  ({iter_elapsed:.2f}s)')
                optimal = n_guessed
                if n_guessed < current_mg:
                    current_mg = n_guessed
                else:
                    current_mg -= 1
            elif result is False:
                print(f'  max_guess = {current_mg:{_w}d}:  UNSAT  ({iter_elapsed:.2f}s)')
                break
            else:
                print(f'  max_guess = {current_mg:{_w}d}:  TIMEOUT  ({iter_elapsed:.2f}s)')
                break

        sat.delete()
        itot.delete()
    else:
        # ── Weighted: parse once, rebuild cardinality per iteration ──
        base_clauses = list(solver_obj.cnf_formula.clauses)
        top_id = solver_obj.top_variable_identifier_so_far

        while current_mg >= 0:
            card = pb.PBEnc.leq(lits=lits, weights=weights,
                                bound=current_mg, top_id=top_id,
                                encoding=pb.EncType.binmerge)

            sat = pysat_solvers.Solver(name=parameters['satsolver'])
            for cl in base_clauses:
                sat.add_clause(cl)
            for cl in card.clauses:
                sat.add_clause(cl)

            iter_start = time.time()
            result = sat.solve()
            iter_elapsed = time.time() - iter_start

            if result:
                model = sat.get_model()
                n_guessed = sum(1 for l in lits if model[l - 1] > 0)
                weighted_cost = sum(w for l, w in zip(lits, weights)
                                    if model[l - 1] > 0)
                print(f'  max_guess = {current_mg:{_w}d}:  SAT  — size {n_guessed:{_w}d} (weight {weighted_cost}) exists  ({iter_elapsed:.2f}s)')
                optimal = n_guessed
                # Jump based on weighted cost (that is what the bound constrains)
                if weighted_cost < current_mg:
                    current_mg = weighted_cost
                else:
                    current_mg -= 1
            elif result is False:
                print(f'  max_guess = {current_mg:{_w}d}:  UNSAT  ({iter_elapsed:.2f}s)')
                break
            else:
                print(f'  max_guess = {current_mg:{_w}d}:  TIMEOUT  ({iter_elapsed:.2f}s)')
                break

            sat.delete()

    return optimal


def search_using_cp(parameters):
    """
    Convert the guess-and-determine or key-bridging problem to a SMT problem,
    and then solve it
    """

    from .gdcp import ReduceGDtoCP

    gdsmt = ReduceGDtoCP(inputfile_name=parameters['inputfile'],
                    outputfile_name=parameters['outputfile'],
                    max_guess=parameters['maxguess'],
                    max_steps=parameters['maxsteps'],
                    cp_solver_name=parameters['cpsolver'],
                    cp_optimization=parameters['cpoptimization'],
                    tikz=parameters['tikz'],
                    preprocess=parameters['preprocess'],
                    D=parameters['D'],
                    dglayout=parameters['dglayout'],
                    drawgraph=parameters.get('drawgraph', True),
                    log=parameters['log'],
                    threads=parameters.get('threads', 0),
                    extra_known=_parse_extra_known(parameters))
    gdsmt.make_model()
    gdsmt.time_limit = parameters['timelimit']
    gdsmt.solve_via_cpsolver()

def search_using_milp(parameters):
    """
    Convert the guess-and-determine or key-bridging problem to an MILP problem, 
    and then solve it
    """
    
    from .gdmilp import ReduceGDtoMILP
    
    gdmilp = ReduceGDtoMILP(inputfile_name=parameters['inputfile'],
                        outputfile_name=parameters['outputfile'],
                        max_guess=parameters['maxguess'],
                        max_steps=parameters['maxsteps'],
                        direction=parameters['milpdirection'],
                        tikz=parameters['tikz'],
                        preprocess=parameters['preprocess'],
                        D=parameters['D'],
                        dglayout=parameters['dglayout'],
                        drawgraph=parameters.get('drawgraph', True),
                        log=parameters['log'],
                        threads=parameters.get('threads', 0),
                        extra_known=_parse_extra_known(parameters))
    gdmilp.make_model()
    gdmilp.time_limit = parameters['timelimit']
    gdmilp.solve_model()

def search_using_sat(parameters):
    """
    Convert the guess-and-detrmine or key-bridging problem to a SAT problem,
    and then solve it.  When findmin is enabled, iteratively decrease max_guess
    until the model becomes UNSAT, returning the minimum number of guesses.
    """
    from .gdsat import ReduceGDtoSAT

    findmin = parameters.get('findmin', False)
    if not findmin:
        # Single-shot mode (original behaviour)
        gdsat = ReduceGDtoSAT(inputfile_name=parameters['inputfile'],
                            outputfile_name=parameters['outputfile'],
                            max_guess=parameters['maxguess'],
                            max_steps=parameters['maxsteps'],
                            sat_solver=parameters['satsolver'],
                            tikz=parameters['tikz'],
                            preprocess=parameters['preprocess'],
                            D=parameters['D'],
                            dglayout=parameters['dglayout'],
                            drawgraph=parameters.get('drawgraph', True),
                            log=parameters["log"],
                            extra_known=_parse_extra_known(parameters))
        gdsat.make_model()
        gdsat.time_limit = parameters['timelimit']
        gdsat.solve_via_satsolver()
    else:
        _findmin_descent(parameters, solver_type='sat')

def search_using_smt(parameters):
    """
    Convert the guess-and-determine or key-bridging problem to a SMT problem,
    and then solve it.  When findmin is enabled, iteratively decrease max_guess
    until the model becomes UNSAT, returning the minimum number of guesses.
    """

    from .gdsmt import ReduceGDtoSMT

    findmin = parameters.get('findmin', False)
    if not findmin:
        # Single-shot mode (original behaviour)
        gdsmt = ReduceGDtoSMT(inputfile_name=parameters['inputfile'],
                            outputfile_name=parameters['outputfile'],
                            max_guess=parameters['maxguess'],
                            max_steps=parameters['maxsteps'],
                            smt_solver_name=parameters['smtsolver'],
                            tikz=parameters['tikz'],
                            preprocess=parameters['preprocess'],
                            D=parameters['D'],
                            dglayout=parameters['dglayout'],
                            drawgraph=parameters.get('drawgraph', True),
                            log=parameters['log'],
                            extra_known=_parse_extra_known(parameters))
        gdsmt.make_model()
        gdsmt.time_limit = parameters['timelimit']
        gdsmt.solve_via_smtsolver()
    else:
        _findmin_descent(parameters, solver_type='smt')

def search_using_groebnerbasis(parameters):
    """
    Convert the guess-and-determine or key-bridging problem to the problem of computing Groebner basis,
    and then solve it.

    Prefers *passagemath* (``sage`` importable in the current Python);
    falls back to a system SageMath binary if available.
    """
    import pathlib
    _gdgroebner_path = str(pathlib.Path(__file__).parent / "gdgroebner.py")

    args = [
        "--inputfile", parameters['inputfile'],
        "--output", parameters['outputfile'],
        "--preprocess", str(parameters['preprocess']),
        "--D", str(parameters['D']),
        "--term_ordering", parameters['term_ordering'],
        "--overlapping_number", str(parameters['overlapping_number']),
        "--temp_dir", TEMP_DIR,
        "--cnf_to_anf_conversion", parameters['cnf_to_anf_conversion'],
        "--log", str(parameters['log']),
    ]
    known_str = parameters.get('known', None)
    if known_str:
        args.extend(["--known", known_str])

    if SAGE_IMPORTABLE:
        # passagemath is installed – run gdgroebner as a module with current Python
        cmd = [sys.executable, "-m", "autoguess.core.gdgroebner"] + args
    elif PATH_SAGE:
        # Fall back to the system SageMath binary
        cmd = [PATH_SAGE, "-python3", _gdgroebner_path] + args
    else:
        raise RuntimeError(
            "Groebner solver requires passagemath (pip install 'autoguess[groebner]') "
            "or a system SageMath installation, but neither was found."
        )

    subprocess.call(cmd)

def search_using_mark(parameters):
    from .gdmark import Mark
    gdmark = Mark(inputfile_name=parameters['inputfile'],
                outputfile_name=parameters['outputfile'],
                tikz=parameters['tikz'],
                preprocess=parameters['preprocess'],
                D=parameters['D'],
                extra_known=_parse_extra_known(parameters))
    gdmark.generate_and_triangulate_dependency_matrix()
    gdmark.find_minimal_guess_basis()


def search_using_elim(parameters):
    from .gdelim import Elim
    gdmark = Elim(inputfile_name=parameters['inputfile'],
                outputfile_name=parameters['outputfile'],
                tikz=parameters['tikz'],
                preprocess=parameters['preprocess'],
                D=parameters['D'],
                extra_known=_parse_extra_known(parameters))
    gdmark.remove_the_known_variables()
    gdmark.find_minimal_guess_basis()


def search_using_propagate(parameters):
    """
    Propagate knowledge through a system of connection relations
    starting from a given set of initially known variables.

    When --reducebasis is set, tries to shrink the basis given via -kn
    by testing subsets of decreasing size.
    """
    from .inputparser import read_relation_file

    extra_known = _parse_extra_known(parameters)
    parsed_data = read_relation_file(parameters['inputfile'],
                                     preprocess=parameters.get('preprocess', 0),
                                     D=parameters.get('D', 2),
                                     log=parameters.get('log', 0),
                                     extra_known=extra_known)

    if parameters.get('reducebasis', False):
        from .propagate import reduce_basis
        if not extra_known:
            print("Error: --reducebasis requires -kn with the initial guess basis to reduce.")
            return
        reduce_basis(parsed_data=parsed_data, basis_variables=extra_known)
    else:
        from .propagate import propagate_knowledge
        known_variables = list(parsed_data.get('known_variables', []))
        propagate_knowledge(parsed_data=parsed_data, known_variables=known_variables)