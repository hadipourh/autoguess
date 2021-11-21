#!/usr/local/bin/sage -python3
'''
Created on Feb 14, 2021

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com

Given a set of Boolean polynomials and a positive integer D, as well as a monomial ordering, 
this class performs two main tasks:
    1- Constructing the Macaulay matrix of degree D
    2- Computing the reduced row echelon form of the derived Macaulay matrix
'''

from sage.all import *
from sage.rings.polynomial.multi_polynomial_sequence import PolynomialSequence
import time
import sys
from datetime import datetime
from argparse import ArgumentParser, RawTextHelpFormatter

class Macaulay:
    """
    Given a set of Boolean polynomials and a positive integer D, as well as a monomial ordering, 
    this class performs two main tasks:
    1- Constructing the Macaulay matrix of degree D
    2- Computing the reduced row echelon form of the derived Macaulay matrix
    """

    count = 0

    def __init__(self, inputfile, outputfile, D=2, term_ordering='deglex'):
        Macaulay.count += 1
        self.inputfile = inputfile
        self.outputfile = outputfile
        self.D = D
        self.term_ordering = term_ordering
        self.algebrize_input_polynomials()

    @parallel
    def get_vars(self, symbolic_equations):
        return list(symbolic_equations.variables())
    
    @parallel
    def ring_evaluator(self, eq):
        return self.PolyRing(eq)

    def algebrize_input_polynomials(self):
        """
        This function converts the given polynomials in string format to a list of boolean polynomials of type PolynomialSequence
        """

        try:
            with open(self.inputfile, 'r') as equations_file:
                string_polynomials = equations_file.read().splitlines()
        except IOError:
            print('%s is not accessible!' % self.inputfile)
            sys.exit()
        symbolic_polynomials = list(map(symbolic_expression, string_polynomials))
        symbolic_variables = list(set(flatten(list(map(self.get_vars, symbolic_polynomials)))))
        self.PolyRing = BooleanPolynomialRing(len(symbolic_variables), names=symbolic_variables, order=self.term_ordering)
        self.polynomial_sequence = PolynomialSequence(list(map(self.ring_evaluator, symbolic_polynomials)))

    def build_macaulay_polynomials(self):
        """
        It constrcuts the Macaulay polynomials with degree at most D corresponding to the given boolean polynomaisl sequence
        """

        self.macaulay_polynomials = []
        nvars = self.PolyRing.n_variables()
        degree_spectrum = sorted(set([f.degree() for f in self.polynomial_sequence]))
        print('Number of algebraic equations: %d' % len(self.polynomial_sequence))
        print('Number of algebraic variables: %d' % nvars)
        print('Number of algebraic monomials: %d' % self.polynomial_sequence.nmonomials())
        print('Spectrum of degrees: %s' % degree_spectrum)
        multiplied_monomials = dict()
        for d in degree_spectrum:
            if d < self.D:
                maximal_exponents = IntegerVectors(self.D - d, nvars, max_part = 1)
                leading_terms = [self.PolyRing({tuple(exponent):1}) for exponent in maximal_exponents]
                monomials = [[mono for mono in list(lead_term.lead_divisors())] for lead_term in leading_terms]
                monomials = list(set(flatten(monomials)))
                multiplied_monomials[d] = monomials
            else:
                multiplied_monomials[d] = [1]
        for f in self.polynomial_sequence:        
            self.macaulay_polynomials.extend([m*f for m in multiplied_monomials[f.degree()]])
        self.macaulay_polynomials = PolynomialSequence(self.macaulay_polynomials)   
    
    def build_macaulay_matrix(self):
        """
        This function generates the Macaulay matrix
        """

        if self.polynomial_sequence.maximal_degree() > 1:
            minimum_degree = min([f.degree() for f in self.polynomial_sequence])
            if self.D < minimum_degree:
                self.D = minimum_degree
            self.build_macaulay_polynomials()
            self.macaulay_matrix, self.macaulay_vars = self.macaulay_polynomials.coefficient_matrix()
        else:
            self.macaulay_matrix, self.macaulay_vars = self.polynomial_sequence.coefficient_matrix()
        print('Macaulay matrix was generated in %s' % str.lower(self.macaulay_matrix.parent().__repr__()))
    
    def gaussian_elimination(self):
        """
        This function applies compute the row redecued echelon form of the derived Macaulay matrix
        """

        print('Gaussian elimination was started - %s' % datetime.now())
        start_time = time.time()
        self.macaulay_matrix.echelonize()
        elapsed_time = time.time() - start_time
        self.dependent_vars = [self.macaulay_vars[i][0] for i in self.macaulay_matrix.pivots() \
            if not self.macaulay_vars[i][0] in [0, 1]]
        self.dependent_vars = list(map(str, self.dependent_vars))
        self.free_vars = [self.macaulay_vars[i][0] for i in self.macaulay_matrix.nonpivots() \
            if not self.macaulay_vars[i][0] in [0, 1]]
        self.free_vars = list(map(str, self.free_vars))
        # print(self.free_vars)
        # print(self.dependent_vars)
        print('#Dependent variables: %d' % len(self.dependent_vars))
        print('#Free variables: %d' % len(self.free_vars))
        print('Gaussian elimination was finished after %0.2f seconds' % elapsed_time)

    def write_result(self):
        """
        This function aims to write the derived polynomials into the output file
        """

        nrows = self.macaulay_matrix.nrows()
        print('Writing the results into the %s - %s' % (self.outputfile, datetime.now()))
        starting_time = time.time()
        with open(self.outputfile, 'w') as outputfile:
            for i in range(nrows):
                output = " + ".join([str(self.macaulay_vars[j, 0]) for j in self.macaulay_matrix.nonzero_positions_in_row(i)])
                if output != '':
                    output += "\n"
                    outputfile.write(output)
        elapsed_time = time.time() - starting_time
        print('Result was written into %s after %0.02f seconds' % (self.outputfile, elapsed_time))

def loadparameters(args):
    """
    Get parameters from the argument list and inputfile.
    """

    # Load default values
    params = {"inputfile": "example2.txt",
              "outputfile": "macaulay_basis.txt",
              "D" : 2,
              "term_ordering": 'deglex'}

    # Override parameters if they are set on commandline
    if args.inputfile:
        params["inputfile"] = args.inputfile[0]

    if args.outputfile:
        params["outputfile"] = args.outputfile[0]
    
    if args.D:
        params["D"] = args.D[0]
    
    if args.term_ordering:
        params["term_ordering"] = args.term_ordering[0]

    return params

def main():
    """
    Parse the arguments and start the request functionality with the provided
    parameters.
    """

    parser = ArgumentParser(description="This tool computes the Macaulay matrix with degree D,"
                                        " given a system of boolean polynomials and"
                                        " a positive integer D",
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('-i', '--inputfile', nargs=1, help="Use an input file in plaintext format to"
                                                     " read the relations from.")
    parser.add_argument('-o', '--outputfile', nargs=1, help="Use an output file to"
                        " write the output into it.")
    parser.add_argument('-D', '--D', nargs=1, type=int,
                        help="A positive integer as the degree of Macaulay matrix.")
    parser.add_argument('-t', '--term_ordering', nargs=1, type=str,
                        help="A term ordering such as deglex or degrevlex.")

    # Parse command line arguments and construct parameter list.
    args = parser.parse_args()
    params = loadparameters(args)
    macaulay = Macaulay(inputfile=params['inputfile'], outputfile=params['outputfile'], \
        D=params['D'], term_ordering=params['term_ordering'])
    macaulay.build_macaulay_matrix()
    macaulay.gaussian_elimination()
    macaulay.write_result()

if __name__ == '__main__':
    main()
