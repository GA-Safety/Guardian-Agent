"""Configuration modules"""

# Re-export settings from the parent config.py file
import importlib.util
from pathlib import Path

# Load the parent config.py file directly
parent_dir = Path(__file__).parent.parent
config_file = parent_dir / "config.py"

# Create a module spec and load it
spec = importlib.util.spec_from_file_location("app.config_file", config_file)
_config_module = importlib.util.module_from_spec(spec)

# Execute the module (this will run config.py and create settings)
spec.loader.exec_module(_config_module)

# Re-export settings
settings = _config_module.settings
Settings = _config_module.Settings

from .cache_config import (
    CACHE_TTL,
    CACHE_KEY_PREFIXES,
    get_message_cache_key,
    get_pattern_cache_key,
    get_url_cache_key,
)

__all__ = [
    "settings",
    "Settings",
    "CACHE_TTL",
    "CACHE_KEY_PREFIXES",
    "get_message_cache_key",
    "get_pattern_cache_key",
    "get_url_cache_key",
]

