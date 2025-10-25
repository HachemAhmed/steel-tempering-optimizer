import pandas as pd
import numpy as np
import os

# --- Configuração de Caminhos ---
# (Assumindo que este script está na pasta 'src')
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)

# Caminho de entrada (processado)
processed_data_dir = os.path.join(root_dir, 'datasets')
input_file = os.path.join(processed_data_dir, 'preprocessed_steel_data.csv')

# Caminho de saída (agrupado)
output_file = os.path.join(processed_data_dir, 'grouped_steel_data.csv')

try:
    # 1. Carregar o arquivo pré-processado
    df = pd.read_csv(input_file)
    print(f"Arquivo '{input_file}' carregado com {len(df)} registros.")

    # 2. Agrupar 'Final hardness (HRC)' em faixas de 5 HRC
    # (Min=0.9, Max=64 -> vamos de 0 a 65)
    hardness_bins = list(range(0, 66, 5)) # [0, 5, 10, ..., 65]
    hardness_labels = [f'{i}-{i+5} HRC' for i in hardness_bins[:-1]] # ['0-5 HRC', '5-10 HRC', ...]
    
    df['hardness_group'] = pd.cut(df['Final hardness (HRC) - post tempering'],
                                  bins=hardness_bins,
                                  labels=hardness_labels,
                                  right=True, # (0, 5] -> 0 não está incluso, 5 está.
                                  include_lowest=True) # Garante que o valor 0 seja incluído
    
    print("Coluna 'hardness_group' criada.")

    # 3. Agrupar 'Tempering temperature (ºC)' em faixas de 50 ºC
    # (Min=100, Max=704.4 -> vamos de 100 a 750)
    temp_bins = list(range(100, 751, 50)) # [100, 150, 200, ..., 750]
    temp_labels = [f'{i}-{i+50} C' for i in temp_bins[:-1]] # ['100-150 C', '150-200 C', ...]
    
    df['temp_group'] = pd.cut(df['Tempering temperature (ºC)'],
                              bins=temp_bins,
                              labels=temp_labels,
                              right=True,
                              include_lowest=True)
    
    print("Coluna 'temp_group' criada.")

    # 4. Tratar 'Tempering time (s)' como categórico
    # Vamos apenas criar uma coluna de "grupo" para manter o padrão,
    # convertendo o número para uma string legível.
    df['time_group'] = df['Tempering time (s)'].astype(str) + ' s'
    
    print("Coluna 'time_group' criada.")
    
    # 5. 'Steel type' já é categórico, não precisa de nova coluna.

    print("\n--- Verificação dos novos grupos ---")
    print("\nValores únicos de 'hardness_group':")
    print(df['hardness_group'].value_counts().sort_index())
    
    print("\nValores únicos de 'temp_group':")
    print(df['temp_group'].value_counts().sort_index())

    print("\nValores únicos de 'time_group' (Amostra):")
    print(df['time_group'].value_counts().sort_index().head())
    
    # 6. Salvar o novo arquivo agrupado
    df.to_csv(output_file, index=False)
    
    print(f"\nSucesso! Arquivo com dados agrupados salvo em: {output_file}")
    print("Este novo arquivo agora contém as colunas 'hardness_group', 'temp_group' e 'time_group'.")

except FileNotFoundError:
    print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")