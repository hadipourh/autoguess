# Created on Nov 27, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com

def main():
    n = 4
    with open("output_twosides.txt", "r") as detfile:
        lns = detfile.readlines()
    output_buffer = ""
    cnt = 0
    for ln in lns:
        if "===>" in ln:
            temp = ln.split(": ")[1][:-1]
            temp = temp.split(" ===> ")
            if len(temp[0].split("_")) == 3:
                lhs = temp[0].split("_")
                lhs = lhs[0] + "_{" + lhs[1] + "," + lhs[2] + "}"
            else:
                lhs_temp = temp[0].split(", ")
                lhs = []
                for el in lhs_temp:
                    el = el.split("_")
                    el = el[0] + "_{" + el[1] + "," + el[2] + "}"
                    lhs += [el]
                lhs = ", ".join(lhs)
            rhs = temp[1].split("_")
            rhs = rhs[0] + "_{" + rhs[1] + "," + rhs[2] + "}"
            cnt += 1
            if cnt % n == 0:
                output_buffer += str(cnt) + " & " + "$" + lhs + " \\Rightarrow " + rhs + "$\\\\\n"
            else: 
                output_buffer += str(cnt) + " & " + "$" + lhs + " \\Rightarrow " + rhs + "$ & "
            # print(output_buffer)
    with open("output_latex.tex", "w") as latex_output:
        latex_output.write(output_buffer)

    

        
    
if __name__ == '__main__':
    main()
