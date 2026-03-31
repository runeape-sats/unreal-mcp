# Main entry point for the Unreal Engine MCP server

import logging
import json
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any
import traceback

from mcp.server.fastmcp import FastMCP, Context

from .connection import get_unreal_connection
from .utils import parse_kwargs

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UnrealMCPServer")

# Global spatial context to track all actors
spatial_context: Dict[str, Dict[str, str]] = {}


def _parse_tool_params(kwargs: str) -> Dict[str, Any]:
    """Parse MCP kwargs consistently for tool wrappers."""
    return parse_kwargs(kwargs)


def _update_spatial_context_from_params(params: Dict[str, Any], default_prefix: str) -> None:
    """Update cached spatial context from common actor transform params."""
    global spatial_context

    actor_label = params.get("actor_label") or params.get("name") or f"{default_prefix}_{len(spatial_context)}"
    spatial_context[actor_label] = {
        "location": str(params.get("location", [0, 0, 0])),
        "rotation": str(params.get("rotation", [0, 0, 0])),
        "scale": str(params.get("scale", [1, 1, 1]))
    }

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    global spatial_context
    try:
        logger.info("UnrealMCP server starting up")

        try:
            unreal = get_unreal_connection()
            if unreal.test_connection():
                logger.info("Successfully connected to Unreal Engine on startup")
            else:
                logger.warning("Could not connect to Unreal Engine on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Unreal Engine on startup: {str(e)}")

        spatial_context = {}
        yield {}
    finally:
        logger.info("UnrealMCP server shut down")
        spatial_context.clear()

# Create the MCP server with lifespan support
mcp = FastMCP(
    "UnrealMCP",
    instructions="Unreal Engine integration with spatial context tracking",
    lifespan=server_lifespan
)

@mcp.tool()
def get_spatial_context(ctx: Context) -> str:
    """Return the current spatial context of all actors as a JSON string."""
    global spatial_context
    try:
        return json.dumps(spatial_context, indent=2)
    except Exception as e:
        logger.error(f"Error in get_spatial_context: {str(e)}")
        return f"Error retrieving spatial context: {str(e)}"

@mcp.tool()
def reset_spatial_context(ctx: Context) -> str:
    """Reset the spatial context, clearing all tracked actors."""
    global spatial_context
    try:
        spatial_context.clear()
        return "Spatial context reset successfully."
    except Exception as e:
        logger.error(f"Error in reset_spatial_context: {str(e)}")
        return f"Error resetting spatial context: {str(e)}"

@mcp.tool()
def delete_actor(ctx: Context, actor_label: str) -> str:
    """
    Delete a specific actor from the Unreal Engine level.

    Parameters:
    - actor_label: The label/name of the actor to delete
    """
    global spatial_context
    try:
        from .actors import delete_actor as del_actor
        result = del_actor(actor_label)
        spatial_context.pop(actor_label, None)
        return result
    except Exception as e:
        logger.error(f"Error in delete_actor: {str(e)}")
        return f"Error deleting actor: {str(e)}"

@mcp.tool()
def spawn_actor_from_blueprint(ctx: Context, kwargs: str) -> str:
    """
    Spawn a level actor based on an Unreal Blueprint class.

    Parameters:
    - kwargs: String containing parameters as key=value pairs or JSON object
      Example: "actor_class=/Game/AssetName/Blueprints/BP_House0.BP_House0_C location=100,100,0 name=MyHouse"

    Supported parameters:
    - actor_class: (required) Path to the blueprint class
    - actor_label/name: Name for the actor
    - location: x,y,z location coordinates
    - rotation: pitch,yaw,roll rotation in degrees
    - scale: x,y,z scale factors
    """
    global spatial_context
    try:
        from .actors import spawn_actor_from_blueprint as spawn_bp
        result = spawn_bp(kwargs)
        params = _parse_tool_params(kwargs)
        _update_spatial_context_from_params(params, "Actor")
        return result
    except Exception as e:
        logger.error(f"Error in spawn_actor_from_blueprint: {str(e)}")
        return f"Error spawning actor from blueprint: {str(e)}"

@mcp.tool()
def spawn_static_mesh(ctx: Context, kwargs: str) -> str:
    """
    Spawn a static mesh actor using an existing static mesh asset from the content browser.

    Parameters:
    - kwargs: String containing parameters as key=value pairs or JSON object
      Example: "static_mesh=/Game/AssetName/Meshes/Bench01 location=100,100,0 name=MyBench"

    Supported parameters:
    - static_mesh: (required) Path to the static mesh asset
    - actor_label/name: Name for the actor
    - location: x,y,z location coordinates
    - rotation: pitch,yaw,roll rotation in degrees
    - scale: x,y,z scale factors
    - material_override: Path to material to use
    - color: r,g,b color values (0.0-1.0)
    """
    global spatial_context
    try:
        from .actors import spawn_static_mesh_actor_from_mesh
        result = spawn_static_mesh_actor_from_mesh(kwargs)
        params = _parse_tool_params(kwargs)
        _update_spatial_context_from_params(params, "Mesh")
        return result
    except Exception as e:
        logger.error(f"Error in spawn_static_mesh: {str(e)}")
        return f"Error spawning static mesh actor: {str(e)}"

@mcp.tool()
def create_static_mesh_actor(ctx: Context, kwargs: str) -> str:
    """
    Create a new static mesh actor in the Unreal Engine level using a simpler approach.

    Parameters:
    - kwargs: String containing parameters as key=value pairs or JSON object
      Example: "actor_label=Cube mesh_type=CUBE location=0,0,0"

    Supported parameters:
    - actor_label/name: Name for the actor
    - mesh_type: One of CUBE, SPHERE, CYLINDER, PLANE, CONE
    - location: x,y,z location coordinates
    - rotation: pitch,yaw,roll rotation in degrees
    - scale: x,y,z scale factors. 1 means same scale (100%)
    - color: r,g,b color values (0.0-1.0)
    """
    global spatial_context
    try:
        from .actors import create_static_mesh_actor as create_mesh
        result = create_mesh(kwargs)
        params = _parse_tool_params(kwargs)
        _update_spatial_context_from_params(params, "Mesh")
        return result
    except Exception as e:
        logger.error(f"Error in create_static_mesh_actor: {str(e)}")
        return f"Error creating static mesh actor: {str(e)}"

@mcp.tool()
def modify_actor(ctx: Context, kwargs: str) -> str:
    """
    Modify an existing actor in the Unreal Engine level.

    Parameters:
    - kwargs: String containing parameters as key=value pairs or JSON object
      Example: "actor_label=Cube location=100,200,50 rotation=0,45,0"

    Supported parameters:
    - actor_label: Label/name of the actor to modify (required)
    - location: x,y,z location coordinates
    - rotation: pitch,yaw,roll rotation in degrees
    - scale: x,y,z scale factors
    - visible: true/false to set visibility
    - color: r,g,b color values (0.0-1.0)
    """
    global spatial_context
    try:
        from .actors import modify_actor as mod_actor
        result = mod_actor(kwargs)
        params = _parse_tool_params(kwargs)
        actor_label = params["actor_label"]
        if actor_label in spatial_context:
            spatial_context[actor_label].update({
                k: str(params[k]) for k in ["location", "rotation", "scale"] if k in params
            })
        return result
    except Exception as e:
        logger.error(f"Error in modify_actor: {str(e)}")
        return f"Error modifying actor: {str(e)}"

@mcp.tool()
def get_level_info(ctx: Context) -> str:
    """Get information about the current Unreal Engine level and update spatial context."""
    global spatial_context
    try:
        from .assets import get_level_info as get_level
        level_info = get_level()

        try:
            level_data = json.loads(level_info)
            if isinstance(level_data, dict) and "actors" in level_data:
                spatial_context.clear()
                for actor in level_data["actors"]:
                    actor_label = actor.get("actor_label", actor.get("name", f"Actor_{len(spatial_context)}"))
                    spatial_context[actor_label] = {
                        "location": actor.get("location", "0,0,0"),
                        "rotation": actor.get("rotation", "0,0,0"),
                        "scale": actor.get("scale", "1,1,1")
                    }
        except json.JSONDecodeError:
            logger.info("Level info not in expected JSON format, spatial context unchanged")

        return level_info
    except Exception as e:
        logger.error(f"Error in get_level_info: {str(e)}")
        return f"Error getting level info: {str(e)}"

@mcp.tool()
def list_available_assets(ctx: Context, kwargs: str) -> str:
    """
    List available assets of a specific type in the Unreal Engine project.

    Parameters:
    - kwargs: String containing parameters as key=value pairs or JSON object
      Example: "asset_type=StaticMesh search_path=/Game/AssetName search_term=House"

    Supported parameters:
    - asset_type: Type of assets to list (BlueprintClass, StaticMesh, Material, etc.)
    - search_path: Optional path to search for assets (default: /Game)
    - search_term: Optional term to filter results
    - max_results: Maximum number of results to return (default: 20)
    """
    try:
        from .assets import get_available_assets
        return get_available_assets(kwargs)
    except Exception as e:
        logger.error(f"Error in list_available_assets: {str(e)}")
        return f"Error listing available assets: {str(e)}"

@mcp.tool()
def get_actor_info(ctx: Context, actor_label: str) -> str:
    """
    Get detailed information about a specific actor in the Unreal Engine level.

    Parameters:
    - actor_label: The label/name of the actor to get information about
    """
    try:
        from .actors import get_actor_info as get_info
        return get_info(actor_label)
    except Exception as e:
        logger.error(f"Error in get_actor_info: {str(e)}")
        return f"Error getting actor info: {str(e)}"

@mcp.tool()
def search_assets_recursively(ctx: Context, base_path: str, asset_type: str = None, search_term: str = None, max_results: int = 50) -> str:
    """
    Search for assets recursively in all common subdirectories.

    Parameters:
    - base_path: The base path to search in (e.g., '/Game/KyotoAlley')
    - asset_type: Optional type of assets to filter by
    - search_term: Optional search term to filter results
    - max_results: Maximum number of results (default: 50)
    """
    try:
        from .assets import search_assets_recursively as search_assets
        return search_assets(base_path, asset_type, search_term, max_results)
    except Exception as e:
        logger.error(f"Error in search_assets_recursively: {str(e)}")
        return f"Error searching assets recursively: {str(e)}"

@mcp.tool()
def list_level_actors(ctx: Context, kwargs: str = "") -> str:
    """
    List actors in the current level.

    Parameters:
    - kwargs: Optional key=value pairs or JSON object
      Supported parameters:
      - filter: Case-insensitive label/path substring filter
      - include_transforms: true/false, default true
      - max_results: Maximum actors to return, default 100
    """
    try:
        from .remote import list_level_actors as list_actors
        return list_actors(kwargs)
    except Exception as e:
        logger.error(f"Error in list_level_actors: {str(e)}")
        return f"Error listing level actors: {str(e)}"

@mcp.tool()
def get_selected_actors(ctx: Context) -> str:
    """Get the actors currently selected in the Unreal Editor."""
    try:
        from .remote import get_selected_actors as get_selected
        return get_selected()
    except Exception as e:
        logger.error(f"Error in get_selected_actors: {str(e)}")
        return f"Error getting selected actors: {str(e)}"

@mcp.tool()
def select_actors(ctx: Context, kwargs: str) -> str:
    """
    Select one or more actors in the Unreal Editor.

    Parameters:
    - kwargs: key=value pairs or JSON object
      Supported parameters:
      - actor_labels: Comma-separated list or JSON array of actor labels
      - replace_selection: true/false, default true
    """
    try:
        from .remote import select_actors as select_actor_labels
        return select_actor_labels(kwargs)
    except Exception as e:
        logger.error(f"Error in select_actors: {str(e)}")
        return f"Error selecting actors: {str(e)}"

@mcp.tool()
def save_current_level(ctx: Context) -> str:
    """Save the currently open Unreal level."""
    try:
        from .remote import save_current_level as save_level
        return save_level()
    except Exception as e:
        logger.error(f"Error in save_current_level: {str(e)}")
        return f"Error saving current level: {str(e)}"

@mcp.tool()
def remote_call(ctx: Context, kwargs: str) -> str:
    """
    Call any Unreal Remote Control function.

    Parameters:
    - kwargs: key=value pairs or JSON object
      Supported parameters:
      - object_path: Direct Unreal object path
      - actor_label: Actor label to resolve into an object path
      - component_class: Optional component class to resolve from the actor
      - function_name: Unreal function to call
      - parameters: JSON object of function parameters
      - generate_transaction: true/false, default true
    """
    try:
        from .remote import call_remote_function
        return call_remote_function(kwargs)
    except Exception as e:
        logger.error(f"Error in remote_call: {str(e)}")
        return f"Error calling remote function: {str(e)}"

@mcp.tool()
def get_object_property(ctx: Context, kwargs: str) -> str:
    """
    Read any Unreal object property through the Remote Control property endpoint.

    Parameters:
    - kwargs: key=value pairs or JSON object
      Supported parameters:
      - object_path: Direct Unreal object path
      - actor_label: Actor label to resolve into an object path
      - component_class: Optional component class to resolve from the actor
      - property_name: Unreal property name to read
    """
    try:
        from .remote import get_object_property as read_property
        return read_property(kwargs)
    except Exception as e:
        logger.error(f"Error in get_object_property: {str(e)}")
        return f"Error getting object property: {str(e)}"

@mcp.tool()
def set_object_property(ctx: Context, kwargs: str) -> str:
    """
    Write any Unreal object property through the Remote Control property endpoint.

    Parameters:
    - kwargs: key=value pairs or JSON object
      Supported parameters:
      - object_path: Direct Unreal object path
      - actor_label: Actor label to resolve into an object path
      - component_class: Optional component class to resolve from the actor
      - property_name: Unreal property name to write
      - property_value: Value to assign, preferably via JSON for structs
      - generate_transaction: true/false, default true
    """
    try:
        from .remote import set_object_property as write_property
        return write_property(kwargs)
    except Exception as e:
        logger.error(f"Error in set_object_property: {str(e)}")
        return f"Error setting object property: {str(e)}"

@mcp.tool()
def create_basic_castle(ctx: Context, kwargs: str = "") -> str:
    """
    Create a sample castle workflow from primitive shapes.

    Parameters:
    - kwargs: Optional key=value pairs or JSON object
      Supported parameters:
      - prefix: Actor label prefix, default Castle
      - origin: x,y,z base location
      - stone_color: r,g,b or r,g,b,a color for stone elements
      - roof_color: r,g,b or r,g,b,a color for roof elements
    - layout: classic, courtyard, bastion, or longhall
    - size: compact, standard, or grand
    - palette: granite, sandstone, moss, or obsidian
    - yaw: rotate the layout around the origin in degrees
    - replace_existing: true/false, default true
      - dry_run: true/false, default false
    """
    global spatial_context
    try:
        from examples.castle import create_basic_castle as build_castle

        params = _parse_tool_params(kwargs)
        prefix = params.get("prefix", "Castle")
        origin = params.get("origin") or params.get("location")
        stone_color = params.get("stone_color")
        roof_color = params.get("roof_color")
        layout = params.get("layout", "classic")
        size = params.get("size", "standard")
        palette = params.get("palette", "granite")
        yaw = params.get("yaw", 0.0)
        dry_run = params.get("dry_run", False)
        replace_existing = params.get("replace_existing", True)

        result = build_castle(prefix, origin, stone_color, roof_color, dry_run, replace_existing, layout, size, palette, yaw)

        if not dry_run and not str(result).startswith("Error"):
            try:
                parsed = json.loads(result)
                for actor_label in parsed.get("created", []):
                    spatial_context.setdefault(actor_label, {
                        "location": str(origin or [0, 0, 0]),
                        "rotation": str([0, 0, 0]),
                        "scale": str([1, 1, 1])
                    })
            except json.JSONDecodeError:
                logger.warning("create_basic_castle returned non-JSON output; spatial context was not updated")

        return result
    except Exception as e:
        logger.error(f"Error in create_basic_castle: {str(e)}")
        return f"Error creating basic castle: {str(e)}"

@mcp.tool()
def verify_basic_castle(ctx: Context, prefix: str = "Castle") -> str:
    """
    Verify that a castle built from the shared plan exists in the current level.

    Parameters:
    - prefix: Actor label prefix, default Castle
    """
    try:
        from examples.castle import verify_basic_castle as verify_castle
        return verify_castle(prefix)
    except Exception as e:
        logger.error(f"Error in verify_basic_castle: {str(e)}")
        return f"Error verifying basic castle: {str(e)}"

@mcp.tool()
def reset_basic_castle(ctx: Context, kwargs: str = "") -> str:
    """
    Delete a castle by prefix.

    Parameters:
    - kwargs: Optional key=value pairs or JSON object
      Supported parameters:
      - prefix: Actor label prefix, default Castle
      - strict_plan: true/false, default false
      - dry_run: true/false, default false
    """
    global spatial_context
    try:
        from examples.castle import reset_basic_castle as clear_castle

        params = _parse_tool_params(kwargs)
        prefix = params.get("prefix", "Castle")
        strict_plan = params.get("strict_plan", False)
        dry_run = params.get("dry_run", False)
        result = clear_castle(prefix, strict_plan, dry_run)

        if not dry_run and not str(result).startswith("Error"):
            try:
                parsed = json.loads(result)
                for actor_label in parsed.get("deleted", []):
                    spatial_context.pop(actor_label, None)
            except json.JSONDecodeError:
                logger.warning("reset_basic_castle returned non-JSON output; spatial context was not updated")

        return result
    except Exception as e:
        logger.error(f"Error in reset_basic_castle: {str(e)}")
        return f"Error resetting basic castle: {str(e)}"

if __name__ == "__main__":
    try:
        logger.info("Starting UnrealMCP server...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running UnrealMCP server: {str(e)}")
        traceback.print_exc()
