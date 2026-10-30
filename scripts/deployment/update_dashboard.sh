#!/usr/bin/env bash
# Update only Dashboard on an installer-owned VPS; leave backend units/state alone.
set -Eeuo pipefail
umask 077
REF=${1:-main}
[[ $REF =~ ^[a-zA-Z0-9][a-zA-Z0-9._/-]*$ && $REF != *..* ]] || { echo 'Invalid Git ref' >&2; exit 1; }
[[ $EUID == 0 && -f /etc/30na/installed-release ]] || { echo 'Run as root on an installer-owned VPS.' >&2; exit 1; }
exec 9>/run/lock/30na-install.lock
flock -n 9 || { echo 'Another install/update is active.' >&2; exit 1; }
BASE=/opt/30na
LINK=$BASE/dashboard-current
DROPIN=/etc/systemd/system/30na-dashboard.service.d/99-30na-release.conf
[[ ! -e $LINK || -L $LINK ]] || { echo 'Dashboard path is not a managed symlink.' >&2; exit 1; }
[[ ! -e $DROPIN || -f /etc/30na/dashboard-release ]] || { echo 'Existing unowned Dashboard override; review it before updating.' >&2; exit 1; }
BACKUP=$(mktemp -d /tmp/30na-dashboard-update.XXXXXXXX)
HAD_LINK=0 HAD_DROPIN=0 HAD_CLI=0 CHANGED=0
CLI_LAUNCHER=/usr/local/bin/30na
if [[ -e $CLI_LAUNCHER ]]; then
    grep -Fxq "# 30na managed CLI launcher v1" "$CLI_LAUNCHER" || { echo "Existing unowned 30na command; review before updating." >&2; exit 1; }
    HAD_CLI=1; cp "$CLI_LAUNCHER" "$BACKUP/cli"
fi
if [[ -L $LINK ]]; then HAD_LINK=1; readlink "$LINK" >"$BACKUP/link"; fi
if [[ -f $DROPIN ]]; then HAD_DROPIN=1; cp "$DROPIN" "$BACKUP/dropin"; fi
rollback() {
    trap - ERR INT TERM
    set +e
    if [[ $CHANGED == 1 ]]; then
        if [[ $HAD_LINK == 1 ]]; then ln -sfn "$(cat "$BACKUP/link")" "$LINK"; else rm -f "$LINK"; fi
        if [[ $HAD_DROPIN == 1 ]]; then cp "$BACKUP/dropin" "$DROPIN"; else rm -f "$DROPIN"; fi
        if [[ $HAD_CLI == 1 ]]; then install -m 0755 "$BACKUP/cli" "$CLI_LAUNCHER"; else rm -f "$CLI_LAUNCHER"; fi
        systemctl daemon-reload
        systemctl restart 30na-dashboard
        echo 'Update failed; previous Dashboard configuration restored. Check 30na-review status.' >&2
    fi
    rm -rf "$BACKUP"
    exit 1
}
trap rollback ERR INT TERM
TEMPORARY=$(mktemp -d "$BASE/releases/dashboard.XXXXXXXX")
(umask 022; git clone --quiet --no-checkout https://github.com/sina1991/30nA-Hybrid-architecture.git "$TEMPORARY")
git -C "$TEMPORARY" fetch --quiet origin "$REF"
SHA=$(git -C "$TEMPORARY" rev-parse 'FETCH_HEAD^{commit}')
git -C "$TEMPORARY" checkout --quiet --detach "$SHA"
chmod -R a+rX "$TEMPORARY"
# Use a separate release directory even if a backend checkout has the same SHA.
RELEASE=$BASE/releases/dashboard-$SHA
if [[ -e $RELEASE ]]; then
    [[ $(git -C "$RELEASE" rev-parse HEAD) == "$SHA" && -z $(git -C "$RELEASE" status --porcelain) ]]
    rm -rf "$TEMPORARY"
else
    mv -T "$TEMPORARY" "$RELEASE"
fi
(umask 022; cd "$RELEASE"; bash scripts/deployment/prepare.sh)
STATE_DIR=/var/lib/30na/dashboard
if [[ -L $STATE_DIR ]]; then echo 'Dashboard state path must not be a symlink.' >&2; exit 1; fi
if [[ ! -e $STATE_DIR ]]; then
    install -d -m 0700 -o 30na -g 30na "$STATE_DIR"
else
    [[ -d $STATE_DIR && $(stat -c %u "$STATE_DIR") == "$(id -u 30na)" ]] || { echo 'Existing Dashboard state is not owned by 30na.' >&2; exit 1; }
    mode=$(stat -c %a "$STATE_DIR")
    (( (8#$mode & 077) == 0 )) || { echo 'Dashboard state directory must be private.' >&2; exit 1; }
fi
install -d -m 0755 "$(dirname "$DROPIN")"
CHANGED=1
ln -sfn "$RELEASE" "$LINK"
cat >"$DROPIN" <<'UNIT'
[Service]
ReadWritePaths=/var/lib/30na/dashboard
WorkingDirectory=/opt/30na/dashboard-current/units/consumers/dashboard-core
Environment=PYTHONPATH=/opt/30na/dashboard-current:/opt/30na/dashboard-current/units/worker-manager:/opt/30na/dashboard-current/units/consumers/dashboard-core
ExecStart=
ExecStart=/opt/30na/dashboard-current/.venv/bin/python -m uvicorn dashboard.production:create_app --factory --workers 1 --host 127.0.0.1 --port 8020 --no-access-log --no-proxy-headers --limit-concurrency 64 --timeout-keep-alive 5
UNIT
chmod 0644 "$DROPIN"
systemctl daemon-reload
systemctl restart 30na-dashboard
READY=0
for ((attempt=0;attempt<30;attempt++)); do
    if curl -fsS --cacert /etc/30na/ca/trust.pem https://localhost:18446/health >/dev/null 2>&1 && \
       curl -fsS --cacert /etc/30na/ca/trust.pem https://localhost:18446/ | grep -F 'worker-management' >/dev/null; then READY=1; break; fi
    sleep 1
done
[[ $READY == 1 ]]
install -m 0755 "$RELEASE/deployment/30na-cli" "$CLI_LAUNCHER"
printf '%s\n' "$SHA" >/etc/30na/dashboard-release
CHANGED=0
trap - ERR INT TERM
rm -rf "$BACKUP"
printf 'Dashboard updated to %s. Refresh your browser. Token and backend state are unchanged.\n' "$SHA"
