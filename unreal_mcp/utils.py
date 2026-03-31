# Utility functions for the Unreal MCP server

import json
import logging
from typing import Any, Dict, List, Tuple

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UnrealUtils")


def parse_kwargs(kwargs_str) -> Dict[str, Any]:
    """Parse kwargs from string, dict, or JSON format to a unified dictionary."""
    if not kwargs_str:
        return {}

    if isinstance(kwargs_str, dict):
        return kwargs_str

    if isinstance(kwargs_str, str):
        if kwargs_str.strip().startswith("{") and kwargs_str.strip().endswith("}"):
            try:
                return json.loads(kwargs_str)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse as JSON: {kwargs_str}")

    kwargs = {}

    if isinstance(kwargs_str, str):
        parts = kwargs_str.split()

        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                kwargs[key] = parse_value(key, value)

    return kwargs


def parse_value(key: str, value: str) -> Any:
    """Parse a string value into the appropriate type based on key and content."""
    if "," in value and key in ["location", "rotation", "scale", "color", "material_color"]:
        return [float(x) for x in value.split(",")]

    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    try:
        if "." not in value:
            return int(value)
        return float(value)
    except ValueError:
        pass

    return value


def vector_to_ue_format(vector: List[float], keys: List[str] = None) -> Dict[str, float]:
    """Convert a vector list to Unreal Engine X/Y/Z or custom-key format."""
    if not keys:
        keys = ["X", "Y", "Z"]

    if not isinstance(vector, list) or len(vector) < len(keys):
        return {k: 0.0 if k != "A" else 1.0 for k in keys}

    result = {}
    for index, key in enumerate(keys):
        if index < len(vector):
            result[key] = float(vector[index])
        elif key == "A":
            result[key] = 1.0
        else:
            result[key] = 0.0

    return result


def format_transform_params(params: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """Format location, rotation, and scale parameters for Unreal Engine."""
    result = {}

    location = params.get("location")
    if location:
        result["location"] = vector_to_ue_format(location)

    rotation = params.get("rotation")
    if rotation:
        result["rotation"] = vector_to_ue_format(rotation, ["Pitch", "Yaw", "Roll"])

    scale = params.get("scale")
    if scale:
        result["scale"] = vector_to_ue_format(scale)

    return result


def get_common_actor_name(params: Dict[str, Any], default_name: str = "NewActor") -> str:
    """Get actor name from parameters, checking common variations."""
    return params.get("actor_label") or params.get("name") or params.get("label") or default_name


def validate_required_params(params: Dict[str, Any], required_keys: List[str]) -> Tuple[bool, str]:
    """Validate that required parameters are present."""
    missing = [key for key in required_keys if not params.get(key)]

    if missing:
        return False, f"Missing required parameters: {', '.join(missing)}"

    return True, ""


COMMON_SUBDIRS = [
    "",
    "/Blueprints",
    "/Meshes",
    "/StaticMeshes",
    "/Materials",
    "/Textures",
    "/FX",
    "/Audio",
    "/Animations"
]

BASIC_SHAPES = {
    "CUBE": "/Engine/BasicShapes/Cube.Cube",
    "SPHERE": "/Engine/BasicShapes/Sphere.Sphere",
    "CYLINDER": "/Engine/BasicShapes/Cylinder.Cylinder",
    "PLANE": "/Engine/BasicShapes/Plane.Plane",
    "CONE": "/Engine/BasicShapes/Cone.Cone"
}

ASSET_TYPE_IDENTIFIERS = {
    "blueprint": ["/blueprint", "/blueprints", "bp_", "_bp"],
    "staticmesh": ["/mesh", "/meshes", "/staticmesh", "/staticmeshes", "sm_", "_sm"],
    "material": ["/material", "/materials", "mat_", "_mat", "m_"],
    "texture": ["/texture", "/textures", "t_", "_t"],
    "sound": ["/sound", "/sounds", "/audio", "s_", "_s"],
    "particle": ["/fx", "/effect", "/effects", "/particle", "/particles", "fx_", "p_", "_p"],
    "animation": ["/anim", "/animation", "/animations", "a_", "_a"],
}