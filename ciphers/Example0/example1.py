# Created on Sep 2, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

import os

output_dir = os.path.curdir

def example():
    cipher_name = 'example1'
    eqs = '#Example 1\n'
    eqs += 'connection relations\n'
    eqs += 'p2 => p1\n'
    eqs += 'p3, p4 => p1\n'
    eqs += 'p1, p3 => p2\n'
    eqs += 'p1, p4 => p3\n'
    eqs += 'p1, p2 => p4\n'
    eqs += 'end'
    eqsfile_path = os.path.join(output_dir, 'relationfile_%s.txt' % (cipher_name))
    with open(eqsfile_path, 'w') as relation_file:
        relation_file.write(eqs)

def main():
    example()

if __name__ == '__main__':
    main()