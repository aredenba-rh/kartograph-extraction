#!/usr/bin/env python3
"""
Agent tools for Claude Agent SDK integration.

This module provides a simple interface for Claude agents to interact with
the KGaaS system during knowledge graph extraction.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any


class KGaaSTools:
    """Tools for Claude agents to use during KG extraction workflow."""

    def __init__(self, data_dir: str = "data", partitions_dir: str = "partitions",
                 ontologies_dir: str = "ontologies", checklists_dir: str = "checklists"):
        self.data_dir = Path(data_dir)
        self.partitions_dir = Path(partitions_dir)
        self.ontologies_dir = Path(ontologies_dir)
        self.checklists_dir = Path(checklists_dir)
        self.scripts_dir = Path("scripts")

    def confirm_acceptable_partition(self) -> Dict[str, Any]:
        """
        Validate that partitions form a complete, disjoint cover of data/ folder.

        Returns:
            Dict with validation results
        """
        result = subprocess.run(
            [sys.executable, str(self.scripts_dir / "confirm_acceptable_partition.py")],
            capture_output=True,
            text=True
        )

        return {
            "valid": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }

    def check_ontology_element(
        self,
        element_type: str,
        description: str,
        ontology_type: str = "entity"
    ) -> Dict[str, Any]:
        """
        Check if an ontology element already exists or has similar matches.

        Args:
            element_type: The type to check (e.g., "Service", "DEPENDS_ON")
            description: Description of the element
            ontology_type: "entity" or "relationship"

        Returns:
            Dict with check results including recommendation
        """
        result = subprocess.run(
            [
                sys.executable,
                str(self.scripts_dir / "check_master_ontology.py"),
                ontology_type,
                element_type,
                description
            ],
            capture_output=True,
            text=True
        )

        # Parse the output to extract key information
        output = result.stdout

        return {
            "output": output,
            "recommendation": self._extract_recommendation(output),
            "has_exact_match": "EXACT MATCH" in output,
            "has_similar": "SIMILAR ELEMENTS FOUND" in output
        }

    def _extract_recommendation(self, output: str) -> str:
        """Extract recommendation from check output."""
        for line in output.split('\n'):
            if "RECOMMENDATION:" in line:
                if "USE_EXISTING" in line:
                    return "USE_EXISTING"
                elif "REVIEW_SIMILAR" in line:
                    return "REVIEW_SIMILAR"
                elif "CREATE_NEW" in line:
                    return "CREATE_NEW"
        return "UNKNOWN"

    def update_master_ontology(
        self,
        partition_id: str,
        update_type: str = "both"
    ) -> Dict[str, Any]:
        """
        Update master ontology with elements from a partition.

        Args:
            partition_id: ID of the partition to merge
            update_type: "entity", "relationship", or "both"

        Returns:
            Dict with update results
        """
        result = subprocess.run(
            [
                sys.executable,
                str(self.scripts_dir / "update_master_ontology.py"),
                partition_id,
                update_type
            ],
            capture_output=True,
            text=True
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }

    def view_checklist(self, checklist_id: str, recursive: bool = False) -> str:
        """
        View checklist status.

        Args:
            checklist_id: ID of checklist to view
            recursive: If True, expand sub-checklists

        Returns:
            Formatted checklist output
        """
        cmd = [
            sys.executable,
            str(self.scripts_dir / "manage_checklist.py"),
            "view",
            checklist_id
        ]
        if recursive:
            cmd.append("--recursive")

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout

    def check_off_item(self, checklist_id: str, item_id: str) -> Dict[str, Any]:
        """
        Mark a checklist item as completed.

        Args:
            checklist_id: ID of the checklist
            item_id: ID of the item to check off

        Returns:
            Dict with operation result
        """
        result = subprocess.run(
            [
                sys.executable,
                str(self.scripts_dir / "manage_checklist.py"),
                "check",
                checklist_id,
                item_id
            ],
            capture_output=True,
            text=True
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }

    def generate_preprocessing_checklist(self) -> Dict[str, Any]:
        """
        Generate preprocessing checklist based on existing partitions.

        Returns:
            Dict with generation result
        """
        result = subprocess.run(
            [
                sys.executable,
                str(self.scripts_dir / "manage_checklist.py"),
                "generate-preprocessing"
            ],
            capture_output=True,
            text=True
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }

    def get_master_ontology(self, ontology_type: str = "entity") -> Dict:
        """
        Load and return the master ontology.

        Args:
            ontology_type: "entity" or "relationship"

        Returns:
            Master ontology as dict
        """
        file_name = f"master_{ontology_type}_ontology.json"
        file_path = self.ontologies_dir / file_name

        if not file_path.exists():
            return {
                "ontology_type": ontology_type,
                "version": "0.1.0",
                "elements": []
            }

        with open(file_path, 'r') as f:
            return json.load(f)

    def list_partitions(self) -> List[str]:
        """
        Get list of all partition IDs.

        Returns:
            List of partition IDs
        """
        if not self.partitions_dir.exists():
            return []

        return sorted([f.stem for f in self.partitions_dir.glob("*.json")])

    def get_partition(self, partition_id: str) -> Optional[Dict]:
        """
        Load a specific partition.

        Args:
            partition_id: ID of the partition to load

        Returns:
            Partition data as dict, or None if not found
        """
        partition_path = self.partitions_dir / f"{partition_id}.json"

        if not partition_path.exists():
            return None

        with open(partition_path, 'r') as f:
            return json.load(f)

    def save_partition(self, partition_id: str, partition_data: Dict) -> bool:
        """
        Save a partition to file.

        Args:
            partition_id: ID for the partition
            partition_data: Partition data to save

        Returns:
            True if successful
        """
        try:
            self.partitions_dir.mkdir(parents=True, exist_ok=True)
            partition_path = self.partitions_dir / f"{partition_id}.json"

            with open(partition_path, 'w') as f:
                json.dump(partition_data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error saving partition: {e}", file=sys.stderr)
            return False

    def get_data_files(self) -> List[str]:
        """
        Get list of all files in data/ directory (excluding .git).

        Returns:
            List of relative file paths
        """
        data_files = []

        if not self.data_dir.exists():
            return data_files

        for file_path in self.data_dir.rglob("*"):
            if ".git" not in file_path.parts and file_path.is_file():
                data_files.append(str(file_path))

        return sorted(data_files)


def main():
    """Demo usage of agent tools."""
    tools = KGaaSTools()

    print("=== KGaaS Agent Tools Demo ===\n")

    # List data files
    print(f"Data files found: {len(tools.get_data_files())}")

    # List partitions
    partitions = tools.list_partitions()
    print(f"Partitions found: {len(partitions)}")
    if partitions:
        for p_id in partitions:
            partition = tools.get_partition(p_id)
            print(f"  - {p_id}: {partition.get('title', 'No title')}")

    # View master checklist
    print("\n=== Master Checklist ===")
    print(tools.view_checklist("master_checklist"))


if __name__ == "__main__":
    main()
