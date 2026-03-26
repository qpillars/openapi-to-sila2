default:
    @just --
    
install:
    uv sync --all-packages

test:
    uv run pytest

lint:
    uv run ruff format --check .
    uv run ruff check .
    uv run ty check .

format: 
    uv run ruff format .
    uv run ruff check --fix .

build:
    uv build
