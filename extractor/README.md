# Extractor Directory README

This directory contains Lean 4 scripts that extract metadata, dependencies, and AST information from Lean codebases. These scripts generate the input files required by the Python pipeline in `scripts/`.

## Overview

The extractor consists of two main scripts:
1. **`ExtractDeclarations.lean`**: Extracts declaration metadata and dependency relationships
2. **`ExtractAST.lean`**: Extracts Abstract Syntax Trees (ASTs), tactic traces, and premise usage from Lean source files

Both scripts can be run independently, but both should be executed before running the Python database population scripts.

## Prerequisites

### Required Software
- **Lean 4** (version 4.15.0, as specified in `lean-toolchain`)
- **Lake** (Lean's build tool, included with Lean 4)
- **elan** (Lean version manager, if not using system-wide Lean installation)

### Required Lean Libraries

The extractor requires access to the following Lean libraries, which are automatically downloaded via Lake when you build the project:

- **Mathlib**: Comprehensive mathematics library (`mathlib4`)
- **Batteries**: General-purpose utility library
- **PhysLean**: Physics-related concepts library
- **FLT**: Fermat's Last Theorem formalization library
- **Std**: Standard library (included with Lean)
- **Init**: Core initialization library (included with Lean)
- **Lean**: Core Lean library (included with Lean)

These dependencies are configured in `lakefile.lean`. Run `lake build` to download and compile them.

### Configuration

**`extractor_config.json`**: Specifies the path to the Lean toolchain source directory.

**Example configuration**:
```json
{
  "toolchainCoreSrcDir": "/path/to/lean/toolchain/src"
}
```

The script will fall back to the default sysroot path if this file is missing or invalid.

**Note**: The script appends `/lean` to this path to locate Init, Std, and Lean source directories (e.g., `{toolchainCoreSrcDir}/lean/Init`).

## Scripts

### 1. `ExtractDeclarations.lean`

**Purpose**: Extracts comprehensive declaration metadata and dependency relationships from Lean codebases.

**Usage**:
```bash
cd extractor
lake env lean --run ExtractDeclarations.lean
```

**What it does**:
- Imports specified Lean modules (Mathlib, Batteries, Std, PhysLean, FLT)
- Processes all declarations in the environment
- Extracts metadata for each declaration:
  - Lean name (fully qualified)
  - Declaration type (axiom, definition, theorem, inductive, etc.)
  - Module name
  - Source file path
  - Source position (line/column ranges)
  - Docstring
  - Status flags (protected, deprecated, projection, etc.)
- Identifies direct dependencies between declarations by analyzing expression types and values
- Filters out internal declarations and universe-level constants

**Outputs**:
- `../data/declarations.jsonl`: JSONL file where each line is a JSON object representing a single declaration
- `../data/dependencies.jsonl`: JSONL file where each line is a JSON object representing a dependency relationship

**Output Format**:

**declarations.jsonl** (example line):
```json
{"lean_name":"Nat.add","decl_type":"definition","module_name":"Init.Data.Nat.Basic","source_file":"Init/Data/Nat/Basic.lean","range_start_line":123,"range_start_col":5,"range_end_line":125,"range_end_col":10,"docstring":"Addition of natural numbers","is_protected":false,"is_deprecated":false,"attributes":[]}
```

**dependencies.jsonl** (example line):
```json
{"source_lean_name":"Nat.add","target_lean_name":"Nat.zero","dependency_type":"Direct"}
```

**Target Libraries**: The script processes declarations from:
- Mathlib
- Batteries
- PhysLean
- Std
- Init
- Lean
- FLT

**Performance Notes**:
- Disables heartbeat limits to prevent timeouts on large codebases
- Reports progress every 5,000 declarations
- Processing time depends on the size of the imported libraries (can take hours for large codebases)

**Requirements**:
- All required Lean libraries must be compiled (`.olean` files must exist)
- Sufficient memory for loading large environments (Mathlib can require several GB)

---

### 2. `ExtractAST.lean`

**Purpose**: Extracts Abstract Syntax Trees (ASTs), tactic application traces, and premise usage information from Lean source files.

**Usage**:
```bash
cd extractor
lake env lean --run ExtractAST.lean processProject
```

**Alternative usage** (for processing a single file, used internally):
```bash
lake env lean --run ExtractAST.lean processSingleFileTask <input_path> <ast_json_output_path> <dep_paths_output_path> <full_module_name_string>
```

**What it does**:
- Discovers all `.lean` source files in configured libraries
- For each file:
  - Parses the file and builds the Lean environment
  - Traverses Lean's `InfoTree` to extract:
    - Command ASTs with byte spans
    - Tactic applications with goal states (before/after)
    - Premise usage (definitions/theorems used and their locations)
  - Extracts import dependencies
- Processes files in parallel (up to 32 concurrent workers)
- Skips files whose `.ast.json` output already exists (resumable)

**Outputs**:
- `../data/AST/<LibraryName>/<path>/<file>.ast.json`: JSON files containing ASTs, tactic traces, and premise traces
- `../data/AST/<LibraryName>/<path>/<file>.dep_paths`: Text files listing imported module source paths

**Output Structure**: The output directory structure mirrors the source file structure within each library.

**Example**:
- Source: `.lake/packages/mathlib/Mathlib/Data/Nat/Basic.lean`
- Output AST: `../data/AST/Mathlib/Mathlib/Data/Nat/Basic.ast.json`
- Output Deps: `../data/AST/Mathlib/Mathlib/Data/Nat/Basic.dep_paths`

**Target Libraries**: The script processes files from:
- **Toolchain libraries** (from `toolchainCoreSrcDir`):
  - Init (`{toolchainCoreSrcDir}/lean/Init`)
  - Std (`{toolchainCoreSrcDir}/lean/Std`)
  - Lean (`{toolchainCoreSrcDir}/lean/Lean`)
- **Lake packages** (from `.lake/packages/`):
  - Batteries (`batteries`)
  - Mathlib (`mathlib`)
  - PhysLean (`PhysLean`)

**Configuration**: Uses `extractor_config.json` to locate the Lean toolchain source directory. Lake packages are automatically discovered.

**Performance Notes**:
- Processes files in parallel (configurable via `maxWorkers`, default: 32)
- Skips files that already have output (resumable)
- Only processes files that have corresponding `.olean` files (compiled)
- Reports progress every 10 files processed
- Can take hours to process large libraries like Mathlib

**Troubleshooting Stack Overflow**:
If you encounter "deep recursion was detected" errors:
1. **Primary solution**: Increase system stack size before running:
   ```bash
   ulimit -s 65536  # or higher (default is typically 8192 on macOS)
   cd extractor
   lake env lean --run ExtractAST.lean processProject
   ```
   Each worker process runs independently and needs sufficient stack space for processing complex files.
2. **Optional optimization**: If you have limited RAM, reducing `maxWorkers` (e.g., to 16, 8, or 4) in `ExtractAST.lean` may help with overall memory pressure, but won't fix stack overflow itself.
3. **Alternative**: Process libraries separately by modifying `getTargetLibraries` to process one at a time

**Requirements**:
- All source files must have corresponding compiled `.olean` files
- Requires significant disk space for output (can be tens of GB for large libraries)

**Output Format**:

**`.ast.json` file structure**:
```json
{
  "commandASTs": [
    {
      "commandSyntax": {...},
      "byteStart": 0,
      "byteEnd": 150
    }
  ],
  "tactics": [
    {
      "stateBefore": "...",
      "stateAfter": "...",
      "pos": 200,
      "endPos": 250
    }
  ],
  "premises": [
    {
      "fullName": "Nat.add",
      "defPos": {...},
      "defEndPos": {...},
      "modName": "Init.Data.Nat.Basic",
      "defPath": "/path/to/file.lean",
      "pos": {...},
      "endPos": {...}
    }
  ]
}
```

**`.dep_paths` file format**: Newline-separated list of absolute paths to imported module source files.

---

## Execution Order

Both scripts can be run independently, but they should both be executed before running the Python pipeline:

```bash
# 1. Ensure dependencies are downloaded and compiled
cd extractor
lake build

# 2. Extract declarations and dependencies
lake env lean --run ExtractDeclarations.lean

# 3. Extract ASTs from source files
lake env lean --run ExtractAST.lean processProject

# 4. Now you can run the Python scripts (from project root)
cd ..
python scripts/populate_db.py --create-tables
```

**Note**: The order between steps 2 and 3 doesn't matter—they can be run in parallel or in either order.

---

## External Data Sources

### Lean Toolchain Source Files

**Source**: Lean 4 installation (via elan or system installation)

**Location**: Configured in `extractor_config.json` as `toolchainCoreSrcDir`

**What it provides**:
- Source code for Init, Std, and Lean core libraries
- Required for `ExtractAST.lean` to process toolchain files

**How to obtain**:
- Automatically available if Lean 4 is installed
- The script auto-detects the sysroot if `extractor_config.json` is missing
- Update `extractor_config.json` if your toolchain is in a non-standard location

### Lake Packages

**Source**: Automatically downloaded by Lake when running `lake build`

**Location**: `.lake/packages/` directory within the extractor project

**What it provides**:
- Source code for Mathlib, Batteries, PhysLean, FLT, and other dependencies
- Required for both extractor scripts

**How to obtain**:
```bash
cd extractor
lake build  # Downloads and compiles all dependencies
```

**Dependencies configured in `lakefile.lean`**:
- `mathlib` (from `leanprover-community/mathlib4`)
- `batteries` (from `leanprover-community/batteries`)
- `PhysLean` (from `HEPLean/PhysLean`)
- `FLT` (from `ImperialCollegeLondon/FLT`)
- Additional transitive dependencies (aesop, proofwidgets, etc.)

### Compiled `.olean` Files

**Source**: Generated by Lake when compiling Lean code

**Location**: `.lake/build/lib/lean/` and `.lake/packages/*/.lake/build/lib/lean/`

**What it provides**:
- Compiled binary representations of Lean modules
- Required for `ExtractAST.lean` to determine which files are eligible for processing

**How to obtain**:
- Automatically generated when running `lake build`
- Must exist for files to be processed by `ExtractAST.lean`

---

## Data Flow

```
External Sources:
├─ Lean Toolchain (Init, Std, Lean)
│  └─ Source: Lean 4 installation
│
└─ Lake Packages (Mathlib, Batteries, PhysLean, FLT)
   └─ Source: Downloaded via `lake build`
   
Extractor Scripts:
├─ ExtractDeclarations.lean
│  └─→ ../data/declarations.jsonl
│  └─→ ../data/dependencies.jsonl
│
└─ ExtractAST.lean
   └─→ ../data/AST/<Library>/<path>/*.ast.json
   └─→ ../data/AST/<Library>/<path>/*.dep_paths

Outputs (used by Python scripts):
├─ declarations.jsonl → scripts/populate_db.py
├─ dependencies.jsonl → scripts/populate_db.py
└─ data/AST/ → scripts/populate_db.py (Phase 2)
```

---

## Troubleshooting

### ExtractDeclarations.lean Issues

**Error: "Module not found"**
- Ensure all dependencies are downloaded: `lake build`
- Check that `lakefile.lean` has all required dependencies
- Verify the Lean toolchain version matches `lean-toolchain` (4.15.0)

**Error: "Out of memory"**
- Mathlib is very large; ensure you have at least 8GB+ RAM available
- Consider processing smaller subsets of libraries

**Slow performance**
- This is expected for large codebases; Mathlib can take hours
- Progress is reported every 5,000 declarations

### ExtractAST.lean Issues

**Error: "Source directory not found"**
- Check `extractor_config.json` has correct `toolchainCoreSrcDir` path
- Ensure the path points to the `src` directory (not `src/lean`)
- The script appends `/lean` automatically

**Warning: "Source directory for library 'X' not found"**
- The library may not be installed or compiled
- Run `lake build` to ensure all dependencies are available
- Some libraries may be optional and can be skipped

**No files processed**
- Ensure `.olean` files exist (run `lake build`)
- Only files with compiled `.olean` counterparts are processed
- Check that source directories exist and contain `.lean` files

**Parallel processing issues**
- Reduce `maxWorkers` if you encounter resource limits
- Check available CPU cores and memory

---

## Configuration Files

### `extractor_config.json`

**Purpose**: Specifies the Lean toolchain source directory path.

**Format**:
```json
{
  "toolchainCoreSrcDir": "/absolute/path/to/lean/toolchain/src"
}
```

**Notes**:
- Use absolute paths
- The script appends `/lean` to locate Init, Std, and Lean directories
- Falls back to sysroot if file is missing or invalid

### `lakefile.lean`

**Purpose**: Configures Lake package dependencies.

**Notable dependencies**:
- All packages pinned to Lean 4.15.0
- Mathlib, Batteries, PhysLean, FLT configured as direct dependencies
- Additional transitive dependencies automatically resolved

**Modifying dependencies**: Edit `lakefile.lean` and run `lake build` to update.

### `lean-toolchain`

**Purpose**: Specifies the exact Lean version to use.

**Content**: `leanprover/lean4:v4.15.0`

**Note**: Must match the version expected by dependencies in `lakefile.lean`.

---

## Tips

1. **First-time setup**: Run `lake build` first to ensure all dependencies are downloaded and compiled
2. **Resumable processing**: `ExtractAST.lean` skips files that already have output, making it safe to interrupt and resume
3. **Disk space**: Ensure you have sufficient disk space (tens of GB for large libraries)
4. **Memory**: Large libraries like Mathlib require significant RAM (8GB+ recommended)
5. **Parallel processing**: `ExtractAST.lean` benefits significantly from multiple CPU cores
6. **Configuration**: Always use absolute paths in `extractor_config.json`

---

## Related Documentation

- Main project README: `../README.md`
- Python scripts documentation: `../scripts/README.md`
- Lean 4 documentation: https://leanprover-community.github.io/
- Lake documentation: https://github.com/leanprover/lake

