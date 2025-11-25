.PHONY: help clean fetch-openshift-docs fetch-rosa-kcs fetch-ops-sop fetch-all list-data install-deps \
	validate-partitions check-ontology update-ontology view-checklist check-item \
	generate-preprocessing start-extraction demo-tools

# Default target
help:
	@echo "Kartograph Data Extraction - Makefile"
	@echo ""
	@echo "=== Data Fetching ==="
	@echo "  make install-deps        - Install Python dependencies"
	@echo "  make fetch-openshift-docs - Fetch OpenShift documentation"
	@echo "  make fetch-rosa-kcs      - Fetch ROSA KCS solutions (requires credentials)"
	@echo "  make fetch-ops-sop       - Fetch OpenShift Ops SOP (requires credentials)"
	@echo "  make fetch-all           - Fetch all data sources"
	@echo "  make list-data           - List all downloaded data"
	@echo "  make clean               - Remove all downloaded data"
	@echo "  make clean-openshift     - Remove OpenShift docs only"
	@echo "  make clean-rosa-kcs      - Remove ROSA KCS only"
	@echo "  make clean-ops-sop       - Remove Ops SOP only"
	@echo ""
	@echo "=== KG Extraction Workflow ==="
	@echo "  make start-extraction    - Start the KG extraction workflow (Step 1: Partition + Ontology)"
	@echo "  make validate-partitions - Validate partition coverage"
	@echo "  make view-checklist      - View master checklist (use CHECKLIST=<id> for specific)"
	@echo "  make check-item          - Check off checklist item (CHECKLIST=<id> ITEM=<item_id>)"
	@echo "  make generate-preprocessing - Generate preprocessing checklist from partitions"
	@echo "  make demo-tools          - Demo the agent tools"
	@echo ""
	@echo "=== Ontology Management ==="
	@echo "  make check-ontology      - Check if ontology element exists (TYPE=<type> DESC=<desc> ONT=entity|relationship)"
	@echo "  make update-ontology     - Update master ontology from partition (PARTITION=<id> ONT=entity|relationship|both)"
	@echo ""
	@echo "Environment variables:"
	@echo "  ROSA_KCS_GIT_TOKEN       - GitHub token for rosa-kcs private repo"
	@echo ""

# Install Python dependencies
install-deps:
	@echo "Installing Python dependencies..."
	pip install pyyaml

# Fetch OpenShift documentation (public repo)
fetch-openshift-docs:
	@echo "Fetching OpenShift documentation..."
	python3 contexts/get_data_source.py contexts/openshift-docs.yaml

# Fetch ROSA KCS (private repo - requires credentials)
fetch-rosa-kcs:
	@if [ -z "$$ROSA_KCS_GIT_TOKEN" ]; then \
		echo "Error: ROSA_KCS_GIT_TOKEN environment variable not set"; \
		echo "Please set it in your .env file or export it:"; \
		echo "  export ROSA_KCS_GIT_TOKEN=your_token_here"; \
		exit 1; \
	fi
	@echo "Fetching ROSA KCS solutions..."
	python3 contexts/get_data_source.py contexts/rosa-kcs.yaml

# Fetch OpenShift Ops SOP (requires credentials)
fetch-ops-sop:
	@if [ -z "$$ROSA_KCS_GIT_TOKEN" ]; then \
		echo "Error: ROSA_KCS_GIT_TOKEN environment variable not set"; \
		echo "Please set it in your .env file or export it:"; \
		echo "  export ROSA_KCS_GIT_TOKEN=your_token_here"; \
		exit 1; \
	fi
	@echo "Fetching OpenShift Ops SOP..."
	python3 contexts/get_data_source.py contexts/ops-sop.yaml

# Fetch all data sources
fetch-all: fetch-openshift-docs fetch-rosa-kcs fetch-ops-sop

# List contents of data directory
list-data:
	@echo "Data directory contents:"
	@if [ -d "data" ]; then \
		find data -type f | head -20; \
		echo ""; \
		echo "Total files: $$(find data -type f | wc -l)"; \
		echo "Total size: $$(du -sh data | cut -f1)"; \
	else \
		echo "No data directory found. Run 'make fetch-openshift-docs' or 'make fetch-rosa-kcs' first."; \
	fi

# Clean all data
clean:
	@echo "Removing all data..."
	rm -rf data/
	@echo "✓ Cleaned all data"

# Clean specific data sources
clean-openshift:
	@echo "Removing OpenShift docs..."
	rm -rf data/openshift-docs/
	@echo "✓ Cleaned OpenShift docs"

clean-rosa-kcs:
	@echo "Removing ROSA KCS..."
	rm -rf data/rosa-kcs/
	@echo "✓ Cleaned ROSA KCS"

clean-ops-sop:
	@echo "Removing Ops SOP..."
	rm -rf data/ops-sop/
	@echo "✓ Cleaned Ops SOP"

# Quick switch between data sources
switch-to-openshift: clean-rosa-kcs fetch-openshift-docs
	@echo "✓ Switched to OpenShift docs"

switch-to-rosa: clean-openshift fetch-rosa-kcs
	@echo "✓ Switched to ROSA KCS"

# ============================================================================
# KG Extraction Workflow Targets
# ============================================================================

# Start the KG extraction workflow
start-extraction:
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║  KGaaS Extraction Workflow - Step 1: Partition + Ontology  ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "This workflow will guide you through:"
	@echo "  1. Creating a disjoint partition of files in data/"
	@echo "  2. Defining entity and relationship ontologies for each partition"
	@echo "  3. Building master ontologies across all partitions"
	@echo ""
	@echo "Available tools for the agent:"
	@echo "  - confirm_acceptable_partition.py - Validate partition coverage"
	@echo "  - check_master_ontology.py        - Check for similar ontology elements"
	@echo "  - update_master_ontology.py       - Update master ontologies"
	@echo "  - manage_checklist.py             - Track progress"
	@echo "  - agent_tools.py                  - Python API for all tools"
	@echo ""
	@echo "Current status:"
	@python3 scripts/manage_checklist.py view master_checklist
	@echo ""
	@echo "Next steps:"
	@echo "  1. Use Claude Agent SDK to analyze data/ folder"
	@echo "  2. Create partitions in partitions/ directory"
	@echo "  3. Run 'make validate-partitions' to check coverage"
	@echo "  4. Define ontologies for each partition"
	@echo "  5. Use checklist system to track progress"
	@echo ""

# Validate that partitions cover all files
validate-partitions:
	@echo "Validating partition coverage..."
	@python3 scripts/confirm_acceptable_partition.py

# View checklist (default: master_checklist)
view-checklist:
	@python3 scripts/manage_checklist.py view $(or $(CHECKLIST),master_checklist) $(if $(RECURSIVE),--recursive,)

# Check off a checklist item
check-item:
	@if [ -z "$(CHECKLIST)" ] || [ -z "$(ITEM)" ]; then \
		echo "Usage: make check-item CHECKLIST=<checklist_id> ITEM=<item_id>"; \
		echo "Example: make check-item CHECKLIST=01_create_file_partition ITEM=1.1"; \
		exit 1; \
	fi
	@python3 scripts/manage_checklist.py check $(CHECKLIST) $(ITEM)

# Generate preprocessing checklist
generate-preprocessing:
	@python3 scripts/manage_checklist.py generate-preprocessing

# Check ontology element
check-ontology:
	@if [ -z "$(TYPE)" ] || [ -z "$(DESC)" ]; then \
		echo "Usage: make check-ontology TYPE='<type>' DESC='<description>' ONT=entity|relationship"; \
		echo "Example: make check-ontology TYPE='Service' DESC='A microservice component' ONT=entity"; \
		exit 1; \
	fi
	@python3 scripts/check_master_ontology.py $(or $(ONT),entity) "$(TYPE)" "$(DESC)"

# Update master ontology from partition
update-ontology:
	@if [ -z "$(PARTITION)" ]; then \
		echo "Usage: make update-ontology PARTITION=<partition_id> ONT=entity|relationship|both"; \
		echo "Example: make update-ontology PARTITION=partition_01 ONT=both"; \
		exit 1; \
	fi
	@python3 scripts/update_master_ontology.py $(PARTITION) $(or $(ONT),both)

# Demo the agent tools
demo-tools:
	@python3 scripts/agent_tools.py

