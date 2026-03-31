---
name: unreal-castle-builder
description: 'Use when creating a castle, fortress, keep, walls, towers, or battlements in Unreal Engine with primitive shapes. Use this skill to inspect the Unreal CLI help, create the sample castle workflow, and verify the result by listing actors.'
argument-hint: 'Optional prefix or placement notes for the castle build'
user-invocable: true
---

# Unreal Castle Builder

## When To Use
- Build a quick castle or fortress prototype in Unreal Engine from basic shapes.
- Teach another agent how to drive this repository through the direct CLI instead of MCP tool discovery.
- Verify that a generated castle actually exists in the current level by listing actors.

## Procedure
1. Inspect the CLI entrypoint first.
   Run `unreal-mcp-cli --help`.
   If the editable script is not installed yet, run `.\.venv\Scripts\python.exe unreal_cli.py --help` instead.
2. Inspect the castle-specific commands.
   Run `unreal-mcp-cli create-basic-castle --help` and `unreal-mcp-cli list-level-actors --help`.
   Pay attention to the `--layout`, `--size`, `--palette`, `--yaw`, and `--origin` options so the castle can vary without changing the required actor set.
3. Review the shared castle layout in [examples/castle/assets/castle-plan.json](../../../examples/castle/assets/castle-plan.json).
4. Create the castle with a unique prefix so verification is unambiguous.
   Example: `unreal-mcp-cli create-basic-castle --prefix SkillCastle --layout courtyard --size grand --palette sandstone`
5. Verify the result by listing actors with the same prefix.
   Example: `unreal-mcp-cli list-level-actors --kwargs "filter=SkillCastle max_results=40"`
6. Run the dedicated verification command.
   Example: `unreal-mcp-cli verify-basic-castle --prefix SkillCastle`
7. If the user asks for cleanup or a rebuild, inspect `unreal-mcp-cli reset-basic-castle --help` and use it with the same prefix.
8. Report the created actor count, any missing labels, and whether the castle is complete.

## Expectations
- Do not save the level unless the user asks for it.
- Prefer a unique prefix per run to avoid collisions with prior castle attempts.
- Use named variation presets when the user asks for a different silhouette or mood; use `--origin` and `--yaw` when the user asks for a different placement.
- If verification fails, report the missing labels and stop instead of guessing.

## References
- [castle workflow notes](./references/castle-workflow.md)
- [examples/castle/assets/castle-plan.json](../../../examples/castle/assets/castle-plan.json)