'''
Created on Aug 24, 2020

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

from logging import log
import subprocess
from autoguess.config import PATH_SAGE, TEMP_DIR

def search_using_cp(parameters):
    """
    Convert the guess-and-determine or key-bridging problem to a SMT problem,
    and then solve it
    """

    from .gdcp import ReduceGDtoCP

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
                    drawgraph=parameters.get('drawgraph', True),
                    log=parameters['log'])
    gdsmt.make_model()
    gdsmt.time_limit = parameters['timelimit']
    gdsmt.solve_via_cpsolver()

def search_using_milp(parameters):
    """
    Convert the guess-and-determine or key-bridging problem to an MILP problem, 
    and then solve it
    """
    
    from .gdmilp import ReduceGDtoMILP
    
    gdmilp = ReduceGDtoMILP(inputfile_name=parameters['inputfile'],
                        outputfile_name=parameters['outputfile'],
                        max_guess=parameters['maxguess'],
                        max_steps=parameters['maxsteps'],
                        direction=parameters['milpdirection'],
                        tikz=parameters['tikz'],
                        preprocess=parameters['preprocess'],
                        D=parameters['D'],
                        dglayout=parameters['dglayout'],
                        drawgraph=parameters.get('drawgraph', True),
                        log=parameters['log'])
    gdmilp.make_model()
    gdmilp.time_limit = parameters['timelimit']
    gdmilp.solve_model()

def search_using_sat(parameters):
    """
    Convert the guess-and-detrmine or key-bridging problem to a SAT problem,
    and then solve it
    """
    from .gdz3smt import ReduceGDtoZ3SMT
    from .gdsat import ReduceGDtoSAT

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
                        drawgraph=parameters.get('drawgraph', True),
                        log=parameters["log"])
    gdsat.make_model()
    gdsat.time_limit = parameters['timelimit']
    gdsat.solve_via_satsolver()

def search_using_smt(parameters):
    """
    Convert the guess-and-determine or key-bridging problem to a SMT problem,
    and then solve it
    """

    from .gdsmt import ReduceGDtoSMT

    gdsmt = ReduceGDtoSMT(inputfile_name=parameters['inputfile'],
                        outputfile_name=parameters['outputfile'],
                        max_guess=parameters['maxguess'],
                        max_steps=parameters['maxsteps'],
                        smt_solver_name=parameters['smtsolver'],
                        tikz=parameters['tikz'],
                        preprocess=parameters['preprocess'],
                        D=parameters['D'],
                        dglayout=parameters['dglayout'],
                        drawgraph=parameters.get('drawgraph', True),
                        log=parameters['log'])
    gdsmt.make_model()
    gdsmt.time_limit = parameters['timelimit']
    gdsmt.solve_via_smtsolver()

def search_using_groebnerbasis(parameters):
    """
    Convert the guess-and-determine or key-bridging problem to the problem of computing Groebner basis,
    and then solve it
    """
    import pathlib
    _gdgroebner_path = str(pathlib.Path(__file__).parent / "gdgroebner.py")

    sage_process = subprocess.call([PATH_SAGE, "-python3", _gdgroebner_path, 
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
    from .gdmark import Mark
    gdmark = Mark(inputfile_name=parameters['inputfile'],
                outputfile_name=parameters['outputfile'],
                tikz=parameters['tikz'],
                preprocess=parameters['preprocess'],
                D=parameters['D'])
    gdmark.generate_and_triangulate_dependency_matrix()
    gdmark.find_minimal_guess_basis()


def search_using_elim(parameters):
    from .gdelim import Elim
    gdmark = Elim(inputfile_name=parameters['inputfile'],
                outputfile_name=parameters['outputfile'],
                tikz=parameters['tikz'],
                preprocess=parameters['preprocess'],
                D=parameters['D'])
    gdmark.remove_the_known_variables()
    gdmark.find_minimal_guess_basis()


def search_using_propagate(parameters):
    """
    Propagate knowledge through a system of connection relations
    starting from a given set of initially known variables.
    """
    from .propagate import propagate_knowledge
    from .inputparser import read_relation_file

    parsed_data = read_relation_file(parameters['inputfile'],
                                     preprocess=parameters.get('preprocess', 0),
                                     D=parameters.get('D', 2),
                                     log=parameters.get('log', 0))
    # Start with known variables from the input file
    known_variables = list(parsed_data.get('known_variables', []))
    # Merge any extra variables given via --known on the command line
    known_str = parameters.get('known', None)
    if known_str:
        cli_vars = [v.strip() for v in known_str.split(',') if v.strip()]
        for v in cli_vars:
            if v not in known_variables:
                known_variables.append(v)
    propagate_knowledge(parsed_data=parsed_data, known_variables=known_variables)