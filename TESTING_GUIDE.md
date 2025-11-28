# Testing Guide

This guide shows how to test the three pillars implementation.

## Test 1: Create Partition Script

Test the auto-incrementing partition creation:

```bash
# Create first partition
python scripts/create_partition.py \
  "AWS Integration Docs" \
  "Documentation related to AWS service integration" \
  "data/rosa-kcs/kcs_solutions/"

# Create second partition (should auto-increment to ID 2)
python scripts/create_partition.py \
  "Configuration Files" \
  "ROSA configuration and setup files" \
  "data/rosa-kcs/configs/"

# List created partitions
make list-partitions
```

**Expected:**
- First partition: `partition_01.json` with `partition_id: 1`
- Second partition: `partition_02.json` with `partition_id: 2`
- Both have empty entity_ontology and relationship_ontology arrays

## Test 2: Validation with Detailed Errors

Test validation with incomplete partitions:

```bash
# Create incomplete partition (only covers some files)
python scripts/create_partition.py \
  "Incomplete Partition" \
  "Only covers a subset of files" \
  "examples/partition_example/data/folderA/"

# Run validation (should fail with detailed error message)
python scripts/confirm_acceptable_partition.py
```

**Expected Output:**
```
❌ MISSING FILES (X):
  (Files in data/ not covered by any partition)
  - data/rosa-kcs/file1.md
  - data/rosa-kcs/file2.md
  ... and X more files
  ⚠️  Please add these X files to appropriate partitions
```

## Test 3: Validation with Duplicates

Test duplicate detection:

```bash
# Clean existing partitions
make clean-partitions

# Create partition 1 with a file
python scripts/create_partition.py \
  "Partition 1" \
  "First partition" \
  "data/rosa-kcs/kcs_solutions/file1.md"

# Create partition 2 with SAME file (duplicate)
python scripts/create_partition.py \
  "Partition 2" \
  "Second partition" \
  "data/rosa-kcs/kcs_solutions/file1.md"

# Run validation (should detect duplicate)
python scripts/confirm_acceptable_partition.py
```

**Expected Output:**
```
❌ DUPLICATE FILES (1):
  (Files appearing in multiple partitions)
  - data/rosa-kcs/kcs_solutions/file1.md
    Found in partitions: 1, 2
    ⚠️  Please remove this file from all but ONE partition
```

## Test 4: Directory Path Expansion

Test that directory paths (with trailing /) are properly expanded:

```bash
# Create partition with directory path
python scripts/create_partition.py \
  "All KCS Solutions" \
  "All files in kcs_solutions directory" \
  "data/rosa-kcs/kcs_solutions/"

# Validation should expand to all files in that directory
python scripts/confirm_acceptable_partition.py
```

**Expected:**
- Directory path expanded to all 764 files
- Should show "Files covered by partitions: 764"

## Test 5: Complete Workflow (Integration Test)

Test the full workflow with Claude SDK integration:

```bash
# Clean everything
make clean-partitions

# Set config to not skip partition creation
python scripts/toggle_flag.py use_current_partition  # Ensure it's OFF

# Start workflow (will invoke Claude SDK)
make start-extraction
```

**Expected Flow:**
1. Script loads configuration
2. Builds dynamic prompt for Claude
3. Invokes Claude Code Agent SDK
4. Claude analyzes data source
5. Claude calls create_partition.py multiple times
6. Validation runs automatically
7. If errors: Claude receives feedback and retries (max 3 attempts)
8. If success: Routes to Step 2.1

## Test 6: Validation Loop (Error Recovery)

Test that validation errors are fed back to Claude:

```bash
# Manually create intentionally bad partition
python scripts/create_partition.py \
  "Incomplete" \
  "Missing most files" \
  "data/rosa-kcs/file1.md"

# Start workflow (should detect incomplete partitions)
# Claude should receive error message and fix
make start-extraction
```

**Expected:**
- Validation fails on first attempt
- Error message shows missing files
- Claude receives this feedback
- Claude creates additional partitions to cover missing files
- Validation succeeds on retry
- Routes to Step 2.1

## Test 7: Example Partition Structure

Test that examples are accessible:

```bash
# View example README
make view-examples

# List example partition files
ls -la examples/partition_example/

# Read example partition structure
cat examples/partition_example/partition_01.json
cat examples/partition_example/partition_02.json
```

**Expected:**
- README clearly explains partition structure
- Example data in examples/partition_example/data/
- Two example partition files showing complete coverage

## Test 8: Available Tools Integration

Test that checklist specifies available tools:

```bash
# View checklist with available tools
make view-checklist CHECKLIST=01_create_file_partitions
```

**Expected Output:**
```json
{
  "item_id": "1.1",
  "description": "...",
  "available_tools": ["create_partition"]
}
```

## Verification Checklist

After running tests, verify:

- [ ] create_partition.py auto-increments IDs
- [ ] Partition files use integer partition_id
- [ ] entity_ontology and relationship_ontology initialize as []
- [ ] Validation detects missing files with detailed list
- [ ] Validation detects duplicate files with partition IDs
- [ ] Validation detects invalid file references
- [ ] Directory paths (ending with /) expand to all files
- [ ] Error messages are clear and actionable
- [ ] Workflow invokes Claude SDK correctly
- [ ] Validation loop retries with error feedback
- [ ] Success routes to Step 2.1
- [ ] Max retry limit prevents infinite loops
- [ ] Examples are accessible and clear
- [ ] Checklists include available_tools field

## Clean Up After Testing

```bash
# Remove test partitions
make clean-partitions

# Reset configuration if needed
cat extraction_config.json
```

## Troubleshooting

**Issue:** Claude SDK import error
```
ModuleNotFoundError: No module named 'claude_agent_sdk'
```
**Solution:** Install dependencies
```bash
make install-deps
```

**Issue:** Validation fails with all files missing
```
❌ MISSING FILES (764)
```
**Solution:** This is expected if no partitions exist. Create partitions to cover files.

**Issue:** Partition ID not auto-incrementing
**Solution:** Check that partition files are named `partition_XX.json` and contain `partition_id` as integer.

**Issue:** Directory path not expanding
**Solution:** Ensure path ends with `/` (e.g., `data/folder/` not `data/folder`)

