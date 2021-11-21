# Created on Apr 25, 2021
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

def ordered_set(seq):
    """
    This method eliminates duplicated elements in a given list, 
    and returns a list in which each elements appears only once
    """

    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def zuc(T=9):
    cipher_name = 'zuc'
    recommended_mg = 0
    recommended_ms = 35
    eqs = ['#%s %d clock cycles' % (cipher_name, T)]
    eqs += ['connection relations']
    for t in range(T):
        eqs += ['S_%d, S_%d, S_%d, S_%d, S_%d, S_%d' % (16 + t, 15 + t, 13 + t, 10 + t, 4 + t, t)] # Checked

        eqs += ['S_%d => SL_%d' % (14 + t, 14 + t)]               # Checked
        eqs += ['S_%d => SH_%d' % (14 + t, 14 + t)]
        eqs += ['SL_%d, SH_%d => S_%d' % (14 + t, 14 + t, 14 + t)]

        eqs += ['S_%d => SL_%d' % (15 + t, 15 + t)]               # Checked
        eqs += ['S_%d => SH_%d' % (15 + t, 15 + t)]
        eqs += ['SL_%d, SH_%d => S_%d' % (15 + t, 15 + t, 15 + t)]

        eqs += ['S_%d => SL_%d' % (11 + t, 11 + t)]               # Checked
        eqs += ['S_%d => SH_%d' % (11 + t, 11 + t)]
        eqs += ['SL_%d, SH_%d => S_%d' % (11 + t, 11 + t, 11 + t)]
        
        eqs += ['S_%d => SL_%d' % (9 + t, 9 + t)]                 # Checked
        eqs += ['S_%d => SH_%d' % (9 + t, 9 + t)]
        eqs += ['SL_%d, SH_%d => S_%d' % (9 + t, 9 + t, 9 + t)]

        eqs += ['S_%d => SL_%d' % (7 + t, 7 + t)]                 # Checked
        eqs += ['S_%d => SH_%d' % (7 + t, 7 + t)]
        eqs += ['SL_%d, SH_%d => S_%d' % (7 + t, 7 + t, 7 + t)]

        eqs += ['S_%d => SL_%d' % (5 + t, 5 + t)]                 # Checked
        eqs += ['S_%d => SH_%d' % (5 + t, 5 + t)]
        eqs += ['SL_%d, SH_%d => S_%d' % (5 + t, 5 + t, 5 + t)]

        eqs += ['S_%d => SL_%d' % (2 + t, 2 + t)]                 # Checked
        eqs += ['S_%d => SH_%d' % (2 + t, 2 + t)]
        eqs += ['SL_%d, SH_%d => S_%d' % (2 + t, 2 + t, 2 + t)]

        eqs += ['S_%d => SL_%d' % (t, t)]                         # Checked
        eqs += ['S_%d => SH_%d' % (t, t)]
        eqs += ['SL_%d, SH_%d => S_%d' % (t, t, t)]

        # X0 = SH_(15 + t) || SL_(14 + t)
        # X3 = SL_(2 + t) || SH_(t)
        eqs += ['Z_%d, X0_%d, R1_%d, R2_%d, X3_%d' % (t, t, t, t, t)]                     # Checked
        eqs += ['SH_%d, SL_%d => X0_%d' % (15 +  t, 14 + t, t)]
        eqs += ['X0_%d => SH_%d' % (t, 15 + t)]
        eqs += ['X0_%d => SL_%d' % (t, 14 + t)]
        eqs += ['SL_%d, SH_%d => X3_%d' % (2 + t, t, t)]
        eqs += ['X3_%d => SL_%d' % (t, 2 + t)]
        eqs += ['X3_%d => SH_%d' % (t, t)]

        eqs += ['W_%d, X0_%d, R1_%d, R2_%d' % (t, t, t, t)]
        eqs += ['W_%d, X3_%d, Z_%d' % (t, t, t)]

        eqs += ['ZL_%d, SL_%d, R1L_%d, R2L_%d, SH_%d' % (t, 14 + t, t, t, t)]               # Checked
        eqs += ['ZH_%d, SH_%d, R1H_%d, R2H_%d, c1_%d, SL_%d' % (t, 15 + t, t, t, t, 2 + t)] # Checked
        eqs += ['SL_%d, R1L_%d, R2L_%d => c1_%d' % (14 + t, t, t, t)]                       # Checked
                                         
        eqs += ['R1_%d => R1L_%d' % (t, t)]                                                 # Checked
        eqs += ['R1_%d => R1H_%d' % (t, t)]
        eqs += ['R1L_%d, R1H_%d => R1_%d' % (t, t, t)]
        eqs += ['R2_%d => R2L_%d' % (t, t)]
        eqs += ['R2_%d => R2H_%d' % (t, t)]
        eqs += ['R2L_%d, R2H_%d => R2_%d' % (t, t, t)]
        
        # X1 = SL_(11 + t) || SH_(9 + t)
        eqs += ['W1_%d, R1_%d, X1_%d' % (t, t, t)]                                         # Checked
        eqs += ['SL_%d, SH_%d => X1_%d' % (11 + t, 9 + t, t)]
        eqs += ['X1_%d => SL_%d' % (t, 11 + t)]
        eqs += ['X1_%d => SH_%d' % (t, 9 + t)]

        eqs += ['W1L_%d, R1L_%d, SH_%d' % (t, t, 9 + t)]                                    # Checked
        eqs += ['W1H_%d, R1H_%d, SL_%d, c2_%d' % (t, t, 11 + t, t)]
        eqs += ['R1L_%d, SH_%d => c2_%d' % (t, 9 + t, t)]
        eqs += ['W1_%d => W1L_%d' % (t, t)]
        eqs += ['W1_%d => W1H_%d' % (t, t)]
        eqs += ['W1L_%d, W1H_%d => W1_%d' % (t, t, t)]

        # X2 = SL_(7 + t) || SH_(5 + t)
        eqs += ['W2_%d, R2_%d, X2_%d' % (t, t, t)]                                         # Checked
        eqs += ['SL_%d, SH_%d => X2_%d' % (7 + t, 5 + t, t)]
        eqs += ['X2_%d => SL_%d' % (t, 7 + t)]
        eqs += ['X2_%d => SH_%d' % (t, 5 + t)]

        eqs += ['W2L_%d, R2L_%d, SH_%d' % (t, t, 5 + t)]                                    # Checked
        eqs += ['W2H_%d, R2H_%d, SL_%d' % (t, t, 7 + t)]
        eqs += ['W2_%d => W2L_%d' % (t, t)]
        eqs += ['W2_%d => W2H_%d' % (t, t)]
        eqs += ['W2L_%d, W2H_%d => W2_%d' % (t, t, t)]

        eqs += ['R1_%d => W1L_%d' % (1 + t, t)]                                             # Checked
        eqs += ['R1_%d => W2H_%d' % (1 + t, t)]
        eqs += ['W1L_%d, W2H_%d => R1_%d' % (t, t, 1 + t)]

        eqs += ['R2_%d => W2L_%d' % (1 + t, t)]                                             # Checked
        eqs += ['R2_%d => W1H_%d' % (1 + t, t)]
        eqs += ['W2L_%d, W1H_%d => R2_%d' % (t, t, 1 + t)]

        # for j in range(16):
        #     eqs += ['SL_%d, SH_%d => Y_%d' % (t + j, t + j, t + j)]
        #     #eqs += ['SL_%d => Y_%d' % (t + j, t + j)]
        #     #eqs += ['SH_%d => Y_%d' % (t + j, t + j)]
        #     eqs += ['S_%d => Y_%d' % (t + j, t + j)]
    eqs = ordered_set(eqs)
    eqs  = '\n'.join(eqs) + '\n'    
    
    weights = []
    for t in range(T + 16):
        weights.append('S_%d 31' % t)
        weights.append('SL_%d 16' % t)
        weights.append('SH_%d 16' % t)
    for t in range(T + 1):
        weights.append('X0_%d 32' % t)
        weights.append('X3_%d 32' % t)
        weights.append('R1_%d 32' % t)
        weights.append('R2_%d 32' % t)
        weights.append('R1L_%d 16' % t)
        weights.append('R1H_%d 16' % t)
        weights.append('R2L_%d 16' % t)
        weights.append('R2H_%d 16' % t)
        weights.append('W_%d 32' % t)
        weights.append('W1_%d 32' % t)
        weights.append('W2_%d 32' % t)
        weights.append('W1L_%d 16' % t)
        weights.append('W1H_%d 16' % t)
        weights.append('W2L_%d 16' % t)
        weights.append('W2H_%d 16' % t)
        weights.append('X1_%d 32' % t)
        weights.append('X2_%d 32' % t)
        weights.append('c1_%d 1' % t)
        weights.append('c2_%d 1' % t)
        weights.append('Z_%d 32' % t)
        weights.append('ZL_%d 16' % t)
        weights.append('ZH_%d 16' % t)
    eqs += 'weights\n' + '\n'.join(weights) + '\n'
    guess_basis1 = ['S_5', 'S_6', 'S_7', 'S_9', 'S_10', 'SL_13', 'S_15',  'S_16', 'S_18', 'S_19', 'S_20', 'R1_5', 'c1_4', 'c2_4', 'c2_5', 'SH_13', 'SH_12', 'c1_3']    
    guess_basis2 = ['S_5', 'S_6', 'S_7', 'S_9', 'S_10', 'SL_13', 'S_15',  'S_16', 'S_18', 'S_19', 'S_20', 'R1_5',                 'c2_5', 'SH_13', 'SH_12', 'c1_3']  # 9 clock cycles is enough
    guess_basis3 = ['S_5', 'S_6', 'S_3', 'S_9', 'S_10', 'SL_13', 'S_15',  'S_16', 'S_18', 'S_19', 'S_20', 'R1_5',                 'c2_5', 'SH_13', 'SH_12', 'c1_3']  # 9 clock cycles is enough
    guess_basis4 = ['S_5', 'S_6', 'S_3', 'S_22', 'S_10', 'SL_13', 'S_15',  'S_16', 'S_18', 'S_19', 'S_20', 'R1_5',                'c2_5', 'SH_13', 'SH_12', 'c1_3']  # 9 clock cycles is enough
    guess_basis5 = ['S_5', 'S_6', 'S_7', 'S_21', 'S_22', 'W2H_6', 'S_15', 'S_16', 'S_18', 'S_19', 'S_20', 'R1_5', 'c1_4', 'c2_4', 'c2_5', 'SH_13', 'SH_12', 'c1_3']  # 9 clock cycles is enough
    test =         []

    eqs += 'known\n' + '\n'.join(['Z_%d' % i for i in range(T)] +
                                 ['ZL_%d' % i for i in range(T)] + 
                                 ['ZH_%d' % i for i in range(T)] + guess_basis2)
    # eqs += '\ntarget\n' + '\n'.join('S_%d' % i for i in range(16)) + '\nR1_0\nR2_0'
    # eqs += '\ntarget\n' + 'SL_2'
    eqs += '\nend'
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dclk_mg%d_ms%d.txt' % (cipher_name, T, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    zuc(T=9)
    
if __name__ == '__main__':
    main()
