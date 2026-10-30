# CODE MANAGER

مرجع جامع نسخه فعلی: [دفترچه واحد](../../docs/manual/05-code-manager.md). اسناد تاریخی این README باید با وضعیت نسخه فعلی تطبیق داده شوند.


## Implemented

- `code_manager/blob_storage.py` stores binary content by SHA-256.
- `code_manager/source_archive.py` inspects ZIP bundles without extraction
  or execution.
- `code_manager/source_registration.py` registers immutable source versions
  through the DATA MANAGER public API.
- `code_manager/source_registry.py` performs owner-scoped metadata lookup
  and verifies stored ZIP bytes.
- `code_manager/data_manager_client.py` is a replaceable JSON HTTP client.
- `code_manager/api.py` provides a framework-independent WSGI API.
- `code_manager/build_pipeline.py` provides deterministic packaging, durable owner-scoped build history, and test execution in a pinned, network-disabled Docker image.

## API

The application is created through `create_application(...)`. The caller
must inject:

- `blob_storage`: a CODE MANAGER-owned `BlobStorage` instance.
- `data_manager_client_factory(owner_id)`: a factory returning a DATA MANAGER
  client authorized for that exact owner.
- `identity_provider`: a replaceable object implementing `resolve(environ)`.

The authenticated owner comes from trusted WSGI `REMOTE_USER`. The optional
`X-Code-Manager-ID` development header is disabled unless
`CODE_MANAGER_ALLOW_INSECURE_HEADER=1` is explicitly set.

The development DATA MANAGER client factory is restricted to loopback URLs
and requires both `CODE_MANAGER_ALLOW_INSECURE_HEADER=1` and
`DATA_MANAGER_ALLOW_INSECURE_HEADER=1`. Never enable these options in
production.

A production adapter must integrate with a trusted identity gateway and
ensure that DATA MANAGER authorizes the same owner. A client bearer token
does not, by itself, populate `REMOTE_USER`.

## Current endpoints

- `POST /api/v1/sources`: register a source ZIP using `source_content_base64`.
- `GET /api/v1/sources`: list the authenticated owner's source versions.
- `GET /api/v1/sources/{source_id}/versions/{source_version}`: retrieve metadata.
- `POST /api/v1/sources/{source_id}/versions/{source_version}/inspect`:
  validate archive structure without executing the source.
- `POST /api/v1/builds`: runs static preflight, deterministic normalization, and source tests inside a digest-pinned Docker image; records every stage and remains blocked unless all mandatory stages pass.
- `GET /api/v1/builds`: lists durable, owner-scoped build reports; supports `?limit=1..100`.
- `GET /api/v1/builds/{build_id}`: retrieves an owner-scoped immutable build report.
- `POST /api/v1/artifacts/{artifact_id}/publish`: requires a successful `build_id`, verifies every stage, the stored artifact digest and provenance, then immutably publishes a `built_artifact`.
- `GET /api/v1/artifacts/{artifact_id}/content`: returns byte-exact content only for a published `built_artifact`; source ZIP manifests are not downloadable through this endpoint.

Successful and error responses use the shared contract version and may preserve
a valid `X-Correlation-ID`. Errors do not expose stack traces or secrets.
Requests have a configurable size limit in the application factory.

## Integration test

The real DATA MANAGER integration test is skipped by default. To run it,
start a local development DATA MANAGER and explicitly enable its development
identity header, then set `CODE_MANAGER_INTEGRATION=1`. The test refuses
non-loopback DATA MANAGER URLs. Never enable development identity headers
in production.

## Security and lifecycle

ZIP inspection is validation, not a guarantee that source code is safe to run. Submitted source code is never executed in the privileged API process. Source tests run in a separate Docker container with no network, read-only root, non-root UID/GID, dropped capabilities, no-new-privileges, bounded CPU/memory/PIDs/tmpfs, read-only source mounts, and a wall-clock/output limit. The configured image must be pinned by digest or immutable image ID and already available locally.

The dependency profile is fail-closed and offline. Standard-library/archive-local imports work without extra configuration. External imports are allowed only when a root `requirements.txt` uses exact `package==version --hash=sha256:<digest>` pins matching the trusted `CODE_MANAGER_DEPENDENCY_ALLOWLIST` JSON and the wheel bytes in `CODE_MANAGER_DEPENDENCY_WHEELHOUSE`. The allowlist entry contains `version`, `sha256`, `wheel`, and `modules`. Only small pure-Python `py3-none-any` wheels with unconditional exact-version `Requires-Dist` pins are supported. Every transitive dependency must also appear in the root requirements file and match the trusted allowlist and wheelhouse. Native extensions, environment markers, extras, `.pth` files and standard-library shadowing remain unsupported. Selected wheel files are mounted read-only for isolated tests, then vendored into the deterministic artifact with `vendor/dependencies.json`; Worker Runtime re-verifies their hashes before import. No package manager runs and no network access is available. Other manifests, dynamic imports, credential-like files, and missing test suites block publication. Tests use Python `unittest` discovery and the declared entrypoint is imported and checked for callability inside the sandbox. The produced ZIP excludes tests and caches and is stored by SHA-256. Publication requires a durable successful build report; downloads serve only `built_artifact`, never a registered source ZIP.

Configure `CODE_MANAGER_BUILD_SANDBOX_IMAGE` to a locally available immutable image ID (`sha256:...`) or registry digest. Docker is launched with `--pull=never`, so deployment must provision the image ahead of time. Set `CODE_MANAGER_DEPENDENCY_ALLOWLIST` to trusted JSON and `CODE_MANAGER_DEPENDENCY_WHEELHOUSE` to a read-only, trusted wheel directory when dependencies are required. The image must provide the Python interpreter compatible with the worker source. The Docker daemon must be dedicated to this service and preferably rootless; never expose the Docker socket to submitted code, mount host credentials, or use writable host mounts. Worker Runtime independently requires `WORKER_RUNTIME_SANDBOX_IMAGE`.

This is an initial container boundary, not production certification. Use a trusted dedicated, preferably rootless Docker daemon; do not mount the Docker socket, host credentials or writable host directories.


## Artifact download boundary

The download API verifies the immutable built-artifact manifest, source hash, build provenance and content-addressed blob. A registered source ZIP is not a built artifact and cannot pass the public download route. Worker Runtime remains fail-closed unless its own sandbox is configured. Production identity middleware must validate the Authorization header and set trusted `REMOTE_USER`; this WSGI module does not parse bearer tokens itself.
