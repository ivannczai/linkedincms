# Use a more specific and potentially updated base image tag
FROM python:3.10-slim-bookworm

WORKDIR /app

# Install system dependencies
# - netcat-openbsd provides the 'nc' command used in entrypoint.sh
# - postgresql-client provides pg_isready (optional more robust check)
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    # postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.6.1

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Copy only configuration files first to leverage Docker cache
COPY pyproject.toml poetry.lock* ./
# Install dependencies using the lock file
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy the rest of the application code
COPY . .

# Dependencies (including the app in editable mode) are already installed

# Expose the port the app will run on
EXPOSE 8000

# Set the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command passed to the entrypoint (starts Uvicorn via the script)
# The entrypoint script itself calls uvicorn, so CMD can be empty or omitted
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
