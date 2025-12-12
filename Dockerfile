# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies (if any needed for python-docx/pypdf/postgres)
# libpq-dev and gcc are often needed for psycopg2, though binary wheels exist.
# Keeping it minimal for now.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files first to leverage Docker cache
COPY requirements.txt requirements-web.txt ./

# Install python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements-web.txt && \
    # Install asyncpg for Postgres support
    pip install asyncpg

# Copy the rest of the application
COPY . .

# Create a non-root user and switch to it
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the application
# We use run_api.py directly or uvicorn
CMD ["python", "run_api.py"]

