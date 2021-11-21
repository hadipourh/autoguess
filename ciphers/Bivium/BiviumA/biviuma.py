# Created on Mar 07, 2021
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

str_feedback1 = lambda a24, b15, b0, b1, b2: a24 + ' + ' +  b15 + ' + ' + b0 + ' + ' + b1 + '*' + b2
str_feedback2 = lambda b6, a27, a0, a1, a2: b6 + ' + ' + a27 + ' + ' + a0 + ' + ' + a1 + '*' + a2
str_f = lambda b0, b15: b0 + ' + ' + b15

def biviuma(T=177):
    cipher_name = 'biviuma'
    # 177 clock cycles
    recommended_mg = 24
    recommended_ms = 85

    eqs = '#%s %d clock cycles\n' % (cipher_name, T)
    eqs += 'connection relations\n'
    for t in range(T):
        eqs += 'b_%d, b_%d => bm_%d\n' % (t + 1, t + 2, t)
        eqs += 'a_%d, a_%d => am_%d\n' % (t + 1, t + 2 ,t)
    eqs += 'algebraic relations\n'
    for t in range(T):
        eqs += 'a_%d + a_%d + z_%d + bm_%d\n' % (t + 93, t + 24, t, t)
        eqs += 'b_%d + b_%d + a_%d + a_%d + am_%d\n' % (t + 84, t + 6, t + 27, t, t)
        eqs += 'b_%d + b_%d + z_%d\n' % (t, t + 15, t)
    eqs += 'known\n' + '\n'.join(['z_%d' % i for i in range(T)]) + '\nend'
    eqsfile_path = os.path.join(output_dir, 'relationfile_%s_%dclk_mg%d_ms%d.txt' % (
        cipher_name, T, recommended_mg, recommended_ms))
    with open(eqsfile_path, 'w') as relation_file:
        relation_file.write(eqs)

def biviuma_algebraic_equations(T=177):
    cipher_name = 'biviuma'
    # 177 clock cycles
    recommended_mg = 24
    recommended_ms = 85
    eqs = '#%s %d clock cycles\n' % (cipher_name, T)
    eqs += 'algebraic relations\n'
    for t in range(T):
        eqs += 'a_%d + a_%d + z_%d + b_%d*b_%d\n' % (t + 93, t + 24, t, t + 1, t + 2)
        eqs += 'b_%d + b_%d + a_%d + a_%d + a_%d*a_%d\n' % (t + 84, t + 6, t + 27, t, t + 1, t + 2)
        eqs += 'b_%d + b_%d + z_%d\n' % (t, t + 15, t)
    eqs += 'known\n' + '\n'.join(['z_%d' % i for i in range(T)]) + '\nend'
    eqsfile_path = os.path.join(output_dir, 'relationfile_%s_%dclk_mg%d_ms%d.txt' % (
        cipher_name, T, recommended_mg, recommended_ms))
    with open(eqsfile_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    biviuma(T=177)
    # biviuma_algebraic_equations(T=177)

if __name__ == '__main__':
    main()
