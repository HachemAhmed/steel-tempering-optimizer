"""
Visualization module for graph and solution space analysis.
Generates graph diagrams and heatmaps for optimization results.
"""
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.patheffects as path_effects
import numpy as np
import os
def _deterministic_layout(G):
    """
    Creates a 100% reproducible layout based on node values and layers.
    Replaces random/heuristic layouts to ensure scientific consistency.
    Y-axis logic: Sorts nodes by their physical 'value' (Temp/Time) or Name.
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

def plot_interactive_heatmap(graph, output_filename, highlight_points=None, auto_open=False):
    """
    Generates an interactive Plotly heatmap of Temperature vs Time with hardness as color.
    FIX: Legend positioned to avoid overlap with colorbar.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("WARNING: Plotly not installed. Falling back to matplotlib heatmap.")
        _plot_matplotlib_heatmap_fallback(graph, output_filename, highlight_points)
        return

    print(f"Generating interactive heatmap: {output_filename}...")
    
    # Dictionary to group data: key=(temp, time), value=list of {steel, hardness}
    points_data = defaultdict(list)
    
    # SAFE STRATEGY: Iterate over 'temp' nodes (Layer 3)
    for node, data in graph.nodes(data=True):
        if data.get('type') == 'temp':
            temp_val = data.get('value')
            
            try:
                # 1. Get Time (unique predecessor of Temp node)
                preds = list(graph.predecessors(node))
                if not preds: continue
                time_node = preds[0]
                time_val = graph.nodes[time_node].get('value')
                
                # 2. Get Steel (predecessor of Time node)
                steel_preds = list(graph.predecessors(time_node))
                if not steel_preds: continue
                steel_node = steel_preds[0]
                steel_name = graph.nodes[steel_node].get('steel_type', str(steel_node))
                
                # 3. Get Hardness (successor of Temp node)
                succs = list(graph.successors(node))
                if not succs: continue
                hard_node = succs[0]
                hard_val = graph.nodes[hard_node].get('value')
                
                if temp_val is not None and time_val is not None:
                    points_data[(temp_val, time_val)].append({
                        'steel': steel_name,
                        'hardness': hard_val
                    })
                    
            except Exception:
                continue

    if not points_data:
        print("WARNING: No valid data points found for heatmap (Graph might be empty).")
        return

    optimal_coords = set(highlight_points) if highlight_points else set()
    
    single_temps, single_times, single_hardnesses, single_hovers = [], [], [], []
    multi_temps, multi_times, multi_hardnesses, multi_hovers = [], [], [], []
    opt_temps, opt_times, opt_hardnesses, opt_hovers = [], [], [], []
    
    for (temp, time), items in points_data.items():
        avg_hardness = sum(item['hardness'] for item in items) / len(items)
        
        # Remove duplicates
        unique_steels = {}
        for item in items:
            unique_steels[item['steel']] = item['hardness']
            
        if len(unique_steels) == 1:
            item = items[0]
            hover_text = (
                f"Steel: {item['steel']}<br>"
                f"Temp: {temp}°C<br>"
                f"Time: {time}s<br>"
                f"Hardness: {item['hardness']:.1f} HRC"
            )
        else:
            sorted_steels = sorted(unique_steels.items())
            if len(sorted_steels) > 15:
                steels_list = "<br>".join([f"  • {s}: {h:.1f} HRC" for s, h in sorted_steels[:15]])
                steels_list += f"<br>  ... and {len(sorted_steels)-15} more"
            else:
                steels_list = "<br>".join([f"  • {s}: {h:.1f} HRC" for s, h in sorted_steels])
                
            hover_text = (
                f"<b>Multiple Steels ({len(unique_steels)})</b><br>"
                f"Temp: {temp}°C<br>"
                f"Time: {time}s<br>"
                f"Avg Hardness: {avg_hardness:.1f} HRC<br>"
                f"Steels:<br>{steels_list}"
            )
        
        if (temp, time) in optimal_coords:
            opt_temps.append(temp)
            opt_times.append(time)
            opt_hardnesses.append(avg_hardness)
            opt_hover_text = f"<b>⭐ OPTIMAL SOLUTION ⭐</b><br>{hover_text}"
            opt_hovers.append(opt_hover_text)
        elif len(unique_steels) > 1:
            multi_temps.append(temp)
            multi_times.append(time)
            multi_hardnesses.append(avg_hardness)
            multi_hovers.append(hover_text)
        else:
            single_temps.append(temp)
            single_times.append(time)
            single_hardnesses.append(avg_hardness)
            single_hovers.append(hover_text)
    
    all_hardnesses = single_hardnesses + multi_hardnesses + opt_hardnesses
    vmin, vmax = (min(all_hardnesses), max(all_hardnesses)) if all_hardnesses else (0, 100)
    
    fig = go.Figure()
    
    # 1. Single Steel Points
    if single_temps:
        fig.add_trace(go.Scatter(
            x=single_temps, y=single_times, mode='markers',
            marker=dict(size=12, symbol='circle', color=single_hardnesses, 
                       colorscale='RdYlBu_r', cmin=vmin, cmax=vmax,
                       showscale=True, 
                       colorbar=dict(
                           title="Hardness (HRC)",
                           x=1.02,  # Position colorbar to the right
                           xanchor='left'
                       )),
            text=single_hovers, hovertemplate='%{text}<extra></extra>', 
            name='Single Steel',
            showlegend=True
        ))
    
    # 2. Multi-Steel Points
    if multi_temps:
        show_scale = not single_temps
        fig.add_trace(go.Scatter(
            x=multi_temps, y=multi_times, mode='markers',
            marker=dict(size=14, symbol='square', color=multi_hardnesses, 
                       colorscale='RdYlBu_r', cmin=vmin, cmax=vmax,
                       showscale=show_scale, line=dict(width=1, color='white'),
                       colorbar=dict(
                           title="Hardness (HRC)",
                           x=1.02,
                           xanchor='left'
                       ) if show_scale else None),
            text=multi_hovers, hovertemplate='%{text}<extra></extra>', 
            name='Multiple Steels',
            showlegend=True
        ))
    
    # 3. Optimal Points
    if opt_temps:
        fig.add_trace(go.Scatter(
            x=opt_temps, y=opt_times, mode='markers',
            marker=dict(size=22, symbol='star', color=opt_hardnesses, 
                       colorscale='RdYlBu_r', cmin=vmin, cmax=vmax,
                       line=dict(width=2, color='black'),
                       showscale=False),
            text=opt_hovers, hovertemplate='%{text}<extra></extra>', 
            name='Optimal',
            showlegend=True
        ))
    
    fig.update_layout(
        title=dict(
            text="Steel Heat Treatment Solution Space: Temperature-Time Analysis with Hardness Response",
            x=0.5,
            xanchor='center',
            font=dict(size=16)
        ),
        xaxis_title="Temperature (°C)", 
        yaxis_title="Time (s)",
        template='plotly_white', 
        width=1200,
        height=800,
        hovermode='closest',
        font=dict(size=12),
        # Position legend horizontally below the plot
        legend=dict(
            orientation='h',
            x=0.5,
            y=-0.12,
            xanchor='center',
            yanchor='top',
            bgcolor='rgba(255, 255, 255, 0.95)',
            bordercolor='rgba(0, 0, 0, 0.3)',
            borderwidth=1.5
        ),
        # Add margins for colorbar and bottom legend
        margin=dict(r=120, b=80)
    )
    
    fig.write_html(output_filename, config={'displayModeBar': True})
    print(f"✓ Interactive heatmap saved: {output_filename}")
    if auto_open:
        import webbrowser
        import os
        webbrowser.open(f"file://{os.path.abspath(output_filename)}")


def _plot_matplotlib_heatmap_fallback(graph, output_filename, highlight_points):
    """Fallback to matplotlib if Plotly is not available."""
    print("Using matplotlib fallback (no interactive features)...")
    
    points_agg = defaultdict(list)
    
    for node, data in graph.nodes(data=True):
        if data.get('type') == 'temp':
            temp_val = data.get('value')
            preds = list(graph.predecessors(node))
            succs = list(graph.successors(node))
            
            if preds and succs:
                time_node = preds[0]
                time_val = graph.nodes[time_node].get('value')
                hardness_node = succs[0]
                hardness_val = graph.nodes[hardness_node].get('value')
                points_agg[(temp_val, time_val)].append(hardness_val)

    if not points_agg:
        return

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

    min_h, max_h = (min(all_hardnesses)-1, max(all_hardnesses)+1) if all_hardnesses else (0, 65)

    plt.figure(figsize=(10, 8))
    
    if single_x:
        sc = plt.scatter(single_x, single_y, c=single_c, cmap='RdYlBu_r', 
                         s=100, edgecolors='gray', alpha=0.9, 
                         vmin=min_h, vmax=max_h, label='Single Steel', zorder=1)
        plt.colorbar(sc).set_label('Final Hardness (HRC)', rotation=270, labelpad=15)
    
    if multi_x:
        plt.scatter(multi_x, multi_y, c='#A9A9A9', s=120, edgecolors='black', 
                   alpha=0.8, label='Multi-Steel', zorder=2)
        for x, y, count in zip(multi_x, multi_y, multi_count):
            text = plt.text(x, y, str(count), fontsize=7, fontweight='bold', 
                          color='white', ha='center', va='center', zorder=3)
            text.set_path_effects([path_effects.withStroke(linewidth=2, foreground='black')])

    if highlight_points:
        opt_x, opt_y = zip(*set(highlight_points)) if highlight_points else ([], [])
        plt.scatter(opt_x, opt_y, s=300, facecolors='none',
                   edgecolors='lime', linewidths=4, label='Optimal', zorder=10)

    plt.title('Solution Space Heatmap\n(Install Plotly for interactive version)', fontsize=14)
    plt.xlabel('Tempering Temperature (°C)', fontsize=12)
    plt.ylabel('Tempering Time (s)', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Static heatmap saved: {output_filename}")

def plot_static_heatmap(graph, output_filename, highlight_points=None, dpi=300):
    """
    Generates a high-resolution static PNG heatmap for scientific publications.
    
    This version prioritizes:
    - Publication-quality resolution (300 DPI default)
    - Clear axis labels and legends
    - Proper color normalization
    - Optimal highlighting of solution points
    
    Args:
        graph: NetworkX graph (pruned)
        output_filename: Path to save PNG
        highlight_points: List of (temp, time) tuples for optimal solutions
        dpi: Resolution (default 300 for publication quality)
    """
    print(f"Generating publication-quality static heatmap: {output_filename}...")
    
    # Dictionary to aggregate data: key=(temp, time), value=list of {steel, hardness}
    points_data = defaultdict(list)
    
    # Strategy: Iterate over 'temp' nodes (Layer 3)
    for node, data in graph.nodes(data=True):
        if data.get('type') == 'temp':
            temp_val = data.get('value')
            
            try:
                # Get Time (unique predecessor of Temp node)
                preds = list(graph.predecessors(node))
                if not preds: 
                    continue
                time_node = preds[0]
                time_val = graph.nodes[time_node].get('value')
                
                # Get Steel (predecessor of Time node)
                steel_preds = list(graph.predecessors(time_node))
                if not steel_preds: 
                    continue
                steel_node = steel_preds[0]
                steel_name = graph.nodes[steel_node].get('steel_type', str(steel_node))
                
                # Get Hardness (successor of Temp node)
                succs = list(graph.successors(node))
                if not succs: 
                    continue
                hard_node = succs[0]
                hard_val = graph.nodes[hard_node].get('value')
                
                if temp_val is not None and time_val is not None:
                    points_data[(temp_val, time_val)].append({
                        'steel': steel_name,
                        'hardness': hard_val
                    })
                    
            except Exception:
                continue

    if not points_data:
        print("WARNING: No valid data points found for static heatmap.")
        return

    # Separate points by type
    optimal_coords = set(highlight_points) if highlight_points else set()
    
    single_x, single_y, single_c = [], [], []
    multi_x, multi_y, multi_c, multi_count = [], [], [], []
    opt_x, opt_y, opt_c = [], [], []
    
    for (temp, time), items in points_data.items():
        avg_hardness = sum(item['hardness'] for item in items) / len(items)
        unique_steels = {item['steel']: item['hardness'] for item in items}
        
        if (temp, time) in optimal_coords:
            opt_x.append(temp)
            opt_y.append(time)
            opt_c.append(avg_hardness)
        elif len(unique_steels) > 1:
            multi_x.append(temp)
            multi_y.append(time)
            multi_c.append(avg_hardness)
            multi_count.append(len(unique_steels))
        else:
            single_x.append(temp)
            single_y.append(time)
            single_c.append(avg_hardness)
    
    # Determine color scale range
    all_hardnesses = single_c + multi_c + opt_c
    if not all_hardnesses:
        print("WARNING: No hardness values to plot.")
        return
    
    vmin, vmax = min(all_hardnesses) - 1, max(all_hardnesses) + 1
    
    # Create figure with publication-quality settings
    fig, ax = plt.subplots(figsize=(12, 9))
    
    # 1. Plot single steel points
    if single_x:
        sc1 = ax.scatter(single_x, single_y, c=single_c, 
                        cmap='RdYlBu_r', s=150, marker='o',
                        edgecolors='gray', linewidths=0.5, alpha=0.85,
                        vmin=vmin, vmax=vmax, label='Single Steel', zorder=2)
    
    # 2. Plot multi-steel points (squares with count labels)
    if multi_x:
        sc2 = ax.scatter(multi_x, multi_y, c=multi_c, 
                        cmap='RdYlBu_r', s=180, marker='s',
                        edgecolors='black', linewidths=1.0, alpha=0.85,
                        vmin=vmin, vmax=vmax, label='Multiple Steels', zorder=3)
        
        # Add count labels to multi-steel points
        for x, y, count in zip(multi_x, multi_y, multi_count):
            text = ax.text(x, y, str(count), fontsize=9, fontweight='bold',
                          color='white', ha='center', va='center', zorder=4)
            text.set_path_effects([path_effects.withStroke(linewidth=2, foreground='black')])
    
    # 3. Plot optimal solution points (stars with borders)
    if opt_x:
        sc3 = ax.scatter(opt_x, opt_y, c=opt_c,
                  cmap='RdYlBu_r', s=400, marker='*',
                  edgecolors='black', linewidths=2.5, alpha=1.0,
                  vmin=vmin, vmax=vmax, label='Optimal Solution', zorder=5)
    
    # Add colorbar - use whichever scatter plot exists
    if single_x or multi_x or opt_x:
        if single_x:
            colorbar_source = sc1
        elif multi_x:
            colorbar_source = sc2
        else:
            colorbar_source = sc3
        
        cbar = plt.colorbar(colorbar_source, ax=ax, pad=0.02)
        cbar.set_label('Final Hardness (HRC)', rotation=270, labelpad=20, fontsize=12, fontweight='bold')
        cbar.ax.tick_params(labelsize=10)
    
    # Styling for publication
    ax.set_xlabel('Tempering Temperature (°C)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Tempering Time (s)', fontsize=14, fontweight='bold')
    ax.set_title('Steel Heat Treatment Solution Space', fontsize=16, fontweight='bold', pad=15)
    
    # Grid for readability
    ax.grid(True, linestyle='--', alpha=0.3, linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Legend with custom styling - positioned to avoid colorbar
    legend = ax.legend(loc='upper left', frameon=True, shadow=True, 
                      fontsize=11, markerscale=0.8)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_alpha(0.95)
    
    # Tick parameters
    ax.tick_params(axis='both', which='major', labelsize=11)
    
    # Tight layout to avoid label cutoff
    plt.tight_layout()
    
    # Save with high resolution
    plt.savefig(output_filename, dpi=dpi, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"✓ Static heatmap saved at {dpi} DPI: {output_filename}")