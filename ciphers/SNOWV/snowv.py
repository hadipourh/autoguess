# Created on Sep 2, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir


def snowv(T=5):
    cipher_name = 'snowv'
    recommended_mg = 3
    recommended_ms = 8
    eqs = '#%s %d Rounds\n'
    eqs += 'connection relations\n'
    for t in range(T):
        # FSM symmetric relations:
        eqs += 'R1_%d, R2_%d, R3_%d, AL_%d\n' % (t + 1, t, t, t)
        eqs += 'R2_%d, R1_%d\n' % (t + 1, t)
        eqs += 'R3_%d, R2_%d\n' % (t + 1, t)        
        # Output relations:
        eqs += 'z_%d, R1_%d, BH_%d, R2_%d\n' % (t, t, t, t)        
        # Feedback implication relations:
        eqs += 'AL_%d, AH_%d\n' % (t + 1, t)
        eqs += 'AH_%d, BL_%d, A_%d\n' % (t + 1, t, t)
        eqs += 'AH_%d, AL_%d => A_%d\n' % (t, t, t)
        eqs += 'A_%d => AL_%d\n' % (t, t)
        eqs += 'A_%d => AH_%d\n' % (t, t)
        eqs += 'BL_%d, BH_%d\n' % (t + 1, t)
        eqs += 'BH_%d, AL_%d, B_%d\n' % (t + 1, t, t)
        eqs += 'BH_%d, BL_%d => B_%d\n' % (t, t, t)
        eqs += 'B_%d => BL_%d\n' % (t, t)
        eqs += 'B_%d => BH_%d\n' % (t, t)
    eqs += 'known\n' + '\n'.join(['z_%d' % i for i in range(T)])
    eqs += '\nend'
    eqsfile_path = os.path.join(output_dir, 'relationfile_%s_%dclk_mg%d_ms%d.txt' % (
        cipher_name, T, recommended_mg, recommended_ms))
    with open(eqsfile_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    snowv(T=4)

if __name__ == '__main__':
    main()
