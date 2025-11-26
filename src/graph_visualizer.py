import networkx as nx
import matplotlib.pyplot as plt
import numpy as np 
def plot_filtered_graph(graph, path, cost, optimize_by, output_image_filename):
    if graph is None or not path or isinstance(path, str):
        return

    print(f"Gerando visualização do grafo em {output_image_filename}...")
    
    G_display = nx.DiGraph()
    
    def get_label(node_name):
        if "|" in node_name:
            return node_name.split("|")[0].strip()
        return node_name

    for u, v in graph.edges():
        u_label = get_label(u)
        v_label = get_label(v)
        u_layer = graph.nodes[u].get('layer', 0)
        v_layer = graph.nodes[v].get('layer', 0)
        
        G_display.add_node(u_label, layer=u_layer)
        G_display.add_node(v_label, layer=v_layer)
        G_display.add_edge(u_label, v_label)

    path_display = [get_label(n) for n in path]
    path_nodes_set = set(path_display)
    all_nodes = set(G_display.nodes())
    other_nodes = list(all_nodes - path_nodes_set)

    plt.figure(figsize=(22, 14)) 
    
    try:
        pos = nx.multipartite_layout(G_display, subset_key='layer')
    except Exception:
        pos = nx.spring_layout(G_display)
    
    nx.draw_networkx_nodes(G_display, pos, nodelist=other_nodes, node_size=2000, node_color='lightblue', alpha=0.7)
    nx.draw_networkx_edges(G_display, pos, edge_color='gray', alpha=0.3, arrows=True)
    nx.draw_networkx_labels(G_display, pos, labels={n: n for n in other_nodes}, font_size=10, font_family='sans-serif', font_color='black')
    
    path_edges = list(zip(path_display, path_display[1:]))
    
    nx.draw_networkx_nodes(G_display, pos, nodelist=path_display, node_color='#ff4d4d', node_size=2500, edgecolors='black') 
    nx.draw_networkx_edges(G_display, pos, edgelist=path_edges, edge_color='red', width=3, arrows=True)
    
    nx.draw_networkx_labels(G_display, pos, labels={n: n for n in path_display}, font_size=14, font_weight='bold', font_family='sans-serif')
    
    unit = "s" if optimize_by == 'time' else "ºC"
    
    plt.title(f"Grafo Filtrado - Otimizado por: {optimize_by.upper()}\nCusto: {cost:.2f} {unit}", fontsize=18)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_image_filename)
    plt.close() 
    print(f"Gráfico salvo com sucesso em {output_image_filename}")

def plot_full_graph(graph, output_image_filename):
    if graph is None: return
    print(f"Gerando visualização do grafo COMPLETO em {output_image_filename}...")
    plt.figure(figsize=(25, 15)) 
    for node, data in graph.nodes(data=True):
        if node == 'SOURCE': data['layer'] = 0
        elif node == 'SINK': data['layer'] = 5
    try:
        pos = nx.multipartite_layout(graph, subset_key='layer')
    except Exception:
        pos = nx.spring_layout(graph, k=0.15) 
    nx.draw_networkx_nodes(graph, pos, node_size=500, node_color='lightblue', alpha=0.6)
    nx.draw_networkx_edges(graph, pos, edge_color='gray', alpha=0.2, arrows=False) 
    plt.title("Visualização do Grafo Completo", fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_image_filename)
    plt.close() 
    print(f"Grafo completo salvo com sucesso em {output_image_filename}")

def plot_hardness_heatmap(graph, output_image_filename, highlight_point=None, winner_hardness=None):
    
    if graph is None or graph.number_of_nodes() == 0:
        print("Grafo vazio, pulando mapa de calor.")
        return

    temperatures = []
    times = []
    hardnesses = []

    for node, data in graph.nodes(data=True):
        if data.get('type') == 'temp':
            temp_val = data.get('value')
            predecessors = list(graph.predecessors(node))
            if not predecessors: continue
            time_node = predecessors[0] 
            time_val = graph.nodes[time_node].get('value')
            successors = list(graph.successors(node))
            if not successors: continue
            hardness_node = successors[0]
            hardness_val = graph.nodes[hardness_node].get('value')

            temperatures.append(temp_val)
            times.append(time_val)
            hardnesses.append(hardness_val)

    if not temperatures:
        print("Não há dados suficientes para gerar o mapa de calor.")
        return

    print(f"Gerando Mapa de Calor com {len(temperatures)} pontos em {output_image_filename}...")

    min_h = min(hardnesses)
    max_h = max(hardnesses)
    if min_h == max_h:
        min_h -= 1
        max_h += 1

    plt.figure(figsize=(10, 8))

    sc = plt.scatter(temperatures, times, c=hardnesses, cmap='RdYlBu_r', 
                     s=100, edgecolors='gray', alpha=1.0, 
                     vmin=min_h, vmax=max_h, label='Opções Válidas')
    
    cbar = plt.colorbar(sc)
    cbar.set_label('Dureza Final (HRC)', rotation=270, labelpad=15)

    # 2. DESTAQUE DO VENCEDOR (Redesenhar no topo)
    if highlight_point:
        best_temp, best_time = highlight_point

        if winner_hardness is not None:
            plt.scatter([best_temp], [best_time], c=[winner_hardness], cmap='RdYlBu_r',
                        s=100, edgecolors='black', alpha=1.0,
                        vmin=min_h, vmax=max_h, zorder=5) 

        plt.plot(best_temp, best_time, marker='o', markersize=25, markeredgecolor='black', markerfacecolor='none', markeredgewidth=3, linestyle='None', label='Solução Ótima', zorder=10)

    plt.title('Espaço de Solução: Processos Válidos vs. Solução Ótima', fontsize=14)
    plt.xlabel('Temperatura de Revenimento (ºC)', fontsize=12)
    plt.ylabel('Tempo de Revenimento (s)', fontsize=12)
    
    lgnd = plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, borderaxespad=0.)
    
    for handle in lgnd.legend_handles:
        try: handle.set_sizes([60.0]) 
        except AttributeError:
            try: handle.set_markersize(10)
            except AttributeError: pass
        try: handle.set_linewidth(1.5)
        except AttributeError: pass

    plt.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout() 
    plt.savefig(output_image_filename, bbox_inches='tight') 
    plt.close()
    print(f"Mapa de calor salvo em {output_image_filename}")