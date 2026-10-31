> Historical Stage B checklist. For the current multi-service Release candidate,
> use [Ubuntu deployment](../../../docs/deployment/ubuntu.md) and the templates in
> `deployment/systemd/`. The old wsgiref unit is not the production HTTP entrypoint.

# Agent 09 Stage B — controlled deployment

This patch does not provision or activate operational credentials. Do not start the service until provisioning is completed securely. Do not use development identity flags.

1. Verify that `/home/sina` and all parent directories of the repository are traversable by the dedicated service account without broadening existing permissions; otherwise STOP.
2. Verify no other DATA_MANAGER_DB exists and the proposed database paths are approved. Initializing the WSGI module creates and migrates the SQLite database; never import it before this check.
3. Create dedicated non-login `30na-code-manager` account and persistent directories `/var/lib/30na-code-manager/blobs`, `/var/lib/30na-data-manager`, owned by that account with mode 0700. Never change ownership of existing project or data files.
4. Provision a cryptographically random 32+ byte bearer credential outside Git. Store a JSON mapping of SHA-256 hex digest to a validated owner ID in `/etc/30na-code-manager/credentials.json` (0400, owned by service account); store the bearer token itself separately, readable only by the authorized consumer. Never print it or put it in command arguments or systemd Environment directives. Keep it out of shell history and logs.
5. Recheck port 8099 immediately before start; if occupied STOP. Install the unit file and start only after checking the new credential, source access, and database initialization safety.
6. Test 401 for missing, invalid and revoked tokens; valid-owner access; cross-owner isolation; publish/content byte equality and SHA-256; size limits; loopback-only listener; dashboard and Agent08 health.
7. To revoke: atomically replace the server-side JSON mapping removing the digest; the gateway reloads on every request. Rotate by introducing a second digest and migrating the consumer before revoking the old digest.

Important: `wsgiref` is a minimal single-threaded WSGI server, not a hardened production HTTP server. This deployment is intended for controlled loopback integration only. Review request timeout and resource-exhaustion controls before treating it as a production-grade service.
