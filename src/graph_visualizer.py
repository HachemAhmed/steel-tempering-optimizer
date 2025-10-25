import networkx as nx
import matplotlib.pyplot as plt

def plot_filtered_graph(graph, path, cost, optimize_by, output_image_filename):
    """
    Desenha e salva uma visualização de um grafo filtrado, destacando o caminho encontrado.
    ... (o código desta função permanece o mesmo)...
    """
    if graph is None or not path or isinstance(path, str):
        print(f"Não é possível gerar o gráfico para '{output_image_filename}': caminho não encontrado ou grafo nulo.")
        return

    print(f"Gerando visualização do grafo em {output_image_filename}...")
    
    
    plt.figure(figsize=(20, 12))
    
    
    for node, data in graph.nodes(data=True):
        if node == 'SOURCE': data['layer'] = 0
        elif node == 'SINK': data['layer'] = 5
        

    
    try:
        pos = nx.multipartite_layout(graph, subset_key='layer')
    except Exception as e:
        print(f"Aviso: Não foi possível usar o layout em camadas. Usando layout 'spring'. Erro: {e}")
        pos = nx.spring_layout(graph)
    
    
    nx.draw_networkx_nodes(graph, pos, node_size=2000, node_color='lightblue', alpha=0.7)
    nx.draw_networkx_edges(graph, pos, edge_color='gray', alpha=0.5, arrows=True)
    nx.draw_networkx_labels(graph, pos, font_size=9, font_family='sans-serif')
    
    
    path_edges = list(zip(path, path[1:]))
    nx.draw_networkx_nodes(graph, pos, nodelist=path, node_color='red', node_size=2100)
    nx.draw_networkx_edges(graph, pos, edgelist=path_edges, edge_color='red', width=2, arrows=True)
    
    plt.title(f"Grafo Filtrado - Otimizado por: {optimize_by.upper()}\nCusto: {cost:.2f}", fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_image_filename)
    plt.close() 
    print(f"Gráfico salvo com sucesso em {output_image_filename}")




def plot_full_graph(graph, output_image_filename):
    """
    Desenha e salva uma visualização do grafo completo (não filtrado).
    
    :param graph: O objeto grafo (NetworkX DiGraph) a ser desenhado.
    :param output_image_filename: O caminho completo para salvar a imagem.
    """
    if graph is None:
        print("Grafo nulo, não é possível gerar gráfico.")
        return

    print(f"Gerando visualização do grafo COMPLETO em {output_image_filename}...")
    
    
    plt.figure(figsize=(25, 15)) 
    
    
    for node, data in graph.nodes(data=True):
        if node == 'SOURCE': data['layer'] = 0
        elif node == 'SINK': data['layer'] = 5
        

    
    try:
        pos = nx.multipartite_layout(graph, subset_key='layer')
    except Exception as e:
        print(f"Aviso: Não foi possível usar o layout em camadas. Usando layout 'spring'. Erro: {e}")
        pos = nx.spring_layout(graph, k=0.15) 
    
    
    nx.draw_networkx_nodes(graph, pos, node_size=500, node_color='lightblue', alpha=0.6)
    nx.draw_networkx_edges(graph, pos, edge_color='gray', alpha=0.2, arrows=False) 
    nx.draw_networkx_labels(graph, pos, font_size=7, font_family='sans-serif') 
    
    plt.title("Visualização do Grafo Completo (Todos os Dados - 72 Nós, 565 Arestas)", fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_image_filename)
    plt.close() 
    print(f"Grafo completo salvo com sucesso em {output_image_filename}")