# Use Python 3.13 as base image
FROM python:3.13-slim

# Install curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

# Switch to non-root user for runtime
USER user

# Set environment variables for non-root user
#ENV HOME=/home/user \
#	PATH=/home/user/.local/bin:$PATH

# Set working directory
WORKDIR /home/user/app

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy the current directory contents into the container working directory setting the owner to the user
COPY --chown=user . .

# Use light configuration for public deployment
RUN cp -f light_public_config.json config.json

# Install Python dependencies with uv (as user)
RUN /home/user/.local/bin/uv sync --frozen

# Set environment variables
ENV PYTHONPATH=/home/user/app
ENV PYTHONUNBUFFERED=1

# Expose the port (Hugging Face Spaces default is 7860)
EXPOSE 7860

# Command to run the application
CMD ["/home/user/.local/bin/uv", "run", "main.py", "--host", "0.0.0.0", "--port", "7860"]
