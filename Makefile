.PHONY: help clean fetch-openshift-docs fetch-rosa-kcs fetch-ops-sop fetch-all list-data install-deps \
	validate-partitions check-ontology update-ontology view-checklist check-item \
	generate-preprocessing start-extraction extraction-preview toggle-use-current-partition \
	create-partition list-partitions clean-partitions view-examples

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
	@echo "  make extraction-preview  - Preview data, flags, and checklist status"
	@echo "  make start-extraction    - Start the KG extraction workflow (with Claude SDK)"
	@echo "  make validate-partitions SOURCE=<data_source> - Validate partition coverage"
	@echo "  make view-checklist      - View master checklist (use CHECKLIST=<id> for specific)"
	@echo "  make check-item          - Check off checklist item (CHECKLIST=<id> ITEM=<item_id>)"
	@echo ""
	@echo "=== Partition Management ==="
	@echo "  make create-partition SOURCE=<data_source> TITLE='...' DESC='...' PATHS='path1 path2'"
	@echo "  make list-partitions     - List all existing file subsets"
	@echo "  make clean-partitions    - Remove all partition files"
	@echo "  make view-examples       - View example partition structure"
	@echo ""
	@echo "=== Extraction Flags ==="
	@echo "  make toggle-use-current-partition  - Skip partition creation, use existing partitions"
	@echo "  make toggle-use-current-ontologies - Skip ontology creation, use existing ontologies"
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
	pip install -r requirements.txt

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

# Preview extraction status
extraction-preview:
	@python3 scripts/extraction_preview.py

# Start the KG extraction workflow
start-extraction:
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║         KGaaS Extraction Workflow - Starting...            ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@python3 -m workflow.start_extraction

# Validate that partitions cover all files for a data source
validate-partitions:
	@if [ -z "$(SOURCE)" ]; then \
		echo "Usage: make validate-partitions SOURCE=<data_source>"; \
		echo "Example: make validate-partitions SOURCE=openshift-docs"; \
		exit 1; \
	fi
	@echo "Validating partition coverage for $(SOURCE)..."
	@python3 scripts/validate_partition.py $(SOURCE)

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

# Toggle flags
toggle-use-current-partition:
	@python3 scripts/toggle_flag.py use_current_partition

toggle-use-current-ontologies:
	@python3 scripts/toggle_flag.py use_current_ontologies

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

# ============================================================================
# Partition Management Targets
# ============================================================================

# Create a new file subset manually
create-partition:
	@if [ -z "$(SOURCE)" ] || [ -z "$(TITLE)" ] || [ -z "$(DESC)" ] || [ -z "$(PATHS)" ]; then \
		echo "Usage: make create-partition SOURCE=<data_source> TITLE='...' DESC='...' PATHS='path1 path2 ...'"; \
		echo "Example: make create-partition SOURCE=openshift-docs TITLE='AWS Docs' DESC='AWS integration files' PATHS='aws/'"; \
		exit 1; \
	fi
	@python3 scripts/create_file_subset.py "$(SOURCE)" "$(TITLE)" "$(DESC)" $(PATHS)

# List all existing file subsets
list-partitions:
	@echo "Existing file subsets:"
	@if [ -d "partitions" ]; then \
		for source_dir in partitions/*/; do \
			if [ -d "$$source_dir" ]; then \
				echo ""; \
				echo "📁 $$(basename $$source_dir)/"; \
				for file in $$source_dir*.json 2>/dev/null; do \
					if [ -f "$$file" ]; then \
						echo "  📋 $$(basename $$file)"; \
						python3 -c "import json; f=open('$$file'); d=json.load(f); print(f\"     ID: {d.get('partition_id')}\"); print(f\"     Title: {d.get('title')}\"); print(f\"     Paths: {len(d.get('paths', []))}\")"; \
					fi; \
				done; \
			fi; \
		done; \
	else \
		echo "No partitions directory found"; \
	fi

# Clean all partitions
clean-partitions:
	@echo "Removing all partitions..."
	@rm -rf partitions/*/
	@echo "✓ Cleaned all partition folders"

# View example partition structure
view-examples:
	@echo "Viewing example partition structure..."
	@cat examples/partition_example/README.md
