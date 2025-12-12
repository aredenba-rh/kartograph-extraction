"""
Prompt templates for Claude Agent interactions.

Modules:
    - partition_prompts: Prompts for file partition creation
    - ontology_prompts: Prompts for ontology creation
"""

from .partition_prompts import build_partition_creation_prompt
from .ontology_prompts import build_ontology_creation_prompt

__all__ = [
    "build_partition_creation_prompt",
    "build_ontology_creation_prompt",
]

