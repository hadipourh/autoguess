'''
Created on Feb 6, 2021

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com
'''

import os
import re
import sys
import string
import random
from collections import namedtuple
import subprocess
from config import PATH_SAGE
from config import TEMP_DIR
import time
from datetime import datetime

def ordered_set(seq):
    """
    This function eliminates duplicated elements in a given list, 
    and keeping the order of appearance unchanged, 
    returns a list in which each elements appears only once
    """

    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def read_relation_file(path, preprocess=1, D=2, log=0):
    """
    Reads a relation file in GD format and parses it into a systems of connection relations
    """

    rnd_string_tmp = '%030x' % random.randrange(16**30)
    contents = None
    try:
        if os.path.isfile(path):
            with open(path, 'r') as fileobj:
                contents = fileobj.read()
    except (TypeError, ValueError):
        pass

    contents = contents.strip()
    problem_name = find_problem_name(contents)
    sections = split_contents_by_sections(remove_comments(contents))

    connection_relations = sections.get('connection relations', '')
    algebraic_relations = sections.get('algebraic relations', '')
    algebraic_equations_file = os.path.join(TEMP_DIR, 'algebraic_equations_%s.txt' % rnd_string_tmp)
    if algebraic_relations != '' and preprocess == 1:   
        with open(algebraic_equations_file, 'w') as equations_file:
            equations_file.write(algebraic_relations)
        starting_time = time.time()
        print('Preprocessing phase was started - %s' % datetime.now())
        macaulay_basis_file = os.path.join(TEMP_DIR, 'macaulay_basis_%s.txt' % rnd_string_tmp)
        sage_process = subprocess.call([PATH_SAGE, "-python3", os.path.join("core", "macaulay.py"), 
                                        "-i", algebraic_equations_file,
                                        "-o", macaulay_basis_file,
                                        "-t", "degrevlex",
                                        "-D", str(D)])
        elapsed_time = time.time() - starting_time
        print('Preprocessing phase was finished after %0.4f seconds' % elapsed_time)
        try:
            with open(macaulay_basis_file, 'r') as groebner_basis_file:
                groebner_basis = groebner_basis_file.read()
                temp = groebner_basis_file.readlines()[0:-2]
        except IOError:
            print(macaulay_basis_file + ' is not accessible!')
            sys.exit()
        algebraic_relations += '\n' + groebner_basis
        # algebraic_relations = groebner_basis
        if connection_relations == '':
            connection_relations = algebraic_relations_to_connection_relations(algebraic_relations.split('\n'))
        else:
            connection_relations += '\n' + algebraic_relations_to_connection_relations(algebraic_relations.split('\n'))
    elif algebraic_relations != '' and preprocess == 0:
        if connection_relations == '':
            connection_relations = algebraic_relations_to_connection_relations(algebraic_relations.split('\n'))
        else:
            connection_relations += '\n' + algebraic_relations_to_connection_relations(algebraic_relations.split('\n'))
    symmetric_relations, implication_relations, variables = parse_connection_relations(connection_relations)
    known_variables = sections.get('known', [])
    if known_variables != []:
        known_variables = known_variables.split('\n')
    known_variables.extend([rel[0] for rel in symmetric_relations if len(rel) == 1])
    known_variables = ordered_set(known_variables)
    symmetric_relations = [rel for rel in symmetric_relations if len(rel) != 1]
    target_variables = sections.get('target', [])
    if target_variables != []:
        target_variables = target_variables.split('\n')
    else:
        target_variables = variables
    weights_section = sections.get('weights', [])
    target_weights = None
    if weights_section != []:
        target_weights = dict()
        weights_section = weights_section.split('\n')        
        for element in weights_section:
            var, weight = element.split(' ')
            target_weights[var] = int(weight)
    notguessed_variables = sections.get('not guessed', [])
    if notguessed_variables != []:
        notguessed_variables = notguessed_variables.split('\n')
    parsed_data = {'problem_name': problem_name,
                   'variables': variables,
                   'known_variables': known_variables,
                   'target_variables': target_variables,
                   'target_weights' : target_weights,
                   'notguessed_variables': notguessed_variables,
                   'symmetric_relations': symmetric_relations,
                   'implication_relations': implication_relations}
    if log == 0 and preprocess == 1:
        os.remove(algebraic_equations_file)
        os.remove(macaulay_basis_file)
    return parsed_data


def find_problem_name(contents):
    """
    Find the name of the problem by reading the first comments if it exists.
    If no comments are found 'gdproblem' is used by default.
    """

    pattern = re.compile(r"(?<=#).*?\n", re.DOTALL)
    match = pattern.search(contents)
    if match:
        return match.group().strip()
    return 'gdproblem'


def split_contents_by_sections(contents):
    """
    Split a relation file into multiple sections

    It searches for the following keywords and split the contents by section
    'connection relations', 'algebraic relations', 'known', 'target', 'not guessed'

    Raises ValueError when the given contents is not in a valid GD format    
    """

    keywords = {
        'connection relations': ('connection relation', 'connection relations'),
        'algebraic relations': ('algebraic relation', 'algebraic relations'),
        'known': ('known variables', 'known'),
        'target': ('target variables', 'target'),
        'not guessed': ('not guessed', ),
        'weights': ('weights', 'weight', ),
        'end': ('end', )
    }
    sections = []
    Section = namedtuple('Section', ('name', 'keyword_start', 'keyword_end'))

    for section_name, keywords in keywords.items():
        try:
            match, keyword_start, keyword_end = search_keywords(
                contents, keywords)
            sections.append(Section(section_name.lower(),
                                    keyword_start, keyword_end))
        except AttributeError:
            pass
    # sort by the start index of the section
    sections.sort(key=lambda x: x.keyword_start)

    if sections[-1].name != 'end':
        raise ValueError('File must end with an "end" keyword')

    parsed_sections = {}

    for i in range(len(sections) - 1):
        section = sections[i]
        next_section = sections[i + 1]
        parsed_sections[section.name] = contents[section.keyword_end:next_section.keyword_start].strip()

    return parsed_sections

def search_keywords(contents, keywords):
    """
    Search multiple keywords in a given contents case insensitively, and return the first match

    Raises ValueError when none of the keywords is found in the contents
    """

    sense_pattern = re.compile(
        '|'.join(rf'\b{re.escape(keyword)}\b' for keyword in keywords), re.IGNORECASE)
    match = sense_pattern.search(contents)
    return match.group(), match.start(), match.end()

def remove_comments(contents):
    """
    Remove the comments from the contents
    """
    
    contents = re.sub(re.compile(r"#.*?\n", re.DOTALL), "",
                      contents)  # remove all occurrences of #COMMENT from line
    return contents

def parse_connection_relations(connection_relations):
    variables = []
    symmetric_relations = []
    implication_relations = []
    connection_relations = connection_relations.replace(' ', '')
    connection_relations = connection_relations.split('\n')
    for rel in connection_relations:
        # Extract implication relations
        if '=>' in rel:
            rel = re.split(',|=>', rel)
            implication_relations.append(rel)
        # Extract symmetric relations
        else:
            rel = rel.split(',')
            symmetric_relations.append(rel)
        variables.extend(rel)
    variables = ordered_set(variables)
    return symmetric_relations, implication_relations, variables


def random_prefix_generator(N):
    """
    Generate a random string of length N
    """

    return ''.join(random.choice(string.ascii_uppercase) for _ in range(N))

def get_variables_from_monomial(monomial):
    """
    It is fed by a non-constant monomial like x*y*z and 
    returns a list consisting of given monomial's
    variables. which in this case are: ['x', 'y', 'z']
    """
    assert(not monomial.isdigit())
    temp = monomial.split('*')
    temp.sort()
    return temp

def get_variables_from_list_of_monomials(list_of_monomials):
    """
    It is fed by a list of monomials and returns the variables 
    which are used in the given monomials
    """
    vars = set()
    for monomial in list_of_monomials:
        vars = vars.union(get_variables_from_monomial(monomial))
    temp = list(vars)
    temp.sort()
    return temp

def get_monomials_from_polynomial(polynomial):
    """
    It is fed by a polynomial, and returns its monomials
    """

    monomials = polynomial.split('+')
    if '1' in monomials:
        monomials.remove('1')
    if '0' in monomials:
        monomials.remove('0')
    return list(set(monomials))

def get_monomials_from_list_of_polys(polys):
    """
    It is fed by a list of polynomials and returns
    all of the monomials which are used in the given 
    polynomials
    """

    monomials = set()
    for poly in polys:
        monos = set(get_monomials_from_polynomial(poly))
        monomials = monomials.union(monos)
    return list(monomials)

def degree_of_monomial(monomial):
    """
    Returns the degree of the given monomial
    """

    vars = get_variables_from_monomial(monomial)
    return len(vars)

def algebraic_relations_to_connection_relations(algebraic_relations):
    """
    Generate the connection relations derived from the given algebraic relations by introducing new variables
    It currently work for boolean polynomial relations merely
    """

    connection_relations = []
    if algebraic_relations[-1] == '':
        algebraic_relations[-1:] = []
    algebraic_relations = [poly.replace(' ', '') for poly in algebraic_relations]
    all_monomials = get_monomials_from_list_of_polys(algebraic_relations)
    algebraic_variables = get_variables_from_list_of_monomials(all_monomials)
    dummy_vars_prefix = random_prefix_generator(4)
    substitution_dictionary = dict()
    for monomial in all_monomials:
        if degree_of_monomial(monomial) >= 2:
            monomial_variables = get_variables_from_monomial(monomial)
            var_indices = [algebraic_variables.index(
                x) for x in monomial_variables]
            var_indices = list(map(str, var_indices))
            dummy_var = "{0}{1}".format(
                dummy_vars_prefix, "".join(var_indices))
            if dummy_var not in substitution_dictionary.values():
                connection_relations.append("{0}=>{1}".format(
                    ",".join(monomial_variables), dummy_var))
            substitution_dictionary[monomial] = dummy_var

    for poly in algebraic_relations:
        linearized_relation = [substitution_dictionary.get(term, term) for term in poly.split("+")]
        if '1' in linearized_relation:
            linearized_relation.remove('1')
        if '0' in linearized_relation:
            linearized_relation.remove('0')
        connection_relations.append(",".join(linearized_relation))
    return "\n".join(connection_relations)
