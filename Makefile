typecheck:
	uv run ty check src

format:
	uv run ruff format src

lint:
	uv run ruff src


.PHONY: typecheck format lint
