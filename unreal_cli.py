# Backward-compatibility shim -- real implementation lives in unreal_mcp.cli
from unreal_mcp.cli import *  # noqa: F401,F403
from unreal_mcp.cli import build_parser, main

if __name__ == "__main__":
    import sys
    sys.exit(main())
