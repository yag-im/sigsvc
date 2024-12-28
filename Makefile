ROOT_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
SHELL := /bin/bash

include .devcontainer/.env
export

APP_NAME := webrtc.sigsvc
DOCKER_IMAGE_TAG := $(APP_NAME):dev

.PHONY: help
help: ## This help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: build
build: ## Build app package
	rm -rf dist
	poetry build -f wheel

.PHONY: bootstrap
bootstrap: ## Perform a bootstrap
	# deleting as there may be a conflict when running inside a devcontainer vs local host
	rm -rf .venv && rm -rf .tox
	curl -sSL https://install.python-poetry.org | python3 - --uninstall || true
	curl -sSL https://install.python-poetry.org | python3 -
	# help IDEs to recognize venv's python interpreter
	poetry config virtualenvs.in-project true
	poetry self add "poetry-dynamic-versioning[plugin]"
	# poetry will create .venv as well:
	poetry install --only dev
	# install pre-commit hooks
	source .venv/bin/activate \
		&& pre-commit install \
		&& pre-commit install --hook-type commit-msg
	# install app and all deps
	poetry install

.PHONY: lint
lint: ## Run linters
	poetry run tox -e lint

.PHONY: test
test: ## Run unit tests
	poetry run tox -e test

.PHONY: clean
clean: ## Remove all generated artifacts (except .venv and .env)
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -rf {} +
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf .tox
	rm -rf dist

.PHONY: docker-run
docker-run: ## Run dev docker image
	docker run --rm -it \
		--name yag-$(APP_NAME) \
		-p $(LISTEN_PORT):$(LISTEN_PORT)/tcp \
		--env-file $(ROOT_DIR)/.devcontainer/.env \
		--env-file $(ROOT_DIR)/.devcontainer/secrets.env \
		$(DOCKER_IMAGE_TAG)

.PHONY: docker-build
docker-build: ## Build docker image
	docker build \
		-t $(DOCKER_IMAGE_TAG) \
		--progress plain \
		.

.PHONY: gha-build
gha-build: ## GitHub action: install all deps, lint, test and build app
	poetry install --only dev
	$(MAKE) lint
	$(MAKE) test
	poetry install
	poetry build -f wheel
