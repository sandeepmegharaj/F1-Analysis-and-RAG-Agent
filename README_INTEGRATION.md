# Integrated F1 assistant additions

This extends the existing Streamlit app in-place. The former keyword retriever now uses persistent Chroma semantic vector retrieval; app UI includes a read-only Gold SQL panel. No upstream repository code was copied. The referenced repo had no declared license in the inspected metadata, so this implementation is independently written and does not remove/strip third-party license requirements.

## Install and run
Python 3.10+ recommended. From project root: 

```sh
python -m venv .venv
# activate it, then:
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```
Set the OpenAI credential privately as OPENAI_API_KEY (or .streamlit/secrets.toml using the example). A GPT chat key and embedding endpoint typically use the same OpenAI API credential, subject to project permissions, billing, and model access. The default embedding model is text-embedding-3-small. Never paste keys into source control.

On app sidebar choose **Build / refresh semantic index**. Default chunking is recursive, not semantic boundary detection. Set CHUNKING_STRATEGY=semantic to enable LangChain SemanticChunker, which calls the embedding API and may need additional dependency compatibility. Chroma persistence is in chroma_db/ (ignored by Git).

## Gold SQL
Default is local Delta: place actual Delta table folders in data/dim_races, data/dim_drivers, data/dim_constructors, data/fact_results, or set GOLD_DATA_DIR. Each must contain _delta_log. These names/layout are expected defaults, not a statement your exported Gold objects use them. The SQL panel refuses mutation statements and limits result rows.

For direct SQL Warehouse access set GOLD_BACKEND=databricks_sql and private settings DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN plus GOLD_TABLES mapping logical names to actual fully-qualified catalog.schema.table names, e.g. JSON mapping in environment. Do not infer names: confirm in your workspace first. Use a dedicated least-privilege identity/token, rotate it if exposed, and restrict network/access.

## Optional orchestration
`dags/f1_refresh_dag.py` is an optional Airflow DAG to validate configured Gold access then rebuild Chroma. Airflow is not in the lightweight app dependencies and the DAG has not been run. No Bronze/Silver/Gold transformation pipeline is invented here: the project does not include verified source schemas or confirmed mappings. No credentials are supplied.

## Honest scope / verification
The app provides code paths for LangChain model routing by explicit SQL-vs-RAG UI, DuckDB local Delta queries, Chroma retrieval, OpenAI embeddings, SQL Warehouse connectivity, and optional Airflow tasks. It does not include live credentials/data, actual table-name configuration, nor end-to-end service validation. Build index requires OpenAI embedding access. If API permissions for embedding are absent, resolve through the provider project settings rather than sharing keys.
