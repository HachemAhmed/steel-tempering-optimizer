"""
Configuration module for the Steel Heat Treatment Optimization project.
Centralizes all paths and database column mappings.
"""
import os

# Project paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DATASETS_DIR = os.path.join(ROOT_DIR, 'datasets')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'outputs')

# File paths
RAW_DATA_PATH = os.path.join(DATASETS_DIR, 'Tempering data for carbon and low alloy steels - Raiipa(in).csv')
PROCESSED_DATA_PATH = os.path.join(DATASETS_DIR, 'preprocessed_steel_data.csv')
QUERIES_PATH = os.path.join(ROOT_DIR, 'consultas.json')
LOG_FILE_PATH = os.path.join(ROOT_DIR, 'error_log.txt')

# Database column configuration
class DB_CONFIG:
    """Maps column names from the CSV database."""
    COL_STEEL = 'Steel type'
    COL_TIME = 'Tempering time (s)'
    COL_TEMP = 'Tempering temperature (ºC)'
    COL_HARDNESS = 'Final hardness (HRC) - post tempering'
    KEY_COMPOSITION = '(%wt)'  # Pattern for composition columns: "C (%wt)", "Cr (%wt)", etc.