#!/usr/bin/env sage
# Created on Nov 27, 2020
# author: Hosein Hadipour
# contact: hsn.hadipour@gmail.com
import sys

def dtf_to_dg(file_name):
    with open(file_name, "r") as detfile:
        lns = detfile.readlines()
    output_buffer = ""
    known_variable_line_number = [i + 1 for i in range(len(lns)) if "are initially known" in lns[i]]
    known_variables = lns[known_variable_line_number[0]].split(", ")
    known_variables[-1] = known_variables[-1].replace("\n", "")
    initial_guessed_vars_line_number = [i + 1 for i in range(len(lns)) if "variable(s) are guessed:" in lns[i]]
    initial_guessed_vars = lns[initial_guessed_vars_line_number[0]].split(", ")
    initial_guessed_vars[-1] = initial_guessed_vars[-1].replace("\n", "")
    vertices = []
    edges = []
    cnt = 0
    for ln in lns:
        if "===>" in ln:
            temp = ln.split(": ")[1][:-1]
            temp = temp.split(" ===> ")
            rhs = temp[1]
            lhs_temp = temp[0].split(", ")
            lhs = []
            for el in lhs_temp:
                el = el.replace(" ", "")
                vertices.append(el)
                edges.append((el, rhs))
            cnt += 1
    # Symbolize vertices names
    vertices = list(map(var, vertices))
    initial_guessed_vars = list(map(var, initial_guessed_vars))
    vertices = list(set(vertices + initial_guessed_vars))
    # Symbolize edges' vertiices
    for i in range(len(edges)):
        edges[i] = (var(edges[i][0]), var(edges[i][1]))
    # Symbolize known_variables
    if known_variables != [""]:
        known_variables = list(map(var, known_variables))
    DG = DiGraph([vertices, edges])
    return vertices, edges, DG, known_variables

def main():
    if len(sys.argv) != 2:
        print("Usage: %s <n>" % sys.argv[0])
        sys.exit(1)
    else:
        V, E, DG, known_variables = dtf_to_dg(file_name=sys.argv[1])
        LC = DG.connected_components_subgraphs()
        size_of_source = lambda x: len(x.sources())
        MSG = DiGraph()
        cnt = 0
        for sg in LC:
            print("Sub-graph %d: %s, Root size: %d, Number of vertices: %d" % (cnt, sg, len(sg.sources()), len(sg.vertices())))
            cnt += 1
            new_size = size_of_source(sg)
            current_size = size_of_source(MSG)
            if current_size < new_size:
                MSG = sg
        guessed_vars = MSG.sources()
        for kv in known_variables:
            if kv in guessed_vars:
                guessed_vars.remove(kv)
        print("Number of guessed variables: %d" % len(guessed_vars))
        print("Guessed variables: ")
        print(guessed_vars)
        #MSG.plot()
    
if __name__ == '__main__':
    main()
