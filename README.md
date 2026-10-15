# Apex F1 — Streamlit recruiter demo starter

A polished, dark, responsive Streamlit starter with three sections: RAG Agent, Architecture and Phase 1, and Knowledge files. The architecture is rendered as native UI text and cards, not as an image.

## Run locally
1. Extract the ZIP and open this folder in your IDE.
2. Create and activate a Python virtual environment (recommended).
3. Install: python -m pip install -r requirements.txt
4. Copy .env.example to .env and add your own OPENAI_API_KEY; optionally set OPENAI_MODEL. The app reads environment variables.
5. Add project/circuit/driver reference notes as .md or .txt under knowledge_base/, or upload them through Knowledge files.
6. Start: streamlit run app.py

## What works
- Responsive Streamlit UI with sidebar navigation, chat, and a file-explorer-style knowledge browser.
- Basic RAG loop: keyword retrieval over local Markdown/text files, passing retrieved excerpts to OpenAI, and asking for filenames as citations.
- Interactive Architecture and Phase 1 section explaining SQL, RAG, and hybrid routes and the Databricks Bronze/Silver/Gold flow.
- API key is read from the environment locally or Streamlit secrets when hosted. No key is embedded in source.

## Honest integration boundary
This is a UI and basic retrieval starter. It does not include a live Databricks SQL connection, DuckDB Gold-table connector, Chroma vector index, or the reference repository's agent implementation. The lightweight keyword retriever is intentionally simple so the app can run quickly. To connect your existing agent, replace ask() with a call to your agent/backend, and replace retrieve() with its vector-store retriever. Keep API keys on the server and use read-only data permissions.

For Streamlit Community Cloud, add OPENAI_API_KEY in App settings → Secrets; do not commit .env or secrets.toml. Before publishing, ensure the host can access the knowledge documents and has permission to use any data it serves.

The Phase 1 text follows the architecture reference supplied by the user and prior conversation context. It is explanatory UI content, not independent verification of Databricks tables or counts. This starter does not copy source files from the referenced GitHub repository; review its reuse terms and attribute upstream work if you later integrate it.
