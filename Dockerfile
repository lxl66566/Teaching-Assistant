# Stage 1: Build frontend
FROM node:20-alpine AS frontend_builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile
COPY frontend/ .
RUN pnpm build

# # Stage 2: Build backend
# FROM python:3.12-slim-bookworm AS backend_builder

# # Install git for backend dependencies
# RUN apt-get install -y git

# WORKDIR /app/backend

# # Install uv
# RUN pip install uv

# # Copy backend application code and dependency files
# COPY backend/pyproject.toml ./
# COPY backend/uv.lock ./

# # Install dependencies into a virtual environment
# RUN uv sync --prerelease=allow --no-dev

# # Copy backend application code
# COPY backend/app/ ./app/

# Final stage: Runtime image
FROM python:3.12-slim-bookworm

ENV NO_PROXY="localhost,127.0.0.1,ollama"

RUN apt-get update \
    && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Copy backend application code
COPY backend /app/backend

# Copy frontend build artifacts
COPY --from=frontend_builder /app/frontend/dist /app/frontend/dist

WORKDIR /app/backend

# Expose port
EXPOSE 8000

# Set entrypoint: activate virtual environment and run the app
CMD ["uv", "run", "--prerelease=allow", "--no-dev", "python", "-m", "app"]