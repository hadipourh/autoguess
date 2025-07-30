'''
Created on Oct 4, 2020

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com
'''

import os
import time
import random
import minizinc
from core.inputparser import read_relation_file
from core.parsesolution import parse_solver_solution
from core.graphdrawer import draw_graph
from config import TEMP_DIR
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

    def __init__(self, inputfile_name=None, outputfile_name='output', max_guess=0, max_steps=0, cp_solver_name='cp-sat', \
        cp_optimization=0, tikz=0, preprocess=1, D=2, dglayout="dot", log="0"):
        self.inputfile_name = inputfile_name
        self.output_dir = outputfile_name     
        self.rnd_string_tmp = '%030x' % random.randrange(16**30)
        self.max_guess = max_guess
        self.max_steps = max_steps
        self.cp_solver_name = cp_solver_name
        self.dglayout = dglayout
        self.log = log  
        self.supported_cp_solvers = [solver_name for solver_name in minizinc.default_driver.available_solvers().keys()]
        try:
            if self.cp_solver_name not in self.supported_cp_solvers:
                raise ValueError(f"Solver '{self.cp_solver_name}' is not supported. Supported solvers are: {self.supported_cp_solvers}")
        except ValueError as e:
            print(e)
            print('The default CP solver is used instead: cp-sat (ortools)')
            self.cp_solver_name = 'cp-sat' # for newer versions of MiniZinc, use 'cp-sat' to use Or-tools      
        self.cp_solver = minizinc.Solver.lookup(self.cp_solver_name)      
        self.cp_optimization = cp_optimization
        self.nthreads = 16
        self.cp_boolean_variables = []
        self.cp_constraints = ''
        self._parse_input_file(preprocess, D)
        self._set_max_guess()
        self.deductions = self.generate_possible_deductions()        
        self.time_limit = -1
        self.tikz = tikz

    def _parse_input_file(self, preprocess, D):
        parsed_data = read_relation_file(self.inputfile_name, preprocess, D, self.log)
        self.problem_name = parsed_data['problem_name']
        self.variables = parsed_data['variables']
        self.known_variables = parsed_data['known_variables']
        self.target_variables = parsed_data['target_variables']
        self.notguessed_variables = parsed_data['notguessed_variables']
        self.symmetric_relations = parsed_data['symmetric_relations']
        self.implication_relations = parsed_data['implication_relations']
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
        possible_deductions = {v: [[v]] for v in self.variables}
        for v in self.variables:
            for rel in self.symmetric_relations:
                if v in rel:
                    temp = rel.copy()
                    temp.remove(v)
                    possible_deductions[v].append(temp)
            for rel in self.implication_relations:
                if v == rel[-1]:
                    temp = rel.copy()
                    temp.remove(v)
                    possible_deductions[v].append(temp)
        return possible_deductions
    
    def update_variables_list(self, new_vars):
        self.cp_boolean_variables.extend(v for v in new_vars if v not in self.cp_boolean_variables)
        
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
        initial_state_vars = ['%s_%d' % (v, 0) for v in self.variables if v not in self.known_variables]
        if initial_state_vars:
            self.update_variables_list(initial_state_vars)
            self.cp_constraints += 'constraint %s <= %d;\n' % (' + '.join(initial_state_vars), self.max_guess)

    def _force_target_variables_known(self):
        final_state_target_vars = ['%s_%d' % (v, self.max_steps) for v in self.target_variables]
        self.update_variables_list(final_state_target_vars)
        for fv in final_state_target_vars:
            self.cp_constraints += 'constraint %s = 1;\n' % fv

    def _set_known_variables(self):
        for v in self.known_variables:
            if v:
                self.cp_constraints += 'constraint %s_0 = 1;\n' % v

    def _set_notguessed_variables(self):
        for v in self.notguessed_variables:
            if v:
                self.cp_constraints += 'constraint %s_0 = 0;\n' % v
    
    def generate_objective_function(self):
        """
        This method generates the objective function minimizing the 
        set of known variables at initial state.
        """
        initial_state_vars = ['%s_%d' % (v, 0) for v in self.variables if v not in self.known_variables]
        if self.cp_optimization == 1 and initial_state_vars:
            self.cp_constraints += 'solve minimize %s;\n' % ' + '.join(initial_state_vars)
        else:
            self.cp_constraints += 'solve satisfy;\n'
      
    def generate_cp_constraints(self):
        """
        This method generates the CP constraints corresponding to the 
        obtained deductions
        """
        for step in range(self.max_steps):
            for v in self.variables:
                v_new = '%s_%d' % (v, step + 1)
                tau = len(self.deductions[v])
                v_path_variables = ['%s_%d_%d' % (v, step + 1, i) for i in range(tau)]
                self.update_variables_list([v_new] + v_path_variables)
                self._add_state_variable_constraints(v_new, v_path_variables)
                self._add_path_variable_constraints(v, step, tau, v_path_variables)

    def _add_state_variable_constraints(self, v_new, v_path_variables):
        RHS = ' \/ '.join(v_path_variables)
        self.cp_constraints += 'constraint %s <-> %s;\n' % (v_new, RHS)

    def _add_path_variable_constraints(self, v, step, tau, v_path_variables):
        for i in range(tau):
            v_connected_variables = ['%s_%d' % (var, step) for var in self.deductions[v][i]]
            self.update_variables_list(v_connected_variables)
            RHS = ' /\\ '.join(v_connected_variables)
            self.cp_constraints += 'constraint %s <-> %s;\n' % (v_path_variables[i], RHS)

    def make_model(self):
        """
        This method makes the CP model, and then write it into a file in mzn format
        """
        print('Generating the CP model ...')
        start_time = time.time()
        self.generate_cp_constraints()
        self.generate_initial_conditions()
        boolean_variables = ''.join('var bool: %s;\n' % bv for bv in self.cp_boolean_variables)
        self.cp_constraints = boolean_variables + self.cp_constraints
        self.generate_objective_function()
        self.cp_file_path = os.path.join(TEMP_DIR, 'cpmodel_mg%d_ms%d_%s.mzn' % (
            self.max_guess, self.max_steps, self.rnd_string_tmp))
        elapsed_time = time.time() - start_time
        print('CP model was generated after %0.2f seconds' % elapsed_time)        
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
        print('Solving the CP model with %s ...' % self.cp_solver_name)
        start_time = time.time()
        result = self.cp_inst.solve(timeout=time_limit, processes=nthreads, random_seed=rand_int)
        elapsed_time = time.time() - start_time
        print('Solving process was finished after %0.2f seconds' % elapsed_time)
        return self._handle_solver_result(result)

    def _handle_solver_result(self, result):
        if result.status in [minizinc.Status.OPTIMAL_SOLUTION, minizinc.Status.SATISFIED, minizinc.Status.ALL_SOLUTIONS]:
            self._extract_solution(result)
            parse_solver_solution(self)
            draw_graph(self.vertices, self.edges, self.known_variables, self.guessed_vars, self.output_dir, self.tikz, self.dglayout)
            return True
        elif result.status == minizinc.Status.UNSATISFIABLE:
            print('The model is UNSAT!\nIncrease the max_guess or max_steps parameters and try again.')
            return False
        elif result.status == minizinc.Status.ERROR:
            print(result.status)
        else:
            print('Solver could not find the solution\nThe solving process was interrupted before finding any solution. Perhaps more time is needed!')
            return None

    def _extract_solution(self, result):
        self.solutions = [0] * (self.max_steps + 1)
        for step in range(self.max_steps + 1):
            state_vars = ['%s_%d' % (v, step) for v in self.variables]
            state_values = list(map(lambda vx: int(result.solution[vx]), state_vars))
            self.solutions[step] = dict(zip(state_vars, state_values))
        if self.log == 0:
            os.remove(self.cp_file_path)
