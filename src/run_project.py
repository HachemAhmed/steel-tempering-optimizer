import os
import json
import glob
from steel_graph import SteelGraph
from graph_visualizer import plot_filtered_graph, plot_full_graph

# (NOVO) Importar os scripts da pipeline
import preprocess 
import group_data

# --- Ponto de Execução Principal ---
if __name__ == "__main__":
    
    # --- 1. Configurar Caminhos ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    
    # (NOVO) Definir todos os caminhos de dados
    datasets_dir = os.path.join(root_dir, 'datasets')
    original_data_path = os.path.join(datasets_dir, 'Tempering data for carbon and low alloy steels - Raiipa(in).csv')
    preprocessed_data_path = os.path.join(datasets_dir, 'preprocessed_steel_data.csv')
    grouped_data_path = os.path.join(datasets_dir, 'grouped_steel_data.csv') # Este é o arquivo final
    
    queries_config_path = os.path.join(root_dir, 'consultas.json')
    output_dir = os.path.join(root_dir, 'outputs')
    os.makedirs(output_dir, exist_ok=True)

    # --- (NOVO) VERIFICAR E EXECUTAR PIPELINE DE DADOS ---
    
    print("\n--- Verificando arquivos de dados... ---")
    if not os.path.exists(grouped_data_path):
        print(f"Arquivo '{grouped_data_path}' não encontrado. Iniciando pipeline de dados...")
        
        # 1. Verificar e rodar 'preprocess.py'
        if not os.path.exists(preprocessed_data_path):
            print(f"Arquivo '{preprocessed_data_path}' não encontrado.")
            if not os.path.exists(original_data_path):
                print(f"ERRO CRÍTICO: Arquivo de dados original '{original_data_path}' não encontrado.")
                print("Por favor, adicione o CSV original na pasta 'datasets' e tente novamente.")
                exit()
            
            # Rodar 'preprocess.py'
            success = preprocess.main()
            if not success:
                print("ERRO: Falha ao executar o pré-processamento. Encerrando.")
                exit()
        
        # 2. Rodar 'group_data.py'
        success = group_data.main()
        if not success:
            print("ERRO: Falha ao executar o agrupamento de dados. Encerrando.")
            exit()
            
        print("Pipeline de dados concluída com sucesso.")
    else:
        print(f"Arquivo de dados '{grouped_data_path}' encontrado. Pipeline de dados não necessária.")
    
    # --- 2. Limpar Diretório de Saídas ---
    print(f"\n--- Limpando diretório de saídas: {output_dir} ---")
    
    files_to_delete = glob.glob(os.path.join(output_dir, "*.png"))
    files_to_delete.extend(glob.glob(os.path.join(output_dir, "*.jpg")))

    if not files_to_delete:
        print("Diretório já está limpo.")
    else:
        deleted_count = 0
        for f_path in files_to_delete:
            try:
                os.remove(f_path)
                deleted_count += 1
            except OSError as e:
                print(f"ERRO: Não foi possível apagar o arquivo antigo {f_path}: {e}")
        print(f"Arquivos antigos removidos com sucesso ({deleted_count} arquivos).")
    
    # --- 3. Carregar Consultas do JSON ---
    try:
        with open(queries_config_path, 'r', encoding='utf-8') as f:
            consultas = json.load(f)
        print(f"\nArquivo de configuração '{queries_config_path}' carregado com {len(consultas)} consultas.")
    except FileNotFoundError:
        print(f"ERRO: Arquivo de configuração '{queries_config_path}' não encontrado.")
        exit()
    except json.JSONDecodeError:
        print(f"ERRO: O arquivo '{queries_config_path}' contém um JSON inválido.")
        exit()
    except Exception as e:
        print(f"ERRO ao ler o arquivo de configuração: {e}")
        exit()

    # --- 4. Inicializar o Grafo ---
    print("\nInicializando o sistema de grafos...")
    meu_grafo_de_acos = SteelGraph(grouped_data_path) 

    if not meu_grafo_de_acos.graph:
        print("ERRO: Falha ao carregar o grafo principal. Encerrando.")
        exit()
        
    # --- 5. Gerar Grafo Completo ---
    print("\n--- GERANDO GRAFO COMPLETO (PODE DEMORAR UM POUCO) ---")
    output_path_main = os.path.join(output_dir, 'main_full_graph.png')
    plot_full_graph(meu_grafo_de_acos.graph, output_path_main)
    
    # --- 6. Executar Consultas do JSON em Loop ---
    
    for consulta in consultas:
        print(f"\n--- INICIANDO: {consulta.get('nome_consulta', 'CONSULTA SEM NOME')} ---")
        
        nome_consulta = consulta.get('nome_consulta', 'consulta_sem_nome') 
        filtros = consulta.get('filtros', {})
        otimizar_por = consulta.get('otimizar_por', 'time')
        
        imagem_saida = f"{nome_consulta}_graph.png"
        output_path_consulta = os.path.join(output_dir, imagem_saida)
        
        if not filtros:
            print("AVISO: Esta consulta não tem filtros. Pulando.")
            continue
            
        # Executar o processo
        caminho, custo, grafo_filtrado, detalhes = meu_grafo_de_acos.find_best_process(
            filtros, 
            optimize_by=otimizar_por
        )
        
        # Imprimir resultados
        if isinstance(caminho, str):
            print(f"RESULTADO: {caminho}")
        else:
            print(f"  Caminho (Nós): {caminho}")
            print(f"  Custo ({'Tempo (s)' if otimizar_por == 'time' else 'Temp (C)'}): {custo}")
            
            if detalhes:
                print("  --- Detalhes do Aço Encontrado ---")
                for key, value in detalhes.items():
                    if key != 'Composição Química':
                        print(f"    {key}: {value}")
                if 'Composição Química' in detalhes:
                    print(f"    Composição Química: {detalhes['Composição Química']}")
            
            # Gerar gráfico
            plot_filtered_graph(grafo_filtrado, caminho, custo, otimizar_por, output_path_consulta)
            
    print("\n--- Processamento de consultas concluído. ---")