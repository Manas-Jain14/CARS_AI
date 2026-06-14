# Use an official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for potential builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the FastAPI/Gradio port
EXPOSE 8000

# Set environment variables
# Note: You should still provide GEMINI_API_KEY at runtime via -e or a .env file
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "main.py"]
