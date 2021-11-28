'''
Created on Aug 29, 2020

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com
'''

from config import TEMP_DIR
import os
import time
import random
from pysmt.shortcuts import TRUE, Symbol, BVAdd, BVAnd, BVOr, BVMul, BVULE, BVZExt, Solver, types, BV, Equals, write_smtlib
from math import ceil, log2
from core.inputparser import read_relation_file
from core.parsesolution import parse_solver_solution
from core.graphdrawer import draw_graph

class ReduceGDtoSMT:
    """
    ReduceGDtoSMT
    Using the PySMT, this class reduces the guess-and-determine attack and 
    key-bridging to an SMT (or SAT) problem, and then solves a SMT (or a SAT) solver to solve it.

    Created by Hosein Hadipour
    Aug 29, 2020

    inputfile_name: The name of a text file containing the relations
    max_guess:  The maximum number of guessed variables
    max_steps:  Number of state copies
    """

    count = 0

    def __init__(self, inputfile_name=None, outputfile_name='output', max_guess=0, max_steps=0, smt_solver_name='z3',\
        tikz=0, preprocess=1, D=1, dglayout="dot", log=0):
        self.inputfile_name = inputfile_name
        self.output_dir = outputfile_name
        self.rnd_string_tmp = '%030x' % random.randrange(16**30)
        self.max_guess = max_guess
        self.max_steps = max_steps
        self.smt_solver_name = smt_solver_name
        self.dglayout = dglayout
        self.log = log
        # Supported SMT solvers:
        # msat      True (5.6.1)
        # cvc4      True (1.7-prerelease)
        # z3        True (4.8.8)
        # yices     True (2.6.2)
        # btor      True (3.2.1)
        # picosat   True (965)
        # bdd       True (2.0.3)
        self.supported_smt_solvers = [
            'msat', 'cvc4', 'z3', 'yices', 'btor', 'picosat', 'bdd']
        assert(self.smt_solver_name in self.supported_smt_solvers)
        self.smt_solver = Solver(name=smt_solver_name, logic='QF_BV')
        self.smt_formula = TRUE()
        ###############################
        # Read and parse the input file
        parsed_data = read_relation_file(self.inputfile_name, preprocess=preprocess, D=D, log=self.log)
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
        if self.max_guess > self.num_of_vars:
            self.max_guess = self.num_of_vars
            print('Number of guessed variables is at most: %d' %
                  self.num_of_vars)
        self.deductions = self.generate_possible_deductions()
        self.variables_dictionary = dict()
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

    def update_variables_dictionary(self, varlist):
        for v in varlist:
            if v not in self.variables_dictionary.keys():
                self.variables_dictionary[v] = Symbol(
                    name=v, typename=types.BV1)

    def generate_initial_conditions(self):
        """
        This method generates the initial constraints consisting of 
        constrains corresponding to the maximum number of guessed, and 
        known variables in the initial state
        """

        initial_state_vars = ['%s_%d' % (
            v, 0) for v in self.variables if v not in self.known_variables]
        if initial_state_vars != []:
            self.update_variables_dictionary(initial_state_vars)
            bv_length = ceil(log2(len(initial_state_vars))) + 1
            sum = BV(0, width=bv_length)
            for iv in initial_state_vars:
                sum = BVAdd(sum, BVZExt(
                    self.variables_dictionary[iv], bv_length - 1))
            clause = BVULE(sum, BV(self.max_guess, width=bv_length))
            self.smt_solver.add_assertion(clause)
            # self.smt_formula = self.smt_formula.And(clause)

        final_state_target_vars = ['%s_%d' % (
            v, self.max_steps) for v in self.target_variables]
        for fv in final_state_target_vars:
            clause = Equals(self.variables_dictionary[fv], BV(1, width=1))
            self.smt_solver.add_assertion(clause)
            # self.smt_formula = self.smt_formula.And(clause)

        for v in self.known_variables:
            if v != '':
                LHS = self.variables_dictionary[('%s_0' % v)]
                clause = Equals(LHS, BV(1, width=1))
                self.smt_solver.add_assertion(clause)
                # self.smt_formula = self.smt_formula.And(clause)
            
        for v in self.notguessed_variables:
            if v != '':
                LHS = self.variables_dictionary[('%s_0' % v)]
                clause = Equals(LHS, BV(0, width=1))
                self.smt_solver.add_assertion(clause)

    def generate_smt_constraints(self):
        """
        This method generates the smt constraints corresponding to the 
        obtained deductions
        """

        for step in range(self.max_steps):
            for v in self.variables:
                v_new = '%s_%d' % (v, step + 1)
                tau = len(self.deductions[v])
                v_path_variables = ['%s_%d_%d' %
                                    (v, step + 1, i) for i in range(tau)]
                self.update_variables_dictionary([v_new] + v_path_variables)
                #####################################-State variable constraints-#####################################
                ######################################################################################################
                ######################################################################################################
                LHS = BV(0, width=1)
                for pv in v_path_variables:
                    LHS = BVOr(LHS, self.variables_dictionary[pv])
                RHS = self.variables_dictionary[v_new]
                clause = Equals(LHS, RHS)
                self.smt_solver.add_assertion(clause)
                # self.smt_formula = self.smt_formula.And(clause)
                #####################################-Path variable constraints-######################################
                ######################################################################################################
                ######################################################################################################
                for i in range(0, tau):
                    v_connected_variables = ['%s_%d' % (
                        var, step) for var in self.deductions[v][i]]
                    self.update_variables_dictionary(v_connected_variables)
                    LHS = BV(1, width=1)
                    for vc in v_connected_variables:
                        LHS = BVAnd(LHS, self.variables_dictionary[vc])
                    RHS = self.variables_dictionary[v_path_variables[i]]
                    clause = Equals(LHS, RHS)
                    self.smt_solver.add_assertion(clause)
                    # self.smt_formula = self.smt_formula.And(clause)
                ######################################################################################################
                ######################################################################################################
                ######################################################################################################

    def make_model(self):
        """
        This method makes the SMT model, and then write it into an smt file
        """
        print('Generating the SMT model ...')
        start_time = time.time()
        self.generate_smt_constraints()
        self.generate_initial_conditions()
        self.smt_file_path = os.path.join(TEMP_DIR, 'smtmodel_mg%d_ms%d_%s.smt2' % (
            self.max_guess, self.max_steps, self.rnd_string_tmp))
        # smtlib_format = self.smt_formula.to_smtlib(daggify=True)
        # human_readable_formula = serialize(self.smt_formula)        
        elapsed_time = time.time() - start_time
        # write_smtlib(self.smt_formula, self.smt_file_path)
        print('SMT model was generated after %0.2f seconds' % elapsed_time)

    def solve_via_smtsolver(self):
        """
        This method the chosen SMT solver to solve the generated SMT problem
        """

        # If you want to get the same solution in each single execution, chose a fixed value for the following parameter
        self.smt_solver.options.random_seed = random.randint(0, 1000)
        # self.smt_solver.options.random_seed = 1370
        #         
        print('Checking the satisfiability of the constructed SMT model using %s ...' % self.smt_solver_name)
        start_time = time.time()
        ##########################
        ##########################
        if self.time_limit != -1:
            print('Time limit is not currently supported by PySMT.')
            result = self.smt_solver.check_sat()
        else:
            result = self.smt_solver.check_sat()
        #temp = read_smtlib(self.smt_file_path)
        #result = is_sat(temp)
        ##########################
        ##########################
        elapsed_time = time.time() - start_time
        print('Checking was finished after %0.2f seconds' % elapsed_time)
        #solver_info = self.smt_solver.get_info()
        # print(solver_statistics)
        if result == True:
            # Extract the solution
            self.smt_solver_model = self.smt_solver.get_model()
            self.solutions = [0]*(self.max_steps + 1)
            for step in range(self.max_steps + 1):
                state_vars = ['%s_%d' % (v, step) for v in self.variables]
                temp = list(
                    map(lambda vx: self.variables_dictionary[vx], state_vars))
                state_values = list(
                    map(lambda vx: self.smt_solver.get_py_value(vx), temp))
                # state_values = list(map(lambda vx: self.smt_solver_model.get_py_value(vx), temp))
                self.solutions[step] = dict(zip(state_vars, state_values))
            parse_solver_solution(self)
            draw_graph(self.vertices, self.edges, self.known_variables, self.guessed_vars,\
                 self.output_dir, self.tikz, self.dglayout)
            return True
        elif result == False:
            print(
                'The model is UNSAT!\nIncrease the max_guess, and max_steps paramters, and try again.')
            return False
        else:
            print(
                'Solver could not find the solution\nI need more time! The solving process was interrupted before finding any solution.')
            return None
