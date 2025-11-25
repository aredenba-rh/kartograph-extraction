#!/usr/bin/env python3
"""
Sparse checkout utility for pulling specific paths from git repositories.

This script performs shallow, sparse git clones of repositories based on
YAML configuration files, allowing efficient extraction of specific directories
without cloning entire repositories.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import yaml

from dotenv import load_dotenv
load_dotenv()

class DataSourceFetcher:
    """Handles sparse checkout of git repositories based on YAML configuration."""

    def __init__(self, config_path: str, data_dir: str = "data"):
        """
        Initialize the fetcher.

        Args:
            config_path: Path to the YAML configuration file
            data_dir: Base directory where data will be stored (default: "data")
        """
        self.config_path = Path(config_path)
        self.data_dir = Path(data_dir)
        self.config = self._load_config()
        self.repo_name = self.config["name"]
        self.target_dir = self.data_dir / self.repo_name

    def _load_config(self) -> dict:
        """Load and validate the YAML configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            config = yaml.safe_load(f)

        # Validate required fields
        required_fields = ["name", "git_url", "branch", "sparse_paths"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field in config: {field}")

        if not config["sparse_paths"]:
            raise ValueError("sparse_paths cannot be empty")

        return config

    def _get_git_url_with_auth(self) -> str:
        """
        Get the git URL with authentication if credentials are configured.

        Returns:
            Git URL with embedded credentials (if applicable) or original URL
        """
        git_url = self.config["git_url"]
        credential_var = self.config.get("credential_env_var")

        # If no credential variable specified, return original URL
        if not credential_var:
            return git_url

        # Get the token from environment
        token = os.environ.get(credential_var)
        if not token:
            print(
                f"Warning: {credential_var} not found in environment. "
                "Attempting clone without authentication..."
            )
            return git_url

        # Inject token into URL for HTTPS authentication
        # Convert: https://github.com/user/repo -> https://token@github.com/user/repo
        if git_url.startswith("https://"):
            auth_url = git_url.replace("https://", f"https://{token}@")
            return auth_url

        return git_url

    def _run_command(
        self, cmd: list[str], cwd: Optional[Path] = None, check: bool = True, quiet: bool = False
    ) -> subprocess.CompletedProcess:
        """
        Run a shell command and handle errors.

        Args:
            cmd: Command and arguments as a list
            cwd: Working directory for the command
            check: Whether to raise exception on non-zero exit
            quiet: If True, suppress output unless there's an error

        Returns:
            CompletedProcess instance
        """
        if not quiet:
            print(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                check=check,
                capture_output=True,
                text=True,
            )
            if result.stdout and not quiet:
                print(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}", file=sys.stderr)
            if e.stderr:
                print(f"stderr: {e.stderr}", file=sys.stderr)
            raise

    def clean_existing(self) -> None:
        """Remove existing data directory if it exists."""
        if self.target_dir.exists():
            shutil.rmtree(self.target_dir)

    def fetch(self) -> None:
        """
        Perform the sparse checkout.

        This method:
        1. Creates the target directory
        2. Initializes a git repository
        3. Configures sparse checkout
        4. Adds the remote
        5. Fetches only specified paths with depth=1
        6. Checks out the branch
        7. Cleans up git metadata
        """
        print(f"\n{'=' * 60}")
        print(f"Fetching: {self.repo_name}")
        print(f"{'=' * 60}")

        num_paths = len(self.config["sparse_paths"])
        
        # Create data directory if it doesn't exist
        print(f"[1/7] Preparing directories...")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Clean existing checkout
        self.clean_existing()

        # Create target directory
        self.target_dir.mkdir(parents=True, exist_ok=True)

        # Initialize git repository
        print(f"[2/7] Initializing git repository...")
        self._run_command(["git", "init"], cwd=self.target_dir, quiet=True)

        # Configure sparse checkout
        print(f"[3/7] Configuring sparse checkout ({num_paths} paths)...")
        self._run_command(
            ["git", "config", "core.sparseCheckout", "true"], cwd=self.target_dir, quiet=True
        )

        # Write sparse-checkout patterns
        sparse_checkout_file = self.target_dir / ".git" / "info" / "sparse-checkout"
        sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)

        with open(sparse_checkout_file, "w") as f:
            for path in self.config["sparse_paths"]:
                f.write(f"{path}\n")

        # Add remote
        print(f"[4/7] Adding remote...")
        git_url = self._get_git_url_with_auth()
        self._run_command(
            ["git", "remote", "add", "origin", git_url], cwd=self.target_dir, quiet=True
        )

        # Fetch with depth=1 (shallow clone)
        branch = self.config["branch"]
        print(f"[5/7] Fetching from '{branch}' (depth=1)...")
        self._run_command(
            ["git", "fetch", "--depth=1", "origin", branch], cwd=self.target_dir, quiet=True
        )

        # Checkout the branch
        print(f"[6/7] Checking out branch...")
        self._run_command(["git", "checkout", branch], cwd=self.target_dir, quiet=True)

        # Count files and calculate size
        print(f"[7/7] Gathering statistics...")
        total_files = sum(1 for _ in self.target_dir.rglob("*") if _.is_file() and ".git" not in _.parts)
        total_size = sum(f.stat().st_size for f in self.target_dir.rglob("*") if f.is_file() and ".git" not in f.parts)
        
        # Format size nicely
        if total_size < 1024:
            size_str = f"{total_size} B"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.1f} KB"
        elif total_size < 1024 * 1024 * 1024:
            size_str = f"{total_size / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{total_size / (1024 * 1024 * 1024):.2f} GB"

        print(f"\n{'=' * 60}")
        print(f"✓ Successfully fetched {self.repo_name}")
        print(f"  Location: {self.target_dir}")
        print(f"  Files: {total_files:,}")
        print(f"  Size: {size_str}")
        print(f"  Paths: {num_paths}")
        print(f"{'=' * 60}\n")

    def list_contents(self) -> None:
        """List the contents that were checked out."""
        if not self.target_dir.exists():
            print(f"Target directory does not exist: {self.target_dir}")
            return

        print(f"\nContents of {self.target_dir}:")
        for item in sorted(self.target_dir.rglob("*")):
            if ".git" not in item.parts:
                rel_path = item.relative_to(self.target_dir)
                if item.is_file():
                    size = item.stat().st_size
                    print(f"  📄 {rel_path} ({size:,} bytes)")
                elif item.is_dir():
                    print(f"  📁 {rel_path}/")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Fetch data sources using sparse git checkout",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch OpenShift docs
  python get_data_source.py contexts/openshift-docs.yaml

  # Fetch ROSA KCS (requires ROSA_KCS_GIT_TOKEN in environment)
  python get_data_source.py contexts/rosa-kcs.yaml

  # Fetch and list contents
  python get_data_source.py contexts/openshift-docs.yaml --list

  # Custom data directory
  python get_data_source.py contexts/openshift-docs.yaml --data-dir /tmp/data
        """,
    )

    parser.add_argument(
        "config", help="Path to the YAML configuration file", type=str
    )

    parser.add_argument(
        "--data-dir",
        default="data",
        help="Base directory for storing data (default: data)",
        type=str,
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List contents after checkout",
    )

    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Only clean the existing data without fetching",
    )

    args = parser.parse_args()

    try:
        fetcher = DataSourceFetcher(args.config, args.data_dir)

        if args.clean_only:
            fetcher.clean_existing()
            print(f"✓ Cleaned {fetcher.target_dir}")
            return

        fetcher.fetch()

        if args.list:
            fetcher.list_contents()

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

