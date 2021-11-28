'''
Created on July 13, 2020

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com
'''

from logging import root
import os
import time
from pysat import solvers
from pysat import formula
from pysat import card
from pysat import pb
from aiger import and_gate, or_gate
import random
from core.inputparser import read_relation_file
from threading import Timer
from core.parsesolution import parse_solver_solution
from core.graphdrawer import draw_graph
from config import TEMP_DIR

class ReduceGDtoSAT:
    """
    ReduceGDtoSAT
    Using the PySAT, this class reduces the guess-and-determine attack and 
    key-bridging to a SAT problem, and then solves it via a SAT solver.

    Created by Hosein Hadipour
    Aug 27, 2020

    inputfile_name: The name of a text file containing the relations
    max_guess:  The maximum number of guessed variables
    max_steps:  Number of state copies
    """

    count = 0

    def __init__(self, inputfile_name=None, outputfile_name='output', max_guess=0, max_steps=0, sat_solver='cadical',\
        tikz=0, preprocess=1, D=2, dglayout="dot", log=0):
        ReduceGDtoSAT.count += 1
        self.inputfile_name = inputfile_name
        self.output_dir = outputfile_name
        self.rnd_string_tmp = '%030x' % random.randrange(16**30)
        self.max_guess = max_guess
        self.max_steps = max_steps
        self.sat_solver_name = sat_solver
        self.supported_sat_solvers = list(solvers.SolverNames.cadical) + list(solvers.SolverNames.glucose4) + list(solvers.SolverNames.glucose3) + list(solvers.SolverNames.lingeling) + list(solvers.SolverNames.maplesat) + list(
            solvers.SolverNames.maplechrono) + list(solvers.SolverNames.maplecm) + list(solvers.SolverNames.minicard) + list(solvers.SolverNames.minisat22) + list(solvers.SolverNames.minisatgh)
        assert(sat_solver in self.supported_sat_solvers)
        self.dglayout = dglayout
        self.log = log
        ###############################
        # Read and parse the input file
        parsed_data = read_relation_file(self.inputfile_name, preprocess=preprocess, D=D, log=self.log)
        self.problem_name = parsed_data['problem_name']
        self.variables = parsed_data['variables']
        self.known_variables = parsed_data['known_variables']
        self.target_variables = parsed_data['target_variables']
        self.target_weights = parsed_data['target_weights']
        self.notguessed_variables = parsed_data['notguessed_variables']
        self.symmetric_relations = parsed_data['symmetric_relations']
        self.implication_relations = parsed_data['implication_relations']
        self.num_of_relations = len(
            self.symmetric_relations) + len(self.implication_relations)
        self.num_of_vars = len(self.variables)
        ###############################
        self.variables_dictionary = dict()
        self.top_variable_identifier_so_far = 0
        self.deductions = self.generate_possible_deductions()
        self.cnf_formula = formula.CNF()
        self.solver = solvers.Solver(name=self.sat_solver_name)
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
                    temp.sort()
                    if temp not in possible_deductions[v]:
                        possible_deductions[v].append(temp)
            for rel in self.implication_relations:
                if v == rel[-1]:
                    temp = rel.copy()
                    temp.remove(v)
                    temp.sort()
                    if temp not in possible_deductions[v]:
                        possible_deductions[v].append(temp)
        return possible_deductions

    def update_variables_dictionary(self, new_vars):
        """
        This method is used to update variables' dictionary
        """
        for nv in new_vars:
            if nv not in self.variables_dictionary.keys():
                self.top_variable_identifier_so_far += 1
                self.variables_dictionary[nv] = self.variables_dictionary.get(
                    nv, self.top_variable_identifier_so_far)

    def generate_boundary_conditions(self):
        """
        This method generates the initial constraints corresponding to the 
        known variables in the initial state as well as the constraint 
        corresponding to the maximum number of guessed variables     
        """

        final_state_target_vars = ['%s_%d' % (
            v, self.max_steps) for v in self.target_variables]
        self.update_variables_dictionary(final_state_target_vars)
        self.cnf_formula.extend([[self.variables_dictionary[fsv]]
                                 for fsv in final_state_target_vars])
        for v in self.known_variables:
            if v != '':
                known_variable_at_state0 = v + '_0'
                self.update_variables_dictionary([known_variable_at_state0])
                self.cnf_formula.append(
                    [self.variables_dictionary[known_variable_at_state0]])
        for v in self.notguessed_variables:
            if v != '':
                temp = v + '_0'
                self.update_variables_dictionary([temp])
                self.cnf_formula.append([-self.variables_dictionary[temp]])
        # Cardinality constraint
        unknown_init_state_vars = [v for v in self.variables if v not in self.known_variables]
        initial_state_vars = ['%s_%d' % (v, 0) for v in unknown_init_state_vars]
        if self.target_weights != None:
            weights = [self.target_weights.get(v, 1) for v in unknown_init_state_vars]
        else:
            weights = None
        self.update_variables_dictionary(initial_state_vars)
        # The default value of encoding is card.Enctype.seqcounter
        # pairwise    = 0
        # seqcounter  = 1 *
        # sortnetwrk  = 2 *
        # cardnetwrk  = 3 *
        # bitwise     = 4
        # ladder      = 5
        # totalizer   = 6 *
        # mtotalizer  = 7
        # kmtotalizer = 8
        # native      = 9        
        # card_constraint = card.CardEnc.atmost(lits=[self.variables_dictionary[v] for v in initial_state_vars],
        #                                       bound=self.max_guess,
        #                                       top_id=self.top_variable_identifier_so_far,
        #                                       encoding=card.EncType.sortnetwrk)
        # Using PyPBLib
        card_constraint = pb.PBEnc.leq(lits=[self.variables_dictionary[v] for v in initial_state_vars],
                                             weights=weights,
                                             bound=self.max_guess,
                                             top_id=self.top_variable_identifier_so_far,
                                             encoding=pb.EncType.binmerge)
        card_clauses = card_constraint.clauses
        self.cnf_formula.extend(card_clauses)

    def generate_sat_constraints(self):
        """
        This method generates the smt constraints corresponding to the 
        obtained deductions
        """

        for step in range(self.max_steps):
            for v in self.variables:
                v_new = '%s_%d' % (v, step + 1)
                self.update_variables_dictionary([v_new])
                tau = len(self.deductions[v])
                v_path_variables = ['%s_%d_%d' %
                                    (v, step + 1, i) for i in range(tau)]
                self.update_variables_dictionary(v_path_variables)
                #####################################-State variable constraints-#####################################
                ######################################################################################################
                ######################################################################################################
                # v_new = Or(v_path_variables)
                self.cnf_formula.append([-self.variables_dictionary[v_new]] + [
                                        self.variables_dictionary[vp] for vp in v_path_variables])
                for vp in v_path_variables:
                    self.cnf_formula.append(
                        [-self.variables_dictionary[vp], self.variables_dictionary[v_new]])
                #####################################-Path variable constraints-######################################
                ######################################################################################################
                ######################################################################################################
                for i in range(0, tau):
                    # v_path_variables[i] = And(v_connected_variables)
                    v_connected_variables = ['%s_%d' % (
                        var, step) for var in self.deductions[v][i]]
                    self.update_variables_dictionary(v_connected_variables)
                    for vc in v_connected_variables:
                        self.cnf_formula.append(
                            [-self.variables_dictionary[v_path_variables[i]], self.variables_dictionary[vc]])
                    self.cnf_formula.append([self.variables_dictionary[v_path_variables[i]]] +
                                            [-self.variables_dictionary[vc] for vc in v_connected_variables])
                ######################################################################################################
                ######################################################################################################
                ######################################################################################################

    def make_model(self):
        """
        This method makes the SAT model and then write it into a CNF file in DIMACS format
        """

        print('Generating the SAT model ...')
        start_time = time.time()
        self.generate_sat_constraints()
        self.generate_boundary_conditions()
        self.cnf_file_path = os.path.join(TEMP_DIR, 'cnf_mg%d_ms%d_%s.cnf' % (
            self.max_guess, self.max_steps, self.rnd_string_tmp))        
        elapsed_time = time.time() - start_time
        if self.log == 1:
            self.cnf_formula.to_file(self.cnf_file_path)
            print('SAT model was generated after %0.2f seconds and was written into %s' % \
                (elapsed_time, self.cnf_file_path))
        else:
            print('SAT model was generated after %0.2f seconds' % elapsed_time)

    def interrupt(self, s):
        s.interrupt()

    def solve_via_satsolver(self):
        """
        Using the pysat toolkit, this method invokes a the chosen sat solver to 
        solve the derived CNF formula
        """

        if self.sat_solver_name in solvers.SolverNames.cadical:
            sat_solver = solvers.Cadical()
        elif self.sat_solver_name in solvers.SolverNames.glucose4:
            sat_solver = solvers.Glucose4()
        elif self.sat_solver_name in solvers.SolverNames.glucose3:
            sat_solver = solvers.Glucose3()
        elif self.sat_solver_name in solvers.SolverNames.lingeling:
            sat_solver = solvers.Lingeling()
        elif self.sat_solver_name in solvers.SolverNames.maplesat:
            sat_solver = solvers.Maplesat()
        elif self.sat_solver_name in solvers.SolverNames.maplechrono:
            sat_solver = solvers.MapleChrono()
        elif self.sat_solver_name in solvers.SolverNames.maplecm:
            sat_solver = solvers.MapleCM()
        elif self.sat_solver_name in solvers.SolverNames.minicard:
            sat_solver = solvers.Minicard()
        elif self.sat_solver_name in solvers.SolverNames.minisat22:
            sat_solver = solvers.Minisat22()
        elif self.sat_solver_name in solvers.SolverNames.minisatgh:
            sat_solver = solvers.MinisatGH()
        else:
            print('Choose a solver from the following list please:%s' %
                  ', '.join(self.supported_sat_solvers))
            return
        sat_solver.append_formula(self.cnf_formula)
        print('\nSolving with %s ...' % self.sat_solver_name)
        start_time = time.time()
        # Regarding time_limit: Note that only MiniSat-like solvers support this functionality (e.g. Cadical and Lingeling do not
        # support it).
        if self.time_limit != -1:
            if self.sat_solver_name in list(solvers.SolverNames.cadical) + list(solvers.SolverNames.lingeling):
                print('time_limit is not supported for the chosen sat solver ... ')
                result = sat_solver.solve()
            else:
                timer = Timer(self.time_limit, self.interrupt, [sat_solver])
                timer.start()
                result = sat_solver.solve_limited(expect_interrupt=True)
        else:
            result = sat_solver.solve()
        elapsed_time = time.time() - start_time
        print('Time used by SAT solver: %0.2f seconds' % elapsed_time)
        if result == True:
            self.satsolver_solution = sat_solver.get_model()
            self.solutions = [0]*(self.max_steps + 1)
            for step in range(self.max_steps + 1):
                state_vars = ['%s_%d' % (v, step) for v in self.variables]
                state_values = list(
                    map(lambda x: int(self.satsolver_solution[self.variables_dictionary[x] - 1] > 0),
                        [st_var for st_var in state_vars]))
                self.solutions[step] = dict(zip(state_vars, state_values))
            parse_solver_solution(self)
            draw_graph(self.vertices, self.edges, self.known_variables, self.guessed_vars,\
                 self.output_dir, self.tikz, self.dglayout)
        elif result == False:
            print('The problem is UNSAT!\n')
        else:
            print(
                'I need more time! The solver was interrupted before finding any solution!')
        sat_solver.delete()
