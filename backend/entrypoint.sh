#!/bin/bash
set -e

# Variables from environment (adjust names if needed in .env)
DB_HOST=${POSTGRES_HOST:-db}
DB_PORT=${POSTGRES_PORT:-5432}
DB_USER=${POSTGRES_USER:-postgres}
DB_PASSWORD=${POSTGRES_PASSWORD:-postgres}
DB_NAME=${POSTGRES_DB:-winning_sales_db} # Assuming this is the correct DB name from .env
FIRST_SUPERUSER_EMAIL=${FIRST_SUPERUSER_EMAIL:-admin@example.com} # Default if not set
FIRST_SUPERUSER_PASSWORD=${FIRST_SUPERUSER_PASSWORD:-admin123} # Default if not set

# Function to check if DB is ready
wait_for_db() {
    echo "Waiting for database at $DB_HOST:$DB_PORT..."
    # Use pg_isready utility (requires postgresql-client)
    # Or attempt connection using python/psycopg2 if client not available
    # Simple loop approach:
    retries=10
    while [ $retries -gt 0 ]; do
        # Check if the port is open (basic check)
        nc -z $DB_HOST $DB_PORT > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "Database connection port is open."
            # Optional: Add a more robust check like pg_isready if postgresql-client is installed
            # Or a small python script to attempt connection

            # Attempt Alembic connection check as a proxy
            echo "Attempting to check Alembic connection..."
            # Run alembic commands within the app directory context if needed
            if alembic current > /dev/null 2>&1; then
                 echo "Database seems ready (Alembic connected)."
                 return 0
            else
                 echo "Database port open, but Alembic connection failed. Retrying..."
            fi
        else
            echo "Database port not open yet. Retrying..."
        fi
        retries=$((retries - 1))
        sleep 3
    done

    echo "Error: Database connection timed out after multiple retries."
    exit 1
}

# Wait for the database
wait_for_db

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head

# Create initial superuser using the script
echo "Attempting to create initial superuser..."
# Ensure the script path is correct relative to WORKDIR /app
python /app/scripts/create_admin.py "$FIRST_SUPERUSER_EMAIL" "$FIRST_SUPERUSER_PASSWORD"
echo "Initial superuser creation process finished."

# Start the main application (Uvicorn)
# Use exec to replace the shell process with Uvicorn, allowing it to receive signals correctly
echo "Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
