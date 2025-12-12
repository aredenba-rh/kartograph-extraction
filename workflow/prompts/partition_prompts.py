"""
Prompt templates for partition creation.

Provides the prompt for Claude to create file partitions from a data source.
"""

from typing import List


def build_partition_creation_prompt(data_source_path: str, special_commands: List[str], example_partition_path: str = "examples/partition_example") -> str:
    """
    Build the user message prompt for Claude to create partitions.
    
    Args:
        data_source_path: Path to the data source directory
        special_commands: List of make commands available to the agent
        example_partition_path: Path to example partition structure
        
    Returns:
        Formatted prompt string
    """
    # Format special commands for display
    commands_list = "\n".join([f"  - `{cmd}`" for cmd in special_commands])
    
    prompt = f"""I'm building a Knowledge Graph from {data_source_path}.

## Success Pattern (Follow These Steps)
1. **Explore**: Run `find {data_source_path} -type f | wc -l` and `find {data_source_path} -type d | sort` to understand file count and structure
2. **Plan**: Create scratch files in `/tmp/` to track which files go in each partition title. 
    - Single partition is not allowed - there must be multiple partitions. Use the commands below to create the partitions.
    - The partitions should be disjoint and cover all files in {data_source_path}.
3. **Create**: Run `python3 scripts/create_partition.py` for each partition
4. **Validate**: Run `make validate-partitions`
5. **Complete**: Respond without tools when validation passes


## Your Task
Create partitions for all files in {data_source_path}. 
- **Each file must appear in exactly one partition** (no duplicates, no missing files)
- **Do NOT modify {data_source_path}** — it is read-only


## Available Commands
You have access to a **bash tool** that allows you to execute shell commands. Use ONLY these commands:
{commands_list}


## How to Create Partitions
```bash
python3 scripts/create_partition.py "<title>" "<description>" <path1> [path2] ...
```

**Arguments:**
- `<title>`: Concise label (≤8 words) describing the partition's content
- `<description>`: 2-3 sentences describing the files and their common characteristics
- `<paths>`: File/directory paths relative to {data_source_path}

**Path notation (paths are relative to {data_source_path}):**
- Directory: `"subfolder/"` = ALL files in that directory
- Specific file: `"subfolder/file.md"` = single file
- Top-level files: `"file.md"`

**DO NOT include `{data_source_path}` in PATHS - it's automatically prepended**


## Example Partition Creation
The partitions at `{example_partition_path}/` could be created from `{example_partition_path}/data/data_source_repo_name/` using the commands similar to:

```bash
python3 scripts/create_partition.py \\
  "Installation and Provisioning" \\
  "Documentation focused on cluster installation..." \\
  folderA/ folderB/fileBA.md fileA.md fileB.md
```

Complete the steps of "## Success Pattern" above.
"""
    return prompt

