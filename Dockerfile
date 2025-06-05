# Stage 1: Build frontend
FROM node:20-alpine AS frontend_builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile
COPY frontend/ .
RUN pnpm build

# Final stage: Runtime image
# Stage 2: Build backend
FROM python:3.12-slim-bookworm AS backend_builder

# Install git for backend dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# Install uv
RUN pip install uv

# Copy backend application code and dependency files
COPY backend/pyproject.toml ./
COPY backend/uv.lock ./

# Install dependencies into a virtual environment
RUN uv sync --prerelease=allow

# Copy backend application code
COPY backend/app/ ./app/

# Final stage: Runtime image
FROM python:3.12-slim-bookworm

WORKDIR /app

# Copy virtual environment from backend_builder
COPY --from=backend_builder /app/backend/.venv ./.venv

# Copy backend application code
COPY backend/app/ ./backend/app/

# Copy frontend build artifacts
COPY --from=frontend_builder /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Create a non-root user
RUN adduser --system --group appuser
USER appuser

# Set entrypoint: activate virtual environment and run the app
CMD ["sh", "-c", ". ./.venv/bin/activate && python -m backend.app"]
