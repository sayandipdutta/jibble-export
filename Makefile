typecheck:
	uv run ty check --output-format concise src

format:
	uv run ruff format src

lint:
	uv run ruff src


.PHONY: typecheck format lint
