'''
Created on July 13, 2020

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com
'''

import os
import time
from pysat import solvers
from pysat import formula
import random
from .inputparser import read_relation_file
from threading import Timer
import z3
from core.parsesolution import parse_solver_solution
from core.graphdrawer import draw_graph
from config import TEMP_DIR


class ReduceGDtoZ3SMT:
    """
    ReduceGDtoZ3SMT-version 2
    Using the Z3 SMT solver, this class reduces the guess-and-determine attack and 
    key-bridging to an SMT (or SAT) problem, and then solves it via Z3 (or a SAT solver).

    Created by Hosein Hadipour
    July 13, 2020

    inputfile_name: The name of a text file containing the relations
    max_guess:  The maximum number of guessed variables
    max_steps:  Number of state copies
    """
    count = 0

    def __init__(self, inputfile_name=None, outputfile_name='output', max_guess=0, max_steps=0, sat_solver='cadical',\
        tikz=0, preprocess=1, D=2, dglayout="dot", log=0):
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
        self.notguessed_variables = parsed_data['notguessed_variables']
        self.symmetric_relations = parsed_data['symmetric_relations']
        self.implication_relations = parsed_data['implication_relations']
        self.num_of_relations = len(
            self.symmetric_relations) + len(self.implication_relations)
        self.num_of_vars = len(self.variables)
        ###############################
        self.deductions = self.generate_possible_deductions()
        self.solver = z3.Solver()
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

    def generate_initial_conditions(self):
        """
        This method generates the initial constraints consisting of 
        constrains corresponding to the maximum number of guessed, and 
        known variables in the initial state
        """
        # initial_state_vars = list(map(z3.Bool, ['%s_%d' % (
        #     v, 0) for v in self.variables if v not in self.known_variables]))
        # self.solver.add(z3.Sum([z3.If(initial_state_vars[i], 1, 0)
        #                     for i in range(len(initial_state_vars))]) <= self.max_guess)
        initial_state_vars = list(map(lambda x: (z3.Bool(x), 1), ['%s_%d' % (
            v, 0) for v in self.variables if v not in self.known_variables]))
        if initial_state_vars != []:
            self.solver.add(z3.PbLe([initial_state_vars[i] for i in range(
                len(initial_state_vars))], self.max_guess))

        final_state_target_vars = list(
            map(z3.Bool, ['%s_%d' % (v, self.max_steps) for v in self.target_variables]))
        self.solver.add(z3.And(final_state_target_vars) == True)
        for v in self.known_variables:
            if v != '':
                self.solver.add(z3.Bool('%s_0' % v) == True)
        for v in self.notguessed_variables:
            if v != '':
                self.solver.add(z3.Bool('%s_0' % v) == False)

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
                #####################################-State variable constraints-#####################################
                ######################################################################################################
                ######################################################################################################
                LHS = z3.Or(list(map(z3.Bool, v_path_variables)))
                RHS = z3.Bool(v_new)
                self.solver.add(LHS == RHS)
                #####################################-Path variable constraints-######################################
                ######################################################################################################
                ######################################################################################################
                for i in range(0, tau):
                    v_connected_variables = list(
                        map(z3.Bool, ['%s_%d' % (var, step) for var in self.deductions[v][i]]))
                    LHS = z3.And(v_connected_variables)
                    RHS = z3.Bool(v_path_variables[i])
                    self.solver.add(LHS == RHS)
                ######################################################################################################
                ######################################################################################################
                ######################################################################################################

    def make_model(self):
        """
        This method makes the SMT model, and then write it into an smt file
        """
        print('Generating the SMT model ...')
        start_time = time.time()
        self.generate_initial_conditions()
        self.generate_smt_constraints()
        z3.set_param(smtlib2_compliant=True)
        smt2_model = self.solver.to_smt2()
        file_path = os.path.join(TEMP_DIR, 'smtmodel_mg%d_ms%d.smt2' % (
            self.max_guess, self.max_steps))
        elapsed_time = time.time() - start_time
        if self.log == 1:
            with open(file_path, 'w') as outputfile:
                outputfile.write(smt2_model)
            print('SMT model was generated after %0.2f seconds and was written into %s'\
                 % (elapsed_time, file_path))
        else:
            print('SMT model was generated after %0.2f seconds' % elapsed_time)
        

    def convert_smt_to_cnf(self):
        """
        This method encodes the obtained SMT problem to CNF

        Goal is a collection of constraints we want to find a solution or show to be unsatisfiable (infeasible).

        Goals are processed using Tactics. A Tactic transforms a goal into a set of subgoals.
        A goal has a solution if one of its subgoals has a solution.
        A goal is unsatisfiable if all subgoals are unsatisfiable.
        """
        G = z3.Goal()
        G.add(self.solver.assertions())
        # z3.set_option("sat.cardinality.encoding", "circuit")
        # z3.set_option("sat.cardinality.encoding", "sorting")
        cnf_format = z3.Then('simplify', 'card2bv', 'tseitin-cnf')
        # cnf_format = z3.Then("card2bv", "tseitin-cnf")
        # cnf_format = z3.Tactic("card2bv")
        print('Converting the SMT problem to CNF in dimacs format ...')
        start_time = time.time()
        temp = cnf_format(G)
        """
        Regarding dimcas mehod:
        'dimacs' convert a goal into a DIMACS formatted string. The goal must be in CNF. 
        You can convert a goal to CNF by applying the tseitin-cnf tactic. Bit-vectors are not 
        automatically converted to Booleans either, so if the caller intends to preserve satisfiability, 
        it should apply bit-blasting tactics. Quantifiers and theory atoms will not be encoded.
        """
        dimacs_format = temp[0].dimacs()
        conversion_table = list(
            filter(lambda x: x[0:2] == 'c ', dimacs_format.split('\n')))
        self.dimacs_vars_dict = dict()
        for row in conversion_table:
            row = row.split(' ')[1:]
            self.dimacs_vars_dict[row[1]] = int(row[0])
        dimacs_file_name = 'cnf_mg%d_ms%d_%s.cnf' % (
            self.max_guess, self.max_steps, self.rnd_string_tmp)
        self.cnf_file_path = os.path.join(TEMP_DIR, dimacs_file_name)
        with open(self.cnf_file_path, 'w') as outputfile:
            outputfile.write(dimacs_format)
        elapsed_time = time.time() - start_time
        if self.log == 1:
            print('SMT was converted to the CNF after %0.2f seconds and was written into %s' %\
                 (elapsed_time, self.cnf_file_path))
        else:
            print('SMT was converted to the CNF after %0.2f seconds' % elapsed_time)

    def interrupt(self, s):
        s.interrupt()

    def solve_via_satsolver(self):
        """
        Using the pysat toolkit, this method invokes the chosen sat solver to 
        solve the derived CNF formula
        """

        self.convert_smt_to_cnf()
        cnf_formula = formula.CNF(self.cnf_file_path)
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
        sat_solver.append_formula(cnf_formula)
        print('\nSolving via a SAT solver ...')
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
                    map(lambda x: int(self.satsolver_solution[self.dimacs_vars_dict[x] - 1] > 0),
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
        if self.log == 0:
            os.remove(self.cnf_file_path)

    def solve_via_smtsolver(self):
        """
        This method uses Z3 to solve the obtained SMT problem
        """
        # If you want to produce a new solution at each new run uncomment this line
        z3.set_param('smt.random_seed', int(time.time()))
        # If you want get the same solution as before, uncomment this line
        # z3.set_param('smt.random_seed', 1370)
        # z3.set_param(verbose=2)
        # z3.set_param(memory_max_size=8192)
        # self.solver.set("sat.cardinality.solver", True)
        z3.set_param('parallel.enable', True)
        print('Checking the satisfiablity of the obtained SMT model using z3-solver ...')
        if self.time_limit != -1:
            self.solver.set(timeout=self.time_limit * 1000)
        start_time = time.time()
        ##########################
        ##########################
        result = self.solver.check()
        ##########################
        ##########################
        elapsed_time = time.time() - start_time
        print('Checking was finished after %0.2f seconds' % elapsed_time)

        solver_statistics = self.solver.statistics()
        # print(solver_statistics)
        if result == z3.sat:
            # self.solution = self.solver.model()
            # Extract the solution
            self.solver_model = self.solver.model()
            self.solutions = [0]*(self.max_steps + 1)
            for step in range(self.max_steps + 1):
                state_vars = ['%s_%d' % (v, step) for v in self.variables]
                z3_state_vars = list(
                    map(z3.Bool, ['%s_%d' % (v, step) for v in self.variables]))
                state_values = list(
                    map(int, [z3.is_true(self.solver_model[st_var]) for st_var in z3_state_vars]))
                self.solutions[step] = dict(zip(state_vars, state_values))
            parse_solver_solution(self)
            draw_graph(self.vertices, self.edges, self.known_variables, self.guessed_vars,\
                 self.output_dir, self.tikz)
        elif result == z3.unsat:
            print(
                'The model is UNSAT!\nIncrease the max_guess, and max_steps paramters, and try again.')
        elif result == z3.unknown:
            print(
                'Solver could not find the solution\nI need more time! The solving process was interrupted before finding any solution.')
