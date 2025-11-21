# kartograph-extraction

A sparse git checkout utility for extracting specific documentation and content from repositories for Knowledge Graph as a Service (KGaaS) platform development.

## Overview

This repository provides a declarative YAML-based system for performing shallow, sparse git checkouts of specific directories from source repositories. This allows you to efficiently extract only the content you need without cloning entire repositories.

## Features

- 🎯 **Sparse Checkout**: Only clone specific directories/paths
- ⚡ **Shallow Clone**: Uses `--depth=1` for minimal history
- 📝 **Declarative Configuration**: YAML-based data source definitions
- 🔐 **Credential Support**: Environment variable-based authentication for private repos
- 🔄 **Easy Switching**: Quickly switch between data sources
- 🧹 **Clean Management**: Easy cleanup of downloaded data

## Quick Start

### 1. Install Dependencies

```bash
make install-deps
```

### 2. Fetch OpenShift Documentation (Public)

```bash
make fetch-openshift-docs
```

This will create `data/openshift-docs/` with the following structure:
- `modules/` - Actual documentation content
- `_attributes/` - Variable definitions
- `snippets/` - Shared content fragments
- `rosa_*/` - ROSA-specific documentation (9 directories)
- `osd_*/` - OpenShift Dedicated documentation (8 directories)
- `hosted_control_planes/` - HCP documentation

### 3. Fetch ROSA KCS (Private - Requires Credentials)

First, set up your credentials:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your GitHub token
# ROSA_KCS_GIT_TOKEN=ghp_your_token_here
```

Then fetch:

```bash
make fetch-rosa-kcs
```

This will create `data/rosa-kcs/kcs_solutions/` with the KCS solutions content.

## Configuration

Data sources are defined as YAML files in the `contexts/` directory.

### Example: OpenShift Docs (`contexts/openshift-docs.yaml`)

```yaml
name: openshift-docs
description: OpenShift documentation - ROSA, OSD, and HCP content
git_url: https://github.com/openshift/openshift-docs
credential_env_var: null  # Public repo, no credentials needed
branch: main
sparse_paths:
  - modules/
  - _attributes/
  - rosa_architecture/
  # ... more paths
```

### Example: ROSA KCS (`contexts/rosa-kcs.yaml`)

```yaml
name: rosa-kcs
description: ROSA Knowledge Centered Service solutions
git_url: https://github.com/aredenba-rh/rosa-kcs
credential_env_var: ROSA_KCS_GIT_TOKEN
branch: main
sparse_paths:
  - kcs_solutions/
```

## Available Make Targets

```bash
make help                  # Show all available targets
make install-deps          # Install Python dependencies
make fetch-openshift-docs  # Fetch OpenShift documentation
make fetch-rosa-kcs        # Fetch ROSA KCS (requires credentials)
make fetch-all             # Fetch all data sources
make list-data             # List downloaded data
make clean                 # Remove all data
make clean-openshift       # Remove OpenShift docs only
make clean-rosa-kcs        # Remove ROSA KCS only
make switch-to-openshift   # Clean others and fetch OpenShift
make switch-to-rosa        # Clean others and fetch ROSA KCS
```

## Direct Script Usage

You can also use the Python script directly:

```bash
# Fetch with default settings
python3 contexts/get_data_source.py contexts/openshift-docs.yaml

# Fetch and list contents
python3 contexts/get_data_source.py contexts/openshift-docs.yaml --list

# Use custom data directory
python3 contexts/get_data_source.py contexts/openshift-docs.yaml --data-dir /tmp/data

# Clean only (no fetch)
python3 contexts/get_data_source.py contexts/openshift-docs.yaml --clean-only
```

## Directory Structure

```
kartograph-extraction/
├── contexts/              # Data source configuration files
│   ├── get_data_source.py # Sparse checkout utility script
│   ├── openshift-docs.yaml
│   └── rosa-kcs.yaml
├── data/                  # Downloaded content (gitignored)
│   ├── openshift-docs/
│   └── rosa-kcs/
├── extraction/            # Extraction and processing scripts
├── .env                   # Environment variables (gitignored)
├── .env.example           # Example environment configuration
├── Makefile               # Make targets for easy usage
└── README.md              # This file
```

## Adding New Data Sources

1. Create a new YAML file in `contexts/`:

```yaml
name: my-new-source
description: Description of the data source
git_url: https://github.com/org/repo
credential_env_var: MY_REPO_TOKEN  # or null for public repos
branch: main
sparse_paths:
  - path/to/content/
  - another/path/
```

2. Add your credential to `.env` (if needed):

```bash
MY_REPO_TOKEN=your_token_here
```

3. Add a Make target to `Makefile`:

```makefile
fetch-my-source:
	python3 contexts/get_data_source.py contexts/my-new-source.yaml --list
```

4. Run it:

```bash
make fetch-my-source
```

## Environment Variables

Create a `.env` file (from `.env.example`) with your credentials:

- `ROSA_KCS_GIT_TOKEN`: GitHub Personal Access Token for rosa-kcs repository
  - Create at: https://github.com/settings/tokens
  - Required scopes: `repo` (Full control of private repositories)

## Tips

- **Switching Data Sources**: Use `make clean` between fetches if you want to avoid mixing data
- **Storage**: Sparse checkouts are much smaller than full clones
- **Updates**: Re-run `make fetch-*` to get the latest content from `origin/main`
- **Git Metadata**: The `.git` directory is kept by default. Uncomment the cleanup code in `get_data_source.py` if you want to save more space

## Requirements

- Python 3.6+
- Git
- PyYAML (installed via `make install-deps`)

## License

[Your License Here]
