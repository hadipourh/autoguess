# Created on Sep 7, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

def skinnytk3(R=1):
    """
    This function generates the relations of Skinny-n-n for R rounds. 

                              tk ================================================> TWEAKEY_P(tk) ===> ---
         SB       AC           |           P           MC       SB       AC           |
    x_0 ===> x_0 ===> x_0 ===> + ===> y_0 ===> P(y_0) ===> x_1 ===> x_1 ===> x_1 ===> + ===> y_1 ===> ---
    """

    cipher_name = 'skinnytk3'    
    P = [0, 1, 2, 3, 7, 4, 5, 6, 10, 11, 8, 9, 13, 14, 15, 12]
    TKP = [9, 15, 8, 13, 10, 14, 12, 11, 0, 1, 2, 3, 4, 5, 6, 7]
    tk1 = ['tk1_%d' % i for i in range(16)]   
    tk2 = ['tk2_%d' % i for i in range(16)]
    tk3 = ['tk3_%d' % i for i in range(16)]
    # 1 round
    # recommended_mg = 16
    # recommended_ms = 4
    # 2 rounds
    # recommended_mg = 32
    # recommended_ms = 8
    # 3 rounds
    # recommended_mg = 35
    # recommended_ms = 25
    # 4 rounds
    # recommended_mg = 37
    # recommended_ms = 30
    # 5 rounds 
    # recommended_mg = 38
    # recommended_ms = 50
    # 6 rounds
    # recommended_mg = 41
    # recommended_ms = 50
    # 7 rounds 
    # recommended_mg = 42
    # recommended_ms = 60
    # 8 rounds 
    # recommended_mg = 44
    # recommended_ms = 70
    # 9 rounds 
    # recommended_mg = 44
    # recommended_ms = 90    
    # 10 rounds 
    # recommended_mg = 46
    # recommended_ms = 110
    # 11 rounds 
    recommended_mg = 47
    recommended_ms = 120
    eqs = '#%s %d Rounds\n' % (cipher_name, R)
    eqs += 'connection relations\n'
    for r in range(R):
        xin = ['x_%d_%d' % (r, i) for i in range(16)]        
        xout = ['x_%d_%d' % (r + 1, i) for i in range(16)]
        y = ['y_%d_%d' % (r, i) for i in range(16)]
        tk = ['tk_%d_%d' % (r, i) for i in range(8)]
        # Generaete AddTweakey relations
        for i in range(4):
            for j in range(4):
                if i < 2:
                    eqs += '%s, %s, %s, %s\n' % (tk1[j + 4*i], tk2[j + 4*i], tk3[j + 4*i], tk[j + 4*i])
                    eqs += '%s, %s, %s\n' % (xin[j + 4*i], tk[j + 4*i], y[j + 4*i])
                else:
                    eqs += '%s, %s\n' % (xin[j + 4*i], y[j + 4*i])
        # Apply ShiftRows
        py = [y[P[i]] for i in range(16)]
        # Generate MixColumn relations
        for j in range(4):
            eqs += '%s, %s, %s, %s\n' % (py[j + 0*4], py[j + 2*4], py[j + 3*4], xout[j + 0*4])
            eqs += '%s, %s\n' % (py[j], xout[j + 1*4])
            eqs += '%s, %s, %s\n' % (py[j + 1*4], py[j + 2*4], xout[j + 2*4])
            eqs += '%s, %s, %s\n' % (py[j + 0*4], py[j + 2*4], xout[j + 3*4])
        # Update Tweakey
        temp1 = tk1.copy()
        temp2 = tk2.copy()
        temp3 = tk3.copy()
        tk1 = [temp1[TKP[i]] for i in range(16)]
        tk2 = [temp2[TKP[i]] for i in range(16)]
        tk3 = [temp3[TKP[i]] for i in range(16)]

    plaintext = ['x_0_%d' % i for i in range(16)]
    ciphertext = ['x_%d_%d' % (R, i) for i in range(16)]
    eqs += 'known\n' + '\n'.join(plaintext + ciphertext)
    eqs += '\nend'
   
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    skinnytk3(R=11)
    
if __name__ == '__main__':
    main()
