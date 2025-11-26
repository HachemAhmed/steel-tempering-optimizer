import pandas as pd
import numpy as np
import os


script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
datasets_dir = os.path.join(root_dir, 'datasets')
file_path = os.path.join(datasets_dir, 'Tempering data for carbon and low alloy steels - Raiipa(in).csv')
output_filename = os.path.join(datasets_dir, 'preprocessed_steel_data.csv')

def main():
    """
    Executa a etapa de pré-processamento dos dados.
    """
    print("--- Executando Pré-processamento (preprocess.py) ---")
    try:
        
        df = pd.read_csv(file_path, header=0)
        
        
        df_cleaned = df.dropna(how='all')

        
        columns_to_drop = ['Initial hardness (HRC) - post quenching', 'Source']
        existing_columns_to_drop = [col for col in columns_to_drop if col in df_cleaned.columns]
        
        if existing_columns_to_drop:
            df_cleaned = df_cleaned.drop(columns=existing_columns_to_drop)
            print(f"Colunas removidas com sucesso: {existing_columns_to_drop}")
        
        
        total_missing = df_cleaned.isnull().sum().sum()
        if total_missing > 0:
            print(f"\nAVISO: Foram encontrados {total_missing} dados ausentes (NaN).")
        else:
            print("Verificação: Nenhum dado ausente (NaN) encontrado.")

        
        df_cleaned.to_csv(output_filename, index=False)
        print(f"Arquivo pré-processado salvo com sucesso como: {output_filename}")
        return True 

    except FileNotFoundError:
        print(f"ERRO (preprocess.py): O arquivo original '{file_path}' não foi encontrado.")
        return False 
    except Exception as e:
        print(f"Ocorreu um erro inesperado em preprocess.py: {e}")
        return False 

if __name__ == "__main__":
    
    main()