"""
Graph visualization module for process flow diagrams.
Generates comparison and full graph visualizations.
"""
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np


def _deterministic_layout(G):
    """
    Creates a 100% reproducible layout based on node values and layers.
    Ensures scientific consistency by sorting nodes deterministically.
    """
    pos = {}
    nodes_by_layer = defaultdict(list)
    
    for node, data in G.nodes(data=True):
        layer = data.get('layer', 0)
        nodes_by_layer[layer].append((node, data))
    
    for layer, nodes in nodes_by_layer.items():
        nodes.sort(key=lambda x: (x[1].get('sort_val', 0), str(x[0])), reverse=True)
        
        n = len(nodes)
        for i, (node, _) in enumerate(nodes):
            x = layer
            y = (n - 1) * 0.5 - i 
            pos[node] = np.array([x, y])
            
    return pos


def plot_filtered_graph_comparison(graph, paths, cost, optimize_by, output_image_filename):
    """
    Generates a visually rich and 100% deterministic comparison graph.
    Uses position based on physical values.
    """
    if graph is None or not paths:
        return

    print(f"Generating deterministic comparison graph: {output_image_filename}...")
    
    paths = sorted(paths, key=lambda p: str(p))

    G_display = nx.DiGraph()
    
    def get_label(node_name):
        if "|" in str(node_name): 
            return str(node_name).split("|")[0].strip()
        return str(node_name)

    sorted_edges = sorted(graph.edges(), key=lambda x: (str(x[0]), str(x[1])))

    for u, v in sorted_edges:
        u_lbl, v_lbl = get_label(u), get_label(v)
        
        u_data = graph.nodes[u]
        v_data = graph.nodes[v]
        
        u_val = u_data.get('value', 0) if isinstance(u_data.get('value'), (int, float)) else 0
        v_val = v_data.get('value', 0) if isinstance(v_data.get('value'), (int, float)) else 0

        G_display.add_node(u_lbl, layer=u_data.get('layer', 0), sort_val=u_val)
        G_display.add_node(v_lbl, layer=v_data.get('layer', 0), sort_val=v_val)
        G_display.add_edge(u_lbl, v_lbl)

    pos = _deterministic_layout(G_display)

    plt.figure(figsize=(24, 16))
    
    all_path_nodes = set()
    for p in paths:
        all_path_nodes.update([get_label(n) for n in p])
    
    other_nodes = sorted([n for n in G_display.nodes() if n not in all_path_nodes], key=str)
    
    nx.draw_networkx_nodes(G_display, pos, nodelist=other_nodes, node_size=1000, 
                          node_color='#f0f0f0', alpha=0.5)
    nx.draw_networkx_edges(G_display, pos, edge_color='#e0e0e0', arrows=False, alpha=0.4)
    nx.draw_networkx_labels(G_display, pos, labels={n:n for n in other_nodes}, 
                           font_color='#bbbbbb', font_size=8)

    colors = plt.cm.tab10(np.linspace(0, 1, len(paths)))
    legend_handles = []
    
    num_paths = len(paths)
    rad_step = 0.15 
    
    for i, path in enumerate(paths):
        if num_paths > 1:
            rad = (i - (num_paths - 1) / 2) * rad_step
            connection_style = f"arc3,rad={rad:.2f}"
        else:
            connection_style = "arc3,rad=0"
            
        color = colors[i]
        path_clean = [get_label(n) for n in path]
        edges = list(zip(path_clean, path_clean[1:]))
        
        nx.draw_networkx_edges(G_display, pos, edgelist=edges, edge_color=[color], 
                             width=2.5, connectionstyle=connection_style, 
                             arrowstyle='-|>', arrowsize=20)
        
        nx.draw_networkx_nodes(G_display, pos, nodelist=path_clean, node_size=2000, 
                              node_color='white', edgecolors=[color], linewidths=2.5)
        
        legend_handles.append(plt.Line2D([], [], color=color, linewidth=2.5, 
                                       label=f'Strategy #{i+1}'))

    nx.draw_networkx_labels(G_display, pos, labels={n:n for n in all_path_nodes}, 
                           font_size=11, font_weight='bold')

    unit = "s" if optimize_by == 'time' else "C" if optimize_by == 'temperature' else "(Score)"
    
    if optimize_by == 'time':
        main_title = "Time-Optimized Process Flow (Fastest Route)"
    elif optimize_by == 'temperature':
        main_title = "Temperature-Optimized Process Flow (Minimum Thermal Load)"
    elif optimize_by == 'balanced':
        main_title = "Balanced Optimization Process Flow"
    else:
        main_title = "Optimal Heat Treatment Process Flow"

    subtitle = f"Comparing {num_paths} Best Routes | Cost: {cost:.2f} {unit}"
    
    plt.title(f"{main_title}\n{subtitle}", fontsize=20, pad=20)
    plt.legend(handles=legend_handles, loc='upper center', bbox_to_anchor=(0.5, -0.05), 
              ncol=min(5, len(paths)), fontsize=12, frameon=True, shadow=True)
    
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_image_filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Comparison graph saved: {output_image_filename}")


def plot_full_graph(graph, output_image_filename):
    """Visualizes the complete master graph."""
    if graph is None: 
        return
    print(f"Generating FULL graph visualization: {output_image_filename}...")
    plt.figure(figsize=(25, 15)) 
    
    for node, data in graph.nodes(data=True):
        if node == 'SOURCE': 
            data['layer'] = 0
        elif node == 'SINK': 
            data['layer'] = 5
    
    try:
        for n, d in graph.nodes(data=True):
            if 'sort_val' not in d:
                d['sort_val'] = d.get('value', 0) if isinstance(d.get('value'), (int, float)) else 0
        pos = _deterministic_layout(graph)
    except:
        pos = nx.spring_layout(graph, seed=42)
        
    nx.draw_networkx_nodes(graph, pos, node_size=500, node_color='lightblue', alpha=0.6)
    nx.draw_networkx_edges(graph, pos, edge_color='gray', alpha=0.2, arrows=False) 
    plt.title("Full Master Graph Visualization", fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_image_filename)
    plt.close() 
    print(f"Full graph saved.")
