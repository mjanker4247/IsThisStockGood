# Use a lightweight Python base image
FROM python:3.12-slim
# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 
ENV PYTHONDONTWRITEBYTECODE=1
# Set working directory
WORKDIR /app
# Copy the full app into the container
COPY . .
# Install Python dependencies using uv
RUN python -m pip install --no-cache-dir uv \
    && uv pip install --system .
# Expose the web port
EXPOSE 8080
# Default command: run the Flask web service
CMD ["python", "main.py"]
