# Data Pipeline

This document describes the data processing pipeline for Lean Explore.

## Overview

The pipeline processes Lean 4 code to create a searchable database with semantic embeddings.

## Pipeline Stages

### 1. Extraction

Lean scripts in `extractor/` extract:
- Declarations and metadata
- Dependencies between declarations
- AST information

### 2. Database Population

`populate_db.py` loads data into SQLite:
- Declarations
- Statement groups
- Dependencies
- Source locations

### 3. Enhancement

- **Primary Declarations**: `update_primary_declarations.py` assigns primary declarations to groups
- **PageRank**: `pagerank.py` calculates importance scores

### 4. LLM Processing

- **English Descriptions**: `lean_to_english.py` generates natural language descriptions
- **Summaries**: `get_summaries.py` creates concise summaries

### 5. Embedding Generation

- **Prepare Input**: `prepare_embedding_input.py` formats text for embedding
- **Generate Embeddings**: `generate_embeddings.py` creates vector embeddings
- **Build Index**: `build_faiss_index.py` creates FAISS search index

### 6. Manifest Generation

`generate_manifest.py` creates manifest files for publishing data.

## Data Flow

```
Lean Code
    ↓
Extractor Scripts
    ↓
JSONL Files (declarations, dependencies, AST)
    ↓
populate_db.py
    ↓
SQLite Database
    ↓
update_primary_declarations.py
    ↓
pagerank.py
    ↓
lean_to_english.py
    ↓
get_summaries.py
    ↓
prepare_embedding_input.py
    ↓
generate_embeddings.py
    ↓
build_faiss_index.py
    ↓
FAISS Index + Database
    ↓
generate_manifest.py
    ↓
Published Data
```

## Configuration

Pipeline configuration is managed through:
- `config.yml`: Main configuration file
- `extractor/extractor_config.json`: Extractor configuration
- Environment variables for API keys and model selection

## Next Steps

- [Scripts](scripts.md) - Individual script documentation
- [Contributing](contributing.md) - How to contribute

