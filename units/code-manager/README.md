# CODE MANAGER

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
- `POST /api/v1/builds`: reserved; returns `501` until a validated build pipeline and build isolation exist.
- `GET /api/v1/artifacts/{artifact_id}/content`: returns byte-exact content only for an already-published, owner-scoped artifact; verifies manifest/blob integrity and exposes the SHA-256 digest.
- `POST /api/v1/artifacts/{artifact_id}/publish`: remains reserved and returns `501`; publication is intentionally blocked until build validation exists. Service-level publication of source ZIPs is not equivalent to a validated build.

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

ZIP inspection is validation, not a guarantee that source code is safe to run.
Submitted source code is never executed by the API. Build execution must later
run in a restricted environment, separate from the privileged CODE MANAGER
process. Artifact packaging, immutable artifact versions, and publication
remain unimplemented.


## Artifact download boundary

The download API only reads an artifact that was explicitly published through the local registry and verifies its immutable manifest and content-addressed blob. It does not build, validate dependencies, or make submitted code safe. The publication HTTP route remains disabled. Do not expose the Runtime to untrusted source archives in production: subprocess execution is not a security sandbox. Production identity middleware must validate the Authorization header and set trusted `REMOTE_USER`; this WSGI module does not parse bearer tokens itself.
