# Apex F1: Data Engineering Platform and AI Knowledge Assistant

A Formula 1 data platform and analytical intelligence application combining Databricks Lakehouse architecture, Medallion ETL pipelines, Delta Lake storage, and a Retrieval-Augmented Generation (RAG) assistant.

- Live Application: https://f1agent.streamlit.app/
- Source Code: https://github.com/sandeepmegharaj/F1-Analysis-and-RAG-Agent

---

## Architecture Overview

The system operates across two interconnected phases:

1. Phase 1: Data Engineering Platform
   An end-to-end lakehouse pipeline executing raw data ingestion, transformation, schema validation, quarantine handling, and dimensional modeling across Databricks Bronze, Silver, and Gold Delta layers.

2. Phase 2: Analytics and RAG Intelligence Engine
   A hybrid serving tier combining read-only analytical SQL execution against Gold Delta tables with semantic search across an embedded vector database, synthesized through a Large Language Model.

```
[Raw Sources: Excel / Ergast API]
              |
              v
 [Databricks Bronze Layer: Raw Delta Tables + Ingestion Metadata]
              |
              v
 [Databricks Silver Layer: Conformed Types, Deduplication, Cleansing]
              |
              v
 [Databricks Gold Layer: Star Schema (Fact & Dimension Delta Tables)]
       /                              \
      v                                v
[SQL Analytics Engine]       [ChromaDB Vector Store]
(Databricks SQL / DuckDB)    (Sentence Transformers / Embeddings)
       \                              /
        v                            v
    [LLM Synthesis Tier (Azure OpenAI / OpenAI GPT-4o)]
                          |
                          v
        [Streamlit Analytical Web Interface]
```

---

## Data Engineering Architecture

### 1. Ingestion and Medallion Architecture

Data flows through a structured multi-hop architecture implemented in Databricks and Delta Lake:

#### Bronze Layer (Raw Landing)
- Ingests source datasets (circuits, races, drivers, constructors, qualifying, sprint, and race results).
- Preserves raw source records in native format with original naming.
- Appends platform ingestion metadata: `_ingestion_timestamp`, `_source_file`, `_batch_id`.
- Backed by Delta Lake transaction logs (`_delta_log`) for full lineage and auditability.

#### Silver Layer (Cleaned, Validated, and Conformed)
- Type casting and schema enforcement across temporal, numeric, and string fields.
- String normalization: trimming whitespace, case standardization, handling null values.
- Referential integrity validation: verifies foreign key consistency between races, drivers, constructors, and results.
- Quarantine logic: records with irreconcilable discrepancies or missing required surrogate keys are quarantined rather than discarded, preserving pipeline stability.
- Deduplication and business-rule validation (e.g., driver grid and finishing positions).

#### Gold Layer (Analytics-Ready Dimensional Model)
The Gold tier models data into a star schema optimized for analytical query performance and downstream BI:

- `dim_drivers`: Driver biographical details, code, permanent number, nationality, and historical reference IDs.
- `dim_constructors`: Constructor identity, nationality, lineage, and operational history.
- `dim_races`: Grand Prix calendar dimension, circuit details, round, country, coordinates, and date-time attributes.
- `fact_results`: Granular race event facts containing points, finishing position, grid position, laps completed, fastest lap time, pit stop counts, and session type differentiator (`race` vs `sprint`).

### 2. Delta Lake and Storage Engine
- ACID Transactions: Delta Lake transaction logs guarantee atomic updates and pipeline consistency during re-runs.
- Schema Enforcement: Prevents bad data writes that violate the schema definitions.
- Time Travel: Capability to query previous table versions using Delta history for regression testing and debugging.
- Storage Optimization: Parquet columnar file format with Snappy compression, partitioned by race season.

### 3. Query Execution Engines

#### Databricks SQL Warehouse (Enterprise Mode)
- Connects through the Databricks SQL execution connector via HTTP paths and personal access tokens.
- Queries run against Unity Catalog namespaces (`catalog.schema.table`).
- Read-only execution policy: Enforces strict query validation, rejecting any mutating operations (`INSERT`, `UPDATE`, `DROP`, `ALTER`, `MERGE`, `DELETE`).

#### Local DuckDB Delta Engine (Edge / Embedded Mode)
- In environments without active cluster connectivity, DuckDB loads the native `delta` extension.
- Scans local Delta tables directly via `delta_scan()` using local file paths, reading table metadata from `_delta_log`.
- Provides serverless, in-memory OLAP query speeds without requiring a running cloud cluster.

### 4. Workflow Orchestration (Apache Airflow)
Pipeline dependencies and periodic updates are orchestrated via Airflow DAGs located in `dags/`:
- `validate_configured_gold`: Verifies connectivity, table accessibility, and schema integrity across all Gold dimension and fact tables.
- `rebuild_chroma_index`: Automatically synchronizes and rebuilds semantic vector indices when knowledge files or underlying data change.

---

## Technology Stack

- Data Lakehouse Platform: Databricks, Apache Spark
- Storage and Table Format: Delta Lake, Apache Parquet
- Data Governance: Unity Catalog
- Query Engines: Databricks SQL Warehouse, DuckDB (with Delta extension)
- Orchestration: Apache Airflow
- Vector Database: ChromaDB (persistent local store)
- Embeddings: Local Sentence Transformers (`all-MiniLM-L6-v2`) and OpenAI (`text-embedding-3-small`)
- Large Language Models: Azure OpenAI Service / OpenAI GPT-4o
- RAG and Chunking Framework: LangChain, Recursive Character Text Splitter
- Application Layer: Streamlit, Python 3.10+

---

## Repository Structure

```
├── .streamlit/
│   ├── config.toml                # Dark theme UI configuration
│   └── secrets.toml.example       # Template for API keys and connection tokens
├── dags/
│   └── f1_refresh_dag.py          # Airflow DAG for Gold schema validation and index refresh
├── data/
│   ├── dim_constructors/          # Constructor dimension Delta table
│   ├── dim_drivers/               # Driver dimension Delta table
│   ├── dim_races/                 # Race dimension Delta table
│   └── fact_results/              # Race and sprint results fact Delta table
├── f1_agent/
│   ├── config.py                  # Secrets resolution and environment mappings
│   ├── rag.py                     # Chroma vector store, embedding setup, chunking, and retrieval
│   └── sql_tools.py               # Read-only SQL query runner (Databricks SQL & DuckDB Delta)
├── knowledge_base/
│   ├── f1_2024_season_and_regulations.md  # 2024 grid, teams, scoring, and sprint rules
│   ├── f1_circuits_and_countries.md       # Circuit calendar and host nations
│   ├── f1_records_and_history.md          # Driver stats, historical scoring, and championships
│   └── project_architecture.md            # System architecture and engineering notes
├── scripts/
│   └── build_vector_index.py      # Standalone vector index generation script
├── app.py                         # Streamlit application entry point
├── requirements.txt               # Project dependencies
└── README.md                      # Documentation
```

---

## Local Setup and Installation

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Environment Setup
Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/sandeepmegharaj/F1-Analysis-and-RAG-Agent.git
cd F1-Analysis-and-RAG-Agent
python -m venv .venv
```

Activate the virtual environment:
- Windows (PowerShell):
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- Linux / macOS:
  ```bash
  source .venv/bin/activate
  ```

Install required packages:
```bash
pip install -r requirements.txt
```

### 3. Configuration
Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Configuration parameters:

```ini
# OpenAI / Azure OpenAI Credentials
OPENAI_API_KEY="your-api-key"
OPENAI_CHAT_MODEL="gpt-4o"
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"

# Or Azure OpenAI
AZURE_OPENAI_KEY="your-azure-key"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT="gpt-4o"

# Vector Store Settings
CHROMA_DIR="./chroma_db"
CHUNKING_STRATEGY="recursive"
CHUNK_SIZE=900
CHUNK_OVERLAP=120

# Gold Layer Backend: 'local_delta' or 'databricks_sql'
GOLD_BACKEND=local_delta
GOLD_DATA_DIR=./data

# For Databricks SQL (Optional)
DATABRICKS_SERVER_HOSTNAME="your-databricks-host.cloud.databricks.com"
DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
DATABRICKS_TOKEN="your-pat-token"
GOLD_TABLES='{"dim_races":"catalog.schema.dim_races","dim_drivers":"catalog.schema.dim_drivers","dim_constructors":"catalog.schema.dim_constructors","fact_results":"catalog.schema.fact_results"}'
```

### 4. Build Vector Index and Run App
Run the Streamlit application:

```bash
streamlit run app.py
```

The application will initialize at `http://localhost:8501`. On initial launch, the vector store automatically processes and indexes knowledge files into ChromaDB if not already present.

---

## Security and Governance

- Credential Isolation: API keys, tokens, and warehouse endpoints are resolved from private environments or Streamlit Secrets. No credentials are committed to version control.
- Read-Only SQL Policy: Query inputs are parsed with regular expressions to prohibit data definition or data modification language (`CREATE`, `DROP`, `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `ALTER`).
- Table Access Boundaries: SQL queries are validated against permitted logical Gold table definitions to prevent arbitrary database access.
