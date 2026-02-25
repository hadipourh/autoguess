'''
Created on May 15, 2021

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

class Elim:
    """    
    This class implements the marking algorithm to solve the guess-and-determine problem
    Created by Hosein Hadipour
    May 15, 2020
    """

    count = 0

    def __init__(self, inputfile_name=None, outputfile_name='output', tikz=0, preprocess=1, D=1, extra_known=None):
        Elim.count += 1
        self.inputfile_name = inputfile_name
        self.output_dir = outputfile_name
        self.rnd_string_tmp = '%030x' % random.randrange(16**30)       
        ###############################
        # Read and parse the input file
        parsed_data = read_relation_file(self.inputfile_name, preprocess=preprocess, D=D, log=self.log, extra_known=extra_known)
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
        self.deductions = self.remove_the_known_variables()
        self.tikz = tikz

    def remove_the_known_variables(self):
        """

        """
                
        known_variables = set(self.known_variables)
        for i in range(len(self.symmetric_relations)):
            self.symmetric_relations[i] = set(self.symmetric_relations[i]).difference(known_variables)            
        # rows = sorted(rows, key=itemgetter("weight"), reverse = True)
        # columns = [{"variable_name" : var, "coefficients" : [int(var in row["relation"]) for row in rows]} for var in self.variables]        
        # for i in range(len(columns)):
        #     variable_name = columns[i]['variable_name']
        #     columns[i]["weight"] = sum(columns[i]["coefficients"])
        #     columns[i]["known"] = int(variable_name in self.known_variables)            
        # columns = sorted(columns, key = itemgetter("weight"), reverse = False)
        # self.dependency_matrix_rows = rows
        # self.dependency_matrix_columns = columns
        # self.number_of_rows = len(rows)

    def find_minimal_guess_basis(self):
        """        
        """

        self.guess_basis = []        
        processed_variables = []
        flag = True
        while flag:
            flag = False
            for v in self.variables:
                cnt = 0
                for rel in self.symmetric_relations:
                    if v in rel:
                        cnt += 1
                        processed_relation = rel
                if cnt == 1:
                    self.symmetric_relations.remove(processed_relation)
                    self.variables.remove(v)
                    processed_variables.append(v)
                    flag = True
                    break
        self.guess_basis = self.variables
        print("Number of guessed variables %d" % len(self.guess_basis))
        print("Guess basis: %s" % self.guess_basis)


    




