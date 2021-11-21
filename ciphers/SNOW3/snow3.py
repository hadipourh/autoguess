# Created on Sep 2, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

def snow3(T=10):
    cipher_name = 'snow3'
    recommended_mg = 10
    recommended_ms = 12
    eqs = '#%s %d Rounds\n' % (cipher_name, T)
    eqs += 'connection relations\n'
    # for t in range(T//2):
    #     eqs += 'S_%d, S_%d, S_%d, S_%d, S_%d, S_%d, S_%d\n' % (t, 2 + t, 4 + t, 11 + t, 13 + t, 16 + t, 18 + t)
    # for t in range(T//3):
    #     eqs += 'S_%d, S_%d, S_%d, S_%d, S_%d, S_%d, S_%d\n' % (t, 2 + t, 5 + t, 7 + t, 11 + t, 16 + t, 21 + t)
    for t in range(T):
        # feedback relations
        eqs += 'S_%d, S_%d, S_%d, S_%d\n' % (t, 2 + t, 11 + t, 16 + t)
        # output relations
        eqs += 'S_%d, S_%d, R_%d, R_%d\n' % (t, 15 + t, 1 + t, 2 + t)
        # eqs += 'S_%d, R_%d, R_%d, R_%d\n' % (5 + t, 2 + t, 1 + t, t) # fsm relations (Warning: This relation has been considered in (https://ieeexplore.ieee.org/abstract/document/7000843/))
        # However it is wrong!
        eqs += 'S_%d, S_%d, R_%d, R_%d\n' % (5 + t, 3 + t, 1 + t, t)
    eqs += 'end'
    eqsfile_path = os.path.join(output_dir, 'relationfile_%s_%dclk_mg%d_ms%d.txt' % (cipher_name, T, recommended_mg, recommended_ms))
    with open(eqsfile_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    snow3(T=10)

if __name__ == '__main__':
    main()
