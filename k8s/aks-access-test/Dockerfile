FROM python:3.10-alpine

WORKDIR /app

# Install required packages with urllib3 1.26.x to avoid Python 3.10 SSLEOFError bug
RUN pip install --no-cache-dir requests urllib3==1.26.18

# Copy test script
COPY test.py .

# Make it executable
RUN chmod +x test.py

# Expose port for health checks
EXPOSE 8080

# Run the test with unbuffered output
CMD ["python3", "-u", "test.py"]
