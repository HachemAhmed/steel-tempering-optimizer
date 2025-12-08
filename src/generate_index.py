"""
Generates index.html automatically from consultas.json
targetting GitHub Pages structure (docs/ folder).
"""
import json
import os
import config

def format_filters_to_html(filters):
    """
    Converts filter dictionary to readable HTML for the query card.
    """
    lines = []
    
    if 'hardness_range' in filters:
        h = filters['hardness_range']
        lines.append(f"Target: <strong>{h.get('min', '?')}-{h.get('max', '?')} HRC</strong>")
    
    if 'temperature_range' in filters:
        t = filters['temperature_range']
        lines.append(f"Temp: {t.get('min', '?')}-{t.get('max', '?')} °C")
    
    if 'time_range' in filters:
        tm = filters['time_range']
        if tm.get('min') == tm.get('max'):
            lines.append(f"Time: {tm.get('min')}s (Fixed)")
        else:
            lines.append(f"Time: {tm.get('min')}-{tm.get('max')}s")

    elements = []
    for key, val in filters.items():
        if '(%wt)' in key:
            op = val.get('op', '=')
            v = val.get('val', 0)
            clean_key = key.split()[0]
            elements.append(f"{clean_key} {op} {v}%")
    
    if elements:
        lines.append("Comp: " + ", ".join(elements))
        
    if 'steel_type' in filters:
        lines.append(f"Steel: <strong>{filters['steel_type']}</strong>")

    return "<br>".join(lines)

def get_badge_color(optimize_by):
    """Retorna classes ou estilos baseados no tipo de otimização"""
    if optimize_by == 'time':
        return 'linear-gradient(135deg, #FF9966 0%, #FF5E62 100%)' # Laranja/Vermelho
    elif optimize_by == 'temperature':
        return 'linear-gradient(135deg, #56CCF2 0%, #2F80ED 100%)' # Azul gelo
    elif optimize_by == 'balanced':
        return 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)' # Verde
    return '#667eea' # Padrão Roxo

def generate_index_html():
    """
    Lê consultas.json e gera o docs/index.html com o design avançado.
    """
    try:
        # Define caminhos
        # Assume que o script roda da raiz ou src, ajusta para salvar em 'docs/'
        project_root = os.getcwd()
        if os.path.basename(project_root) == 'src':
            project_root = os.path.dirname(project_root)
            
        docs_dir = os.path.join(project_root, 'docs')
        os.makedirs(docs_dir, exist_ok=True)
        
        output_html_path = os.path.join(docs_dir, 'index.html')

        # Lê as consultas
        with open(config.QUERIES_PATH, 'r', encoding='utf-8') as f:
            queries = json.load(f)
        
        # --- HTML HEADER & CSS ---
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Steel Heat Treatment Optimization - Interactive Results</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        header h1 { font-size: 2.5em; margin-bottom: 10px; }
        header p { font-size: 1.2em; opacity: 0.9; }
        .content { padding: 40px; }
        .info-box {
            background: #f8f9fa;
            border-left: 5px solid #667eea;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 4px;
        }
        .query-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }
        .query-card {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 25px;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        .query-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.15);
            border-color: #667eea;
        }
        .badge {
            display: inline-block;
            padding: 5px 12px;
            color: white;
            border-radius: 20px;
            font-size: 0.85em;
            margin-bottom: 15px;
            font-weight: bold;
            align-self: flex-start;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .query-card h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3em;
            line-height: 1.4;
        }
        .description {
            color: #555;
            font-size: 0.95em;
            margin-bottom: 20px;
            line-height: 1.6;
            background: #f9f9f9;
            padding: 10px;
            border-radius: 8px;
        }
        .btn {
            display: block;
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            text-decoration: none;
            border-radius: 8px;
            transition: opacity 0.3s;
            font-weight: bold;
        }
        .btn:hover { opacity: 0.9; }
        footer {
            background: #f1f2f6;
            padding: 20px;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
            border-top: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔥 Steel Heat Treatment Optimization</h1>
            <p>Interactive Visualization of Dijkstra-Based Process Selection</p>
        </header>
        
        <div class="content">
            <div class="info-box">
                <h2>📊 Project Overview</h2>
                <p>
                    Below are the results of algorithmic searches for optimal heat treatment processes based on varying constraints.
                    Click on any card to explore the solution space heatmap.
                </p>
            </div>
            
            <div class="query-grid">
"""
        
        # --- LOOP PARA GERAR CARDS DINAMICAMENTE ---
        for query in queries:
            q_name = query.get('query_name', 'Unnamed')
            opt_by = query.get('optimize_by', 'Standard')
            filters = query.get('filters', {})
            
            # Formatações
            display_name = q_name.replace('_', ' ')
            badge_bg = get_badge_color(opt_by)
            desc_html = format_filters_to_html(filters)
            
            # Link para o arquivo HTML (que está na pasta heatmaps)
            # O link é relativo: heatmaps/Nome_Do_Arquivo.html
            link_ref = f"heatmaps/{q_name}_heatmap.html"
            
            card_html = f"""
                <div class="query-card">
                    <span class="badge" style="background: {badge_bg}">{opt_by.capitalize()} Opt</span>
                    <h3>{display_name}</h3>
                    <div class="description">
                        {desc_html}
                    </div>
                    <a href="{link_ref}" class="btn" target="_blank">View Heatmap →</a>
                </div>
            """
            html_content += card_html

        # --- FOOTER ---
        html_content += """
            </div> </div> <footer>
            <p>Generated automatically via Python | Steel Optimization Research</p>
        </footer>
    </div>
</body>
</html>
"""
        
        # Salva o arquivo final
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Fancy Index HTML generated successfully: {output_html_path}")
        return True
        
    except Exception as e:
        print(f"ERROR generating index.html: {e}")
        return False

if __name__ == "__main__":
    generate_index_html()