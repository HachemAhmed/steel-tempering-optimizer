import os
from steel_graph import SteelGraph
from graph_visualizer import plot_filtered_graph, plot_full_graph


if __name__ == "__main__":
    
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    data_path = os.path.join(root_dir, 'datasets', 'grouped_steel_data.csv')

    
    output_dir = os.path.join(root_dir, 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    
    output_path_1 = os.path.join(output_dir, 'consulta_1_graph.png')
    output_path_2 = os.path.join(output_dir, 'consulta_2_graph.png')
    output_path_main = os.path.join(output_dir, 'main_full_graph.png')


    
    print("Inicializando o sistema de grafos...")
    meu_grafo_de_acos = SteelGraph(data_path)

    if meu_grafo_de_acos.graph:
        
        
        print("\n--- GERANDO GRAFO COMPLETO (PODE DEMORAR UM POUCO) ---")
        plot_full_graph(meu_grafo_de_acos.graph, output_path_main)
        
        
        print("\n--- INICIANDO CONSULTA 1 ---")
        filtros_1 = {
            'hardness_group': '50-55 HRC',
            'C (%wt)': ('>', 0.6),
            'temp_group': '200-250 C'
        }
        
        
        caminho_1, custo_1, grafo_filtrado_1, detalhes_1 = meu_grafo_de_acos.find_best_process(
            filtros_1, 
            optimize_by='time'
        )
        
        print(f"Resultado Consulta 1:\n  Caminho (Nós): {caminho_1}\n  Custo (Tempo): {custo_1} s")
        
        
        if detalhes_1:
            print("  --- Detalhes do Aço Encontrado ---")
            for key, value in detalhes_1.items():
                if key != 'Composição Química':
                    print(f"    {key}: {value}")
            if 'Composição Química' in detalhes_1:
                print(f"    Composição Química: {detalhes_1['Composição Química']}")
        
        
        plot_filtered_graph(grafo_filtrado_1, caminho_1, custo_1, 'time', output_path_1)

        
        print("\n--- INICIANDO CONSULTA 2 ---")
        filtros_2 = {
            'hardness_group': '40-45 HRC',
            'C (%wt)': ('<', 0.5),
            'time_group': '3600.0 s'
        }
        
        
        caminho_2, custo_2, grafo_filtrado_2, detalhes_2 = meu_grafo_de_acos.find_best_process(
            filtros_2, 
            optimize_by='temperature'
        )
        
        print(f"Resultado Consulta 2:\n  Caminho (Nós): {caminho_2}\n  Custo (Temp): {custo_2} ºC")

        
        if detalhes_2:
            print("  --- Detalhes do Aço Encontrado ---")
            for key, value in detalhes_2.items():
                if key != 'Composição Química':
                    print(f"    {key}: {value}")
            if 'Composição Química' in detalhes_2:
                print(f"    Composição Química: {detalhes_2['Composição Química']}")

        
        plot_filtered_graph(grafo_filtrado_2, caminho_2, custo_2, 'temperature', output_path_2)