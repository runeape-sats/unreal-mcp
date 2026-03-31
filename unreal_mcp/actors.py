# Core functions for actor creation and manipulation

import json
import logging
from typing import Any, Dict, Optional

from .connection import get_unreal_connection
from .utils import (
    BASIC_SHAPES,
    format_transform_params,
    get_common_actor_name,
    parse_kwargs,
    validate_required_params,
)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UnrealActors")


def spawn_actor_base(actor_class: str, params: Dict[str, Any]) -> Optional[str]:
    """Base function to spawn an actor from any class."""
    try:
        unreal = get_unreal_connection()
        transform = format_transform_params(params)
        name = get_common_actor_name(params)

        spawn_params = {
            "ActorClass": actor_class,
        }

        if "location" in transform:
            spawn_params["Location"] = transform["location"]

        if "rotation" in transform:
            spawn_params["Rotation"] = transform["rotation"]

        spawn_result = unreal.send_command(
            "/Script/EditorScriptingUtilities.Default__EditorLevelLibrary",
            "SpawnActorFromClass",
            spawn_params
        )

        actor_path = spawn_result.get("ReturnValue", "")

        if not actor_path:
            logger.error(f"Failed to spawn actor of class {actor_class}")
            return None

        unreal.send_command(
            actor_path,
            "SetActorLabel",
            {"NewActorLabel": name}
        )

        if "scale" in transform:
            unreal.send_command(
                actor_path,
                "SetActorScale3D",
                {"NewScale3D": transform["scale"]}
            )

        return actor_path
    except Exception as e:
        logger.error(f"Error in spawn_actor_base: {str(e)}")
        return None


def create_static_mesh_actor(kwargs_str) -> str:
    """Create a new static mesh actor with a basic shape or custom mesh."""
    try:
        unreal = get_unreal_connection()
        params = parse_kwargs(kwargs_str)

        mesh_type = params.get("mesh_type", "CUBE").upper()
        mesh_path = params.get("static_mesh_asset_path") or params.get("static_mesh")

        if not mesh_path:
            if mesh_type in BASIC_SHAPES:
                mesh_path = BASIC_SHAPES[mesh_type]
            else:
                return f"Error: Unsupported mesh type '{mesh_type}'. Supported types are: {', '.join(BASIC_SHAPES.keys())}"

        name = get_common_actor_name(params, f"My{mesh_type.capitalize()}")
        actor_path = spawn_actor_base("/Script/Engine.StaticMeshActor", params)

        if not actor_path:
            return "Error: Failed to spawn static mesh actor"

        component_path = unreal.get_component_by_class(
            actor_path,
            "/Script/Engine.StaticMeshComponent"
        )

        if not component_path:
            return "Error: Failed to get StaticMeshComponent"

        unreal.send_command(
            component_path,
            "SetStaticMesh",
            {"NewMesh": mesh_path}
        )

        material_override = params.get("material_override")
        color = params.get("color") or params.get("material_color")

        if material_override:
            unreal.send_command(
                component_path,
                "SetMaterial",
                {"ElementIndex": 0, "Material": material_override}
            )
        elif color and isinstance(color, list) and len(color) >= 3:
            create_mat_result = unreal.send_command(
                component_path,
                "CreateDynamicMaterialInstance",
                {"ElementIndex": 0, "SourceMaterial": "/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"}
            )

            material_path = create_mat_result.get("ReturnValue", "")

            if material_path:
                color_param = {"R": color[0], "G": color[1], "B": color[2], "A": 1.0}
                if len(color) >= 4:
                    color_param["A"] = color[3]

                unreal.send_command(
                    material_path,
                    "SetVectorParameterValue",
                    {
                        "ParameterName": "Color",
                        "Value": color_param
                    }
                )

        return f"Successfully created {name} actor at position {params.get('location', [0, 0, 0])}"
    except Exception as e:
        logger.error(f"Error in create_static_mesh_actor: {str(e)}")
        return f"Error creating static mesh actor: {str(e)}"


def spawn_actor_from_blueprint(kwargs_str) -> str:
    """Spawn an actor from a blueprint class."""
    try:
        params = parse_kwargs(kwargs_str)
        actor_class = params.get("actor_class") or params.get("class")

        valid, error_msg = validate_required_params(params, ["actor_class"])
        if not valid:
            return error_msg

        actor_path = spawn_actor_base(actor_class, params)

        if not actor_path:
            return f"Error: Failed to spawn actor from blueprint class: {actor_class}"

        name = get_common_actor_name(params, "BlueprintActor")
        return f"Successfully created actor '{name}' from blueprint class '{actor_class}'"
    except Exception as e:
        logger.error(f"Error in spawn_actor_from_blueprint: {str(e)}")
        return f"Error spawning actor from blueprint: {str(e)}"


def spawn_static_mesh_actor_from_mesh(kwargs_str) -> str:
    """Spawn a static mesh actor using an existing static mesh asset."""
    try:
        params = parse_kwargs(kwargs_str)
        static_mesh = params.get("static_mesh") or params.get("mesh")

        valid, error_msg = validate_required_params(params, ["static_mesh"])
        if not valid:
            return error_msg

        params["static_mesh_asset_path"] = static_mesh
        return create_static_mesh_actor(params)
    except Exception as e:
        logger.error(f"Error in spawn_static_mesh_actor_from_mesh: {str(e)}")
        return f"Error spawning static mesh actor: {str(e)}"


def modify_actor(kwargs_str) -> str:
    """Modify an existing actor in the level."""
    try:
        unreal = get_unreal_connection()
        params = parse_kwargs(kwargs_str)
        actor_label = params.get("actor_label")

        valid, error_msg = validate_required_params(params, ["actor_label"])
        if not valid:
            return error_msg

        actor_path = unreal.find_actor_by_label(actor_label)

        if not actor_path:
            return f"Actor '{actor_label}' not found in the current level."

        transform = format_transform_params(params)

        if "location" in transform:
            unreal.send_command(actor_path, "SetActorLocation", {"NewLocation": transform["location"]})

        if "rotation" in transform:
            unreal.send_command(actor_path, "SetActorRotation", {"NewRotation": transform["rotation"]})

        if "scale" in transform:
            unreal.send_command(actor_path, "SetActorScale3D", {"NewScale3D": transform["scale"]})

        visible = params.get("visible")
        if visible is not None:
            unreal.send_command(actor_path, "SetActorHiddenInGame", {"NewHidden": not visible})

        color = params.get("color") or params.get("material_color")
        if color and isinstance(color, list) and len(color) >= 3:
            component_path = unreal.get_component_by_class(
                actor_path,
                "/Script/Engine.StaticMeshComponent"
            )

            if component_path:
                create_mat_result = unreal.send_command(
                    component_path,
                    "CreateDynamicMaterialInstance",
                    {"ElementIndex": 0, "SourceMaterial": "/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"}
                )

                material_path = create_mat_result.get("ReturnValue", "")

                if material_path:
                    color_param = {"R": color[0], "G": color[1], "B": color[2], "A": 1.0}
                    if len(color) >= 4:
                        color_param["A"] = color[3]

                    unreal.send_command(
                        material_path,
                        "SetVectorParameterValue",
                        {
                            "ParameterName": "Color",
                            "Value": color_param
                        }
                    )

        return f"Successfully modified actor: {actor_label}"
    except Exception as e:
        logger.error(f"Error in modify_actor: {str(e)}")
        return f"Error modifying actor: {str(e)}"


def get_actor_info(actor_label: str) -> str:
    """Get detailed information about an actor."""
    try:
        unreal = get_unreal_connection()
        actor_path = unreal.find_actor_by_label(actor_label)

        if not actor_path:
            return f"Actor '{actor_label}' not found in the current level."

        info = {
            "path": actor_path,
            "label": actor_label
        }

        try:
            location_result = unreal.send_command(actor_path, "GetActorLocation")
            info["location"] = location_result.get("ReturnValue", {})
        except Exception as e:
            logger.warning(f"Could not get location for actor {actor_path}: {str(e)}")
            info["location"] = "Not available"

        try:
            rotation_result = unreal.send_command(actor_path, "GetActorRotation")
            info["rotation"] = rotation_result.get("ReturnValue", {})
        except Exception as e:
            logger.warning(f"Could not get rotation for actor {actor_path}: {str(e)}")
            info["rotation"] = "Not available"

        try:
            scale_result = unreal.send_command(actor_path, "GetActorScale3D")
            info["scale"] = scale_result.get("ReturnValue", {})
        except Exception as e:
            logger.warning(f"Could not get scale for actor {actor_path}: {str(e)}")
            info["scale"] = "Not available"

        try:
            bounds_result = unreal.send_command(
                actor_path,
                "GetActorBounds",
                {"bOnlyCollidingComponents": False}
            )

            if bounds_result:
                origin = bounds_result.get("Origin", {})
                box_extent = bounds_result.get("BoxExtent", {})

                min_point = {
                    "X": origin.get("X", 0) - box_extent.get("X", 0),
                    "Y": origin.get("Y", 0) - box_extent.get("Y", 0),
                    "Z": origin.get("Z", 0) - box_extent.get("Z", 0)
                }

                max_point = {
                    "X": origin.get("X", 0) + box_extent.get("X", 0),
                    "Y": origin.get("Y", 0) + box_extent.get("Y", 0),
                    "Z": origin.get("Z", 0) + box_extent.get("Z", 0)
                }

                info["bounding_box"] = {
                    "origin": origin,
                    "extent": box_extent,
                    "min": min_point,
                    "max": max_point,
                    "size": {
                        "X": box_extent.get("X", 0) * 2,
                        "Y": box_extent.get("Y", 0) * 2,
                        "Z": box_extent.get("Z", 0) * 2
                    }
                }
            else:
                info["bounding_box"] = "Not available"
        except Exception as e:
            logger.warning(f"Could not get bounding box for actor {actor_path}: {str(e)}")
            info["bounding_box"] = "Not available"

        actor_type = "Unknown"
        if "StaticMeshActor" in actor_path:
            actor_type = "StaticMeshActor"

            component_path = unreal.get_component_by_class(
                actor_path,
                "/Script/Engine.StaticMeshComponent"
            )

            if component_path:
                try:
                    mesh_result = unreal.send_command(component_path, "GetStaticMesh")
                    info["static_mesh"] = mesh_result.get("ReturnValue", "")
                except Exception:
                    info["static_mesh"] = "Not available"

                try:
                    material_result = unreal.send_command(
                        component_path,
                        "GetMaterial",
                        {"ElementIndex": 0}
                    )
                    info["material"] = material_result.get("ReturnValue", "")
                except Exception:
                    info["material"] = "Not available"

                try:
                    comp_bounds_result = unreal.send_command(component_path, "GetBounds")
                    if comp_bounds_result:
                        info["component_bounds"] = comp_bounds_result.get("ReturnValue", {})
                except Exception as e:
                    logger.warning(f"Could not get component bounds for {component_path}: {str(e)}")
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

        info["type"] = actor_type
        return json.dumps(info, indent=2)
    except Exception as e:
        logger.error(f"Error getting actor info: {str(e)}")
        return f"Error getting actor info: {str(e)}"


def delete_actor(actor_label: str) -> str:
    """Delete an actor from the current level by its label."""
    try:
        unreal = get_unreal_connection()
        actor_path = unreal.find_actor_by_label(actor_label)

        if not actor_path:
            return f"Actor '{actor_label}' not found in the current level."

        unreal.send_command(
            actor_path,
            "DestroyActor",
            {"ActorTarget": actor_path}
        )

        return f"Successfully deleted actor '{actor_label}'"
    except Exception as e:
        logger.error(f"Error in delete_actor: {str(e)}")
        return f"Error deleting actor: {str(e)}"