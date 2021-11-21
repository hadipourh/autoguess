# Created on Sep 7, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

def lea128(R=3):
    cipher_name = 'LEA128'
    # 1 round
    # recommended_mg = 1
    # recommended_ms = 1
    # 2 rounds 
    # recommended_mg = 1
    # recommended_ms = 6
    # 3 rounds 
    # recommended_mg = 2
    # recommended_ms = 5
    # 4 rounds 
    recommended_mg = 3
    recommended_ms = 4

    eqs = '#%s %d Rounds\n' % (cipher_name, R)
    eqs += 'connection relations\n'
    rk = ['k_0', 'k_1', 'k_2', 'k_1', 'k_3', 'k_1']
    for r in range(R):
        xout = ['x_%d_%d' % (r + 1, i) for i in range(4)] 
        xin = ['x_%d_%d' % (r, i) for i in range(4)]
        eqs += '%s, %s, %s, %s, %s\n' % (xout[0], xin[0], rk[0], xin[1], rk[1])
        eqs += '%s, %s, %s, %s, %s\n' % (xout[1], xin[1], rk[2], xin[2], rk[3])
        eqs += '%s, %s, %s, %s, %s\n' % (xout[2], xin[2], rk[4], xin[3], rk[5])
        eqs += '%s, %s\n' % (xout[3], xin[0])
    plaintext = ['x_%d_%d' % (0, i) for i in range(4)]
    ciphertext = ['x_%d_%d' % (R, i) for i in range(4)]
    eqs += 'known\n' + '\n'.join(plaintext + ciphertext) + '\nend'
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    lea128(R=4)
    
if __name__ == '__main__':
    main()
