set dotenv-load
source := "meltano-hub/_data"

build-db $ONLY_GROUP="build":
    uv run python -I build.py {{source}}

[group('update')]
gha-update:
    uvx --python python3.12 gha-update

[group('update')]
pre-commit-autoupdate:
    uvx pre-commit autoupdate

[group('update')]
lock:
    uv lock

serve: build-db
    uv run --no-dev granian hub_api.main:app

test $ONLY_GROUP="tests": build-db
    uv run pytest

coverage $ONLY_GROUP="tests": build-db
    uv run coverage run -m pytest -v
    uv run coverage combine --keep
    uv run coverage report --fail-under=100 --show-missing
