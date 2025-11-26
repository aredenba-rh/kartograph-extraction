#!/usr/bin/env python3
"""
Extraction Preview Tool
Shows current status of data, flags, and checklists for KG extraction workflow
"""

import json
import os
from pathlib import Path

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
    
    # Flag display names with descriptions
    flag_names = {
        "use_current_partition": "use_current_partition (Skip 01)",
        "use_current_ontologies": "use_current_ontologies (Skip 02)"
    }
    
    for key, value in config.items():
        status = "✓ ON " if value else "✗ OFF"
        toggle_cmd = f"make toggle-{key.replace('_', '-')}"
        display_name = flag_names.get(key, key)
        print(f"  {display_name:35s}  {status:11s}  {toggle_cmd}")
    
    print()
    print("  💡 Use toggle commands to change flag values")
    print()

def show_checklist_status():
    """Show current checklist progress"""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                    Checklist Progress                      ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    master_file = Path("checklists/master_checklist.json")
    
    if not master_file.exists():
        print("  ⚠️  No master checklist found.")
        print()
        return
    
    with open(master_file, 'r') as f:
        master = json.load(f)
    
    print(f"  {master['title']}")
    print()
    
    for item in master['items']:
        status = "✓" if item['completed'] else "○"
        print(f"  {status} {item['item_id']}: {item['description']}")
        
        # Show sub-checklist if exists
        if 'sub_checklist' in item:
            sub_file = Path(f"checklists/{item['sub_checklist']}")
            if sub_file.exists():
                with open(sub_file, 'r') as f:
                    sub = json.load(f)
                
                completed = sum(1 for i in sub['items'] if i['completed'])
                total = len(sub['items'])
                
                print(f"      └─ {sub['title']}: {completed}/{total} items complete")
    
    print()
    print("  💡 View details: make view-checklist")
    print()

def main():
    """Main preview function"""
    print()
    show_data_overview()
    show_flags()
    show_checklist_status()
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                      Next Steps                            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    print("  1. Configure flags as needed using 'make toggle-{flag}'")
    print("  2. Run 'make start-extraction' to begin the workflow")
    print("  3. Use 'make view-checklist' for detailed progress")
    print()

if __name__ == "__main__":
    main()

