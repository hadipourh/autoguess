# Created on Sep 19, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os
import itertools

output_dir = os.path.curdir

def left_rotate_array(A, n, r):
    output = [0]*len(A)
    output[0:n - r:1] = A[r:]
    output[n - r:] = A[0:r:1]
    return output

def lblock_kb(R = 22):
    cipher_name = 'lblock'
    eqs = '#%s - Impossible differential attack on %d rounds of %s proposed in https://eprint.iacr.org/2016/414.pdf\n' % (cipher_name, R + 1, cipher_name)
    eqs += 'connection relations\n'
    for r in range(R):
        round_key = ['k_%d_%d' % (r, i) for i in range(80)]
        round_key_new = ['k_%d_%d' % (r + 1, i) for i in range(80)]
        #Apply rotation
        rotated_key = left_rotate_array(round_key, 80, 29)
        ##############################################################
        #Apply S9
        # Advanced:
        # sbox_io = rotated_key[0:4] + round_key_new[0:4]
        # for quarted in itertools.combinations(sbox_io, 5):    
        #     eqs += ','.join(quarted) + '\n'
        
        # Simple Sbox constraints:
        sbox_input = rotated_key[0:4]
        sbox_output = round_key_new[0:4]
        for output in sbox_output:
            eqs += ','.join(sbox_input) + ' => ' + output + '\n'
        for inp in sbox_input:
            eqs += ','.join(sbox_output) + ' => ' + inp + '\n'
        ##############################################################    
        #Apply S8
        # Advanced:
        # sbox_io = rotated_key[4:8] + round_key_new[4:8]
        # for quarted in itertools.combinations(sbox_io, 5):
        #     eqs += ','.join(quarted) + '\n'

        # Simple Sbox constraints:
        sbox_input = rotated_key[4:8]
        sbox_output = round_key_new[4:8]
        for output in sbox_output:
            eqs += ','.join(sbox_input) + ' => ' + output + '\n'
        for inp in sbox_input:
            eqs += ','.join(sbox_output) + ' => ' + inp + '\n'
        ##############################################################
    eqs += 'algebraic relations\n'
    for r in range(R):
        round_key = ['k_%d_%d' % (r, i) for i in range(80)]
        round_key_new = ['k_%d_%d' % (r + 1, i) for i in range(80)]
        #Apply rotation
        rotated_key = left_rotate_array(round_key, 80, 29)
        for i in range(8, 80):
            eqs += '%s + %s\n' % (rotated_key[i], round_key_new[i])
    index = [[4*i + j for j in range(4)] for i in range(20)]
    if R == 22:
        target_subkeys = ['k_%d_%d' % (r, i) for r in [0] for i in range(0, 7*4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [1] for i in index[1] + index[4] + index[6] + index[7]]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [2] for i in index[0] + index[5]]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [3] for i in index[4]]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [18] for i in index[5]]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [19] for i in index[2] + index[4]]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [20] for i in index[0] + index[1] + index[3] + index[6]]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [21] for i in range(1*4, 8*4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [22] for i in range(8*4)]
    eqs += 'target\n' + '\n'.join(target_subkeys)
    #eqs += '\nknown\n' + '\n'.join("k_22_79, k_22_78, k_22_77, k_22_76, k_22_75, k_22_74, k_22_73, k_22_72, k_22_71, k_22_70, k_22_69, k_22_68, k_22_67, k_22_66, k_22_65, k_22_64, k_22_63, k_22_62, k_22_61, k_22_60, k_22_59, k_22_58, k_22_57, k_22_56, k_22_55, k_22_49, k_22_48, k_22_47, k_22_46, k_22_37, k_22_36, k_22_35, k_22_34, k_22_31, k_22_30, k_22_29, k_22_28, k_22_27, k_22_26, k_22_25, k_22_24, k_22_23, k_22_22, k_22_21, k_22_20, k_22_19, k_22_18, k_22_17, k_22_16, k_22_15, k_22_14, k_22_13, k_22_12, k_22_11, k_22_10, k_22_9, k_22_8, k_22_7, k_22_6, k_22_5, k_22_4, k_22_3, k_22_2, k_22_1, k_22_0, k_14_29, k_11_29, k_9_32, k_6_34, k_6_33, k_6_32, k_6_31, k_3_29".split(", "))
    eqs += '\nend'
    eqsfile_path = os.path.join(output_dir, 'relationfile_%s_%dr_mg73_ms7_preprcoess1.txt' % (cipher_name, R))
    return eqs, eqsfile_path

def main():
    eqs, eqsfile_path = lblock_kb(R=22)
    with open(eqsfile_path, 'w') as relation_file:
        relation_file.write(eqs)

if __name__ == '__main__':
    main()
