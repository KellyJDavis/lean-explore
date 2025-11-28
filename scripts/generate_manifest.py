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
import shutil
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

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


def process_file(
    file_path: pathlib.Path,
    temp_dir: pathlib.Path,
    local_name: str,
    remote_name: str,
) -> Dict[str, Any]:
    """Processes a single file: compresses it and calculates metadata.

    If a compressed file already exists and is newer than or equal to the source file,
    it will be reused to avoid unnecessary recompression.

    Args:
        file_path: Path to the uncompressed file.
        temp_dir: Temporary directory for storing compressed files.
        local_name: The local filename (e.g., "lean_explore_data.db").
        remote_name: The remote compressed filename (e.g., "lean_explore_data.db.gz").

    Returns:
        A dictionary containing file metadata for the manifest.
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

    # Calculate SHA256 of compressed file
    sha256 = calculate_sha256(compressed_path)

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
    version: str,
    description: Optional[str] = None,
    release_date: Optional[str] = None,
    assets_base_path_r2: Optional[str] = None,
    cleanup_temp: bool = True,
) -> None:
    """Generates a manifest.json file from local data files.

    Args:
        data_dir: Directory containing the data files.
        output_path: Path where the manifest.json should be written.
        version: Toolchain version string (e.g., "0.3.0").
        description: Optional description of this toolchain version.
        release_date: Optional release date in YYYY-MM-DD format. Defaults to today.
        assets_base_path_r2: Optional base path for R2 assets (e.g., "assets/0.3.0/").
            Defaults to "assets/{version}/".
        cleanup_temp: If True, removes temporary compressed files after processing.
    """
    logger.info("Starting manifest generation...")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Version: {version}")

    # Set defaults
    if description is None:
        description = f"v{version}"
    if release_date is None:
        release_date = datetime.now().strftime("%Y-%m-%d")
    if assets_base_path_r2 is None:
        assets_base_path_r2 = f"assets/{version}/"

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
            )
            files_metadata.append(file_metadata)

        # Build manifest structure
        manifest = {
            "latest_manifest_version": version,
            "default_toolchain": version,
            "toolchains": {
                version: {
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
        "--version",
        "-v",
        type=str,
        required=True,
        help="Toolchain version string (e.g., '0.3.0').",
    )
    parser.add_argument(
        "--description",
        type=str,
        default=None,
        help="Description of this toolchain version. Defaults to 'v{version}'.",
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
        "Defaults to 'assets/{version}/'.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary compressed files after processing (for inspection).",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    try:
        generate_manifest(
            data_dir=args.data_dir.resolve(),
            output_path=args.output.resolve(),
            version=args.version,
            description=args.description,
            release_date=args.release_date,
            assets_base_path_r2=args.assets_base_path_r2,
            cleanup_temp=not args.keep_temp,
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

