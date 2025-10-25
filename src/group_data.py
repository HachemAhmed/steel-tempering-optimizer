import pandas as pd
import numpy as np
import os



script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)


processed_data_dir = os.path.join(root_dir, 'datasets')
input_file = os.path.join(processed_data_dir, 'preprocessed_steel_data.csv')


output_file = os.path.join(processed_data_dir, 'grouped_steel_data.csv')

try:
    
    df = pd.read_csv(input_file)
    print(f"Arquivo '{input_file}' carregado com {len(df)} registros.")

    
    
    hardness_bins = list(range(0, 66, 5)) 
    hardness_labels = [f'{i}-{i+5} HRC' for i in hardness_bins[:-1]] 
    
    df['hardness_group'] = pd.cut(df['Final hardness (HRC) - post tempering'],
                                  bins=hardness_bins,
                                  labels=hardness_labels,
                                  right=True, 
                                  include_lowest=True) 
    
    print("Coluna 'hardness_group' criada.")

    
    
    temp_bins = list(range(100, 751, 50)) 
    temp_labels = [f'{i}-{i+50} C' for i in temp_bins[:-1]] 
    
    df['temp_group'] = pd.cut(df['Tempering temperature (ºC)'],
                              bins=temp_bins,
                              labels=temp_labels,
                              right=True,
                              include_lowest=True)
    
    print("Coluna 'temp_group' criada.")

    
    
    
    df['time_group'] = df['Tempering time (s)'].astype(str) + ' s'
    
    print("Coluna 'time_group' criada.")
    
    

    print("\n--- Verificação dos novos grupos ---")
    print("\nValores únicos de 'hardness_group':")
    print(df['hardness_group'].value_counts().sort_index())
    
    print("\nValores únicos de 'temp_group':")
    print(df['temp_group'].value_counts().sort_index())

    print("\nValores únicos de 'time_group' (Amostra):")
    print(df['time_group'].value_counts().sort_index().head())
    
    
    df.to_csv(output_file, index=False)
    
    print(f"\nSucesso! Arquivo com dados agrupados salvo em: {output_file}")
    print("Este novo arquivo agora contém as colunas 'hardness_group', 'temp_group' e 'time_group'.")

except FileNotFoundError:
    print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")