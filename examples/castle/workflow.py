# Shared castle example workflow used by the CLI, skill, tests, and formal model

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List

from unreal_mcp.actors import create_static_mesh_actor, delete_actor
from unreal_mcp.remote import list_level_actors

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UnrealCastle")

CASTLE_PLAN_PATH = Path(__file__).parent / "assets" / "castle-plan.json"
DEFAULT_PREFIX = "Castle"
DEFAULT_ORIGIN = [0.0, 0.0, 0.0]
DEFAULT_LAYOUT = "classic"
DEFAULT_SIZE = "standard"
DEFAULT_PALETTE = "granite"
DEFAULT_YAW = 0.0

PALETTE_VARIANTS: Dict[str, Dict[str, List[float]]] = {
    "granite": {
        "stone": [0.62, 0.62, 0.66],
        "roof": [0.29, 0.18, 0.12],
    },
    "sandstone": {
        "stone": [0.76, 0.71, 0.58],
        "roof": [0.55, 0.31, 0.18],
    },
    "moss": {
        "stone": [0.48, 0.56, 0.47],
        "roof": [0.25, 0.19, 0.12],
    },
    "obsidian": {
        "stone": [0.18, 0.2, 0.25],
        "roof": [0.48, 0.12, 0.1],
    },
}

SIZE_VARIANTS: Dict[str, Dict[str, float]] = {
    "compact": {
        "footprint_scale": 0.82,
        "height_scale": 0.9,
        "mesh_scale": 0.92,
    },
    "standard": {
        "footprint_scale": 1.0,
        "height_scale": 1.0,
        "mesh_scale": 1.0,
    },
    "grand": {
        "footprint_scale": 1.24,
        "height_scale": 1.18,
        "mesh_scale": 1.16,
    },
}

LAYOUT_VARIANTS: Dict[str, Dict[str, Any]] = {
    "classic": {
        "footprint_scale": [1.0, 1.0],
        "role_offset": {},
        "role_scale": {},
    },
    "courtyard": {
        "footprint_scale": [1.18, 1.22],
        "role_offset": {
            "Keep": [0.0, 220.0, 0.0],
            "Gatehouse": [0.0, -260.0, 0.0],
            "Tower": [0.0, 0.0, 30.0],
            "Roof": [0.0, 0.0, 40.0],
        },
        "role_scale": {
            "Keep": [0.94, 0.94, 1.06],
            "Gatehouse": [1.12, 1.0, 1.0],
            "Wall": [1.06, 1.0, 1.0],
            "Tower": [1.08, 1.08, 1.12],
            "Roof": [1.05, 1.05, 1.08],
        },
    },
    "bastion": {
        "footprint_scale": [1.32, 0.92],
        "role_offset": {
            "Keep": [0.0, 80.0, 30.0],
            "Gatehouse": [0.0, -180.0, 0.0],
            "Tower": [0.0, 0.0, 50.0],
        },
        "role_scale": {
            "Keep": [1.08, 1.08, 1.12],
            "Gatehouse": [1.18, 1.05, 1.08],
            "Wall": [1.0, 1.0, 1.12],
            "Tower": [1.22, 1.22, 1.18],
            "Roof": [1.12, 1.12, 1.1],
        },
    },
    "longhall": {
        "footprint_scale": [0.88, 1.35],
        "role_offset": {
            "Keep": [0.0, 200.0, 0.0],
            "Gatehouse": [0.0, -380.0, 0.0],
            "Wall": [0.0, 0.0, -10.0],
        },
        "role_scale": {
            "Keep": [1.02, 0.88, 1.04],
            "Gatehouse": [0.94, 1.2, 1.0],
            "Wall": [0.92, 1.08, 1.0],
            "Tower": [0.95, 0.95, 1.06],
            "Roof": [0.96, 0.9, 1.02],
        },
    },
}

DEFAULT_STONE_COLOR = list(PALETTE_VARIANTS[DEFAULT_PALETTE]["stone"])
DEFAULT_ROOF_COLOR = list(PALETTE_VARIANTS[DEFAULT_PALETTE]["roof"])


def _load_plan_file() -> Dict[str, Any]:
    with CASTLE_PLAN_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_vector(value: str) -> List[float]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if len(parts) != 3:
        raise ValueError("Expected a comma-separated vector with 3 components")
    return [float(part) for part in parts]


def _make_label(prefix: str, suffix: str) -> str:
    return f"{prefix}_{suffix}" if prefix else suffix


def _get_variant_or_raise(name: str, variants: Dict[str, Any], variant_type: str) -> Any:
    if name not in variants:
        supported = ", ".join(sorted(variants.keys()))
        raise ValueError(f"Unsupported {variant_type} '{name}'. Supported values: {supported}")
    return variants[name]


def _get_actor_role(entry: Dict[str, Any]) -> str:
    suffix = entry["label_suffix"]
    if suffix == "Keep":
        return "Keep"
    if suffix == "Gatehouse":
        return "Gatehouse"
    if suffix.startswith("Wall"):
        return "Wall"
    if suffix.startswith("Tower"):
        return "Tower"
    if suffix.startswith("Roof"):
        return "Roof"
    return "Generic"


def _resolve_palette_colors(stone_color: List[float] = None,
                            roof_color: List[float] = None,
                            palette: str = DEFAULT_PALETTE) -> List[List[float]]:
    palette_values = _get_variant_or_raise(palette, PALETTE_VARIANTS, "palette")
    return [
        list(stone_color or palette_values["stone"]),
        list(roof_color or palette_values["roof"]),
    ]


def _rotate_xy(location: List[float], yaw_degrees: float) -> List[float]:
    if not yaw_degrees:
        return [float(value) for value in location]

    radians = math.radians(float(yaw_degrees))
    cos_value = math.cos(radians)
    sin_value = math.sin(radians)
    x_value = float(location[0]) * cos_value - float(location[1]) * sin_value
    y_value = float(location[0]) * sin_value + float(location[1]) * cos_value
    return [round(x_value, 4), round(y_value, 4), float(location[2])]


def _apply_yaw_to_rotation(rotation: List[float], yaw_degrees: float) -> List[float]:
    result = [float(value) for value in rotation]
    if len(result) != 3:
        raise ValueError("Expected rotation with 3 components")
    result[1] = round(result[1] + float(yaw_degrees), 4)
    return result


def _build_variation_metadata(origin: List[float],
                              layout: str,
                              size: str,
                              palette: str,
                              yaw: float) -> Dict[str, Any]:
    return {
        "origin": [float(value) for value in origin],
        "layout": layout,
        "size": size,
        "palette": palette,
        "yaw": float(yaw),
    }


def load_castle_plan() -> Dict[str, Any]:
    return _load_plan_file()


def get_expected_castle_labels(prefix: str = DEFAULT_PREFIX) -> List[str]:
    return [instance["actor_label"] for instance in build_castle_instances(prefix)]


def build_castle_instances(prefix: str = DEFAULT_PREFIX,
                           origin: List[float] = None,
                           stone_color: List[float] = None,
                           roof_color: List[float] = None,
                           layout: str = DEFAULT_LAYOUT,
                           size: str = DEFAULT_SIZE,
                           palette: str = DEFAULT_PALETTE,
                           yaw: float = DEFAULT_YAW) -> List[Dict[str, Any]]:
    plan = _load_plan_file()
    origin = origin or DEFAULT_ORIGIN
    size_variant = _get_variant_or_raise(size, SIZE_VARIANTS, "size")
    layout_variant = _get_variant_or_raise(layout, LAYOUT_VARIANTS, "layout")
    stone_color, roof_color = _resolve_palette_colors(stone_color, roof_color, palette)
    yaw = float(yaw)

    instances: List[Dict[str, Any]] = []
    for entry in plan["actors"]:
        role = _get_actor_role(entry)
        color_role = entry.get("color_role", "stone")
        color = stone_color if color_role == "stone" else roof_color
        role_offset = layout_variant.get("role_offset", {}).get(role, [0.0, 0.0, 0.0])
        role_scale = layout_variant.get("role_scale", {}).get(role, [1.0, 1.0, 1.0])
        scaled_local = [
            float(entry["location"][0]) * size_variant["footprint_scale"] * layout_variant["footprint_scale"][0] + float(role_offset[0]),
            float(entry["location"][1]) * size_variant["footprint_scale"] * layout_variant["footprint_scale"][1] + float(role_offset[1]),
            float(entry["location"][2]) * size_variant["height_scale"] + float(role_offset[2]),
        ]
        rotated_local = _rotate_xy(scaled_local, yaw)
        location = [
            float(origin[0]) + float(rotated_local[0]),
            float(origin[1]) + float(rotated_local[1]),
            float(origin[2]) + float(rotated_local[2])
        ]
        scale = [
            round(float(entry["scale"][0]) * size_variant["mesh_scale"] * float(role_scale[0]), 4),
            round(float(entry["scale"][1]) * size_variant["mesh_scale"] * float(role_scale[1]), 4),
            round(float(entry["scale"][2]) * size_variant["mesh_scale"] * size_variant["height_scale"] * float(role_scale[2]), 4),
        ]
        params = {
            "actor_label": _make_label(prefix, entry["label_suffix"]),
            "mesh_type": entry["mesh_type"],
            "location": location,
            "scale": scale,
            "color": color
        }

        if "rotation" in entry or yaw:
            params["rotation"] = _apply_yaw_to_rotation(entry.get("rotation", [0.0, 0.0, 0.0]), yaw)

        instances.append(params)

    return instances


def create_basic_castle(prefix: str = DEFAULT_PREFIX,
                        origin: List[float] = None,
                        stone_color: List[float] = None,
                        roof_color: List[float] = None,
                        dry_run: bool = False,
                        replace_existing: bool = True,
                        layout: str = DEFAULT_LAYOUT,
                        size: str = DEFAULT_SIZE,
                        palette: str = DEFAULT_PALETTE,
                        yaw: float = DEFAULT_YAW) -> str:
    try:
        origin = origin or DEFAULT_ORIGIN
        variation = _build_variation_metadata(origin, layout, size, palette, yaw)
        instances = build_castle_instances(prefix, origin, stone_color, roof_color, layout, size, palette, yaw)
        if dry_run:
            return json.dumps({
                "prefix": prefix,
                "variation": variation,
                "actor_count": len(instances),
                "actors": instances
            }, indent=2)

        deleted = []
        if replace_existing:
            reset_result = json.loads(reset_basic_castle(prefix, strict_plan=True))
            deleted = reset_result.get("deleted", [])

        created = []
        failures = []
        for instance in instances:
            result = create_static_mesh_actor(instance)
            if result.startswith("Successfully"):
                created.append(instance["actor_label"])
            else:
                failures.append({
                    "actor_label": instance["actor_label"],
                    "error": result
                })

        return json.dumps({
            "prefix": prefix,
            "variation": variation,
            "deleted": deleted,
            "created_count": len(created),
            "created": created,
            "failed_count": len(failures),
            "failures": failures
        }, indent=2)
    except Exception as e:
        logger.error(f"Error creating basic castle: {str(e)}")
        return f"Error creating basic castle: {str(e)}"


def verify_basic_castle(prefix: str = DEFAULT_PREFIX) -> str:
    try:
        expected_labels = get_expected_castle_labels(prefix)
        actor_result = list_level_actors(json.dumps({
            "filter": prefix,
            "max_results": len(expected_labels) + 20,
            "include_transforms": True
        }))
        parsed = json.loads(actor_result)

        found_labels = [actor["label"] for actor in parsed.get("actors", [])]
        missing = [label for label in expected_labels if label not in found_labels]
        matched = [label for label in expected_labels if label in found_labels]
        unexpected = [label for label in found_labels if label not in expected_labels]

        return json.dumps({
            "prefix": prefix,
            "expected_count": len(expected_labels),
            "matched_count": len(matched),
            "is_complete": not missing,
            "matched": matched,
            "missing": missing,
            "unexpected": unexpected,
            "found": parsed.get("actors", [])
        }, indent=2)
    except Exception as e:
        logger.error(f"Error verifying basic castle: {str(e)}")
        return f"Error verifying basic castle: {str(e)}"


def reset_basic_castle(prefix: str = DEFAULT_PREFIX,
                       strict_plan: bool = False,
                       dry_run: bool = False) -> str:
    try:
        actor_result = list_level_actors(json.dumps({
            "filter": prefix,
            "max_results": 200,
            "include_transforms": False
        }))
        parsed = json.loads(actor_result)
        found_actors = parsed.get("actors", [])
        found_labels = [actor["label"] for actor in found_actors]

        if strict_plan:
            expected_labels = set(get_expected_castle_labels(prefix))
            target_labels = [label for label in found_labels if label in expected_labels]
        else:
            prefix_with_sep = f"{prefix}_"
            target_labels = [label for label in found_labels if label == prefix or label.startswith(prefix_with_sep)]

        if dry_run:
            return json.dumps({
                "prefix": prefix,
                "strict_plan": strict_plan,
                "deleted": [],
                "delete_count": len(target_labels),
                "targets": target_labels
            }, indent=2)

        deleted = []
        failures = []
        for label in target_labels:
            result = delete_actor(label)
            if result.startswith("Successfully"):
                deleted.append(label)
            else:
                failures.append({
                    "actor_label": label,
                    "error": result
                })

        return json.dumps({
            "prefix": prefix,
            "strict_plan": strict_plan,
            "delete_count": len(deleted),
            "deleted": deleted,
            "failed_count": len(failures),
            "failures": failures
        }, indent=2)
    except Exception as e:
        logger.error(f"Error resetting basic castle: {str(e)}")
        return f"Error resetting basic castle: {str(e)}"


def parse_origin(value: str) -> List[float]:
    return _parse_vector(value)


def parse_color(value: str) -> List[float]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if len(parts) not in (3, 4):
        raise ValueError("Expected a comma-separated color with 3 or 4 components")
    return [float(part) for part in parts]