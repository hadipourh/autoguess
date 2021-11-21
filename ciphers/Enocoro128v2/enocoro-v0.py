# Created on Sep 2, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

def enocoro(T=16, plan=1):
    cipher_name = 'enocoro'
    # T = 16
    recommended_mg = 18
    recommended_ms = 22
    # With the above setting model should be solved in less than 3 seconds on:
    # Architecture:                    x86_64
    # CPU op-mode(s):                  32-bit, 64-bit
    # Byte Order:                      Little Endian
    # Address sizes:                   39 bits physical, 48 bits virtual
    # CPU(s):                          12
    # On-line CPU(s) list:             0-11
    # Thread(s) per core:              2
    # Core(s) per socket:              6
    # Socket(s):                       1
    # NUMA node(s):                    1
    # Vendor ID:                       GenuineIntel
    # CPU family:                      6
    # Model:                           158
    # Model name:                      Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz
    # Stepping:                        10
    # CPU MHz:                         900.256
    # CPU max MHz:                     4500.0000
    # CPU min MHz:                     800.0000
    # BogoMIPS:                        5199.98
    # Virtualization:                  VT-x
    # L1d cache:                       192 KiB
    # L1i cache:                       192 KiB
    # L2 cache:                        1.5 MiB
    # L3 cache:                        12 MiB
    # NUMA node0 CPU(s):               0-11

    # T = 18
    # recommended_mg = 18
    # recommended_ms = 18
    eqs = '#%s %d clock cycles\n' % (cipher_name, T)
    eqs += 'connection relations\n'
    if plan == 0:
        for t in range(T):
            eqs += 'b_%d, a_%d, e_%d\n' % (t + 3, t, t)
            eqs += 'c_%d, b_%d, c_%d\n' % (t + 5, t, t + 1)
            eqs += 'd_%d, c_%d, d_%d\n' % (t + 9, t, t + 1)
            eqs += 'e_%d, d_%d, e_%d\n' % (t + 15, t, t + 3)
            eqs += 'f_%d, a_%d, b_%d\n' % (t, t, t)
            eqs += 'g_%d, a_%d, d_%d\n' % (t, t + 1, t)
            eqs += 'g_%d, f_%d, e_%d\n' % (t, t, t + 2)
            eqs += 'g_%d, f_%d, c_%d\n' % (t, t, t)
            eqs += 'g_%d, e_%d, c_%d\n' % (t, t + 2, t)
            eqs += 'f_%d, e_%d, c_%d\n' % (t, t + 2, t)
    elif plan == 1:
        for t in range(T):
            # second plan:
            # replace f(t) with a(t), b(t)
            # replace g(t) with a(t + 1), d(t)
            eqs += 'b_%d, a_%d, e_%d\n' % (t + 3, t, t)
            eqs += 'c_%d, b_%d, c_%d\n' % (t + 5, t, t + 1)
            eqs += 'd_%d, c_%d, d_%d\n' % (t + 9, t, t + 1)
            eqs += 'e_%d, d_%d, e_%d\n' % (t + 15, t, t + 3)
            # a(t + 1), d(t), a(t), b(t), e(t + 2)
            eqs += 'a_%d, d_%d, a_%d, b_%d, e_%d\n' % (t + 1, t, t, t, t + 2)
            # a(t + 1), d(t), a(t), b(t), c(t)
            eqs += 'a_%d, d_%d, a_%d, b_%d, c_%d\n' % (t + 1, t, t, t, t)
            # a(t + 1), d(t), e(t + 2), c(t)
            eqs += 'a_%d, d_%d, e_%d, c_%d\n' % (t + 1, t, t + 2, t)
            # a(t), b(t), e(t + 2), c(t)
            eqs += 'a_%d, b_%d, e_%d, c_%d\n' % (t, t, t + 2, t)
    eqs += 'end'
    eqsfile_path = os.path.join(output_dir, 'relationfile_%s_%dclk_mg%d_ms%d.txt' % (cipher_name, T, recommended_mg, recommended_ms))
    with open(eqsfile_path, 'w') as relation_file:
        relation_file.write(eqs)
        
def main():
    enocoro(T=16, plan = 1)

if __name__ == '__main__':
    main()
