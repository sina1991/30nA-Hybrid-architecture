#!/usr/bin/env bash
# Ubuntu 24.04 installer. Run as root on a dedicated, fresh VPS.
set -Eeuo pipefail
umask 077
REPOSITORY=https://github.com/sina1991/30nA-Hybrid-architecture.git
REF=main
DOMAIN='' EMAIL='' CHECK_ONLY=0 NONINTERACTIVE=0
CONFIG=/etc/30na
say() { printf '\n%s\n' "$*"; }
die() { say "Error: $*" >&2; exit 1; }
usage() {
    cat <<'HELP'
Install 30nA on a fresh Ubuntu 24.04 VPS (as root)
install.sh [--domain dashboard.example.com] [--email admin@example.com]
           [--ref Git-ref] [--non-interactive] [--check-only]
The domain must point to this VPS, and TCP ports 80/443 must be reachable.
Public HTTPS and certificate renewal use Let's Encrypt and Certbot.
--check-only checks prerequisites without changing the system.
Rerun with the same settings to resume an incomplete installation.
HELP
}
parse() {
    while (($#)); do
        case "$1" in
            --domain|--email|--ref)
                (($# >= 2)) || die "A value is required for $1"
                case "$1" in --domain) DOMAIN=$2;; --email) EMAIL=$2;; --ref) REF=$2;; esac
                shift 2;;
            --non-interactive) NONINTERACTIVE=1; shift;;
            --check-only) CHECK_ONLY=1; shift;;
            --help|-h) usage; exit 0;;
            *) die "Unknown option: $1";;
        esac
    done
}
ask() {
    local answer
    [[ -r /dev/tty && $NONINTERACTIVE == 0 ]] || die "Provide $1 as an argument"
    printf '%s: ' "$2" >/dev/tty
    read -r answer </dev/tty
    printf -v "$1" '%s' "$answer"
}
clean_input() {
    # Strip surrounding terminal/paste whitespace and Unicode direction wrappers.
    # Do not remove or rewrite characters inside an address.
    python3 - "$1" <<'PYTHON'
import sys
value=sys.argv[1]
wrappers='\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069\ufeff'
while True:
    cleaned=value.strip().strip(wrappers).strip()
    if cleaned==value:break
    value=cleaned
print(value)
PYTHON
}
validate() {
    python3 - "$DOMAIN" "$EMAIL" "$REF" <<'PY'
import ipaddress,re,sys
name,email,ref=sys.argv[1:]
try:ipaddress.ip_address(name);raise SystemExit('Use a domain or subdomain, not a bare IP address.')
except ValueError:pass
if len(name)>253 or '.' not in name or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',part) for part in name.split('.')):
    raise SystemExit('A valid lowercase domain without https:// or a path is required.')
if not re.fullmatch(r'[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',email):raise SystemExit('A valid email is required; enter it without spaces or use --email.')
if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,199}',ref) or '..' in ref:raise SystemExit('Invalid Git ref.')
PY
}
as_sandbox() {
    runuser -u 30na-sandbox -- env XDG_RUNTIME_DIR="/run/user/$SANDBOX_UID" \
        DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$SANDBOX_UID/bus" \
        DOCKER_HOST="unix:///run/user/$SANDBOX_UID/docker.sock" "$@"
}
preflight() {
    [[ $EUID == 0 ]] || die 'Run sudo -i first; the installer requires root.'
    [[ -f /etc/os-release ]] || die 'Ubuntu 24.04 is required'
    # shellcheck disable=SC1091
    . /etc/os-release
    [[ $ID == ubuntu && $VERSION_ID == 24.04 ]] || die 'Only Ubuntu 24.04 LTS is supported'
    [[ -d /run/systemd/system ]] || die 'An active systemd is required; do not run the installer in an ordinary container'
    command -v python3 >/dev/null || die 'First run apt-get update && apt-get install -y python3 curl'
    if [[ -f $CONFIG/installer.json ]]; then
        python3 - "$DOMAIN" "$EMAIL" "$REF" <<'PY'
import json,sys
s=json.load(open('/etc/30na/installer.json'))
if s != dict(version=1,domain=sys.argv[1],email=sys.argv[2],ref=sys.argv[3]):
    raise SystemExit('Settings differ from the previous installation; automatic upgrade or domain change is unsupported.')
PY
    else
        for target in /etc/30na /opt/30na /var/lib/30na /var/lib/30na-sandbox /etc/nginx /etc/docker /var/lib/docker /etc/letsencrypt /etc/apt/sources.list.d/30na-docker.list /etc/apt/keyrings/30na-docker.asc /etc/apparmor.d/30na-rootlesskit /etc/systemd/system/30na-dashboard.service /etc/systemd/system/30na-code-manager.service /etc/systemd/system/30na-worker-manager.service /etc/systemd/system/30na-worker-runtime.service /usr/local/bin/30na; do
            [[ ! -e $target ]] || die "Path already exists: $target; a fresh server is required"
        done
        for account in 30na 30na-sandbox; do
            ! id "$account" &>/dev/null || die "Account $account already exists"
        done
        ! command -v docker >/dev/null || die 'Docker already exists; automatic installation requires a fresh VPS'
        python3 - <<'PY'
import socket
for port in (80,443,8020,8099,8101,8102,18443,18444,18445,18446):
    with socket.socket() as s:
        try:s.bind(('0.0.0.0',port))
        except OSError:raise SystemExit(f'Port {port} is in use; installation stopped.')
PY
    fi
    python3 - "$DOMAIN" <<'PY'
import socket,sys
try:socket.getaddrinfo(sys.argv[1],80,type=socket.SOCK_STREAM)
except socket.gaierror:raise SystemExit('Domain DNS does not resolve; configure A/AAAA records first.')
PY
}
packages() {
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y ca-certificates curl git openssl python3-venv python3-pip nginx certbot \
        uidmap dbus-user-session slirp4netns apparmor
    install -d -m 0755 /etc/apt/keyrings
    curl -fsSL --proto '=https' https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/30na-docker.asc
    chmod 0644 /etc/apt/keyrings/30na-docker.asc
    printf 'deb [arch=%s signed-by=/etc/apt/keyrings/30na-docker.asc] https://download.docker.com/linux/ubuntu noble stable\n' \
        "$(dpkg --print-architecture)" >/etc/apt/sources.list.d/30na-docker.list
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-ce-rootless-extras
    # This installer owns this fresh host's Docker installation. Only rootless is used.
    systemctl disable --now docker.service docker.socket
}
checkout() {
    install -d -m 0755 /opt/30na/releases
    if [[ ! -f $CONFIG/release ]]; then
        local temporary sha
        temporary=$(mktemp -d /opt/30na/releases/checkout.XXXXXXXX)
        (umask 022; git clone --quiet --no-checkout "$REPOSITORY" "$temporary")
        git -C "$temporary" fetch --quiet origin "$REF"
        sha=$(git -C "$temporary" rev-parse 'FETCH_HEAD^{commit}')
        git -C "$temporary" checkout --quiet --detach "$sha"
        chmod -R a+rX "$temporary"
        mv "$temporary" "/opt/30na/releases/$sha"
        printf '%s\n' "$sha" >"$CONFIG/release"
    fi
    RELEASE=$(cat "$CONFIG/release")
    [[ $RELEASE =~ ^[0-9a-f]{40}$ ]] || die 'Invalid release marker'
    APP="/opt/30na/releases/$RELEASE"
    [[ -f $APP/scripts/deployment/provision.py ]] || die 'The selected version lacks the complete installer'
    ln -sfn "$APP" /opt/30na/current
    (umask 022; cd "$APP"; bash scripts/deployment/prepare.sh)
}
accounts_and_docker() {
    id 30na &>/dev/null || useradd --system --user-group --no-create-home --shell /usr/sbin/nologin 30na
    id 30na-sandbox &>/dev/null || useradd --create-home --user-group --home-dir /var/lib/30na-sandbox --shell /bin/bash 30na-sandbox
    SANDBOX_UID=$(id -u 30na-sandbox)
    loginctl enable-linger 30na-sandbox
    systemctl start "user@$SANDBOX_UID.service"
    # Ubuntu 24.04 restricts unprivileged user namespaces. Grant only rootlesskit.
    if aa-enabled --quiet; then
        cat >/etc/apparmor.d/30na-rootlesskit <<'PROFILE'
abi <abi/4.0>,
include <tunables/global>
/usr/bin/rootlesskit flags=(unconfined) {
  userns,
  include if exists <local/30na-rootlesskit>
}
PROFILE
        apparmor_parser -r /etc/apparmor.d/30na-rootlesskit
    fi
    if ! as_sandbox systemctl --user is-active --quiet docker; then
        as_sandbox dockerd-rootless-setuptool.sh install
    fi
    as_sandbox systemctl --user enable --now docker
    local information
    information=$(as_sandbox docker info --format '{{json .SecurityOptions}} {{.CgroupDriver}}')
    [[ $information == *rootless* && $information == *systemd* ]] || die 'Rootless Docker with the systemd cgroup driver is required'
    # Reuse this install's immutable image after an interrupted run.
    if [[ ! -f $CONFIG/image ]]; then
        as_sandbox docker build -t 30na-sandbox -f "$APP/units/worker-runtime/tests/sandbox-image/Dockerfile" "$APP"
        as_sandbox docker image inspect --format '{{.Id}}' 30na-sandbox >"$CONFIG/image"
    fi
    IMAGE=$(cat "$CONFIG/image")
    [[ $IMAGE =~ ^sha256:[0-9a-f]{64}$ ]] || die 'Invalid image marker'
    as_sandbox docker image inspect "$IMAGE" >/dev/null
}
obtain_certificate() {
    # Standalone must own port 80. Restore our Nginx even if ACME fails.
    systemctl stop nginx
    local certificate_status=0
    certbot certonly --non-interactive --agree-tos --email "$EMAIL" --standalone --preferred-challenges http \
        --domain "$DOMAIN" --cert-name 30na-dashboard --keep-until-expiring || certificate_status=$?
    systemctl start nginx
    [[ $certificate_status == 0 ]] || return "$certificate_status"
}
certificates() {
    install -d -m 0755 "$CONFIG/ca" /var/lib/30na/acme
    if [[ ! -f $CONFIG/ca/internal.crt ]]; then
        openssl req -x509 -newkey rsa:3072 -sha256 -nodes -days 3650 \
            -subj '/CN=30nA local service CA' -addext 'subjectAltName=DNS:localhost,IP:127.0.0.1' \
            -addext 'basicConstraints=critical,CA:TRUE' \
            -keyout "$CONFIG/ca/internal.key" -out "$CONFIG/ca/internal.crt" 2>/dev/null
    fi
    openssl x509 -checkend 86400 -noout -in "$CONFIG/ca/internal.crt" >/dev/null || die 'The internal certificate is expired or invalid; consult the TLS runbook'
    cat /etc/ssl/certs/ca-certificates.crt "$CONFIG/ca/internal.crt" >"$CONFIG/ca/trust.pem"
    chmod 0644 "$CONFIG/ca/internal.crt" "$CONFIG/ca/trust.pem"
    local public_tls=()
    [[ ! -f /etc/letsencrypt/live/30na-dashboard/fullchain.pem ]] || public_tls=(--public-tls)
    "$APP/.venv/bin/python" "$APP/scripts/deployment/provision.py" --domain "$DOMAIN" --image "$IMAGE" --sandbox-uid "$SANDBOX_UID" "${public_tls[@]}"
    # Remove only the untouched distro default created by this installation.
    if [[ -L /etc/nginx/sites-enabled/default && $(readlink /etc/nginx/sites-enabled/default) == /etc/nginx/sites-available/default ]]; then
        rm /etc/nginx/sites-enabled/default
    fi
    ln -sfn /etc/nginx/sites-available/30na /etc/nginx/sites-enabled/30na
    nginx -t
    systemctl enable --now nginx
    systemctl reload nginx
    if command -v ufw >/dev/null && ufw status | grep -q '^Status: active'; then
        ufw allow 80/tcp
        ufw allow 443/tcp
    fi
    say 'Obtaining the public certificate; DNS must point to this VPS and the cloud firewall must allow TCP 80/443.'
    obtain_certificate
    "$APP/.venv/bin/python" "$APP/scripts/deployment/provision.py" --domain "$DOMAIN" --image "$IMAGE" --sandbox-uid "$SANDBOX_UID" --public-tls
    install -d -m 0755 /etc/letsencrypt/renewal-hooks/{pre,post,deploy}
    # Older webroot certificates retain their stored renewal method until reconfigured.
    if grep -Eq '^authenticator[[:space:]]*=[[:space:]]*standalone[[:space:]]*$' /etc/letsencrypt/renewal/30na-dashboard.conf; then
        printf '#!/bin/sh\nset -eu\n/bin/systemctl stop nginx\n' >/etc/letsencrypt/renewal-hooks/pre/30na-nginx
        printf '#!/bin/sh\nset -eu\n/usr/sbin/nginx -t\n/bin/systemctl start nginx\n' >/etc/letsencrypt/renewal-hooks/post/30na-nginx
        chmod 0755 /etc/letsencrypt/renewal-hooks/{pre,post}/30na-nginx
    fi
    printf '#!/bin/sh\nset -eu\n/usr/sbin/nginx -t\nif /bin/systemctl is-active --quiet nginx; then /bin/systemctl reload nginx; fi\n' >/etc/letsencrypt/renewal-hooks/deploy/30na-nginx
    chmod 0755 /etc/letsencrypt/renewal-hooks/deploy/30na-nginx
    systemctl enable --now certbot.timer
    nginx -t
    systemctl reload nginx
}
start_and_verify() {
    install -m 0755 "$APP/deployment/30na-review" /usr/local/sbin/30na-review
    if [[ -e /usr/local/bin/30na ]] && ! grep -Fxq "# 30na managed CLI launcher v1" /usr/local/bin/30na; then
        die "The /usr/local/bin/30na command belongs to another installation"
    fi
    install -m 0755 "$APP/deployment/30na-cli" /usr/local/bin/30na
    install -m 0644 "$APP"/deployment/systemd/30na-*.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable --now 30na-code-manager 30na-worker-runtime 30na-worker-manager 30na-dashboard
    local ready=0
    for ((attempt=0; attempt<60; attempt++)); do
        if curl -fsS --cacert "$CONFIG/ca/trust.pem" https://localhost:18444/health >/dev/null 2>&1 && \
           curl -fsS --cacert "$CONFIG/ca/trust.pem" https://localhost:18445/health >/dev/null 2>&1 && \
           curl -fsS --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN/health" >/dev/null 2>&1; then ready=1; break; fi
        sleep 1
    done
    [[ $ready == 1 ]] || die 'Services did not become ready; check sudo 30na-review status and the relevant journalctl logs'
    SSL_CERT_FILE="$CONFIG/ca/trust.pem" "$APP/.venv/bin/python" "$APP/scripts/deployment/seed_demo.py" \
        --code-url https://localhost:18443 --manager-url https://localhost:18444 \
        --code-token-file "$CONFIG/customer-token" --manager-token-file "$CONFIG/customer-token" >"$CONFIG/demo.json"
    SSL_CERT_FILE="$CONFIG/ca/trust.pem" "$APP/.venv/bin/python" "$APP/scripts/deployment/verify_install.py"
    printf '%s\n' "$RELEASE" >"$CONFIG/installed-release"
    say "Installation and demo execution succeeded. Dashboard URL: https://$DOMAIN"
    say 'Sign in with the installation token in /etc/30na/customer-token (root only). Keep it out of chat and Git.'
    say 'Certificate renewal: certbot.timer is active. Check renewal with certbot renew --dry-run.'
}
main() {
    parse "$@"
    command -v python3 >/dev/null || die 'Install Python 3 and curl first'
    [[ -n $DOMAIN ]] || ask DOMAIN 'Dashboard domain, e.g. dashboard.example.com'
    [[ -n $EMAIL ]] || ask EMAIL "Email for Let's Encrypt"
    DOMAIN=$(clean_input "$DOMAIN")
    EMAIL=$(clean_input "$EMAIL")
    validate
    if [[ $CHECK_ONLY == 0 ]]; then
        [[ $EUID == 0 ]] || die 'Run sudo -i first'
        exec 9>/run/lock/30na-install.lock
        flock -n 9 || die 'Another installer is running'
    fi
    preflight
    say "Domain: $DOMAIN | Requested ref: $REF | Ubuntu 24.04 / Rootless Docker / Nginx / Let's Encrypt"
    [[ $CHECK_ONLY == 0 ]] || { say 'Preflight passed; no system changes were made. Public access and certificates are checked during installation.'; return; }
    install -d -m 0755 "$CONFIG"
    if [[ ! -f $CONFIG/installer.json ]]; then
        python3 - "$DOMAIN" "$EMAIL" "$REF" <<'PY'
import json,sys
with open('/etc/30na/installer.json','x') as f:json.dump(dict(version=1,domain=sys.argv[1],email=sys.argv[2],ref=sys.argv[3]),f)
PY
    fi
    say 'Installing dependencies and Rootless Docker'
    packages
    checkout
    accounts_and_docker
    certificates
    start_and_verify
}
if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
    trap 'printf "\nInstallation stopped (line %s). Resolve the error and rerun the same command.\n" "$LINENO" >&2' ERR
    main "$@"
fi
