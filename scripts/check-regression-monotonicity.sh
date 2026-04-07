#!/usr/bin/env bash
set -euo pipefail

REGRESSION_DIR="tests/regression"
MAIN_BRANCH="${1:-main}"

current_count=$(find "$REGRESSION_DIR" -name "test_*.py" -type f | wc -l | tr -d ' ')

if git rev-parse --verify "$MAIN_BRANCH" >/dev/null 2>&1; then
  main_count=$(git ls-tree -r "$MAIN_BRANCH" --name-only -- "$REGRESSION_DIR" | grep -c "test_.*\.py$" || echo 0)
else
  main_count=0
fi

echo "Regression tests on $MAIN_BRANCH: $main_count"
echo "Regression tests on current branch: $current_count"

if [ "$current_count" -lt "$main_count" ]; then
  echo "ERROR: Regression test count decreased ($main_count -> $current_count)."
  echo "Regression tests must never be deleted."
  exit 1
fi

echo "OK: regression test count maintained or increased."
