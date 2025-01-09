# hub-api

Experimental 🧪 alternative [Meltano Hub API](https://hub.meltano.com/), using the same underlying data as the official API.

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
