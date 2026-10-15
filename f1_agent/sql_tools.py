"""Read-only DuckDB/Delta or Databricks SQL tools."""
from __future__ import annotations
import re
from .config import gold_backend, table_dirs, table_mapping, secret

def _safe_sql(sql, allowed):
    q=sql.strip()
    if not q or ';' in q or not re.match(r'^(select|with)\b',q,re.I): raise ValueError('Only one read-only SELECT or WITH query is allowed.')
    if re.search(r'\b(insert|update|delete|merge|drop|alter|create|copy|attach|detach|install|load|export|import|pragma|call|execute|use|set|vacuum)\b',q,re.I): raise ValueError('Disallowed SQL operation.')
    refs=set(re.findall(r'\b(?:from|join)\s+([\w."]+)',q,re.I))
    norm={x.strip('"').split('.')[-1].lower() for x in refs}
    if not norm or not norm.issubset({x.lower() for x in allowed}): raise ValueError('Use only configured Gold tables: '+', '.join(allowed))
    return q

def _local_conn():
    import duckdb
    con=duckdb.connect(':memory:')
    try: con.execute('LOAD delta')
    except Exception:
        try: con.execute('INSTALL delta'); con.execute('LOAD delta')
        except Exception as e: con.close(); raise RuntimeError('DuckDB Delta extension could not load; check network access and DuckDB installation.') from e
    found=[]
    for name,p in table_dirs().items():
        if p.exists() and (p/'_delta_log').exists():
            esc=str(p.resolve()).replace("'","''")
            con.execute(f"CREATE VIEW {name} AS SELECT * FROM delta_scan('{esc}')")
            found.append(name)
    if not found: con.close(); raise RuntimeError('No local Gold Delta folders found. Expected data/<table>/_delta_log. Configure GOLD_DATA_DIR or export your confirmed tables.')
    return con,found

def _dbx():
    vals=[secret('DATABRICKS_SERVER_HOSTNAME','databricks','server_hostname'),secret('DATABRICKS_HTTP_PATH','databricks','http_path'),secret('DATABRICKS_TOKEN','databricks','access_token')]
    if not all(vals): raise RuntimeError('Configure Databricks server_hostname, http_path, and access_token in private secrets.')
    return vals

def discover_schema():
    if gold_backend()=='databricks_sql':
        from databricks import sql
        mapping=table_mapping()
        if not mapping: raise RuntimeError('Set GOLD_TABLES to confirmed logical-name/catalog.schema.table mappings. Do not guess workspace names.')
        host,http,token=_dbx(); out=[]
        with sql.connect(server_hostname=host,http_path=http,access_token=token) as con:
            cur=con.cursor()
            for logical,table in mapping.items():
                cur.execute(f'SELECT * FROM {table} LIMIT 0'); out.append(f"{logical} ({table}): "+', '.join(c[0] for c in cur.description))
            cur.close()
        return '\n'.join(out)
    con,found=_local_conn()
    try: return '\n'.join(f"{n}: "+', '.join(x[0] for x in con.execute(f'DESCRIBE {n}').fetchall()) for n in found)
    finally: con.close()

def query_gold(sql_text):
    if gold_backend()=='databricks_sql':
        from databricks import sql
        mapping=table_mapping()
        if not mapping: raise RuntimeError('Set confirmed GOLD_TABLES mappings before querying.')
        q=_safe_sql(sql_text,list(mapping))
        for name,real in mapping.items(): q=re.sub(r'(?<![\w.])'+re.escape(name)+r'(?![\w])',real,q,flags=re.I)
        host,http,token=_dbx()
        with sql.connect(server_hostname=host,http_path=http,access_token=token) as con:
            cur=con.cursor(); cur.execute(q); rows=cur.fetchmany(201); cols=[c[0] for c in cur.description or []]; cur.close()
        return {'columns':cols,'rows':[list(x) for x in rows[:200]],'backend':'Databricks SQL Warehouse'}
    con,found=_local_conn()
    try:
        q=_safe_sql(sql_text,found); cur=con.execute(q); cols=[d[0] for d in cur.description or []]; rows=cur.fetchmany(201)
        return {'columns':cols,'rows':[list(x) for x in rows[:200]],'backend':'DuckDB over local Delta'}
    finally: con.close()
