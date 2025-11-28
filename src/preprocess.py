import pandas as pd
import numpy as np
import os

# Set paths
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
datasets_dir = os.path.join(root_dir, 'datasets')
file_path = os.path.join(datasets_dir, 'Tempering data for carbon and low alloy steels - Raiipa(in).csv')
output_filename = os.path.join(datasets_dir, 'preprocessed_steel_data.csv')

def main():
    """
    Executes the data preprocessing pipeline.
    """
    print("--- Running Preprocessing (preprocess.py) ---")
    try:
        df = pd.read_csv(file_path, header=0)
        
        df_cleaned = df.dropna(how='all')

        columns_to_drop = ['Initial hardness (HRC) - post quenching', 'Source']
        existing_columns_to_drop = [col for col in columns_to_drop if col in df_cleaned.columns]
        
        if existing_columns_to_drop:
            df_cleaned = df_cleaned.drop(columns=existing_columns_to_drop)
            print(f"Columns removed: {existing_columns_to_drop}")

        total_missing = df_cleaned.isnull().sum().sum()
        if total_missing > 0:
            print(f"\nWARNING: Found {total_missing} missing values (NaN).")
        else:
            print("Check: No missing values found.")

        df_cleaned.to_csv(output_filename, index=False)
        print(f"Processed file saved successfully to: {output_filename}")
        return True

    except FileNotFoundError:
        print(f"ERROR (preprocess.py): Original file '{file_path}' not found.")
        return False
    except Exception as e:
        print(f"Unexpected error in preprocess.py: {e}")
        return False

if __name__ == "__main__":
    main()