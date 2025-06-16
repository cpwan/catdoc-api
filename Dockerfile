FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN apt-get update && apt-get install -y \
    catdoc \
    && rm -rf /var/lib/apt/lists/*
# Copy the project into the image
ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0", "--port", "8000"]