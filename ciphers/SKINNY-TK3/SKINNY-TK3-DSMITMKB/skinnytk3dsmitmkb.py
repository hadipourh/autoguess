# Created on Sep 16, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

def tk_permute(TK):
    TWEAKEY_P = [9,15,8,13,10,14,12,11,0,1,2,3,4,5,6,7] # It has taken from Skinny's original source code
    temp = TK.copy()
    for i in range(16):
        TK[i] = temp[TWEAKEY_P[i]]

def skinnytk3dsmitmkb(R = 22):
    """
    This function, generates the relations used for automatic search for key-bridges
    in key-recovery attack based on demirci-selcuk meet in the middle attack, taken from the following paper: 
    'Automatic Demirci-Selçuk Meet-in-the-Middle Attack on SKINNY with Key-Bridging'
    https://link.springer.com/chapter/10.1007/978-3-030-41579-2_14

                                tk1
                                tk2 ================================================> TWEAKEY_P(tk) ===> ---
                                tk3
            SB       AC           |           P           MC       SB       AC           |
    x_0 ===> x_0 ===> x_0 ===> + ===> y_0 ===> P(y_0) ===> x_1 ===> x_1 ===> x_1 ===> + ===> y_1 ===> ---

    'Using a naive strategy 53 subkey bytes must be guessed. However, our tool
     automatically finds out that we only needs to guess 45 bytes to determine all these 53 bytes.'

    """
    cipher_name = 'skinnytk3kb'
    recommended_mg = 45
    recommended_ms = 12
    TK1 = ['tk1_%d' % i for i in range(16)]
    TK2 = ['tk2_%d' % i for i in range(16)]
    TK3 = ['tk3_%d' % i for i in range(16)]
    eqs = '#%s %d Rounds\n' % (cipher_name, R)
    eqs += 'connection relations\n'
    for r in range(R):
        if (r < 2 or r > 13):
            rsk = ['sk_%d_%d' % (r, i) for i in range(8)]
            for i in range(8):
                eqs += '%s, %s, %s, %s\n' % (TK1[i], TK2[i], TK3[i], rsk[i])
        tk_permute(TK1)
        tk_permute(TK2)
        tk_permute(TK3)
    subkeys_must_be_guessed_for_skinny_128_384 = ['sk_%d_%d' % (0, i) for i in [0, 1, 2, 3, 4, 5, 6]] + \
        ['sk_%d_%d' % (1, i) for i in [1, 3, 7]] + ['sk_%d_%d' % (14, i) for i in [1]] + \
        ['sk_%d_%d' % (15, i) for i in [0, 5]] + ['sk_%d_%d' % (16, i) for i in [3, 4, 6]] + \
        ['sk_%d_%d' % (17, i) for i in [1, 2, 4, 5, 7]] + \
        ['sk_%d_%d' % (i, j) for i in range(18, 22) for j in range(8)]
    eqs += 'target\n' + '\n'.join(subkeys_must_be_guessed_for_skinny_128_384)
    eqs += '\nend'
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    skinnytk3dsmitmkb(R=22)
    
if __name__ == '__main__':
    main()
