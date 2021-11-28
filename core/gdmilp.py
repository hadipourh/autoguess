'''
Crated on july 13, 2020

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com
'''

from core.parsesolution import parse_solver_solution
from gurobipy import *
from core.inputparser import read_relation_file
import os
import time
import random
from core.parsesolution import parse_solver_solution
from core.graphdrawer import draw_graph
from config import TEMP_DIR

class ReduceGDtoMILP:
    """
    ReduceGDtoMILP-version4-kb
    This class reduces the guess-and-determine attack and 
    key-bridging to an MILP problem, and then solves it via Gurobi

    Created by Hosein Hadipour
    version4-kb
    July 13, 2020

    mod 0: Maximization
    mod 1: Minimization
    max_guess:  The number of guessed variables in mod 0,
                and an upper bound for the number of guessed variables in mod 1
    max_steps:  Number of state copies 
    """

    count = 0

    def __init__(self, inputfile_name=None, outputfile_name='output', max_guess=0, max_steps=0, direction='min',\
        tikz=0, preprocess=1, D=2, dglayout="dot", log=0):
        self.inputfile_name = inputfile_name
        self.rnd_string_tmp = '%030x' % random.randrange(16**30)        
        self.output_dir = outputfile_name
        self.max_guess = max_guess
        self.max_steps = max_steps
        self.direction = direction
        self.dglayout = dglayout
        self.log = log
        ###############################
        # Read and parse the input file
        parsed_data = read_relation_file(self.inputfile_name, preprocess, D)
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
        if self.max_guess is None:
            self.max_guess = len(self.target_variables)
            print('The number of guessed variables is set to be at most %d' % self.max_guess)
        self.lpfile_name = 'milp_mg%d_ms%d_%s_%s.lp' % (
                            self.max_guess,\
                            max_steps, direction, self.rnd_string_tmp)
        self.deductions = self.generate_possible_deductions()
        # milp_variables is initialized to the variables corresponding to the initial state variables
        self.milp_variables = ['%s_0' % v for v in self.variables]
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

    def generate_objective_function(self):
        """
        This method generates the objective function of the MILP problem
        """

        if self.direction == 'max':
            objective_function = 'Maximize\n'
            final_state = ['%s_%d' % (v, self.max_steps)
                           for v in self.target_variables]
            objective_function += ' + '.join(final_state)
        elif self.direction == 'min':
            objective_function = 'Minimize\n'
            unknown_init_state_vars = [v for v in self.variables if v not in self.known_variables]
            if self.target_weights != None:
                wights = [self.target_weights.get(v, 1) for v in unknown_init_state_vars]
                weighted_init_state = zip(wights, unknown_init_state_vars)
                objective_list = ['%d %s_%d' % (w, v, 0) for (w, v) in weighted_init_state]                
            else:
                objective_list = ['%s_%d' % (v, 0) for v in unknown_init_state_vars]
            objective_function += ' + '.join(objective_list)
        objective_function += '\n'
        return objective_function

    def generate_initial_conditions(self):
        """
        This method generates the initial constraints consisting of 
        constrains corresponding to the maximum number of guessed variables, and 
        number of known variables in the initial state
        """

        initial_constraints = 'Subject To\n'

        unknown_vars = ['%s' % v for v in self.variables if v not in self.known_variables]
        unknown_init_state_vars = ['%s_0' % v for v in unknown_vars]
        if self.target_weights != None:
            LHS1 = ['%d %s_0' % (self.target_weights[v], v) for v in unknown_vars]
            LHS1 = ' + '.join(LHS1)
        else:
            LHS1 = ' + '.join(unknown_init_state_vars)
        RHS1 = self.max_guess
        final_state_target_vars = ['%s_%d' % (
            v, self.max_steps) for v in self.target_variables]
        LHS2 = ' + '.join(final_state_target_vars)
        RHS2 = len(final_state_target_vars)

        if self.direction == 'max':
            # initial_constraints += '%s = %d\n' % (LHS1, RHS1)
            initial_constraints += '%s <= %d\n' % (LHS1, RHS1)
        elif self.direction == 'min':
            initial_constraints += '%s <= %d\n' % (LHS1, RHS1)
            initial_constraints += '%s = %d\n' % (LHS2, RHS2)          

        for v in self.known_variables:
            if v != '':
                initial_constraints += '%s_0 = 1\n' % v

        # Limit the notguessed variables to be equal to 0 in the first step of knowledge propagation
        for v in self.notguessed_variables:
            if v != '':                
                initial_constraints += '%s_0 = 0;\n' % v        
        return initial_constraints
    

    def generate_milp_constraints(self):
        """
        This method generates the milp constraints corresponding to the 
        obtained deductions.
        """

        milp_constraints = ''
        for step in range(self.max_steps):
            for v in self.variables:
                v_old = '%s_%d' % (v, step)
                v_new = '%s_%d' % (v, step + 1)
                tau = len(self.deductions[v])
                v_path_variables = ['%s_%d_%d' %
                                    (v, step + 1, i) for i in range(tau)]
                self.milp_variables.extend([v_new] + v_path_variables)
                #####################################-State variable constraints-#####################################
                ######################################################################################################
                ######################################################################################################
                LHS = ' + '.join(v_path_variables)
                milp_constraints += '\ Constraints corresponding to the state variable %s:\n' % v_new
                if tau == 1:
                    milp_constraints += '%s - %s = 0\n' % (v_new, LHS)
                else:
                    milp_constraints += '-2 %s + %s >= -1\n' % (v_new, LHS)
                    milp_constraints += '%d %s - %s >= 0\n' % (
                        tau, v_new, LHS.replace('+', '-'))
                #####################################-Path variable constraints-######################################
                ######################################################################################################
                ######################################################################################################
                for i in range(tau // 2):
                    v_connected_variables = ['%s_%d' % (
                        var, step) for var in self.deductions[v][i]]
                    LHS = ' - '.join(v_connected_variables)
                    kapa = len(v_connected_variables)
                    milp_constraints += '\ Constraints corresponding to the path variable %s:\n' % v_path_variables[i]
                    if kapa == 1:
                        milp_constraints += '%s - %s = 0\n' % (
                            v_path_variables[i], LHS)
                    else:
                        milp_constraints += '%s - %s >= %d\n' % (
                            v_path_variables[i], LHS, 1 - kapa)
                        milp_constraints += '-%d %s + %s >= 0\n' % (
                            kapa, v_path_variables[i], LHS.replace('-', '+'))
                #####################################-Path variable constraints-######################################
                ######################################################################################################
                ######################################################################################################
                for i in range(tau // 2, tau):
                    v_connected_variables = ['%s_%d' % (
                        var, step) for var in self.deductions[v][i]]
                    LHS = ' - '.join(v_connected_variables)
                    kapa = len(v_connected_variables)
                    milp_constraints += '\ Constraints corresponding to the path variable %s:\n' % v_path_variables[i]
                    if kapa == 1:
                        milp_constraints += '%s - %s = 0\n' % (
                            v_path_variables[i], LHS)
                    else:
                        milp_constraints += '%s - %s >= %d\n' % (
                            v_path_variables[i], LHS, 1 - kapa)
                        milp_constraints += '-%d %s + %s >= 0\n' % (
                            kapa, v_path_variables[i], LHS.replace('-', '+'))
                ######################################################################################################
                ######################################################################################################
                ######################################################################################################
                # Given that the order of putting constraints into an LP file have a great impact on the performance of
                # Gurobi (and other CP solvers), user may want to change the order of constraints inside the generated
                # LP file in order to find a more suitable ordering. It is not known which odering might be the best from
                # the theoretical point of view in general. However, according to my experiences it may be better to put the connected
                # relations closer to each other. For example, change the order of the above blocks to see what impact it has
                # on the performance.
        return milp_constraints

    def declare_binary_variables(self):
        """
        This function declares the binary variables into the generated LP file
        """

        constraints = 'Binary\n'
        for v in self.milp_variables:
            constraints += '%s\n' % v
        return constraints

    def make_model(self):
        """
        This method makes the MILP model, and then write it into an LP file
        """

        print('Generating the MILP model ...')
        start_time = time.time()
        lp_str = self.generate_objective_function()
        lp_str += self.generate_initial_conditions()
        lp_str += self.generate_milp_constraints()
        lp_str += self.declare_binary_variables()
        lp_str += 'End\n'
        lp_file_path = os.path.join(TEMP_DIR, self.lpfile_name)
        elapsed_time = time.time() - start_time
        with open(lp_file_path, 'w') as lpfile:
                lpfile.write(lp_str) 
        if self.log == 1:
            print('MILP model was generated, and written into %s after %0.2f seconds' % (
                lp_file_path, elapsed_time))
        else:
            print('MILP model was generated after %0.2f seconds' % elapsed_time)

    def parse_and_write_solution(self):
        """
        This method parses the obtained soltuion (If MILP model is feasible), 
        and derives the determination flow such that user can simply find
        how the target variables are determined
        """
        
        self.vertices = []
        self.edges = []
        
        separator_line = ''.join(['#']*60)
        output_buffer = ''
        output_buffer += 'Number of relations: %d\n' % self.num_of_relations
        output_buffer += 'Number of variables: %d\n' % self.num_of_vars
        output_buffer += 'Number of target variables: %d\n' % len(
            self.target_variables)
        output_buffer += 'Number of known variables: %d\n' % len(
            self.known_variables)
        output_buffer += 'Number of guessed variables: %d\n' % len(
            self.guessed_vars)
        output_buffer += 'Number of state copies (max_steps): %d\n' % self.max_steps
        output_buffer += 'An upper bound for the number of guessed variables given by user (max_guess): %d\n' % self.max_guess
        output_buffer += '%d out of %d state variables are known after %d state copies\n' % (
            self.final_info, self.num_of_vars, self.max_steps)
        output_buffer += separator_line
        output_buffer += '\nThe following %d variable(s) are guessed:\n%s\n' % (
            len(self.guessed_vars), ', '.join(self.guessed_vars))
        output_buffer += separator_line
        output_buffer += '\nThe following %d variable(s) are initially known:\n%s\n' % (
            len(self.known_variables), ', '.join(self.known_variables))
        output_buffer += separator_line
        output_buffer += '\nTarget variables:\n%s\n' % ', '.join(
            self.target_variables)

        output_buffer += separator_line
        output_buffer += '\nDetermination flow:\n'
        step = 0
        determined_target_variables = dict(
            zip(self.target_variables, [0]*(len(self.target_variables))))
        for v in self.known_variables + self.guessed_vars:
            determined_target_variables[v] = 1
        while step < self.max_steps + 1 and not(all(determined_target_variables.values())):
            sub_title = '\nState %d:\n' % step
            output_buffer += sub_title
            for rel in self.symmetric_relations:
                rel_known_vars = [
                    v for v in rel if self.solutions[step]['%s_%d' % (v, step)] == 1]
                rel_str = ', '.join(rel)
                if len(rel_known_vars) == (len(rel) - 1):
                    determined_var = list(set(rel) - set(rel_known_vars))
                    lhs = ', '.join(rel_known_vars)
                    rhs = ', '.join(determined_var)
                    self.vertices.append(rhs)
                    for vr in rel_known_vars:
                        self.vertices.append(vr)
                        self.edges.append((vr, rhs))
                    if determined_var[0] in self.target_variables:
                        determined_target_variables[determined_var[0]] = 1
                    output = '%s in symmetric relation [%s] are known: %s ===> %s' % (
                        lhs, rel_str, lhs, rhs) + '\n'
                    output_buffer += output
            for rel in self.implication_relations:
                rel_known_vars = [
                    v for v in rel if self.solutions[step]['%s_%d' % (v, step)] == 1]
                rel_str = ', '.join(rel)
                if rel_known_vars == rel[0:-1]:
                    determined_var = [rel[-1]]
                    lhs = ', '.join(rel_known_vars)
                    rhs = ', '.join(determined_var)
                    self.vertices.append(rhs)
                    for vr in rel_known_vars:
                        self.vertices.append(vr)
                        self.edges.append((vr, rhs))
                    if determined_var[0] in self.target_variables:
                        determined_target_variables[determined_var[0]] = 1
                    output = '%s in implication relation [%s] are known: %s ===> %s' % (
                        lhs, rel_str, lhs, rhs) + '\n'
                    output_buffer += output
            output_buffer += separator_line
            step += 1
        self.finally_known = [v for v in self.variables if self.solutions[self.max_steps]['%s_%d' % (v, self.max_steps)] == 1]
        output_buffer += '\nThe following variables are known in final state:\n%s' % ', '.join(self.finally_known)
        with open(self.output_dir, 'w') as outputfile_obj:
            outputfile_obj.write(output_buffer)

    def solve_model(self):
        """
        This method uses Gurobi to solve the obtained MILP problem
        """
        lpfile_path = os.path.join(TEMP_DIR, self.lpfile_name)
        self.milp_model = read(lpfile_path)
        if self.log == 0:
            os.remove(lpfile_path)
        if self.time_limit != -1:
            self.milp_model.params.TimeLimit = self.time_limit
        # 0 (default: Gurobi strikes a balance between finding feasible solution and proving the optimality)
        self.milp_model.params.MIPFocus = 0
        # 1 (quickly find a feasible solution)
        # 2 (proving optimality is in priority)
        # 3 (focus on the best bound)
        self.milp_model.params.Threads = 0  # 0 (default value)
        self.milp_model.params.OutputFlag = 1  # 1 (default value)

        start_time = time.time()
        ##########################
        ##########################
        self.milp_model.optimize()
        ##########################
        ##########################
        elapsed_time = time.time() - start_time
        print('Solving process was finished after %0.2f seconds' % elapsed_time)

        if self.milp_model.Status == GRB.OPTIMAL or self.milp_model.Status == GRB.INTERRUPTED or self.milp_model.Status == GRB.TIME_LIMIT:
            if self.milp_model.SolCount == 0:
                print(
                    'No solution found! Perhaps, I need more time to solve this problem.')
                return
            self.objval = self.milp_model.objval
            self.solutions = [0]*(self.max_steps + 1)
            for step in range(self.max_steps + 1):
                state_vars = ['%s_%d' % (v, step) for v in self.variables]
                state_values = list(
                    map(lambda x: int(self.milp_model.getVarByName(x).Xn), state_vars))
                self.solutions[step] = dict(zip(state_vars, state_values))
            if self.milp_model.SolCount == 0:
                print('Sorry! There is no solution to be parsed.\nTry again please.')
                return
            else:
                if self.log == 1:
                    gurobi_solution_file_name = 'grbsol_mg%d_ms%d_%s.sol' % (
                        self.max_guess, self.max_steps, self.direction)
                    grb_solution_file_path = os.path.join(
                        TEMP_DIR, gurobi_solution_file_name)
                    self.milp_model.write(grb_solution_file_path)                    
                parse_solver_solution(self)
                draw_graph(self.vertices, self.edges, self.known_variables, self.guessed_vars,\
                    self.output_dir, self.tikz, self.dglayout)
        elif self.milp_model.Status == GRB.INFEASIBLE:
            print('The obtained milp model is infeasible')
        else:
            print('Unknown error!')        
