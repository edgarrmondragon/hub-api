source := "meltano-hub/_data"

build-db:
    uv run python -I build.py {{source}}

[group('update')]
gha-update:
    uvx gha-update

[group('update')]
pre-commit-autoupdate:
    uvx pre-commit autoupdate

[group('update')]
lock:
    uv lock

serve: build-db
    uv run uvicorn hub_api.main:app --reload

test: build-db
    uv run pytest

coverage: build-db
    uv run coverage run -m pytest -v
    uv run coverage combine --keep
    uv run coverage report --fail-under=100 --show-missing
