"""
Core module for steel heat treatment process optimization.
Constructs a directed graph representing all possible treatment paths
and uses Dijkstra's algorithm to find optimal processes.
"""
import pandas as pd
import numpy as np
import networkx as nx
import logging
import config

class SteelGraph:
    """
    Represents steel heat treatment processes as a multi-layer directed graph.
    Graph layers: SOURCE -> Steel Type -> Time -> Temperature -> Hardness -> SINK
    """
    
    def __init__(self, preprocessed_data_path):
        """
        Initializes the graph from preprocessed CSV data.
        
        Args:
            preprocessed_data_path: Path to the cleaned CSV file
            
        Raises:
            FileNotFoundError: If data file doesn't exist
            Exception: If data loading or graph construction fails
        """
        try:
            self.df = pd.read_csv(preprocessed_data_path)
            
            # Convert numeric columns and drop invalid rows
            cols_to_check = [config.DB_CONFIG.COL_TIME, config.DB_CONFIG.COL_TEMP, config.DB_CONFIG.COL_HARDNESS]
            cols_to_check += [c for c in self.df.columns if config.DB_CONFIG.KEY_COMPOSITION in c]
            
            for col in cols_to_check:
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            
            self.df.dropna(subset=[config.DB_CONFIG.COL_TIME, config.DB_CONFIG.COL_TEMP], inplace=True)

            # Store normalization factors for balanced optimization
            max_time = self.df[config.DB_CONFIG.COL_TIME].max()
            max_temp = self.df[config.DB_CONFIG.COL_TEMP].max()
            
            self.max_time = max_time if (not np.isnan(max_time) and max_time > 0) else 1.0
            self.max_temp = max_temp if (not np.isnan(max_temp) and max_temp > 0) else 1.0
            self.log_max_time = np.log(max(self.max_time, 1.0))
            
            # Validate log_max_time is positive
            if self.log_max_time <= 0:
                logging.warning(f"Invalid log_max_time: {self.log_max_time}, setting to 1.0")
                self.log_max_time = 1.0

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
        """
        Normalizes string keys for consistent comparison.
        Removes whitespace, special characters, and converts to lowercase.
        
        Example: "C (%wt)" -> "c_wt"
        """
        return key.strip().lower().replace(" ", "_").replace("(", "").replace(")", "").replace("%", "").replace("wt", "")

    def _build_master_graph(self):
        """
        Constructs the complete multi-layer directed graph from dataframe.
        
        Graph structure:
        - Layer 0: SOURCE node
        - Layer 1: Steel type nodes (with composition data)
        - Layer 2: Time nodes (unique per row)
        - Layer 3: Temperature nodes (unique per row)
        - Layer 4: Hardness nodes (final property)
        - Layer 5: SINK node
        """
        if self.df is None: 
            return
            
        self.graph.add_node('SOURCE', layer=0)
        self.graph.add_node('SINK', layer=5) 
        
        # Extract composition columns grouped by steel type
        comp_cols = [c for c in self.df.columns if config.DB_CONFIG.KEY_COMPOSITION in c]
        steel_compositions = self.df.groupby(config.DB_CONFIG.COL_STEEL).first()[comp_cols]
        
        for i, row in self.df.iterrows():
            s = row[config.DB_CONFIG.COL_STEEL]
            t = row[config.DB_CONFIG.COL_TIME]
            tmp = row[config.DB_CONFIG.COL_TEMP]
            h = row[config.DB_CONFIG.COL_HARDNESS]

            # Create unique node names (time/temp/hardness need ID to avoid collisions)
            n_steel = f"Steel: {s}"
            n_time = f"Time: {t} s | id:{i}"  
            n_temp = f"Temp: {tmp} C | id:{i}" 
            n_hardness = f"Hardness: {h} HRC" 

            # Add steel node with composition data (once per steel type)
            if not self.graph.has_node(n_steel):
                comp_data = steel_compositions.loc[s].to_dict() 
                
                node_attrs = {}
                node_attrs['steel_type'] = s
                node_attrs['steel_type_normalized'] = s.strip().lower()  # For case-insensitive comparison
                
                # Store normalized composition keys for filtering
                for k, v in comp_data.items():
                    node_attrs[self._normalize_key(k)] = v
                
                self.graph.add_node(n_steel, layer=1, type='steel', **node_attrs)
                self.graph.add_edge('SOURCE', n_steel) 
            
            # Add process nodes
            if not self.graph.has_node(n_time): 
                self.graph.add_node(n_time, layer=2, type='time', value=t)
            if not self.graph.has_node(n_temp): 
                self.graph.add_node(n_temp, layer=3, type='temp', value=tmp)
            if not self.graph.has_node(n_hardness): 
                self.graph.add_node(n_hardness, layer=4, type='hardness', value=h)

            # Connect nodes with edge weights
            self.graph.add_edge(n_steel, n_time, time=t)
            self.graph.add_edge(n_time, n_temp, temperature=tmp)
            self.graph.add_edge(n_temp, n_hardness)
            self.graph.add_edge(n_hardness, 'SINK') 

    def _prune_graph(self, filters):
        """
        Creates a filtered subgraph based on query constraints.
        
        Args:
            filters: Dictionary with filter criteria:
                - 'steel_type': Exact steel name (case-insensitive)
                - 'time_range': {'min': x, 'max': y}
                - 'temperature_range': {'min': x, 'max': y}
                - 'hardness_range': {'min': x, 'max': y}
                - Composition filters: {'op': '>', 'val': 0.5}
                
        Returns:
            NetworkX DiGraph: Filtered subgraph or None if no valid paths exist
        """
        pruned_graph = self.graph.copy()
        nodes_to_remove = set()
        
        # Normalize all filter keys consistently
        special_keys_normalized = {'time_range', 'temperature_range', 'hardness_range', 'steel_type'}
        normalized_filters = {}
        
        for k, v in filters.items():
            normalized_key = self._normalize_key(k)
            normalized_filters[normalized_key] = v

        df_comp_keys = [self._normalize_key(c) for c in self.df.columns if config.DB_CONFIG.KEY_COMPOSITION in c]

        # Step 1: Filter steel nodes by type and composition
        for node, data in pruned_graph.nodes(data=True):
            if data.get('type') == 'steel':
                remove_node = False
                
                for filt_key, op_val in normalized_filters.items():
                    
                    # Steel type filter (case-insensitive)
                    if filt_key == 'steel_type':
                        node_type_normalized = data.get('steel_type_normalized', '').strip().lower()
                        filter_type_normalized = str(op_val).strip().lower()
                        
                        if node_type_normalized != filter_type_normalized:
                            remove_node = True
                            break
                    
                    # Composition filters (C, Cr, Mn, etc.)
                    elif filt_key in df_comp_keys:
                        steel_val = data.get(filt_key)
                        
                        if steel_val is None:
                            remove_node = True
                            break
                        
                        if isinstance(op_val, dict):
                            op = op_val.get('op')
                            val = op_val.get('val')
                            try:
                                if (op == '>' and not steel_val > val) or \
                                   (op == '<' and not steel_val < val) or \
                                   (op == '==' and not steel_val == val) or \
                                   (op == '>=' and not steel_val >= val) or \
                                   (op == '<=' and not steel_val <= val):
                                    remove_node = True
                                    break
                            except (TypeError, ValueError):
                                remove_node = True
                                break
                
                if remove_node:
                    nodes_to_remove.add(node)

        pruned_graph.remove_nodes_from(nodes_to_remove)

        # Step 2: Filter by range constraints (time, temperature, hardness)
        nodes_to_remove = set()
        range_filters = {
            'time': normalized_filters.get('time_range'), 
            'temp': normalized_filters.get('temperature_range'), 
            'hardness': normalized_filters.get('hardness_range')
        }
        
        for node, data in pruned_graph.nodes(data=True):
            node_type = data.get('type')
            if node_type in range_filters:
                f = range_filters[node_type]
                if f:
                    node_value = data.get('value', -1)
                    
                    if 'min' not in f or 'max' not in f:
                        logging.warning(f"Invalid range filter for {node_type}: {f}")
                        continue
                    
                    if not (f['min'] <= node_value <= f['max']):
                        nodes_to_remove.add(node)
        
        pruned_graph.remove_nodes_from(nodes_to_remove)
        
        # Step 3: Remove orphaned nodes (nodes not reachable from SOURCE to any hardness target)
        target_nodes = [n for n, d in pruned_graph.nodes(data=True) if d.get('type') == 'hardness']
        if not target_nodes: 
            return None

        nodes_from_source = set(nx.descendants(pruned_graph, 'SOURCE'))
        nodes_to_target = set()
        for target in target_nodes:
            try: 
                nodes_to_target.update(nx.ancestors(pruned_graph, target))
            except nx.NetworkXNoPath: 
                continue
            
        valid_nodes = nodes_from_source & nodes_to_target
        valid_nodes.add('SOURCE') 
        valid_nodes.update(target_nodes) 
        
        sorted_nodes = sorted(list(valid_nodes))
        return pruned_graph.subgraph(sorted_nodes)

    def find_best_process(self, filters, optimize_by='time', alpha=0.5):
        """
        Finds optimal heat treatment process(es) using Dijkstra's algorithm.
        
        Args:
            filters: Query filter constraints
            optimize_by: Optimization criterion ('time', 'temperature', 'balanced')
            alpha: Time weight for balanced optimization (0-1, default: 0.5)
            
        Returns:
            On success: (paths_list, total_cost, pruned_graph, details_list)
            On failure: (error_string, 0, None, [])
        """
        if self.graph is None: 
            return "Master graph not built.", 0, None, []

        pruned_graph = self._prune_graph(filters)
        if pruned_graph is None or pruned_graph.number_of_nodes() <= 1: 
            return f"No steel found matching criteria.", 0, None, []
            
        # Create weighted graph for Dijkstra's algorithm
        weighted_graph = nx.DiGraph()
        sorted_nodes = sorted(pruned_graph.nodes())
        for n in sorted_nodes: 
            weighted_graph.add_node(n, **pruned_graph.nodes[n])
            
        # Assign edge weights based on optimization criterion
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
                    # Normalized weighted sum: alpha*log(time) + (1-alpha)*temp
                    if 'time' in edge_data:
                        time_val = max(edge_data['time'], 1.0)
                        norm_time = np.log(time_val) / self.log_max_time
                        edge_data['weight'] = alpha * norm_time
                    elif 'temperature' in edge_data:
                        norm_temp = edge_data['temperature'] / self.max_temp
                        edge_data['weight'] = (1 - alpha) * norm_temp
                
                weighted_graph.add_edge(u, v, **edge_data)
        
        # Find all hardness targets and their costs
        final_target_nodes = [n for n, d in weighted_graph.nodes(data=True) if d.get('type') == 'hardness']
        final_target_nodes.sort()
        if not final_target_nodes: 
            return "No complete path found.", 0, None, []

        min_global_cost = float('inf')
        targets_with_min_cost = []

        # Find minimum cost across all targets (handles ties with tolerance)
        for target in final_target_nodes:
            try:
                cost = nx.shortest_path_length(weighted_graph, 'SOURCE', target, 'weight')
                tolerance = max(1e-4, cost * 1e-6)  # Robust floating-point comparison
                
                if cost < min_global_cost - tolerance:
                    min_global_cost = cost
                    targets_with_min_cost = [target]
                elif abs(cost - min_global_cost) <= tolerance:
                    targets_with_min_cost.append(target)
            except nx.NetworkXNoPath: 
                continue 

        if min_global_cost == float('inf'): 
            return f"No reachable path found.", 0, None, []

        # Extract all optimal paths and their details
        all_optimal_paths = []
        all_details = []

        for target in targets_with_min_cost:
            try:
                paths = list(nx.all_shortest_paths(weighted_graph, 'SOURCE', target, weight='weight'))
                for path in paths:
                    # Validate path structure
                    if len(path) < 5: 
                        logging.warning(f"Invalid path length: {len(path)}")
                        continue
                    
                    try:
                        n_steel_data = weighted_graph.nodes[path[1]]
                        n_time_data = weighted_graph.nodes[path[2]]
                        n_temp_data = weighted_graph.nodes[path[3]]
                        n_hardness_data = weighted_graph.nodes[path[4]]
                        
                        # Verify node types
                        if n_steel_data.get('type') != 'steel' or \
                           n_time_data.get('type') != 'time' or \
                           n_temp_data.get('type') != 'temp' or \
                           n_hardness_data.get('type') != 'hardness':
                            logging.warning(f"Invalid path structure: {path}")
                            continue
                    except (KeyError, IndexError) as e:
                        logging.warning(f"Error accessing path nodes: {e}")
                        continue
                    
                    all_optimal_paths.append(path)
                    
                    # Extract composition data (map normalized keys back to original column names)
                    composition_dict = {}
                    for key, value in n_steel_data.items():
                        for original_col in self.df.columns:
                            if config.DB_CONFIG.KEY_COMPOSITION in original_col:
                                if self._normalize_key(original_col) == key:
                                    try:
                                        composition_dict[original_col] = float(value)
                                    except (TypeError, ValueError):
                                        logging.warning(f"Invalid composition value for {original_col}: {value}")
                                    break
                            
                    detail = {
                        'Found Steel': n_steel_data.get('steel_type', 'Unknown'),
                        'Final Hardness (HRC)': n_hardness_data['value'],
                        'Temp (C)': n_temp_data['value'],
                        'Time (s)': n_time_data['value'],
                        'Composition': composition_dict
                    }
                    all_details.append(detail)
            except nx.NetworkXNoPath: 
                continue

        # Sort results by steel name for consistent output
        combined = sorted(zip(all_optimal_paths, all_details), key=lambda x: x[1]['Found Steel'])
        if not combined: 
            return "Error extracting paths.", 0, None, []
        
        final_paths, final_details = zip(*combined)
        return list(final_paths), min_global_cost, pruned_graph, list(final_details)

    def get_master_graph(self): 
        """Returns the complete unfiltered graph."""
        return self.graph