set dotenv-load

port := "8000"
py := "3.13"
ref := "main"

build: update pre-commit typing coverage

build-db $ONLY_GROUP="build":
    uv run --python={{py}} python -I build.py --git-ref={{ref}}

[group('update')]
update: gha-update pre-commit-autoupdate lock

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
    uv run --python={{py}} --no-dev granian --port={{port}} hub_api.main:app

[group('test')]
pre-commit:
    -uvx --python={{py}} --with pre-commit-uv pre-commit run --all-files

[group('test')]
typing:
    uv run --python={{py}} mypy src tests

[group('test')]
test $ONLY_GROUP="tests": build-db
    uv run --python={{py}} pytest

[group('test')]
coverage $ONLY_GROUP="tests": build-db
    uv run --python={{py}} coverage run -m pytest -v
    uv run --python={{py}} coverage combine --keep
    uv run --python={{py}} coverage report --fail-under=100 --show-missing

[group('test')]
api host="127.0.0.1": build-db
    uvx --python={{py}} --from=schemathesis st run --checks all --base-url http://{{host}}:{{port}} --experimental=openapi-3.1 http://{{host}}:{{port}}/openapi.json
