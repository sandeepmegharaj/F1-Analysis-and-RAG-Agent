"""Build the Chroma knowledge index. Run from project root: python scripts/build_vector_index.py"""
from f1_agent.rag import build_index
if __name__=='__main__': print(build_index())
