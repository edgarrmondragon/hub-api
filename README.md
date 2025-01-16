# hub-api

Experimental 🧪 alternative [Meltano Hub API](https://hub.meltano.com/), using the same underlying data as the official API.

Built with:

- SQLite
- [FastAPI](https://github.com/fastapi/fastapi/)
- [Granian](https://github.com/emmett-framework/granian/)
- [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy/)
- [Schemathesis](https://github.com/schemathesis/schemathesis/) (used for testing the OpenAPI spec)

## Usage

1. Run the following command to start the API server:

    ```bash
    uv run --no-dev granian hub_api.main:app
    ```

2. [Configure Meltano to use the new API](https://docs.meltano.com/):

    ```bash
    meltano config meltano set hub_api_root "http://localhost:8000/meltano/api/v1"
    ```

3. Run Meltano as usual.

    ```bash
    meltano add extractor tap-github
    meltano lock --all --update
    ```

### Additional Features

This API also includes additional features that are not available in the official API:

- `/meltano/api/v1/plugins/<plugin type>/<plugin name>/default`: Returns the default variant for a plugin.
- `/meltano/api/v1/maintainers`: Returns a list of maintainers for all plugins.
