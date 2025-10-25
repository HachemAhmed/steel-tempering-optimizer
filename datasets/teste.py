import pandas as pd
import numpy as np

# Nome do arquivo CSV
file_name = 'Tempering data for carbon and low alloy steels - Raiipa(in).csv'

try:
    # Ler o arquivo CSV para um DataFrame
    # Explicitamente tratar '?' como NaN (Not a Number) para facilitar a contagem
    df = pd.read_csv(file_name, na_values='?')

    # Nome da coluna a ser verificada
    column_name = 'Initial hardness (HRC) - post quenching'

    # Verificar se a coluna existe no DataFrame
    if column_name in df.columns:
        # Contar o número total de linhas
        total_rows = len(df)

        # Contar o número de valores ausentes (NaN) na coluna especificada
        missing_values_count = df[column_name].isnull().sum()

        # Calcular a porcentagem de valores ausentes
        if total_rows > 0:
            missing_percentage = (missing_values_count / total_rows) * 100
            print(f"Total de registros: {total_rows}")
            print(f"Número de valores ausentes em '{column_name}': {missing_values_count}")
            print(f"Porcentagem de valores ausentes: {missing_percentage:.2f}%")
        else:
            print("O arquivo CSV está vazio.")

    else:
        print(f"Erro: A coluna '{column_name}' não foi encontrada no arquivo CSV.")
        print("Colunas disponíveis:", df.columns.tolist())

except FileNotFoundError:
    print(f"Erro: O arquivo '{file_name}' não foi encontrado.")
except Exception as e:
    print(f"Ocorreu um erro ao processar o arquivo: {e}")