#!/usr/bin/env bash
#
# sync-local-dev.sh
#
# This script automates the local Git operations required after a Pull Request
# from the 'dev' branch has been successfully merged into 'main' on GitHub,
# and the CI/CD pipeline has recreated the remote 'dev' branch from 'main'.
#
# It ensures that the local 'main' branch is up-to-date and then resets
# the local 'dev' branch to mirror the new remote 'dev' branch.
#
# Prerequisites:
# 1. The PR on GitHub (dev -> main) must be merged.
# 2. The 'cycle-dev-branch.yml' GitHub Actions workflow must have completed
#    successfully, recreating 'origin/dev'.
#
# Usage:
#   Run this script from the root of your Git repository.
#   ./scripts/sync-local-dev.sh

set -e # Exit immediately if a command exits with a non-zero status.

echo "🔄 Starting local sync process after 'dev' -> 'main' merge..."

# Ensure we are not on the dev branch to avoid issues deleting it later
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" == "dev" ]; then
  echo "   Switching from 'dev' to 'main' branch..."
  git checkout main
  if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to checkout 'main' branch. Aborting."
    exit 1
  fi
fi

echo "Updating local 'main' branch from 'origin/main'..."
git checkout main # Double-check we are on main
git pull origin main
if [ $? -ne 0 ]; then
  echo "❌ ERROR: Failed to pull updates for 'main' branch. Aborting."
  exit 1
fi

echo "Fetching all remote changes and pruning stale remote-tracking branches..."
# This ensures our local view of the remote (origin) is up-to-date,
# especially for the newly created origin/dev.
git fetch origin --prune
if [ $? -ne 0 ]; then
  echo "❌ ERROR: Failed to fetch from 'origin'. Aborting."
  exit 1
fi

echo "Deleting old local 'dev' branch (if it exists)..."
# We use -D to force delete, as the old local 'dev' is now outdated.
# The `|| true` part ensures the script doesn't exit if 'dev' didn't exist locally.
git branch -D dev > /dev/null 2>&1 || true

echo "Creating new local 'dev' branch tracking 'origin/dev'..."
# The remote 'origin/dev' should now be a fresh copy of 'origin/main'.
git checkout -b dev origin/dev
if [ $? -ne 0 ]; then
  echo "❌ ERROR: Failed to create new local 'dev' branch from 'origin/dev'. Aborting."
  exit 1
fi

echo "✅ Success! Local 'main' is updated, and local 'dev' has been reset from 'origin/dev'."
echo "You are now on branch: $(git rev-parse --abbrev-ref HEAD)"