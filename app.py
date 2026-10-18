from pathlib import Path
import os, re
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
KB = ROOT / "knowledge_base"
KB.mkdir(exist_ok=True)
st.set_page_config(page_title="Apex | F1 Data Assistant", page_icon="🏁", layout="wide", initial_sidebar_state="expanded")
CSS = """
<style>
:root{--bg:#090b10;--panel:#10141d;--line:#252c39;--muted:#9aa5b5;--text:#edf1f7;--accent:#e84b59;--mint:#76e0c1}
html,body,[data-testid="stAppViewContainer"]{background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
[data-testid="stHeader"]{background:transparent}[data-testid="stMainBlockContainer"]{max-width:1320px;padding:2rem 2.1rem 5rem}
[data-testid="stSidebar"]{background:#0d1017;border-right:1px solid var(--line)}[data-testid="stSidebar"]>div{padding-top:1rem}
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;letter-spacing:-.035em;color:#f4f6fa}.stMarkdown p,.stMarkdown li{color:#c7cfdb;line-height:1.65}
.hero{padding:1.55rem 1.7rem;border:1px solid #293141;border-radius:18px;background:radial-gradient(ellipse at 90% 0%,rgba(232,75,89,.15),transparent 38%),linear-gradient(135deg,#131923,#0e121a);margin:0 0 1.35rem}
.eyebrow{font-size:.71rem;letter-spacing:.16em;text-transform:uppercase;color:var(--mint);font-weight:700}.hero h1{font:700 clamp(1.8rem,4vw,2.7rem) Inter,ui-sans-serif,system-ui,sans-serif;letter-spacing:-.05em;margin:.35rem 0}.hero p{color:#aab4c3;margin:0;max-width:720px}
.card{background:linear-gradient(145deg,#131925,#10141c);border:1px solid var(--line);border-radius:15px;padding:1.05rem 1.15rem;margin-bottom:.75rem}.card h3{font-size:1rem;margin:.1rem 0 .45rem}.card p{color:#aeb8c8;font-size:.9rem;margin:0}.tag{display:inline-block;border:1px solid #394354;color:#aebbd0;border-radius:999px;padding:.2rem .6rem;font-size:.72rem;margin:.15rem .2rem .1rem 0}.node{border:1px solid #30394a;background:#131925;border-radius:12px;padding:.85rem .9rem;margin:.25rem 0;text-align:center}.node strong{color:#f3f5f8}.arrow{text-align:center;color:#718095;font-size:1.15rem;line-height:1.2}.phase{border-left:2px solid #e84b59;padding:.15rem 0 .25rem 1rem;margin:.4rem 0 1rem}.phase b{color:#f5f6f9}.small{color:#8f9bad;font-size:.8rem}.brand{font:700 1.15rem Inter,ui-sans-serif,system-ui,sans-serif;letter-spacing:-.04em}.brand span{color:#ed5965}.status{display:inline-flex;align-items:center;gap:.45rem;border:1px solid #273342;background:#111822;padding:.35rem .65rem;border-radius:99px;color:#b8c4d4;font-size:.75rem}.dot{height:7px;width:7px;border-radius:50%;background:#70d8b6;display:inline-block}
[data-testid="stChatMessage"]{background:#111620;border:1px solid #252d3a;border-radius:14px;padding:.65rem .9rem}[data-testid="stChatInput"]{background:#10151e;border-color:#30394a;border-radius:16px}hr{border-color:#252c39!important}
button,[data-testid=stFileUploader],.node,.card{transition:border-color .18s ease,background-color .18s ease,transform .18s ease}
.node:hover,.card:hover{border-color:#465267}
[data-testid=stSidebar] label{font-weight:600}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{transition:none!important;scroll-behavior:auto!important}}

@media(max-width:700px){[data-testid="stMainBlockContainer"]{padding:1.1rem .8rem 4rem}.hero{padding:1.2rem}.card{padding:.85rem}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def secret(name, section=None, key=None, default=None):
    val = os.getenv(name)
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

def get_docs():
    docs=[]
    for p in sorted(KB.rglob('*')):
        if p.is_file() and p.suffix.lower() in {'.md','.txt'}:
            try: docs.append((p.relative_to(KB).as_posix(),p.read_text(encoding='utf-8',errors='ignore')))
            except OSError: pass
    return docs

def retrieve(question, docs=None, k=4):
    from f1_agent.rag import retrieve as semantic_retrieve
    try: return [(x['source'],x['text']) for x in semantic_retrieve(question,k)]
    except Exception as e:
        # Keep explicit error visible: no silent downgrade to keyword search.
        raise RuntimeError(str(e)) from e

def ask(question,docs=None):
    azure_key = secret('AZURE_OPENAI_KEY', 'azure_openai')
    azure_endpoint = secret('AZURE_OPENAI_ENDPOINT', 'azure_openai')
    openai_key = secret('OPENAI_API_KEY', 'openai')
    if not azure_key and not openai_key:
        return '**Setup needed:** add Azure OpenAI or OpenAI credentials to private environment or Streamlit secrets.'
    try: hits=retrieve(question,docs)
    except Exception as e: return '**RAG setup issue:** '+str(e)
    context='\n\n'.join('SOURCE: '+n+'\n'+text[:5000] for n,text in hits) if hits else ''
    if azure_key and azure_endpoint:
        from openai import AzureOpenAI
        client = AzureOpenAI(
            api_key=azure_key,
            azure_endpoint=azure_endpoint,
            api_version=secret('AZURE_OPENAI_API_VERSION', 'azure_openai', default='2024-02-15-preview')
        )
        model = secret('AZURE_OPENAI_DEPLOYMENT', 'azure_openai', default='gpt-4o')
    else:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        model = secret('OPENAI_CHAT_MODEL', 'openai', default='gpt-4o')
    system_prompt = (
        'You are Apex, an expert Formula 1 and data intelligence assistant. '
        'When relevant knowledge excerpts are provided below, synthesize them directly and cite their filenames in square brackets like [filename.md]. '
        'For general Formula 1 questions, driver stats, rules, circuits, countries, or historical records, provide an accurate, high-quality response.'
    )
    user_prompt = f"Question: {question}" + (f"\n\nRetrieved excerpts:\n{context}" if context else "")
    resp=client.chat.completions.create(model=model,temperature=.2,messages=[
      {'role':'system','content':system_prompt},
      {'role':'user','content':user_prompt}])
    return resp.choices[0].message.content or 'No answer returned.'

def hero(kicker,title,subtitle):
    st.markdown('<section class="hero"><div class="eyebrow">'+kicker+'</div><h1>'+title+'</h1><p>'+subtitle+'</p></section>',unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand">APEX<span> / F1</span></div><div class="small">DATA INTELLIGENCE</div>',unsafe_allow_html=True)
    st.markdown('---')
    section=st.radio('WORKSPACE',['RAG Agent','Architecture and Phase 1','Knowledge files'],label_visibility='collapsed')
    st.markdown('---')
    docs=get_docs()
    st.markdown('<span class="status"><i class="dot"></i>'+str(len(docs))+' knowledge files indexed</span>',unsafe_allow_html=True)
    st.caption('Dark, focused F1 data assistant')
    if st.button('Build / refresh semantic index', use_container_width=True):
        try:
            from f1_agent.rag import build_index
            with st.spinner('Embedding knowledge files and updating Chroma…'): result=build_index()
            st.success(f"Indexed {result['sources']} files into {result['chunks']} chunks ({result['strategy']}).")
        except Exception as e: st.error(str(e))

if section=='RAG Agent':
    with st.expander('Gold data • read-only SQL tool'):
        st.caption('DuckDB reads configured local Delta folders by default. Databricks SQL Warehouse is optional; only configure confirmed table mappings and private credentials.')
        if st.button('Inspect configured Gold schemas'):
            try:
                from f1_agent.sql_tools import discover_schema
                st.code(discover_schema())
            except Exception as e: st.error(str(e))
        sqlq=st.text_area('SQL (SELECT only)',placeholder='SELECT * FROM fact_results LIMIT 10',height=90)
        if st.button('Run read-only query'):
            try:
                from f1_agent.sql_tools import query_gold
                result=query_gold(sqlq); st.caption(result['backend'])
                st.dataframe(result['rows'],column_config=None,use_container_width=True) if not result['columns'] else st.dataframe(__import__('pandas').DataFrame(result['rows'],columns=result['columns']),use_container_width=True)
            except Exception as e: st.error(str(e))
    hero('FORMULA 1 • KNOWLEDGE ASSISTANT','Ask the data. Explore the race.','A focused RAG experience for questions grounded in your F1 knowledge files. Answers cite the files they use.')
    st.markdown('<span class="tag">RAG assistant</span><span class="tag">Source-grounded</span><span class="tag">F1 2024</span>',unsafe_allow_html=True)
    if 'messages' not in st.session_state: st.session_state.messages=[]
    if not st.session_state.messages: st.markdown('<div class="card"><h3>Start with a question</h3><p>Try: Explain the Gold layer, or What is the role of the RAG knowledge base? The agent uses retrieved knowledge files.</p></div>',unsafe_allow_html=True)
    for m in st.session_state.messages:
        with st.chat_message(m['role']): st.markdown(m['content'])
    prompt=st.chat_input('Ask about F1 data, the agent, or the architecture…')
    if prompt:
        st.session_state.messages.append({'role':'user','content':prompt})
        with st.chat_message('user'): st.markdown(prompt)
        with st.chat_message('assistant'):
            with st.spinner('Searching your knowledge files…'):
                try: answer=ask(prompt,get_docs())
                except Exception as e: answer='Request failed: '+type(e).__name__+'. Check your API key, model name, and network connection.'
            st.markdown(answer)
        st.session_state.messages.append({'role':'assistant','content':answer})
    if st.button('Clear conversation'): st.session_state.messages=[]; st.rerun()
elif section=='Architecture and Phase 1':
    hero('SYSTEM OVERVIEW','Architecture and Phase 1','Complete data engineering and recruiter-facing AI application architecture.')
    st.markdown('### End-to-end system architecture')
    from pathlib import Path
    img1 = Path('docs/images/f1_system_architecture.png')
    if img1.exists():
        st.image(str(img1), caption='Formula 1 AI Data Engineering & Intelligent Q&A System', use_container_width=True)
    img2 = Path('docs/images/f1_agent_architecture.png')
    if img2.exists():
        st.markdown('### Recruiter-facing agent architecture')
        st.image(str(img2), caption='Recruiter-Facing Agent Architecture & Tool Routing', use_container_width=True)
    st.markdown('### Workflow breakdown')
    flow=[('1 · User question','A recruiter asks a structured, knowledge-based, or hybrid question.'),('2 · Intent and tool routing','The agent chooses analytical data (SQL), reference knowledge (RAG), or both.'),('3 · Tool execution','SQL queries Gold analytical tables; RAG retrieves relevant F1 knowledge documents.'),('4 · LLM synthesis','The language model combines tool results and explains the answer with evidence.'),('5 · Answer','The UI presents a concise response and source references in chat.')]
    for title,desc in flow: st.markdown('<div class="node"><strong>'+title+'</strong><br><span class="small">'+desc+'</span></div><div class="arrow">↓</div>',unsafe_allow_html=True)
    st.markdown('### Phase 1 · Databricks Medallion data engineering')
    st.caption('These describe the project architecture; this starter is not connected to your Databricks workspace.')
    phases=[('Raw Excel files','2024 circuits, races, drivers, constructors, results, and sprint results. Preserve an unchanged source copy and record its origin.'),('Bronze · raw landing','Load source sheets into Delta tables with ingestion metadata. Preserve source values and make reruns traceable.'),('Silver · clean and conformed','Standardize names and types, trim strings, handle blanks and invalid values, check duplicates and key integrity, and quarantine records for review.'),('Gold · analytics-ready','Publish dimensions such as dim_races, dim_drivers, dim_constructors and fact_results. Distinguish race and sprint sessions with session_type.'),('Serve the AI application','Expose Gold data to a SQL tool for numeric questions. Keep narrative knowledge documents in the separate RAG pipeline.')]
    for title,desc in phases: st.markdown('<div class="phase"><b>'+title+'</b><br><span class="small">'+desc+'</span></div>',unsafe_allow_html=True)
    with st.expander('How the answer paths differ'):
        st.markdown('**SQL:** counts, rankings, comparisons, and numeric questions. The agent should validate a query against the available Gold schema.\n\n**RAG:** explanations grounded in prose notes (circuit, driver, or project documentation).\n\n**Hybrid:** combine measured results from SQL with contextual explanation from RAG.')
    with st.expander('Databricks concepts for an interview'):
        st.markdown('- **Workspace:** collaborative environment for notebooks, jobs, and data tools.\n- **Unity Catalog:** governance for discovering and controlling access to catalogs, schemas, tables, and volumes.\n- **Catalog → schema → table:** common three-part namespace, for example catalog.schema.table; use names actually present in your workspace.\n- **Delta Lake:** table format with transaction-log capabilities for reliable writes and schema controls.\n- **Medallion architecture:** Bronze preserves source, Silver improves quality, Gold is shaped for analytics. It is a design pattern, not an automatic Databricks feature.')
elif section=='Knowledge files':
    hero('RAG SOURCES','Knowledge files','Browse local reference files used by retrieval. Add Markdown or text documents; they stay on your machine.')
    uploaded=st.file_uploader('Add reference notes',type=['md','txt'],accept_multiple_files=True)
    if uploaded:
        for f in uploaded: (KB/Path(f.name).name).write_bytes(f.getvalue())
        st.success('Saved '+str(len(uploaded))+' file(s) in knowledge_base/.'); st.rerun()
    docs=get_docs()
    if not docs: st.info('No knowledge documents yet. Add .md or .txt files to knowledge_base/ or upload them above.')
    for name,text in docs:
        with st.expander('⌁  '+name+'  ·  '+format(len(text),',')+' characters'):
            st.code(text[:6000]+('\n… preview truncated' if len(text)>6000 else ''),language='markdown')
    st.markdown('---')
    st.caption('This starter uses lightweight keyword retrieval for speed. Replace retrieve() with your production vector-store retriever (for example Chroma) when connecting your existing RAG pipeline.')
