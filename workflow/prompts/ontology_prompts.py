"""
Prompt templates for ontology creation.

Provides the prompt for Claude to create entity and relationship ontologies for partitions.
"""

from typing import Dict


def build_ontology_creation_prompt(partition: Dict, data_source_path: str, item_id: str) -> str:
    """
    Build the user message prompt for Claude to create ontologies for a partition.
    
    Args:
        partition: The partition data dictionary
        data_source_path: Path to the data source directory
        item_id: The checklist item ID for this partition (e.g., "2.1")
        
    Returns:
        Formatted prompt string
    """
    partition_id = partition.get("partition_id")
    title = partition.get("title", "Unknown")
    description = partition.get("description", "")
    paths = partition.get("paths", [])
    file_count = len(paths)
    
    # Build file list preview (first 10 files)
    file_preview = "\n".join([f"  - {p}" for p in paths[:10]])
    if len(paths) > 10:
        file_preview += f"\n  ... and {len(paths) - 10} more files"
    
    prompt = f"""I'm building a Knowledge Graph from {data_source_path}. You are assigned to create ontologies for **Partition {partition_id}**.

## Your Partition Assignment

**Partition {partition_id}: {title}**
- Description: {description}
- Files: {file_count} files
- File list preview:
{file_preview}

## Success Pattern (Follow These Steps)

1. **Review Partition**: Read `partitions/partition_{partition_id:02d}.json` to understand all files in your partition
2. **Analyze Files**: Read several representative files to understand the content, entities, and relationships present
3. **Create Entity Ontology**: For each distinct entity TYPE you identify, run:
   ```bash
   python scripts/create_entity.py {partition_id} "<entity_type>" "<description>" "<example_file>" "<example_in_file>"
   ```
4. **Create Relationship Ontology**: For each distinct relationship TYPE you identify, run:
   ```bash
   python scripts/create_relationship.py {partition_id} "<type>" "<source_entity_type>" "<target_entity_type>" "<description>" "<example_file>" "<example_in_file>"
   ```
5. **Mark Subtask Complete**: After creating ALL entities and relationships for the partition:
   ```bash
   python scripts/mark_subtask.py {item_id} {item_id}.1
   ```
6. **Verify Each File**: For each file subtask (2.X.2 through 2.X.N), verify entities/relationships are captured:
   ```bash
   python scripts/mark_subtask.py {item_id} {item_id}.<subtask_num>
   ```
7. **Final Check**: Run `python scripts/all_subtasks_done.py {item_id}` to verify completion
8. **Complete**: Respond without tools when all subtasks are done


## Your Goal

Create a **COMPLETE** entity and relationship ontology for this partition that:
- Captures ALL meaningful entities present in the files
- Captures ALL meaningful relationships between entities
- Uses an appropriate level of abstraction (not too granular, not too abstract)
- Enables COMPLETE UNDERSTANDING of the underlying data through the Knowledge Graph

**CRITICAL**: 
- Check the existing ontology BEFORE creating each entity/relationship to avoid duplicates
- The scripts will warn you if you try to create a duplicate
- Focus on entity/relationship TYPES, not individual instances


## Entity and Relationship Structure

**Entity Example** (from examples/ontology_example/example_entity_ontology.json):
```json
{{
  "entity_id": "1",
  "type": "Red Hat Product",
  "example_file": "data/rosa-kcs/kcs_solutions/example.md",
  "description": "A Red Hat product involved in the given KCS article.",
  "example_in_file": "Openshift Container Platform 4"
}}
```

**Relationship Example** (from examples/ontology_example/example_relationship_ontology.json):
```json
{{
  "relationship_id": "1",
  "type": "DOCUMENTS",
  "source_entity_type": "KCS Article",
  "target_entity_type": "Red Hat Product",
  "description": "Indicates that a KCS Article documents troubleshooting steps for a Red Hat Product.",
  "example_file": "data/rosa-kcs/kcs_solutions/example.md",
  "example_in_file": "KCS 5682881 -> DOCUMENTS -> Openshift Container Platform 4"
}}
```


## Available Commands

```bash
# Create an entity in partition {partition_id}'s ontology
python scripts/create_entity.py {partition_id} "<type>" "<description>" "<example_file>" "<example_in_file>"

# Create a relationship in partition {partition_id}'s ontology  
python scripts/create_relationship.py {partition_id} "<type>" "<source_entity_type>" "<target_entity_type>" "<description>" "<example_file>" "<example_in_file>"

# Mark a subtask as complete
python scripts/mark_subtask.py {item_id} <subtask_item_id>

# Check if all subtasks are done
python scripts/all_subtasks_done.py {item_id}

# View current entity ontology
cat ontologies/partition_{partition_id:02d}_entity_ontology.json

# View current relationship ontology
cat ontologies/partition_{partition_id:02d}_relationship_ontology.json
```


## Environment Variable

Your PARTITION_ITEM_ID is set to `{item_id}`. This allows scripts to know which partition you're working on.

Begin by reading the partition file and a few representative data files to understand the content.
"""
    return prompt

