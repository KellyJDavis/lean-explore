"""Re-export configuration from dev_tools.config for convenient importing.

This module provides a convenient import path for scripts that add the project root
to sys.path. It re-exports APP_CONFIG and get_gemini_api_key from dev_tools.config.

Usage:
    from config import APP_CONFIG
    from config import get_gemini_api_key
"""

# Import from dev_tools.config - this will work when dev_tools is installed
# as a package or when the project root is in sys.path
try:
    from dev_tools.config import APP_CONFIG, get_gemini_api_key

    # Re-export for convenience
    __all__ = ["APP_CONFIG", "get_gemini_api_key"]
except ImportError as e:
    # If dev_tools.config cannot be imported, provide a helpful error
    raise ImportError(
        f"Could not import from dev_tools.config: {e}\n"
        "This usually means:\n"
        "1. The 'dev_tools' package is not installed. Run 'make install' or 'pip install -e .'\n"
        "2. The project root is not in sys.path. Ensure scripts add the project root to sys.path."
    ) from e



