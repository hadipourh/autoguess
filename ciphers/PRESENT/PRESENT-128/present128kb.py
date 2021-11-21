# Created on Sep 19, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os
import itertools

output_dir = os.path.curdir

def present128kb(R=28):
    """
    This attack is taken from "Improving Key-Recovery in Linear Attacks: Application to 28-Round PRESENT"
    https://link.springer.com/chapter/10.1007/978-3-030-45721-1_9

    There is a typo in this paper: The involved subkey bits can be deduced from 115 bits. However, the authors' claim 
    that they can be deduced from 114 bits. The computed time complexity is based on 114 which must be modified. 
    """
    cipher_name = 'present128_kb'
    # 28 rounds
    recommended_mg = 115
    recommended_ms = 30    
    cipher_name = 'present_kb'
    eqs = '#%s %d Rounds\n' % (cipher_name, R)
    eqs += 'connection relations\n'
    algebraic_equations = 'algebraic relations\n'
    key_permutation = []
    for r in range(R):
        round_key = ['k_%d_%d' % (r, i) for i in range(128)]
        permuted_key = round_key[61:128:1] + round_key[0:61:1]
        round_key_new = ['k_%d_%d' % (r + 1, i) for i in range(128)]
        ##########################################################
        ##########################################################
        ##########################################################
        # Apply Sbox
        # first plan
        # sbox_io = permuted_key[0:4] + round_key_new[0:4]
        # for quarted in itertools.combinations(sbox_io, 4):
        #     for element in sbox_io:
        #         if element not in quarted:
        #             eqs += ','.join(quarted) + ' => ' + element + '\n'
        # second plan
        # sbox_io = permuted_key[0:4] + round_key_new[0:4]
        # for quarted in itertools.combinations(sbox_io, 5):
        #     eqs += ','.join(quarted) + '\n'
        # Simple condition for Sbox
        sbox_input = permuted_key[0:4]
        sbox_output = round_key_new[0:4]
        for output in sbox_output:
            eqs += ','.join(sbox_input) + ' => ' + output + '\n'
        for inp in sbox_input:
            eqs += ','.join(sbox_output) + ' => ' + inp + '\n'
        ################################################################
        # first plan
        # sbox_io = permuted_key[4:8] + round_key_new[4:8]
        # for quarted in itertools.combinations(sbox_io, 4):
        #     for element in sbox_io:
        #         if element not in quarted:
        #             eqs += ','.join(quarted) + ' => ' + element + '\n'
        # second plan
        # sbox_io = permuted_key[4:8] + round_key_new[4:8]
        # for quarted in itertools.combinations(sbox_io, 5):
        #     eqs += ','.join(quarted) + '\n'
        # Simple condition for Sbox
        sbox_input = permuted_key[4:8]
        sbox_output = round_key_new[4:8]
        for output in sbox_output:
            eqs += ','.join(sbox_input) + ' => ' + output + '\n'
        for inp in sbox_input:
            eqs += ','.join(sbox_output) + ' => ' + inp + '\n'
        ##########################################################
        ##########################################################
        ##########################################################
        for i in range(8, 128):
            algebraic_equations += '%s + %s\n' % (permuted_key[i], round_key_new[i])
    if R == 28:
        target_subkeys = ['k_%d_%d' % (r, i) for r in [0] for i in range(0*4, 11*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [1] for i in (list(range(0*4, 2*4 + 4)) + \
            list(range(4*4, 6*4 + 4)) + list(range(8*4, 10*4 + 4)))]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [27] for i in [0, 2, 2*4, 2*4 + 2, 3*4, 3*4 + 2, 4*4, 4*4 + 2, 6*4, 6*4 + 2, 7*4, 7*4 + 2, 8*4, 8*4 + 2, 10*4, 10*4 + 2, 11*4, 11*4 + 2, 12*4, 12*4 + 2, 14*4, 14*4 + 2, 15*4, 15*4 + 2]]
        k28_index = list(filter(lambda x : x not in [1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49, 53, 57, 61] ,list(range(0, 64))))
        target_subkeys += ['k_%d_%d' % (r, i) for r in [28] for i in k28_index]
    else:
        print('R must be chosen from {28}')
        return
    print('Size of involved subkeys: %d' % len(target_subkeys))
    eqs += algebraic_equations
    eqs += 'target\n' + '\n'.join(target_subkeys) + '\n'
    ##################################################################################
    known_data = ['k_%d_%d' % (r, i) for r in [0] for i in range(0*4, 11*4 + 4)]
    known_data += ['k_%d_%d' % (r, i) for r in [1] for i in (list(range(0*4, 2*4 + 4)) + \
            list(range(4*4, 6*4 + 4)) + list(range(7*4, 7*4 + 4)) + list(range(8*4, 10*4 + 4))) + \
                list(range(11*4, 11*4 + 3)) + [126, 127]]
    known_data += ['k_%d_%d' % (r, i) for r in [27] for i in [0, 2, 2*4, 2*4 + 2, 3*4, 3*4 + 2, 4*4, 4*4 + 2, 64]]
    known_data += ['k_%d_%d' % (r, i) for r in [28] for i in [4, 6, 7, 8, 10, 11, 12, 14, 15, 28, 30, 31, 32]]
    #eqs += 'known, ' + ','.join(known_data) # For less than 28 steps the MILP problem becoms infeasible
    eqs += 'end'
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    present128kb(R=28)
    
if __name__ == '__main__':
    main()
