# hub-api

Experimental 🧪 alternative [Meltano Hub API](https://hub.meltano.com/), using the same underlying data as the official API.

Built with:

- SQLite
- [FastAPI]
- [Granian]
- [SQLAlchemy]
- [Schemathesis] (used for testing the OpenAPI spec)

## Usage

1. Build the plugin database:

    ```bash
    uv run python -I build.py
    ```

2. Run the following command to start the API server:

    ```bash
    uv run --no-dev granian hub_api.main:app
    ```

3. [Configure Meltano (v4+) to use the new API](https://docs.meltano.com/):

    ```bash
    meltano config set meltano hub_api_root "http://localhost:8000/meltano/api/v1"
    ```

4. Run Meltano as usual.

    ```bash
    meltano add extractor tap-github
    meltano lock --all --update
    ```

## Additional Features

This API also includes additional features that are not available in the official API.

### Default Variant Endpoint

The `/meltano/api/v1/plugins/<plugin type>/<plugin name>/default` endpoint returns the default variant for a plugin.

### Maintainers Endpoints

- `/meltano/api/v1/maintainers`: Returns a list of maintainers for all plugins.
- `/meltano/api/v1/maintainers/<maintainer>`: Returns details for a specific maintainer.

### ETag Support

All endpoints respond with an [`ETag`][etag] header, which can be used to check if the data has changed since the last request to save bandwidth.

```console
$ curl -I http://localhost:8000/meltano/api/v1/plugins/index
HTTP/1.1 200 OK
server: granian
content-length: 217962
content-type: application/json
etag: "etag-df7f7bd3-946d-4f48-99ae-eb64639eb76c"
date: Sat, 18 Jan 2025 13:21:35 GMT
```

```console
$ curl -I -X GET http://localhost:8000/meltano/api/v1/plugins/index -H 'If-None-Match: "etag-df7f7bd3-946d-4f48-99ae-eb64639eb76c"'
HTTP/1.1 304 Not Modified
server: granian
etag: "etag-df7f7bd3-946d-4f48-99ae-eb64639eb76c"
date: Sat, 18 Jan 2025 03:21:45 GMT
```

### GZip Compression

Large responses are compressed using GZip to save bandwidth.

```console
$ curl -I -X GET http://localhost:8000/meltano/api/v1/plugins/index
HTTP/1.1 200 OK
server: granian
content-length: 217962
content-type: application/json
etag: "etag-ad96ae68-5317-44c2-b700-0492035b741c"
date: Sat, 18 Jan 2025 03:26:20 GMT
```

```console
$ curl -I -X GET http://localhost:8000/meltano/api/v1/plugins/index -H 'Accept-Encoding: gzip'
HTTP/1.1 200 OK
server: granian
content-length: 19895
content-type: application/json
content-encoding: gzip
vary: Accept-Encoding
etag: "etag-ad96ae68-5317-44c2-b700-0492035b741c"
date: Sat, 18 Jan 2025 03:26:32 GMT
```

[etag]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ETag
[fastapi]: https://fastapi.tiangolo.com/
[granian]: https://github.com/emmett-framework/granian/
[sqlalchemy]: https://github.com/sqlalchemy/sqlalchemy/
[schemathesis]: https://github.com/schemathesis/schemathesis/
