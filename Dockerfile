# ---- 1. Build Stage ----
# Use a full Python image to build dependencies, which may need a compiler.
FROM python:3.11 as builder

WORKDIR /opt/venv
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install build-essential for compiling packages like hnswlib (for chromadb)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

RUN python -m venv .

COPY requirements.txt .
RUN . /opt/venv/bin/activate && pip install --no-cache-dir -r requirements.txt


# ---- 2. Final Stage ----
# Use a slim image for a smaller final container size.
FROM python:3.11-slim

WORKDIR /app

# Install curl for the healthcheck, and create a non-root user for security.
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --shell /bin/bash appuser

# Copy the virtual environment from the builder stage with correct ownership.
COPY --chown=appuser:appuser --from=builder /opt/venv /opt/venv

# Copy the application code as the new user.
COPY --chown=appuser:appuser . .

# Switch to the non-root user.
USER appuser

# Add the venv to the PATH and set environment variables.
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port the app runs on.
EXPOSE 8501

# Add a healthcheck to ensure the app is running correctly.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the Streamlit app, binding to all interfaces to be accessible.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]