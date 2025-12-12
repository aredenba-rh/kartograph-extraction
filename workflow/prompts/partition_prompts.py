"""
Prompt templates for partition creation.

Provides the prompt for Claude to create file partitions from a data source.
"""

from typing import List


def build_partition_creation_prompt(
    data_path: str,
    data_sources: List[str],
    special_commands: List[str],
    example_partition_path: str = "examples/partition_example"
) -> str:
    """
    Build the user message prompt for Claude to create partitions.
    
    Args:
        data_path: Path to the data directory (e.g., "data")
        data_sources: List of folders (data sources) within the data directory
        special_commands: List of make commands available to the agent
        example_partition_path: Path to example partition structure
        
    Returns:
        Formatted prompt string
    """
    # Format special commands for display
    commands_list = "\n".join([f"  - `{cmd}`" for cmd in special_commands])
    
    # Format data sources list for display
    data_sources_list = "\n".join([f"  - `{data_path}/{src}/`" for src in data_sources])
    data_sources_bullets = "\n".join([f"- `{src}/`" for src in data_sources])
    
    prompt = f"""I'm building a Knowledge Graph from all data sources in `{data_path}/`.


## Data Sources
The following data sources exist in `{data_path}/`:
{data_sources_list}


## Your Task
Create partitions for all files across ALL data sources in `{data_path}/`. 
- **Each file must appear in exactly one partition** (no duplicates, no missing files)
- **Do NOT modify `{data_path}/`** — it is read-only


## Success Pattern (Follow These Steps)
1. **Explore**: Run `find {data_path} -type f | wc -l` and `find {data_path} -type d | sort` to understand file count and structure across ALL data sources
2. **Plan**: Create scratch files in `/tmp/` to track which files go in each partition title. 
    - Single partition is not allowed - there must be multiple partitions. Use the commands below to create the partitions.
    - The partitions should be disjoint and cover all files across ALL data sources in `{data_path}/`.
3. **Create**: Run `python3 scripts/create_partition.py` for each partition
4. **Validate**: Run `make validate-partitions`
5. **Complete**: Respond without tools when validation passes





## CRITICAL RULE: No Entire Data Sources as Partition Paths
You **MUST NOT** use an entire data source folder as a partition path. The following paths are **FORBIDDEN** in any partition:
{data_sources_bullets}

Instead, you must specify more granular subdirectories or files within each data source. For example:
- ❌ WRONG: `openshift-docs/`
- ✅ CORRECT: `openshift-docs/rosa_architecture/`, `openshift-docs/modules/`, etc.


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
- `<paths>`: File/directory paths relative to `{data_path}/`

**Paths MUST include the data source folder name (e.g., `openshift-docs/`, `rosa-kcs/`, `ops-sop/`) as a prefix**

**DO NOT include `{data_path}/` in PATHS - it's automatically prepended**

**Path notation (paths are relative to `{data_path}/`):**
- Directory: `openshift-docs/subfolder/` = ALL files in that directory
- Specific file: `rosa-kcs/kcs_solutions/file.md` = single file
- Top-level files within a data source: `ops-sop/README.md`


## Example Partition Creation
If you need an example, look at the partitions at `{example_partition_path}/`

Complete the steps of "## Success Pattern" above.
"""
    return prompt

