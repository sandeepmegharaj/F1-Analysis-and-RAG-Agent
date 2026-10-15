# F1 AI data project — architecture notes

## Two connected workstreams
Phase 1 is the data engineering platform in Databricks. Phase 2 is an AI question-answering application that uses analytical tables and narrative knowledge documents through separate tools.

## Phase 1: medallion flow
- Source: Excel workbook with circuits, races, drivers, constructors, results, and sprint_results. Keep a source copy and track provenance.
- Bronze: raw landing in Delta tables. Preserve source values and include ingestion lineage so inputs can be traced.
- Silver: clean and conform data. Normalize field names and types, handle blanks and invalid values deliberately, investigate duplicates and key relationships, and quarantine questionable records rather than silently dropping them.
- Gold: publish analytics-ready dimensions (dim_races, dim_drivers, dim_constructors) and a fact_results table. Keep race and sprint result rows distinguishable with session_type. Verify grain, keys, row counts, and joins against actual workspace data.

These are project design notes. Actual Databricks objects, schema, counts, and successful execution need verification in the user's workspace.

## Phase 2: answer paths
- SQL tool: best for counts, rankings, comparisons, and structured numeric questions against Gold data. Validate generated SQL and restrict it to read-only access.
- RAG tool: retrieves relevant passages from circuit, driver, constructor, or project notes and supplies them as context to the language model.
- Hybrid question: combine measured Gold-table facts with retrieved narrative context.
- Agent: route the question to the relevant tool(s), synthesize their evidence, and return a clear answer with citations.

## Data platform concepts
Databricks organizes governed data through Unity Catalog namespaces commonly written catalog.schema.table. Use names verified in the workspace; examples in project notes are not proof of the user's namespace. Delta Lake provides a transaction-log-based table format. Medallion is an architectural pattern: Bronze retains source, Silver improves quality, and Gold serves analytics.
