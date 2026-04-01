FROM python:3.11-slim

LABEL authors="gyankritbhuyan"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create working directory for the app
WORKDIR /app

# Copy the requirements file specifically
COPY requirements.txt /app/MCP_Enhancement/

# Install dependencies (plus fastapi and uvicorn which are imported but might not be in requirements.txt directly)
RUN pip install --no-cache-dir -r /app/MCP_Enhancement/requirements.txt \
    && pip install --no-cache-dir fastapi uvicorn

# Copy the contents of the local MCP_Enhancement directory into /app/MCP_Enhancement
COPY . /app/MCP_Enhancement/

# Set working directory to the project root for execution
WORKDIR /app/MCP_Enhancement

# Expose the port used by the FastAPI app
EXPOSE 3000

# Command to run the application
CMD ["python", "agent_start.py"]