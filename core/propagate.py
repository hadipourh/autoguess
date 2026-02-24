
"""
Copyright (C) 2024 Hosein Hadipour
Contact: hsn.hadipour@gmail.com

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
"""

import time
from datetime import datetime
from core.inputparser import read_relation_file


def propagate_knowledge(parsed_data, known_variables):
    """
    Propagate knowledge through a system of connection relations.

    Given a set of initially known variables and a system of symmetric /
    implication relations, iteratively deduce new variables until no more
    can be learned (fixed-point).

    Returns the set of all known variables after propagation, or None on error.
    """

    all_variables = parsed_data["variables"]
    symmetric_relations = parsed_data["symmetric_relations"]
    implication_relations = parsed_data["implication_relations"]
    target_variables = parsed_data.get("target_variables", all_variables)
    problem_name = parsed_data.get("problem_name", "")

    # Validate input
    for var in known_variables:
        if var not in all_variables:
            print("Error: variable '%s' not found in the parsed data." % var)
            return None

    start_time = time.time()
    separator = '=' * 60

    print(separator)
    print('Knowledge propagation started - %s' % datetime.now())
    if problem_name:
        print('Problem: %s' % problem_name)
    print('Total variables: %d' % len(all_variables))
    print('Total relations: %d (symmetric: %d, implication: %d)' % (
        len(symmetric_relations) + len(implication_relations),
        len(symmetric_relations), len(implication_relations)))
    print('Initially known variables: %d' % len(known_variables))
    print('  %s' % ', '.join(known_variables))
    print(separator)

    known_set = set(known_variables)
    iteration = 0

    while True:
        newly_learned = []

        for rel in symmetric_relations:
            rel_known = [v for v in rel if v in known_set]
            if len(rel_known) == len(rel) - 1:
                determined = list(set(rel) - set(rel_known))
                if determined[0] not in known_set:
                    newly_learned.append((determined[0], rel))

        for rel in implication_relations:
            rel_known = [v for v in rel[:-1] if v in known_set]
            if rel_known == rel[:-1] and rel[-1] not in known_set:
                newly_learned.append((rel[-1], rel))

        if not newly_learned:
            break

        iteration += 1
        # Deduplicate (a variable may be deducible from multiple relations)
        seen = set()
        unique_learned = []
        for var, rel in newly_learned:
            if var not in seen:
                seen.add(var)
                unique_learned.append((var, rel))

        print('\nIteration %d: learned %d new variable(s)' % (iteration, len(unique_learned)))
        for var, rel in unique_learned:
            print('  %s  <--  [%s]' % (var, ', '.join(rel)))

        known_set.update(seen)

    elapsed = time.time() - start_time

    # Summary
    initially_known_count = len(known_variables)
    newly_learned_count = len(known_set) - initially_known_count
    unreachable = [v for v in all_variables if v not in known_set]
    targets_covered = [v for v in target_variables if v in known_set]

    print('\n' + separator)
    print('PROPAGATION SUMMARY')
    print(separator)
    print('Total iterations:          %d' % iteration)
    print('Initially known:           %d' % initially_known_count)
    print('Newly learned:             %d' % newly_learned_count)
    print('Total known after prop.:   %d / %d' % (len(known_set), len(all_variables)))
    print('Unreachable variables:     %d' % len(unreachable))
    if unreachable:
        print('  %s' % ', '.join(unreachable))
    print('Target variables covered:  %d / %d' % (len(targets_covered), len(target_variables)))
    print('Elapsed time:              %.4f seconds' % elapsed)
    print(separator)

    return known_set


if __name__ == '__main__':
    relation_file = "relationfile.txt"
    parsed_data = read_relation_file(relation_file, preprocess=0, D=2, log=0)
    learned_variables = propagate_knowledge(parsed_data=parsed_data, known_variables=["x0", "x1"])
    print("Learned variables:", learned_variables)
    print("Learned variables:", learned_variables)