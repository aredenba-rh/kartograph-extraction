#!/usr/bin/env python3
"""
Check master ontology for similar elements before adding new ones.

This script helps standardize ontologies across partitions by checking
if similar entity or relationship types already exist in the master ontology.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from difflib import SequenceMatcher


def load_master_ontology(ontology_type: str) -> Dict:
    """Load master entity or relationship ontology."""
    file_name = f"master_{ontology_type}_ontology.json"
    file_path = Path("ontologies") / file_name

    if not file_path.exists():
        print(f"❌ Master ontology file not found: {file_path}")
        return {}

    with open(file_path, 'r') as f:
        return json.load(f)


def similarity_score(str1: str, str2: str) -> float:
    """Calculate similarity between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def find_similar_elements(
    new_type: str,
    new_description: str,
    master_ontology: Dict,
    similarity_threshold: float = 0.6
) -> List[Dict]:
    """
    Find similar elements in the master ontology.

    Args:
        new_type: The type name to check (e.g., "Configuration")
        new_description: Description of the new element
        master_ontology: The loaded master ontology
        similarity_threshold: Minimum similarity score (0.0-1.0)

    Returns:
        List of similar elements with similarity scores
    """
    similar_elements = []

    for element in master_ontology.get("elements", []):
        existing_type = element["type"]
        existing_desc = element.get("description", "")

        # Calculate similarities
        type_sim = similarity_score(new_type, existing_type)
        desc_sim = similarity_score(new_description, existing_desc) if existing_desc else 0.0

        # Combined score (weighted towards type similarity)
        combined_sim = (type_sim * 0.7) + (desc_sim * 0.3)

        if combined_sim >= similarity_threshold:
            similar_elements.append({
                "type": existing_type,
                "description": existing_desc,
                "source_partitions": element.get("source_partitions", []),
                "similarity_score": combined_sim,
                "type_similarity": type_sim,
                "description_similarity": desc_sim
            })

    # Sort by similarity score (descending)
    similar_elements.sort(key=lambda x: x["similarity_score"], reverse=True)

    return similar_elements


def check_element(
    element_type: str,
    description: str,
    ontology_type: str = "entity"
) -> Dict:
    """
    Check if an element already exists or has similar matches.

    Args:
        element_type: The type to check (e.g., "Service", "DEPENDS_ON")
        description: Description of the element
        ontology_type: "entity" or "relationship"

    Returns:
        Dictionary with check results
    """
    master_ontology = load_master_ontology(ontology_type)

    if not master_ontology:
        return {
            "exists": False,
            "similar_elements": [],
            "recommendation": "CREATE_NEW",
            "message": "Master ontology could not be loaded"
        }

    # Check for exact match
    exact_match = None
    for element in master_ontology.get("elements", []):
        if element["type"].lower() == element_type.lower():
            exact_match = element
            break

    if exact_match:
        return {
            "exists": True,
            "exact_match": exact_match,
            "recommendation": "USE_EXISTING",
            "message": f"Exact match found: '{exact_match['type']}'"
        }

    # Check for similar elements
    similar = find_similar_elements(element_type, description, master_ontology)

    if similar:
        if similar[0]["similarity_score"] > 0.85:
            recommendation = "USE_EXISTING"
            message = f"Very similar element found: '{similar[0]['type']}' (score: {similar[0]['similarity_score']:.2f})"
        else:
            recommendation = "REVIEW_SIMILAR"
            message = f"Similar elements found. Review before creating new."
    else:
        recommendation = "CREATE_NEW"
        message = "No similar elements found. Safe to create new element."

    return {
        "exists": False,
        "similar_elements": similar,
        "recommendation": recommendation,
        "message": message
    }


def format_check_results(results: Dict, element_type: str, ontology_type: str):
    """Print formatted check results."""
    print("\n" + "="*60)
    print(f"CHECKING {ontology_type.upper()} ONTOLOGY: '{element_type}'")
    print("="*60)

    print(f"\n{results['message']}")

    if results["exists"]:
        exact = results["exact_match"]
        print(f"\n✅ EXACT MATCH:")
        print(f"  Type: {exact['type']}")
        print(f"  Description: {exact['description']}")
        print(f"  Source Partitions: {', '.join(exact['source_partitions'])}")
        print(f"\n📋 RECOMMENDATION: {results['recommendation']}")
        print(f"  Use the existing type: '{exact['type']}'")

    elif results["similar_elements"]:
        print(f"\n🔍 SIMILAR ELEMENTS FOUND ({len(results['similar_elements'])}):")
        for i, similar in enumerate(results["similar_elements"][:5], 1):  # Show top 5
            print(f"\n  {i}. Type: {similar['type']}")
            print(f"     Similarity: {similar['similarity_score']:.2%} "
                  f"(type: {similar['type_similarity']:.2%}, "
                  f"desc: {similar['description_similarity']:.2%})")
            print(f"     Description: {similar['description'][:100]}...")
            print(f"     Source Partitions: {', '.join(similar['source_partitions'])}")

        print(f"\n📋 RECOMMENDATION: {results['recommendation']}")
        if results["recommendation"] == "USE_EXISTING":
            print(f"  Consider using: '{results['similar_elements'][0]['type']}'")
        else:
            print(f"  Review similar elements above before creating new type")

    else:
        print(f"\n📋 RECOMMENDATION: {results['recommendation']}")
        print(f"  No conflicts found. You can create this new element.")

    print("\n" + "="*60 + "\n")


def main():
    """Main CLI interface."""
    if len(sys.argv) < 4:
        print("Usage: python check_master_ontology.py <entity|relationship> <type> <description>")
        print("\nExample:")
        print("  python check_master_ontology.py entity 'Service' 'A microservice component'")
        print("  python check_master_ontology.py relationship 'DEPENDS_ON' 'Dependency between services'")
        return 1

    ontology_type = sys.argv[1]
    element_type = sys.argv[2]
    description = sys.argv[3]

    if ontology_type not in ["entity", "relationship"]:
        print("❌ Error: ontology_type must be 'entity' or 'relationship'")
        return 1

    results = check_element(element_type, description, ontology_type)
    format_check_results(results, element_type, ontology_type)

    return 0


if __name__ == "__main__":
    sys.exit(main())
