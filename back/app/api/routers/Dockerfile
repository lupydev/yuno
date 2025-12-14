## ------------------------------- Builder Stage ------------------------------ ##
FROM python:3.13-bookworm AS builder

# Install small tooling and the uv CLI to manage dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (astral) to manage dependencies exactly like local dev
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod +x /install.sh && /install.sh && rm /install.sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copy only the files needed to resolve dependencies (pyproject + lock)
COPY pyproject.toml uv.lock ./

# Install dependencies with uv (creates .venv automatically and installs all packages)
RUN uv sync

## ------------------------------- Production Stage ------------------------------ ##
FROM python:3.13-slim-bookworm AS production

# Minimal runtime packages (add libpq5 if you need PostgreSQL runtime libs)
RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home appuser || true

WORKDIR /app

# Copy the prepared .venv from the builder into the app dir so console-scripts exist
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:${PATH}"

# Copy application code, alembic migrations, and entrypoint
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser ./alembic ./alembic
COPY --chown=appuser:appuser ./entrypoint.sh ./entrypoint.sh
COPY --chown=appuser:appuser ./alembic.ini ./alembic.ini

RUN chmod +x ./entrypoint.sh || true

# Switch to non-root user
USER appuser

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="/app:${PYTHONPATH}"

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
