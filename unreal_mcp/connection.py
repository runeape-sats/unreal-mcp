# Handles connection and communication with Unreal Engine

import logging
from typing import Any, Dict, Optional

import requests

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UnrealConnection")


class UnrealConnection:
    """Class to manage connection to Unreal Engine Remote Control API."""

    def __init__(self, host: str = "127.0.0.1", port: int = 30010):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/remote"
        self.call_url = f"{self.base_url}/object/call"
        self.property_url = f"{self.base_url}/object/property"

    def test_connection(self) -> bool:
        """Test connection to Unreal Engine Remote Control API."""
        try:
            payload = {
                "objectPath": "/Script/UnrealEd.Default__EditorActorSubsystem",
                "functionName": "GetAllLevelActors"
            }

            response = requests.put(self.call_url, json=payload, timeout=5)
            response.raise_for_status()

            logger.info(f"Successfully connected to Unreal Engine at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Unreal Engine: {str(e)}")
            return False

    def _send_request(self, url: str, payload: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
        """Send a raw Remote Control request and return the JSON response."""
        try:
            response = requests.put(url, json=payload, timeout=timeout)
            response.raise_for_status()

            if not response.content:
                return {}

            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending request to Unreal Engine: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response details: {e.response.text}")
            raise Exception(f"Communication error with Unreal Engine: {str(e)}")
        except ValueError as e:
            logger.error(f"Failed to decode Unreal Engine response: {str(e)}")
            raise Exception(f"Invalid response from Unreal Engine: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")

    def call_remote_function(self,
                             object_path: str,
                             function_name: str,
                             parameters: Dict[str, Any] = None,
                             generate_transaction: bool = True) -> Dict[str, Any]:
        """Call a function on a remote Unreal object."""
        payload = {
            "objectPath": object_path,
            "functionName": function_name,
            "parameters": parameters or {},
            "generateTransaction": generate_transaction
        }

        if parameters:
            logger.info(f"Sending UE command: {function_name} with params: {parameters}")
        else:
            logger.info(f"Sending UE command: {function_name}")

        result = self._send_request(self.call_url, payload)
        logger.info(f"Command successful: {function_name}")
        return result

    def get_object_property(self,
                            object_path: str,
                            property_name: str,
                            access: str = "READ_ACCESS") -> Dict[str, Any]:
        """Read a property value through the Remote Control property endpoint."""
        payload = {
            "objectPath": object_path,
            "propertyName": property_name,
            "access": access
        }

        logger.info(f"Reading UE property: {property_name} on {object_path}")
        return self._send_request(self.property_url, payload)

    def set_object_property(self,
                            object_path: str,
                            property_name: str,
                            property_value: Any,
                            generate_transaction: bool = True,
                            access: str = "WRITE_ACCESS") -> Dict[str, Any]:
        """Write a property value through the Remote Control property endpoint."""
        payload = {
            "objectPath": object_path,
            "propertyName": property_name,
            "access": access,
            "propertyValue": property_value,
            "generateTransaction": generate_transaction
        }

        logger.info(f"Writing UE property: {property_name} on {object_path}")
        return self._send_request(self.property_url, payload)

    def send_command(self,
                     object_path: str,
                     function_name: str,
                     parameters: Dict[str, Any] = None,
                     generate_transaction: bool = True) -> Dict[str, Any]:
        """Send a command to Unreal Engine and return the response."""
        return self.call_remote_function(
            object_path,
            function_name,
            parameters,
            generate_transaction,
        )

    def find_actor_by_label(self, actor_label: str) -> Optional[str]:
        """Find an actor by its label and return its path."""
        try:
            actors_result = self.send_command(
                "/Script/UnrealEd.Default__EditorActorSubsystem",
                "GetAllLevelActors"
            )

            actors = actors_result.get("ReturnValue", [])

            for path in actors:
                try:
                    label_result = self.send_command(path, "GetActorLabel")
                    label = label_result.get("ReturnValue", "")

                    if label == actor_label:
                        return path
                except Exception:
                    if actor_label in path:
                        return path

            return None
        except Exception as e:
            logger.error(f"Error finding actor by label: {str(e)}")
            return None

    def get_component_by_class(self, actor_path: str, component_class: str) -> Optional[str]:
        """Get a component by its class from an actor."""
        try:
            result = self.send_command(
                actor_path,
                "GetComponentByClass",
                {"ComponentClass": component_class}
            )

            return result.get("ReturnValue")
        except Exception as e:
            logger.error(f"Error getting component: {str(e)}")
            return None


_unreal_connection = None


def get_unreal_connection():
    """Get or create a persistent Unreal connection."""
    global _unreal_connection

    if _unreal_connection is not None:
        try:
            if _unreal_connection.test_connection():
                return _unreal_connection
        except Exception as e:
            logger.warning(f"Existing connection is no longer valid: {str(e)}")
            _unreal_connection = None

    if _unreal_connection is None:
        _unreal_connection = UnrealConnection()
        if not _unreal_connection.test_connection():
            logger.error("Failed to connect to Unreal Engine")
            _unreal_connection = None
            raise Exception("Could not connect to Unreal Engine. Make sure Unreal Engine is running with Remote Control API enabled.")
        logger.info("Created new persistent connection to Unreal Engine")

    return _unreal_connection