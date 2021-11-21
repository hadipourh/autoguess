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

def tktwine80kb(R=25):
    """
    Evaluating the results of the following paper:
    Impossible Differential Cryptanalysis of Reduced-Round Tweakable TWINE [eprint-2020]
    ID attack on 25 rounds of T-TWIN-80 in which 22 subkey nibbles are involved. 
    According to the authors' claim, all of these 22 nibbles can be deduced from 18 nibbles. 
    However using our tool we prove these 22 nibbles deduced from 19 nibbles. There might be a mistake in this paper!
    After contacting athors we noticed that there was a typo in paper whih missled us. As aresult their claim seems to be true
    since we have considered an extra invloved nibbles in our previous experiments.
    
    Received email from the authors:
    
    '''
    "22 round keys" should be "21 round keys", thank you for pointing out this typo.These 21 round keys take only 2^72 possible values (18 nibbles). These 21 round keys are: $ RK^{0}      _{[0,1,2,3,5,6,7]}, RK^{1}_{[2,4,5,6]}, RK^{2}_{[3,5]}, RK^{3}_{1}, RK^{22}_{7}, RK^{23}_{[5,7]}$, and $ RK^{24}_{[0,4,5,7]}$. And based on the key schedule, $ RK^{2}_{3} = RK^{0}_{5}, RK^{2}_{5} = RK^{0}_{1} $, and $ RK^{3}_{1} = RK^{0}_{6} + CONSTANT $. This makes them equivalent to 18 nibbles.

    Finally, please note that $ RK^{0}_{4} $ is not involved in the attack.
    '''
    
    """
    cipher_name = 'tktwine80_kb'
    # 25 rounds
    # recommended_mg = 18
    # recommended_ms = 2
    # 26 rounds
    recommended_mg = 19
    recommended_ms = 5
    # 27 rounds
    # recommended_mg = 76
    # recommended_ms = 5
    eqs = '#%s %d Rounds\n' % (cipher_name, R)
    eqs += 'connection relations\n'
    RK = [[0 for i in range(8)] for r in range(R)]
    for r in range(R):
        key_st = ['k_%d_%d' % (r, i) for i in range(20)]
        new_key_st = ['k_%d_%d' % (r + 1, i) for i in range(20)]
        temp1 = right_rotate_array(new_key_st, 20, 4)
        temp2 = right_rotate_array(temp1[0:4], 4, 1)
        new_key_st_permuted = temp2 + temp1[4:]
        RK[r] = [key_st[1], key_st[3], key_st[4], key_st[6], key_st[13], key_st[14], key_st[15], key_st[16]]
        # Apply Sboxes
        eqs += '%s, %s, %s\n' % (new_key_st_permuted[1], key_st[1], key_st[0])
        eqs += '%s, %s, %s\n' % (new_key_st_permuted[4], key_st[4], key_st[16])
        for i in range(20):
            if i not in [1, 4]:
                eqs += '%s, %s\n' % (new_key_st_permuted[i], key_st[i])
    if R == 25:
        target_subkeys =  [RK[0][i] for i in list(range(0, 4)) + list(range(5, 8))] + \
            [RK[1][i] for i in [2, 4, 5, 6]] + \
            [RK[2][i] for i in [3, 5]] + \
            [RK[3][i] for i in [1]] + \
            [RK[22][i] for i in [7]] + \
            [RK[23][i] for i in [5, 7]] + \
            [RK[24][i] for i in [0, 4, 5, 7]]
    if R == 26:
        # reference: https://eprint.iacr.org/2020/1227
        # Sec. 4.1
        target_subkeys = [RK[25][i] for i in range(8)] + \
            [RK[24][i] for i in [0, 1, 2, 3, 4, 5, 7]] + \
                [RK[23][i] for i in [0, 1, 2, 6, 7]] + \
                    [RK[22][i] for i in [0, 4, 6]] + \
                        [RK[21][i] for i in [4, 5]] + \
                            [RK[20][i] for i in [5]] + \
                                [RK[19][i] for i in [7]]
                                
    print('Size of involved subkeys: %d' % len(target_subkeys))
    ##########################################################
    # Remove k_0_3, k_0_14, k_0_15 from the known variables
    # known_variables = target_subkeys.copy()
    # for k in ['k_0_3', 'k_0_14', 'k_0_15']:
    #     known_variables.remove(k)
    #eqs += 'known, ' + ','.join(known_variables) + '\n'
    ##########################################################
    eqs += 'target\n' + '\n'.join(target_subkeys)
    eqs += '\nend'
   
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    tktwine80kb(R=25)
    
if __name__ == '__main__':
    main()
