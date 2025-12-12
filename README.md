# Otimização de Processos de Revenimento em Aços via Algoritmos de Caminho Mínimo em Grafos

## 📄 Artigo Relacionado

Este repositório contém o código-fonte e os datasets utilizados no trabalho:
[**Otimização de Processos de Revenimento em Aços via Algoritmos de Caminho Mínimo em Grafos**](https://github.com/HachemAhmed/steel-tempering-optimizer/blob/main/artigo/Otimiza%C3%A7%C3%A3o_de_Processos_de_Revenimento_em_A%C3%A7os_via_Algoritmos_de_Caminho_M%C3%ADnimo_em_Grafos.pdf)

## 📌 Visão Geral

Este projeto propõe uma abordagem determinística para a otimização do tratamento térmico de revenimento utilizando Teoria dos Grafos. O sistema modela o espaço de soluções (Tempo × Temperatura) como um Grafo Dirigido Acíclico (DAG) e aplica o algoritmo de Dijkstra para encontrar rotas ótimas de processamento.

As principais funcionalidades incluem:

* **Modelagem Topológica:** Transformação de dados experimentais em uma estrutura sequencial (Fonte → Aço → Tempo → Temperatura → Dureza).
* **Otimização Multiobjetivo:** Minimização de custos baseada em Tempo, Temperatura ou uma abordagem Balanceada (via Escalarização Linear).
* **Filtragem Avançada:** Seleção de ligas por composição química (ex: `%C > 0.4`, `%Cr > 0.9`) e faixas de dureza alvo (HRC).
* **Análise de Robustez:** Geração de mapas de calor (*heatmaps*) para identificação de janelas de processo seguras.

## ⚙️ Instalação e Configuração

### 1️⃣ Pré-requisitos

Certifique-se de ter instalado:

* Python (>=3.8)
* Git

### 2️⃣ Clonar o repositório

```bash
git clone https://github.com/HachemAhmed/steel-tempering-optimizer.git
cd steel-tempering-optimizer
```

### 3️⃣ Instalar dependências

Recomenda-se criar um ambiente virtual para isolar as bibliotecas.

**Linux / macOS**

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows**

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 🚀 Executando o Projeto

1. **Configuração da Consulta (`consultas.json`)**

O sistema é data-driven. Configure os parâmetros de busca e filtros no arquivo JSON antes de executar. Exemplo de configuração:

```json
{
  "query_name": "Teste_Otimizacao_Balanceada",
  "optimize_by": "balanced",
  "alpha": 0.5,
  "filters": {
    "hardness_range": {"min": 50, "max": 55},
    "C (%wt)": {"op": ">", "val": 0.4}
  }
}
```

2. **Execução do Pipeline Principal**

Para rodar o processamento de dados, construção do grafo e busca do caminho mínimo:

```bash
python src/run_project.py
```

## 📚 Bibliotecas Utilizadas

As principais dependências do projeto são:

* `networkx`: Modelagem de grafos e algoritmo de Dijkstra.
* `pandas`: Manipulação de dados e ETL.
* `numpy`: Cálculos numéricos e funções logarítmicas.
* `matplotlib` & `seaborn`: Visualização de dados estática.
* `plotly`: Geração de mapas de calor interativos.

## 🔗 Saídas (Outputs)

Após a execução, os artefatos são gerados na pasta `output/`:

* **Relatórios de Rotas:** Detalhes técnicos da melhor rota encontrada (Liga, Temp, Tempo).
* **Heatmaps Interativos:** Arquivos .html para análise exploratória do espaço de soluções.
* **Grafos Exportáveis:** Arquivos formatados para visualização avançada no Gephi.

Autores: Ahmed Amer Hachem & Álvaro Augusto José Silva

DECOM-DV / CEFET-MG
