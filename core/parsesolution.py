'''
Created on Aug 24, 2020

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com
'''

def parse_solver_solution(gd):
        """
        This method parses the obtained solution (if exists), into a human readable format
        """
        
        gd.vertices = []
        gd.edges = []
        gd.guessed_vars = [v for v in gd.variables if (gd.solutions[0]
                             ['%s_0' % v] == 1) and (v not in gd.known_variables)]
        numbers_of_guesses = sum(gd.solutions[0].values()) - len(gd.known_variables)
        if numbers_of_guesses != len(gd.guessed_vars):
            print('There exist duplicated variables among the known variables!')
        gd.final_info = sum(gd.solutions[gd.max_steps].values())
        print('Number of guesses: %d' % numbers_of_guesses)
        temp = [v for v in gd.variables if v ]
        print('Number of known variables in the final state: %d out of %d' % (
            gd.final_info, len(gd.variables)))
        print('The following %d variable(s) are guessed:' %
              len(gd.guessed_vars))
        print(', '.join(gd.guessed_vars))
        separator_line = ''.join(['#']*60)
        output_buffer = ''
        output_buffer += 'Number of relations: %d\n' % gd.num_of_relations
        output_buffer += 'Number of variables: %d\n' % gd.num_of_vars
        output_buffer += 'Number of target variables: %d\n' % len(
            gd.target_variables)
        output_buffer += 'Number of known variables: %d\n' % len(
            gd.known_variables)
        output_buffer += 'Number of guessed variables: %d\n' % len(
            gd.guessed_vars)
        output_buffer += 'Number of state copies (max_steps): %d\n' % gd.max_steps
        output_buffer += 'An upper bound for the number of guessed variables given by user (max_guess): %d\n' % gd.max_guess
        output_buffer += '%d out of %d state variables are known after %d state copies\n' % (
            gd.final_info, gd.num_of_vars, gd.max_steps)
        output_buffer += separator_line
        output_buffer += '\nThe following %d variable(s) are guessed:\n%s\n' % (
            len(gd.guessed_vars), ', '.join(gd.guessed_vars))
        output_buffer += separator_line
        output_buffer += '\nThe following %d variable(s) are initially known:\n%s\n' % (
            len(gd.known_variables), ', '.join(gd.known_variables))
        output_buffer += separator_line
        output_buffer += '\nTarget variables:\n%s\n' % ', '.join(
            gd.target_variables)

        output_buffer += separator_line
        output_buffer += '\nDetermination flow:\n'
        step = 0
        variables_deductor_relations = dict()
        for v in gd.variables:
            variables_deductor_relations[v] = {'deductor_relations' : [], 'number_of_deductions' : 0}
        detector_relations = []
        used_symmetric_relations = []
        used_implication_relations = []
        determined_target_variables = dict(
            zip(gd.target_variables, [0]*(len(gd.target_variables))))
        for v in gd.known_variables + gd.guessed_vars:
            determined_target_variables[v] = 1
        while step < gd.max_steps + 1 and not(all(determined_target_variables.values())):
            sub_title = '\nState %d:\n' % step
            output_buffer += sub_title
            for rel in gd.symmetric_relations:
                rel_known_vars = [
                    v for v in rel if gd.solutions[step]['%s_%d' % (v, step)] == 1]
                rel_str = ', '.join(rel)
                if len(rel_known_vars) == (len(rel) - 1):
                    determined_var = list(set(rel) - set(rel_known_vars))                    
                    lhs = ', '.join(rel_known_vars)
                    rhs = ', '.join(determined_var)
                    gd.vertices.append(rhs)
                    variables_deductor_relations[determined_var[0]]['number_of_deductions'] += 1
                    variables_deductor_relations[determined_var[0]]['deductor_relations'].append(rel_str)                
                    for vr in rel_known_vars:
                        gd.vertices.append(vr)
                        gd.edges.append((vr, rhs, variables_deductor_relations[determined_var[0]]['number_of_deductions']))
                    if determined_var[0] in gd.target_variables:
                        determined_target_variables[determined_var[0]] = 1
                    output = '%s in symmetric relation [%s] are known: %s ===> %s' % (
                        lhs, rel_str, lhs, rhs) + '\n'
                    output_buffer += output
                    used_symmetric_relations += [rel]
            
            for rel in gd.implication_relations:
                rel_known_vars = [
                    v for v in rel if gd.solutions[step]['%s_%d' % (v, step)] == 1]
                rel_str = ', '.join(rel[0:-1]) + ' => ' + rel[-1]
                if rel_known_vars == rel[0:-1]:
                    determined_var = [rel[-1]]
                    lhs = ', '.join(rel_known_vars)
                    rhs = ', '.join(determined_var)
                    gd.vertices.append(rhs)
                    variables_deductor_relations[determined_var[0]]['number_of_deductions'] += 1
                    variables_deductor_relations[determined_var[0]]['deductor_relations'].append(rel_str)           
                    for vr in rel_known_vars:
                        gd.vertices.append(vr)
                        gd.edges.append((vr, rhs, variables_deductor_relations[determined_var[0]]['number_of_deductions']))
                    if determined_var[0] in gd.target_variables:
                        determined_target_variables[determined_var[0]] = 1
                    output = '%s in implication relation [%s] are known: %s ===> %s' % (
                        lhs, rel_str, lhs, rhs) + '\n'
                    output_buffer += output
                    used_implication_relations += [rel]
            output_buffer += separator_line
            step += 1
        for rel in gd.symmetric_relations:
            if rel not in used_symmetric_relations:
                detector_relations += [', '.join(rel)]
        for rel in gd.implication_relations:
            if rel not in used_implication_relations:
                detector_relations += [', '.join(rel[0:-1]) + ' => ' + rel[-1]]
        gd.finally_known = [v for v in gd.variables if gd.solutions[gd.max_steps]['%s_%d' % (v, gd.max_steps)] == 1]
        output_buffer += '\nThe following variables are known in final state:\n%s\n' % ', '.join(gd.finally_known)        
        output_buffer += separator_line
        output_buffer += '\nThe following relations have not been used in determination (they might be used to check the correctness of guesses):\n'
        output_buffer += '\n'.join(detector_relations)
        output_buffer += '\n' + separator_line
        output_buffer += '\nThe following variables can be deduced from multiple paths:\n'
        for v in gd.variables:
            if variables_deductor_relations[v]['number_of_deductions'] > 1:
                output_buffer += '\n%s can be deduced from:\n%s\n' % (v, '\n'.join(variables_deductor_relations[v]['deductor_relations']))
        with open(gd.output_dir, 'w') as outputfile_obj:
            outputfile_obj.write(output_buffer)