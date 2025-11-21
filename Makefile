.PHONY: help clean fetch-openshift-docs fetch-rosa-kcs fetch-all list-data install-deps

# Default target
help:
	@echo "Kartograph Data Extraction - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make install-deps        - Install Python dependencies"
	@echo "  make fetch-openshift-docs - Fetch OpenShift documentation"
	@echo "  make fetch-rosa-kcs      - Fetch ROSA KCS solutions (requires credentials)"
	@echo "  make fetch-all           - Fetch all data sources"
	@echo "  make list-data           - List all downloaded data"
	@echo "  make clean               - Remove all downloaded data"
	@echo "  make clean-openshift     - Remove OpenShift docs only"
	@echo "  make clean-rosa-kcs      - Remove ROSA KCS only"
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

# Fetch all data sources
fetch-all: fetch-openshift-docs fetch-rosa-kcs

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

# Quick switch between data sources
switch-to-openshift: clean-rosa-kcs fetch-openshift-docs
	@echo "✓ Switched to OpenShift docs"

switch-to-rosa: clean-openshift fetch-rosa-kcs
	@echo "✓ Switched to ROSA KCS"

