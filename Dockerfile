FROM python:3.13

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install -U pip && pip install -r requirements.txt

RUN apt-get update && apt-get install -y curl \
    && curl -L https://github.com/vi/websocat/releases/download/v2.0.0/websocat.x86_64-unknown-linux-musl -o /usr/local/bin/websocat \
    && chmod +x /usr/local/bin/websocat \
    && apt-get remove -y curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wait-for-it.sh script
COPY wait-for-it.sh .
RUN chmod +x wait-for-it.sh

# Copy start.sh script
COPY start.sh .
RUN chmod +x start.sh

COPY api/ ./api

EXPOSE 8000

# Use start.sh as the entrypoint
# ENVIRONMENT variable can be set externally (e.g., via docker-compose or Kubernetes)
CMD ["./start.sh"]
