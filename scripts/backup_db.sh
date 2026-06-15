#!/bin/bash
# Backup script for SQLite / PostgreSQL database
# Parses DATABASE_URL to determine database type and runs the backup.
set -e

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

DB_URL=${DATABASE_URL:-"sqlite:///blog.db"}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Get directory of this script and project root
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_ROOT="$(cd "$DIR/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups"
mkdir -p "$BACKUP_DIR"

if [[ "$DB_URL" == sqlite* ]]; then
    # SQLite Backup
    # Extract file path from URL (remove sqlite:// or sqlite:///)
    DB_FILE=$(echo "$DB_URL" | sed 's/sqlite:\/\/\///g' | sed 's/sqlite:\/\///g')
    
    # If the file path is relative, resolve it to project root
    if [[ "$DB_FILE" != /* ]]; then
        DB_FILE="$PROJECT_ROOT/$DB_FILE"
    fi
    
    BACKUP_FILE="$BACKUP_DIR/sqlite_backup_$TIMESTAMP.db"
    
    if [ -f "$DB_FILE" ]; then
        cp "$DB_FILE" "$BACKUP_FILE"
        gzip "$BACKUP_FILE"
        echo "SQLite database backup created: ${BACKUP_FILE}.gz"
    else
        echo "Error: SQLite database file not found at $DB_FILE"
        exit 1
    fi
elif [[ "$DB_URL" == postgres* ]]; then
    # PostgreSQL Backup
    BACKUP_FILE="$BACKUP_DIR/postgres_backup_$TIMESTAMP.sql"
    
    # Use pg_dump to backup PostgreSQL database
    pg_dump "$DB_URL" > "$BACKUP_FILE"
    gzip "$BACKUP_FILE"
    echo "PostgreSQL database backup created: ${BACKUP_FILE}.gz"
else
    echo "Error: Unsupported database scheme in DATABASE_URL: $DB_URL"
    exit 1
fi
