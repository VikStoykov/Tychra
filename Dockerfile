# Multi-stage build for Python package
FROM python:3.9-alpine AS builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev

# Install build tools
RUN pip install --no-cache-dir build wheel

# Copy only package files
COPY pyproject.toml README.md LICENSE version.py ./
COPY main.py ./
COPY src/ ./src/
COPY providers/ ./providers/

# Build the wheel
RUN python -m build --wheel

# Runtime stage
FROM python:3.9-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install runtime dependencies only
RUN apk add --no-cache libffi

# Copy and install only the wheel (no source code)
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm -rf /tmp/*.whl /root/.cache

# Create non-root user
RUN adduser -D -u 1000 botuser && \
    chown -R botuser:botuser /app
USER botuser

CMD ["tychra"]
