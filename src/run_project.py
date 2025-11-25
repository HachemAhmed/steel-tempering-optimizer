import os
import json
import glob
import sys
import logging

# --- Configuração de Silêncio ---
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

        if not os.path.exists(preprocessed_data_path):
            if not os.path.exists(original_data_path):
                log_error(f"Arquivo original não encontrado em: {original_data_path}", level='CRITICAL')
                sys.exit(1)
            try:
                success = preprocess.main()
                if not success:
                    log_error("O script preprocess.main() retornou falha.")
                    sys.exit(1)
            except Exception as e:
                log_error(f"Erro durante a execução do pré-processamento: {e}", exc_info=True)
                sys.exit(1)
        
        extensions = ["*.png", "*.jpg", "*.txt"]
        for ext in extensions:
            for f in glob.glob(os.path.join(output_dir, ext)):
                try: os.remove(f)
                except: pass

        try:
            with open(queries_config_path, 'r', encoding='utf-8') as f:
                consultas = json.load(f)
        except Exception as e:
            log_error(f"Erro ao ler consultas.json: {e}", level='CRITICAL')
            sys.exit(1)

        try:
            meu_grafo_de_acos = SteelGraph(preprocessed_data_path)
            if not meu_grafo_de_acos.graph:
                log_error("O Grafo Mestre foi inicializado mas está vazio.", level='CRITICAL')
                sys.exit(1)
        except Exception as e:
            log_error(f"Erro fatal ao construir o Grafo Mestre: {e}", exc_info=True)
            sys.exit(1)
            
        try:
            output_path_main = os.path.join(output_dir, 'main_full_graph.png')
            plot_full_graph(meu_grafo_de_acos.get_master_graph(), output_path_main)
        except Exception as e:
            log_error(f"Erro ao gerar a imagem do Grafo Completo: {e}")
        
        for i, consulta in enumerate(consultas):
            nome_consulta = consulta.get('nome_consulta', f'Consulta_{i}')
            filtros = consulta.get('filtros', {})
            otimizar_por = consulta.get('otimizar_por', 'time')
            
            imagem_saida = f"{nome_consulta}_graph.png"
            output_path_consulta = os.path.join(output_dir, imagem_saida)
            relatorio_filename = f"{nome_consulta}_relatorio.txt"
            output_path_relatorio = os.path.join(output_dir, relatorio_filename)
            
            if not filtros:
                continue
            
            try:
                caminho, custo, grafo_podado, detalhes = meu_grafo_de_acos.find_best_process(
                    filtros, 
                    optimize_by=otimizar_por
                )
            except Exception as e:
                log_error(f"Erro ao processar algoritmo para consulta '{nome_consulta}': {e}", exc_info=True)
                try:
                    with open(output_path_relatorio, 'w', encoding='utf-8') as f:
                        f.write(f"ERRO DE EXECUÇÃO:\nDetalhe: {e}")
                except: pass
                continue 

            try:
                with open(output_path_relatorio, 'w', encoding='utf-8') as f:
                    f.write("="*60 + "\n")
                    f.write(f"RELATÓRIO TÉCNICO: {nome_consulta}\n")
                    f.write("="*60 + "\n\n")
                    
                    f.write("1. PARÂMETROS DE BUSCA\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"Objetivo de Otimização: {otimizar_por.upper()} (Minimizar)\n")
                    f.write("Filtros Aplicados:\n")
                    for k, v in filtros.items():
                        if isinstance(v, dict):
                            if 'min' in v: val_str = f"Entre {v['min']} e {v['max']}"
                            elif 'op' in v: val_str = f"{v['op']} {v['val']}"
                            else: val_str = str(v)
                        else: val_str = str(v)
                        f.write(f"  - {k}: {val_str}\n")
                    f.write("\n")
                    
                    f.write("2. RESULTADO DA OTIMIZAÇÃO (DIJKSTRA)\n")
                    f.write("-" * 30 + "\n")
                    
                    if isinstance(caminho, str):
                        f.write(f"STATUS: NÃO ENCONTRADO\n")
                        f.write(f"Motivo: {caminho}\n")
                    else:
                        unit = "s" if otimizar_por == 'time' else "ºC"
                        f.write(f"STATUS: SOLUÇÃO ÓTIMA ENCONTRADA\n")
                        f.write(f"Custo Total: {custo} {unit}\n\n")
                        
                        caminho_limpo = []
                        for node in caminho:
                            clean_name = node.split("|")[0].strip() if "|" in node else node
                            if clean_name == 'SOURCE': clean_name = 'Início'
                            if clean_name == 'SINK': clean_name = 'Fim'
                            caminho_limpo.append(clean_name)
                        
                        f.write("Fluxo do Processo:\n")
                        f.write(" -> ".join(caminho_limpo) + "\n\n")
                        
                        if detalhes:
                            f.write("3. ESPECIFICAÇÕES DO AÇO SELECIONADO\n")
                            f.write("-" * 30 + "\n")
                            f.write(f"  Tipo de Aço:            {detalhes.get('Aço Encontrado')}\n")
                            f.write(f"  Dureza Final Obtida:    {detalhes.get('Dureza Final (HRC)')} HRC\n")
                            f.write(f"  Temperatura Processo:   {detalhes.get('Temp. Revenimento (C)')} ºC\n")
                            f.write(f"  Tempo de Processo:      {detalhes.get('Tempo Revenimento (s)')} s\n")
                            
                            if 'Composição Química' in detalhes:
                                f.write(f"\n  Composição Química (% peso):\n")
                                comp = detalhes['Composição Química']
                                for elem, qtd in comp.items():
                                    clean_elem = elem.replace(" (%wt)", "")
                                    f.write(f"    {clean_elem:<4}: {qtd}\n")
                    f.write("\n" + "="*60 + "\n")
            except Exception as e:
                log_error(f"Erro ao escrever relatório TXT para '{nome_consulta}': {e}")

            if grafo_podado is not None and grafo_podado.number_of_nodes() > 0:
                try:
                    plot_filtered_graph(grafo_podado, caminho, custo, otimizar_por, output_path_consulta)
                except Exception as e:
                    log_error(f"Erro ao gerar gráfico visual para '{nome_consulta}': {e}")

                try:
                    heatmap_filename = f"{nome_consulta}_heatmap.png"
                    output_path_heatmap = os.path.join(output_dir, heatmap_filename)
                    
                    coords_vencedor = None
                    hardness_vencedor = None
                    if detalhes:
                        coords_vencedor = (detalhes['Temp. Revenimento (C)'], detalhes['Tempo Revenimento (s)'])
                        # IMPORTANTE: Captura a dureza para passar ao visualizador
                        hardness_vencedor = detalhes.get('Dureza Final (HRC)')
                    
                    plot_hardness_heatmap(grafo_podado, output_path_heatmap, highlight_point=coords_vencedor, winner_hardness=hardness_vencedor)
                except Exception as e:
                    log_error(f"Erro ao gerar mapa de calor para '{nome_consulta}': {e}")

    except Exception as e:
        log_error("Erro fatal na execução principal:", exc_info=True)