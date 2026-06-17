.PHONY: help install test lint scan run docker-build docker-run compose-up compose-down helm-lint clean

IMAGE ?= devops-demo-platform:local

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Install dev dependencies
	pip install -r app/requirements-dev.txt

test: ## Run unit tests with coverage
	cd app && pytest --cov=app --cov-report=term-missing

lint: ## Run ruff linter
	cd app && ruff check .

scan: ## Run bandit static security scan
	cd app && bandit -r app.py

run: ## Run the app locally (Flask dev server)
	cd app && python app.py

docker-build: ## Build the Docker image
	docker build -t $(IMAGE) .

docker-run: ## Run the container
	docker run --rm -p 8000:8000 $(IMAGE)

compose-up: ## Start app + Prometheus locally
	docker compose up --build

compose-down: ## Stop the local stack
	docker compose down

helm-lint: ## Lint the Helm chart
	helm lint helm/demo-app

clean: ## Remove caches and build artifacts
	rm -rf app/.pytest_cache app/.ruff_cache app/htmlcov app/.coverage **/__pycache__
