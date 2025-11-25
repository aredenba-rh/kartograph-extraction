#!/usr/bin/env python3
"""
Toggle Extraction Configuration Flags
"""

import json
import sys
from pathlib import Path

def toggle_flag(flag_name):
    """Toggle a boolean flag in extraction_config.json"""
    config_file = Path("extraction_config.json")
    
    if not config_file.exists():
        print(f"❌ Error: extraction_config.json not found")
        sys.exit(1)
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    if flag_name not in config:
        print(f"❌ Error: Unknown flag '{flag_name}'")
        print(f"   Available flags: {', '.join(config.keys())}")
        sys.exit(1)
    
    # Toggle the flag
    old_value = config[flag_name]
    config[flag_name] = not old_value
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    new_value = config[flag_name]
    status_old = "ON" if old_value else "OFF"
    status_new = "ON" if new_value else "OFF"
    
    print(f"✓ Toggled '{flag_name}': {status_old} → {status_new}")

def main():
    if len(sys.argv) != 2:
        print("Usage: toggle_flag.py <flag_name>")
        sys.exit(1)
    
    flag_name = sys.argv[1]
    toggle_flag(flag_name)

if __name__ == "__main__":
    main()

