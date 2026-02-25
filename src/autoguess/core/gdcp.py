'''
Created on Oct 4, 2020

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

import os
import time
import random
import minizinc
from .inputparser import read_relation_file
from .parsesolution import parse_solver_solution
from .graphdrawer import draw_graph
from autoguess.config import TEMP_DIR, MINIZINC_LIB_DIR, ensure_minizinc_driver

ensure_minizinc_driver()
from .varnames import step_var, path_var
import datetime
import subprocess

class ReduceGDtoCP:
    """
    ReduceGDtoCP
    Using the MiniZinc python interface, this class reduces the guess-and-determine attack and search for
    key-bridges to CP model, and then calls a CP solver to solve it.

    Created by Hosein Hadipour
    Oct 4, 2020

    inputfile_name: The name of a text file containing the relations
    max_guess:  The maximum number of guessed variables
    max_steps:  Number of state copies
    """

    count = 0

    def __init__(self, inputfile_name=None, outputfile_name='output', max_guess=0, max_steps=0, cp_solver_name="cp-sat", \
        cp_optimization=0, tikz=0, preprocess=1, D=2, dglayout="dot", drawgraph=True, log="0", threads=0, extra_known=None):
        self.inputfile_name = inputfile_name
        self.output_dir = outputfile_name     
        self.rnd_string_tmp = '%030x' % random.randrange(16**30)
        self.max_guess = max_guess
        self.max_steps = max_steps
        self.cp_solver_name = cp_solver_name
        self.dglayout = dglayout
        self.draw_graph = drawgraph
        self.log = log  
        self.supported_cp_solvers = [solver_name for solver_name in minizinc.default_driver.available_solvers().keys()]
        if self.cp_solver_name not in self.supported_cp_solvers:
            # Try a ranked preference list of well-known solvers
            _preferred = ["cp-sat", "gecode", "chuffed"]
            fallback = None
            for _s in _preferred:
                if _s in self.supported_cp_solvers:
                    fallback = _s
                    break
            if fallback is None and self.supported_cp_solvers:
                fallback = self.supported_cp_solvers[0]
            if fallback is None:
                raise RuntimeError(
                    f"Solver '{self.cp_solver_name}' is not available and no "
                    f"fallback solver found.  Available: {self.supported_cp_solvers}"
                )
            print(f"WARNING: Solver '{self.cp_solver_name}' not available.")
            print(f"  Available: {self.supported_cp_solvers}")
            print(f"  Falling back to: {fallback}")
            self.cp_solver_name = fallback
        self.cp_solver = minizinc.Solver.lookup(self.cp_solver_name)      
        self.cp_optimization = cp_optimization
        self.nthreads = threads if threads > 0 else (os.cpu_count() or 1)
        self.cp_boolean_variables = []
        self._cp_vars_set = set()
        self._constraint_lines = []
        self.extra_known = extra_known
        self._parse_input_file(preprocess, D)
        self._set_max_guess()
        self.deductions = self.generate_possible_deductions()        
        self.time_limit = -1
        self.tikz = tikz

    def _parse_input_file(self, preprocess, D):
        parsed_data = read_relation_file(self.inputfile_name, preprocess, D, self.log, extra_known=self.extra_known)
        self.problem_name = parsed_data['problem_name']
        self.variables = parsed_data['variables']
        self.known_variables = parsed_data['known_variables']
        self.target_variables = parsed_data['target_variables']
        self.notguessed_variables = parsed_data['notguessed_variables']
        self.symmetric_relations = parsed_data['symmetric_relations']
        self.implication_relations = parsed_data['implication_relations']
        self.dummy_mapping = parsed_data.get('dummy_mapping', {})
        self.num_of_relations = len(self.symmetric_relations) + len(self.implication_relations)
        self.num_of_vars = len(self.variables)

    def _set_max_guess(self):
        if (self.max_guess is None) or (self.max_guess > len(self.target_variables)):
            self.max_guess = len(self.target_variables) if self.notguessed_variables is None else len(self.variables)
            print('Number of guessed variables is set to be at most %d' % self.max_guess)

    def ordered_set(self, seq):
        """
        This method eliminates duplicated elements in a given list, 
        and returns a list in which each elements appears only once
        """
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]

    def generate_possible_deductions(self):
        """
        This method generates all possible deductions 

        Core idea of information propagation: 
            If there is a relation in which all terms are known except one, 
            then the value of the last term can be determined as well. 
        """
        # Build inverted indices for O(1) lookup instead of O(|R|) scan per variable
        from collections import defaultdict
        sym_index = defaultdict(list)
        for rel in self.symmetric_relations:
            for v in rel:
                sym_index[v].append(rel)
        impl_index = defaultdict(list)
        for rel in self.implication_relations:
            impl_index[rel[-1]].append(rel)

        possible_deductions = {v: [[v]] for v in self.variables}
        for v in self.variables:
            for rel in sym_index.get(v, []):
                temp = rel.copy()
                temp.remove(v)
                possible_deductions[v].append(temp)
            for rel in impl_index.get(v, []):
                temp = rel.copy()
                temp.remove(v)
                possible_deductions[v].append(temp)
        return possible_deductions
    
    def update_variables_list(self, new_vars):
        for v in new_vars:
            if v not in self._cp_vars_set:
                self._cp_vars_set.add(v)
                self.cp_boolean_variables.append(v)
        
    def generate_initial_conditions(self):
        """
        This method generates the constraints corresponding to the initially known variables, 
        and limits the maximum number of guessed variables. 
        It also limits the target variables to be known in the final step of knowledge propagation
        """
        self._limit_max_guessed_variables()
        self._force_target_variables_known()
        self._set_known_variables()
        self._set_notguessed_variables()

    def _limit_max_guessed_variables(self):
        initial_state_vars = [step_var(v, 0) for v in self.variables if v not in self.known_variables]
        if initial_state_vars:
            self.update_variables_list(initial_state_vars)
            self._constraint_lines.append('constraint %s <= %d;\n' % (' + '.join(initial_state_vars), self.max_guess))

    def _force_target_variables_known(self):
        final_state_target_vars = [step_var(v, self.max_steps) for v in self.target_variables]
        self.update_variables_list(final_state_target_vars)
        for fv in final_state_target_vars:
            self._constraint_lines.append('constraint %s = 1;\n' % fv)

    def _set_known_variables(self):
        for v in self.known_variables:
            if v:
                self._constraint_lines.append('constraint %s = 1;\n' % step_var(v, 0))

    def _set_notguessed_variables(self):
        for v in self.notguessed_variables:
            if v:
                self._constraint_lines.append('constraint %s = 0;\n' % step_var(v, 0))
    
    def generate_objective_function(self):
        """
        This method generates the objective function minimizing the 
        set of known variables at initial state.
        """
        initial_state_vars = [step_var(v, 0) for v in self.variables if v not in self.known_variables]
        if self.cp_optimization == 1 and initial_state_vars:
            self._constraint_lines.append('solve minimize %s;\n' % ' + '.join(initial_state_vars))
        else:
            self._constraint_lines.append('solve satisfy;\n')
      
    def generate_cp_constraints(self):
        """
        This method generates the CP constraints corresponding to the 
        obtained deductions
        """
        for step in range(self.max_steps):
            for v in self.variables:
                v_new = step_var(v, step + 1)
                tau = len(self.deductions[v])
                v_path_variables = [path_var(v, step + 1, i) for i in range(tau)]
                self.update_variables_list([v_new] + v_path_variables)
                self._add_state_variable_constraints(v_new, v_path_variables)
                self._add_path_variable_constraints(v, step, tau, v_path_variables)

    def _add_state_variable_constraints(self, v_new, v_path_variables):
        RHS = ' \\/ '.join(v_path_variables)
        self._constraint_lines.append('constraint %s <-> %s;\n' % (v_new, RHS))

    def _add_path_variable_constraints(self, v, step, tau, v_path_variables):
        for i in range(tau):
            v_connected_variables = [step_var(var, step) for var in self.deductions[v][i]]
            self.update_variables_list(v_connected_variables)
            RHS = ' /\\ '.join(v_connected_variables)
            self._constraint_lines.append('constraint %s <-> %s;\n' % (v_path_variables[i], RHS))

    def make_model(self):
        """
        This method makes the CP model, and then write it into a file in mzn format
        """
        print('=' * 60)
        print('CP SOLVER — %s' % self.problem_name)
        print('=' * 60)
        print('Variables: %d | Relations: %d' % (self.num_of_vars, self.num_of_relations))
        print('Max guess: %d | Max steps: %d' % (self.max_guess, self.max_steps))
        print('Solver: %s' % self.cp_solver_name)
        print('-' * 60)
        print('MODEL GENERATION')
        print('-' * 60)
        start_time = time.time()
        self.generate_cp_constraints()
        self.generate_initial_conditions()
        self.generate_objective_function()
        # Assemble the full model: variable declarations + constraints
        parts = ['var bool: %s;\n' % bv for bv in self.cp_boolean_variables]
        parts.extend(self._constraint_lines)
        self.cp_constraints = ''.join(parts)
        self.cp_file_path = os.path.join(TEMP_DIR, 'cpmodel_mg%d_ms%d_%s.mzn' % (
            self.max_guess, self.max_steps, self.rnd_string_tmp))
        elapsed_time = time.time() - start_time
        print('CP model generated in %0.2f seconds' % elapsed_time)        
        with open(self.cp_file_path, 'w') as minizinc_file:
            minizinc_file.write(self.cp_constraints)
        self.cp_model = minizinc.Model()
        self.cp_model.output_type = dict
        self.cp_model.add_file(self.cp_file_path)        
        self.cp_inst = minizinc.Instance(solver=self.cp_solver, model=self.cp_model)        

    def solve_via_cpsolver(self):
        """
        This method calls the chosen CP solver to solve the generated CP problem
        """
        rand_int = random.randint(0, 1000) if '-r' in self.cp_solver.stdFlags else None
        time_limit = datetime.timedelta(seconds=self.time_limit) if self.time_limit != -1 else None
        nthreads = self.nthreads if '-p' in self.cp_solver.stdFlags else None
        print('-' * 60)
        print('SOLVING')
        print('-' * 60)
        start_time = time.time()
        # Temporarily set LD_LIBRARY_PATH for bundled solver shared libs
        # (e.g. fzn-cp-sat / OR-Tools).  Scoped here so it does not pollute
        # the environment for later subprocesses like Graphviz's dot.
        _old_ld = os.environ.get("LD_LIBRARY_PATH")
        if MINIZINC_LIB_DIR:
            _ld = _old_ld or ""
            if MINIZINC_LIB_DIR not in _ld.split(os.pathsep):
                os.environ["LD_LIBRARY_PATH"] = (
                    MINIZINC_LIB_DIR + os.pathsep + _ld if _ld else MINIZINC_LIB_DIR
                )
        try:
            result = self.cp_inst.solve(timeout=time_limit, processes=nthreads, random_seed=rand_int)
        finally:
            # Restore original LD_LIBRARY_PATH
            if _old_ld is None:
                os.environ.pop("LD_LIBRARY_PATH", None)
            else:
                os.environ["LD_LIBRARY_PATH"] = _old_ld
        elapsed_time = time.time() - start_time
        print('Solving finished in %0.2f seconds' % elapsed_time)
        return self._handle_solver_result(result)

    def _handle_solver_result(self, result):
        if result.status in [minizinc.Status.OPTIMAL_SOLUTION, minizinc.Status.SATISFIED, minizinc.Status.ALL_SOLUTIONS]:
            self._extract_solution(result)
            parse_solver_solution(self)
            if self.draw_graph:
                draw_graph(self.vertices, self.edges, self.known_variables, self.guessed_vars, self.output_dir, self.tikz, self.dglayout)
            return True
        elif result.status == minizinc.Status.UNSATISFIABLE:
            print('\n' + '=' * 60)
            print('RESULT: UNSATISFIABLE')
            print('The model is UNSAT!')
            print('Increase max_guess or max_steps and try again.')
            print('=' * 60)
            return False
        elif result.status == minizinc.Status.ERROR:
            print('\n' + '=' * 60)
            print('RESULT: ERROR')
            print(result.status)
            print('=' * 60)
        else:
            print('\n' + '=' * 60)
            print('RESULT: TIMEOUT')
            print('The solver was interrupted before finding any solution.')
            print('Perhaps more time is needed!')
            print('=' * 60)
            return None

    def _extract_solution(self, result):
        self.solutions = [0] * (self.max_steps + 1)
        for step in range(self.max_steps + 1):
            state_vars = [step_var(v, step) for v in self.variables]
            state_values = list(map(lambda vx: int(result.solution[vx]), state_vars))
            self.solutions[step] = dict(zip(state_vars, state_values))
        if self.log == 0:
            os.remove(self.cp_file_path)
