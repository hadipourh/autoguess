'''
Created on Aug 24, 2020

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com
'''

from random import random
from graphviz import Digraph
import dot2tex
import os

def draw_graph(vertices, edges, known_variables, guessed_vars, output_dir, tikz, dglayout):
    """
    Using the Graphviz package this function constructs a 
    directed graph representing the determination flow
    """

    vertices = list(set(vertices))
    edges = list(set(edges))
    directed_graph = Digraph(name='DataFlow', node_attr={'shape': 'circle'})
    layout = 'dot' # circo dot fdp neato nop nop1 nop2 osage patchwork sfdp twopi
    directed_graph.graph_attr["layout"] = dglayout
    directed_graph.graph_attr["ranksep"] = '0.75 equally'
    directed_graph.graph_attr["rankdir"] = 'TB' # 'LR, BT, TB'
    directed_graph.graph_attr["overlap"] = 'scale'
    directed_graph.graph_attr["orientation"] = '[lL]*'
    directed_graph.graph_attr["pagedir"] = 'BL'
    directed_graph.graph_attr["ratio"] = 'compress'
    #directed_graph.graph_attr["model"] = "circuit"
    # directed_graph.graph_attr["len"] = '2'
    ##############################################
    # directed_graph.node_attr["fixedsize"] = 'true'
    # directed_graph.node_attr["width"] = '0.75'
    # directed_graph.node_attr["height"] = '0.75'
    ##############################################
    digraph_tikz = Digraph(name='DataFlowTikz', node_attr={'shape' : 'circle'},\
        graph_attr={'layout' : layout, 
                    'overlap' : 'scale', 
                    'orientation' : '[lL]*]',
                    'rankdir' : 'TB'})
    for edge in edges:
        if edge[2] >= 2:                           
            directed_graph.edge(edge[0], edge[1], style='dashed')            
        else:  
            directed_graph.edge(edge[0], edge[1])
        node1 = edge[0]
        node2 = edge[1]
        if "_" in node1:
            node1_temp = node1.split("_")
            node1_name = "{%s_{%s}}" % (node1_temp[0], ",".join(node1_temp[1:]))
            node2_temp = node2.split("_")
            node2_name = "{%s_{%s}}" % (node2_temp[0], ",".join(node2_temp[1:]))
        else:
            node1_name = node1
            node2_name = node2
        if edge[2] >= 2:
            #digraph_tikz.edge(node1_name, node2_name, style='dashed')
            pass
        else:
            digraph_tikz.edge(node1_name, node2_name)
    for vertex in vertices:
        if "_" in vertex:
            vertex_name = vertex.split("_")
            vertex_name = "{%s_{%s}}" % (vertex_name[0], ",".join(vertex_name[1:]))
        else:
            vertex_name = vertex
        if vertex in known_variables:
            directed_graph.node(vertex, color="blue", style="filled", shape="doublecircle")
            digraph_tikz.node(vertex_name, color="blue", style="filled", shape="doublecircle", texmode="math")
        elif vertex in guessed_vars:
            directed_graph.node(vertex, color="red", style="filled", \
                shape="doublecircle", texmode="math", root='true')
            digraph_tikz.node(vertex_name, color="red", style="filled", \
                shape="doublecircle", texmode="math", root='true')
        else:
            directed_graph.node(vertex, color="green", style="filled", shape="circle")
            digraph_tikz.node(vertex_name, color="green", style="filled", shape="circle", texmode="math")
    # directed_graph.node_attr["fontsize"] = "5"
    # directed_graph.node_attr["fixedsize"] = "true"
    graph_file_name = output_dir + "_graph"
    directed_graph.render(graph_file_name)
    # Generate the Tikz code of derived Digraph
    if tikz == 1:
        print("Generating the tikz code ...")
        texcode = dot2tex.dot2tex(digraph_tikz.source, format='tikz', crop=True)
        # with open(os.path.join("graphtikz", graph_file_name + ".tex"), "w") as tikzfile:
        with open(os.path.join(graph_file_name + ".tex"), "w") as tikzfile:
            tikzfile.write(texcode)
