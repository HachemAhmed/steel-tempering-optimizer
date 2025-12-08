"""
Main execution script for steel heat treatment optimization.
Orchestrates the complete pipeline: preprocessing, graph construction,
query execution, and output generation.
"""
import os
import json
import glob
import sys
import config
import preprocess
from steel_graph import SteelGraph
from utils import log_error, NullWriter
from graph_visualizer import plot_filtered_graph_comparison, plot_full_graph, plot_interactive_heatmap, plot_static_heatmap

from reporter import generate_text_report
from generate_index import generate_index_html
# ============================================================================
# VALIDATION
# ============================================================================

def validate_query(query, index):
    """
    Validates query structure and parameters.
    """
    required = ['query_name', 'optimize_by', 'filters']
    
    for key in required:
        if key not in query:
            log_error(f"Query #{index}: Missing required field '{key}'", level='WARNING')
            return None
    
    valid_optimizations = ['time', 'temperature', 'balanced']
    if query['optimize_by'] not in valid_optimizations:
        log_error(f"Query #{index} ('{query['query_name']}'): Invalid optimize_by", level='WARNING')
        return None
    
    if query['optimize_by'] == 'balanced' and 'alpha' not in query:
        query['alpha'] = 0.5
    
    if not query['filters']:
        log_error(f"Query #{index} ('{query['query_name']}'): Empty filters", level='WARNING')
        return None
    
    return query


# ============================================================================
# QUERY EXECUTION
# ============================================================================

def execute_query(graph, query, output_dir):
    """
    Executes a complete query: runs algorithm, generates report and visualizations.
    """
    nome = query['query_name']
    filtros = query['filters']
    optimize_by = query['optimize_by']
    alpha = query.get('alpha', 0.5)
    
    # Step 1: Run optimization algorithm
    result = _run_algorithm(graph, nome, filtros, optimize_by, alpha)
    if result is None:
        return False
    
    paths, custo, grafo_podado, details_list, success = result
    
    # Step 2: Generate report
    report_path = os.path.join(output_dir, f"{nome}_report.txt")
    if success:
        result_data = (paths, custo, grafo_podado, details_list)
    else:
        result_data = paths
    
    generate_text_report(report_path, nome, optimize_by, filtros, result_data, alpha)
    
    # Step 3: Generate visualizations
    if success and grafo_podado and grafo_podado.number_of_nodes() > 0:
        _generate_visualizations(output_dir, nome, paths, custo, optimize_by, 
                                grafo_podado, details_list)
    
    return success


def _run_algorithm(graph, nome, filtros, optimize_by, alpha):
    """
    Executes the optimization algorithm.
    """
    try:
        result = graph.find_best_process(filtros, optimize_by=optimize_by, alpha=alpha)
        
        if isinstance(result, tuple):
            paths, custo, grafo_podado, details_list = result
            return paths, custo, grafo_podado, details_list, True
        else:
            log_error(f"Query '{nome}' returned error: {result}", level='WARNING')
            return result, 0, None, [], False
            
    except Exception as e:
        log_error(f"Error processing '{nome}': {e}", exc_info=True)
        return f"Execution error: {str(e)}", 0, None, [], False


def _generate_visualizations(output_dir, nome, paths, custo, optimize_by, 
                             grafo_podado, details_list):
    """
    Generates visual outputs optimized for scientific publication:
    1. Comparison graph (PNG) -> outputs/ (for local analysis)
    2. Heatmap PNG (high-res) -> outputs/ (for paper figures)
    3. Interactive heatmap (HTML) -> docs/heatmaps/ (for GitHub Pages supplement)
    """
    
    # 1. Comparison Graph PNG (unchanged)
    try:
        output_path = os.path.join(output_dir, f"{nome}_graph.png")
        plot_filtered_graph_comparison(grafo_podado, paths, custo, optimize_by, output_path)
    except Exception as e:
        log_error(f"Error plotting comparison graph '{nome}': {e}")
    
    # Prepare highlight points for heatmaps
    highlight_points = [(d['Temp (C)'], d['Time (s)']) 
                       for d in details_list if isinstance(details_list, list)]
    
    # 2. Static Heatmap PNG (NEW - for paper)
    try:
        png_path = os.path.join(output_dir, f"{nome}_heatmap.png")
        plot_static_heatmap(grafo_podado, png_path, highlight_points=highlight_points)
        print(f"   -> Static heatmap (for paper): {png_path}")
    except Exception as e:
        log_error(f"Error plotting static heatmap '{nome}': {e}")
    
    # 3. Interactive Heatmap HTML (for GitHub Pages only)
    try:
        docs_dir = os.path.join(os.getcwd(), 'docs', 'heatmaps')
        os.makedirs(docs_dir, exist_ok=True)
        html_path = os.path.join(docs_dir, f"{nome}_heatmap.html")
        
        plot_interactive_heatmap(grafo_podado, html_path, 
                                highlight_points=highlight_points, auto_open=False)
        
        print(f"   -> Interactive heatmap (online): {html_path}")
    except Exception as e:
        log_error(f"Error plotting interactive heatmap '{nome}': {e}")


# ============================================================================
# SETUP AND INITIALIZATION
# ============================================================================

def setup_environment():
    """
    Configures initial environment.
    """
    if os.path.exists(config.LOG_FILE_PATH):
        try: 
            os.remove(config.LOG_FILE_PATH)
        except: 
            pass
    
    # Suppress stdout only if explicitly enabled
    # sys.stdout = NullWriter()  # Commented out to see output
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    for ext in ["*.png", "*.jpg", "*.txt"]:
        for f in glob.glob(os.path.join(config.OUTPUT_DIR, ext)):
            try: 
                os.remove(f)
            except: 
                pass


def load_and_validate_queries():
    """
    Loads and validates queries from consultas.json.
    """
    try:
        with open(config.QUERIES_PATH, 'r', encoding='utf-8') as f:
            consultas_raw = json.load(f)
        
        if not isinstance(consultas_raw, list):
            log_error("consultas.json must contain a list of queries", level='CRITICAL')
            return None
        
        consultas = []
        for idx, query in enumerate(consultas_raw):
            validated = validate_query(query, idx)
            if validated:
                consultas.append(validated)
        
        if not consultas:
            log_error("No valid queries found", level='CRITICAL')
            return None
        
        return consultas
        
    except FileNotFoundError:
        log_error(f"consultas.json not found at: {config.QUERIES_PATH}", level='CRITICAL')
        return None
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON: {e}", level='CRITICAL')
        return None
    except Exception as e:
        log_error(f"Error reading consultas.json: {e}", level='CRITICAL')
        return None


def initialize_graph():
    """
    Initializes the master steel graph.
    """
    from steel_graph import SteelGraph
    import preprocess
    
    if not os.path.exists(config.PROCESSED_DATA_PATH):
        if not os.path.exists(config.RAW_DATA_PATH):
            log_error(f"Raw file not found: {config.RAW_DATA_PATH}", level='CRITICAL')
            return None
        try:
            if not preprocess.main():
                log_error("Preprocessing failed", level='CRITICAL')
                return None
        except Exception as e:
            log_error(f"Preprocessing error: {e}", exc_info=True, level='CRITICAL')
            return None
    
    try:
        graph = SteelGraph(config.PROCESSED_DATA_PATH)
        if not graph.graph:
            log_error("Master Graph empty", level='CRITICAL')
            return None
        
        try:
            output_path = os.path.join(config.OUTPUT_DIR, 'main_full_graph.png')
            plot_full_graph(graph.get_master_graph(), output_path)
        except Exception as e:
            log_error(f"Error generating full graph: {e}")
        
        return graph
        
    except Exception as e:
        log_error(f"Error building graph: {e}", exc_info=True, level='CRITICAL')
        return None

def load_queries():
    """
    Loads query definitions from consultas.json
    
    Returns:
        list: List of query dictionaries, or empty list on error
    """
    try:
        with open(config.QUERIES_PATH, 'r', encoding='utf-8') as f:
            queries = json.load(f)
        
        if not isinstance(queries, list):
            log_error("consultas.json must contain a list of queries")
            return []
        
        print(f"✓ Loaded {len(queries)} queries from {config.QUERIES_PATH}")
        return queries
        
    except FileNotFoundError:
        log_error(f"Query file not found: {config.QUERIES_PATH}")
        return []
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in {config.QUERIES_PATH}: {e}")
        return []
    except Exception as e:
        log_error(f"Error loading queries: {e}")
        return []
# ============================================================================
# MAIN
# ============================================================================

def main():
    """
    Main execution pipeline:
    1. Preprocesses raw data
    2. Constructs the steel treatment graph
    3. Generates full graph visualization
    4. Executes all queries from consultas.json
    5. Generates index.html automatically
    """
    setup_environment()
    
    # Step 1: Preprocess data
    print("\n" + "="*60)
    print("STEP 1: DATA PREPROCESSING")
    print("="*60)
    if not preprocess.main():
        log_error("Preprocessing failed")
        return False
    
    # Step 2: Build graph
    print("\n" + "="*60)
    print("STEP 2: GRAPH CONSTRUCTION")
    print("="*60)
    try:
        from steel_graph import SteelGraph
        graph = SteelGraph(config.PROCESSED_DATA_PATH)
        print("✓ Graph constructed successfully")
    except Exception as e:
        log_error(f"Graph construction failed: {e}")
        return False
    
    # Step 3: Generate full graph visualization
    print("\n" + "="*60)
    print("STEP 3: FULL GRAPH VISUALIZATION")
    print("="*60)
    full_graph_path = os.path.join(config.OUTPUT_DIR, "full_graph.png")
    plot_full_graph(graph.get_master_graph(), full_graph_path)
    
    # Step 4: Load and execute queries
    print("\n" + "="*60)
    print("STEP 4: EXECUTING QUERIES")
    print("="*60)
    queries = load_queries()
    if not queries:
        log_error("No queries to execute")
        return False
    
    print(f"Found {len(queries)} queries to execute\n")
    
    for idx, query in enumerate(queries, 1):
        print(f"\n--- Query {idx}/{len(queries)}: {query.get('query_name', 'Unnamed')} ---")
        if not validate_query(query, idx):
            continue
        execute_query(graph, query, config.OUTPUT_DIR)
    
    # Step 5: Generate index.html automatically
    print("\n" + "="*60)
    print("STEP 5: GENERATING INDEX.HTML")
    print("="*60)
    generate_index_html()
    
    print("\n" + "="*60)
    print("✓ ALL STEPS COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"✓ Results saved in: {config.OUTPUT_DIR}")
    print(f"✓ Open index.html in your browser to view all results")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    main()