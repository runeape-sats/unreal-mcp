# Castle Workflow Notes

This skill uses the direct Unreal CLI added to this repository.
The castle example implementation and formal model live under `examples/castle/`.

Recommended command order:
1. `unreal-mcp-cli commands`
2. `unreal-mcp-cli create-basic-castle --help`
3. `unreal-mcp-cli list-level-actors --help`
4. `unreal-mcp-cli create-basic-castle --prefix <Prefix> --layout <classic|courtyard|bastion|longhall> --size <compact|standard|grand> --palette <granite|sandstone|moss|obsidian>`
5. `unreal-mcp-cli list-level-actors --kwargs "filter=<Prefix> max_results=40"`
6. `unreal-mcp-cli verify-basic-castle --prefix <Prefix>`
7. `unreal-mcp-cli reset-basic-castle --prefix <Prefix>` when cleanup is requested

The castle plan contains:
- 1 keep
- 1 gatehouse
- 5 wall segments
- 4 towers
- 5 roof pieces

Verification succeeds only when every expected actor label with the chosen prefix exists in the current level.
The layout, size, palette, origin, and yaw may vary, but the verification target remains the same shared core actor set.