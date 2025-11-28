# Partition Example

This example demonstrates how to create successful partitions for a knowledge graph extraction workflow.

## Example Data Structure

```
data/
├── folderA/
│   ├── fileAA.md
│   └── fileAB.md
├── folderB/
│   ├── fileBA.md
│   └── fileBB.md
├── fileA.md
├── fileB.md
└── fileC.md
```

## Successful Partition Strategy

### Partition 1: Core Documentation (partition_01.json)
Files related to primary documentation and folder A resources:
- `data/folderA/` (all files in folderA)
- `data/folderB/fileBA.md` (specific file from folderB)
- `data/fileA.md`
- `data/fileB.md`

### Partition 2: Supporting Resources (partition_02.json)
Files related to secondary resources:
- `data/folderB/fileBB.md` (specific file from folderB)
- `data/fileC.md`

## Key Points

1. **Directory Notation**: Using `data/folderA/` (with trailing slash) indicates ALL files in that directory
2. **Specific Files**: Individual files are listed with their full path
3. **Disjoint Coverage**: Each file appears in exactly one partition
4. **Complete Coverage**: All files in data/ are included in at least one partition
5. **Logical Groupings**: Files are grouped by their content relationships and intended use

## How to Create Partitions

Use the `create_partition.py` script:

```bash
# Create first partition with a directory and specific files
python scripts/create_partition.py \
  "Core Documentation" \
  "Primary documentation files and folder A resources" \
  "data/folderA/" \
  "data/folderB/fileBA.md" \
  "data/fileA.md" \
  "data/fileB.md"

# Create second partition
python scripts/create_partition.py \
  "Supporting Resources" \
  "Secondary supporting documentation and resources" \
  "data/folderB/fileBB.md" \
  "data/fileC.md"
```

## Validation

After creating partitions, validate them with:

```bash
python scripts/confirm_acceptable_partition.py
```

This will check:
- ✅ All files in data/ are included exactly once
- ✅ No duplicate coverage (files in multiple partitions)
- ✅ No missing files (files not in any partition)
- ✅ No invalid references (non-existent files)

