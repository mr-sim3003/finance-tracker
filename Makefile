.PHONY: test test-sqlite test-pg lint

test: test-sqlite

test-sqlite:
	pytest

test-pg:
	pytest --ds=config.settings.postgres_test

lint:
	ruff check .

