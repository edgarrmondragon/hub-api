set dotenv-load

port := "8000"
py := "3.13"
source := "meltano-hub/_data"

build-db $ONLY_GROUP="build":
    uv run --python={{py}} python -I build.py {{source}}

[group('update')]
gha-update:
    uvx --python {{py}} gha-update

[group('update')]
pre-commit-autoupdate:
    uvx --python={{py}} pre-commit autoupdate

[group('update')]
lock:
    uv lock --upgrade

serve: build-db
    uv run --python={{py}} --no-dev granian  --port={{port}} hub_api.main:app

[group('test')]
test $ONLY_GROUP="tests": build-db
    uv run --python={{py}} pytest

[group('test')]
coverage $ONLY_GROUP="tests": build-db
    uv run --python={{py}} coverage run -m pytest -v
    uv run --python={{py}} coverage combine --keep
    uv run --python={{py}} coverage report --fail-under=100 --show-missing

[group('test')]
api: build-db
    uvx --python={{py}} --from=schemathesis st run --checks all --base-url http://localhost:8000 --experimental=openapi-3.1 http://localhost:{{port}}/openapi.json
