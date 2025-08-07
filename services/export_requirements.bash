#!/bin/bash
# filepath: /workspace/ms-backend/services/export_requirements.sh

echo "Starting batch export of requirements.txt for all service groups..."

# Find all service groups (e.g. auth_service) in pyproject.toml
SERVICE_GROUPS=$(grep -oP '\[tool.poetry.group.\K[^]]+' pyproject.toml | grep service | cut -d. -f1 | sort | uniq)

for GROUP in $SERVICE_GROUPS; do
    FOLDER=$(echo "$GROUP" | tr '_' '-')
    mkdir -p "$FOLDER"
    echo "Exporting requirements for group: $GROUP -> $FOLDER/requirements.txt"
    poetry export --without-hashes --with "$GROUP" -f requirements.txt -o "$FOLDER/requirements.txt"
    if [ $? -eq 0 ]; then
        echo "Exported: $FOLDER/requirements.txt"
    else
        echo "Failed to export for group: $GROUP"
    fi
done

echo "Batch export completed."