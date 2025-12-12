"""
Configuration utilities for the extraction workflow.

Provides functions for:
- Loading extraction configuration
- Getting the data source path
- Configuring Claude agent settings
"""

import json
from pathlib import Path
from typing import Dict, List


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
    Returns the 'data/' directory path.
    """
    data_dir = Path("data")
    
    if not data_dir.exists():
        raise FileNotFoundError("data/ directory does not exist")
    
    return str(data_dir)


def get_data_sources() -> List[str]:
    """
    Get a list of all data source folder names in data/ directory.
    
    Returns:
        List of data source folder names (e.g., ["openshift-docs", "ops-sop", "rosa-kcs"])
    """
    data_dir = Path("data")
    
    if not data_dir.exists():
        raise FileNotFoundError("data/ directory does not exist")
    
    # Get all subdirectories in data/
    subdirs = sorted([d.name for d in data_dir.iterdir() if d.is_dir()])
    
    if len(subdirs) == 0:
        raise FileNotFoundError("No subdirectories found in data/")
    
    return subdirs


def configure_claude_agent_settings(data_path: str, data_sources: List[str]):
    """
    Configure .claude/settings.local.json with required permissions for the agent.
    
    Sets up:
    - Allow rules for Bash commands (tree, mkdir, chmod, make)
    - Deny rules for writing/modifying all data source folders
    
    Only adds rules if not already present. Does not remove existing rules.
    
    Args:
        data_path: Path to the data directory (e.g., "data")
        data_sources: List of data source folder names (e.g., ["openshift-docs", "ops-sop", "rosa-kcs"])
    """
    settings_file = Path(".claude/settings.local.json")
    
    # Required allow rules for Bash commands
    required_allow_rules = [
        "Bash(tree:*)",
        "Bash(mkdir:*)",
        "Bash(chmod:*)",
        "Bash(make:*)"
    ]
    
    # Build deny rules for all data sources
    required_deny_rules = []
    for data_source in data_sources:
        data_source_path = f"{data_path}/{data_source}"
        required_deny_rules.extend([
            f"Write(./{data_source_path}/**)",
            f"Bash(rm:*{data_source_path}*)",
            f"Bash(mv:*{data_source_path}*)",
            f"Bash(cp:*{data_source_path}*)",
            f"Bash(mkdir:*{data_source_path}*)",
            f"Bash(touch:*{data_source_path}*)",
            f"Bash(echo:*>{data_source_path}*)",
            f"Bash(cat:*>{data_source_path}*)",
            f"Bash(cd:*{data_source_path}*&&*mkdir*)",
        ])
    
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
        print(f"  ✓ Added data source protection for: {', '.join(data_sources)}")
    
    # Write back to file only if modified
    if modified:
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
    else:
        print(f"  ✓ Agent settings already configured")

