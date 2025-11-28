# Kartograph Extraction

Knowledge Graph extraction framework with automated partition creation and ontology management using Claude Code Agent SDK.

## Overview

This project creates knowledge graphs from documentation sources by:
1. **Partitioning** files into logical groupings
2. **Creating ontologies** for each partition (entity and relationship types)
3. **Extracting** knowledge graph triples from the content

Currently configured to extract from ROSA (Red Hat OpenShift on AWS) documentation.

## Quick Start

```bash
# Start the extraction workflow
python scripts/start_extraction_workflow.py

# Validate existing partitions
python scripts/confirm_acceptable_partition.py

# View checklist progress
make view-checklist
```

## Workflow Steps

### Step 1: Create File Partitions (Automated)

The workflow automatically invokes Claude Code Agent SDK to analyze your data source and create logical partitions.

**Partitions are:**
- Logical groupings of files for knowledge graph extraction
- Disjoint (each file appears in exactly one partition)
- Complete (all files are covered)

Claude uses the `create_partition.py` script to create partitions, which are then automatically validated.

### Step 2: Create Ontologies

For each partition, define:
- **Entity types** (e.g., AWSService, Configuration, Error)
- **Relationship types** (e.g., REQUIRES, DOCUMENTS, CONFIGURES)

These are merged into master ontologies to maintain consistency across the knowledge graph.

## Configuration

Edit `extraction_config.json`:

```json
{
  "use_current_partition": false,  // Skip partition creation step
  "use_current_ontologies": false  // Skip ontology creation step
}
```

## Directory Structure

```
kartograph-extraction/
├── checklists/          # Workflow tracking
├── contexts/            # Data source configurations
├── data/                # Source documentation
├── examples/            # Example partition structures
├── ontologies/          # Master ontologies
├── partitions/          # Generated partition files
├── schemas/             # JSON schemas for validation
└── scripts/             # Automation scripts
```

## Examples

See `examples/partition_example/` for a complete demonstration of:
- How to structure data
- How to create partitions
- Directory vs. file path notation
- Complete and disjoint coverage

## Scripts

### `start_extraction_workflow.py`
Main orchestration script that:
- Invokes Claude Code Agent SDK
- Validates partitions automatically
- Routes to appropriate workflow steps
- Handles validation failures with retry logic

### `create_partition.py`
Creates partition files with auto-incrementing IDs:
```bash
python scripts/create_partition.py \
  "Title" \
  "Description of files in this partition" \
  "data/folder/" \
  "data/specific_file.md"
```

### `confirm_acceptable_partition.py`
Validates partition coverage:
- Checks for duplicate files
- Checks for missing files
- Validates directory path expansion
- Returns detailed error messages

## Contributing

1. Follow the checklist workflow in `checklists/`
2. Use provided scripts for automation
3. Validate changes before committing
