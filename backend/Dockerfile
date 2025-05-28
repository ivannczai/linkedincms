# Stage 1: Build dependencies
FROM python:3.10-slim-bookworm AS builder

WORKDIR /app

# Install system dependencies
# - netcat-openbsd provides the 'nc' command used in entrypoint.sh
# - postgresql-client provides pg_isready (optional more robust check)
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    # postgresql-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.6.1

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Copy only configuration files first to leverage Docker cache
COPY pyproject.toml poetry.lock* ./
# Install dependencies using the lock file
RUN poetry install --no-interaction --no-ansi --no-root --only main

# Copy the entrypoint script first (can be cached if it doesn't change often)
COPY entrypoint.sh /app/entrypoint.sh

# Copy the rest of the application code
COPY . .

# Ensure entrypoint is executable AFTER all code is copied
RUN chmod +x /app/entrypoint.sh

# Dependencies (including the app in editable mode) are already installed

# Expose the port the app will run on
EXPOSE 8000

# Set the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command passed to the entrypoint (starts Uvicorn via the script)
# The entrypoint script itself calls uvicorn, so CMD can be empty or omitted
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 2: Production image
FROM python:3.10-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

RUN chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER nobody

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
