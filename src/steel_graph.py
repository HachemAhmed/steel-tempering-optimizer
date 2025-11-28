import pandas as pd
import numpy as np
import networkx as nx
import os

class SteelGraph:
    def __init__(self, preprocessed_data_path):
        """
        Initializes the graph by loading the preprocessed data.
        """
        try:
            self.df = pd.read_csv(preprocessed_data_path)
            
            self.max_time = self.df['Tempering time (s)'].max()
            self.max_temp = self.df['Tempering temperature (ºC)'].max()
            
            self.graph = nx.DiGraph() 
            self._build_master_graph()
        except FileNotFoundError:
            self.df = None
            self.graph = None
            raise 

    def _build_master_graph(self):
        """
        Builds the precise master graph with all 1196 processes.
        """
        if self.df is None: return
            
        self.graph.add_node('SOURCE', layer=0)
        self.graph.add_node('SINK', layer=5) 
        
        comp_cols = [c for c in self.df.columns if '%wt' in c]
        steel_compositions = self.df.groupby('Steel type').first()[comp_cols]
        
        for i, row in self.df.iterrows():
            s = row['Steel type']
            t = row['Tempering time (s)']
            tmp = row['Tempering temperature (ºC)']
            h = row['Final hardness (HRC) - post tempering']

            n_steel = f"Steel: {s}"
            n_time = f"Time: {t} s | id:{i}"  
            n_temp = f"Temp: {tmp} C | id:{i}" 
            n_hardness = f"Hardness: {h} HRC" 

            if not self.graph.has_node(n_steel):
                comp_data = steel_compositions.loc[s].to_dict() 
                comp_data['steel_type'] = s 
                comp_data['Steel type'] = s 
                self.graph.add_node(n_steel, layer=1, type='steel', **comp_data)
                self.graph.add_edge('SOURCE', n_steel) 
            
            if not self.graph.has_node(n_time): self.graph.add_node(n_time, layer=2, type='time', value=t)
            if not self.graph.has_node(n_temp): self.graph.add_node(n_temp, layer=3, type='temp', value=tmp)
            if not self.graph.has_node(n_hardness): self.graph.add_node(n_hardness, layer=4, type='hardness', value=h)

            # Add Edges
            self.graph.add_edge(n_steel, n_time, time=t)
            self.graph.add_edge(n_time, n_temp, temperature=tmp)
            self.graph.add_edge(n_temp, n_hardness)
            self.graph.add_edge(n_hardness, 'SINK') 

    def _prune_graph(self, filters):
        """
        Graph Pruning Algorithm.
        Removes nodes that do not meet the criteria.
        """
        pruned_graph = self.graph.copy()
        nodes_to_remove = set()
        
        comp_filters = {k: v for k, v in filters.items() if '%wt' in k}
        exact_filters = {k: v for k, v in filters.items() if '%wt' not in k and '_range' not in k}

        for node, data in pruned_graph.nodes(data=True):
            if data.get('type') == 'steel':
                for col, op_val in comp_filters.items():
                    if col not in data: continue 
                    
                    if isinstance(op_val, dict):
                        op = op_val.get('op')
                        val = op_val.get('val')
                    else: continue

                    steel_val = data[col]
                    try:
                        if (op == '>' and not steel_val > val) or \
                           (op == '<' and not steel_val < val) or \
                           (op == '==' and not steel_val == val):
                            nodes_to_remove.add(node); break
                    except Exception: continue

                if node in nodes_to_remove: continue 
                
                for col, val in exact_filters.items():
                    if col in data:
                        if data[col] != val:
                            nodes_to_remove.add(node); break
                    
        pruned_graph.remove_nodes_from(nodes_to_remove)

        nodes_to_remove = set()
        range_filters = {'time': filters.get('time_range'), 'temp': filters.get('temperature_range'), 'hardness': filters.get('hardness_range')}
        
        for node, data in pruned_graph.nodes(data=True):
            node_type = data.get('type')
            if node_type in range_filters:
                f = range_filters[node_type]
                if f and not (f['min'] <= data.get('value', -1) <= f['max']):
                    nodes_to_remove.add(node)
        pruned_graph.remove_nodes_from(nodes_to_remove)
        
        target_nodes = [n for n, d in pruned_graph.nodes(data=True) if d.get('type') == 'hardness']
        if not target_nodes: return None

        nodes_from_source = set(nx.descendants(pruned_graph, 'SOURCE'))
        nodes_to_target = set()
        for target in target_nodes:
            try: nodes_to_target.update(nx.ancestors(pruned_graph, target))
            except nx.NetworkXNoPath: continue
            
        valid_nodes = nodes_from_source & nodes_to_target
        valid_nodes.add('SOURCE') 
        valid_nodes.update(target_nodes) 
        
        sorted_nodes = sorted(list(valid_nodes))
        
        return pruned_graph.subgraph(sorted_nodes)

    def find_best_process(self, filters, optimize_by='time', alpha=0.5):
        """
        Main algorithm: Pruning + Dijkstra Optimization.
        """
        if self.graph is None: return "Master graph not built.", 0, None, None

        pruned_graph = self._prune_graph(filters)
        if pruned_graph is None or pruned_graph.number_of_nodes() <= 1: 
            return f"No steel found matching criteria.", 0, None, None
            
        weighted_graph = nx.DiGraph()
        sorted_nodes = sorted(pruned_graph.nodes())
        for n in sorted_nodes:
            weighted_graph.add_node(n, **pruned_graph.nodes[n])
            
        for u in sorted_nodes:
            neighbors = sorted(pruned_graph.successors(u))
            for v in neighbors:
                edge_data = pruned_graph[u][v].copy()
                edge_data['weight'] = 0.0
                
                if optimize_by == 'time' and 'time' in edge_data: 
                    edge_data['weight'] = edge_data['time']
                elif optimize_by == 'temperature' and 'temperature' in edge_data: 
                    edge_data['weight'] = edge_data['temperature']
                elif optimize_by == 'balanced':
                    if 'time' in edge_data:
                        norm_time = edge_data['time'] / self.max_time
                        edge_data['weight'] = alpha * norm_time
                    elif 'temperature' in edge_data:
                        norm_temp = edge_data['temperature'] / self.max_temp
                        edge_data['weight'] = (1 - alpha) * norm_temp
                
                weighted_graph.add_edge(u, v, **edge_data)
        
        final_target_nodes = [n for n, d in weighted_graph.nodes(data=True) if d.get('type') == 'hardness']
        final_target_nodes.sort()
        
        if not final_target_nodes: return "No complete path found.", 0, None, None

        best_path = None
        best_cost = float('inf')

        for target in final_target_nodes:
            try:
                cost = nx.shortest_path_length(weighted_graph, 'SOURCE', target, 'weight')
                if cost < best_cost:
                    best_cost = cost
                    best_path = nx.shortest_path(weighted_graph, 'SOURCE', target, 'weight')
            except nx.NetworkXNoPath: continue 

        if best_path is None: return f"No reachable path found.", 0, None, None

        if len(best_path) < 5:
             return f"Internal Error: Invalid path length.", 0, None, None

        n_steel_data = weighted_graph.nodes[best_path[1]]
        n_time_data = weighted_graph.nodes[best_path[2]]
        n_temp_data = weighted_graph.nodes[best_path[3]]
        n_hardness_data = weighted_graph.nodes[best_path[4]]
        
        comp_cols = [c for c in self.df.columns if '%wt' in c]
        composition_dict = {}
        for k, v in n_steel_data.items():
            if k in comp_cols:
                try: composition_dict[k] = float(v)
                except (TypeError, ValueError): composition_dict[k] = 0.0

        result_details = {
            'Found Steel': n_steel_data.get('steel_type', 'Unknown'),
            'Final Hardness (HRC)': n_hardness_data['value'],
            'Temp (C)': n_temp_data['value'],
            'Time (s)': n_time_data['value'],
            'Composition': composition_dict
        }
        
        return best_path, best_cost, pruned_graph, result_details

    def get_master_graph(self): return self.graph