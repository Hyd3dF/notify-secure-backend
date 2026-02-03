FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for compilation of some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variable to ensure output is flushed immediately
ENV PYTHONUNBUFFERED=1

# Expose the Flask port
EXPOSE 5000

# Script to run the application (Flask + Background Worker)
# We'll use a simple python script entrypoint or gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "run:app"]
