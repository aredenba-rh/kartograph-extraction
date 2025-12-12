# Partition Example

This example demonstrates how to create successful partitions for a given data source


## Example Data Structure 
In our example, "data_source_1" is the data_source. There may be multiple data_sources within the real 'data' folder, but that should be ignored - you are responsible for partitioning a singular data_source only, so this example should provide sufficient guidance.
```
data/
└── data_source_1/
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

### Partition 1: Installation and Provisioning (partition_01.json)
- `folderA/` (all files in folderA)
- `folderB/fileBA.md` (specific file from folderB)
- `fileA.md`
- `fileB.md`

### Partition 2: Security and Authentication (partition_02.json)
- `folderB/fileBB.md` (specific file from folderB)
- `fileC.md`


## Key Points
1. **Directory Notation**: Using `folderA/` (with trailing slash) indicates ALL files in that directory
2. **Specific Files**: Individual files are listed with their full path
3. **Disjoint Coverage**: Each file appears in exactly one partition
4. **Complete Coverage**: All files in `data_source_1/` are included in at least one partition
5. **Logical Groupings**: Files are grouped by their content relationships and intended use

## How to Create Partitions

Use the `create_partition.py` script:

```bash
# Create first partition with a directory and specific files
python scripts/create_partition.py \
  "Installation and Provisioning" \
  "Documentation focused on cluster installation, setup, provisioning, and initial configuration." \
  "folderA/" \
  "folderB/fileBA.md" \
  "fileA.md" \
  "fileB.md"

# Create second partition
python scripts/create_partition.py \
  "Security and Authentication" \
  "Documentation focused on security and authentication best practices, including authentication methods, authorization mechanisms, and security protocols." \
  "folderB/fileBB.md" \
  "fileC.md"
```

## Validation

After creating all file subsets for a given partition, validate the partition with:

```bash
python3 scripts/validate_partition.py
```

This will check:
- ✅ All files in data/ are included exactly once
- ✅ No duplicate coverage (files in multiple partitions)
- ✅ No missing files (files not in any partition)
- ✅ No invalid references (non-existent files)

