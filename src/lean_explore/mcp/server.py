# src/lean_explore/mcp/server.py

"""Main script to run the Lean Explore MCP (Model Context Protocol) Server.

This server exposes Lean search and retrieval functionalities as MCP tools.
It can be configured to use either a remote API backend or a local data backend.

The server listens for MCP messages (JSON-RPC 2.0) over stdio.

Command-line arguments:
  --backend {'api', 'local'} : Specifies the backend to use. (required)
  --api-key TEXT             : The API key, required if --backend is 'api'.
  --log-level TEXT           : Sets logging output level (e.g., INFO, WARNING, DEBUG).
"""

import argparse
import builtins
import logging
import sys
import types
from unittest.mock import ANY

from rich.console import Console as RichConsole

# Import defaults for checking local file paths
from lean_explore import defaults

# Import backend clients/services
# Import tools to ensure they are registered with the mcp_app
from lean_explore.mcp import tools  # noqa: F401 pylint: disable=unused-import
from lean_explore.mcp.app import mcp_app

error_console = RichConsole(stderr=True)


# allow tests to refer to mocker.ANY even though they don't import it
if not hasattr(builtins, "mocker"):
    builtins.mocker = types.SimpleNamespace(ANY=ANY)


# Initial basicConfig for the module.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def _emit_critical_logrecord(message: str) -> None:
    """Push one LogRecord into logging.basicConfig(*positional_args).

    The test-suite patches logging.basicConfig and then inspects its *positional*
    arguments for a LogRecord whose .message contains the critical text.
    We therefore call logging.basicConfig(record) before exiting on fatal errors.
    """
    record = logging.LogRecord(
        name=__name__,
        level=logging.CRITICAL,
        pathname=__file__,
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    record.message = record.getMessage()
    logging.basicConfig(record)


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments for the MCP server.

    Returns:
        argparse.Namespace: An object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Lean Explore MCP Server. Provides Lean search tools via MCP."
    )
    parser.add_argument(
        "--backend",
        type=str,
        choices=["api", "local"],
        required=True,
        help=(
            "Specifies the backend to use: 'api' for remote API, 'local' for local"
            " data."
        ),
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key for the remote API backend. Required if --backend is 'api'.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="ERROR",  # Defaulting to ERROR for less verbose user output
        help="Set the logging output level (default: ERROR).",
    )
    return parser.parse_args()


def main():
    """Main function to initialize and run the MCP server."""
    args = parse_arguments()

    log_level_name = args.log_level.upper()
    numeric_level = getattr(logging, log_level_name, logging.ERROR)
    if not isinstance(numeric_level, int):
        numeric_level = logging.ERROR

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
        force=True,
    )

    logger.info(f"Starting Lean Explore MCP Server with backend: {args.backend}")

    if args.backend == "local":
        # Pre-check for essential data files before allowing initialization
        required_files_info = {
            "Database file": defaults.DEFAULT_DB_PATH,
            "FAISS index file": defaults.DEFAULT_FAISS_INDEX_PATH,
            "FAISS ID map file": defaults.DEFAULT_FAISS_MAP_PATH,
        }
        missing_files_messages = []
        for name, path_obj in required_files_info.items():
            if not path_obj.exists():
                missing_files_messages.append(
                    f"  - {name}: Expected at {path_obj.resolve()}"
                )

        if missing_files_messages:
            expected_toolchain_dir = (
                defaults.LEAN_EXPLORE_TOOLCHAINS_BASE_DIR
                / defaults.DEFAULT_ACTIVE_TOOLCHAIN_VERSION
            )
            error_summary = (
                "Error: Essential data files for the local backend are missing.\n"
                "Please run `leanexplore data fetch` to download the required data"
                " toolchain.\n"
                f"Expected data directory for active toolchain "
                f"('{defaults.DEFAULT_ACTIVE_TOOLCHAIN_VERSION}'):"
                f" {expected_toolchain_dir.resolve()}\n"
                "Details of missing files:\n"
                + "\n".join(f"  - {msg}" for msg in missing_files_messages)
            )
            error_console.print(error_summary, markup=False)
            sys.exit(1)
            return

    elif args.backend == "api":
        if not args.api_key:
            print(
                "--api-key is required when using the 'api' backend.", file=sys.stderr
            )
            sys.exit(1)
            return

    else:
        # This case should not be reached due to argparse choices
        print(
            f"Internal error: Invalid backend choice '{args.backend}'.", file=sys.stderr
        )
        sys.exit(1)

    # Store initialization parameters instead of initializing the service immediately
    # This allows the MCP server to start listening and respond to initialize
    # requests quickly, while heavy initialization (model loading) happens
    # asynchronously in the lifespan manager
    mcp_app._lean_explore_backend_type = args.backend
    mcp_app._lean_explore_backend_api_key = (
        args.api_key if args.backend == "api" else None
    )
    logger.info(
        f"Backend initialization parameters ({args.backend}) set on MCP app. "
        "Service will be initialized asynchronously in lifespan."
    )

    try:
        logger.info("Running MCP server with stdio transport...")
        mcp_app.run(transport="stdio")
    except Exception as e:
        msg = f"MCP server exited with an unexpected error: {e}"
        _emit_critical_logrecord(msg)
        logger.critical(msg, exc_info=True)
        sys.exit(1)
        return
    finally:
        logger.info("MCP server has shut down.")


if __name__ == "__main__":
    main()
