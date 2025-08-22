# Use Python 3.11 as base image (compatible with Hugging Face Spaces)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application files
COPY . .

# Create a non-root user for security
RUN useradd -m -u 1000 user
USER user

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the port (Hugging Face Spaces default is 7860)
EXPOSE 7860

# Command to run the application
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "7860"]
