# Use official slim Python 3.11 image
FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8501

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definitions
COPY pyproject.toml requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

# Create target directories
RUN mkdir -p artifacts src app config

# Copy application source code and precomputed artifacts
COPY src/ ./src/
COPY app/ ./app/
COPY config/ ./config/
COPY artifacts/ ./artifacts/

# Expose Streamlit port
EXPOSE 8501

# Healthcheck for container orchestrators
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Command to launch Streamlit app
CMD ["streamlit", "run", "app/Home.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
