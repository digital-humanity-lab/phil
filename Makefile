.PHONY: test-python test-r test-all test-philcorpus lint build-api docker-up

test-python:
	@echo "Running Python tests..."
	@for pkg in python/*/; do \
		if [ -f "$$pkg/pyproject.toml" ]; then \
			echo "Testing $$pkg"; \
			cd "$$pkg" && python -m pytest tests/ && cd ../..; \
		fi \
	done

test-r:
	@echo "Running R tests..."
	@for pkg in r/*/; do \
		if [ -f "$$pkg/DESCRIPTION" ]; then \
			echo "Testing $$pkg"; \
			Rscript -e "testthat::test_dir('$$pkg/tests/testthat')"; \
		fi \
	done

test-philcorpus:
	@echo "Testing philcorpus..."
	@cd python/philcorpus && python -m pytest tests/ -v

test-all: test-python test-r

lint:
	@echo "Linting Python packages..."
	@ruff check python/
	@echo "Linting R packages..."
	@Rscript -e "lintr::lint_dir('r/')"

build-api:
	@echo "Building philapi..."
	@cd python/philapi && pip install -e .

docker-up:
	@echo "Starting services..."
	@docker compose -f docker/docker-compose.yml up -d
