# Scripts

The `scripts/` directory contains utilities for processing Lean code data, generating embeddings, and building search indices.

## Overview

See the [Scripts README](../../scripts/README.md) for detailed documentation on all scripts.

## Key Scripts

### Data Processing

- **`populate_db.py`**: Populates the database from Lean declaration files
- **`update_primary_declarations.py`**: Updates primary declaration assignments
- **`pagerank.py`**: Calculates PageRank scores for declarations

### Embeddings and Search

- **`prepare_embedding_input.py`**: Prepares text for embedding generation
- **`generate_embeddings.py`**: Generates vector embeddings from text
- **`build_faiss_index.py`**: Builds FAISS search index from embeddings

### LLM Processing

- **`lean_to_english.py`**: Generates English descriptions using LLMs
- **`get_summaries.py`**: Generates summaries for statement groups

### Documentation

- **`generate_docs_data.py`**: Generates documentation data
- **`generate_manifest.py`**: Creates manifest files for data toolchains

## Pipeline

The typical data processing pipeline:

1. Extract Lean declarations (using Lean scripts in `extractor/`)
2. Populate database: `populate_db.py`
3. Update primary declarations: `update_primary_declarations.py`
4. Calculate PageRank: `pagerank.py`
5. Generate English descriptions: `lean_to_english.py`
6. Generate summaries: `get_summaries.py`
7. Prepare embedding input: `prepare_embedding_input.py`
8. Generate embeddings: `generate_embeddings.py`
9. Build FAISS index: `build_faiss_index.py`
10. Generate manifest: `generate_manifest.py`

## Next Steps

- [Data Pipeline](data-pipeline.md) - Detailed pipeline documentation
- [Contributing](contributing.md) - How to contribute

