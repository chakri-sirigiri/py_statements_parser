#!/usr/bin/env python3
"""
Simple version bumping script that manually updates pyproject.toml.
"""

import re
import subprocess
import sys
from pathlib import Path


def bump_version(version_type="patch"):
    """Bump the version in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")

    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        return False

    # Read the current content
    content = pyproject_path.read_text()

    # Find current version
    version_match = re.search(r'version = "(\d+)\.(\d+)\.(\d+)"', content)
    if not version_match:
        print("Error: Could not find version in pyproject.toml")
        return False

    major, minor, patch = map(int, version_match.groups())

    # Bump version based on type
    if version_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif version_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    new_version = f"{major}.{minor}.{patch}"
    print(
        f"Bumping version from {version_match.group(1)}.{version_match.group(2)}.{version_match.group(3)} to {new_version}"
    )

    # Replace version in content
    new_content = re.sub(r'version = "\d+\.\d+\.\d+"', f'version = "{new_version}"', content)

    # Also update current_version in bump-my-version config
    new_content = re.sub(r'current_version = "\d+\.\d+\.\d+"', f'current_version = "{new_version}"', new_content)

    # Write back to file
    pyproject_path.write_text(new_content)

    # Stage the changes - both pyproject.toml and uv.lock
    try:
        subprocess.run(["git", "add", "pyproject.toml", "uv.lock"], check=True)
        print("Version bumped and files staged successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error staging changes: {e}")
        return False


def main():
    """Main function."""
    if len(sys.argv) > 1:
        version_type = sys.argv[1]
        if version_type not in ["major", "minor", "patch"]:
            print("Invalid version type. Use: major, minor, or patch")
            sys.exit(1)
    else:
        version_type = "patch"

    success = bump_version(version_type)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
