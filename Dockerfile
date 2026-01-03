FROM python:3.11-slim

# Install Java (required for tabula-py)
RUN apt-get update && \
    apt-get install -y default-jre && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway will use PORT env variable)
EXPOSE 10000

# Run the application
# Use Railway's PORT environment variable if set, otherwise default to 10000
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
