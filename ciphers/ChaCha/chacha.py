# Created on Sep 16, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

def qr_chacha(a, b, c, d, a_new, b_new, c_new, d_new, t, br):
    x = 'a_%d_%d' % (t, br)
    y = 'b_%d_%d' % (t, br)
    z = 'c_%d_%d' % (t, br)
    w = 'd_%d_%d' % (t, br)
    eqs = '%s, %s, %s\n' % (a, b, x)
    eqs += '%s, %s, %s\n' % (x, w, a_new)
    eqs += '%s, %s, %s\n' % (b, y, w)
    eqs += '%s, %s, %s\n' % (w, c_new, b_new)
    eqs += '%s, %s, %s\n' % (c, z, y)
    eqs += '%s, %s, %s\n' % (y, d_new, c_new)
    eqs += '%s, %s, %s\n' % (d, x, z)
    eqs += '%s, %s, %s\n' % (z, a_new, d_new)
    return eqs

def chacha(T=2):
    cipher_name = 'chacha'
    # 2 rounds:
    # recommended_mg = 4
    # recommended_ms = 10
    # 3 rounds:
    # recommended_mg = 4
    # recommended_ms = 15
    # 4 rounds:
    # recommended_mg = 6
    # recommended_ms = 25
    # 5 rounds:
    recommended_mg = 8
    recommended_ms = 25

    eqs = '#%s %d clock cycles\n' % (cipher_name, T)
    eqs += 'connection relations\n'
    for t in range(T):
        xin = ['X_%d_%d' % (t, i) for i in range(16)]
        xout = ['X_%d_%d' % (t + 1, i) for i in range(16)]
        if t%2 == 1:
            eqs += qr_chacha(xin[0], xin[4], xin[8], xin[12], xout[0], xout[4], xout[8], xout[12], t, 0)
            eqs += qr_chacha(xin[1], xin[5], xin[9], xin[13], xout[1], xout[5], xout[9], xout[13], t, 1)
            eqs += qr_chacha(xin[2], xin[6], xin[10], xin[14], xout[2], xout[6], xout[10], xout[14], t, 2)
            eqs += qr_chacha(xin[3], xin[7], xin[11], xin[15], xout[3], xout[7], xout[11], xout[15], t, 3)
        else:
            eqs += qr_chacha(xin[0], xin[5], xin[10], xin[15], xout[0], xout[5], xout[10], xout[15], t, 0)
            eqs += qr_chacha(xin[1], xin[6], xin[11], xin[12], xout[1], xout[6], xout[11], xout[12], t, 1)
            eqs += qr_chacha(xin[2], xin[7], xin[8], xin[13], xout[2], xout[7], xout[8], xout[13], t, 2)
            eqs += qr_chacha(xin[3], xin[4], xin[9], xin[14], xout[3], xout[4], xout[9], xout[14], t, 3)
    init_state = ['X_%d_%d' % (0, i) for i in range(16)]
    final_state = ['X_%d_%d' % (T, i) for i in range(16)]
    for i in range(16):
        eqs += '%s, %s\n' % (init_state[i], final_state[i])
    initially_known = ['X_%d_%d' % (0, i) for i in [0, 1, 2, 3, 12, 13, 14, 15]]
    eqs += 'known\n' + '\n'.join(initially_known) + '\nend'
    eqsfile_path = os.path.join(output_dir, 'relationfile_%s_%dclk_mg%d_ms%d.txt' % (
        cipher_name, T, recommended_mg, recommended_ms))
    with open(eqsfile_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    chacha(T=5)

if __name__ == '__main__':
    main()
