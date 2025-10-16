# Use a lightweight Python base image
FROM python:3.12-slim
# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh
# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh
# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 
ENV PYTHONDONTWRITEBYTECODE=1
# Set working directory
WORKDIR /app
# Copy the full app into the container
COPY . .
# Install Python dependencies using uv
RUN uv sync
# Expose the web port
EXPOSE 8080
# Default command: run the Flask web service
CMD ["uv", "run", "main.py"]
