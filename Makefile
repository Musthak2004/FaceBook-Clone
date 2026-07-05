.PHONY: help run migrate makemigrations test test-app check shell superuser collectstatic clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

run: ## Start the development server
	python manage.py runserver

migrate: ## Apply database migrations
	python manage.py migrate

makemigrations: ## Create new migrations
	python manage.py makemigrations

test: ## Run all tests
	python manage.py test

test-app: ## Run tests for a specific app (usage: make test-app app=accounts)
	python manage.py test $(app)

check: ## Run Django system checks
	python manage.py check

shell: ## Open Django shell
	python manage.py shell

superuser: ## Create a superuser
	python manage.py createsuperuser

collectstatic: ## Collect static files
	python manage.py collectstatic --noinput

clean: ## Clean Python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
