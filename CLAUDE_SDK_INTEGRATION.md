# Claude Code Agent SDK Integration Guide

This document explains how the kartograph-extraction framework integrates with the Claude Code Agent SDK.

## Three Pillars of Integration

### 1. Claude SDK Invocation for Partition Creation (Step 1.1)

The workflow invokes Claude Code Agent SDK to analyze the data source and create partitions:

```python
from claude_agent_sdk import create_agent

agent = create_agent(
    name="partition_creator",
    instructions="You are a data partitioning expert..."
)

result = agent.run(user_message)
```

**Dynamic Prompt Construction:**
- Data source path is injected dynamically
- Context about ROSA Ask-SRE assistant
- Instructions on partition strategy
- Available tools (create_partition.py)
- Examples from `examples/partition_example/`

### 2. Validation with Detailed Error Messages (Step 1.2)

After Claude creates partitions, `confirm_acceptable_partition.py` validates them:

**What it checks:**
- ✅ Complete coverage (all files in data/ are included)
- ✅ Disjoint partitions (no file appears multiple times)
- ✅ No invalid references (all paths exist)
- ✅ Directory path expansion (paths ending with `/`)

**Error Message Format:**

```
DUPLICATE FILES (appearing in multiple partitions):
  - data/rosa-kcs/file.md
    Found in partitions: 1, 2
    ⚠️  Please remove this file from all but ONE partition

MISSING FILES (in data/ but not in any partition):
  - data/rosa-kcs/missing.md
  ... and 15 more files
  ⚠️  Please add these 16 files to appropriate partitions
```

### 3. Validation Loop with Conditional Routing

**Flow:**

```
[Start] 
  → Step 1.1: Claude creates partitions
    → Step 1.2: Validate partitions
      ├─ Valid? → Route to Step 2.1 (Create Ontologies)
      └─ Invalid? → Send error message back to Step 1.1
         └─ Max retries? → Exit with error
```

**Retry Logic:**
- Maximum 3 attempts
- Error message fed back to Claude with specific fixes needed
- Claude can delete problematic partitions and recreate them

## Key Features

### Available Tools Field

Checklists now specify which scripts Claude can use:

```json
{
  "item_id": "1.1",
  "description": "Create partitions",
  "available_tools": ["create_partition"]
}
```

### Auto-Incrementing Partition IDs

The `create_partition.py` script automatically assigns integer IDs:
- Partition 1: `partition_01.json` with `"partition_id": 1`
- Partition 2: `partition_02.json` with `"partition_id": 2`

### Directory Path Support

Use trailing slash for directory paths:
- `"data/rosa-kcs/kcs_solutions/"` = all files in that directory
- `"data/rosa-kcs/README.md"` = specific file

The validation script automatically expands directory references.

## Prompt Engineering

### System Context

```
I'm creating a "ROSA Ask-SRE" Assistant. ROSA indicates "RedHat 
OpenShift on AWS" and an SRE is a "Site Reliability Engineer"...
```

### Task Definition

```
Analyze the contents at {data_source_path}, and create a partition 
of the files/paths there.
```

### Tool Instructions

```
Use the `create_partition.py` script located in the `scripts/` 
directory. Call it once for each partition you create.
```

### Examples

Reference to `examples/partition_example/` showing:
- Dummy data structure
- Successful partition files
- Complete and disjoint coverage

## Usage

```bash
# Start workflow (automatically invokes Claude)
python scripts/start_extraction_workflow.py

# The workflow will:
# 1. Build dynamic prompt for Claude
# 2. Invoke Claude Code Agent SDK
# 3. Validate created partitions
# 4. Retry with error feedback if needed
# 5. Route to next step when valid
```

## Configuration

The workflow reads from `extraction_config.json`:

```json
{
  "use_current_partition": false,  // If true, skip partition creation
  "use_current_ontologies": false  // If true, skip ontology creation
}
```

## Error Handling

**Validation Failures:**
- Detailed error messages show exactly which files are problematic
- Error message includes both duplicates AND missing files
- Claude receives this feedback for correction

**SDK Failures:**
- Exceptions during Claude execution are caught
- Workflow exits gracefully with error message
- Retry logic prevents infinite loops (max 3 attempts)

## Future Enhancements

- Make data source path configurable (currently hardcoded to rosa-kcs)
- Implement Step 2.1 (ontology creation) with Claude SDK
- Add more sophisticated prompt engineering
- Support for multiple simultaneous data sources

