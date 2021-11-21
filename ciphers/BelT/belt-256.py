# Created on Apr 3, 2021
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

def belt(R=1):
    cipher_name = 'belt-256'
    # R round
    recommended_mg = 10
    recommended_ms = 10
    SK = ['k_%d' % i for i in range(1, 9)]

    
    eqs = '#%s %d Rounds\n' % (cipher_name, R)
    eqs += 'connection relations\n'
    for r in range(0, R):
        eqs += 'w_%d, %s, a_%d\n' % (r, SK[(0 + r*7)%8], r)
        eqs += 'a_%d, x_%d, d_%d\n' % (r, r, r)
        eqs += 'y_%d, b_%d, e_%d\n' % (r, r, r)
        eqs += '%s, b_%d, z_%d\n' % (SK[(1 + r*7)%8], r, r)
        eqs += 'w_%d, c_%d, y_%d\n' % (r, r, r + 1)
        eqs += 'c_%d, %s, d_%d\n' % (r, SK[(2 + r*7)%8], r)
        eqs += 'd_%d, %s, e_%d, f_%d\n' % (r, SK[(3 + r*7)%8], r, r)
        eqs += 'd_%d, f_%d, g_%d\n' % (r, r, r)
        eqs += 'f_%d, e_%d, h_%d\n' % (r, r, r)
        eqs += 'h_%d, %s, p_%d\n' % (r, SK[(4 + r*7)%8], r)
        eqs += 'p_%d, z_%d, x_%d\n' % (r, r, r + 1)
        eqs += 'y_%d, %s, q_%d\n' % (r + 1, SK[(5 + r*7)%8], r)
        eqs += 'q_%d, g_%d, w_%d\n' % (r, r, r + 1)
        eqs += 'h_%d, s_%d, z_%d\n' % (r, r, r + 1)
        eqs += 's_%d, %s, x_%d\n' % (r, SK[(6 + r*7)%8], r + 1)
    known_input = ['w_0', 'x_0', 'y_0', 'z_0']
    known_output = ['w_%d' % R, 'x_%d' % R, 'y_%d' % R, 'z_%d' % R]
    eqs += 'known\n' + '\n'.join(known_input + known_output)   
    eqs += '\ntarget\n' + '\n'.join(SK)
    eqs += '\nend'
    relation_file_path = os.path.join(output_dir, 'relationfile_%s_%dr_mg%d_ms%d.txt' % (cipher_name, R, recommended_mg, recommended_ms))
    with open(relation_file_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    belt(R=5)
    
if __name__ == '__main__':
    main()
