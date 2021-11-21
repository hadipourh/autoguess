# Created on Sep 19, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os
import itertools

output_dir = os.path.curdir

def present80kb(R=26):
    """
    This attack is taken from "Improving Key-Recovery in Linear Attacks: Application to 28-Round PRESENT"
    https://link.springer.com/chapter/10.1007/978-3-030-45721-1_9

    'For key-recovery attack described on 26 rounds of PRESENT-80, in total there are 96 bits of the subkeys which
     need to be guessed.
    According to the authors' claim, they can all be deduced from the |kT| = 61 bits of key.
    However, using our tool we prove they all can be deduced from the |kT| = 60 bits. 
    """
    cipher_name = 'present_kb'
    key_permutation = []
    eqs = '#%s %d Rounds\n' % (cipher_name, R)
    eqs += 'connection relations\n'
    algebraic_relations = 'algebraic relations\n'
    for r in range(R):
        round_key = ['k_%d_%d' % (r, i) for i in range(80)]
        # permuted_key = round_key[62:80:1] + round_key[0:62:1] # Wrong
        permuted_key = round_key[61:80:1] + round_key[0:61:1]
        round_key_new = ['k_%d_%d' % (r + 1, i) for i in range(80)]
        ##########################################################
        # sbox_io = permuted_key[0:4] + round_key_new[0:4]
        # for quarted in itertools.combinations(sbox_io, 5):
        #     eqs += ','.join(quarted) + '\n'
        ##########################################################
        # Simple condition for Sbox
        sbox_input = permuted_key[0:4]
        sbox_output = round_key_new[0:4]
        for output in sbox_output:
            eqs += ','.join(sbox_input) + ' => ' + output + '\n'
        for inp in sbox_input:
            eqs += ','.join(sbox_output) + ' => ' + inp + '\n'
        ##########################################################
        for i in range(4, 80):
            algebraic_relations += '%s + %s\n' % (permuted_key[i], round_key_new[i])
    if R == 26:
        # 26 round
        recommended_mg = 60
        recommended_ms = 10
        target_subkeys = ['k_%d_%d' % (r, i) for r in [0] for i in range(4*4, 11*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [1] for i in (list(range(5*4, 6*4 + 4)) + \
            list(range(9*4, 10*4 + 4)))]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [25] for i in [0, 2, 8, 10, 16, 18, 24, 26, 32, 34, 40, 42, 48, 50, 56, 58]]
        target_subkeys += ['k_%d_%d' % (r, 2*i) for r in [26] for i in range(0, 32)]
    elif R == 27:
        # 27 rounds
        recommended_mg = 68
        recommended_ms = 28
        target_subkeys = ['k_%d_%d' % (r, i) for r in [0] for i in range(4*4, 11*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [1] for i in list(range(5*4, 6*4 + 4)) + \
            list(range(9*4, 10*4 + 4))]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [26] for i in [0, 2, 8, 10, 16, 18, 24, 26, 32, 34, 40, 42, 48, 50, 56, 58]]
        target_subkeys += ['k_%d_%d' % (r, 2*i) for r in [27] for i in range(0, 32)]
    elif R == 28:
        # 28 rounds
        recommended_mg = 73
        recommended_ms = 30
        target_subkeys = ['k_%d_%d' % (r, i) for r in [0] for i in range(0*4, 11*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [1] for i in (list(range(4*4, 6*4 + 4)) + \
            list(range(8*4, 10*4 + 4)))]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [27] for i in [0, 2, 8, 10, 16, 18, 24, 26, 32, 34, 40, 42, 48, 50, 56, 58]]
        target_subkeys += ['k_%d_%d' % (r, 2*i) for r in [28] for i in range(0, 32)]
    else:
        print('R must be chosen from {26, 27, 28}')
        return
    print('Size of the involved subkeys: %d' % len(target_subkeys))
    eqs += algebraic_relations
    eqs += 'target\n' + '\n'.join(target_subkeys)
    eqs += '\nend'
   
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    present80kb(R=28)
    
if __name__ == '__main__':
    main()
