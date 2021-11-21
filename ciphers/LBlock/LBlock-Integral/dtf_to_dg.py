# Created on Nov 27, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

def main():
    with open("output_twosides.txt", "r") as detfile:
        lns = detfile.readlines()
    output_buffer = ""
    vertices = []
    edges = []
    cnt = 0
    for ln in lns:
        if "===>" in ln:
            temp = ln.split(": ")[1][:-1]
            temp = temp.split(" ===> ")
            rhs = temp[1]
            vertices.append(rhs)
            if len(temp[0].split("_")) == 3:
                lhs = temp[0]
                vertices.append(lhs)
                edges.append((lhs, rhs))    
            else:
                lhs_temp = temp[0].split(", ")
                lhs = []
                for el in lhs_temp:
                    vertices.append(el)
                    edges.append((el, rhs))
            cnt += 1
    vertices = list(set(vertices))
    return vertices, edges        
    

    

        
    
if __name__ == '__main__':
    main()
