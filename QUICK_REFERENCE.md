# KGaaS Quick Reference Guide

## Common Commands

### Starting the Workflow
```bash
make start-extraction      # Display workflow overview and current status
```

### Partition Management
```bash
make validate-partitions   # Check partition coverage
make list-data            # See what files need to be partitioned
```

### Ontology Management
```bash
# Check if element already exists
make check-ontology TYPE="ServiceName" DESC="A microservice component" ONT=entity
make check-ontology TYPE="DEPENDS_ON" DESC="Dependency relationship" ONT=relationship

# Update master ontology from partition
make update-ontology PARTITION=partition_01 ONT=both
make update-ontology PARTITION=partition_01 ONT=entity
make update-ontology PARTITION=partition_01 ONT=relationship
```

### Checklist Management
```bash
# View checklists
make view-checklist                                    # View master checklist
make view-checklist CHECKLIST=01_create_file_partition # View specific checklist
make view-checklist CHECKLIST=master_checklist RECURSIVE=1 # Recursive view

# Check off items
make check-item CHECKLIST=01_create_file_partition ITEM=1.1
make check-item CHECKLIST=02_preprocess_each_partition ITEM=partition_01

# Generate preprocessing checklist
make generate-preprocessing
```

### Python API (for Claude Agent SDK)
```python
from scripts.agent_tools import KGaaSTools

tools = KGaaSTools()

# Get data files
files = tools.get_data_files()  # Returns list of all files in data/

# Partition management
partitions = tools.list_partitions()
partition = tools.get_partition("partition_01")
tools.save_partition("partition_01", partition_data)

# Validation
result = tools.confirm_acceptable_partition()
# Returns: {"valid": True/False, "output": "...", "error": None/error_msg}

# Ontology checking
result = tools.check_ontology_element("Service", "A microservice", "entity")
# Returns: {"recommendation": "USE_EXISTING"|"REVIEW_SIMILAR"|"CREATE_NEW", ...}

# Master ontology operations
master_entities = tools.get_master_ontology("entity")
master_relationships = tools.get_master_ontology("relationship")
tools.update_master_ontology("partition_01", "both")

# Checklist operations
status = tools.view_checklist("master_checklist")
tools.check_off_item("01_create_file_partition", "1.1")
tools.generate_preprocessing_checklist()
```

## Partition JSON Template

```json
{
  "partition_id": "partition_XX",
  "title": "One sentence summary of partition contents",
  "description": "Detailed description of how files relate and fit into repo",
  "paths": [
    "data/repo/path/to/file1.md",
    "data/repo/path/to/file2.md"
  ],
  "entity_ontology": [
    {
      "type": "EntityType",
      "example_files": ["data/repo/file1.md", "data/repo/file2.md"],
      "example_files_description": "What content motivates this entity type"
    }
  ],
  "relationship_ontology": [
    {
      "type": "RELATIONSHIP_TYPE",
      "example_files": ["data/repo/fileA.md", "data/repo/fileB.md"],
      "example_files_description": "Source in fileA, target in fileB"
    }
  ]
}
```

## Workflow Checklist

- [ ] 1.1 - Analyze data/ folder structure
- [ ] 1.2 - Identify logical groupings
- [ ] 1.3 - Create partition JSON files
- [ ] 1.4 - Validate partition coverage (`make validate-partitions`)
- [ ] 1.5 - Create entity ontology for each partition
- [ ] 1.6 - Create relationship ontology for each partition
- [ ] 1.7 - Update master entity ontology
- [ ] 1.8 - Update master relationship ontology

## Tips

1. **Before adding new ontology element**: Always check master ontology first
   ```bash
   make check-ontology TYPE="YourType" DESC="Description" ONT=entity
   ```

2. **Partition strategy**: Group files with similar patterns/content for token efficiency

3. **Ontology granularity**: Not too many types, but capture ALL important entities/relationships (aim for 95%+ coverage)

4. **Example files**: For entities use 1-3 files, for relationships use tuple `[fileA, fileB]` or `[file, file]` for internal

5. **Track progress**: Use checklist system to avoid missing steps
   ```bash
   make check-item CHECKLIST=01_create_file_partition ITEM=1.1
   ```

## File Locations

- **Partitions**: `partitions/partition_XX.json`
- **Master Ontologies**: `ontologies/master_entity_ontology.json`, `ontologies/master_relationship_ontology.json`
- **Checklists**: `checklists/master_checklist.json`, `checklists/01_create_file_partition.json`
- **Schemas**: `schemas/partition_schema.json`, `schemas/master_ontology_schema.json`
- **Scripts**: `scripts/confirm_acceptable_partition.py`, `scripts/check_master_ontology.py`, etc.

## Troubleshooting

**Validation fails?**
- Check that all files in data/ are included in exactly one partition
- Ensure no file appears in multiple partitions
- Verify all paths in partition files exist in data/

**Ontology update fails?**
- Ensure partition JSON is valid and follows schema
- Check partition_id matches filename (without .json)

**Checklist item not found?**
- View checklist first to see available item IDs: `make view-checklist CHECKLIST=<id>`
- Item IDs are case-sensitive
