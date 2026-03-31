# Generic Remote Control and editor helper functions for Unreal Engine

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from .connection import get_unreal_connection
from .utils import parse_kwargs, validate_required_params

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UnrealRemote")

EDITOR_ACTOR_SUBSYSTEM = "/Script/UnrealEd.Default__EditorActorSubsystem"
EDITOR_LEVEL_LIBRARY = "/Script/EditorScriptingUtilities.Default__EditorLevelLibrary"


def _json_response(payload: Any) -> str:
    """Return a stable JSON string for MCP responses."""
    return json.dumps(payload, indent=2)


def _coerce_dict(value: Any, field_name: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Accept a dict directly or parse a JSON string into a dict."""
    if value is None:
        return {}, None

    if isinstance(value, dict):
        return value, None

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            return None, f"Invalid JSON for {field_name}: {str(exc)}"

        if not isinstance(parsed, dict):
            return None, f"{field_name} must be a JSON object"

        return parsed, None

    return None, f"{field_name} must be a dictionary or JSON object string"


def _split_labels(value: Any) -> List[str]:
    """Normalize actor label input into a list of labels."""
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str):
        return [item.strip() for item in value.split(',') if item.strip()]

    return [str(value).strip()]


def _resolve_object_path(params: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """Resolve an object path directly or through actor label and component class."""
    unreal = get_unreal_connection()

    object_path = params.get("object_path") or params.get("path")
    actor_label = params.get("actor_label")
    component_class = params.get("component_class")

    if not object_path and actor_label:
        object_path = unreal.find_actor_by_label(actor_label)
        if not object_path:
            return None, f"Actor '{actor_label}' not found in the current level."

    if not object_path:
        return None, "Missing required parameters: object_path or actor_label"

    if component_class:
        component_path = unreal.get_component_by_class(object_path, component_class)
        if not component_path:
            return None, f"Component '{component_class}' was not found on '{object_path}'"
        object_path = component_path

    return object_path, None


def _safe_function_call(object_path: str, function_name: str, parameters: Dict[str, Any] = None) -> Any:
    """Call a Remote Control function and return its ReturnValue when present."""
    unreal = get_unreal_connection()
    response = unreal.send_command(object_path, function_name, parameters)
    if isinstance(response, dict) and "ReturnValue" in response:
        return response.get("ReturnValue")
    return response


def call_remote_function(kwargs_str) -> str:
    """Call any Unreal Remote Control function via object path or actor label."""
    try:
        params = parse_kwargs(kwargs_str)
        valid, error_msg = validate_required_params(params, ["function_name"])
        if not valid:
            return error_msg

        object_path, object_error = _resolve_object_path(params)
        if object_error:
            return object_error

        parameters, param_error = _coerce_dict(params.get("parameters") or params.get("params"), "parameters")
        if param_error:
            return param_error

        generate_transaction = params.get("generate_transaction", True)
        unreal = get_unreal_connection()
        result = unreal.call_remote_function(
            object_path,
            params["function_name"],
            parameters,
            generate_transaction
        )

        return _json_response({
            "object_path": object_path,
            "function_name": params["function_name"],
            "result": result
        })
    except Exception as e:
        logger.error(f"Error calling remote function: {str(e)}")
        return f"Error calling remote function: {str(e)}"


def get_object_property(kwargs_str) -> str:
    """Read any Unreal object property via object path or actor label."""
    try:
        params = parse_kwargs(kwargs_str)
        valid, error_msg = validate_required_params(params, ["property_name"])
        if not valid:
            return error_msg

        object_path, object_error = _resolve_object_path(params)
        if object_error:
            return object_error

        unreal = get_unreal_connection()
        result = unreal.get_object_property(object_path, params["property_name"])

        return _json_response({
            "object_path": object_path,
            "property_name": params["property_name"],
            "result": result
        })
    except Exception as e:
        logger.error(f"Error getting object property: {str(e)}")
        return f"Error getting object property: {str(e)}"


def set_object_property(kwargs_str) -> str:
    """Write any Unreal object property via object path or actor label."""
    try:
        params = parse_kwargs(kwargs_str)
        valid, error_msg = validate_required_params(params, ["property_name"])
        if not valid:
            return error_msg

        if "property_value" not in params:
            return "Missing required parameters: property_value"

        object_path, object_error = _resolve_object_path(params)
        if object_error:
            return object_error

        generate_transaction = params.get("generate_transaction", True)
        unreal = get_unreal_connection()
        result = unreal.set_object_property(
            object_path,
            params["property_name"],
            params["property_value"],
            generate_transaction
        )

        return _json_response({
            "object_path": object_path,
            "property_name": params["property_name"],
            "result": result
        })
    except Exception as e:
        logger.error(f"Error setting object property: {str(e)}")
        return f"Error setting object property: {str(e)}"


def list_level_actors(kwargs_str=None) -> str:
    """List actors in the current level, optionally including transforms."""
    try:
        params = parse_kwargs(kwargs_str)
        name_filter = str(params.get("filter", "")).strip().lower()
        include_transforms = params.get("include_transforms", True)
        max_results = int(params.get("max_results", 100))

        unreal = get_unreal_connection()
        actor_paths = _safe_function_call(EDITOR_ACTOR_SUBSYSTEM, "GetAllLevelActors") or []

        actors: List[Dict[str, Any]] = []
        for actor_path in actor_paths:
            label = actor_path.split('.')[-1]
            try:
                actor_label = _safe_function_call(actor_path, "GetActorLabel")
                if actor_label:
                    label = actor_label
            except Exception as e:
                logger.warning(f"Could not read label for {actor_path}: {str(e)}")

            if name_filter and name_filter not in label.lower() and name_filter not in actor_path.lower():
                continue

            actor_info: Dict[str, Any] = {
                "label": label,
                "path": actor_path
            }

            if include_transforms:
                for function_name, key in [
                    ("GetActorLocation", "location"),
                    ("GetActorRotation", "rotation"),
                    ("GetActorScale3D", "scale")
                ]:
                    try:
                        actor_info[key] = _safe_function_call(actor_path, function_name)
                    except Exception as e:
                        logger.warning(f"Could not read {key} for {actor_path}: {str(e)}")

            actors.append(actor_info)
            if len(actors) >= max_results:
                break

        return _json_response({
            "total_found": len(actors),
            "filter": name_filter,
            "actors": actors
        })
    except Exception as e:
        logger.error(f"Error listing level actors: {str(e)}")
        return f"Error listing level actors: {str(e)}"


def get_selected_actors() -> str:
    """Return the current editor actor selection."""
    try:
        selected_paths = _safe_function_call(EDITOR_ACTOR_SUBSYSTEM, "GetSelectedLevelActors") or []
        selected = []

        for actor_path in selected_paths:
            label = actor_path.split('.')[-1]
            try:
                actor_label = _safe_function_call(actor_path, "GetActorLabel")
                if actor_label:
                    label = actor_label
            except Exception as e:
                logger.warning(f"Could not read selected actor label for {actor_path}: {str(e)}")

            selected.append({
                "label": label,
                "path": actor_path
            })

        return _json_response({
            "selected_count": len(selected),
            "actors": selected
        })
    except Exception as e:
        logger.error(f"Error getting selected actors: {str(e)}")
        return f"Error getting selected actors: {str(e)}"


def select_actors(kwargs_str) -> str:
    """Set the editor selection from a comma-separated or JSON list of actor labels."""
    try:
        params = parse_kwargs(kwargs_str)
        labels = _split_labels(
            params.get("actor_labels") or params.get("labels") or params.get("actor_label")
        )
        if not labels:
            return "Missing required parameters: actor_labels"

        replace_selection = params.get("replace_selection", True)
        unreal = get_unreal_connection()

        if replace_selection:
            try:
                unreal.send_command(EDITOR_ACTOR_SUBSYSTEM, "ClearActorSelectionSet")
            except Exception as e:
                logger.warning(f"Could not clear actor selection set: {str(e)}")

        selected_labels: List[str] = []
        missing_labels: List[str] = []
        for label in labels:
            actor_path = unreal.find_actor_by_label(label)
            if not actor_path:
                missing_labels.append(label)
                continue

            unreal.send_command(
                EDITOR_ACTOR_SUBSYSTEM,
                "SetActorSelectionState",
                {
                    "Actor": actor_path,
                    "bShouldBeSelected": True
                }
            )
            selected_labels.append(label)

        return _json_response({
            "selected": selected_labels,
            "not_found": missing_labels,
            "replace_selection": replace_selection
        })
    except Exception as e:
        logger.error(f"Error selecting actors: {str(e)}")
        return f"Error selecting actors: {str(e)}"


def save_current_level() -> str:
    """Save the currently open level."""
    try:
        result = _safe_function_call(EDITOR_LEVEL_LIBRARY, "SaveCurrentLevel")
        return _json_response({
            "saved": bool(result) if result is not None else True,
            "result": result
        })
    except Exception as e:
        logger.error(f"Error saving current level: {str(e)}")
        return f"Error saving current level: {str(e)}"
