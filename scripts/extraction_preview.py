#!/usr/bin/env python3
"""
Extraction Preview Tool
Shows current status of data, flags, and checklists for KG extraction workflow
"""

import json
import os
from pathlib import Path


def get_data_source_path() -> str:
    """
    Get the data source path to extract from.
    Returns the first (and only) folder found in data/ directory.
    Returns None if no valid data source exists.
    """
    data_dir = Path("data")
    
    if not data_dir.exists():
        return None
    
    subdirs = [d for d in data_dir.iterdir() if d.is_dir()]
    
    if len(subdirs) != 1:
        return None
    
    return str(subdirs[0])


def configure_claude_agent_settings(data_source_path: str):
    """
    Configure .claude/settings.local.json with required permissions for the agent.
    
    Sets up:
    - Allow rules for Bash commands (tree, mkdir, chmod, make)
    - Deny rules for writing/modifying the data source folder
    
    Only adds rules if not already present. Does not remove existing rules.
    
    Args:
        data_source_path: Path to the data source directory (e.g., "data/rosa-kcs")
    """
    settings_file = Path(".claude/settings.local.json")
    
    # Required allow rules for Bash commands
    required_allow_rules = [
        "Bash(tree:*)",
        "Bash(mkdir:*)",
        "Bash(chmod:*)",
        "Bash(make:*)"
    ]
    
    # Deny rules for data source protection (file tools and bash commands)
    required_deny_rules = [
        f"Write(./{data_source_path}/**)",
        f"Bash(rm:*{data_source_path}*)",
        f"Bash(mv:*{data_source_path}*)",
        f"Bash(cp:*{data_source_path}*)",
        f"Bash(mkdir:*{data_source_path}*)",
        f"Bash(touch:*{data_source_path}*)",
        f"Bash(echo:*>{data_source_path}*)",
        f"Bash(cat:*>{data_source_path}*)",
        f"Bash(cd:*{data_source_path}*&&*mkdir*)",
    ]
    
    # Load existing settings or create default structure
    if settings_file.exists():
        with open(settings_file, 'r') as f:
            settings = json.load(f)
    else:
        # Create .claude directory if needed
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings = {"permissions": {"allow": [], "deny": [], "ask": []}}
    
    # Ensure permissions structure exists
    if "permissions" not in settings:
        settings["permissions"] = {"allow": [], "deny": [], "ask": []}
    if "allow" not in settings["permissions"]:
        settings["permissions"]["allow"] = []
    if "deny" not in settings["permissions"]:
        settings["permissions"]["deny"] = []
    
    modified = False
    
    # Add missing allow rules
    allow_list = settings["permissions"]["allow"]
    for rule in required_allow_rules:
        if rule not in allow_list:
            allow_list.append(rule)
            modified = True
            print(f"  ✓ Added allow rule: {rule}")
    
    # Add missing deny rules
    deny_list = settings["permissions"]["deny"]
    for rule in required_deny_rules:
        if rule not in deny_list:
            deny_list.append(rule)
            modified = True
    
    if modified:
        print(f"  ✓ Added data source protection for {data_source_path}")
    
    # Write back to file only if modified
    if modified:
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
    else:
        print(f"  ✓ Agent settings already configured")


def count_files_in_dir(path):
    """Count total files recursively in a directory"""
    return sum(1 for _ in Path(path).rglob('*') if _.is_file())

def show_data_overview():
    """Show folders in data/ and file counts"""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                    Data Folder Overview                    ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    data_dir = Path("data")
    if not data_dir.exists():
        print("  ⚠️  No data/ folder found. Run 'make fetch-all' first.")
        print()
        return
    
    subdirs = [d for d in data_dir.iterdir() if d.is_dir()]
    
    if not subdirs:
        print("  ⚠️  No data sources found. Run 'make fetch-all' first.")
        print()
        return
    
    print(f"  Total data sources: {len(subdirs)}")
    print()
    
    for subdir in sorted(subdirs):
        file_count = count_files_in_dir(subdir)
        print(f"  📁 {subdir.name:30s} {file_count:>8,} files")
    
    print()

def show_flags():
    """Show current extraction configuration flags"""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                  Extraction Flags (Config)                 ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    config_file = Path("extraction_config.json")
    
    if not config_file.exists():
        print("  ⚠️  No extraction_config.json found. Creating default...")
        default_config = {
            "use_current_partition": False,
            "use_current_ontologies": False
        }
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        config = default_config
    else:
        with open(config_file, 'r') as f:
            config = json.load(f)
    
    print("  Flag                                Value        Toggle Command")
    print("  " + "─" * 66)
    
    # Flag display names and their corresponding step numbers
    flag_info = {
        "use_current_partition": ("use_current_partition", "01"),
        "use_current_ontologies": ("use_current_ontologies", "02")
    }
    
    # Only show the specific flags we care about
    for key in ["use_current_partition", "use_current_ontologies"]:
        value = config.get(key, False)
        display_name, step_num = flag_info[key]
        status = "--SKIP--" if value else f"Step {step_num}"
        toggle_cmd = f"make toggle-{key.replace('_', '-')}"
        print(f"  {display_name:35s}  {status:11s}  {toggle_cmd}")
    
    print()
    print("  💡 Use toggle commands to change flag values")
    print()

def main():
    """Main preview function"""
    print()
    
    # Configure Claude agent settings (allow/deny rules)
    data_source_path = get_data_source_path()
    if data_source_path:
        configure_claude_agent_settings(data_source_path)
        print()
    
    show_data_overview()
    show_flags()

if __name__ == "__main__":
    main()

