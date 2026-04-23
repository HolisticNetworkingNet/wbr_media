#!/usr/bin/env bash

# ---------------------------------------------
# Menu Goblin – Canonical Project Tree Generator
#
# Copyright (c) 2025 We Build Reactions.
# Proprietary and confidential.
#
# This file is a generated architectural artifact.
# It represents the intended high-level structure
# of the Menu Goblin subsystem and is used to:
#
# - Detect structural drift
# - Support architectural documentation
# - Aid onboarding and review
#
# Do not edit the generated tree manually.
# Re-run this script after intentional changes.
# ---------------------------------------------

set -euo pipefail

ROOT_DIR="."
OUTPUT_FILE="document-tree.txt"

if [ ! -d "$ROOT_DIR" ]; then
  echo "Error: $ROOT_DIR does not exist."
  exit 1
fi

cat > "$OUTPUT_FILE" <<'EOF'
# =============================================
# Belknap.biz – Canonical Project Tree
#
# Generated artifact. See generate_tree.sh
# =============================================

EOF

tree "$ROOT_DIR" \
  --dirsfirst \
  -I "__pycache__|*.pyc|.DS_Store|node_modules|.venv" \
  >> "$OUTPUT_FILE"

echo "✔ Tree written to $OUTPUT_FILE"
