# Direct CLI for Unreal Remote Control workflows and repo-specific scenarios

import argparse
import sys
from typing import Callable, Dict, List, Optional

from .actors import (
    create_static_mesh_actor,
    delete_actor,
    get_actor_info,
    modify_actor,
    spawn_actor_from_blueprint,
    spawn_static_mesh_actor_from_mesh,
)
from .assets import get_available_assets, get_level_info, search_assets_recursively
from examples.castle import (
    DEFAULT_LAYOUT,
    DEFAULT_PALETTE,
    DEFAULT_SIZE,
    DEFAULT_YAW,
    LAYOUT_VARIANTS,
    PALETTE_VARIANTS,
    SIZE_VARIANTS,
    create_basic_castle,
    parse_color,
    parse_origin,
    reset_basic_castle,
    verify_basic_castle,
)
from .remote import (
    call_remote_function,
    get_object_property,
    get_selected_actors,
    list_level_actors,
    save_current_level,
    select_actors,
    set_object_property,
)


def _run_and_print(func: Callable[..., str], *args) -> int:
    result = func(*args)
    print(result)
    return 0 if not str(result).startswith("Error") else 1


def _add_kwargs_command(subparsers: argparse._SubParsersAction,
                        name: str,
                        summary: str,
                        details: str,
                        examples: List[str],
                        func: Callable[[str], str]) -> None:
    parser = subparsers.add_parser(
        name,
        help=summary,
        description=details,
        epilog="Examples:\n  " + "\n  ".join(examples),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--kwargs",
        required=True,
        help="Key=value string or JSON object passed straight to the Unreal helper function.",
    )
    parser.set_defaults(handler=lambda args: _run_and_print(func, args.kwargs))


def _add_zero_arg_command(subparsers: argparse._SubParsersAction,
                          name: str,
                          summary: str,
                          details: str,
                          func: Callable[[], str]) -> None:
    parser = subparsers.add_parser(name, help=summary, description=details)
    parser.set_defaults(handler=lambda args: _run_and_print(func))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="unreal-mcp-cli",
        description="Direct CLI for Unreal Engine Remote Control helpers and castle workflows.",
        epilog="Run 'unreal-mcp-cli <command> --help' to see argument details and examples for a specific function.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    commands = subparsers.add_parser(
        "commands",
        help="List available CLI commands.",
        description="List available CLI commands in a machine-readable order.",
    )
    commands.set_defaults(handler=_handle_commands)

    _add_kwargs_command(
        subparsers,
        "spawn-actor-from-blueprint",
        "Spawn an actor from a Blueprint class.",
        "Spawn a level actor from an Unreal Blueprint class using a key=value string or JSON payload.",
        [
            "unreal-mcp-cli spawn-actor-from-blueprint --kwargs \"actor_class=/Game/My/BP_Crate.BP_Crate_C actor_label=Castle_Crate location=0,0,0\"",
            "unreal-mcp-cli spawn-actor-from-blueprint --kwargs '{\"actor_class\": \"/Game/My/BP_Crate.BP_Crate_C\", \"actor_label\": \"Castle_Crate\"}'",
        ],
        spawn_actor_from_blueprint,
    )
    _add_kwargs_command(
        subparsers,
        "spawn-static-mesh",
        "Spawn a static mesh actor from an asset path.",
        "Spawn a StaticMeshActor using an existing static mesh asset from the content browser.",
        [
            "unreal-mcp-cli spawn-static-mesh --kwargs \"static_mesh=/Game/Meshes/SM_Bench actor_label=Bench01 location=0,0,0\"",
        ],
        spawn_static_mesh_actor_from_mesh,
    )
    _add_kwargs_command(
        subparsers,
        "create-static-mesh-actor",
        "Create a primitive static mesh actor.",
        "Create a primitive shape actor such as a cube, cylinder, sphere, plane, or cone.",
        [
            "unreal-mcp-cli create-static-mesh-actor --kwargs \"actor_label=Wall_A mesh_type=CUBE location=0,0,100 scale=4,1,2 color=0.6,0.6,0.65\"",
        ],
        create_static_mesh_actor,
    )
    _add_kwargs_command(
        subparsers,
        "modify-actor",
        "Modify an existing actor.",
        "Update actor transform, visibility, or material color using a key=value string or JSON payload.",
        [
            "unreal-mcp-cli modify-actor --kwargs \"actor_label=Wall_A location=100,0,100 rotation=0,90,0\"",
        ],
        modify_actor,
    )
    _add_zero_arg_command(
        subparsers,
        "get-level-info",
        "Get the current level summary.",
        "Return a JSON summary of the current level and its actors.",
        get_level_info,
    )
    _add_kwargs_command(
        subparsers,
        "list-available-assets",
        "Search assets in the project.",
        "List project assets using search path, asset type, and text filters.",
        [
            "unreal-mcp-cli list-available-assets --kwargs \"asset_type=staticmesh search_path=/Game search_term=wall max_results=10\"",
        ],
        get_available_assets,
    )
    _add_kwargs_command(
        subparsers,
        "list-level-actors",
        "List actors in the current level.",
        "List actors currently in the open level, optionally filtered by label or path substring.",
        [
            "unreal-mcp-cli list-level-actors --kwargs \"filter=Castle max_results=25\"",
        ],
        list_level_actors,
    )
    _add_zero_arg_command(
        subparsers,
        "get-selected-actors",
        "Show the current editor selection.",
        "Return the actors currently selected in the Unreal Editor.",
        get_selected_actors,
    )
    _add_kwargs_command(
        subparsers,
        "select-actors",
        "Select actors by label.",
        "Replace or extend the current Unreal Editor selection by actor label.",
        [
            "unreal-mcp-cli select-actors --kwargs \"actor_labels=Castle_Keep,Castle_Gatehouse replace_selection=true\"",
        ],
        select_actors,
    )
    _add_zero_arg_command(
        subparsers,
        "save-current-level",
        "Save the current level.",
        "Save the currently open map in the Unreal Editor.",
        save_current_level,
    )
    _add_kwargs_command(
        subparsers,
        "remote-call",
        "Call any Remote Control function.",
        "Call any Unreal Remote Control function by object path or actor label.",
        [
            "unreal-mcp-cli remote-call --kwargs \"actor_label=SkyLight function_name=GetActorLocation\"",
            "unreal-mcp-cli remote-call --kwargs '{\"object_path\": \"/Script/UnrealEd.Default__EditorActorSubsystem\", \"function_name\": \"GetAllLevelActors\"}'",
        ],
        call_remote_function,
    )
    _add_kwargs_command(
        subparsers,
        "get-object-property",
        "Read a Remote Control property.",
        "Read any Unreal object property using the Remote Control property endpoint.",
        [
            "unreal-mcp-cli get-object-property --kwargs \"actor_label=SkyLight property_name=Mobility\"",
        ],
        get_object_property,
    )
    _add_kwargs_command(
        subparsers,
        "set-object-property",
        "Write a Remote Control property.",
        "Write any Unreal object property using the Remote Control property endpoint.",
        [
            "unreal-mcp-cli set-object-property --kwargs '{\"actor_label\": \"SkyLight\", \"property_name\": \"Intensity\", \"property_value\": 5.0}'",
        ],
        set_object_property,
    )

    actor_info = subparsers.add_parser(
        "get-actor-info",
        help="Get detailed information about one actor.",
        description="Return transform and component details for a named actor.",
    )
    actor_info.add_argument("actor_label", help="Actor label to inspect.")
    actor_info.set_defaults(handler=lambda args: _run_and_print(get_actor_info, args.actor_label))

    delete = subparsers.add_parser(
        "delete-actor",
        help="Delete one actor by label.",
        description="Delete one actor from the current level by its label.",
    )
    delete.add_argument("actor_label", help="Actor label to delete.")
    delete.set_defaults(handler=lambda args: _run_and_print(delete_actor, args.actor_label))

    search = subparsers.add_parser(
        "search-assets-recursively",
        help="Search assets recursively in common subfolders.",
        description="Search assets recursively under a base content path and optional asset type filter.",
    )
    search.add_argument("base_path", help="Base content path such as /Game or /Game/Environment")
    search.add_argument("--asset-type", dest="asset_type", help="Optional asset type filter such as staticmesh or blueprint")
    search.add_argument("--search-term", dest="search_term", help="Optional case-insensitive search term")
    search.add_argument("--max-results", dest="max_results", type=int, default=50, help="Maximum number of assets to return")
    search.set_defaults(
        handler=lambda args: _run_and_print(
            search_assets_recursively,
            args.base_path,
            args.asset_type,
            args.search_term,
            args.max_results,
        )
    )

    create_castle = subparsers.add_parser(
        "create-basic-castle",
        help="Create a sample castle using primitive shapes.",
        description="Create a castle scene made from cubes, cylinders, and cones. Existing actors with the same planned labels are removed before placement by default, and layout, size, palette, and yaw presets can vary the generated castle while keeping the same core actor set.",
        epilog="Examples:\n  unreal-mcp-cli create-basic-castle --prefix SkillCastle\n  unreal-mcp-cli create-basic-castle --prefix DemoCastle --layout courtyard --size grand --palette sandstone\n  unreal-mcp-cli create-basic-castle --prefix Bastion01 --origin 5000,0,0 --yaw 45\n  unreal-mcp-cli create-basic-castle --dry-run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    create_castle.add_argument("--prefix", default="Castle", help="Prefix used for every generated actor label")
    create_castle.add_argument("--origin", default="0,0,0", help="Base location added to every castle actor")
    create_castle.add_argument("--stone-color", help="Optional RGB or RGBA override for stone elements; defaults to the selected palette")
    create_castle.add_argument("--roof-color", help="Optional RGB or RGBA override for roof elements; defaults to the selected palette")
    create_castle.add_argument("--layout", default=DEFAULT_LAYOUT, choices=sorted(LAYOUT_VARIANTS.keys()), help="Castle footprint/layout preset")
    create_castle.add_argument("--size", default=DEFAULT_SIZE, choices=sorted(SIZE_VARIANTS.keys()), help="Castle size preset")
    create_castle.add_argument("--palette", default=DEFAULT_PALETTE, choices=sorted(PALETTE_VARIANTS.keys()), help="Default color palette for stone and roof elements")
    create_castle.add_argument("--yaw", default=DEFAULT_YAW, type=float, help="Rotate the generated castle footprint around the origin in degrees")
    create_castle.set_defaults(replace_existing=True)
    create_castle.add_argument("--replace-existing", dest="replace_existing", action="store_true", help="Delete existing actors with the same labels before rebuilding (default)")
    create_castle.add_argument("--keep-existing", dest="replace_existing", action="store_false", help="Skip deletion and place the new castle without removing matching old actors first")
    create_castle.add_argument("--dry-run", action="store_true", help="Print the instantiated castle plan without spawning actors")
    create_castle.set_defaults(handler=_handle_create_basic_castle)

    verify_castle = subparsers.add_parser(
        "verify-basic-castle",
        help="Verify a castle created from the shared plan.",
        description="Verify that all expected castle actors exist by listing actors in the current level.",
        epilog="Examples:\n  unreal-mcp-cli verify-basic-castle --prefix SkillCastle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    verify_castle.add_argument("--prefix", default="Castle", help="Prefix used for the expected actor labels")
    verify_castle.set_defaults(handler=lambda args: _run_and_print(verify_basic_castle, args.prefix))

    reset_castle = subparsers.add_parser(
        "reset-basic-castle",
        help="Delete a castle built from the shared plan or prefix.",
        description="Delete castle actors by prefix. By default this removes all actors whose labels start with the prefix; use --strict-plan to only target plan-defined labels.",
        epilog="Examples:\n  unreal-mcp-cli reset-basic-castle --prefix SkillCastle\n  unreal-mcp-cli reset-basic-castle --prefix SkillCastle --strict-plan --dry-run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    reset_castle.add_argument("--prefix", default="Castle", help="Prefix used for actor labels")
    reset_castle.add_argument("--strict-plan", action="store_true", help="Delete only the labels defined by the shared castle plan")
    reset_castle.add_argument("--dry-run", action="store_true", help="Print deletion targets without removing actors")
    reset_castle.set_defaults(handler=lambda args: _run_and_print(reset_basic_castle, args.prefix, args.strict_plan, args.dry_run))

    return parser


def _handle_commands(args: argparse.Namespace) -> int:
    command_descriptions: Dict[str, str] = {
        "commands": "List available CLI commands.",
        "spawn-actor-from-blueprint": "Spawn an actor from a Blueprint class.",
        "spawn-static-mesh": "Spawn a static mesh actor from an asset path.",
        "create-static-mesh-actor": "Create a primitive static mesh actor.",
        "modify-actor": "Modify an existing actor.",
        "delete-actor": "Delete one actor by label.",
        "get-level-info": "Get the current level summary.",
        "list-available-assets": "Search assets in the project.",
        "search-assets-recursively": "Search assets recursively in common subfolders.",
        "get-actor-info": "Get detailed information about one actor.",
        "list-level-actors": "List actors in the current level.",
        "get-selected-actors": "Show the current editor selection.",
        "select-actors": "Select actors by label.",
        "save-current-level": "Save the current level.",
        "remote-call": "Call any Remote Control function.",
        "get-object-property": "Read a Remote Control property.",
        "set-object-property": "Write a Remote Control property.",
        "create-basic-castle": "Create a sample castle using primitive shapes.",
        "verify-basic-castle": "Verify a castle created from the shared plan.",
        "reset-basic-castle": "Delete a castle built from the shared plan or prefix.",
    }
    for name, description in command_descriptions.items():
        print(f"{name}\t{description}")
    return 0


def _handle_create_basic_castle(args: argparse.Namespace) -> int:
    origin = parse_origin(args.origin)
    stone_color = parse_color(args.stone_color) if args.stone_color else None
    roof_color = parse_color(args.roof_color) if args.roof_color else None
    return _run_and_print(
        create_basic_castle,
        args.prefix,
        origin,
        stone_color,
        roof_color,
        args.dry_run,
        args.replace_existing,
        args.layout,
        args.size,
        args.palette,
        args.yaw,
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
