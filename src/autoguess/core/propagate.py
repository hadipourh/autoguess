
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
from .inputparser import read_relation_file


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

    # Build inverted indices: variable -> list of relations containing it
    from collections import defaultdict
    sym_by_var = defaultdict(list)
    for rel in symmetric_relations:
        for v in rel:
            sym_by_var[v].append(rel)
    impl_by_var = defaultdict(list)   # index by premise variables only
    for rel in implication_relations:
        for v in rel[:-1]:
            impl_by_var[v].append(rel)

    # Initial frontier: all initially known variables
    frontier = set(known_variables)

    while frontier:
        newly_learned = []
        checked = set()  # relation ids already examined this iteration

        for fvar in frontier:
            # Symmetric relations: if exactly 1 unknown remains, it's determined
            for rel in sym_by_var.get(fvar, []):
                rid = id(rel)
                if rid in checked:
                    continue
                checked.add(rid)
                unknown = None
                n_unknown = 0
                for v in rel:
                    if v not in known_set:
                        n_unknown += 1
                        unknown = v
                        if n_unknown > 1:
                            break
                if n_unknown == 1:
                    newly_learned.append((unknown, rel))

            # Implication relations: if all premises known and conclusion unknown
            for rel in impl_by_var.get(fvar, []):
                rid = id(rel)
                if rid in checked:
                    continue
                checked.add(rid)
                target = rel[-1]
                if target in known_set:
                    continue
                if all(v in known_set for v in rel[:-1]):
                    newly_learned.append((target, rel))

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
        frontier = seen  # next iteration only re-checks relations touching new vars

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


def _propagate_quiet(symmetric_relations, implication_relations, known_variables, all_variables):
    """
    Run fixed-point propagation silently (no output).
    Returns the set of known variables after propagation.
    """
    from collections import defaultdict

    known_set = set(known_variables)

    sym_by_var = defaultdict(list)
    for rel in symmetric_relations:
        for v in rel:
            sym_by_var[v].append(rel)
    impl_by_var = defaultdict(list)
    for rel in implication_relations:
        for v in rel[:-1]:
            impl_by_var[v].append(rel)

    frontier = set(known_variables)
    while frontier:
        newly_learned = set()
        checked = set()
        for fvar in frontier:
            for rel in sym_by_var.get(fvar, []):
                rid = id(rel)
                if rid in checked:
                    continue
                checked.add(rid)
                unknown = None
                n_unknown = 0
                for v in rel:
                    if v not in known_set:
                        n_unknown += 1
                        unknown = v
                        if n_unknown > 1:
                            break
                if n_unknown == 1:
                    newly_learned.add(unknown)
            for rel in impl_by_var.get(fvar, []):
                rid = id(rel)
                if rid in checked:
                    continue
                checked.add(rid)
                target = rel[-1]
                if target not in known_set and all(v in known_set for v in rel[:-1]):
                    newly_learned.add(target)
        newly_learned -= known_set
        if not newly_learned:
            break
        known_set.update(newly_learned)
        frontier = newly_learned
    return known_set


def reduce_basis(parsed_data, basis_variables):
    """
    Given a known guess basis, try to reduce it by testing subsets of
    decreasing size via propagation.

    Enumerates subsets starting from size |basis|-1, then |basis|-2, etc.
    At each level, if at least one valid subset exists the search continues
    to the next smaller size.  The search stops at the first level where NO
    subset is a valid guess basis, and returns one of the valid subsets
    from the previous (smallest successful) level.

    Returns the reduced basis (list) or the original basis if no reduction
    is possible.
    """
    from itertools import combinations
    from math import comb

    all_variables = parsed_data["variables"]
    symmetric_relations = parsed_data["symmetric_relations"]
    implication_relations = parsed_data["implication_relations"]
    target_variables = parsed_data.get("target_variables", all_variables)
    problem_name = parsed_data.get("problem_name", "")

    # Separate file-level known vars from the basis being reduced
    file_known = parsed_data.get("known_variables", [])
    # basis_variables are the ones supplied via -kn; file_known already
    # includes them (merged by inputparser), so the "extra" basis vars are
    # those not originally in the file's known section.  But for reduction
    # we treat the *entire* basis_variables list as the set to shrink, and
    # the file-level known vars that are NOT part of the basis stay fixed.
    basis_set = set(basis_variables)
    fixed_known = [v for v in file_known if v not in basis_set]

    target_set = set(target_variables)

    # Validate
    for var in basis_variables:
        if var not in all_variables:
            print("Error: variable '%s' not found in the parsed data." % var)
            return None

    start_time = time.time()
    separator = '=' * 60

    print(separator)
    print('BASIS REDUCTION via propagation — %s' % datetime.now())
    if problem_name:
        print('Problem: %s' % problem_name)
    print('Total variables: %d' % len(all_variables))
    print('Total relations: %d (symmetric: %d, implication: %d)' % (
        len(symmetric_relations) + len(implication_relations),
        len(symmetric_relations), len(implication_relations)))
    print('Target variables: %d' % len(target_variables))
    if fixed_known:
        print('Fixed known (from file): %d  (%s)' % (len(fixed_known), ', '.join(fixed_known)))
    print('Initial basis to reduce (%d): %s' % (len(basis_variables), ', '.join(basis_variables)))
    print(separator)

    # First verify the full basis is indeed a guess basis
    full_known = _propagate_quiet(symmetric_relations, implication_relations,
                                  fixed_known + basis_variables, all_variables)
    if not target_set.issubset(full_known):
        uncovered = sorted(target_set - full_known)
        print('\nERROR: The supplied basis is NOT a valid guess basis!')
        print('  Uncovered targets (%d): %s' % (len(uncovered), ', '.join(uncovered)))
        print(separator)
        return None

    print('\nFull basis (%d vars) verified — all targets covered.' % len(basis_variables))

    n = len(basis_variables)
    best_basis = list(basis_variables)
    total_checked = 0

    for drop in range(1, n):
        subset_size = n - drop
        n_subsets = comb(n, subset_size)
        print('\n--- Trying subsets of size %d  (%d candidates) ---' % (subset_size, n_subsets))

        found_at_level = None          # first valid candidate at this level
        for idx, subset in enumerate(combinations(basis_variables, subset_size), 1):
            total_checked += 1
            candidate = list(subset)
            known_after = _propagate_quiet(symmetric_relations, implication_relations,
                                           fixed_known + candidate, all_variables)
            if target_set.issubset(known_after):
                print('  [%d/%d] {%s}  =>  VALID guess basis!' % (idx, n_subsets, ', '.join(candidate)))
                if found_at_level is None:
                    found_at_level = candidate   # keep the first valid one
                break                            # no need to check remaining subsets at this level
            else:
                if idx <= 20 or idx == n_subsets:
                    uncov = len(target_set - known_after)
                    print('  [%d/%d] {%s}  =>  %d target(s) uncovered' % (idx, n_subsets, ', '.join(candidate), uncov))
                elif idx == 21:
                    print('  ... (suppressing further output for this level) ...')

        if found_at_level is not None:
            best_basis = found_at_level
            print('  ==> Size %d is feasible — continuing to smaller sizes ...' % subset_size)
        else:
            # No valid subset at this level — stop and return the best we found
            print('  ==> No valid guess basis of size %d.' % subset_size)
            break

    elapsed = time.time() - start_time
    print('\n' + separator)
    print('REDUCTION RESULT')
    print(separator)
    if len(best_basis) < n:
        print('Original basis size:   %d' % n)
        print('Reduced basis size:    %d  (dropped %d)' % (len(best_basis), n - len(best_basis)))
        print('Reduced basis:         %s' % ', '.join(best_basis))
        dropped = sorted(set(basis_variables) - set(best_basis))
        print('Dropped variable(s):   %s' % ', '.join(dropped))
    else:
        print('No smaller guess basis found via propagation.')
        print('The original basis of size %d is minimal (w.r.t. propagation).' % n)
    print('Subsets tested:        %d' % total_checked)
    print('Elapsed time:          %.4f seconds' % elapsed)
    print(separator)
    return best_basis


if __name__ == '__main__':
    relation_file = "relationfile.txt"
    parsed_data = read_relation_file(relation_file, preprocess=0, D=2, log=0)
    learned_variables = propagate_knowledge(parsed_data=parsed_data, known_variables=["x0", "x1"])
    print("Learned variables:", learned_variables)
    print("Learned variables:", learned_variables)