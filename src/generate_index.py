"""
Generates index.html automatically from consultas.json
"""
import json
import os
import config

def generate_index_html():
    """
    Reads consultas.json and generates an index.html with links to all query results.
    """
    try:
        # Read queries
        with open(config.QUERIES_PATH, 'r', encoding='utf-8') as f:
            queries = json.load(f)
        
        # Start HTML
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Steel Heat Treatment Optimization - Results</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        .query-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .query-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }
        .query-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #2980b9;
            margin-bottom: 10px;
        }
        .query-filters {
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 15px;
        }
        .links {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .link-btn {
            display: inline-block;
            padding: 10px 20px;
            background-color: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 500;
            transition: background-color 0.3s;
        }
        .link-btn:hover {
            background-color: #2980b9;
        }
        .link-btn.report {
            background-color: #95a5a6;
        }
        .link-btn.report:hover {
            background-color: #7f8c8d;
        }
        .link-btn.heatmap {
            background-color: #e74c3c;
        }
        .link-btn.heatmap:hover {
            background-color: #c0392b;
        }
        .filter-tag {
            display: inline-block;
            background-color: #ecf0f1;
            padding: 3px 8px;
            border-radius: 3px;
            margin: 2px;
            font-size: 0.85em;
        }
        footer {
            margin-top: 50px;
            text-align: center;
            color: #95a5a6;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <h1>🔬 Steel Heat Treatment Optimization Results</h1>
    <p>Automated graph-based optimization using Dijkstra's algorithm to find optimal heat treatment parameters.</p>
    
    <h2>📊 Query Results</h2>
"""
        
        # Add each query as a card
        for idx, query in enumerate(queries, 1):
            query_name = query.get('name', f'Query {idx}')
            optimize_by = query.get('optimize_by', 'time')
            filters = query.get('filters', {})
            
            # Format filters
            filter_items = []
            if filters.get('steel_type'):
                filter_items.append(f"<span class='filter-tag'>Steel: {filters['steel_type']}</span>")
            if filters.get('min_hardness'):
                filter_items.append(f"<span class='filter-tag'>Min Hardness: {filters['min_hardness']} HRC</span>")
            if filters.get('max_hardness'):
                filter_items.append(f"<span class='filter-tag'>Max Hardness: {filters['max_hardness']} HRC</span>")
            if filters.get('min_temp'):
                filter_items.append(f"<span class='filter-tag'>Min Temp: {filters['min_temp']}°C</span>")
            if filters.get('max_temp'):
                filter_items.append(f"<span class='filter-tag'>Max Temp: {filters['max_temp']}°C</span>")
            if filters.get('min_time'):
                filter_items.append(f"<span class='filter-tag'>Min Time: {filters['min_time']}s</span>")
            if filters.get('max_time'):
                filter_items.append(f"<span class='filter-tag'>Max Time: {filters['max_time']}s</span>")
            
            filter_html = "".join(filter_items) if filter_items else "<span class='filter-tag'>No filters</span>"
            
            # Create safe filename (same logic as in run_project.py)
            safe_name = query_name.replace(" ", "_").replace("/", "_")
            
            html_content += f"""
    <div class="query-card">
        <div class="query-title">{query_name}</div>
        <div class="query-filters">
            <strong>Optimization:</strong> {optimize_by.capitalize()} | 
            <strong>Filters:</strong> {filter_html}
        </div>
        <div class="links">
            <a href="output/{safe_name}_graph.png" class="link-btn" target="_blank">📈 View Graph</a>
            <a href="output/{safe_name}_report.txt" class="link-btn report" target="_blank">📄 Technical Report</a>
            <a href="output/{safe_name}_heatmap.html" class="link-btn heatmap" target="_blank">🔥 Interactive Heatmap</a>
        </div>
    </div>
"""
        
        # Close HTML
        html_content += """
    <footer>
        <p>Generated automatically from consultas.json | Steel Heat Treatment Optimization System</p>
    </footer>
</body>
</html>
"""
        
        # Write to file
        output_path = os.path.join(os.path.dirname(config.OUTPUT_DIR), 'index.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Index HTML generated: {output_path}")
        return True
        
    except FileNotFoundError:
        print(f"ERROR: consultas.json not found at {config.QUERIES_PATH}")
        return False
    except Exception as e:
        print(f"ERROR generating index.html: {e}")
        return False

if __name__ == "__main__":
    generate_index_html()