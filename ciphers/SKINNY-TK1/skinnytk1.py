# Created on Sep 7, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

def skinnytk1(R=1):
    """
    This function generates the relations of Skinny-n-n for R rounds. 

                              tk ================================================> TWEAKEY_P(tk) ===> ---
         SB       AC           |           P           MC       SB       AC           |
    x_0 ===> x_0 ===> x_0 ===> + ===> y_0 ===> P(y_0) ===> x_1 ===> x_1 ===> x_1 ===> + ===> y_1 ===> ---
    """

    cipher_name = 'skinnytk1'    
    P = [0, 1, 2, 3, 7, 4, 5, 6, 10, 11, 8, 9, 13, 14, 15, 12]
    TKP = [9, 15, 8, 13, 10, 14, 12, 11, 0, 1, 2, 3, 4, 5, 6, 7]
    tk = ['tk_%d' % i for i in range(16)]    
    # 1 round
    # recommended_mg = 0
    # recommended_ms = 3
    # 2 rounds
    # recommended_mg = 0
    # recommended_ms = 7
    # 3 rounds
    # recommended_mg = 3
    # recommended_ms = 22
    # 4 rounds
    # recommended_mg = 5
    # recommended_ms = 22
    # 5 rounds 
    # recommended_mg = 6
    # recommended_ms = 30
    # 6 rounds
    # recommended_mg = 9
    # recommended_ms = 40
    # 7 rounds 
    # recommended_mg = 10
    # recommended_ms = 40
    # 8 rounds 
    # recommended_mg = 12
    # recommended_ms = 60
    # 9 rounds 
    # recommended_mg = 12
    # recommended_ms = 70
    # 10 rounds 
    recommended_mg = 14
    recommended_ms = 70
    # 11 rounds 
    # recommended_mg = 14
    # recommended_ms = 75
    eqs = '#%s %d Rounds\n' % (cipher_name, R)
    eqs += 'connection relations\n'
    for r in range(R):
        xin = ['x_%d_%d' % (r, i) for i in range(16)]        
        xout = ['x_%d_%d' % (r + 1, i) for i in range(16)]
        y = ['y_%d_%d' % (r, i) for i in range(16)]
        # Generaete AddTweakey relations
        for i in range(4):
            for j in range(4):
                if i < 2:
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
        temp = tk.copy()
        tk = [temp[TKP[i]] for i in range(16)]
    plaintext = ['x_0_%d' % i for i in range(16)]
    ciphertext = ['x_%d_%d' % (R, i) for i in range(16)]
    eqs += 'known\n' + '\n'.join(plaintext + ciphertext)
    eqs += '\nend'
   
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    skinnytk1(R=10)
    
if __name__ == '__main__':
    main()
