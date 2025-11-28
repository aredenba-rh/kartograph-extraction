# Workflow Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     KARTOGRAPH EXTRACTION WORKFLOW                       │
│                        (Three Pillars Architecture)                      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  START: scripts/start_extraction_workflow.py                             │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Load Configuration   │
                    │  extraction_config    │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Check Flags          │
                    │  use_current_*        │
                    └───────────┬───────────┘
                                │
                ┌───────────────┴────────────────┐
                │                                │
        use_current_partition?                  │
                │                                │
        ┌───────┴───────┐                        │
        │               │                        │
       YES             NO                        │
        │               │                        │
        │               ▼                        │
        │    ╔══════════════════════════════╗    │
        │    ║  PILLAR 1: CLAUDE SDK       ║    │
        │    ║  Step 1.1: Create Partitions ║    │
        │    ╚══════════════════════════════╝    │
        │               │                        │
        │               ▼                        │
        │    ┌──────────────────────────────┐   │
        │    │ Build Dynamic Prompt         │   │
        │    │ - ROSA Ask-SRE context       │   │
        │    │ - Data source path           │   │
        │    │ - Partition strategy         │   │
        │    │ - Tool instructions          │   │
        │    │ - Example references         │   │
        │    └──────────────┬───────────────┘   │
        │                   │                    │
        │                   ▼                    │
        │    ┌──────────────────────────────┐   │
        │    │ Invoke Claude Code Agent SDK │   │
        │    │ Available tools:             │   │
        │    │ - create_partition           │   │
        │    └──────────────┬───────────────┘   │
        │                   │                    │
        │                   ▼                    │
        │    ┌──────────────────────────────┐   │
        │    │ Claude Analyzes Data Source  │   │
        │    │ - Explores data/ directory   │   │
        │    │ - Identifies groupings       │   │
        │    │ - Creates logical partitions │   │
        │    └──────────────┬───────────────┘   │
        │                   │                    │
        │                   ▼                    │
        │    ┌──────────────────────────────┐   │
        │    │ Claude Calls create_partition│   │
        │    │ Multiple times (once per     │   │
        │    │ partition created)           │   │
        │    │                              │   │
        │    │ scripts/create_partition.py: │   │
        │    │ - Auto-increment ID          │   │
        │    │ - Create partition_XX.json   │   │
        │    │ - Set ontologies to []       │   │
        │    └──────────────┬───────────────┘   │
        │                   │                    │
        │                   ▼                    │
        │    ╔══════════════════════════════╗   │
        │    ║  PILLAR 2: VALIDATION       ║   │
        │    ║  Step 1.2: Validate Coverage ║   │
        │    ╚══════════════════════════════╝   │
        │                   │                    │
        │                   ▼                    │
        │    ┌──────────────────────────────┐   │
        │    │ confirm_acceptable_partition │   │
        │    │                              │   │
        │    │ 1. Load all partition files  │   │
        │    │ 2. Expand directory paths    │   │
        │    │    (paths ending with /)     │   │
        │    │ 3. Get all files in data/    │   │
        │    │ 4. Check coverage            │   │
        │    └──────────────┬───────────────┘   │
        │                   │                    │
        │        ┌──────────┴──────────┐         │
        │        │                     │         │
        │        ▼                     ▼         │
        │   VALIDATION              VALIDATION   │
        │     PASSED                 FAILED      │
        │        │                     │         │
        │        │                     ▼         │
        │        │        ╔══════════════════════════════╗
        │        │        ║  PILLAR 3: VALIDATION LOOP  ║
        │        │        ╚══════════════════════════════╝
        │        │                     │         │
        │        │                     ▼         │
        │        │        ┌────────────────────────────┐
        │        │        │ Generate Error Message:    │
        │        │        │                            │
        │        │        │ DUPLICATE FILES:           │
        │        │        │  - file.md in [1, 2]       │
        │        │        │                            │
        │        │        │ MISSING FILES:             │
        │        │        │  - missing1.md             │
        │        │        │  - missing2.md             │
        │        │        │  ... and X more            │
        │        │        │                            │
        │        │        │ INVALID FILES:             │
        │        │        │  - nonexistent.md          │
        │        │        └────────────┬───────────────┘
        │        │                     │
        │        │                     ▼
        │        │        ┌────────────────────────────┐
        │        │        │ Increment attempt counter  │
        │        │        │ attempt < 3?               │
        │        │        └────────────┬───────────────┘
        │        │                     │
        │        │        ┌────────────┴────────────┐
        │        │        │                         │
        │        │       YES                       NO
        │        │        │                         │
        │        │        ▼                         ▼
        │        │  ┌──────────────────┐  ┌─────────────────┐
        │        │  │ Send error msg   │  │ Exit with error │
        │        │  │ back to Claude   │  │ "Max attempts   │
        │        │  │                  │  │  reached"       │
        │        │  │ Build new prompt │  └─────────────────┘
        │        │  │ with errors      │
        │        │  └────────┬─────────┘
        │        │           │
        │        │           └──────────┐
        │        │                      │
        │        └──────────────────────┼── LOOP BACK TO
        │                               │   PILLAR 1
        └───────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ ROUTE TO STEP 2.1     │
                    │ Create Ontologies     │
                    │                       │
                    │ (Future Implementation)│
                    └───────────────────────┘
                                │
                                ▼
                         ┌─────────────┐
                         │  COMPLETE   │
                         └─────────────┘
```

## Key Components

### Pillar 1: Claude SDK Invocation
- **Entry Point**: `execute_step_1_1_create_partitions()`
- **Tool**: `scripts/create_partition.py`
- **Output**: Partition files in `partitions/partition_XX.json`

### Pillar 2: Detailed Validation
- **Entry Point**: `validate_and_get_errors()`
- **Checks**: Duplicates, Missing, Invalid files
- **Output**: Detailed error message string

### Pillar 3: Validation Loop
- **Max Attempts**: 3
- **Retry Logic**: Error feedback → Claude → New partitions
- **Exit Conditions**: 
  - Success → Route to Step 2.1
  - Failure after 3 attempts → Exit with error

## Data Flow

```
Configuration
     ↓
Claude Prompt (dynamic)
     ↓
Claude Agent Execution
     ↓
create_partition.py calls × N
     ↓
Partition Files (partition_XX.json)
     ↓
Validation Logic
     ↓
Error Messages (if invalid)
     ↓
Back to Claude (retry)
```

## File Structure

```
kartograph-extraction/
├── scripts/
│   ├── start_extraction_workflow.py  ← Main orchestration
│   ├── create_partition.py           ← Partition creation
│   └── confirm_acceptable_partition.py ← Validation
├── partitions/
│   ├── partition_01.json             ← Created by Claude
│   ├── partition_02.json             ← Created by Claude
│   └── ...
├── examples/
│   └── partition_example/            ← Reference examples
│       ├── README.md
│       ├── partition_01.json
│       └── partition_02.json
├── checklists/
│   └── 01_create_file_partitions.json ← With available_tools
└── extraction_config.json            ← Workflow configuration
```

## Configuration Decision Tree

```
START
  │
  ├─ use_current_partition = true?
  │    └─ YES → Skip to Step 2
  │
  └─ use_current_partition = false?
       └─ YES → Execute Pillar 1-3
            │
            ├─ use_current_ontologies = true?
            │    └─ YES → Skip Step 2, go to Step 3
            │
            └─ use_current_ontologies = false?
                 └─ YES → Execute Step 2 after Step 1
```

## Error Handling Flow

```
Validation Errors
      │
      ├─ Duplicates? → Show: file, partitions containing it
      │
      ├─ Missing? → Show: list of files not in any partition
      │
      └─ Invalid? → Show: references that don't exist
            │
            └─ Format as detailed message
                  │
                  └─ Send to Claude for correction
```

## Success Criteria

```
Validation Check
      │
      ├─ All files in data/ covered? ✓
      │
      ├─ No duplicates? ✓
      │
      ├─ No invalid references? ✓
      │
      └─ All checks pass?
            │
            └─ YES → Route to Step 2.1 ✓
```

