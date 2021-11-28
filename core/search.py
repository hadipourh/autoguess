'''
Created on Aug 24, 2020

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com
'''

from logging import log
import subprocess
from config import PATH_SAGE, TEMP_DIR

def search_using_cp(parameters):
    """
    Convert the guess-and-determine or key-bridging problem to a SMT problem,
    and then solve it
    """

    from core.gdcp import ReduceGDtoCP

    gdsmt = ReduceGDtoCP(inputfile_name=parameters['inputfile'],
                    outputfile_name=parameters['outputfile'],
                    max_guess=parameters['maxguess'],
                    max_steps=parameters['maxsteps'],
                    cp_solver_name=parameters['cpsolver'],
                    cp_optimization=parameters['cpoptimization'],
                    tikz=parameters['tikz'],
                    preprocess=parameters['preprocess'],
                    D=parameters['D'],
                    dglayout=parameters['dglayout'],
                    log=parameters['log'])
    gdsmt.make_model()
    gdsmt.time_limit = parameters['timelimit']
    gdsmt.solve_via_cpsolver()

def search_using_milp(parameters):
    """
    Convert the guess-and-determine or key-bridging problem to an MILP problem, 
    and then solve it
    """
    
    from core.gdmilp import ReduceGDtoMILP
    
    gdmilp = ReduceGDtoMILP(inputfile_name=parameters['inputfile'],
                        outputfile_name=parameters['outputfile'],
                        max_guess=parameters['maxguess'],
                        max_steps=parameters['maxsteps'],
                        direction=parameters['milpdirection'],
                        tikz=parameters['tikz'],
                        preprocess=parameters['preprocess'],
                        D=parameters['D'],
                        dglayout=parameters['dglayout'],
                        log=parameters['log'])
    gdmilp.make_model()
    gdmilp.time_limit = parameters['timelimit']
    gdmilp.solve_model()

def search_using_sat(parameters):
    """
    Convert the guess-and-detrmine or key-bridging problem to a SAT problem,
    and then solve it
    """
    from core.gdz3smt import ReduceGDtoZ3SMT
    from core.gdsat import ReduceGDtoSAT

    # Using Z3 CNF converter:
    # gdsat = ReduceGDtoZ3SMT(inputfile_name=parameters['inputfile'],
    #                     outputfile_name=parameters['outputfile'],
    #                     max_guess=parameters['maxguess'],
    #                     max_steps=parameters['maxsteps'],
    #                     sat_solver=parameters['satsolver'],
    #                     tikz=parameters['tikz'],
    #                     preprocess=parameters['preprocess'],
    #                     D=parameters['D'],
    #                     dglayout=parameters['dglayout'],
    #                     log=parameters["log"])

    # Using PySAT CNF converter:
    gdsat = ReduceGDtoSAT(inputfile_name=parameters['inputfile'],
                        outputfile_name=parameters['outputfile'],
                        max_guess=parameters['maxguess'],
                        max_steps=parameters['maxsteps'],
                        sat_solver=parameters['satsolver'],
                        tikz=parameters['tikz'],
                        preprocess=parameters['preprocess'],
                        D=parameters['D'],
                        dglayout=parameters['dglayout'],
                        log=parameters["log"])
    gdsat.make_model()
    gdsat.time_limit = parameters['timelimit']
    gdsat.solve_via_satsolver()

def search_using_smt(parameters):
    """
    Convert the guess-and-determine or key-bridging problem to a SMT problem,
    and then solve it
    """

    from core.gdsmt import ReduceGDtoSMT

    gdsmt = ReduceGDtoSMT(inputfile_name=parameters['inputfile'],
                        outputfile_name=parameters['outputfile'],
                        max_guess=parameters['maxguess'],
                        max_steps=parameters['maxsteps'],
                        smt_solver_name=parameters['smtsolver'],
                        tikz=parameters['tikz'],
                        preprocess=parameters['preprocess'],
                        D=parameters['D'],
                        dglayout=parameters['dglayout'],
                        log=parameters['log'])
    gdsmt.make_model()
    gdsmt.time_limit = parameters['timelimit']
    gdsmt.solve_via_smtsolver()

def search_using_groebnerbasis(parameters):
    """
    Convert the guess-and-determine or key-bridging problem to the problem of computing Groebner basis,
    and then solve it
    """

    sage_process = subprocess.call([PATH_SAGE, "-python3", "./core/gdgroebner.py", 
    "--inputfile", parameters['inputfile'],
    "--output", parameters['outputfile'],
    "--preprocess", str(parameters['preprocess']),
    "--D", str(parameters['D']),
    "--term_ordering", parameters['term_ordering'],
    "--overlapping_number", str(parameters['overlapping_number']),
    "--temp_dir", TEMP_DIR,
    "--cnf_to_anf_conversion", parameters['cnf_to_anf_conversion'],
    "--log", str(parameters['log'])])

def search_using_mark(parameters):
    from core.gdmark import Mark
    gdmark = Mark(inputfile_name=parameters['inputfile'],
                outputfile_name=parameters['outputfile'],
                tikz=parameters['tikz'],
                preprocess=parameters['preprocess'],
                D=parameters['D'])
    gdmark.generate_and_triangulate_dependency_matrix()
    gdmark.find_minimal_guess_basis()


def search_using_elim(parameters):
    from core.gdelim import Elim
    gdmark = Elim(inputfile_name=parameters['inputfile'],
                outputfile_name=parameters['outputfile'],
                tikz=parameters['tikz'],
                preprocess=parameters['preprocess'],
                D=parameters['D'])
    gdmark.remove_the_known_variables()
    gdmark.find_minimal_guess_basis()