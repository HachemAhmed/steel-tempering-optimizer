"""
Data preprocessing module for steel heat treatment data.
Handles ETL (Extract, Transform, Load) operations on raw CSV data.
"""
import pandas as pd
import config

def main():
    """
    Executes the ETL pipeline:
    1. Loads raw CSV data
    2. Cleans column names and removes unnecessary columns
    3. Validates required columns exist
    4. Saves processed data for graph construction
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("--- Running Preprocessing (preprocess.py) ---")
    try:
        df = pd.read_csv(config.RAW_DATA_PATH, header=0, encoding='utf-8')
        
        # Clean whitespace from column names
        df.columns = df.columns.str.strip()
        
        # Remove completely empty rows
        df_cleaned = df.dropna(how='all')

        # Drop unnecessary columns
        columns_to_drop = ['Initial hardness (HRC) - post quenching', 'Source']
        existing_columns_to_drop = [col for col in columns_to_drop if col in df_cleaned.columns]
        
        if existing_columns_to_drop:
            df_cleaned = df_cleaned.drop(columns=existing_columns_to_drop)
            print(f"Columns removed: {existing_columns_to_drop}")
        
        # Validate required columns exist
        required_columns = [
            config.DB_CONFIG.COL_STEEL,
            config.DB_CONFIG.COL_TIME,
            config.DB_CONFIG.COL_TEMP,
            config.DB_CONFIG.COL_HARDNESS
        ]
        
        missing_columns = [col for col in required_columns if col not in df_cleaned.columns]
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            print(f"Available columns: {list(df_cleaned.columns)}")
            return False
        
        # Verify composition columns format
        comp_cols = [c for c in df_cleaned.columns if config.DB_CONFIG.KEY_COMPOSITION in c]
        if not comp_cols:
            print(f"WARNING: No composition columns found with pattern '{config.DB_CONFIG.KEY_COMPOSITION}'")
            print(f"Available columns: {list(df_cleaned.columns)}")
        else:
            print(f"Found {len(comp_cols)} composition columns: {comp_cols}")
        
        # Report missing values
        total_missing = df_cleaned.isnull().sum().sum()
        if total_missing > 0:
            print(f"\nWARNING: Found {total_missing} missing values (NaN).")

        # Save processed data
        df_cleaned.to_csv(config.PROCESSED_DATA_PATH, index=False, encoding='utf-8')
        print(f"Processed file saved to: {config.PROCESSED_DATA_PATH}")
        return True

    except FileNotFoundError:
        print(f"ERROR: Raw file not found at {config.RAW_DATA_PATH}")
        return False
    except Exception as e:
        print(f"Critical error in preprocessing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()