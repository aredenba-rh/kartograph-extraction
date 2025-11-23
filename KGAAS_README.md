# KGaaS (Knowledge Graph as a Service) - Step 1: Partition + Ontology

This directory contains the infrastructure for Step 1 of the KGaaS extraction workflow: creating partitions and ontologies for knowledge graph extraction.

## Overview

The workflow follows a hybrid ontology approach where:
1. Files in `data/` are partitioned into logical groupings
2. Each partition gets an Entity Ontology and Relationship Ontology
3. Partition ontologies are standardized across a Master Ontology
4. The system supports both predetermined and dynamic ontology expansion

## Directory Structure

```
kartograph-extraction/
├── data/                          # Source repos to extract KG from
├── partitions/                    # Partition JSON files
│   ├── partition_01.json
│   ├── partition_02.json
│   └── ...
├── ontologies/                    # Master ontologies
│   ├── master_entity_ontology.json
│   └── master_relationship_ontology.json
├── checklists/                    # Progress tracking
│   ├── master_checklist.json
│   ├── 01_create_file_partition.json
│   └── 02_preprocess_each_partition.json
├── schemas/                       # JSON schemas
│   ├── partition_schema.json
│   ├── master_ontology_schema.json
│   └── checklist_schema.json
└── scripts/                       # Automation tools
    ├── confirm_acceptable_partition.py
    ├── check_master_ontology.py
    ├── update_master_ontology.py
    ├── manage_checklist.py
    └── agent_tools.py
```

## Partition Structure

Each partition is a JSON file with the following structure:

```json
{
  "partition_id": "partition_01",
  "title": "One sentence summary",
  "description": "How these files relate to each other and the repo",
  "paths": [
    "data/rosa-kcs/file1.md",
    "data/rosa-kcs/file2.md"
  ],
  "entity_ontology": [
    {
      "type": "Service",
      "example_files": ["data/rosa-kcs/file1.md"],
      "example_files_description": "Description of entity instances"
    }
  ],
  "relationship_ontology": [
    {
      "type": "DEPENDS_ON",
      "example_files": ["data/rosa-kcs/file1.md", "data/rosa-kcs/file2.md"],
      "example_files_description": "Description of relationship"
    }
  ]
}
```

## Ontology Elements

### Entity Ontology
- **type**: Entity type (e.g., "Person", "Service", "Configuration")
- **example_files**: 1-3 file paths containing this entity type
- **example_files_description**: What content motivates this entity type

### Relationship Ontology
- **type**: Relationship type (e.g., "DEPENDS_ON", "CONTAINS")
- **example_files**: Tuple `[fileA, fileB]` showing the relationship (use `[file, file]` for internal)
- **example_files_description**: Description of the relationship with source/target info

## Available Scripts

### 1. Validate Partitions
```bash
python scripts/confirm_acceptable_partition.py
# or
make validate-partitions
```
Checks that:
- All partitions are valid JSON
- All files in `data/` are covered exactly once (disjoint)
- No file appears in multiple partitions
- No invalid file paths

### 2. Check Master Ontology
```bash
python scripts/check_master_ontology.py entity "Service" "A microservice component"
# or
make check-ontology TYPE="Service" DESC="A microservice component" ONT=entity
```
Before adding a new ontology element, check if similar ones exist to maintain standardization.

### 3. Update Master Ontology
```bash
python scripts/update_master_ontology.py partition_01 both
# or
make update-ontology PARTITION=partition_01 ONT=both
```
Merge a partition's ontologies into the master ontologies.

### 4. Manage Checklists
```bash
# View checklist
python scripts/manage_checklist.py view master_checklist
make view-checklist CHECKLIST=master_checklist

# Check off item
python scripts/manage_checklist.py check 01_create_file_partition 1.1
make check-item CHECKLIST=01_create_file_partition ITEM=1.1

# Generate preprocessing checklist
python scripts/manage_checklist.py generate-preprocessing
make generate-preprocessing
```

### 5. Agent Tools (for Claude Agent SDK)
```python
from scripts.agent_tools import KGaaSTools

tools = KGaaSTools()

# Get all data files
files = tools.get_data_files()

# Check partition validity
result = tools.confirm_acceptable_partition()

# Check ontology element
result = tools.check_ontology_element("Service", "A microservice", "entity")

# Save partition
tools.save_partition("partition_01", partition_data)

# Update master ontology
tools.update_master_ontology("partition_01", "both")

# Manage checklist
tools.check_off_item("01_create_file_partition", "1.1")
```

## Workflow: Creating Partitions

### Step 1: Analyze Data
```bash
make list-data
```

### Step 2: Create Partitions
Create partition JSON files in `partitions/` directory. Use the Claude Agent SDK to:
1. Analyze file contents and patterns
2. Group similar files together
3. Create partition JSON with title, description, and paths

### Step 3: Validate Coverage
```bash
make validate-partitions
```
Ensure all files are covered exactly once.

### Step 4: Create Partition Ontologies
For each partition:
1. **Check master ontology** for existing similar elements:
   ```bash
   make check-ontology TYPE="YourType" DESC="Description" ONT=entity
   ```
2. **Add entity ontology** elements to partition JSON
3. **Add relationship ontology** elements to partition JSON
4. **Update master ontology**:
   ```bash
   make update-ontology PARTITION=partition_01 ONT=both
   ```

### Step 5: Track Progress
```bash
# View overall progress
make view-checklist

# View detailed checklist
make view-checklist CHECKLIST=01_create_file_partition

# Check off completed items
make check-item CHECKLIST=01_create_file_partition ITEM=1.1
```

## Starting the Workflow

To kick off the entire extraction process:

```bash
make start-extraction
```

This will:
1. Display the workflow overview
2. Show available tools
3. Display current checklist status
4. Provide next steps

## Checklist System

The checklist system keeps Claude agents on track:

- **master_checklist.json**: Top-level workflow steps
- **01_create_file_partition.json**: Steps for creating partitions
- **02_preprocess_each_partition.json**: Per-partition preprocessing (dynamically generated)

Use checklists to ensure no work is skipped and track progress across the entire workflow.

## Design Principles

1. **Disjoint Partitions**: Every file in `data/` appears in exactly one partition
2. **Token Efficiency**: Similar files grouped together for efficient LLM processing
3. **Hybrid Ontology**: Mix of predetermined (master) and dynamic (expandable) ontologies
4. **Standardization**: Check master ontology before creating new element types
5. **Traceability**: Every ontology element links back to example files
6. **Progress Tracking**: Comprehensive checklist system ensures completeness

## Example Partition

```json
{
  "partition_id": "partition_01",
  "title": "ROSA cluster configuration and setup knowledge base articles",
  "description": "KCS articles related to ROSA cluster configuration, setup, credentials, and AWS integration. These files share common patterns around cluster lifecycle and AWS-specific configurations.",
  "paths": [
    "data/rosa-kcs/kcs_solutions/5609901-red-hat-openshift-service-on-aws-(rosa)-pre-ga-support.md",
    "data/rosa-kcs/kcs_solutions/5795441-cloud-credentials-insufficient-to-satisfy-credentialsrequest-on-aws-rhocp-4.md"
  ],
  "entity_ontology": [
    {
      "type": "AWSService",
      "example_files": ["data/rosa-kcs/kcs_solutions/5795441-cloud-credentials-insufficient-to-satisfy-credentialsrequest-on-aws-rhocp-4.md"],
      "example_files_description": "References to AWS services like S3, IAM, EC2 that integrate with ROSA clusters"
    },
    {
      "type": "Credential",
      "example_files": ["data/rosa-kcs/kcs_solutions/5795441-cloud-credentials-insufficient-to-satisfy-credentialsrequest-on-aws-rhocp-4.md"],
      "example_files_description": "Cloud credentials, IAM roles, and authentication mechanisms for ROSA"
    }
  ],
  "relationship_ontology": [
    {
      "type": "REQUIRES",
      "example_files": ["data/rosa-kcs/kcs_solutions/5795441-cloud-credentials-insufficient-to-satisfy-credentialsrequest-on-aws-rhocp-4.md", "data/rosa-kcs/kcs_solutions/5795441-cloud-credentials-insufficient-to-satisfy-credentialsrequest-on-aws-rhocp-4.md"],
      "example_files_description": "ROSA clusters require specific AWS credentials with sufficient permissions"
    }
  ]
}
```

## Next Steps (Beyond Step 1)

After completing Step 1 (Partition + Ontology):
- Step 2: Knowledge graph extraction per partition using the defined ontologies
- Step 3: Merging and deduplication of knowledge graph elements
- Step 4: Validation and quality assurance
- Step 5: Export and serving (KGaaS)
