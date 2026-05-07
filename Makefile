.PHONY: help setup up down build test lint clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Setup development environment
	./scripts/setup.sh

up: ## Start all services
	docker-compose -f infra/docker/docker-compose.yml up -d

up-dev: ## Start all services in development mode
	docker-compose -f infra/docker/docker-compose.yml -f docker-compose.override.yml up -d

down: ## Stop all services
	docker-compose -f infra/docker/docker-compose.yml down

build: ## Build all services
	docker-compose -f infra/docker/docker-compose.yml build

test: ## Run tests
	docker-compose -f infra/docker/docker-compose.yml exec backend pytest

test-cov: ## Run tests with coverage
	docker-compose -f infra/docker/docker-compose.yml exec backend pytest --cov=app --cov=src --cov-report=html

lint: ## Run linting
	docker-compose -f infra/docker/docker-compose.yml exec backend black --check .
	docker-compose -f infra/docker/docker-compose.yml exec backend isort --check-only .
	docker-compose -f infra/docker/docker-compose.yml exec backend flake8 .
	docker-compose -f infra/docker/docker-compose.yml exec backend mypy .

format: ## Format code
	docker-compose -f infra/docker/docker-compose.yml exec backend black .
	docker-compose -f infra/docker/docker-compose.yml exec backend isort .

migrate: ## Run database migrations
	./scripts/migrate.sh

logs: ## Show logs
	docker-compose -f infra/docker/docker-compose.yml logs -f

logs-backend: ## Show backend logs
	docker-compose -f infra/docker/docker-compose.yml logs -f backend

logs-frontend: ## Show frontend logs
	docker-compose -f infra/docker/docker-compose.yml logs -f frontend

logs-airflow: ## Show airflow logs
	docker-compose -f infra/docker/docker-compose.yml logs -f airflow-webserver airflow-scheduler

shell-backend: ## Open backend shell
	docker-compose -f infra/docker/docker-compose.yml exec backend bash

shell-airflow: ## Open airflow shell
	docker-compose -f infra/docker/docker-compose.yml exec airflow-webserver bash

clean: ## Clean up containers and volumes
	docker-compose -f infra/docker/docker-compose.yml down -v
	docker system prune -f