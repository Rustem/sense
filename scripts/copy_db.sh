#!/bin/bash
# Copy KnowledgeC database to data directory

set -e

SOURCE="$HOME/Library/Application Support/Knowledge/knowledgeC.db"
DEST="data/knowledgeC.db"
BACKUP_DIR="data/backups"

# Check if source exists
if [ ! -f "$SOURCE" ]; then
    echo "Error: KnowledgeC database not found at $SOURCE"
    echo "Make sure you have Full Disk Access enabled for Terminal"
    exit 1
fi

# Create directories
mkdir -p "$BACKUP_DIR"

# Backup existing if it exists
if [ -f "$DEST" ]; then
    TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
    echo "Backing up existing database to $BACKUP_DIR/knowledgeC_$TIMESTAMP.db"
    cp "$DEST" "$BACKUP_DIR/knowledgeC_$TIMESTAMP.db"
fi

# Copy database
echo "Copying KnowledgeC database..."
cp "$SOURCE" "$DEST"

# Check size
SIZE=$(du -h "$DEST" | cut -f1)
echo "✓ Database copied successfully ($SIZE)"
echo "Location: $DEST"
