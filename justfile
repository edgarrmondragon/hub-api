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

test: build-db
    uv run pytest
