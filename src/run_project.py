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
from utils import log_error, NullWriter
from graph_visualizer import plot_filtered_graph_comparison, plot_full_graph, plot_interactive_heatmap
from reporter import generate_text_report

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
    Generates visual outputs:
    1. Comparison graph (PNG)
    2. Interactive heatmap (HTML) - Saved to both output_dir AND docs/heatmaps/
    """
    # 1. Comparison Graph (Mantido igual)
    try:
        output_path = os.path.join(output_dir, f"{nome}_graph.png")
        plot_filtered_graph_comparison(grafo_podado, paths, custo, optimize_by, output_path)
    except Exception as e:
        log_error(f"Error plotting comparison graph '{nome}': {e}")
    
    # 2. Interactive Heatmap (ATUALIZADO PARA GITHUB PAGES)
    try:
        # Caminho 1: Pasta de outputs normal (para seu uso local)
        output_path_local = os.path.join(output_dir, f"{nome}_heatmap.html")
        
        # Caminho 2: Pasta do GitHub Pages (docs/heatmaps)
        # Cria a pasta docs/heatmaps se ela não existir
        docs_dir = os.path.join(os.getcwd(), 'docs', 'heatmaps')
        os.makedirs(docs_dir, exist_ok=True)
        output_path_docs = os.path.join(docs_dir, f"{nome}_heatmap.html")

        highlight_points = [(d['Temp (C)'], d['Time (s)']) 
                           for d in details_list if isinstance(details_list, list)]
        
        # Gera o gráfico salvando direto na pasta do site
        plot_interactive_heatmap(grafo_podado, output_path_docs, highlight_points=highlight_points, auto_open=False)
        
        # Opcional: Copiar também para a pasta de outputs local se quiser duplicado
        # Mas salvar direto na docs/heatmaps já resolve o problema do site.
        print(f"   -> Heatmap published to: {output_path_docs}")

    except Exception as e:
        log_error(f"Error plotting heatmap '{nome}': {e}")


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
    
    sys.stdout = NullWriter()
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


# ============================================================================
# MAIN
# ============================================================================

def main():
    setup_environment()
    
    consultas = load_and_validate_queries()
    if consultas is None: 
        sys.exit(1)
    
    graph = initialize_graph()
    if graph is None: 
        sys.exit(1)
    
    for query in consultas:
        try:
            execute_query(graph, query, config.OUTPUT_DIR)
        except Exception as e:
            log_error(f"Fatal error in query '{query.get('query_name')}': {e}", exc_info=True)
            continue


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_error("Fatal error in main execution", exc_info=True)
        sys.exit(1)