SHELL := /bin/bash
.PHONY: help install run test docker-build docker-up docker-down docker-logs dev-up dev-down dev-logs ci

help:
	@echo "Common targets:"
	@echo "  install      - Sync Python deps with uv"
	@echo "  run          - Run the app locally (uv run python main.py)"
	@echo "  test         - Run pytest"
	@echo "  docker-run   - Build the production image and run the production docker compose"
	@echo "  docker-down  - Stop the production docker compose"
	@echo "  docker-logs  - Tail logs from the production service"
	@echo "  dev-up       - Run dev compose with live-reload and volume mount"
	@echo "  dev-down     - Stop dev compose"
	@echo "  dev-logs     - Tail logs from the dev service"

install:
	uv sync

run:
	uv run python main.py

test:
	uv run pytest

docker-run:
	docker compose build
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f --no-color

dev-up:
	docker compose -f docker-compose.dev.yml up -d --build

dev-down:
	docker compose -f docker-compose.dev.yml down

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f --no-color


