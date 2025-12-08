"""
Heatmap visualization module for solution space analysis.
Generates interactive (HTML) and static (PNG) heatmaps.
"""
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import os


def plot_interactive_heatmap(graph, output_filename, highlight_points=None, auto_open=False):
    """
    Generates an interactive Plotly heatmap of Temperature vs Time with hardness as color.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("WARNING: Plotly not installed. Falling back to matplotlib heatmap.")
        _plot_matplotlib_heatmap_fallback(graph, output_filename, highlight_points)
        return

    print(f"Generating interactive heatmap: {output_filename}...")
    
    points_data = defaultdict(list)
    
    for node, data in graph.nodes(data=True):
        if data.get('type') == 'temp':
            temp_val = data.get('value')
            
            try:
                preds = list(graph.predecessors(node))
                if not preds: continue
                time_node = preds[0]
                time_val = graph.nodes[time_node].get('value')
                
                steel_preds = list(graph.predecessors(time_node))
                if not steel_preds: continue
                steel_node = steel_preds[0]
                steel_name = graph.nodes[steel_node].get('steel_type', str(steel_node))
                
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
    
    import plotly.graph_objects as go
    fig = go.Figure()
    
    if single_temps:
        fig.add_trace(go.Scatter(
            x=single_temps, y=single_times, mode='markers',
            marker=dict(size=12, symbol='circle', color=single_hardnesses, 
                       colorscale='RdYlBu_r', cmin=vmin, cmax=vmax,
                       showscale=True, 
                       colorbar=dict(
                           title="Hardness (HRC)",
                           x=1.02,
                           xanchor='left'
                       )),
            text=single_hovers, hovertemplate='%{text}<extra></extra>', 
            name='Single Steel',
            showlegend=True
        ))
    
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
        legend=dict(
            orientation='h',
            x=0.5,
            y=-0.15,
            xanchor='center',
            yanchor='top',
            xref='paper',
            yref='paper',
            bgcolor='rgba(255, 255, 255, 0.95)',
            bordercolor='rgba(0, 0, 0, 0.3)',
            borderwidth=1.5
        ),
        margin=dict(r=120, b=100),
        autosize=False
    )
    
    fig.write_html(output_filename, config={'displayModeBar': True})
    print(f"✓ Interactive heatmap saved: {output_filename}")
    if auto_open:
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(output_filename)}")


def plot_static_heatmap(graph, output_filename, highlight_points=None, dpi=300):
    """
    Generates a high-resolution static PNG heatmap for scientific publications.
    
    Args:
        graph: NetworkX graph (pruned)
        output_filename: Path to save PNG
        highlight_points: List of (temp, time) tuples for optimal solutions
        dpi: Resolution (default 300 for publication quality)
    """
    print(f"Generating publication-quality static heatmap: {output_filename}...")
    
    points_data = defaultdict(list)
    
    for node, data in graph.nodes(data=True):
        if data.get('type') == 'temp':
            temp_val = data.get('value')
            
            try:
                preds = list(graph.predecessors(node))
                if not preds: 
                    continue
                time_node = preds[0]
                time_val = graph.nodes[time_node].get('value')
                
                steel_preds = list(graph.predecessors(time_node))
                if not steel_preds: 
                    continue
                steel_node = steel_preds[0]
                steel_name = graph.nodes[steel_node].get('steel_type', str(steel_node))
                
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
    
    all_hardnesses = single_c + multi_c + opt_c
    if not all_hardnesses:
        print("WARNING: No hardness values to plot.")
        return
    
    vmin, vmax = min(all_hardnesses) - 1, max(all_hardnesses) + 1
    
    fig, ax = plt.subplots(figsize=(12, 9))
    
    if single_x:
        sc1 = ax.scatter(single_x, single_y, c=single_c, 
                        cmap='RdYlBu_r', s=150, marker='o',
                        edgecolors='gray', linewidths=0.5, alpha=0.85,
                        vmin=vmin, vmax=vmax, label='Single Steel', zorder=2)
    
    if multi_x:
        sc2 = ax.scatter(multi_x, multi_y, c=multi_c, 
                        cmap='RdYlBu_r', s=180, marker='s',
                        edgecolors='black', linewidths=1.0, alpha=0.85,
                        vmin=vmin, vmax=vmax, label='Multiple Steels', zorder=3)
        
        for x, y, count in zip(multi_x, multi_y, multi_count):
            text = ax.text(x, y, str(count), fontsize=9, fontweight='bold',
                          color='white', ha='center', va='center', zorder=4)
            text.set_path_effects([path_effects.withStroke(linewidth=2, foreground='black')])
    
    if opt_x:
        sc3 = ax.scatter(opt_x, opt_y, c=opt_c,
                  cmap='RdYlBu_r', s=400, marker='*',
                  edgecolors='black', linewidths=2.5, alpha=1.0,
                  vmin=vmin, vmax=vmax, label='Optimal Solution', zorder=5)
    
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
    
    ax.set_xlabel('Tempering Temperature (°C)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Tempering Time (s)', fontsize=14, fontweight='bold')
    ax.set_title('Steel Heat Treatment Solution Space', fontsize=16, fontweight='bold', pad=15)
    
    ax.grid(True, linestyle='--', alpha=0.3, linewidth=0.5)
    ax.set_axisbelow(True)
    
    legend = ax.legend(loc='upper left', frameon=True, shadow=True, 
                      fontsize=11, markerscale=0.8)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_alpha(0.95)
    
    ax.tick_params(axis='both', which='major', labelsize=11)
    
    plt.tight_layout()
    
    plt.savefig(output_filename, dpi=dpi, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"✓ Static heatmap saved at {dpi} DPI: {output_filename}")


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
