"""Persistent Chroma semantic retrieval over local Markdown/text knowledge files."""
from pathlib import Path
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .config import ROOT,secret
KB=ROOT/'knowledge_base'; DB=Path(secret('CHROMA_DIR','rag','chroma_dir',str(ROOT/'chroma_db')))
COLLECTION=secret('CHROMA_COLLECTION','rag','chroma_collection','f1_knowledge')

class LocalChromaEmbeddings(Embeddings):
    def __init__(self):
        import chromadb.utils.embedding_functions as ef
        self._fn = ef.DefaultEmbeddingFunction()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        res = self._fn(texts)
        return [[float(v) for v in row] for row in res]

    def embed_query(self, text: str) -> list[float]:
        res = self._fn([text])
        return [float(v) for v in res[0]]

def embeddings():
    azure_key = secret('AZURE_OPENAI_KEY','azure_openai')
    azure_endpoint = secret('AZURE_OPENAI_ENDPOINT','azure_openai')
    azure_deployment = secret('AZURE_OPENAI_EMBEDDING_DEPLOYMENT','azure_openai')
    if azure_key and azure_endpoint and azure_deployment:
        from langchain_openai import AzureOpenAIEmbeddings
        api_ver = secret('AZURE_OPENAI_API_VERSION','azure_openai',default='2024-02-15-preview')
        try:
            emb = AzureOpenAIEmbeddings(azure_endpoint=azure_endpoint, api_key=azure_key, azure_deployment=azure_deployment, api_version=api_ver)
            emb.embed_query('test')
            return emb
        except Exception:
            pass
    openai_key = secret('OPENAI_API_KEY','openai','api_key')
    if openai_key and not openai_key.startswith('6JRl'):
        try:
            return OpenAIEmbeddings(model=secret('OPENAI_EMBEDDING_MODEL','openai','embedding_model','text-embedding-3-small'),api_key=openai_key)
        except Exception:
            pass
    return LocalChromaEmbeddings()
def load_source_docs():
    docs=[]
    for p in sorted(KB.rglob('*')):
        if p.is_file() and p.suffix.lower() in {'.md','.txt'}:
            text=p.read_text(encoding='utf-8',errors='ignore').strip()
            if text: docs.append(Document(page_content=text,metadata={'source':p.relative_to(KB).as_posix()}))
    return docs
def _split(docs):
    mode=(secret('CHUNKING_STRATEGY','rag','chunking_strategy','recursive') or 'recursive').lower()
    if mode=='semantic':
        try:
            from langchain_experimental.text_splitter import SemanticChunker
            return SemanticChunker(embeddings(),breakpoint_threshold_type='percentile').split_documents(docs)
        except Exception as e: raise RuntimeError('Semantic chunking failed. Check embedding access/dependencies, or explicitly choose recursive chunking.') from e
    splitter=RecursiveCharacterTextSplitter(chunk_size=int(secret('CHUNK_SIZE','rag','chunk_size',900)),chunk_overlap=int(secret('CHUNK_OVERLAP','rag','chunk_overlap',120)),add_start_index=True)
    return splitter.split_documents(docs)
def build_index():
    docs=load_source_docs()
    if not docs: raise RuntimeError(f'No .md/.txt files found in {KB}.')
    chunks=_split(docs)
    if not chunks: raise RuntimeError('Chunking produced no documents.')
    DB.mkdir(parents=True,exist_ok=True); emb=embeddings()
    try: Chroma(collection_name=COLLECTION,embedding_function=emb,persist_directory=str(DB)).delete_collection()
    except Exception: pass
    Chroma.from_documents(chunks,emb,collection_name=COLLECTION,persist_directory=str(DB))
    return {'sources':len(docs),'chunks':len(chunks),'path':str(DB),'strategy':secret('CHUNKING_STRATEGY','rag','chunking_strategy','recursive')}
def get_store():
    if not DB.exists() or not any(DB.iterdir()):
        try:
            build_index()
        except Exception as e:
            raise RuntimeError(f"Chroma index is missing and auto-build failed: {e}. Build it from the app sidebar first.") from e
    return Chroma(collection_name=COLLECTION,embedding_function=embeddings(),persist_directory=str(DB))
def retrieve(query,k=5):
    return [{'text':d.page_content,'source':d.metadata.get('source','unknown')} for d in get_store().similarity_search(query,k=int(k))]
