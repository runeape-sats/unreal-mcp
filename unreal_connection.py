# Backward-compatibility shim -- real implementation lives in unreal_mcp.connection
from unreal_mcp.connection import *  # noqa: F401,F403
from unreal_mcp.connection import UnrealConnection, get_unreal_connection
