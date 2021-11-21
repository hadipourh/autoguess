# Created on Sep 2, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

def rabitgen(offset=0, start_clock=0, n=3, ivn=0):
    cipher_name = 'rabit'
    recommended_mg = 6
    recommended_ms = 22
    eqs = '#%s %d clock cycles\n' % (cipher_name, n)
    eqs += 'connection relations\n'
    known_vars = ['x_%d_0' % j for j in range(0, ivn)]
    for i in range(start_clock, n):
        for j in range(0, 8):
            eqs += 'x_%d_%d, x_%d_%d, x_%d_%d\n' % (
                j, i + 1, (j - 1) % 8, i, (j - 2) % 8, i)
        if (i > offset):
            eqs += 'z_%d, x_%d_%d, x_%d_%d\n' % (i, 2, i, 7, i)
            known_vars.append('z_%d' % i)
    known_vars_st = 'known\n' + '\n'.join(known_vars) + '\nend'
    if known_vars != []:
        eqs += known_vars_st
    eqsfile_path = os.path.join(output_dir, 'relationfile_%s_%dclk_mg%d_ms%d.txt' % (cipher_name, n, recommended_mg, recommended_ms))
    with open(eqsfile_path, 'w') as relation_file:
        relation_file.write(eqs)
    
def main():
    rabitgen(n=9)

if __name__ == '__main__':
    main()
