# Backward-compatibility shim -- real implementation lives in unreal_mcp.remote
from unreal_mcp.remote import *  # noqa: F401,F403
from unreal_mcp.remote import (
    EDITOR_ACTOR_SUBSYSTEM,
    EDITOR_LEVEL_LIBRARY,
    call_remote_function,
    get_object_property,
    get_selected_actors,
    list_level_actors,
    save_current_level,
    select_actors,
    set_object_property,
)
