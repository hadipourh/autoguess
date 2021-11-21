# Created on Sep 19, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

def craft(R=1):
    cipher_name = 'craft'
    # 1 round
    # recommended_mg = 0
    # recommended_ms = 3
    # 2 rounds
    # recommended_mg = 16
    # recommended_ms = 4
    # 3 rounds
    # recommended_mg = 16
    # recommended_ms = 10
    # 4 rounds
    # recommended_mg = 20
    # recommended_ms = 16
    # 5 rounds 
    # recommended_mg = 20
    # recommended_ms = 16
    # 6 rounds
    # recommended_mg = 23
    # recommended_ms = 35
    # 7 rounds 
    # recommended_mg = 23
    # recommended_ms = 35
    # 8 rounds 
    # recommended_mg = 26
    # recommended_ms = 40
    # 9 rounds 
    # recommended_mg = 26
    # recommended_ms = 50    
    # 10 rounds 
    # recommended_mg = 28
    # recommended_ms = 50
    # 11 rounds 
    # recommended_mg = 28
    # recommended_ms = 52
    # 12 rounds 
    # recommended_mg = 29
    # recommended_ms = 55
    # 13 rounds 
    # recommended_mg = 30
    # recommended_ms = 60
    # 14 rounds 
    recommended_mg = 32
    recommended_ms = 70

    permute_nibble = [15, 12, 13, 14, 10, 9, 8, 11, 6, 5, 4, 7, 1, 2, 3, 0]
    eqs = '#%s %d Rounds\n' % (cipher_name, R)
    eqs += 'connection relations\n'
    key = [['k_%d_%d_%d' % (i, j, k) for j in range(4) for k in range(4)] for i in range(2)]
    for r in range(0, R):
        x = ['x_%d_%d_%d' % (r, i, j) for i in range(4) for j in range(4)]
        y = ['y_%d_%d_%d' % (r, i, j) for i in range(4) for j in range(4)]
        x_new = ['x_%d_%d_%d' % (r + 1, i, j) for i in range(4) for j in range(4)]
        # Apply MixColumn
        for n in range(4):
            eqs += '%s, %s, %s, %s\n' % (x[n], x[8 + n], x[12 + n], y[n])
            eqs += '%s, %s, %s\n' % (x[4 + n], x[12 + n], y[4 + n])
            eqs += '%s, %s\n' % (x[8 + n], y[8 + n])
            eqs += '%s, %s\n' % (x[12 + n], y[12 + n])
        round_key = key[r%2]
        # Apply Inverse PermuteNibble
        p_inv_x_new = [0]*16
        for n in range(16):
            p_inv_x_new[permute_nibble[n]] = x_new[n]
        for n in range(16):
            eqs += '%s, %s, %s\n' % (y[n], round_key[n], p_inv_x_new[n])
    plaintext = ['x_0_%d_%d' % (i, j) for i in range(4) for j in range(4)]
    ciphertext = ['x_%d_%d_%d' % (R, i, j) for i in range(4) for j in range(4)]
    eqs += 'known\n' + '\n'.join(plaintext + ciphertext) + '\nend'
   
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    craft(R=14)
    
if __name__ == '__main__':
    main()
