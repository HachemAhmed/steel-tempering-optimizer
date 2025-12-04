"""
Visualization module for graph and solution space analysis.
Generates graph diagrams and heatmaps for optimization results.
"""
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.patheffects as path_effects

def plot_filtered_graph(graph, path, cost, optimize_by, output_image_filename):
    """
    Draws the filtered graph with the optimal path highlighted.
    
    Args:
        graph: Filtered NetworkX DiGraph
        path: List of nodes in the optimal path
        cost: Total cost of the path
        optimize_by: Optimization criterion used
        output_image_filename: Output file path
    """
    if graph is None or not path:
        return

    print(f"Generating graph visualization: {output_image_filename}...")
    
    G_display = nx.DiGraph()
    
    def get_label(node_name):
        """Extracts clean label from node name (removes ID suffixes)."""
        if "|" in node_name:
            return node_name.split("|")[0].strip()
        return str(node_name)

    # Build display graph with cleaned labels
    for u, v in graph.edges():
        u_label = get_label(u)
        v_label = get_label(v)
        u_layer = graph.nodes[u].get('layer', 0)
        v_layer = graph.nodes[v].get('layer', 0)
        
        G_display.add_node(u_label, layer=u_layer)
        G_display.add_node(v_label, layer=v_layer)
        G_display.add_edge(u_label, v_label)

    # Prepare path nodes for highlighting
    path_to_draw = path[0] if isinstance(path[0], list) else path
    path_display = [get_label(n) for n in path_to_draw]
    path_nodes_set = set(path_display)
    all_nodes = set(G_display.nodes())
    other_nodes = list(all_nodes - path_nodes_set)

    plt.figure(figsize=(22, 14)) 
    
    # Layout nodes by layer (multipartite)
    try: 
        pos = nx.multipartite_layout(G_display, subset_key='layer')
    except Exception: 
        pos = nx.spring_layout(G_display)
    
    # Draw non-path nodes and edges (muted colors)
    nx.draw_networkx_nodes(G_display, pos, nodelist=other_nodes, node_size=2000, 
                          node_color='lightblue', alpha=0.7)
    nx.draw_networkx_edges(G_display, pos, edge_color='gray', alpha=0.3, arrows=True)
    nx.draw_networkx_labels(G_display, pos, labels={n: n for n in other_nodes}, 
                           font_size=10, font_family='sans-serif', font_color='black')
    
    # Draw optimal path (highlighted in red)
    path_edges = list(zip(path_display, path_display[1:]))
    nx.draw_networkx_nodes(G_display, pos, nodelist=path_display, node_color='#ff4d4d', 
                          node_size=2500, edgecolors='black') 
    nx.draw_networkx_edges(G_display, pos, edgelist=path_edges, edge_color='red', 
                          width=3, arrows=True)
    nx.draw_networkx_labels(G_display, pos, labels={n: n for n in path_display}, 
                           font_size=14, font_weight='bold', font_family='sans-serif')
    
    # Add title with cost information
    unit = "s" if optimize_by == 'time' else "C" if optimize_by == 'temperature' else "(Score)"
    plt.title(f"Filtered Graph - Optimization: {optimize_by.upper()}\nCost: {cost:.2f} {unit}", 
             fontsize=18)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_image_filename)
    plt.close() 
    print(f"Graph saved: {output_image_filename}")

def plot_full_graph(graph, output_image_filename):
    """
    Visualizes the complete master graph (all possible processes).
    
    Args:
        graph: Full NetworkX DiGraph
        output_image_filename: Output file path
    """
    if graph is None: 
        return
        
    print(f"Generating FULL graph visualization: {output_image_filename}...")
    plt.figure(figsize=(25, 15)) 
    
    # Assign layers for SOURCE and SINK nodes
    for node, data in graph.nodes(data=True):
        if node == 'SOURCE': 
            data['layer'] = 0
        elif node == 'SINK': 
            data['layer'] = 5
            
    try: 
        pos = nx.multipartite_layout(graph, subset_key='layer')
    except Exception: 
        pos = nx.spring_layout(graph, k=0.15) 
        
    nx.draw_networkx_nodes(graph, pos, node_size=500, node_color='lightblue', alpha=0.6)
    nx.draw_networkx_edges(graph, pos, edge_color='gray', alpha=0.2, arrows=False) 
    plt.title("Full Master Graph Visualization", fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_image_filename)
    plt.close() 
    print(f"Full graph saved.")

def plot_hardness_heatmap(graph, output_image_filename, highlight_points=None):
    """
    Generates a heatmap of the solution space (temperature vs time vs hardness).
    Highlights optimal solution(s) with larger markers and black borders.
    
    Args:
        graph: Filtered NetworkX DiGraph
        output_image_filename: Output file path
        highlight_points: List of (temp, time) tuples to highlight as optimal
    """
    if graph is None or graph.number_of_nodes() == 0:
        print("Empty graph, skipping heatmap.")
        return

    # Aggregate data points by (temperature, time) coordinates
    points_agg = defaultdict(list)
    winner_data_map = {}  # Store hardness values for coloring

    for node, data in graph.nodes(data=True):
        if data.get('type') == 'temp':
            temp_val = data.get('value')
            predecessors = list(graph.predecessors(node))
            if not predecessors: 
                continue
                
            time_node = predecessors[0] 
            time_val = graph.nodes[time_node].get('value')
            successors = list(graph.successors(node))
            if not successors: 
                continue
                
            hardness_node = successors[0]
            hardness_val = graph.nodes[hardness_node].get('value')

            points_agg[(temp_val, time_val)].append(hardness_val)
            winner_data_map[(temp_val, time_val)] = hardness_val

    if not points_agg:
        print("Not enough data for heatmap.")
        return

    print(f"Generating Heatmap with {len(points_agg)} unique coordinates...")

    # Separate single-option and multi-option points
    single_x, single_y, single_c = [], [], []
    multi_x, multi_y, multi_count = [], [], []
    all_hardnesses = []

    for (temp, time), h_list in points_agg.items():
        all_hardnesses.extend(h_list)
        if len(h_list) == 1:
            single_x.append(temp)
            single_y.append(time)
            single_c.append(h_list[0])
        else:
            multi_x.append(temp)
            multi_y.append(time)
            multi_count.append(len(h_list))

    # Determine color scale range
    if all_hardnesses:
        min_h = min(all_hardnesses)
        max_h = max(all_hardnesses)
        if min_h == max_h: 
            min_h -= 1
            max_h += 1
    else:
        min_h, max_h = 0, 65

    plt.figure(figsize=(10, 8))
    
    # Plot single-option points (colored by hardness)
    if single_x:
        sc = plt.scatter(single_x, single_y, c=single_c, cmap='RdYlBu_r', 
                         s=100, edgecolors='gray', alpha=0.9, 
                         vmin=min_h, vmax=max_h, label='Single Option', zorder=1)
        cbar = plt.colorbar(sc)
        cbar.set_label('Final Hardness (HRC)', rotation=270, labelpad=15)
    
    # Plot multi-option points (grey with count label)
    if multi_x:
        plt.scatter(multi_x, multi_y, c='#A9A9A9', s=120, edgecolors='black', 
                   alpha=0.8, label='Multiple Options', zorder=2)
        for x, y, count in zip(multi_x, multi_y, multi_count):
            text = plt.text(x, y, str(count), fontsize=7, fontweight='bold', 
                          color='white', ha='center', va='center', zorder=3)
            text.set_path_effects([path_effects.withStroke(linewidth=2, foreground='black')])

    # Highlight optimal solutions (larger markers with thick black borders)
    if highlight_points:
        unique_points = set(highlight_points)
        
        winner_single_x, winner_single_y, winner_single_c = [], [], []
        winner_multi_x, winner_multi_y = [], []
        
        for pt in unique_points:
            temp, time = pt
            if len(points_agg[(temp, time)]) > 1:
                winner_multi_x.append(temp)
                winner_multi_y.append(time)
            else:
                winner_single_x.append(temp)
                winner_single_y.append(time)
                winner_single_c.append(winner_data_map.get((temp, time), min_h))

        # Optimal single-option points (colored, larger, thick border)
        if winner_single_x:
            plt.scatter(winner_single_x, winner_single_y, c=winner_single_c, cmap='RdYlBu_r',
                        s=200, edgecolors='black', linewidths=3, alpha=1.0,
                        vmin=min_h, vmax=max_h, label='Optimal Solution', zorder=10)

        # Optimal multi-option points (grey, larger, thick border)
        if winner_multi_x:
            plt.scatter(winner_multi_x, winner_multi_y, c='#A9A9A9',
                        s=200, edgecolors='black', linewidths=3, alpha=1.0,
                        label='Optimal Solution (Multi)', zorder=10)
            
            # Redraw count labels on top of highlighted markers
            for x, y in zip(winner_multi_x, winner_multi_y):
                count = len(points_agg[(x, y)])
                text = plt.text(x, y, str(count), fontsize=8, fontweight='bold', 
                              color='white', ha='center', va='center', zorder=11)
                text.set_path_effects([path_effects.withStroke(linewidth=2, foreground='black')])

    plt.title('Solution Space: Valid Processes vs. Optimal Solution(s)', fontsize=14)
    plt.xlabel('Tempering Temperature (C)', fontsize=12)
    plt.ylabel('Tempering Time (s)', fontsize=12)
    
    # Create legend with unique labels
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    lgnd = plt.legend(by_label.values(), by_label.keys(), loc='upper center', 
                     bbox_to_anchor=(0.5, -0.15), ncol=3, borderaxespad=0.)
    
    # Adjust legend marker sizes for visibility
    for handle in lgnd.legend_handles:
        try: 
            handle.set_sizes([60.0]) 
        except AttributeError:
            try: 
                handle.set_markersize(10)
            except AttributeError: 
                pass
        try: 
            handle.set_linewidth(1.5)
        except AttributeError: 
            pass

    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout() 
    plt.savefig(output_image_filename, bbox_inches='tight') 
    plt.close()
    print(f"Heatmap saved: {output_image_filename}")