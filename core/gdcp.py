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

# logging.basicConfig(filename="./temp/minizinc-python.log", level=logging.DEBUG)


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

    def __init__(self, inputfile_name=None, outputfile_name='output', max_guess=0, max_steps=0, cp_solver_name='gecode', \
        cp_optimization=0, tikz=0, preprocess=1, D=2, dglayout="dot", log="0"):
        self.inputfile_name = inputfile_name
        self.output_dir = outputfile_name     
        self.rnd_string_tmp = '%030x' % random.randrange(16**30)
        self.max_guess = max_guess
        self.max_steps = max_steps
        self.cp_solver_name = cp_solver_name
        self.dglayout = dglayout
        self.log = log  
        # Supported CP solvers: All CP solvers supported by MiniZinc
        # coinbc
        # gurobi
        # cplex
        # gecode
        # chuffed
        # choco
        # eclipse
        # haifacsp
        # jacop
        # minisatid
        # mistral
        # opturion
        # ortools
        # oscar
        # picat
        # sicstus
        # scip
        # yuck
        self.supported_cp_solvers = [
            'gecode', 'chuffed', 'cbc', 'gurobi', 'picat', 'scip', 'choco', 'or-tools']
        self.cp_optimization = cp_optimization
        assert(self.cp_solver_name in self.supported_cp_solvers)
        self.cp_solver = minizinc.Solver.lookup(self.cp_solver_name)        
        self.nthreads = 16
        self.cp_boolean_variables = []
        self.cp_constraints = ''
        ###############################
        # Read and parse the input file
        parsed_data = read_relation_file(self.inputfile_name, preprocess, D, self.log)
        self.problem_name = parsed_data['problem_name']
        self.variables = parsed_data['variables']
        self.known_variables = parsed_data['known_variables']
        self.target_variables = parsed_data['target_variables']
        self.notguessed_variables = parsed_data['notguessed_variables']
        self.symmetric_relations = parsed_data['symmetric_relations']
        self.implication_relations = parsed_data['implication_relations']
        self.num_of_relations = len(
            self.symmetric_relations) + len(self.implication_relations)
        self.num_of_vars = len(self.variables)
        ###############################
        if (self.max_guess is None) or (self.max_guess > len(self.target_variables)):
            self.max_guess = len(self.target_variables)
            print('Number of guessed variables is set to be at most %d' % self.max_guess)   
        self.deductions = self.generate_possible_deductions()        
        self.time_limit = -1
        self.tikz = tikz

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
        
        possible_deductions = {}
        for v in self.variables:
            possible_deductions[v] = [[v]]
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
        for v in new_vars:
            if v not in self.cp_boolean_variables:
                self.cp_boolean_variables.append(v)
        
    def generate_initial_conditions(self):
        """
        This method generates the constraints corresponding to the initially known variables, 
        and limits the maximum number of guessed variables. 
        It also limits the target variables to be known in the final step of knowledge propagation
        """

        # Limit the maximum number of guessed variables
        initial_state_vars = ['%s_%d' % (
            v, 0) for v in self.variables if v not in self.known_variables]
        if initial_state_vars != []:
            self.update_variables_list(initial_state_vars)
            self.cp_constraints += 'constraint %s <= %d;\n' % (' + '.join(initial_state_vars), self.max_guess)  

        # Force the target variables to be known in the final step of knowledge propagation
        final_state_target_vars = ['%s_%d' % (
            v, self.max_steps) for v in self.target_variables]
        self.update_variables_list(final_state_target_vars)
        for fv in final_state_target_vars:
            self.cp_constraints += 'constraint %s = 1;\n' % fv

        # Limit the known variables to be equal to 1 in the first step of knowledge propagation
        for v in self.known_variables:
            if v != '':
                LHS = '%s_0' % v
                self.cp_constraints += 'constraint %s = 1;\n' % (LHS)
            
        # Limit the notguessed variables to be equal to 0 in the first step of knowledge propagation
        for v in self.notguessed_variables:
            if v != '':
                LHS = '%s_0' % v
                self.cp_constraints += 'constraint %s = 0;\n' % (LHS)
    
    def generate_objective_function(self):
        """
        This method generates the objective function minimizng the 
        set of known variables at initial state.
        """

        initial_state_vars = ['%s_%d' % (
            v, 0) for v in self.variables if v not in self.known_variables]
        if self.cp_optimization == 1 and initial_state_vars != []:
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
                v_path_variables = ['%s_%d_%d' %
                                    (v, step + 1, i) for i in range(tau)]
                self.update_variables_list([v_new] + v_path_variables)
                #####################################-State variable constraints-#####################################
                ######################################################################################################
                ######################################################################################################                                
                RHS = ' \/ '.join(v_path_variables)
                LHS = v_new
                self.cp_constraints += 'constraint %s <-> %s;\n' % (LHS, RHS)
                #####################################-Path variable constraints-######################################
                ######################################################################################################
                ######################################################################################################
                for i in range(0, tau):
                    v_connected_variables = ['%s_%d' % (
                        var, step) for var in self.deductions[v][i]]
                    self.update_variables_list(v_connected_variables)
                    LHS = v_path_variables[i]
                    RHS = ' /\\ '.join(v_connected_variables)
                    self.cp_constraints += 'constraint %s <-> %s;\n' % (LHS, RHS)
                ######################################################################################################
                ######################################################################################################
                ######################################################################################################

    def make_model(self):
        """
        This method makes the CP model, and then write it into a file in mzn format
        """
        print('Generating the CP model ...')
        start_time = time.time()
        self.generate_cp_constraints()
        self.generate_initial_conditions()
        boolean_variables = ''
        for bv in self.cp_boolean_variables:
            boolean_variables += 'var bool: %s;\n' % bv
        self.cp_constraints = boolean_variables + self.cp_constraints
        self.generate_objective_function()
        self.cp_file_path = os.path.join(TEMP_DIR, 'cpmodel_mg%d_ms%d_%s.mzn' % (
            self.max_guess, self.max_steps, self.rnd_string_tmp))
        elapsed_time = time.time() - start_time
        print('CP model was generated after %0.2f seconds' % elapsed_time)        
        with open(self.cp_file_path, 'w') as minizinc_file:
            minizinc_file.write(self.cp_constraints)
        self.cp_model = minizinc.Model()
        ####################################################################################################
        # To bypass the error produced by Python 3.6 when more than 255 arguments are passed into a function
        self.cp_model.output_type = dict
        ####################################################################################################
        self.cp_model.add_file(self.cp_file_path)        
        self.cp_inst = minizinc.Instance(solver=self.cp_solver, model=self.cp_model)        

    def solve_via_cpsolver(self):
        """
        This method calls the chosen CP solver to solve the generated CP problem
        """
        
        if '-r' in self.cp_solver.stdFlags:
            rand_int = random.randint(0, 1000)
        else:
            rand_int = None
        if self.time_limit != -1:
            time_limit = datetime.timedelta(seconds=self.time_limit)
        else:
            time_limit = None
        if '-p' in self.cp_solver.stdFlags:
            nthreads = self.nthreads
        else:
            nthreads = None
        print('Solving the CP model with %s ...' % self.cp_solver_name)
        start_time = time.time()
        ##########################
        ##########################
        result = self.cp_inst.solve(timeout=time_limit, processes=nthreads, random_seed=rand_int)
        ##########################
        ##########################
        if self.log == 0:
            os.remove(self.cp_file_path)
        elapsed_time = time.time() - start_time
        print('Solving process was finished after %0.2f seconds' % elapsed_time)
        if result.status == minizinc.Status.OPTIMAL_SOLUTION or result.status == minizinc.Status.SATISFIED or result.status == minizinc.Status.ALL_SOLUTIONS:
            """
            ERROR: An error occurred during the solving process.
            UNKNOWN: No solutions have been found and search has terminated without
                     exploring the whole search space.
            UNBOUNDED: The objective of the optimization problem is unbounded.
            UNSATISFIABLE: No solutions have been found and the whole search space
                           was explored.
            SATISFIED: A solution was found, but possibly not the whole search
                       space was explored.
            ALL_SOLUTIONS: All solutions in the search space have been found.
            OPTIMAL_SOLUTION: A solution has been found that is optimal according
                              to the objective.
            """
            # Extract the solution            
            self.solutions = [0]*(self.max_steps + 1)
            for step in range(self.max_steps + 1):
                state_vars = ['%s_%d' % (v, step) for v in self.variables]
                state_values = list(
                    map(lambda vx: int(result.solution[vx]), state_vars))
                self.solutions[step] = dict(zip(state_vars, state_values))
            parse_solver_solution(self)
            draw_graph(self.vertices, self.edges, self.known_variables, self.guessed_vars,\
                 self.output_dir, self.tikz, self.dglayout)
            return True
        elif result.status == minizinc.Status.UNSATISFIABLE:
            print(
                'The model is UNSAT!\nIncrease the max_guess or max_steps paramters and try again.')
            return False
        elif result.status == minizinc.Status.ERROR:
            print(result.status)
        else:
            print(
                'Solver could not find the solution\nThe solving process was interrupted before finding any solution. Perhaps more time is needed!')
            return None
