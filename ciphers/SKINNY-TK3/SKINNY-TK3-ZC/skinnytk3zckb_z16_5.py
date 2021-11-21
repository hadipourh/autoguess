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

def skinnytk3zckb(R = 23):
    """
    Checking the ZC attack propsed in the following paper: 
    Zero-Correlation Attacks on Tweakable Block Ciphers with Linear Tweakey Expansion
    https://eprint.iacr.org/2019/185
    This attack covers 23 rounds of Skinny-64-192 in which 37 nibbles of subtweakeys are involved
    """
    assert(R == 23)
    cipher_name = 'skinnytk3zckb'
    recommended_mg = 34
    recommended_ms = 12    
    TK1 = ['tk1_%d' % i for i in range(16)]
    TK2 = ['tk2_%d' % i for i in range(16)]
    TK3 = ['tk3_%d' % i for i in range(16)]
    eqs = '#%s %d Rounds\n' % (cipher_name, R)
    eqs += 'connection relations\n'    
    for r in range(R):
        if (r > 15):
            rsk = ['sk_%d_%d' % (r, i) for i in range(8)]
            for i in range(8):
                eqs += '%s, %s, %s, %s\n' % (TK1[i], TK2[i], TK3[i], rsk[i])
        tk_permute(TK1)
        tk_permute(TK2)
        tk_permute(TK3)
    subkeys_must_be_guessed_for_skinny_zc_64_192 = ['sk_%d_%d' % (16, i) for i in [5]] + \
        ['sk_%d_%d' % (17, i) for i in [6]] + ['sk_%d_%d' % (18, i) for i in [1, 4, 7]] + \
        ['sk_%d_%d' % (19, i) for i in [0, 2, 3, 4, 5]] + \
        ['sk_%d_%d' % (i, j) for i in range(20, 23) for j in range(8)]
    print('Size of the involved sub-tweakeys: %d' % len(subkeys_must_be_guessed_for_skinny_zc_64_192))
    eqs += 'target\n' + '\n'.join(subkeys_must_be_guessed_for_skinny_zc_64_192)
    eqs += '\nend'
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dr_mg%d_ms%d_z16_5.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    skinnytk3zckb(R=23)
    
if __name__ == '__main__':
    main()
