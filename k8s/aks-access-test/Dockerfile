FROM python:3.10-alpine

WORKDIR /app

# Install required packages
RUN pip install --no-cache-dir requests urllib3

# Copy test script
COPY test.py .

# Make it executable
RUN chmod +x test.py

# Expose port for health checks
EXPOSE 8080

# Run the test
CMD ["python3", "test.py"]
