set dotenv-load
source := "meltano-hub/_data"

build-db:
    uv run --group=build python -I build.py {{source}}

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
    uv run granian hub_api.main:app

test: build-db
    uv run --group=test pytest

coverage: build-db
    uv run --group=test coverage run -m pytest -v
    uv run --group=test coverage combine --keep
    uv run --group=test coverage report --fail-under=100 --show-missing
