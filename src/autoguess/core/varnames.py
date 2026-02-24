"""
Unambiguous internal variable naming for solver models.

Original variable names from relation files may contain underscores
(e.g., k_6_61).  To avoid collisions when appending step/path indices,
we use distinct separators instead of a plain underscore:

  Step variable:  v + '__S' + str(step)
      e.g.  k_6_61 at step 0  →  k_6_61__S0
            k_6    at step 61  →  k_6__S61

  Path variable:  v + '__S' + str(step) + '__P' + str(path_idx)
      e.g.  k_6_61 at step 0, path 3  →  k_6_61__S0__P3
            k_6    at step 61, path 0  →  k_6__S61__P0

This eliminates the ambiguity where the old '%s_%d' pattern could
produce identical strings for different (variable, step) pairs.

Copyright (C) 2021 Hosein Hadipour
License: GPL-3.0-or-later
"""

STEP_SEP = '__S'
PATH_SEP = '__P'


def step_var(v, step):
    """Construct the step-indexed name for variable *v* at the given *step*."""
    return f'{v}{STEP_SEP}{step}'


def path_var(v, step, path_idx):
    """Construct the path-indexed name for variable *v* at the given *step* and *path_idx*."""
    return f'{v}{STEP_SEP}{step}{PATH_SEP}{path_idx}'
