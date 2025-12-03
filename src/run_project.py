import os
import json
import glob
import sys
import logging

class NullWriter:
    def write(self, text): pass
    def flush(self): pass

LOG_FILE_PATH = ""

def log_error(message, level='ERROR', exc_info=None):
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            filename=LOG_FILE_PATH,
            level=logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    if level == 'CRITICAL': logging.critical(message, exc_info=exc_info)
    elif level == 'WARNING': logging.warning(message, exc_info=exc_info)
    else: logging.error(message, exc_info=exc_info)

if __name__ == "__main__":
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    LOG_FILE_PATH = os.path.join(root_dir, 'error_log.txt')
    
    # Silent Mode (Background execution)
    sys.stdout = NullWriter()

    try:
        from steel_graph import SteelGraph
        from graph_visualizer import plot_filtered_graph, plot_full_graph, plot_hardness_heatmap
        import preprocess 

        datasets_dir = os.path.join(root_dir, 'datasets')
        original_data_path = os.path.join(datasets_dir, 'Tempering data for carbon and low alloy steels - Raiipa(in).csv')
        preprocessed_data_path = os.path.join(datasets_dir, 'preprocessed_steel_data.csv') 
        
        queries_config_path = os.path.join(root_dir, 'consultas.json')
        output_dir = os.path.join(root_dir, 'outputs')
        os.makedirs(output_dir, exist_ok=True)

        # Data Verification
        if not os.path.exists(preprocessed_data_path):
            if not os.path.exists(original_data_path):
                log_error(f"Original file not found at: {original_data_path}", level='CRITICAL')
                sys.exit(1)
            try:
                success = preprocess.main()
                if not success:
                    log_error("Preprocessing failed.")
                    sys.exit(1)
            except Exception as e:
                log_error(f"Error during preprocessing: {e}", exc_info=True)
                sys.exit(1)
        
        # Cleanup
        extensions = ["*.png", "*.jpg", "*.txt"]
        for ext in extensions:
            for f in glob.glob(os.path.join(output_dir, ext)):
                try: os.remove(f)
                except: pass

        # Load Config
        try:
            with open(queries_config_path, 'r', encoding='utf-8') as f:
                consultas = json.load(f)
        except Exception as e:
            log_error(f"Error reading consultas.json: {e}", level='CRITICAL')
            sys.exit(1)

        # Init Engine
        try:
            meu_grafo_de_acos = SteelGraph(preprocessed_data_path)
            if not meu_grafo_de_acos.graph:
                log_error("Master Graph initialized but empty.", level='CRITICAL')
                sys.exit(1)
        except Exception as e:
            log_error(f"Fatal error building Master Graph: {e}", exc_info=True)
            sys.exit(1)
            
        try:
            output_path_main = os.path.join(output_dir, 'main_full_graph.png')
            plot_full_graph(meu_grafo_de_acos.get_master_graph(), output_path_main)
        except Exception as e:
            log_error(f"Error generating full graph image: {e}")
        
        # Run Queries
        for i, consulta in enumerate(consultas):
            nome_consulta = consulta.get('query_name', f'Query_{i}')
            filtros = consulta.get('filters', {})
            otimizar_por = consulta.get('optimize_by', 'time')
            alpha = consulta.get('alpha', 0.5)
            
            imagem_saida = f"{nome_consulta}_graph.png"
            output_path_consulta = os.path.join(output_dir, imagem_saida)
            relatorio_filename = f"{nome_consulta}_report.txt"
            output_path_relatorio = os.path.join(output_dir, relatorio_filename)
            
            if not filtros:
                continue
            
            try:
                caminho, custo, grafo_podado, detalhes = meu_grafo_de_acos.find_best_process(
                    filtros, 
                    optimize_by=otimizar_por,
                    alpha=alpha
                )
            except Exception as e:
                log_error(f"Error processing algorithm for '{nome_consulta}': {e}", exc_info=True)
                try:
                    with open(output_path_relatorio, 'w', encoding='utf-8') as f:
                        f.write(f"EXECUTION ERROR:\nDetails: {e}")
                except: pass
                continue 

            # Write Report
            try:
                with open(output_path_relatorio, 'w', encoding='utf-8') as f:
                    f.write("="*60 + "\n")
                    f.write(f"TECHNICAL REPORT: {nome_consulta}\n")
                    f.write("="*60 + "\n\n")
                    
                    f.write("1. SEARCH PARAMETERS\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"Optimization Goal: {otimizar_por.upper()} (Minimize)\n")
                    if otimizar_por == 'balanced':
                        f.write(f"Alpha (Time Weight): {alpha}\n")
                        f.write(f"Beta (Temp Weight): {1-alpha:.1f}\n")

                    f.write("Filters Applied:\n")
                    for k, v in filtros.items():
                        if isinstance(v, dict):
                            if 'min' in v: val_str = f"Between {v['min']} and {v['max']}"
                            elif 'op' in v: val_str = f"{v['op']} {v['val']}"
                            else: val_str = str(v)
                        else: val_str = str(v)
                        f.write(f"  - {k}: {val_str}\n")
                    f.write("\n")
                    
                    f.write("2. OPTIMIZATION RESULTS (DIJKSTRA)\n")
                    f.write("-" * 30 + "\n")
                    
                    if isinstance(caminho, str):
                        f.write(f"STATUS: NOT FOUND\n")
                        f.write(f"Reason: {caminho}\n")
                    else:
                        if otimizar_por == 'time': unit = "s"
                        elif otimizar_por == 'temperature': unit = "C"
                        else: unit = "(Score)"
                        
                        f.write(f"STATUS: OPTIMAL SOLUTION FOUND\n")
                        f.write(f"Total Cost: {custo:.2f} {unit}\n\n")
                        
                        caminho_limpo = []
                        for node in caminho:
                            clean_name = node.split("|")[0].strip() if "|" in node else node
                            if clean_name == 'SOURCE': clean_name = 'Start'
                            if clean_name == 'SINK': clean_name = 'End'
                            caminho_limpo.append(clean_name)
                        
                        f.write("Process Flow:\n")
                        f.write(" -> ".join(caminho_limpo) + "\n\n")
                        
                        if detalhes:
                            f.write("3. SELECTED STEEL SPECS\n")
                            f.write("-" * 30 + "\n")
                            f.write(f"  Steel Type:        {detalhes.get('Found Steel')}\n")
                            f.write(f"  Final Hardness:    {detalhes.get('Final Hardness (HRC)')} HRC\n")
                            f.write(f"  Temp Process:      {detalhes.get('Temp (C)')} C\n")
                            f.write(f"  Time Process:      {detalhes.get('Time (s)')} s\n")
                            
                            if 'Composition' in detalhes:
                                f.write(f"\n  Composition (%):\n")
                                for elem, qtd in detalhes['Composition'].items():
                                    clean_elem = elem.replace(" (%wt)", "")
                                    f.write(f"    {clean_elem:<4}: {qtd}\n")
                    f.write("\n" + "="*60 + "\n")
            except Exception as e:
                log_error(f"Error writing report for '{nome_consulta}': {e}")

            # Graphs
            if grafo_podado is not None and grafo_podado.number_of_nodes() > 0:
                try:
                    plot_filtered_graph(grafo_podado, caminho, custo, otimizar_por, output_path_consulta)
                except Exception as e:
                    log_error(f"Error plotting graph '{nome_consulta}': {e}")

                try:
                    heatmap_filename = f"{nome_consulta}_heatmap.png"
                    output_path_heatmap = os.path.join(output_dir, heatmap_filename)
                    
                    coords_vencedor = None
                    hardness_vencedor = None
                    if detalhes:
                        coords_vencedor = (detalhes['Temp (C)'], detalhes['Time (s)'])
                        hardness_vencedor = detalhes.get('Final Hardness (HRC)')
                    
                    plot_hardness_heatmap(grafo_podado, output_path_heatmap, highlight_point=coords_vencedor, winner_hardness=hardness_vencedor)
                except Exception as e:
                    log_error(f"Error plotting heatmap '{nome_consulta}': {e}")

    except Exception as e:
        log_error("Fatal error in main execution loop.", exc_info=True)