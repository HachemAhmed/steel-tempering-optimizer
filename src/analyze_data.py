import pandas as pd
import numpy as np
import os

# --- Configuração de Caminhos ---
# (Assumindo que este script também está na pasta 'src')
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
datasets_dir = os.path.join(root_dir, 'datasets')
file_path = os.path.join(datasets_dir, 'preprocessed_steel_data.csv')

try:
    # Carregar o arquivo pré-processado
    df = pd.read_csv(file_path)

    print(f"Arquivo '{file_path}' carregado com sucesso.")
    print("Analisando as colunas-chave para discretização...\n")

    # Colunas que queremos agrupar para se tornarem nós
    columns_to_analyze = [
        'Final hardness (HRC) - post tempering',
        'Tempering temperature (ºC)',
        'Tempering time (s)'
    ]
    
    # 1. Obter estatísticas descritivas
    print("--- Estatísticas Descritivas ---")
    # Usamos percentis para entender melhor a distribuição
    percentiles = [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]
    print(df[columns_to_analyze].describe(percentiles=percentiles).to_string())

    # 2. Analisar 'Tempering time (s)' separadamente, pois pode ter valores muito variados
    print("\n\n--- Análise de Valores Únicos de 'Tempering time (s)' ---")
    unique_times = np.sort(df['Tempering time (s)'].unique())
    print(f"Valores de tempo únicos encontrados ({len(unique_times)}):")
    print(unique_times)
    
    # 3. Analisar 'Steel type' para ver a quantidade de nós
    print("\n\n--- Análise de 'Steel type' ---")
    unique_steels = df['Steel type'].unique()
    print(f"Total de tipos de aço únicos: {len(unique_steels)}")
    print("Exemplos:", unique_steels[:10])


except FileNotFoundError:
    print(f"Erro: O arquivo '{file_path}' não foi encontrado.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")