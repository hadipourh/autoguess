# Created on Sep 6, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

def snow1(T=9):
    cipher_name = 'snow1'
    recommended_mg = 9
    recommended_ms = 9
    eqs = '#%s %d Rounds\n'
    eqs += 'connection relations\n'
    for t in range(T):
        # FSM symmetric relations:
        eqs += 'R_%d, R_%d, R_%d, S_%d\n' % (t + 2, t, t + 1, 15 + t)
        # Output relations:
        eqs += 'S_%d, S_%d, R_%d, R_%d, z_%d\n' % (t, 15 + t, t + 1, t, t)
        # Feedback relations:
        eqs += 'S_%d, S_%d, S_%d, S_%d\n' % (t + 16, t + 9, t + 3, t)
        # if t < (T // 2):
        #     eqs += 'S_%d, S_%d, S_%d, S_%d\n' % (t + 32, t + 18, t + 6, t)
    eqs += 'known\n' + '\n'.join(['z_%d' % i for i in range(T)])
    eqs += '\nend'
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dclk_mg%d_ms%d.txt' % (cipher_name, T, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    snow1(T=9)
    
if __name__ == '__main__':
    main()
