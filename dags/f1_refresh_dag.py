"""Optional Apache Airflow DAG. Install Airflow separately; this is not required by Streamlit."""
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

def validate_gold():
    from f1_agent.sql_tools import discover_schema
    print(discover_schema())

def refresh_rag():
    from f1_agent.rag import build_index
    print(build_index())

with DAG(dag_id='f1_gold_and_rag_refresh',start_date=datetime(2024,1,1),schedule=None,catchup=False,tags=['f1','rag']) as dag:
    gold_check=PythonOperator(task_id='validate_configured_gold',python_callable=validate_gold)
    rag=PythonOperator(task_id='rebuild_chroma_index',python_callable=refresh_rag)
    gold_check >> rag
