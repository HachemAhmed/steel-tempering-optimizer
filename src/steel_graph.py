import pandas as pd
import numpy as np
import networkx as nx
import os
import logging

# --- CENTRALIZED CONFIGURATION ---
# Single source of truth for column names to avoid magic strings.
class DB_CONFIG:
    COL_STEEL = 'Steel type'
    COL_TIME = 'Tempering time (s)'
    COL_TEMP = 'Tempering temperature (ºC)'
    COL_HARDNESS = 'Final hardness (HRC) - post tempering'
    KEY_COMPOSITION = '%wt' 

class SteelGraph:
    def __init__(self, preprocessed_data_path):
        """
        Initializes the optimization engine.
        Loads data, enforces types, and pre-calculates metrics for normalization.
        """
        try:
            self.df = pd.read_csv(preprocessed_data_path)
            
            # 1. Data Hardening: Force numeric types to prevent crashes during comparison
            cols_to_check = [DB_CONFIG.COL_TIME, DB_CONFIG.COL_TEMP, DB_CONFIG.COL_HARDNESS]
            cols_to_check += [c for c in self.df.columns if DB_CONFIG.KEY_COMPOSITION in c]
            
            for col in cols_to_check:
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            
            # Remove rows that became NaN after coercion
            self.df.dropna(subset=[DB_CONFIG.COL_TIME, DB_CONFIG.COL_TEMP], inplace=True)

            # 2. Pre-calculate Max Values for Weighted Sum Normalization
            # Protected against NaN/Zero to avoid DivisionByZero errors
            max_time = self.df[DB_CONFIG.COL_TIME].max()
            max_temp = self.df[DB_CONFIG.COL_TEMP].max()
            
            self.max_time = max_time if (not np.isnan(max_time) and max_time > 0) else 1.0
            self.max_temp = max_temp if (not np.isnan(max_temp) and max_temp > 0) else 1.0
            
            # Pre-calculate Log Max for Time (Handles orders of magnitude: 10s vs 100,000s)
            self.log_max_time = np.log(max(self.max_time, 1.0))

            self.graph = nx.DiGraph() 
            self._build_master_graph()
        except FileNotFoundError:
            logging.critical(f"Data file not found: {preprocessed_data_path}")
            self.df = None
            self.graph = None
            raise 
        except Exception as e:
            logging.critical(f"Data initialization error: {e}")
            raise

    def _normalize_key(self, key):
        """Helper: Normalizes dictionary keys (lowercase, no spaces) for robust filtering."""
        return key.strip().lower().replace(" ", "_").replace("(", "").replace(")", "").replace("%", "").replace("wt", "")

    def _build_master_graph(self):
        """
        Builds the Master Graph representing the entire solution space.
        
        ARCHITECTURAL DECISION: UNIQUE NODES
        We create UNIQUE nodes for intermediate steps (Time, Temp) using row IDs (e.g., 'Time: 10s | id:5').
        This prevents 'Phantom Paths', ensuring the algorithm cannot mix parameters from different 
        steel processes (e.g., starting with Steel A but using Steel B's temperature curve).
        """
        if self.df is None: return
            
        self.graph.add_node('SOURCE', layer=0)
        self.graph.add_node('SINK', layer=5) 
        
        # Efficiently fetch static composition data
        comp_cols = [c for c in self.df.columns if DB_CONFIG.KEY_COMPOSITION in c]
        steel_compositions = self.df.groupby(DB_CONFIG.COL_STEEL).first()[comp_cols]
        
        for i, row in self.df.iterrows():
            s = row[DB_CONFIG.COL_STEEL]
            t = row[DB_CONFIG.COL_TIME]
            tmp = row[DB_CONFIG.COL_TEMP]
            h = row[DB_CONFIG.COL_HARDNESS]

            # Unique Identifiers (English)
            n_steel = f"Steel: {s}"
            n_time = f"Time: {t} s | id:{i}"  
            n_temp = f"Temp: {tmp} C | id:{i}" 
            n_hardness = f"Hardness: {h} HRC" # Hardness is shared (Convergence Point)

            # 1. Add Steel Node (Layer 1)
            if not self.graph.has_node(n_steel):
                comp_data = steel_compositions.loc[s].to_dict() 
                comp_data['steel_type'] = s 
                
                # Add normalized attributes for easier filtering
                node_attrs = {}
                node_attrs['steel_type'] = s
                for k, v in comp_data.items():
                    node_attrs[self._normalize_key(k)] = v
                
                self.graph.add_node(n_steel, layer=1, type='steel', **node_attrs)
                self.graph.add_edge('SOURCE', n_steel) 
            
            # 2. Add Process Nodes (Layers 2-4)
            if not self.graph.has_node(n_time): self.graph.add_node(n_time, layer=2, type='time', value=t)
            if not self.graph.has_node(n_temp): self.graph.add_node(n_temp, layer=3, type='temp', value=tmp)
            if not self.graph.has_node(n_hardness): self.graph.add_node(n_hardness, layer=4, type='hardness', value=h)

            # 3. Create Path Edges
            self.graph.add_edge(n_steel, n_time, time=t)
            self.graph.add_edge(n_time, n_temp, temperature=tmp)
            self.graph.add_edge(n_temp, n_hardness)
            self.graph.add_edge(n_hardness, 'SINK') 

    def _prune_graph(self, filters):
        """
        Pruning Algorithm.
        Filters the Master Graph to remove nodes that violate user constraints.
        Returns a subgraph containing only valid paths.
        """
        pruned_graph = self.graph.copy()
        nodes_to_remove = set()
        
        normalized_filters = {self._normalize_key(k): v for k, v in filters.items()}
        df_comp_keys = [self._normalize_key(c) for c in self.df.columns if DB_CONFIG.KEY_COMPOSITION in c]

        # 1. Prune Steel Nodes (Composition & Exact Type)
        for node, data in pruned_graph.nodes(data=True):
            if data.get('type') == 'steel':
                for filt_key, op_val in normalized_filters.items():
                    # Composition Filter
                    if filt_key in df_comp_keys:
                        steel_val = data.get(filt_key)
                        if steel_val is None: continue 
                        if isinstance(op_val, dict):
                            op = op_val.get('op')
                            val = op_val.get('val')
                            try:
                                if (op == '>' and not steel_val > val) or \
                                   (op == '<' and not steel_val < val) or \
                                   (op == '==' and not steel_val == val):
                                    nodes_to_remove.add(node); break
                            except Exception: continue
                    # Exact Type Filter
                    elif filt_key == 'steel_type':
                        node_type = data.get('steel_type')
                        if node_type != op_val:
                            nodes_to_remove.add(node); break

        pruned_graph.remove_nodes_from(nodes_to_remove)

        # 2. Prune Process Nodes (Ranges)
        nodes_to_remove = set()
        range_filters = {'time': filters.get('time_range'), 'temp': filters.get('temperature_range'), 'hardness': filters.get('hardness_range')}
        
        for node, data in pruned_graph.nodes(data=True):
            node_type = data.get('type')
            if node_type in range_filters:
                f = range_filters[node_type]
                if f and not (f['min'] <= data.get('value', -1) <= f['max']):
                    nodes_to_remove.add(node)
        pruned_graph.remove_nodes_from(nodes_to_remove)
        
        # 3. Orphan Cleanup
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
        
        # Sort nodes to ensure deterministic subgraph creation structure
        sorted_nodes = sorted(list(valid_nodes))
        return pruned_graph.subgraph(sorted_nodes)

    def find_best_process(self, filters, optimize_by='time', alpha=0.5):
        """
        Main Optimization Logic:
        1. Prune Graph (Constraint Satisfaction).
        2. Reconstruct Graph Deterministically (Reproducibility).
        3. Assign Dynamic Weights (Objective Function).
        4. Run Dijkstra.
        """
        if self.graph is None: return "Master graph not built.", 0, None, None

        pruned_graph = self._prune_graph(filters)
        if pruned_graph is None or pruned_graph.number_of_nodes() <= 1: 
            return f"No steel found matching criteria.", 0, None, None
            
        # --- DETERMINISTIC RECONSTRUCTION ---
        # Instead of copying, we rebuild the graph inserting nodes/edges in strict alphabetical order.
        # This guarantees that Dijkstra's tie-breaking is always identical across runs.
        weighted_graph = nx.DiGraph()
        sorted_nodes = sorted(pruned_graph.nodes())
        for n in sorted_nodes: weighted_graph.add_node(n, **pruned_graph.nodes[n])
            
        for u in sorted_nodes:
            neighbors = sorted(pruned_graph.successors(u))
            for v in neighbors:
                edge_data = pruned_graph[u][v].copy()
                edge_data['weight'] = 0.0
                
                # Weight Assignment Logic
                if optimize_by == 'time' and 'time' in edge_data: 
                    edge_data['weight'] = edge_data['time']
                
                elif optimize_by == 'temperature' and 'temperature' in edge_data: 
                    edge_data['weight'] = edge_data['temperature']
                
                elif optimize_by == 'balanced':
                    # Weighted Sum Method:
                    # Cost = Alpha * Norm(Time) + (1-Alpha) * Norm(Temp)
                    # Time uses Logarithmic normalization due to large order of magnitude variance.
                    if 'time' in edge_data:
                        time_val = max(edge_data['time'], 1.0)
                        norm_time = np.log(time_val) / self.log_max_time
                        edge_data['weight'] = alpha * norm_time
                    elif 'temperature' in edge_data:
                        norm_temp = edge_data['temperature'] / self.max_temp
                        edge_data['weight'] = (1 - alpha) * norm_temp
                
                weighted_graph.add_edge(u, v, **edge_data)
        
        # Identify all valid targets
        final_target_nodes = [n for n, d in weighted_graph.nodes(data=True) if d.get('type') == 'hardness']
        final_target_nodes.sort()
        
        if not final_target_nodes: return "No complete path found.", 0, None, None

        # Run Dijkstra for every potential target to find global minimum
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

        # Extract Results
        n_steel_data = weighted_graph.nodes[best_path[1]]
        n_time_data = weighted_graph.nodes[best_path[2]]
        n_temp_data = weighted_graph.nodes[best_path[3]]
        n_hardness_data = weighted_graph.nodes[best_path[4]]
        
        comp_cols = [c for c in self.df.columns if DB_CONFIG.KEY_COMPOSITION in c]
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