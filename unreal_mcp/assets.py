# Functions for working with Unreal Engine assets

import json
import logging

from .connection import get_unreal_connection
from .utils import ASSET_TYPE_IDENTIFIERS, COMMON_SUBDIRS, parse_kwargs

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UnrealAssets")


def get_available_assets(kwargs_str) -> str:
    """Get a list of available assets of a specific type in the project."""
    try:
        unreal = get_unreal_connection()
        params = parse_kwargs(kwargs_str)

        asset_type = params.get("asset_type", "All").lower()
        search_path = params.get("search_path", "/Game")
        search_term = params.get("search_term", "")
        max_results = params.get("max_results", 20)
        recursive = params.get("recursive", True)

        if isinstance(recursive, str):
            recursive = recursive.lower() == "true"

        try:
            list_assets_result = unreal.send_command(
                "/Script/EditorScriptingUtilities.Default__EditorAssetLibrary",
                "ListAssets",
                {
                    "DirectoryPath": search_path,
                    "Recursive": recursive,
                    "IncludeFolder": True
                }
            )

            assets = list_assets_result.get("ReturnValue", [])
            logger.info(f"Found {len(assets)} total assets in {search_path}")

            filtered_assets = []
            for asset_path in assets:
                if not asset_path:
                    continue

                asset_path_lower = asset_path.lower()

                asset_type_match = True
                if asset_type != "all" and asset_type in ASSET_TYPE_IDENTIFIERS:
                    identifiers = ASSET_TYPE_IDENTIFIERS[asset_type]
                    if not any(identifier in asset_path_lower for identifier in identifiers):
                        asset_type_match = False

                search_term_match = True
                if search_term and search_term.lower() not in asset_path_lower:
                    search_term_match = False

                if asset_type_match and search_term_match:
                    filtered_assets.append(asset_path)

                if len(filtered_assets) >= max_results:
                    break

            result = {
                "asset_type": asset_type.capitalize() if asset_type != "all" else "All",
                "search_path": search_path,
                "search_term": search_term,
                "total_found": len(filtered_assets),
                "assets": filtered_assets
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error using EditorAssetLibrary: {str(e)}")

            try:
                get_assets_result = unreal.send_command(
                    "/Script/EditorScriptingUtilities.Default__EditorAssetLibrary",
                    "GetAssetsByPath",
                    {
                        "DirectoryPath": search_path,
                        "Recursive": recursive,
                        "IncludeFolder": True
                    }
                )

                assets = get_assets_result.get("ReturnValue", [])
                filtered_assets = []
                for asset_path in assets:
                    if not asset_path:
                        continue

                    asset_path_lower = asset_path.lower()

                    asset_type_match = True
                    if asset_type != "all" and asset_type in ASSET_TYPE_IDENTIFIERS:
                        identifiers = ASSET_TYPE_IDENTIFIERS[asset_type]
                        if not any(identifier in asset_path_lower for identifier in identifiers):
                            asset_type_match = False

                    search_term_match = True
                    if search_term and search_term.lower() not in asset_path_lower:
                        search_term_match = False

                    if asset_type_match and search_term_match:
                        filtered_assets.append(asset_path)

                    if len(filtered_assets) >= max_results:
                        break

                result = {
                    "asset_type": asset_type.capitalize() if asset_type != "all" else "All",
                    "search_path": search_path,
                    "search_term": search_term,
                    "total_found": len(filtered_assets),
                    "assets": filtered_assets
                }

                return json.dumps(result, indent=2)
            except Exception as e2:
                logger.error(f"Alternative approach also failed: {str(e2)}")
                return f"Error listing assets: {str(e)}. Alternative approach also failed: {str(e2)}"
    except Exception as e:
        logger.error(f"Error getting available assets: {str(e)}")
        return f"Error getting available assets: {str(e)}"


def search_assets_recursively(base_path: str, asset_type: str = None, search_term: str = None, max_results: int = 50) -> str:
    """Search for assets in all common subdirectories of a base path."""
    asset_type_param = f"asset_type={asset_type} " if asset_type else ""
    search_term_param = f"search_term={search_term} " if search_term else ""
    max_results_param = f"max_results={max_results}"

    all_assets = []

    for subdir in COMMON_SUBDIRS:
        search_path = f"{base_path}{subdir}"
        kwargs_str = f"{asset_type_param}search_path={search_path} {search_term_param}{max_results_param}"

        try:
            result_str = get_available_assets(kwargs_str)
            result = json.loads(result_str)

            if result and "assets" in result:
                found_assets = result.get("assets", [])
                all_assets.extend(found_assets)
                logger.info(f"Found {len(found_assets)} assets in {search_path}")
        except Exception as e:
            logger.warning(f"Error searching in {search_path}: {str(e)}")
            continue

    unique_assets = []
    for asset in all_assets:
        if asset not in unique_assets:
            unique_assets.append(asset)

    combined_result = {
        "asset_type": asset_type.capitalize() if asset_type else "All",
        "search_path": base_path,
        "search_term": search_term or "",
        "total_found": len(unique_assets),
        "assets": unique_assets[:max_results]
    }

    return json.dumps(combined_result, indent=2)


def get_level_info() -> str:
    """Get information about the current level."""
    try:
        unreal = get_unreal_connection()
        actors_result = unreal.send_command(
            "/Script/UnrealEd.Default__EditorActorSubsystem",
            "GetAllLevelActors"
        )

        actors = actors_result.get("ReturnValue", [])
        actors_info = []

        for actor_path in actors:
            try:
                actor_info = {"path": actor_path}

                try:
                    label_result = unreal.send_command(actor_path, "GetActorLabel")
                    actor_info["label"] = label_result.get("ReturnValue", "Unknown")
                except Exception as e:
                    logger.warning(f"Could not get label for actor {actor_path}: {str(e)}")
                    try:
                        actor_info["label"] = actor_path.split(".")[-1]
                    except Exception:
                        actor_info["label"] = "Unknown"

                try:
                    location_result = unreal.send_command(actor_path, "GetActorLocation")
                    actor_info["location"] = location_result.get("ReturnValue", {})
                except Exception as e:
                    logger.warning(f"Could not get location for actor {actor_path}: {str(e)}")
                    actor_info["location"] = "Unknown"

                actor_type = "Unknown"
                if "StaticMeshActor" in actor_path:
                    actor_type = "StaticMeshActor"
                elif "Light" in actor_path:
                    actor_type = "Light"
                elif "PlayerStart" in actor_path:
                    actor_type = "PlayerStart"
                elif "SkyAtmosphere" in actor_path:
                    actor_type = "SkyAtmosphere"
                elif "SkyLight" in actor_path:
                    actor_type = "SkyLight"
                elif "Fog" in actor_path:
                    actor_type = "Fog"
                elif "VolumetricCloud" in actor_path:
                    actor_type = "VolumetricCloud"

                actor_info["type"] = actor_type
                actors_info.append(actor_info)
            except Exception as e:
                logger.warning(f"Error getting details for actor {actor_path}: {str(e)}")
                actors_info.append({"path": actor_path, "error": str(e)})

        level_name = "Unknown"
        if actors:
            try:
                path_parts = actors[0].split(":")
                if path_parts:
                    map_part = path_parts[0]
                    level_name = map_part.split(".")[-1]
            except Exception as e:
                logger.warning(f"Error extracting level name: {str(e)}")

        level_info = {
            "level_name": level_name,
            "actor_count": len(actors),
            "actors": actors_info
        }

        return json.dumps(level_info, indent=2)
    except Exception as e:
        logger.error(f"Error getting level info: {str(e)}")
        return f"Error getting level info: {str(e)}"