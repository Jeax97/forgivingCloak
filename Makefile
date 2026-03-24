.PHONY: up down build logs restart clean dev

# Start all services
up:
	docker compose up -d

# Stop all services
down:
	docker compose down

# Build and start
build:
	docker compose up -d --build

# View logs
logs:
	docker compose logs -f

# Restart all services
restart:
	docker compose restart

# Full clean (removes volumes)
clean:
	docker compose down -v --remove-orphans

# Backend logs only
logs-backend:
	docker compose logs -f backend

# Frontend logs only
logs-frontend:
	docker compose logs -f frontend

# Redis logs only
logs-redis:
	docker compose logs -f redis

# Run database migrations
migrate:
	docker compose exec backend alembic upgrade head

# Create a new migration
migration:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

# Shell into backend container
shell:
	docker compose exec backend /bin/bash

# Run backend tests
test:
	docker compose exec backend pytest

# Dev mode - backend with hot reload
dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
