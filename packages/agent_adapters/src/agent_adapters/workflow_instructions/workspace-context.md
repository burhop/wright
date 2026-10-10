Here are the instructions on how to use the loaded MCP tools within the Wright platform:

## Global Workspace Rules
1. **Workspace Path**: The absolute path to the current project workspace is `{{workspace_path}}`. All files and assets generated or modified during this session must reside directly within this folder or its subdirectories.
2. **Excluding System Temp/Hidden Paths**: Never write or export final requested outputs to system temporary directories (such as `/tmp/`, `/var/tmp/`, etc.).
3. **Explicit MCP Target Arguments**: When calling MCP tools to create models, save files, run simulations, or export files, explicitly specify their advertised target directory and output path parameters pointing to this active workspace or a subfolder inside it. Use exact tool schemas rather than relying on default temporary directories.
