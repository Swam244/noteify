# SETUP BASIC APP SETUP, BUT DATABASE SETUP IS REMAINING (IF DB IS USED LOCALLY)

FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:$PATH"

# Set work directory
WORKDIR /backend

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -Ls https://astral.sh/uv/install.sh | bash

# Copy project files
COPY . .

# Create virtual environment and install dependencies
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv sync

# Activate venv for the container
ENV PATH="/backend/.venv/bin:$PATH"

# Expose the port
EXPOSE 8000

# Start the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
