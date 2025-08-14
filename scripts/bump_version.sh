#!/bin/bash
# Simple version bumping script using built-in bump-my-version functionality

set -e

echo "Bumping version..."

# Use bump-my-version directly (faster than uv run)
bump-my-version bump patch --allow-dirty

# Stage all changes including the version bump
git add -A

echo "Version bumped and all changes staged successfully!"
