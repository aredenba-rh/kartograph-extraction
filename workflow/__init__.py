"""
Workflow Package for Kartograph Extraction

This package orchestrates the knowledge graph extraction process using Claude Code Agent SDK.

Modules:
    - helpers: Utility functions for logging, config, checklists, and filesystem operations
    - prompts: LLM prompt templates for partition and ontology creation
    - agents: Claude Agent SDK session management
    - steps: Individual workflow step implementations
"""

from .start_extraction import main

__all__ = ["main"]

