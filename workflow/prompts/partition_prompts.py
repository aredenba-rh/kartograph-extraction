"""
Prompt templates for partition creation.

Provides the prompt for Claude to create file subsets from a data source.
"""

from typing import List


def build_partition_creation_prompt(data_source: str, data_source_path: str, special_commands: List[str], example_partition_path: str = "examples/partition_example") -> str:
    """
    Build the user message prompt for Claude to create file subsets for a single data source.
    
    Args:
        data_source: Name of the data source (e.g., "openshift-docs")
        data_source_path: Full path to the data source directory (e.g., "data/openshift-docs")
        special_commands: List of make commands available to the agent
        example_partition_path: Path to example partition structure
        
    Returns:
        Formatted prompt string
    """
    # Format special commands for display
    commands_list = "\n".join([f"  - `{cmd}`" for cmd in special_commands])
    
    prompt = f"""I'm building a Knowledge Graph from {data_source_path}. Your cwd is the project root. Key directories: `data/` and `scripts/`.


## Your Task
Create file subsets for all files in {data_source_path}. 
- **Each file must appear in exactly one file subset** (no duplicates, no missing files)
- **Do NOT modify {data_source_path}** — it is read-only


## Success Pattern (Follow These Steps)
1. **Explore**: Run `find {data_source_path} -type f | wc -l` and `find {data_source_path} -type d | sort` to understand file count and structure
2. **Plan**: Create scratch files in `/tmp/` to track which files go in each file subset title. 
    - Single file subset is not allowed - there must be multiple file subsets. Use the commands below to create them.
    - The file subsets should be disjoint and cover all files in {data_source_path}.
3. **Create**: Run `python3 scripts/create_file_subset.py "<data_source>" "<title>" "<description>" <path1> [path2] ...` for each file subset
4. **Validate**: Run `python3 scripts/validate_partition.py {data_source}`
5. **Complete**: Respond without tools when validation passes


## Available Commands
You have access to a **bash tool** that allows you to execute shell commands. Use ONLY these commands:
{commands_list}


## How to Create File Subsets
```bash
python3 scripts/create_file_subset.py "<data_source>" "<title>" "<description>" <path1> [path2] ...
```

**Arguments:**
- `<data_source>`: The data source name (ALWAYS use "{data_source}")
- `<title>`: Concise label (≤8 words) describing the file subset's content
- `<description>`: 2-3 sentences describing the files and their common characteristics
- `<paths>`: File/directory paths relative to {data_source_path}

**Path notation (paths are relative to {data_source_path}):**
- Directory: `"subfolder/"` = ALL files in that directory
- Specific file: `"subfolder/file.md"` = single file
- Top-level files: `"file.md"`

**DO NOT include `{data_source_path}` in PATHS - it's automatically prepended**

File subsets are saved to `partitions/{data_source}/file_subset_XX.json`


## Example File Subset Creation
If needed, `{example_partition_path}/README.md` outlines an example scenario for a data source and the commands to create file subsets for it.

Complete the steps of "## Success Pattern" above.
"""
    return prompt
