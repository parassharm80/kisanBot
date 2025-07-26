# Use slim Python 3.12 base image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y gcc build-essential

# Set workdir
WORKDIR /app

# Copy source code and requirements
COPY ./src /app/src
COPY requirements.txt .

# Set environment for Python and GCP
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Expose Cloud Run port
EXPOSE 8080

# Start FastAPI app via Uvicorn
CMD ["uvicorn", "chat_app.run:app", "--host", "0.0.0.0", "--port", "8080"]
