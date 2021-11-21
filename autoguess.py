#!/usr/bin/python3
#-*- coding: UTF-8 -*-
'''
Created on Aug 23, 2020

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com

For more information, feedback or any questions, please contact hsn.hadipour@gmail.com
'''

from core import search
from argparse import ArgumentParser, RawTextHelpFormatter
import os
from config import TEMP_DIR

def startsearch(tool_parameters):
    """
    Starts the search tool for the given parameters
    """

    # Handle program flow
    if tool_parameters["solver"] == 'milp':
        search.search_using_milp(tool_parameters)
    elif tool_parameters["solver"] == 'sat':
        search.search_using_sat(tool_parameters)
    elif tool_parameters["solver"] == 'smt':
        search.search_using_smt(tool_parameters)
    elif tool_parameters["solver"] == 'cp':
        search.search_using_cp(tool_parameters)
    elif tool_parameters["solver"] == 'groebner':
        search.search_using_groebnerbasis(tool_parameters)
    elif tool_parameters["solver"] == 'mark':
        search.search_using_mark(tool_parameters)
    elif tool_parameters["solver"] == 'elim':
        search.search_using_elim(tool_parameters)
    else:
        print('Choose the solver from the following options please:%s' %
              'cp, milp, sat, smt, groebner, mark')
    return

def checkenvironment():
    """
    Basic checks if the environment is set up correctly
    """

    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    return

def loadparameters(args):
    """
    Get parameters from the argument list and inputfile.
    """

    # Load default values
    params = {"inputfile": "./ciphers/AES/relationfile_aes1kp_1r_mg6_ms14.txt",
              "outputfile": "output",
              "maxguess": 50,
              "maxsteps": 5,
              "solver": 'groebner',
              "milpdirection": 'min',
              "timelimit": -1,
              "cpsolver": 'or-tools',
              "satsolver": 'cadical',
              "smtsolver": 'z3',
              "cpoptimization": 1,
              "tikz": 0,
              "preprocess" : 1,
              "D" : 2, 
              "term_ordering": 'degrevlex',
              "overlapping_number": 2,
              "cnf_to_anf_conversion": 'simple',
              "dglayout": "dot",
              "log": 0}

    # Override parameters if they are set on commandline
    if args.inputfile:
        params["inputfile"] = args.inputfile[0]

    if args.outputfile:
        params["outputfile"] = args.outputfile[0]

    if args.maxguess:
        params["maxguess"] = args.maxguess[0]

    if args.maxsteps:
        params["maxsteps"] = args.maxsteps[0]

    if args.solver:
        params["solver"] = args.solver[0]

    if args.milpdirection:
        params["milpdirection"] = args.milpdirection[0]
    
    if args.cpsolver:
        params["cpsolver"] = args.cpsolver[0]
    
    if args.smtsolver:
        params["smtsolver"] = args.smtsolver[0]

    if args.satsolver:
        params["satsolver"] = args.satsolver[0]

    if args.timelimit:
        params["timelimit"] = args.timelimit[0]
    
    if args.cpoptimization:
        params["cpoptimization"] = args.cpoptimization[0]
    
    if args.tikz:
        params["tikz"] = args.tikz[0]

    if args.preprocess:
        params["preprocess"] = args.preprocess[0]
    
    if args.D:
        params["D"] = args.D[0]
    
    if args.term_ordering:
        params["term_ordering"] = args.term_ordering[0]
    
    if args.overlapping_number:
        params["overlapping_number"] = args.overlapping_number[0]
    
    if args.cnf_to_anf_conversion:
        params["cnf_to_anf_conversion"] = args.cnf_to_anf_conversion[0]
    
    if args.dglayout:
        params["dglayout"] = args.dglayout[0]

    if args.log:
        params["log"] = args.log[0]

    return params

def main():
    """
    Parse the arguments and start the request functionality with the provided
    parameters.
    """
    parser = ArgumentParser(description="This tool automates the Guess-and-Determine"
                                        " and Key-Bridging techniques"
                                        " using the variety of CP, MILP, SMT and SAT solvers, as well as"
                                        " the algebraic method based on Groebner basis",
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('--inputfile', nargs=1, help="Use an input file in plain text format")
    parser.add_argument('--outputfile', nargs=1, help="Use an output file to"
                        " write the output into it")
    parser.add_argument('--maxguess', nargs=1, type=int,
                        help="An upper bound for the number of guessed variables")
    parser.add_argument('--maxsteps', nargs=1, type=int,
                        help="An integer number specifying the depth of search")
    parser.add_argument('--solver', nargs=1,
                        choices=['cp', 'milp', 'sat', 'smt', 'groebner'], help="cp = solve the problem using CP solvers\n"
                        "milp = solve the problem using the MILP solvers\n"
                        "sat = solve the problem using the SAT solvers\n"
                        "smt = solve the problem using the SMT solvers\n"
                        "groebner = solve the problem using the Groebner basis algorithm\n"
                        )
    parser.add_argument('--milpdirection', nargs=1,
                        choices=['min', 'max'], help="min = convert the problem to a minimization problem looking for the minimal set of guessed variables.\n"
                        "max = convert the problem to a maximization problem in which the known variables in final state are maximized,\n"
                        "when the size of the initially known variables is equal or less than \"maxguess\"\n")
    parser.add_argument('--cpsolver', nargs=1, type=str,
                        choices=['gecode', 'chuffed', 'coin-bc', 'gurobi', 'picat', 'scip', 'choco', 'or-tools'], help="\n")
    parser.add_argument('--satsolver', nargs=1, type=str,
                        choices=['cadical', 'glucose3', 'glucose4', 'lingeling', 'maplechrono', 'maplecm', 'maplesat', 'minicard', 'minisat22', 'minisat-gh'], help="\n")
    parser.add_argument('--smtsolver', nargs=1, type=str,
                        choices=['msat', 'cvc4', 'z3', 'yices', 'btor', 'bdd'], help="\n")
    parser.add_argument('--cpoptimization', nargs=1, type=int, choices=[0, 1],
                        help="1: Looking for a minimal guess basis \n0: Decides whether a guess basis of size up to \"maxguess\" exists\n")
    parser.add_argument('--timelimit', nargs=1, type=int,
                        help="Set a timelimit for the search in seconds\n")
    parser.add_argument('--tikz', nargs=1, type=int,
                        help="Set to 1 to generate the tikz code of the determination flow graph\n")
    parser.add_argument('--preprocess', nargs=1, type=int,
                        help="Set to 1 to enable the preprocessing phase\n")
    parser.add_argument('--D', nargs=1, type=int,
                        help="It specifies the degree of Macaulay matrix generated in preprocessing phase\n")
    parser.add_argument('--term_ordering', nargs=1, type=str,
                        help="A degree compatible term ordering such as \"degrevlex\" or \"deglex\"\n")
    parser.add_argument('--overlapping_number', nargs=1, type=int,
                        help="A positive integer specifying the overlapping number in block-wise CNF to ANF conversion\n")

    parser.add_argument('--cnf_to_anf_conversion', nargs=1, type=str, choices=['simple', 'blockwise'],
                        help="It specifies the CNF to ANF conversion method\n")

    parser.add_argument('--dglayout', nargs=1, type=str, choices=["dot", "circo", "twopi", "fdp", \
                        "neato", "nop", "nop1", "nop2", "osage", "patchwork", "sfdp"],
                        help="It specifies the layout of determination flow graph\n")
    
    parser.add_argument('--log', nargs=1, type=int, choices=[0, 1],
                        help="By setting this parameter to 1, the intermediate generated files such as CP/MILP/SAT models as well as\n"
                        "some intermediate results are stored inside the temp folder\n")
    



    # Parse command line arguments and construct parameter list.
    args = parser.parse_args()
    params = loadparameters(args)

    # Check if environment is setup correctly.
    checkenvironment()

    # Start the solver
    startsearch(params)

if __name__ == '__main__':
    main()
