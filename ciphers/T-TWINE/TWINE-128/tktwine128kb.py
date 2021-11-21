# Created on Sep 19, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os
import itertools

output_dir = os.path.curdir

def right_rotate_array(A, n, r):
    output = [0]*len(A)
    output[0:r] = A[n-r:]
    output[r:] = A[0:n - r]
    return output

def tktwine128kb(R=27):
    """
    Checking the results of the following paper:
    "Impossible Differential Cryptanalysis of Reduced-Round Tweakable TWINE [eprint-2020]"
    ID attack on 27 rounds of T-TWINE-128 in which 37 subkey nibbles are involved. 
    It is proven that all of these 37 nibbles can be deduced from 31 nibbles. 
    """
    cipher_name = 'tktwine128_kb'
    # 27 rounds
    recommended_mg = 31
    recommended_ms = 20
    eqs = '#%s %d Rounds\n' % (cipher_name, R)
    eqs += 'connection relations\n'
    RK = [[0 for i in range(8)] for r in range(R)]
    for r in range(R):
        key_st = ['k_%d_%d' % (r, i) for i in range(32)]
        new_key_st = ['k_%d_%d' % (r + 1, i) for i in range(32)]
        temp1 = right_rotate_array(new_key_st, 32, 4)
        temp2 = right_rotate_array(temp1[0:4], 4, 1)
        new_key_st_permuted = temp2 + temp1[4:]
        RK[r] = [key_st[2], key_st[3], key_st[12], key_st[15], key_st[17], key_st[18], key_st[28], key_st[31]]
        # Apply Sboxes
        eqs += '%s, %s, %s\n' % (new_key_st_permuted[1], key_st[1], key_st[0])
        eqs += '%s, %s, %s\n' % (new_key_st_permuted[4], key_st[4], key_st[16])
        eqs += '%s, %s, %s\n' % (new_key_st_permuted[23], key_st[23], key_st[30])
        for i in range(32):
            if i not in [1, 4, 23]:
                eqs += '%s, %s\n' % (new_key_st_permuted[i], key_st[i])
    if R == 27:
        target_subkeys =  [RK[0][i] for i in range(8)] + \
            [RK[1][i] for i in range(8)] + \
            [RK[2][i] for i in [0, 1, 2, 3, 5, 6, 7]] + \
            [RK[3][i] for i in [2, 4, 5, 6]] + \
            [RK[4][i] for i in [3, 5]] + \
            [RK[5][i] for i in [1]] + \
            [RK[24][i] for i in [7]] + \
            [RK[25][i] for i in [5, 7]] + \
            [RK[26][i] for i in [0, 4, 5, 7]]
    print('Size of involved subkeys: %d' % len(target_subkeys))
    eqs += 'target\n' + '\n'.join(target_subkeys)
    eqs += '\nend'
   
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    tktwine128kb(R=27)
    
if __name__ == '__main__':
    main()
