# Created on Sep 6, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import itertools
import os

output_dir = os.path.curdir

def aes1kp(R=2):
    """
    This function is used to generate the word-based relations of AES
    The used variables are as follows: 

           K_0 ==============> Key-Schedule==========> K_1 ==============> Key-Schedule==========> K_2 =========== ...
            |         SB       SR           MC          |         SB       SR           MC          |
      P ==> + ==> X_0 ==> SX_0 ==> SR(SX_0) ==> W_0 ==> + ==> X_1 ==> SX_1 ==> SR(SX_1) ==> W_1 ==> + ==> X_2 == > ...

    Knowing X_i is equivalent to know SX_i, therefore, using X_i instead of SX_i, we eliminate SX_i variables in 
    each round. 
    Involved variables:
    P_0
    X_i for 0 <= i <= r
    W_i for 0 <= i <= r - 1
    K_i for 0 <= i <= r

    State array:
    X_i_0_0  X_i_0_1  X_i_0_2  X_i_0_3
    X_i_1_0  X_i_1_1  X_i_1_2  X_i_1_3
    X_i_2_0  X_i_2_1  X_i_2_2  X_i_2_3
    X_i_3_0  X_i_3_1  X_i_3_2  X_i_3_3
    """
    cipher_name = 'aes1kp'    
    # Template of 'SR o MDS' relations describing output words w.r.t. the input words
    mds_plain_relations = ['W_0_0_0, X_0_0_0, X_0_1_1, X_0_2_2, X_0_3_3',
                           'W_0_0_1, X_0_0_1, X_0_1_2, X_0_2_3, X_0_3_0',
                           'W_0_0_2, X_0_0_2, X_0_1_3, X_0_2_0, X_0_3_1',
                           'W_0_0_3, X_0_0_3, X_0_1_0, X_0_2_1, X_0_3_2',
                           'W_0_1_0, X_0_0_0, X_0_1_1, X_0_2_2, X_0_3_3',
                           'W_0_1_1, X_0_0_1, X_0_1_2, X_0_2_3, X_0_3_0',
                           'W_0_1_2, X_0_0_2, X_0_1_3, X_0_2_0, X_0_3_1',
                           'W_0_1_3, X_0_0_3, X_0_1_0, X_0_2_1, X_0_3_2',
                           'W_0_2_0, X_0_0_0, X_0_1_1, X_0_2_2, X_0_3_3',
                           'W_0_2_1, X_0_0_1, X_0_1_2, X_0_2_3, X_0_3_0',
                           'W_0_2_2, X_0_0_2, X_0_1_3, X_0_2_0, X_0_3_1',
                           'W_0_2_3, X_0_0_3, X_0_1_0, X_0_2_1, X_0_3_2',
                           'W_0_3_0, X_0_0_0, X_0_1_1, X_0_2_2, X_0_3_3',
                           'W_0_3_1, X_0_0_1, X_0_1_2, X_0_2_3, X_0_3_0',
                           'W_0_3_2, X_0_0_2, X_0_1_3, X_0_2_0, X_0_3_1',
                           'W_0_3_3, X_0_0_3, X_0_1_0, X_0_2_1, X_0_3_2']
    # Template of key-Schedule relations
    key_sch_relations = ['K_0_3_3, K_1_3_2, K_1_3_3',
                         'K_0_3_2, K_1_3_1, K_1_3_2',
                         'K_0_3_1, K_1_3_0, K_1_3_1',
                         'K_0_0_3, K_0_3_0, K_1_3_0',
                         'K_0_2_3, K_1_2_2, K_1_2_3',
                         'K_0_2_2, K_1_2_1, K_1_2_2',
                         'K_0_2_1, K_1_2_0, K_1_2_1',
                         'K_0_2_0, K_0_3_3, K_1_2_0',
                         'K_0_1_3, K_1_1_2, K_1_1_3',
                         'K_0_1_2, K_1_1_1, K_1_1_2',
                         'K_0_1_1, K_1_1_0, K_1_1_1',
                         'K_0_1_0, K_0_2_3, K_1_1_0',
                         'K_0_0_3, K_1_0_2, K_1_0_3',
                         'K_0_0_2, K_1_0_1, K_1_0_2',
                         'K_0_0_1, K_1_0_0, K_1_0_1',
                         'K_0_0_0, K_0_1_3, K_1_0_0']
    eqs = '#%s %d Rounds\n' % (cipher_name, R)
    # Generate whitening key relations
    eqs += 'connection relations\n'
    for i in range(4):
        for j in range(4):
            eqs += 'P_%d_%d, K_%d_%d_%d, X_%d_%d_%d\n' % \
                (i, j, 0, i, j, 0, i, j)
    for r in range(R):
        # AddRoundKey Relations
        for i in range(4):
            for j in range(4):
                eqs += 'W_%d_%d_%d, K_%d_%d_%d, X_%d_%d_%d\n' % \
                    (r, i, j, r + 1, i, j, r + 1, i, j)
        # Generate key-schedule relations
        for rel in key_sch_relations:
            updated_relation = rel.replace('K_1', 'K_%d' % (r + 1))
            updated_relation = updated_relation.replace('K_0', 'K_%d' % r)
            eqs += '%s\n' % updated_relation
    ########################## Generate SR o MDS relations #############################
    ####################################################################################
        # Generate SR o MDS relations describing output w.r.t. the input for each round
        # for rel in mds_plain_relations:
        #     updated_relation = rel.replace('W_0', 'W_%d' % r)
        #     updated_relation = updated_relation.replace('X_0', 'X_%d' % r)
        #     eqs += '%s\n' % updated_relation
        # MDS property: if y = MixColumn(x), then knowledge of four bytes in (x, y) is sufficient to recover the
        # remaining four bytes in a unique way
        col0 = ['X_%d_0_0' % r, 'X_%d_1_1' % r, 'X_%d_2_2' % r, 'X_%d_3_3' % r] + \
            ['W_%d_%d_%d' % (r, i, 0) for i in range(4)]
        col1 = ['X_%d_0_1' % r, 'X_%d_1_2' % r, 'X_%d_2_3' % r, 'X_%d_3_0' % r] + \
            ['W_%d_%d_%d' % (r, i, 1) for i in range(4)]
        col2 = ['X_%d_0_2' % r, 'X_%d_1_3' % r, 'X_%d_2_0' % r, 'X_%d_3_1' % r] + \
            ['W_%d_%d_%d' % (r, i, 2) for i in range(4)]
        col3 = ['X_%d_0_3' % r, 'X_%d_1_0' % r, 'X_%d_2_1' % r, 'X_%d_3_2' % r] + \
            ['W_%d_%d_%d' % (r, i, 3) for i in range(4)]
        cols = [col0, col1, col2, col3]
        for col in cols:
            for quarter in itertools.combinations(col, 4):
                for element in col:
                    if element not in quarter:
                        eqs += ','.join(quarter) + ' => ' + element + '\n'
    ########################### End of SR o MDS relations ##############################
    ####################################################################################
    plaintext = ['P_%d_%d' % (i, j) for i in range(4) for j in range(4)]
    ciphertext = ['X_%d_%d_%d' % (R, i, j) for i in range(4) for j in range(4)]
    if R == 1:
        # 1 round
        # SAT solver solves this case faster
        recommended_mg = 6
        recommended_ms = 14
        # Observation 4: 
        # k_0_col3 = ', '.join(['K_0_%d_%d' % (i, 3) for i in range(4)])
        # eqs += plaintext + ', ' + ciphertext + ', ' + k_0_col3 + ' => ' + 'K_0_1_0\n'
        # eqs += plaintext + ', ' + ciphertext + ', ' + k_0_col3 + ' => ' + 'K_0_0_3\n'
        pass
    if R == 2:
        # 2 rounds
        # SAT solver solves this case faster
        recommended_mg = 10
        recommended_ms = 20        
        # Observation 3:
        r = 0
        for i in range(4):
            eqs += 'K_%d_%d_%d, K_%d_%d_%d, K_%d_%d_%d\n' % (r + 2, i, 0, r + 2, i, 2, r, i, 2)
            eqs += 'K_%d_%d_%d, K_%d_%d_%d, K_%d_%d_%d\n' % (r + 2, i, 1, r + 2, i, 3, r, i, 3)
            eqs += 'K_%d_%d_%d, K_%d_%d_%d, K_%d_%d_%d\n' % (r + 2, i, 1, r + 1, (i + 1)%4, 3, r, i, 1)
        # pass
    if R == 3:
        # 3 rounds
        # SAT solver solves this case faster
        recommended_mg = 15
        recommended_ms = 22        
    # Declare known variables
    eqs += 'known\n'
    known_data = plaintext + ciphertext
    eqs += "\n".join(known_data)    
    eqs += '\nend'
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    aes1kp(R=3)
    
if __name__ == '__main__':
    main()
