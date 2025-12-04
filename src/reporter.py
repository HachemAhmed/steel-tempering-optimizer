"""
Report generation module for optimization results.
Creates technical reports in TXT format detailing query results.
"""

def generate_text_report(filepath, query_name, optimize_by, filters, result_data, alpha=0.5):
    """
    Writes a technical report to a TXT file.
    Handles both successful results (list of paths) and failures (error string).
    
    Args:
        filepath: Output file path for the report
        query_name: Name of the query being executed
        optimize_by: Optimization criterion ('time', 'temperature', 'balanced')
        filters: Dictionary of applied filters
        result_data: Either tuple (paths, cost, graph, details) or error string
        alpha: Weight for time in balanced optimization (default: 0.5)
    """
    # Determine if result is success or failure
    if isinstance(result_data, tuple):
        paths, custo, _, details_list = result_data
        status = "SUCCESS"
    else:
        status = "FAILURE"
        error_msg = result_data

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write(f"TECHNICAL REPORT: {query_name}\n")
        f.write("="*60 + "\n\n")
        
        # Section 1: Search Parameters
        f.write("1. SEARCH PARAMETERS\n")
        f.write("-" * 30 + "\n")
        f.write(f"Optimization Goal: {optimize_by.upper()} (Minimize)\n")
        if optimize_by == 'balanced':
            f.write(f"Alpha (Time Weight): {alpha}\n")
            f.write(f"Beta (Temp Weight): {1-alpha:.1f}\n")

        f.write("Filters Applied:\n")
        for k, v in filters.items():
            val_str = str(v)
            if isinstance(v, dict):
                if 'min' in v: 
                    val_str = f"{v['min']} - {v['max']}"
                elif 'op' in v: 
                    val_str = f"{v['op']} {v['val']}"
            f.write(f"  - {k}: {val_str}\n")
        f.write("\n")
        
        # Section 2: Optimization Results
        f.write("2. OPTIMIZATION RESULTS (DIJKSTRA)\n")
        f.write("-" * 30 + "\n")
        
        if status == "FAILURE":
            f.write(f"STATUS: NOT FOUND\n")
            f.write(f"Reason: {error_msg}\n")
        else:
            # Determine cost unit based on optimization type
            unit = "s" if optimize_by == 'time' else "C" if optimize_by == 'temperature' else "(Score)"
            f.write(f"STATUS: {len(paths)} OPTIMAL SOLUTION(S) FOUND\n")
            f.write(f"Total Cost: {custo:.2f} {unit}\n\n")
            
            # Detail each solution option
            for idx, (path, detalhes) in enumerate(zip(paths, details_list)):
                f.write(f"--- OPTION #{idx + 1} ---\n")
                
                # Clean path node names for display
                caminho_limpo = []
                for node in path:
                    clean_name = node.split("|")[0].strip() if "|" in node else node
                    if clean_name == 'SOURCE': clean_name = 'Start'
                    if clean_name == 'SINK': clean_name = 'End'
                    caminho_limpo.append(clean_name)
                
                f.write("Process Flow:\n")
                f.write(" -> ".join(caminho_limpo) + "\n\n")
                
                # Write steel specifications
                f.write("Selected Steel Specs:\n")
                f.write(f"  Steel Type:        {detalhes.get('Found Steel')}\n")
                f.write(f"  Final Hardness:    {detalhes.get('Final Hardness (HRC)')} HRC\n")
                f.write(f"  Temp Process:      {detalhes.get('Temp (C)')} C\n")
                f.write(f"  Time Process:      {detalhes.get('Time (s)')} s\n")
                
                # Write composition if available
                if 'Composition' in detalhes:
                    f.write(f"  Composition (%):\n")
                    for elem, qtd in detalhes['Composition'].items():
                        cln = elem.replace(" (%wt)", "")
                        f.write(f"    {cln:<4}: {qtd}\n")
                f.write("\n")
        
        f.write("="*60 + "\n")