# Unreal Engine MCP Server for Claude Desktop

This repository contains a Model Context Protocol (MCP) Python server that allows Claude Desktop to interact with Unreal Engine 5.3 (via Remote Control API), creating and manipulating 3D objects based on text prompts. This integration enables Claude to build and modify 3D scenes in Unreal Engine through natural language, representing an early step toward text-to-game-generation technology. 

Current Features:
- use Claude Desktop text prompts to arrange assets in Unreal Engine Editor
- create static meshes for assembling primitive shapes
- look up Unreal project folder for assets
- list actors in the current level and inspect the current editor selection
- save the current level from MCP
- call arbitrary Unreal Remote Control functions
- read and write Unreal object properties through the Remote Control property endpoint
- direct CLI with per-command `--help` for non-MCP agents
- shared castle workflow, sample agent skill, and TLA+ use-case model
- castle reset workflow and first-class castle MCP tools

![image](https://github.com/user-attachments/assets/f7d3d1e7-2057-41c1-bf5b-06734829a8aa)

![image](https://github.com/user-attachments/assets/394c3590-b54e-4824-a763-9df62b3d4cc1)


## Quick Start

### 1. Requirements
  - Python 3.10+
  - Unreal Engine 5.3 with Remote Control API (plugin) enabled

### 2. Installation
Clone the repository and install in editable mode:

```bash
git clone https://github.com/runeape-sats/unreal-mcp.git
cd unreal-mcp
pip install -e .
```

This installs the `unreal-mcp-cli` command and makes the `unreal_mcp` package importable.

### 3. Configure MCP server
- if you are using Claude Desktop → File → Settings → Developer → Edit Config `claude_desktop_config.json` and add the following, adjusting the path to your local repository:

```json
{
  "mcpServers": {
    "unreal-mcp": {
      "command": "uv",
      "args": ["--directory", "\\path\\to\\unreal-mcp", "run", "unreal_mcp_server.py"],
      "env": {}
    }
  }
}
```

If you already have other MCP servers configured (like `blender-mcp`), you may need to disable them to ensure they don't conflict.

### 4. Launch Unreal Engine
Open Unreal Engine with your project and ensure the Remote Control API plugin is enabled.

### 5. Launch MCP client (such as Claude Desktop)
- Restart Claude Desktop (i.e., need a clean exit without Claude's icon in the system tray) to load the new configuration. You can verify if it's connected by asking Claude to create objects in Unreal Engine.

## Project Structure

```
unreal_mcp/              # Core package
  __init__.py
  server.py              # MCP server — registers all tools
  cli.py                 # Direct CLI with subcommands and --help
  connection.py          # HTTP connection to Unreal Remote Control API
  actors.py              # Actor create / modify / delete helpers
  assets.py              # Asset discovery and level info
  remote.py              # Generic Remote Control and editor helpers
  utils.py               # Shared constants and parsing utilities

examples/                # Example workflows (separate from core)
  castle/
    workflow.py           # Castle build / verify / reset workflow
    assets/castle-plan.json
    specs/CastleConstruction.tla

tests/                   # Unit tests (20 tests)
  test_castle_assets.py
  test_castle_workflow.py
  test_unreal_cli.py
```

Root-level shim modules (`unreal_mcp_server.py`, `unreal_cli.py`, etc.) re-export from `unreal_mcp.*` for backward compatibility.

## Features

### Basic Object Creation

Create primitive shapes with a variety of parameters:
- Cubes, Spheres, Cylinders, Planes, Cones
- Custom position, rotation, scale
- Custom colors and materials

Example prompt: "Create a red cube at position 100, 200, 50"

### Blueprint Actor Creation

Spawn actors from Blueprint classes:
- Buildings, props, characters, etc.
- Custom parameters like in Basic Object Creation

Example prompt: "Spawn a bench from the blueprint at /Game/CustomAsset/Blueprints/BP_Bench01"

### Scene Manipulation

Modify existing objects:
- Change position, rotation, scale
- Adjust colors and materials
- Toggle visibility

Example prompt: "Move the cube to position 0, 0, 100 and rotate it 45 degrees"

### Editor Introspection And Selection

Inspect the current level and editor selection:
- List all actors in the current level, optionally with transforms
- Read the actors currently selected in the editor
- Select actors by label from MCP
- Save the current level after a batch of changes

Example prompt: "List all actors with 'Bench' in the label and then select them"

### Generic Remote Control Access

The server now exposes a generic Remote Control escape hatch so you can reach Unreal functionality that does not yet have a dedicated MCP tool:
- Call arbitrary functions on any object path
- Resolve an actor label to an object path automatically
- Target a component by class when reading or writing properties
- Read and write properties through `/remote/object/property`

This is useful for driving lights, post process volumes, components, editor subsystems, and custom Blueprint-exposed APIs without adding a new Python wrapper first.

### Direct CLI Access

Agents that do not speak MCP can use the direct CLI instead:
- `unreal-mcp-cli --help` lists all commands
- `unreal-mcp-cli <command> --help` shows how to use one function
- Commands route directly to the same Unreal helper modules used by the MCP server

Example commands:

```bash
unreal-mcp-cli commands
unreal-mcp-cli list-level-actors --kwargs "filter=Castle max_results=20"
unreal-mcp-cli remote-call --kwargs "actor_label=SkyLight function_name=GetActorLocation"
```

If you have not installed the editable script yet, use `.venv\Scripts\python.exe unreal_cli.py --help`.

### Castle Skill And TLA+ Model

The repo now includes:
- a reusable castle plan in `examples/castle/assets/castle-plan.json`
- a sample skill in `.github/skills/unreal-castle-builder/SKILL.md`
- a TLA+ use-case model in `examples/castle/specs/CastleConstruction.tla`
- dedicated castle create, verify, and reset entry points in both the CLI and MCP server

The castle workflow is designed so an agent can inspect CLI help, build a castle from basic shapes, and verify the result by listing actors.
The build workflow removes old castle actors with the same planned labels before placing the new ones by default. It now supports deterministic variation presets for layout, size, palette, and yaw while keeping the same required core actor set. The reset workflow deletes a castle by prefix, and the TLA+ model now covers retries, rebuilds, and variant selection as well as successful completion.

### Asset Discovery

Search for and list available assets:
- Filter by asset type (blueprints, meshes, materials)
- Search in specific paths
- Find assets matching certain terms

Example prompt: "List all bench static meshes in the project"

## Example Prompts

Here are some example prompts you can use with Claude:

```
Create a blue sphere at position 0, 100, 50 with scale 2, 2, 2

Create a scene with a red cube at 0,0,0, a green sphere at 100,0,0, and a blue cylinder at 0,100,0

List all blueprint assets in the /Game/CustomAsset folder

Get information about the current level

Create a cylinder and then change its color to yellow

List all actors whose label contains Bench

Show me the actors currently selected in the editor

Select actors Bench_A, Bench_B, and Bench_C

Save the current level

Set the intensity property on actor KeyLight to 5000

Call a remote function on actor SkyLight to recapture the scene

Use the CLI help for the castle workflow

Create a castle from basic shapes with prefix SkillCastle

Create a grand sandstone courtyard castle at a new placement

Verify the SkillCastle actors exist in the level

Reset the SkillCastle actors after verification
```

## New MCP Tools

In addition to the existing spawn, modify, delete, and asset lookup tools, the server now exposes:

- `list_level_actors`: List actors with optional filtering and transform data
- `get_selected_actors`: Inspect the current Unreal Editor selection
- `select_actors`: Select actors by label
- `save_current_level`: Save the open map
- `remote_call`: Call any Unreal Remote Control function by object path or actor label
- `get_object_property`: Read any Unreal object property
- `set_object_property`: Write any Unreal object property
- `create_basic_castle`: Build the shared primitive castle workflow directly from MCP
- `verify_basic_castle`: Verify the expected castle actor set by prefix
- `reset_basic_castle`: Delete castle actors by prefix or strict plan labels

The castle create entry point accepts `layout`, `size`, `palette`, `origin`, and `yaw` so agents can generate deliberate castle variants while the verification step still checks for the same required labels.

For complex `remote_call` or property writes, prefer JSON-shaped arguments so nested parameter structs survive parsing cleanly.

## CLI Setup

Install the project in editable mode inside your virtual environment to get the `unreal-mcp-cli` command:

```bash
.venv\Scripts\python.exe -m pip install -e .
unreal-mcp-cli --help
```

Useful command patterns:

```bash
unreal-mcp-cli create-static-mesh-actor --help
unreal-mcp-cli create-basic-castle --prefix SkillCastle --layout courtyard --size grand --palette sandstone
unreal-mcp-cli create-basic-castle --prefix Bastion01 --origin 6000,1200,0 --yaw 45 --palette obsidian
unreal-mcp-cli list-level-actors --kwargs "filter=SkillCastle max_results=40"
unreal-mcp-cli verify-basic-castle --prefix SkillCastle
unreal-mcp-cli reset-basic-castle --prefix SkillCastle --strict-plan
```

`create-basic-castle` replaces matching old castle actors by default. Use `--keep-existing` only if you explicitly want overlapping duplicates.
Named presets provide controlled variation: `--layout` changes the footprint, `--size` changes the overall scale, `--palette` changes default colors, and `--origin` or `--yaw` change placement/orientation.

## Tests

Run the automated tests with:

```bash
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

These tests cover the CLI surface, the shared castle plan, the TLA+ actor set, and the sample skill wiring.

## Troubleshooting

### Connection Issues

- Make sure Unreal Engine is running before starting the MCP server
- Ensure the Remote Control API plugin is enabled in Unreal Engine
- Check if another process is using port 30010
- Verify your firewall is not blocking the connection

### Objects Not Appearing

- Check the output log in Unreal Engine for any errors
- Make sure objects are not being created too far from the origin (0,0,0)
- Try simplifying your requests to isolate issues

### Logging

The server logs detailed information to the console. If you're having issues, check the logs for error messages and tracebacks.

## Development

To run the server in development mode:

```bash
pip install mcp[cli]
mcp dev unreal_mcp_server.py
```

## Contributing

Contributions are welcome! This is an integration between Claude and Unreal Engine, and there's much that can be improved:

- Better natural language processing for scene descriptions
- More complex object creation capabilities
- Supporting more Unreal Engine features
- Improved error handling and feedback

## License

[MIT License](LICENSE)
