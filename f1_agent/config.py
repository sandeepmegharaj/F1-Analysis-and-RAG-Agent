"""Configuration helpers. Secrets are read at runtime and never logged."""
from __future__ import annotations
import json, os
from pathlib import Path
import streamlit as st
ROOT=Path(__file__).resolve().parents[1]
def secret(name: str, section: str|None=None, key: str|None=None, default=None):
    val=os.getenv(name)
    if val: return val
    try:
        if section and section in st.secrets:
            sec = st.secrets[section]
            if key and key in sec: return sec[key]
            if key and key.lower() in sec: return sec[key.lower()]
            if name.lower() in sec: return sec[name.lower()]
            if name in sec: return sec[name]
        if name in st.secrets: return st.secrets[name]
        if name.lower() in st.secrets: return st.secrets[name.lower()]
    except Exception: pass
    return default
def gold_backend(): return (secret('GOLD_BACKEND','databricks','gold_backend','local_delta') or 'local_delta').lower()
def table_mapping():
    raw=secret('GOLD_TABLES','databricks','gold_tables','')
    if isinstance(raw,dict): return {str(k):str(v) for k,v in raw.items()}
    if raw:
        try: return {str(k):str(v) for k,v in json.loads(raw).items()}
        except Exception: pass
    return {}
def table_dirs():
    base=Path(secret('GOLD_DATA_DIR','databricks','gold_data_dir',str(ROOT/'data')))
    return {n:base/n for n in ('dim_races','dim_drivers','dim_constructors','fact_results')}
