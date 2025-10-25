import pandas as pd
import numpy as np
import networkx as nx
import os

class SteelGraph:
    def __init__(self, processed_data_path):
        """
        Inicializa o grafo, carregando os dados agrupados.
        """
        try:
            self.df = pd.read_csv(processed_data_path)
            self.graph = nx.DiGraph() # Cria um Grafo Direcionado
            self._build_graph()
            print(f"Arquivo '{processed_data_path}' carregado.")
            print(f"Grafo principal construído com {self.graph.number_of_nodes()} nós e {self.graph.number_of_edges()} arestas.")
        except FileNotFoundError:
            print(f"Erro: Arquivo de dados '{processed_data_path}' não encontrado.")
            self.df = None
            self.graph = None

    def _build_graph(self):
        """
        Constrói o grafo em camadas a partir do DataFrame.
        """
        if self.df is None:
            return

        # Nós de início e fim com suas camadas
        self.graph.add_node('SOURCE', layer=0) # Camada 0
        self.graph.add_node('SINK', layer=5)   # Camada 5

        # Iterar sobre cada linha (cada processo de revenimento)
        for _, row in self.df.iterrows():
            # Extrair os nós do processo
            steel = row['Steel type']
            temp_group = row['temp_group']
            time_group = row['time_group']
            hardness_group = row['hardness_group']
            
            # Extrair os valores brutos para usar como pesos
            raw_temp = row['Tempering temperature (ºC)']
            raw_time = row['Tempering time (s)']

            # Adicionar nós com suas camadas
            self.graph.add_node(steel, layer=1)
            self.graph.add_node(temp_group, layer=2)
            self.graph.add_node(time_group, layer=3)
            self.graph.add_node(hardness_group, layer=4)

            # Adicionar arestas com os valores brutos como atributos
            self.graph.add_edge('SOURCE', steel)
            self.graph.add_edge(steel, temp_group, temperature=raw_temp)
            self.graph.add_edge(temp_group, time_group, time=raw_time)
            self.graph.add_edge(time_group, hardness_group)
            self.graph.add_edge(hardness_group, 'SINK')

    def find_best_process(self, filters, optimize_by='time'):
        """
        Encontra o melhor processo (caminho mais curto) usando Dijkstra.
        
        :param filters: Dicionário de filtros (restrições)
        :param optimize_by: 'time' ou 'temperature' (o que minimizar)
        :return: (Tupla) caminho, custo, grafo filtrado, e dict de detalhes
        """
        if self.graph is None:
            return "Grafo não foi construído.", 0, None, None

        # --- 1. Filtrar DataFrame ---
        filtered_df = self.df.copy()
        for col, op_val in filters.items():
            if col not in filtered_df.columns:
                print(f"Aviso: A coluna de filtro '{col}' não foi encontrada. Ignorando.")
                continue

            if isinstance(op_val, tuple):
                op, val = op_val
                if op == '>':
                    filtered_df = filtered_df[filtered_df[col] > val]
                elif op == '<':
                    filtered_df = filtered_df[filtered_df[col] < val]
                elif op == '==':
                    filtered_df = filtered_df[filtered_df[col] == val]
            else:
                filtered_df = filtered_df[filtered_df[col] == op_val]
        
        if filtered_df.empty:
            return f"Nenhum aço encontrado com os filtros: {filters}", 0, None, None
        
        # --- 2. Construir Grafo Temporário Filtrado ---
        temp_graph = SteelGraph.__new__(SteelGraph) 
        temp_graph.df = filtered_df
        temp_graph.graph = nx.DiGraph()
        temp_graph._build_graph() 
        
        print(f"Grafo filtrado construído com {temp_graph.graph.number_of_nodes()} nós e {temp_graph.graph.number_of_edges()} arestas.")

        # --- 3. Definir Pesos com base na Otimização ---
        for u, v in temp_graph.graph.edges():
            temp_graph.graph[u][v]['weight'] = 0.0

        if optimize_by == 'time':
            for u, v, data in temp_graph.graph.edges(data=True):
                if 'time' in data:
                    data['weight'] = data['time']
            print(f"\nOtimizando por: Menor Tempo de Revenimento")
                    
        elif optimize_by == 'temperature':
            for u, v, data in temp_graph.graph.edges(data=True):
                if 'temperature' in data:
                    data['weight'] = data['temperature']
            print(f"\nOtimizando por: Menor Temperatura (Custo Energético)")

        # --- 4. Rodar Dijkstra ---
        target_node = filters.get('hardness_group')
        if not target_node:
            return "Erro: 'hardness_group' (dureza) deve ser especificado nos filtros.", 0, None, None
            
        if target_node not in temp_graph.graph:
             return f"Dureza '{target_node}' não é alcançável com os filtros atuais.", 0, None, None

        try:
            path = nx.shortest_path(temp_graph.graph,
                                    source='SOURCE',
                                    target=target_node,
                                    weight='weight')
            
            cost = nx.shortest_path_length(temp_graph.graph,
                                           source='SOURCE',
                                           target=target_node,
                                           weight='weight')
            
            # --- 5. (MUDANÇA) EXTRAIR DETALHES COMPLETOS ---
            
            # Pegar os nós do caminho
            steel_type = path[1]
            temp_group = path[2]
            time_group = path[3]
            hardness_group = path[4]

            # Encontrar a linha exata no DataFrame filtrado que corresponde ao caminho
            chosen_row = filtered_df[
                (filtered_df['Steel type'] == steel_type) &
                (filtered_df['temp_group'] == temp_group) &
                (filtered_df['time_group'] == time_group) &
                (filtered_df['hardness_group'] == hardness_group)
            ]
            
            result_details = {} # Dicionário principal de resultados
            if not chosen_row.empty:
                # Pegar a primeira linha
                first_row = chosen_row.iloc[0]
                
                # (NOVO) Adicionar os detalhes do processo
                result_details['Aço Encontrado'] = first_row['Steel type']
                result_details['Dureza Final (HRC)'] = float(first_row['Final hardness (HRC) - post tempering'])
                result_details['Temp. Revenimento (C)'] = float(first_row['Tempering temperature (ºC)'])
                result_details['Tempo Revenimento (s)'] = float(first_row['Tempering time (s)'])
                
                # Adicionar colunas de composição
                comp_cols = ['C (%wt)', 'Mn (%wt)', 'P (%wt)', 'S (%wt)', 
                             'Si (%wt)', 'Ni (%wt)', 'Cr (%wt)', 'Mo (%wt)', 
                             'V (%wt)', 'Al (%wt)', 'Cu (%wt)']
                
                composition_dict = {} # Criar um sub-dicionário
                for col in comp_cols:
                    if col in first_row:
                        composition_dict[col] = float(first_row[col])
                
                result_details['Composição Química'] = composition_dict # Adicionar como sub-dicionário
            
            # Retorna os detalhes completos
            return path, cost, temp_graph.graph, result_details

        except nx.NetworkXNoPath:
            return f"Nenhum caminho encontrado de 'SOURCE' para '{target_node}' com os filtros atuais.", 0, None, None
        except Exception as e:
            return f"Ocorreu um erro: {e}", 0, None, None