# Created on Sep 7, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

def khudra_alternative(R = 14):
    """
    "A Guess-and-Determine Attack on Reduced-Round Khudra and Weak Keys of Full Cipher"
    https://eprint.iacr.org/2015/1163.pdf
    """
    cipher_name = 'khudra_alternative'
    # 1 rounds
    # recommended_mg = 0
    # recommended_ms = 5
    # 2 rounds
    # recommended_mg = 1
    # recommended_ms = 5
    # 3 rounds
    # recommended_mg = 1
    # recommended_ms = 6
    # 4 rounds
    # recommended_mg = 1
    # recommended_ms = 6
    # 5 rounds
    # recommended_mg = 2
    # recommended_ms = 6
    # 6 rounds
    # recommended_mg = 3
    # recommended_ms = 6
    # 7 rounds
    # recommended_mg = 3
    # recommended_ms = 8
    # 8 rounds
    # recommended_mg = 3
    # recommended_ms = 11
    # 9 rounds
    # recommended_mg = 3
    # recommended_ms = 13
    # 10 rounds
    # recommended_mg = 4
    # recommended_ms = 10
    # 11 rounds
    # recommended_mg = 4
    # recommended_ms = 11
    # 12 rounds
    # recommended_mg = 4
    # recommended_ms = 12
    # # 13 rounds
    # recommended_mg = 4
    # recommended_ms = 15
    # 14 rounds
    recommended_mg = 4
    recommended_ms = 16
    eqs = '#%s %d Rounds\n' % (cipher_name, R)
    eqs += 'algebraic relations\n'
    key = ['k_0', 'k_1', 'k_2', 'k_3', 'k_4']
    for r in range(0, R):
        x = ['x_%d_%d' % (r, i) for i in range(4)]
        x_new = ['x_%d_%d' % (r + 1, i) for i in range(4)]
        # if r == 0:
        #     # Whitenning key
        #     eqs += '%s, %s, %s\n' % (x[0], key[0], x_new[3])
        #     eqs += '%s, %s, %s\n' % (x[2], key[1], x_new[1])        
        eqs += '%s, %s, %s, %s\n' % (x[0], key[(2*r + 1)%5], x[1], x_new[0])
        eqs += '%s, %s, %s\n' % (x[2], x[3], x_new[2])
        eqs += '%s, %s\n' % (x[0], x_new[3])
        eqs += '%s, %s\n' % (x[2], x_new[1])
    x = ['x_%d_%d' % (R, i) for i in range(4)]
    x_new = ['x_%d_%d' % (R + 1, i) for i in range(4)]    
    eqs += '%s, %s, %s\n' % (x[0], key[4], x_new[0])
    eqs += '%s, %s, %s\n' % (x[1], key[4], x_new[1])
    eqs += '%s, %s\n' % (x[2], x_new[2])
    eqs += '%s, %s, %s\n' % ('dummy_var', key[2], key[3])
    eqs += '%s, %s, %s\n' % (x[3], 'dummy_var', x_new[3])
    plaintext = ['x_0_%d' % i for i in range(4)]
    ciphertext = ['x_%d_%d' % (R + 1, i) for i in range(4)]
    eqs += 'known\n' + '\n'.join(plaintext + ciphertext) + '\nend'
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    khudra_alternative(R=14)
    
if __name__ == '__main__':
    main()
