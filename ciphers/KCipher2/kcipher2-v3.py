# Created on Apr 12, 2021
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir


def k2cipher(T=7):
    cipher_name = 'kcipher2'
    recommended_mg = 10
    recommended_ms = 19
    eqs = '#%s %d Rounds\n'
    eqs += 'connection relations\n'
    for t in range(T):
        # FSR-A Relations
        eqs += 'A_%d, A_%d, A_%d\n' % (5 + t, 3 + t, t)
        # FSR-B Relations
        eqs += 'B_%d, BD_%d, B_%d, B_%d, BD_%d\n' % (11 + t, t, 1 + t, 6 + t, 8 + t)
        eqs += 'A_%d, B_%d => BD_%d\n' % (2 + t, t, t)
        eqs += 'A_%d, B_%d => BD_%d\n' % (2 + t, 8 + t, 8 + t)
        # FSM Relations:
        eqs += 'R1_%d, L2_%d, B_%d\n' % (1 + t, t, 9 + t)
        eqs += 'L1_%d, R2_%d, B_%d\n' % (1 + t, t, 4 + t)
        eqs += 'R2_%d, R1_%d\n' % (1 + t, t)
        eqs += 'L2_%d, L1_%d\n' % (1 + t, t)
        # Output Relations
        eqs += 'B_%d, R2_%d, R1_%d, A_%d\n' % (t, t, t, 4 + t)
        eqs += 'B_%d, L2_%d, L1_%d, A_%d\n' % (10 + t, t, t, t)
    eqs += 'end'
    eqsfile_path = os.path.join(output_dir, 'relationfile_%s_%dclk_mg%d_ms%d.txt' % (
        cipher_name, T, recommended_mg, recommended_ms))
    with open(eqsfile_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    k2cipher(T=7)

if __name__ == '__main__':
    main()
