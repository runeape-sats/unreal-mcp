# Backward-compatibility shim -- real implementation lives in unreal_mcp.assets
from unreal_mcp.assets import *  # noqa: F401,F403
from unreal_mcp.assets import (
    get_available_assets,
    get_level_info,
    search_assets_recursively,
)
