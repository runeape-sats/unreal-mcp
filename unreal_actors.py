# Backward-compatibility shim -- real implementation lives in unreal_mcp.actors
from unreal_mcp.actors import *  # noqa: F401,F403
from unreal_mcp.actors import (
    create_static_mesh_actor,
    delete_actor,
    get_actor_info,
    modify_actor,
    spawn_actor_base,
    spawn_actor_from_blueprint,
    spawn_static_mesh_actor_from_mesh,
)
