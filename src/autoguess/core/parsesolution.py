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
from .varnames import step_var
def parse_solver_solution(gd):
    """
    This method parses the obtained solution (if exists), into a human readable format
    """
    
    gd.vertices = []
    gd.edges = []
    gd.guessed_vars = [v for v in gd.variables if (gd.solutions[0][step_var(v, 0)] == 1) and (v not in gd.known_variables)]
    numbers_of_guesses = sum(gd.solutions[0].values()) - len(gd.known_variables)
    
    if numbers_of_guesses != len(gd.guessed_vars):
        print('There exist duplicated variables among the known variables!')
    
    gd.final_info = sum(gd.solutions[gd.max_steps].values())

    # Build pretty guessed-variables list
    guessed_vars_pretty = []
    for v in gd.guessed_vars:
        if hasattr(gd, "dummy_mapping") and v in gd.dummy_mapping:
            guessed_vars_pretty.append(f"{v} (represents: {' * '.join(gd.dummy_mapping[v])})")
        else:
            guessed_vars_pretty.append(v)

    print('\n' + '=' * 60)
    print('RESULTS')
    print('=' * 60)
    print(f'Number of guesses:         {numbers_of_guesses}')
    print(f'Known in final state:      {gd.final_info} / {len(gd.variables)}')
    print(f'Max steps used:            {gd.max_steps}')
    print('-' * 60)
    print(f'Guessed variable(s) ({len(gd.guessed_vars)}):')
    print(f'  {", ".join(guessed_vars_pretty)}')
    print('=' * 60)
    
    separator_line = '#' * 60
    output_buffer = ''
    
    output_buffer += 'Number of relations: %d\n' % gd.num_of_relations
    output_buffer += 'Number of variables: %d\n' % gd.num_of_vars
    output_buffer += 'Number of target variables: %d\n' % len(gd.target_variables)
    output_buffer += 'Number of known variables: %d\n' % len(gd.known_variables)
    output_buffer += 'Number of guessed variables: %d\n' % len(gd.guessed_vars)
    output_buffer += 'Number of state copies (max_steps): %d\n' % gd.max_steps
    output_buffer += 'An upper bound for the number of guessed variables given by user (max_guess): %d\n' % gd.max_guess
    output_buffer += '%d out of %d state variables are known after %d state copies\n' % (gd.final_info, gd.num_of_vars, gd.max_steps)
    output_buffer += separator_line
    guessed_vars_pretty = []
    for v in gd.guessed_vars:
        if hasattr(gd, "dummy_mapping") and v in gd.dummy_mapping:
            guessed_vars_pretty.append(f"{v} (represents: {' * '.join(gd.dummy_mapping[v])})")
        else:
            guessed_vars_pretty.append(v)
    output_buffer += f"\nThe following {len(gd.guessed_vars)} variable(s) are guessed:\n{', '.join(guessed_vars_pretty)}\n"
    output_buffer += separator_line
    output_buffer += '\nThe following %d variable(s) are initially known:\n%s\n' % (len(gd.known_variables), ', '.join(gd.known_variables))
    output_buffer += separator_line
    output_buffer += '\nTarget variables:\n%s\n' % ', '.join(gd.target_variables)
    output_buffer += separator_line
    output_buffer += '\nDetermination flow:\n'
    
    step = 0
    variables_deductor_relations = {v: {'deductor_relations': [], 'number_of_deductions': 0} for v in gd.variables}
    detector_relations = []
    used_symmetric_relations = []
    used_implication_relations = []
    determined_target_variables = {v: 0 for v in gd.target_variables}
    
    for v in gd.known_variables + gd.guessed_vars:
        determined_target_variables[v] = 1
    
    while step < gd.max_steps + 1 and not all(determined_target_variables.values()):
        output_buffer += '\nState %d:\n' % step
        
        for rel in gd.symmetric_relations:
            rel_known_vars = [v for v in rel if gd.solutions[step][step_var(v, step)] == 1]
            if len(rel_known_vars) == (len(rel) - 1):
                determined_var = list(set(rel) - set(rel_known_vars))
                lhs = ', '.join(rel_known_vars)
                rhs = ', '.join(determined_var)
                gd.vertices.append(rhs)
                variables_deductor_relations[determined_var[0]]['number_of_deductions'] += 1
                variables_deductor_relations[determined_var[0]]['deductor_relations'].append(', '.join(rel))
                for vr in rel_known_vars:
                    gd.vertices.append(vr)
                    gd.edges.append((vr, rhs, variables_deductor_relations[determined_var[0]]['number_of_deductions']))
                if determined_var[0] in gd.target_variables:
                    determined_target_variables[determined_var[0]] = 1
                output_buffer += '%s in symmetric relation [%s] are known: %s ===> %s\n' % (lhs, ', '.join(rel), lhs, rhs)
                used_symmetric_relations.append(rel)
        
        for rel in gd.implication_relations:
            rel_known_vars = [v for v in rel if gd.solutions[step][step_var(v, step)] == 1]
            if rel_known_vars == rel[0:-1]:
                determined_var = [rel[-1]]
                lhs = ', '.join(rel_known_vars)
                rhs = ', '.join(determined_var)
                gd.vertices.append(rhs)
                variables_deductor_relations[determined_var[0]]['number_of_deductions'] += 1
                variables_deductor_relations[determined_var[0]]['deductor_relations'].append(', '.join(rel[0:-1]) + ' => ' + rel[-1])
                for vr in rel_known_vars:
                    gd.vertices.append(vr)
                    gd.edges.append((vr, rhs, variables_deductor_relations[determined_var[0]]['number_of_deductions']))
                if determined_var[0] in gd.target_variables:
                    determined_target_variables[determined_var[0]] = 1
                output_buffer += '%s in implication relation [%s] are known: %s ===> %s\n' % (lhs, ', '.join(rel[0:-1]) + ' => ' + rel[-1], lhs, rhs)
                used_implication_relations.append(rel)
        
        output_buffer += separator_line
        step += 1
    
    for rel in gd.symmetric_relations:
        if rel not in used_symmetric_relations:
            detector_relations.append(', '.join(rel))
    
    for rel in gd.implication_relations:
        if rel not in used_implication_relations:
            detector_relations.append(', '.join(rel[0:-1]) + ' => ' + rel[-1])
    
    gd.finally_known = [v for v in gd.variables if gd.solutions[gd.max_steps][step_var(v, gd.max_steps)] == 1]
    output_buffer += '\nThe following variables are known in final state:\n%s\n' % ', '.join(gd.finally_known)
    output_buffer += separator_line
    output_buffer += '\nThe following relations have not been used in determination (they might be used to check the correctness of guesses):\n'
    output_buffer += '\n'.join(detector_relations)
    output_buffer += '\n' + separator_line
    output_buffer += '\nThe following variables can be deduced from multiple paths:\n'
    
    for v in gd.variables:
        if variables_deductor_relations[v]['number_of_deductions'] > 1:
            output_buffer += '\n%s can be deduced from:\n%s\n' % (v, '\n'.join(variables_deductor_relations[v]['deductor_relations']))
    
    if hasattr(gd, 'dummy_mapping') and gd.dummy_mapping:
        output_buffer += '\n' + separator_line
        output_buffer += '\nDummy variable mapping (introduced during linearization of algebraic relations):\n'
        output_buffer += 'Total dummy variables: %d\n\n' % len(gd.dummy_mapping)
        for dummy_var, original_vars in sorted(gd.dummy_mapping.items()):
            output_buffer += '  %s = %s\n' % (dummy_var, ' * '.join(original_vars))
        output_buffer += '\n' + separator_line

    with open(gd.output_dir, 'w') as outputfile_obj:
        outputfile_obj.write(output_buffer)
