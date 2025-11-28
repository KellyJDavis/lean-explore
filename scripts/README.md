# Scripts Directory README

This directory contains scripts for processing Lean code data, generating embeddings, and building search indices. This document describes each script, their usage, execution order, and data flow between them.

## Overview

The scripts follow a pipeline workflow:
1. **Database Population**: Load Lean declarations and dependencies into a database
2. **Data Enhancement**: Update primary declarations and calculate PageRank scores
3. **LLM Processing**: Generate English descriptions and summaries
4. **Embedding Generation**: Create vector embeddings from text data
5. **Index Building**: Build a FAISS search index from embeddings
6. **Manifest Generation**: Create manifest files for publishing data toolchains

## Scripts

### 1. `populate_db.py`

**Purpose**: Populates a relational database from Lean declaration and dependency files through a multi-phase process.

**Usage**:
```bash
python scripts/populate_db.py [OPTIONS]
```

**Key Options**:
- `--db-url`: SQLAlchemy database URL (default: `sqlite:///data/lean_explore_data.db`)
- `--create-tables`: Drop existing tables and create new ones (WARNING: deletes all data)
- `--declarations-file`: Path to `declarations.jsonl` (default: `data/declarations.jsonl`)
- `--dependencies-file`: Path to `dependencies.jsonl` (default: `data/dependencies.jsonl`)
- `--ast-json-base`: Base path to `.ast.json` files (default: `data/AST`)
- `--lean-toolchain-src`: Path to Lean toolchain source files
- `--lean-lake-src`: Path to Lake packages source directory
- `--batch-size`: Records per batch commit (default: 1000)

**Phases**:
1. Initial declaration population from `declarations.jsonl`
2. Refinement of declaration source locations using `.ast.json` and `.lean` files
3. Grouping declarations into StatementGroups
4. Population of inter-declaration dependencies from `dependencies.jsonl`
5. Population of StatementGroup dependencies

**Inputs**:
- `declarations.jsonl`: Lean declaration data
- `dependencies.jsonl`: Dependency relationships
- `.ast.json` files: AST representations of Lean code
- `.lean` source files: Raw Lean source code

**Outputs**:
- Populated database with `declarations`, `statement_groups`, `dependencies`, and `statement_group_dependencies` tables

**Order**: **First** - This script must run before all others as it creates the foundational database.

---

### 2. `update_primary_declarations.py`

**Purpose**: Updates the primary declaration for each StatementGroup based on prefix relationships and hierarchical presence in code.

**Usage**:
```bash
python scripts/update_primary_declarations.py
```

**Configuration**: Edit the script to change `DATABASE_URL` and `BATCH_SIZE` constants.

**Inputs**:
- Database populated by `populate_db.py`

**Outputs**:
- Updates `primary_decl_id` and `docstring` fields in `statement_groups` table

**Order**: **After `populate_db.py`** - Optional but recommended for improving data quality.

---

### 3. `pagerank.py`

**Purpose**: Calculates and stores PageRank scores for Declarations and StatementGroups based on dependency graphs.

**Usage**:
```bash
python scripts/pagerank.py [OPTIONS]
```

**Key Options**:
- `--db-url`: Database URL (defaults to config or `sqlite:///data/lean_explore_data.db`)
- `--alpha`: PageRank damping parameter (default: 0.85)
- `--batch-size`: Database update batch size (default: 1000)
- `--skip-declarations`: Skip PageRank for Declarations
- `--skip-statement-groups`: Skip PageRank for StatementGroups

**Inputs**:
- Database with populated `dependencies` and `statement_group_dependencies` tables

**Outputs**:
- Updates `pagerank_score` column in `declarations` and `statement_groups` tables
- Updates `scaled_pagerank_score` column in `statement_groups` table (log-transformed, min-max scaled)

**Order**: **After `populate_db.py`** (and optionally after `update_primary_declarations.py`) - Optional but useful for ranking.

---

### 4. `lean_to_english.py`

**Purpose**: Generates informal English descriptions for StatementGroups using an LLM (Gemini). Processes groups in topological order based on dependencies.

**Usage**:
```bash
python scripts/lean_to_english.py --db-url <DATABASE_URL> [OPTIONS]
```

**Key Options**:
- `--db-url`: SQLAlchemy database URL (required)
- `--batch-size`: Database commit batch size (default: 50)
- `--test N`: Test mode - process N items without database writes
- `--startover`: Re-generate descriptions for all groups

**Requirements**:
- Gemini API key set in `GEMINI_API_KEY` environment variable
- Model specified in `config.yml` (e.g., `gemini-2.0-flash`)
- Prompt template file (default: `scripts/prompt_template.txt`)

**Inputs**:
- Database with populated `statement_groups` table
- Statement groups with `statement_text` field populated

**Outputs**:
- Updates `informal_description` field in `statement_groups` table

**Order**: **After `populate_db.py`** - Required before `get_summaries.py`.

---

### 5. `get_summaries.py`

**Purpose**: Generates concise, search-oriented summaries for StatementGroups using an LLM (Gemini). Optimized for discoverability.

**Usage**:
```bash
python scripts/get_summaries.py [OPTIONS]
```

**Key Options**:
- `--db-url`: Database URL (default: `sqlite:///data/lean_explore_data.db`)
- `--test N`: Test mode - process N items without database writes
- `--startover`: Re-generate summaries for all applicable groups

**Requirements**:
- Gemini API key set in `GEMINI_API_KEY` environment variable
- Model specified in `config.yml` (e.g., `gemini-2.0-flash`)
- Summary prompt template (default: `scripts/summary_prompt_template.txt`)

**Inputs**:
- Database with `statement_groups` table
- Statement groups with `informal_description` field populated (from `lean_to_english.py`)

**Outputs**:
- Updates `informal_summary` field in `statement_groups` table

**Order**: **After `lean_to_english.py`** - Requires `informal_description` field to be populated.

---

### 6. `prepare_embedding_input.py`

**Purpose**: Prepares a JSON file from StatementGroups for embedding generation. Extracts Lean code, informal descriptions, docstrings, and Lean names.

**Usage**:
```bash
python scripts/prepare_embedding_input.py [OPTIONS]
```

**Key Options**:
- `--db-url`: Database URL (defaults to config)
- `--output-file`: Output JSON file path (default: `data/embedding_input.json`)
- `--limit N`: Limit number of StatementGroups to process
- `--exclude-lean`: Exclude Lean code text
- `--exclude-english`: Exclude informal English descriptions
- `--exclude-docstrings`: Exclude docstrings
- `--exclude-lean-names`: Exclude Lean names of primary declarations

**Inputs**:
- Database with populated `statement_groups` table

**Outputs**:
- JSON file (default: `data/embedding_input.json`) with structure:
  ```json
  [
    {
      "id": "sg_123_lean",
      "source_statement_group_id": 123,
      "text_type": "lean",
      "text": "..."
    },
    ...
  ]
  ```

**Order**: **After database population** (can run after `lean_to_english.py` and `get_summaries.py` for better results).

---

### 7. `generate_embeddings.py`

**Purpose**: Generates vector embeddings from text items in a JSON file using a sentence-transformer model.

**Usage**:
```bash
python scripts/generate_embeddings.py [OPTIONS]
```

**Key Options**:
- `--input-file`: Input JSON file (default: `data/embedding_input.json`)
- `--output-file`: Output NPZ file (default: `data/generated_embeddings.npz`)
- `--model-name`: Sentence-transformer model (default: `BAAI/bge-base-en-v1.5`)
- `--device`: Device to use (`cpu`, `cuda`, `mps`) - auto-detects if not specified
- `--batch-size`: Batch size for embedding generation (default: 64)
- `--limit`: Process only first N items

**Inputs**:
- JSON file from `prepare_embedding_input.py` (default: `data/embedding_input.json`)

**Outputs**:
- NPZ file (default: `data/generated_embeddings.npz`) containing:
  - `ids`: Array of string identifiers
  - `embeddings`: 2D float32 array of embedding vectors

**Order**: **After `prepare_embedding_input.py`** - Requires the JSON output from that script.

---

### 8. `build_faiss_index.py`

**Purpose**: Builds and saves a FAISS index from generated embeddings for efficient similarity search.

**Usage**:
```bash
python scripts/build_faiss_index.py [OPTIONS]
```

**Key Options**:
- `--input-npz-file`: Input NPZ file (default: `data/generated_embeddings.npz`)
- `--output-index-file`: Output FAISS index file (default: `data/main_faiss.index`)
- `--output-map-file`: Output ID map JSON file (default: `data/faiss_ids_map.json`)
- `--faiss-index-type`: Index type - `IndexFlatL2`, `IndexFlatIP`, or `IndexIVFFlat` (default: `IndexFlatL2`)
- `--ivf-nlist`: Number of Voronoi cells for `IndexIVFFlat` (default: 100)
- `--force-cpu`: Force CPU usage even if GPU is available
- `--gpu-device`: GPU device ID to use (default: 0)

**Inputs**:
- NPZ file from `generate_embeddings.py` (default: `data/generated_embeddings.npz`)

**Outputs**:
- FAISS index file (default: `data/main_faiss.index`)
- ID map JSON file (default: `data/faiss_ids_map.json`) mapping FAISS internal IDs to original string IDs

**Order**: **After `generate_embeddings.py`** - Requires the NPZ embeddings file.

---

### 9. `generate_manifest.py`

**Purpose**: Generates a `manifest.json` file for Lean Explore data toolchains. Reads the required data files (database, FAISS index, and ID map), compresses them, calculates SHA256 checksums, and creates a manifest that can be used for publishing data to Cloudflare R2 or for local use.

**Optimization**: The script automatically reuses existing compressed files if they are present and up-to-date (i.e., the compressed file's modification time is newer than or equal to the source file's modification time). This avoids unnecessary recompression when regenerating manifests with unchanged source files.

**Usage**:
```bash
python scripts/generate_manifest.py --version <VERSION> [OPTIONS]
```

**Key Options**:
- `--data-dir`, `-d`: Directory containing the data files (default: `data`)
- `--output`, `-o`: Path where the manifest.json should be written (default: `manifest.json`)
- `--version`, `-v`: Toolchain version string, e.g., `0.3.0` (required)
- `--description`: Description of this toolchain version (defaults to `v{version}`)
- `--release-date`: Release date in YYYY-MM-DD format (defaults to today's date)
- `--assets-base-path-r2`: Base path for R2 assets, e.g., `assets/0.3.0/` (defaults to `assets/{version}/`)
- `--keep-temp`: Keep temporary compressed files after processing (for inspection)

**Inputs**:
- `lean_explore_data.db`: Database file (from `populate_db.py`)
- `main_faiss.index`: FAISS index file (from `build_faiss_index.py`)
- `faiss_ids_map.json`: ID map file (from `build_faiss_index.py`)

**Outputs**:
- `manifest.json`: Manifest file containing:
  - Toolchain version information
  - File metadata (local names, remote names, SHA256 checksums, compressed/uncompressed sizes)
  - Asset base paths for R2 storage
  - Release date and description

**Order**: **After `build_faiss_index.py`** - Requires all three data files (database, FAISS index, and ID map) to be present. This is typically the final step before publishing a data toolchain.

---

### 10. `generate_docs_data.py`

**Purpose**: Generates structured documentation data from Python source files using griffe. Independent of the database workflow.

**Usage**:
```bash
python scripts/generate_docs_data.py
```

**Configuration**: Edit constants in the script:
- `PACKAGE_PATH`: Path to Python package to document (default: `src/lean_explore`)
- `OUTPUT_PATH`: Output JSON file path (default: `data/module_data.json`)

**Inputs**:
- Python source files in the specified package directory

**Outputs**:
- JSON file (default: `data/module_data.json`) with structured documentation data for frontend consumption

**Order**: **Independent** - Can be run at any time, unrelated to the database/embedding pipeline.

---

## Execution Order

The scripts must be run in a specific order due to data dependencies. Below are the recommended execution sequences for different use cases.

### Full Pipeline (External Extraction → Database → Embeddings → Index)

**Prerequisites**: Ensure you have generated the required input files (see "External Input Sources" section below).

```bash
# 1. Populate database (must run first)
python scripts/populate_db.py --create-tables

# 2. (Optional) Update primary declarations for better data quality
python scripts/update_primary_declarations.py

# 3. (Optional) Calculate PageRank scores for ranking
python scripts/pagerank.py

# 4. Generate English descriptions (requires GEMINI_API_KEY environment variable)
python scripts/lean_to_english.py --db-url sqlite:///data/lean_explore_data.db

# 5. Generate summaries (requires GEMINI_API_KEY environment variable)
python scripts/get_summaries.py --db-url sqlite:///data/lean_explore_data.db

# 6. Prepare embedding input from database
python scripts/prepare_embedding_input.py --db-url sqlite:///data/lean_explore_data.db

# 7. Generate vector embeddings
python scripts/generate_embeddings.py --input-file data/embedding_input.json

# 8. Build FAISS search index
python scripts/build_faiss_index.py --input-npz-file data/generated_embeddings.npz

# 9. (Optional) Generate manifest for publishing
python scripts/generate_manifest.py --version 0.3.0 --data-dir data --output manifest.json
```

**Note**: Steps 2-3 are optional but recommended for better data quality. Steps 4-5 require `GEMINI_API_KEY` environment variable to be set and the model specified in `config.yml` (e.g., `gemini-2.0-flash`). Step 9 is optional and only needed if you plan to publish the data toolchain.

### Minimal Pipeline (Database Only)

If you only need the database populated without embeddings:

```bash
python scripts/populate_db.py --create-tables
```

### Embedding Pipeline Only (if database already populated)

If your database is already populated and you only need to regenerate embeddings:

```bash
python scripts/prepare_embedding_input.py
python scripts/generate_embeddings.py
python scripts/build_faiss_index.py
```

### External Input Generation

Before running step 1 above, you need to generate the input files from Lean code. This is done using the extractor scripts:

```bash
# Generate declarations and dependencies
cd extractor
lake env lean --run ExtractDeclarations.lean

# Generate AST files
lake env lean --run ExtractAST.lean processProject
cd ..
```

See the "External Input Sources" section below for more details.

---

## External Input Sources

The pipeline requires several inputs that are **not generated by the scripts themselves**. These must be prepared before running the pipeline:

### 1. `declarations.jsonl` and `dependencies.jsonl`

**Source**: Generated by Lean scripts in the `extractor/` directory.

**How to generate**:
```bash
cd extractor
lake env lean --run ExtractDeclarations.lean
```

This script:
- Analyzes Lean code from Mathlib, Batteries, Std, PhysLean, Init, Lean, and FLT
- Extracts declaration metadata (name, type, module, docstring, source location, etc.)
- Identifies direct dependencies between declarations
- Outputs to `../data/declarations.jsonl` and `../data/dependencies.jsonl`

**What it does**: `ExtractDeclarations.lean` imports the specified Lean modules, processes all declarations in the environment, and writes JSONL files with declaration and dependency information.

### 2. `.ast.json` Files

**Source**: Generated by `ExtractAST.lean` script in the `extractor/` directory.

**How to generate**:
```bash
cd extractor
lake env lean --run ExtractAST.lean processProject
```

This script:
- Processes Lean source files from configured libraries (Init, Std, Lean, Mathlib, Batteries, PhysLean)
- Extracts Abstract Syntax Trees (ASTs) for each command
- Records tactic applications and premise usage
- Outputs `.ast.json` files to `data/AST/` directory structure (mirroring source file paths)
- Also generates `.dep_paths` files listing imported modules

**What it does**: `ExtractAST.lean` traverses Lean's `InfoTree` to extract detailed trace information including command ASTs with byte spans, tactic traces, and premise traces.

**Configuration**: The script uses `extractor/extractor_config.json` to locate the Lean toolchain source directory. It also automatically discovers Lake packages in `.lake/packages/`.

### 3. `.lean` Source Files

**Source**: These are the actual Lean source code files from:

- **Lean Toolchain**: Core Lean libraries (Init, Std, Lean) located in the Lean installation's `src/lean/` directory
  - Path configured in `extractor/extractor_config.json` (`toolchainCoreSrcDir`)
  
- **Lake Packages**: Dependencies downloaded by Lake (e.g., Mathlib, Batteries, PhysLean)
  - Typically located in `.lake/packages/` within a Lean project
  - Automatically discovered by `ExtractAST.lean`

**How to obtain**:
- Lean toolchain: Installed as part of the Lean installation
- Lake packages: Automatically downloaded when you run `lake build` or `lake update` in a Lean project that depends on them

### 4. Prompt Templates

**Source**: Text files in the `scripts/` directory.

- `scripts/prompt_template.txt`: Used by `lean_to_english.py` for generating English descriptions
- `scripts/summary_prompt_template.txt`: Used by `get_summaries.py` for generating summaries

**What they are**: Template files with placeholders (e.g., `{primary_lean_name}`, `{statement_text}`) that are filled in by the scripts before sending prompts to the LLM.

**Default locations**: Can be overridden via configuration files.

### 5. Python Source Files (for `generate_docs_data.py`)

**Source**: The Python source code in `src/lean_explore/` (or whatever package path is configured).

**What they are**: The actual Python modules of the project that are parsed to generate API documentation.

### Summary of External Input Generation

Before running `populate_db.py`, you need to:

1. **Set up a Lean project** with dependencies (Mathlib, Batteries, etc.)
2. **Run the extractor scripts**:
   ```bash
   cd extractor
   # Extract declarations and dependencies
   lake env lean --run ExtractDeclarations.lean
   
   # Extract ASTs from source files
   lake env lean --run ExtractAST.lean processProject
   ```
3. **Ensure prompt templates exist** (default templates are provided in the repository)

The extractor scripts require:
- A properly configured Lean project with Lake dependencies
- `extractor/extractor_config.json` configured with toolchain source path
- Compiled Lean code (`.olean` files) for the libraries you want to extract

---

## Data Flow Summary

```
External Sources:
├─ Lean Source Code (.lean files)
│  ├─ Lean Toolchain (Init, Std, Lean)
│  └─ Lake Packages (Mathlib, Batteries, PhysLean, etc.)
│
└─ Extractor Scripts (in extractor/ directory)
   ├─ ExtractDeclarations.lean ─→ declarations.jsonl + dependencies.jsonl
   └─ ExtractAST.lean ─→ .ast.json files (in data/AST/)
   
Pipeline Inputs:
declarations.jsonl ─┐
dependencies.jsonl ─┤
.ast.json files ───┼─→ populate_db.py ─→ Database
.lean files ───────┘
                                           │
                                           ├─→ update_primary_declarations.py ─→ Database (updated)
                                           │
                                           ├─→ pagerank.py ─→ Database (with PageRank scores)
                                           │
                                           ├─→ lean_to_english.py ─→ Database (with informal_description)
                                           │
                                           ├─→ get_summaries.py ─→ Database (with informal_summary)
                                           │
                                           └─→ prepare_embedding_input.py ─→ embedding_input.json
                                                                                │
                                                                                └─→ generate_embeddings.py ─→ generated_embeddings.npz
                                                                                                                   │
                                                                                                                   └─→ build_faiss_index.py ─→ main_faiss.index + faiss_ids_map.json
                                                                                                                      │
                                                                                                                      └─→ generate_manifest.py ─→ manifest.json
```

## Requirements

### Dependencies
- Python 3.x
- SQLAlchemy
- NumPy
- NetworkX (for `pagerank.py`)
- sentence-transformers (for `generate_embeddings.py`)
- faiss-cpu or faiss-gpu (for `build_faiss_index.py`)
- PyTorch (for `generate_embeddings.py`)
- griffe (for `generate_docs_data.py`)
- tqdm (for progress bars)
- Standard library modules: `gzip`, `hashlib`, `json`, `pathlib`, `shutil` (for `generate_manifest.py`)

### Environment Variables
- **GEMINI_API_KEY**: Required for `lean_to_english.py` and `get_summaries.py`. Must be set to your Google Gemini API key. The model to use should be specified in `config.yml` under `llm.generation_model` (e.g., `gemini-2.0-flash`). Get your API key from https://aistudio.google.com/app/apikey

### Configuration
- Most scripts use `config.yml` for database URLs and other settings
- Some scripts have hardcoded defaults that can be modified

## Notes

- **Database URL**: Most scripts default to `sqlite:///data/lean_explore_data.db`. Use `--db-url` to override.
- **Test Mode**: `lean_to_english.py` and `get_summaries.py` support `--test N` to process a limited number of items without database writes (useful for testing).
- **GPU Support**: `generate_embeddings.py` and `build_faiss_index.py` support GPU acceleration when available.
- **Batch Processing**: Most database operations use batching to handle large datasets efficiently.

