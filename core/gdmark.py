'''
Created on May 15, 2021

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com
'''

from logging import root
import os
import time
import random
from core.inputparser import read_relation_file
from threading import Timer
from core.parsesolution import parse_solver_solution
from core.graphdrawer import draw_graph
from config import TEMP_DIR
from operator import itemgetter

class Mark:
    """    
    This class implements the marking algorithm to solve the guess-and-determine problem
    Created by Hosein Hadipour
    May 15, 2020
    """

    count = 0

    def __init__(self, inputfile_name=None, outputfile_name='output', tikz=0, preprocess=1, D=1):
        Mark.count += 1
        self.inputfile_name = inputfile_name
        self.output_dir = outputfile_name
        self.rnd_string_tmp = '%030x' % random.randrange(16**30)       
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
        self.dummy_mapping = parsed_data.get('dummy_mapping', {})
        assert (self.implication_relations == []), "Marking algorithm doesn't support implication relations"
        self.num_of_relations = len(self.symmetric_relations) + len(self.implication_relations)
        self.num_of_vars = len(self.variables)
        ###############################
        self.variables_dictionary = dict()
        self.top_variable_identifier_so_far = 0
        self.deductions = self.generate_and_triangulate_dependency_matrix()
        self.tikz = tikz

    def generate_and_triangulate_dependency_matrix(self):
        """
        This method generates the dependency matrix corresponding to a system of symmetric connection relations
        and then triangulates it
        """
        
        rows = [{"relation" : rel, "weight" : len(rel)} for rel in self.symmetric_relations]
        rows = sorted(rows, key=itemgetter("weight"), reverse = True)
        columns = [{"variable_name" : var, "coefficients" : [int(var in row["relation"]) for row in rows]} for var in self.variables]        
        for i in range(len(columns)):
            variable_name = columns[i]['variable_name']
            columns[i]["weight"] = sum(columns[i]["coefficients"])
            columns[i]["known"] = int(variable_name in self.known_variables)            
        columns = sorted(columns, key = itemgetter("weight"), reverse = False)
        self.dependency_matrix_rows = rows
        self.dependency_matrix_columns = columns
        self.number_of_rows = len(rows)       
    
    def get_index(self, var):
        """
        Given a variable, this function outputs the column's index of that variable
        """

        for i in range(self.num_of_vars):
            if self.dependency_matrix_columns[i]["variable_name"] == var:
                return i


    def find_minimal_guess_basis(self):
        """
        Using marking algorithm, this function finds a guess basis
        """

        self.guess_basis = []
        determined_target_variables = [v for v in self.target_variables if self.dependency_matrix_columns[self.get_index(v)]["known"] == 1]
        i = 1
        while i <= self.num_of_relations and len(determined_target_variables) != len(self.target_variables):
            relation_vars = self.dependency_matrix_rows[-i]['relation']
            relation_vars_indices = [self.get_index(v) for v in relation_vars]
            relation_vars_indices.sort()
            unknown_vars_indices = [ind for ind in relation_vars_indices if self.dependency_matrix_columns[ind]["known"] == 0]
            unknown_vars_indices.sort(reverse=True)
            if len(unknown_vars_indices) == len(relation_vars):
                num_of_guesses = len(unknown_vars_indices) - 1
                self.guess_basis.extend([self.dependency_matrix_columns[j]["variable_name"] for j in unknown_vars_indices[0:num_of_guesses]])
                for j in unknown_vars_indices:
                    self.dependency_matrix_columns[j]["known"] = 1
            elif len(unknown_vars_indices) > 1:
                num_of_guesses = len(unknown_vars_indices) - 1
                self.guess_basis.extend([self.dependency_matrix_columns[j]["variable_name"] for j in unknown_vars_indices[0:num_of_guesses]])
                for j in unknown_vars_indices:
                    self.dependency_matrix_columns[j]["known"] = 1
            elif len(unknown_vars_indices) == 1:
                self.dependency_matrix_columns[unknown_vars_indices[0]]["known"] = 1
            determined_target_variables = [v for v in self.target_variables if self.dependency_matrix_columns[self.get_index(v)]["known"] == 1]
            i += 1
        print("Number of guessed variables %d" % len(self.guess_basis))
        print("Guess basis: %s" % self.guess_basis)
    




