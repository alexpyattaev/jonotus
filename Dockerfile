# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set working directory in container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directories required by the application
RUN mkdir -p queues sequence_numbers

# Expose the port the app runs on
EXPOSE 5000

# Environment variables
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0"]
