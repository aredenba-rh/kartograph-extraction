"""
Configuration utilities for the extraction workflow.

Provides functions for:
- Loading extraction configuration
- Getting the data source path
- Configuring Claude agent settings
"""

import json
from pathlib import Path
from typing import Dict


def load_config() -> Dict:
    """Load extraction configuration"""
    config_file = Path("extraction_config.json")
    
    if not config_file.exists():
        print("⚠️  No extraction_config.json found. Creating default...")
        default_config = {
            "use_current_partition": False,
            "use_current_ontologies": False
        }
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    
    with open(config_file, 'r') as f:
        return json.load(f)


def get_data_source_path() -> str:
    """
    Get the data source path to extract from.
    Returns the first (and only) folder found in data/ directory.
    """
    data_dir = Path("data")
    
    if not data_dir.exists():
        raise FileNotFoundError("data/ directory does not exist")
    
    # Get all subdirectories in data/
    subdirs = [d for d in data_dir.iterdir() if d.is_dir()]
    
    if len(subdirs) == 0:
        raise FileNotFoundError("No subdirectories found in data/")
    
    if len(subdirs) > 1:
        raise ValueError(f"Multiple data sources found in data/: {[d.name for d in subdirs]}. Expected only one.")
    
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

