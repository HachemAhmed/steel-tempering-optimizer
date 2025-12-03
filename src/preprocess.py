import pandas as pd
import os

# Define file paths relative to the script location
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
datasets_dir = os.path.join(root_dir, 'datasets')
file_path = os.path.join(datasets_dir, 'Tempering data for carbon and low alloy steels - Raiipa(in).csv')
output_filename = os.path.join(datasets_dir, 'preprocessed_steel_data.csv')

def main():
    """
    Executes the Data Cleaning Pipeline.
    Ensures the dataset is clean (no NaNs) and properly formatted before the Graph algorithm uses it.
    """
    print("--- Running Preprocessing (preprocess.py) ---")
    try:
        # Load Raw Data (Force UTF-8 to handle symbols like 'ºC')
        df = pd.read_csv(file_path, header=0, encoding='utf-8')
        
        # 1. Remove rows that are completely empty
        df_cleaned = df.dropna(how='all')

        # 2. Remove metadata columns irrelevant to the graph logic
        columns_to_drop = ['Initial hardness (HRC) - post quenching', 'Source']
        existing_columns_to_drop = [col for col in columns_to_drop if col in df_cleaned.columns]
        
        if existing_columns_to_drop:
            df_cleaned = df_cleaned.drop(columns=existing_columns_to_drop)
            print(f"Columns removed: {existing_columns_to_drop}")
        
        # 3. Integrity Check: Ensure no missing values remain
        total_missing = df_cleaned.isnull().sum().sum()
        if total_missing > 0:
            print(f"\nWARNING: Found {total_missing} missing values (NaN).")

        # 4. Save Cleaned Artifact
        df_cleaned.to_csv(output_filename, index=False, encoding='utf-8')
        print(f"Processed file saved to: {output_filename}")
        return True

    except FileNotFoundError:
        print(f"ERROR: Raw file '{file_path}' not found.")
        return False
    except Exception as e:
        print(f"Critical error in preprocessing: {e}")
        return False

if __name__ == "__main__":
    main()