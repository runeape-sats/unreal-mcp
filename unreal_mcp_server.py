# Backward-compatibility shim -- real implementation lives in unreal_mcp.server
from unreal_mcp.server import *  # noqa: F401,F403
from unreal_mcp.server import mcp

if __name__ == "__main__":
    import logging
    import traceback
    logger = logging.getLogger("UnrealMCPServer")
    try:
        logger.info("Starting UnrealMCP server...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running UnrealMCP server: {str(e)}")
        traceback.print_exc()
