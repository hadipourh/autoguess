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

def lblock_kb(R=24):
    """
    Checking the attack presented in the following paper:
    https://digital-library.theiet.org/content/journals/10.1049/iet-ifs.2019.0353
    """
    cipher_name = 'lblock_kb'
    # 24 rounds XL18
    # recommended_mg = 47
    # recommended_ms = 3
    # 24 Rounds Z17
    # recommended_mg = 55
    # recommended_ms = 3
    # 24 Rounds Two sides 
    recommended_mg = 69
    recommended_ms = 10
    # # 23 rounds
    # recommended_mg = 
    # recommended_ms = 10
    eqs = '%s %d Rounds\n' % (cipher_name, R)
    eqs += 'connection relations\n'
    for r in range(17, R):
        round_key = ['k_%d_%d' % (r, i) for i in range(80)]
        round_key_new = ['k_%d_%d' % (r + 1, i) for i in range(80)]
        #Apply rotation
        rotated_key = left_rotate_array(round_key, 80, 29)
        #Apply S9
        # first plan
        # sbox_io = rotated_key[0:4] + round_key_new[0:4]
        # for quarted in itertools.combinations(sbox_io, 4):
        #     for element in sbox_io:
        #         if element not in quarted:
        #             eqs += ','.join(quarted) + ' => ' + element + '\n'
        # second plan
        # sbox_io = rotated_key[0:4] + round_key_new[0:4]
        # for quarted in itertools.combinations(sbox_io, 5):    
        #     eqs += ','.join(quarted) + '\n'
        ##############################################################
        # Simple Sbox constraints:
        sbox_input = rotated_key[0:4]
        sbox_output = round_key_new[0:4]
        for output in sbox_output:
            eqs += ','.join(sbox_input) + ' => ' + output + '\n'
        for inp in sbox_input:
            eqs += ','.join(sbox_output) + ' => ' + inp + '\n'
        ##############################################################    
        #Apply S8
        # first plan
        # sbox_io = rotated_key[4:8] + round_key_new[4:8]
        # for quarted in itertools.combinations(sbox_io, 4):
        #     for element in sbox_io:
        #         if element not in quarted:
        #             eqs += ','.join(quarted) + ' => ' + element + '\n'
        # second plan
        # sbox_io = rotated_key[4:8] + round_key_new[4:8]
        # for quarted in itertools.combinations(sbox_io, 5):
        #     eqs += ','.join(quarted) + '\n'
        ##############################################################
        # Simple Sbox constraints:
        sbox_input = rotated_key[4:8]
        sbox_output = round_key_new[4:8]
        for output in sbox_output:
            eqs += ','.join(sbox_input) + ' => ' + output + '\n'
        for inp in sbox_input:
            eqs += ','.join(sbox_output) + ' => ' + inp + '\n'
        ############################################################## 
        for i in range(8, 80):
            eqs += '%s, %s\n' % (rotated_key[i], round_key_new[i])
    target_subkeys = []
    if R == 24:
        # Key bits involved in determination of Oplus(Z17[4]) according to the paper:
        target_subkeys += ['k_%d_%d' % (r, i) for r in [17] for i in range(2*4, 2*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [18] for i in range(1*4, 1*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [19] for i in range(6*4, 6*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [20] for i in range(4*4, 5*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [21] for i in list(range(0*4, 0*4 + 4)) + list(range(2*4, 2*4 + 4)) + list(range(7*4, 7*4 + 4))]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [22] for i in list(range(7*4, 7*4 + 4)) + list(range(5*4, 5*4 + 4)) + list(range(4*4, 4*4 + 4)) + list(range(1*4, 1*4 + 4)) + list(range(0*4, 0*4 + 4))]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [23] for i in list(range(7*4, 7*4 + 4)) + list(range(6*4, 6*4 + 4)) + list(range(4*4, 4*4 + 4)) + \
                                                                     list(range(3*4, 3*4 + 4)) + list(range(2*4, 2*4 + 4)) + list(range(1*4, 1*4 + 4)) + \
                                                                         list(range(0*4, 0*4 + 4))]
        # Key bits involved in determination of Oplus(X18L[4])
        target_subkeys += ['k_%d_%d' % (r, i) for r in [19] for i in range(3*4, 3*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [20] for i in range(3*4, 3*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [21] for i in list(range(6*4, 6*4 + 4)) + list(range(3*4, 3*4 + 4))]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [22] for i in list(range(6*4, 6*4 + 4)) + list(range(5*4, 5*4 + 4)) + list(range(3*4, 3*4 + 4))]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [23] for i in list(range(7*4, 7*4 + 4)) + list(range(6*4, 6*4 + 4)) + list(range(5*4, 5*4 + 4)) + list(range(3*4, 3*4 + 4)) + list(range(2*4, 2*4 + 4))]
    if R == 23:
        # Integral attack on 23 rounds of LBlock in https://link.springer.com/chapter/10.1007/978-3-319-26617-6_12 (2015)
        target_subkeys = ['k_%d_%d' % (r, i) for r in [22] for i in range(3*4, 3*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [22] for i in range(5*4, 5*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [22] for i in range(1*4, 1*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [21] for i in range(6*4, 6*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [22] for i in range(4*4, 4*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [22] for i in range(6*4, 6*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [22] for i in range(0*4, 0*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [21] for i in range(4*4, 4*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [22] for i in range(7*4, 7*4 + 2)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [21] for i in range(1*4, 1*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [20] for i in range(2*4, 2*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [21] for i in range(0*4, 0*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [22] for i in range(2*4, 2*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [21] for i in range(5*4, 5*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [18] for i in range(0*4, 0*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [20] for i in range(3*4, 3*4 + 1)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [21] for i in range(3*4 + 3, 3*4 + 4)]

        target_subkeys += ['k_%d_%d' % (r, i) for r in [21] for i in range(2*4, 2*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [20] for i in range(4*4, 4*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [20] for i in range(5*4, 5*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [21] for i in range(7*4, 7*4 + 1)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [20] for i in range(6*4 + 2, 6*4 + 4)]
        target_subkeys += ['k_%d_%d' % (r, i) for r in [20] for i in range(7*4, 7*4 + 1)]

                         
    print('Size of involved subkeys: %d' % len(target_subkeys))
    eqs += 'target\n' + '\n'.join(target_subkeys) + '\nend'
   
    # relation_file_path = os.path.join(output_dir, 'XL18_relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    # relation_file_path = os.path.join(output_dir, 'Z17_relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    relation_file_path = os.path.join(output_dir, 'two_sides_relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))    
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    lblock_kb(R=24)
    
if __name__ == '__main__':
    main()
