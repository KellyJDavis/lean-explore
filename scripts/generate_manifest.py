# File: scripts/generate_manifest.py

"""Generates a manifest.json file for Lean Explore data toolchains.

This script reads the three required data files (database, FAISS index, and ID map),
compresses them, calculates SHA256 checksums, and generates a manifest.json file
that can be used for publishing data to Cloudflare R2 or for local use.

The generated manifest follows the same structure as the remote manifest hosted
on R2, allowing the data to be fetched using `leanexplore data fetch`.
"""

import argparse
import gzip
import hashlib
import json
import logging
import pathlib
import re
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import defaults for version constants
# Add src directory to path to allow importing lean_explore
_script_dir = pathlib.Path(__file__).parent
_project_root = _script_dir.parent
_src_dir = _project_root / "src"
if _src_dir.exists():
    sys.path.insert(0, str(_src_dir))

try:
    from lean_explore import defaults  # noqa: E402
except ImportError as e:
    print(
        f"Error: Could not import lean_explore.defaults: {e}\n\n"
        "POSSIBLE CAUSES & SOLUTIONS:\n"
        "1. RUNNING LOCATION: Ensure you are running this script from the "
        "project's ROOT directory,\n"
        "   e.g., 'python scripts/generate_manifest.py'.\n\n"
        "2. PACKAGE INSTALLATION: The 'lean_explore' package might not be "
        "installed in your current Python environment.\n"
        "   - RECOMMENDED: From your project root, run: 'pip install -e .'\n"
        "     This installs it in editable mode, making it available.\n"
        "   - The script attempts to add the 'src/' directory to sys.path,\n"
        "     but this may not work in all environments.\n\n"
        f"Current sys.path (at time of error): {sys.path}",
        file=sys.stderr,
    )
    sys.exit(1)
except Exception as e:
    print(
        f"An unexpected error occurred during import of lean_explore.defaults: {e}",
        file=sys.stderr,
    )
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Default file names
DEFAULT_DB_FILE = "lean_explore_data.db"
DEFAULT_FAISS_INDEX_FILE = "main_faiss.index"
DEFAULT_FAISS_MAP_FILE = "faiss_ids_map.json"

# Split file configuration
# Default threshold: 1.8GB (safe margin below GitHub's 2GB limit)
DEFAULT_SPLIT_THRESHOLD_BYTES = 1800 * 1024 * 1024  # 1.8GB in bytes
DEFAULT_SPLIT_CHUNK_SIZE_BYTES = 1800 * 1024 * 1024  # 1.8GB chunks

# Expected file mappings
FILE_MAPPINGS = {
    DEFAULT_DB_FILE: {
        "local_name": DEFAULT_DB_FILE,
        "remote_name": f"{DEFAULT_DB_FILE}.gz",
    },
    DEFAULT_FAISS_INDEX_FILE: {
        "local_name": DEFAULT_FAISS_INDEX_FILE,
        "remote_name": f"{DEFAULT_FAISS_INDEX_FILE}.gz",
    },
    DEFAULT_FAISS_MAP_FILE: {
        "local_name": DEFAULT_FAISS_MAP_FILE,
        "remote_name": f"{DEFAULT_FAISS_MAP_FILE}.gz",
    },
}


def calculate_sha256(file_path: pathlib.Path) -> str:
    """Calculates the SHA256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        The hexadecimal SHA256 checksum string.
    """
    logger.info(f"Calculating SHA256 checksum for {file_path.name}...")
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        checksum = sha256_hash.hexdigest()
        logger.info(f"SHA256 for {file_path.name}: {checksum}")
        return checksum
    except OSError as e:
        logger.error(f"Error reading file {file_path} for checksum: {e}")
        raise


def compress_file(
    input_path: pathlib.Path, output_path: pathlib.Path
) -> pathlib.Path:
    """Compresses a file using gzip.

    Args:
        input_path: Path to the file to compress.
        output_path: Path where the compressed file should be saved.

    Returns:
        The path to the compressed file.

    Raises:
        OSError: If compression fails.
    """
    logger.info(f"Compressing {input_path.name} to {output_path.name}...")
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(input_path, "rb") as f_in:
            with gzip.open(output_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        logger.info(f"Successfully compressed {input_path.name}")
        return output_path
    except (OSError, gzip.BadGzipFile) as e:
        logger.error(f"Error compressing {input_path}: {e}")
        raise


def get_file_size(file_path: pathlib.Path) -> int:
    """Gets the size of a file in bytes.

    Args:
        file_path: Path to the file.

    Returns:
        File size in bytes.
    """
    try:
        return file_path.stat().st_size
    except OSError as e:
        logger.error(f"Error getting file size for {file_path}: {e}")
        raise


def split_file(
    input_path: pathlib.Path,
    output_prefix: str,
    chunk_size_bytes: int,
) -> List[pathlib.Path]:
    """Splits a file using Unix split command.

    Args:
        input_path: Path to file to split.
        output_prefix: Prefix for output files (e.g., "/path/to/file.gz.").
            The split command will append numeric suffixes like "000", "001", etc.
        chunk_size_bytes: Size of each chunk in bytes.

    Returns:
        List of paths to generated part files, sorted by part number.

    Raises:
        subprocess.CalledProcessError: If the split command fails.
        OSError: If there are errors accessing files.
    """
    # Convert bytes to format split understands (e.g., "1800M")
    chunk_size_mb = chunk_size_bytes // (1024 * 1024)
    chunk_size_str = f"{chunk_size_mb}M"

    logger.info(
        f"Splitting {input_path.name} into chunks of {chunk_size_str} "
        f"({chunk_size_bytes:,} bytes)..."
    )

    cmd = [
        "split",
        "-b",
        chunk_size_str,
        "-d",  # Numeric suffixes
        "-a",
        "3",  # 3-digit suffixes (allows up to 1000 parts)
        str(input_path),
        output_prefix,
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=3600
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Split command failed: {e}")
        logger.error(f"Command output: {e.stderr}")
        raise
    except subprocess.TimeoutExpired:
        logger.error(f"Split command timed out after 1 hour")
        raise

    # Find all generated parts (sorted naturally)
    # Output will be output_prefix + "000", "001", etc.
    prefix_path = pathlib.Path(output_prefix)
    part_files = sorted(prefix_path.parent.glob(f"{prefix_path.name}*"))

    # Filter to only files with numeric 3-digit suffixes (pattern: .\d{3}$)
    numeric_pattern = re.compile(r"\.\d{3}$")
    numeric_parts = [
        p for p in part_files if numeric_pattern.search(p.name) and p.is_file()
    ]
    numeric_parts.sort()  # Ensure sorted order

    if not numeric_parts:
        raise RuntimeError(
            f"No split parts found with numeric suffixes after splitting {input_path}"
        )

    logger.info(f"Created {len(numeric_parts)} parts: {[p.name for p in numeric_parts]}")
    return numeric_parts


def process_split_file_parts(
    part_paths: List[pathlib.Path], base_remote_name: str
) -> List[Dict[str, Any]]:
    """Processes split file parts, calculating metadata for each part.

    Args:
        part_paths: List of paths to part files, should be sorted by part number.
        base_remote_name: Base remote name (e.g., "main_faiss.index.gz").

    Returns:
        List of dictionaries containing metadata for each part, sorted by part_number.
    """
    parts_metadata: List[Dict[str, Any]] = []

    for part_path in part_paths:
        # Extract part number from filename (last 3 digits before extension or at end)
        # e.g., "main_faiss.index.gz.000" -> part_number 0
        numeric_pattern = re.search(r"\.(\d{3})$", part_path.name)
        if not numeric_pattern:
            raise ValueError(
                f"Could not extract part number from filename: {part_path.name}"
            )
        part_number = int(numeric_pattern.group(1))

        # Get part size
        part_size = get_file_size(part_path)

        # Calculate SHA256 of part
        part_sha256 = calculate_sha256(part_path)

        # Build remote name: base_remote_name + ".000", ".001", etc.
        remote_name = f"{base_remote_name}.{part_number:03d}"

        parts_metadata.append(
            {
                "remote_name": remote_name,
                "sha256": part_sha256,
                "size_bytes": part_size,
                "part_number": part_number,
            }
        )

    # Sort by part_number to ensure correct order
    parts_metadata.sort(key=lambda x: x["part_number"])

    logger.info(
        f"Processed {len(parts_metadata)} parts for {base_remote_name}: "
        f"part numbers {[p['part_number'] for p in parts_metadata]}"
    )

    return parts_metadata


def process_file(
    file_path: pathlib.Path,
    temp_dir: pathlib.Path,
    local_name: str,
    remote_name: str,
    split_threshold_bytes: int = DEFAULT_SPLIT_THRESHOLD_BYTES,
    split_chunk_size_bytes: int = DEFAULT_SPLIT_CHUNK_SIZE_BYTES,
) -> Dict[str, Any]:
    """Processes a single file: compresses it and calculates metadata.

    If a compressed file already exists and is newer than or equal to the source file,
    it will be reused to avoid unnecessary recompression.

    If the compressed file exceeds the split threshold, it will be split into multiple
    parts that can be uploaded separately (e.g., to GitHub releases with 2GB limits).

    Args:
        file_path: Path to the uncompressed file.
        temp_dir: Temporary directory for storing compressed files.
        local_name: The local filename (e.g., "lean_explore_data.db").
        remote_name: The remote compressed filename (e.g., "lean_explore_data.db.gz").
        split_threshold_bytes: Size threshold in bytes above which files will be split.
            Defaults to DEFAULT_SPLIT_THRESHOLD_BYTES (1.8GB).
        split_chunk_size_bytes: Size of each split chunk in bytes.
            Defaults to DEFAULT_SPLIT_CHUNK_SIZE_BYTES (1.8GB).

    Returns:
        A dictionary containing file metadata for the manifest. If the file was split,
        the dictionary will include a "parts" array with metadata for each part.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")

    logger.info(f"Processing {local_name}...")

    # Get uncompressed size
    uncompressed_size = get_file_size(file_path)
    logger.info(f"Uncompressed size: {uncompressed_size:,} bytes")

    # Check if compressed file already exists and is up-to-date
    compressed_path = temp_dir / remote_name
    source_mtime = file_path.stat().st_mtime

    if compressed_path.exists():
        compressed_mtime = compressed_path.stat().st_mtime
        if compressed_mtime >= source_mtime:
            logger.info(
                f"Reusing existing compressed file {remote_name} "
                f"(source: {datetime.fromtimestamp(source_mtime)}, "
                f"compressed: {datetime.fromtimestamp(compressed_mtime)})"
            )
        else:
            logger.info(
                f"Source file {local_name} is newer than compressed file, "
                f"recompressing..."
            )
            compress_file(file_path, compressed_path)
    else:
        # Compress the file to a temporary location
        compress_file(file_path, compressed_path)

    # Get compressed size
    compressed_size = get_file_size(compressed_path)
    logger.info(f"Compressed size: {compressed_size:,} bytes")

    # Calculate SHA256 of compressed file (needed whether split or not)
    sha256 = calculate_sha256(compressed_path)

    # Check if file needs to be split
    if compressed_size > split_threshold_bytes:
        logger.info(
            f"Compressed file {remote_name} ({compressed_size:,} bytes) exceeds "
            f"split threshold ({split_threshold_bytes:,} bytes). Splitting..."
        )

        # Split the compressed file
        # Output prefix: compressed_path + "." (e.g., "main_faiss.index.gz.")
        output_prefix = str(compressed_path) + "."
        part_paths = split_file(compressed_path, output_prefix, split_chunk_size_bytes)

        # Process each part to get metadata
        parts_metadata = process_split_file_parts(part_paths, remote_name)

        # Verify sum of part sizes equals compressed file size
        total_parts_size = sum(p["size_bytes"] for p in parts_metadata)
        if total_parts_size != compressed_size:
            logger.warning(
                f"Part sizes sum ({total_parts_size:,} bytes) does not match "
                f"compressed file size ({compressed_size:,} bytes). This may indicate "
                "an issue with the split process."
            )

        logger.info(
            f"File {local_name} will be split into {len(parts_metadata)} parts "
            f"for upload"
        )

        # For split files, remote_name is optional since the actual remote files
        # are the parts (e.g., "main_faiss.index.gz.000"). We include it for
        # clarity and to specify the temporary reassembled filename during download,
        # but it's not strictly required.
        return {
            "local_name": local_name,
            "remote_name": remote_name,  # Used as temp filename for reassembled file
            "sha256": sha256,  # SHA256 of the full reassembled file
            "size_bytes_compressed": compressed_size,
            "size_bytes_uncompressed": uncompressed_size,
            "parts": parts_metadata,
        }
    else:
        # File is small enough, no splitting needed
        logger.info(
            f"Compressed file {remote_name} ({compressed_size:,} bytes) is under "
            f"split threshold ({split_threshold_bytes:,} bytes). No splitting needed."
        )

        return {
            "local_name": local_name,
            "remote_name": remote_name,
            "sha256": sha256,
            "size_bytes_compressed": compressed_size,
            "size_bytes_uncompressed": uncompressed_size,
        }


def generate_manifest(
    data_dir: pathlib.Path,
    output_path: pathlib.Path,
    latest_manifest_version: str,
    default_toolchain: str,
    description: Optional[str] = None,
    release_date: Optional[str] = None,
    assets_base_path_r2: Optional[str] = None,
    cleanup_temp: bool = True,
    split_threshold_bytes: int = DEFAULT_SPLIT_THRESHOLD_BYTES,
    split_chunk_size_bytes: int = DEFAULT_SPLIT_CHUNK_SIZE_BYTES,
) -> None:
    """Generates a manifest.json file from local data files.

    Args:
        data_dir: Directory containing the data files.
        output_path: Path where the manifest.json should be written.
        latest_manifest_version: Manifest version string (e.g., "0.3.0").
        default_toolchain: Default toolchain version string (e.g., "0.2.0").
        description: Optional description of this toolchain version.
        release_date: Optional release date in YYYY-MM-DD format. Defaults to today.
        assets_base_path_r2: Optional base path for R2 assets (e.g., "assets/0.3.0/").
            Defaults to empty string.
        cleanup_temp: If True, removes temporary compressed files after processing.
        split_threshold_bytes: Size threshold in bytes above which files will be split.
            Defaults to DEFAULT_SPLIT_THRESHOLD_BYTES (1.8GB).
        split_chunk_size_bytes: Size of each split chunk in bytes.
            Defaults to DEFAULT_SPLIT_CHUNK_SIZE_BYTES (1.8GB).
    """
    logger.info("Starting manifest generation...")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Latest manifest version: {latest_manifest_version}")
    logger.info(f"Default toolchain: {default_toolchain}")

    # Validate required parameters
    if not latest_manifest_version or not isinstance(latest_manifest_version, str):
        raise ValueError(
            f"latest_manifest_version must be a non-empty string, got: {latest_manifest_version!r}"
        )
    if not default_toolchain or not isinstance(default_toolchain, str):
        raise ValueError(
            f"default_toolchain must be a non-empty string, got: {default_toolchain!r}"
        )

    # Set defaults
    if description is None:
        description = f"v{default_toolchain}"
    if release_date is None:
        release_date = datetime.now().strftime("%Y-%m-%d")
    if assets_base_path_r2 is None:
        assets_base_path_r2 = ""

    # Create temporary directory for compressed files
    temp_dir = data_dir / ".manifest_temp"
    try:
        temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using temporary directory: {temp_dir}")

        # Process each file
        files_metadata: List[Dict[str, Any]] = []

        for filename, mapping in FILE_MAPPINGS.items():
            file_path = data_dir / filename
            file_metadata = process_file(
                file_path,
                temp_dir,
                mapping["local_name"],
                mapping["remote_name"],
                split_threshold_bytes=split_threshold_bytes,
                split_chunk_size_bytes=split_chunk_size_bytes,
            )
            files_metadata.append(file_metadata)

        # Build manifest structure
        manifest = {
            "latest_manifest_version": latest_manifest_version,
            "default_toolchain": default_toolchain,
            "toolchains": {
                default_toolchain: {
                    "description": description,
                    "release_date": release_date,
                    "assets_base_path_r2": assets_base_path_r2,
                    "files": files_metadata,
                }
            },
        }

        # Write manifest to file
        logger.info(f"Writing manifest to {output_path}...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info(f"Manifest successfully written to {output_path}")

        # Cleanup temporary files
        if cleanup_temp:
            logger.info("Cleaning up temporary compressed files...")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.info("Temporary files removed")

    except Exception as e:
        logger.error(f"Error during manifest generation: {e}", exc_info=True)
        # Cleanup on error
        if cleanup_temp and temp_dir.exists():
            logger.info("Cleaning up temporary files after error...")
            shutil.rmtree(temp_dir)
        raise


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments for the script.

    Returns:
        argparse.Namespace: An object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Generate a manifest.json file from local Lean Explore data files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--data-dir",
        "-d",
        type=pathlib.Path,
        default=pathlib.Path("data"),
        help="Directory containing the data files (lean_explore_data.db, "
        "main_faiss.index, faiss_ids_map.json).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=pathlib.Path,
        default=pathlib.Path("manifest.json"),
        help="Path where the manifest.json file should be written.",
    )
    parser.add_argument(
        "--latest-manifest-version",
        type=str,
        default=defaults.LATEST_MANIFEST_VERSION,
        help=f"Latest manifest version string (e.g., '0.3.0'). "
        f"Defaults to {defaults.LATEST_MANIFEST_VERSION}.",
    )
    parser.add_argument(
        "--default-toolchain",
        type=str,
        default=defaults.DEFAULT_ACTIVE_TOOLCHAIN_VERSION,
        help=f"Default toolchain version string (e.g., '0.2.0'). "
        f"This will be used as the key in the 'toolchains' dict and the value of "
        f"'default_toolchain'. Defaults to {defaults.DEFAULT_ACTIVE_TOOLCHAIN_VERSION}.",
    )
    parser.add_argument(
        "--description",
        type=str,
        default=None,
        help="Description of this toolchain version. Defaults to 'v{default_toolchain}'.",
    )
    parser.add_argument(
        "--release-date",
        type=str,
        default=None,
        help="Release date in YYYY-MM-DD format. Defaults to today's date.",
    )
    parser.add_argument(
        "--assets-base-path-r2",
        type=str,
        default=None,
        help="Base path for R2 assets (e.g., 'assets/0.3.0/'). "
        "Defaults to empty string.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary compressed files after processing (for inspection).",
    )
    parser.add_argument(
        "--split-threshold",
        type=int,
        default=DEFAULT_SPLIT_THRESHOLD_BYTES,
        help=f"Size threshold in bytes above which files will be split. "
        f"Defaults to {DEFAULT_SPLIT_THRESHOLD_BYTES:,} bytes (1.8GB).",
    )
    parser.add_argument(
        "--split-chunk-size",
        type=int,
        default=DEFAULT_SPLIT_CHUNK_SIZE_BYTES,
        help=f"Size of each split chunk in bytes. "
        f"Defaults to {DEFAULT_SPLIT_CHUNK_SIZE_BYTES:,} bytes (1.8GB).",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    try:
        generate_manifest(
            data_dir=args.data_dir.resolve(),
            output_path=args.output.resolve(),
            latest_manifest_version=args.latest_manifest_version,
            default_toolchain=args.default_toolchain,
            description=args.description,
            release_date=args.release_date,
            assets_base_path_r2=args.assets_base_path_r2,
            cleanup_temp=not args.keep_temp,
            split_threshold_bytes=args.split_threshold,
            split_chunk_size_bytes=args.split_chunk_size,
        )
        logger.info("--- Manifest generation completed successfully ---")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error(
            "Please ensure all required files exist in the data directory:\n"
            f"  - {args.data_dir / DEFAULT_DB_FILE}\n"
            f"  - {args.data_dir / DEFAULT_FAISS_INDEX_FILE}\n"
            f"  - {args.data_dir / DEFAULT_FAISS_MAP_FILE}"
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Manifest generation failed: {e}", exc_info=True)
        sys.exit(1)

