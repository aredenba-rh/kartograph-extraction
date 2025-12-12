#!/usr/bin/env python3
"""
Extraction Preview Tool
Shows current status of data, flags, and checklists for KG extraction workflow
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import workflow modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from workflow.helpers.config import get_data_source_path, get_data_sources, configure_claude_agent_settings


def get_data_source_path_safe() -> str:
    """
    Wrapper around get_data_source_path that returns None instead of raising.
    """
    try:
        return get_data_source_path()
    except (FileNotFoundError, ValueError):
        return None


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
    data_source_path = get_data_source_path_safe()
    if data_source_path:
        try:
            data_sources = get_data_sources()
            configure_claude_agent_settings(data_source_path, data_sources)
            print()
        except FileNotFoundError:
            pass  # No data sources yet
    
    show_data_overview()
    show_flags()


if __name__ == "__main__":
    main()
