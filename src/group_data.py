import pandas as pd
import numpy as np
import os

# Definir caminhos no topo
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
processed_data_dir = os.path.join(root_dir, 'datasets')
input_file = os.path.join(processed_data_dir, 'preprocessed_steel_data.csv')
output_file = os.path.join(processed_data_dir, 'grouped_steel_data.csv')

def main():
    """
    Executa a etapa de agrupamento (discretização) dos dados.
    """
    print("--- Executando Agrupamento (group_data.py) ---")
    try:
        # 1. Carregar o arquivo pré-processado
        df = pd.read_csv(input_file)
        print(f"Arquivo '{input_file}' carregado com {len(df)} registros.")

        # 2. Agrupar 'Final hardness (HRC)'
        hardness_bins = list(range(0, 66, 5)) 
        hardness_labels = [f'{i}-{i+5} HRC' for i in hardness_bins[:-1]]
        df['hardness_group'] = pd.cut(df['Final hardness (HRC) - post tempering'], bins=hardness_bins, labels=hardness_labels, right=True, include_lowest=True)
        print("Coluna 'hardness_group' criada.")

        # 3. Agrupar 'Tempering temperature (ºC)'
        temp_bins = list(range(100, 751, 50)) 
        temp_labels = [f'{i}-{i+50} C' for i in temp_bins[:-1]]
        df['temp_group'] = pd.cut(df['Tempering temperature (ºC)'], bins=temp_bins, labels=temp_labels, right=True, include_lowest=True)
        print("Coluna 'temp_group' criada.")

        # 4. Tratar 'Tempering time (s)'
        df['time_group'] = df['Tempering time (s)'].astype(str) + ' s'
        print("Coluna 'time_group' criada.")

        # 5. Salvar o novo arquivo agrupado
        df.to_csv(output_file, index=False)
        print(f"Sucesso! Arquivo com dados agrupados salvo em: {output_file}")
        return True # Retorna sucesso

    except FileNotFoundError:
        print(f"ERRO (group_data.py): O arquivo pré-processado '{input_file}' não foi encontrado.")
        print("Você executou o 'preprocess.py' primeiro?")
        return False # Retorna falha
    except Exception as e:
        print(f"Ocorreu um erro inesperado em group_data.py: {e}")
        return False # Retorna falha

if __name__ == "__main__":
    # Isso permite que o script ainda seja executado sozinho, se necessário
    main()