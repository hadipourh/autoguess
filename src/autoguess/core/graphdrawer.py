'''
Created on Aug 24, 2020

@author: Hosein Hadipour
@contact: hsn.hadipour@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

In case you use this tool please include the above copyright informations (name, contact, license)
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
    directed_graph.graph_attr.update({
        "layout": dglayout,
        "ranksep": '0.75 equally',
        "rankdir": 'TB',
        "overlap": 'scale',
        "orientation": '[lL]*',
        "pagedir": 'BL',
        "ratio": 'compress'
    })

    digraph_tikz = Digraph(name='DataFlowTikz', node_attr={'shape': 'circle'}, graph_attr={
        'layout': 'dot',
        'overlap': 'scale',
        'orientation': '[lL]*]',
        'rankdir': 'TB'
    })

    for edge in edges:
        style = 'dashed' if edge[2] >= 2 else None
        directed_graph.edge(edge[0], edge[1], style=style)
        
        node1_name = "{%s_{%s}}" % (edge[0].split("_")[0], ",".join(edge[0].split("_")[1:])) if "_" in edge[0] else edge[0]
        node2_name = "{%s_{%s}}" % (edge[1].split("_")[0], ",".join(edge[1].split("_")[1:])) if "_" in edge[1] else edge[1]
        
        if edge[2] < 2:
            digraph_tikz.edge(node1_name, node2_name)

    for vertex in vertices:
        vertex_name = "{%s_{%s}}" % (vertex.split("_")[0], ",".join(vertex.split("_")[1:])) if "_" in vertex else vertex
        color, shape = ("blue", "doublecircle") if vertex in known_variables else ("red", "doublecircle") if vertex in guessed_vars else ("green", "circle")
        directed_graph.node(vertex, color=color, style="filled", shape=shape)
        digraph_tikz.node(vertex_name, color=color, style="filled", shape=shape, texmode="math")

    graph_file_name = output_dir + "_graph"
    try:
        directed_graph.render(graph_file_name)
    except Exception as exc:
        # Save the .gv source even if the dot binary is missing
        src_path = graph_file_name + ".gv"
        directed_graph.save(src_path)
        print(f"WARNING: Could not render graph ({exc}).")
        print(f"  Graphviz source saved to: {src_path}")
        print(f"  To enable rendering, install the system packages:")
        print(f"    Debian/Ubuntu: apt install graphviz libpangocairo-1.0-0")
        print(f"    macOS:         brew install graphviz")

    if tikz == 1:
        print("Generating the tikz code ...")
        texcode = dot2tex.dot2tex(digraph_tikz.source, format='tikz', crop=True)
        with open(os.path.join(graph_file_name + ".tex"), "w") as tikzfile:
            tikzfile.write(texcode)
