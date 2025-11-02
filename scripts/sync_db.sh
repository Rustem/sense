#!/bin/bash
# Script to copy KnowledgeC database to project directory
# This avoids macOS Full Disk Access restrictions

set -e

SOURCE_DB="$HOME/Library/Application Support/Knowledge/knowledgeC.db"
DEST_DB="$(dirname "$0")/../data/knowledgeC.db"

# Create data directory if it doesn't exist
mkdir -p "$(dirname "$DEST_DB")"

# Copy database
echo "Copying KnowledgeC database..."
cp "$SOURCE_DB" "$DEST_DB"

# Set permissions to read/write for owner
chmod 600 "$DEST_DB"

echo "Database synced successfully to: $DEST_DB"
echo "File size: $(du -h "$DEST_DB" | cut -f1)"
echo "Last modified: $(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$DEST_DB")"
