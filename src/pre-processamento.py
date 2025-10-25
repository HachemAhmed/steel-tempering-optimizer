import pandas as pd
import numpy as np
import os 





script_dir = os.path.dirname(os.path.abspath(__file__))


root_dir = os.path.dirname(script_dir) 


datasets_dir = os.path.join(root_dir, 'datasets') 


input_file = 'Tempering data for carbon and low alloy steels - Raiipa(in).csv'
output_file = 'preprocessed_steel_data.csv'


file_path = os.path.join(datasets_dir, input_file)
output_filename = os.path.join(datasets_dir, output_file)

print(f"Executando script em: {script_dir}")
print(f"Procurando dataset em: {file_path}")
print(f"Salvando resultado em: {output_filename}\n")



try:
    
    df = pd.read_csv(file_path, header=0)

    
    df_cleaned = df.dropna(how='all')

    
    columns_to_drop = ['Initial hardness (HRC) - post quenching', 'Source']
    
    existing_columns_to_drop = [col for col in columns_to_drop if col in df_cleaned.columns]
    
    if existing_columns_to_drop:
        df_cleaned = df_cleaned.drop(columns=existing_columns_to_drop)
        print(f"Colunas removidas com sucesso: {existing_columns_to_drop}")
    else:
        print("As colunas 'Initial hardness (HRC) - post quenching' e/ou 'Source' não foram encontradas.")

    
    print("\n--- Verificando dados ausentes (NaN) nas colunas restantes ---")
    missing_data_count = df_cleaned.isnull().sum()
    print(missing_data_count)
    
    total_missing = missing_data_count.sum()
    if total_missing > 0:
        print(f"\nAVISO: Foram encontrados {total_missing} dados ausentes (NaN) em outras colunas.")
    else:
        print("\nÓtimo! Nenhum dado ausente (NaN) foi encontrado nas colunas restantes.")

    
    print("\n--- Informações do DataFrame Pré-processado ---")
    df_cleaned.info()

    
    df_cleaned.to_csv(output_filename, index=False)
    
    print(f"\nArquivo pré-processado salvo com sucesso como: {output_filename}")
    print(f"Este arquivo contém {len(df_cleaned)} registros de aço prontos para a próxima etapa.")

except FileNotFoundError:
    print(f"Erro: O arquivo '{file_path}' não foi encontrado.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")