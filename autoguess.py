#!/usr/bin/python3
#-*- coding: UTF-8 -*-
'''
Created on Aug 23, 2020

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com

For more information, feedback or any questions, please contact hsn.hadipour@gmail.com

MIT License

Copyright (c) 2021 Hosein Hadipour

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

from core import search
from argparse import ArgumentParser, RawTextHelpFormatter
import os
from config import TEMP_DIR
import minizinc
from pysat import solvers

def start_search(params):
    """
    Starts the search tool for the given parameters
    """
    solver = params["solver"]
    search_methods = {
        'milp': search.search_using_milp,
        'sat': search.search_using_sat,
        'smt': search.search_using_smt,
        'cp': search.search_using_cp,
        'groebner': search.search_using_groebnerbasis,
        'mark': search.search_using_mark,
        'elim': search.search_using_elim
    }

    if solver in search_methods:
        search_methods[solver](params)
    else:
        print('Choose the solver from the following options: cp, milp, sat, smt, groebner, mark')

def check_environment():
    """
    Basic checks if the environment is set up correctly
    """
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

def load_parameters(args):
    """
    Get parameters from the argument list and input file.
    """
    params = {
        # "inputfile": "./ciphers/AES/relationfile_aes1kp_1r_mg6_ms14.txt",
        # "inputfile": "./ciphers/Example1/relationfile.txt",
        "inputfile": "./ciphers/Example4/algebraic_relations.txt",
        "outputfile": "output",
        "maxguess": 50,
        "maxsteps": 5,
        "solver": 'cp',
        "milpdirection": 'min',
        "timelimit": -1,
        "cpsolver": 'cp-sat', # for newer versions of MiniZinc, use 'cp-sat' to use Or-tools
        "satsolver": 'cadical153',
        "smtsolver": 'z3',
        "cpoptimization": 1,
        "tikz": 0,
        "preprocess": 1,
        "D": 2,
        "term_ordering": 'degrevlex',
        "overlapping_number": 2,
        "cnf_to_anf_conversion": 'simple',
        "dglayout": "dot",
        "log": 1
    }

    for key in params:
        if getattr(args, key, None):
            params[key] = getattr(args, key)[0]

    return params

def main():
    """
    Parse the arguments and start the request functionality with the provided parameters.
    """
    parser = ArgumentParser(description="This tool automates the Guess-and-Determine"
                                        " and Key-Bridging techniques"
                                        " using a variety of CP, MILP, SMT and SAT solvers, as well as"
                                        " the algebraic method based on Groebner basis",
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('-i', '--inputfile', nargs=1, help="Use an input file in plain text format")
    parser.add_argument('-o', '--outputfile', nargs=1, help="Use an output file to write the output into it")
    parser.add_argument('-mg', '--maxguess', nargs=1, type=int, help="An upper bound for the number of guessed variables")
    parser.add_argument('-ms', '--maxsteps', nargs=1, type=int, help="An integer number specifying the depth of search")
    parser.add_argument('-s', '--solver', nargs=1, choices=['cp', 'milp', 'sat', 'smt', 'groebner'], help="Solver choice")
    parser.add_argument('-milpd', '--milpdirection', nargs=1, choices=['min', 'max'], help="MILP direction")
    parser.add_argument('-cps', '--cpsolver', nargs=1, type=str, choices=[solver_name for solver_name in minizinc.default_driver.available_solvers().keys()], help="CP solver choice", default='cp-sat')
    parser.add_argument('-sats', '--satsolver', nargs=1, type=str, choices=[solver for solver in solvers.SolverNames.__dict__.keys() if not solver.startswith('__')], help="SAT solver choice")
    parser.add_argument('-smts', '--smtsolver', nargs=1, type=str, choices=['msat', 'cvc4', 'z3', 'yices', 'bdd'], help="SMT solver choice")
    parser.add_argument('-cpopt', '--cpoptimization', nargs=1, type=int, choices=[0, 1], help="CP optimization")
    parser.add_argument('-tl', '--timelimit', nargs=1, type=int, help="Time limit for the search in seconds")
    parser.add_argument('-tk', '--tikz', nargs=1, type=int, help="Generate the tikz code of the determination flow graph")
    parser.add_argument('-prep', '--preprocess', nargs=1, type=int, help="Enable the preprocessing phase")
    parser.add_argument('-D', '--D', nargs=1, type=int, help="Degree of Macaulay matrix generated in preprocessing phase")
    parser.add_argument('-tord', '--term_ordering', nargs=1, type=str, help="Term ordering such as 'degrevlex' or 'deglex'")
    parser.add_argument('-oln', '--overlapping_number', nargs=1, type=int, help="Overlapping number in block-wise CNF to ANF conversion")
    parser.add_argument('-cnf2anf', '--cnf_to_anf_conversion', nargs=1, type=str, choices=['simple', 'blockwise'], help="CNF to ANF conversion method")
    parser.add_argument('-dgl', '--dglayout', nargs=1, type=str, choices=["dot", "circo", "twopi", "fdp", "neato", "nop", "nop1", "nop2", "osage", "patchwork", "sfdp"], help="Layout of determination flow graph")
    parser.add_argument('-log', '--log', nargs=1, type=int, choices=[0, 1], help="Store intermediate generated files and results")

    args = parser.parse_args()
    params = load_parameters(args)

    check_environment()
    start_search(params)

if __name__ == '__main__':
    main()
