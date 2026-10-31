#!/usr/bin/env bash
# Independent installation. Does not edit/restart 30nA, Nginx or Docker services.
set -Eeuo pipefail
umask 077
[[ $EUID == 0 && $# == 1 ]] || { echo 'Usage: sudo bash install.sh DASHBOARD_HOSTNAME_OR_IP' >&2; exit 1; }
RB_HOSTNAME=$1
[[ $RB_HOSTNAME =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]{0,252}$ ]] || { echo 'Invalid hostname' >&2; exit 1; }
[[ $(uname -m) == x86_64 ]] || { echo 'This reviewed image pin supports x86_64 only.' >&2; exit 1; }
RB_SOURCE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
RB_BASE=/opt/independent-browser
RB_CONFIG=/etc/independent-browser
for path in "$RB_BASE" "$RB_BASE/app" "$RB_BASE/.venv" "$RB_CONFIG" "$RB_CONFIG/config.json" "$RB_CONFIG/cert.pem" "$RB_CONFIG/key.pem"; do [[ ! -L $path ]] || { echo 'Refusing symlink install path' >&2; exit 1; }; done
for path in "$RB_BASE" "$RB_CONFIG"; do
    [[ ! -e $path || -f $path/.independent-browser-managed ]] || { echo "Refusing unowned install directory: $path" >&2; exit 1; }
done
for path in /etc/systemd/system/independent-browser.service /etc/systemd/system/independent-browser.socket; do
    [[ ! -L $path ]] || { echo 'Refusing symlink unit' >&2; exit 1; }
    [[ ! -e $path ]] || grep -Fxq '# independent-browser managed unit v1' "$path" || { echo 'Refusing unowned unit' >&2; exit 1; }
done
command -v docker >/dev/null
docker buildx version >/dev/null
command -v openssl >/dev/null
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"'
docker --host=unix:///var/run/docker.sock info >/dev/null
RB_DOCKER_MAJOR=$(docker --host=unix:///var/run/docker.sock version --format '{{.Server.Version}}' | cut -d. -f1)
(( RB_DOCKER_MAJOR >= 28 )) || { echo 'Docker 28+ required for isolated internal networks; daemon was not changed.' >&2; exit 1; }
exec 9>/run/lock/independent-browser-install.lock
flock -n 9
install -d -m 0755 "$RB_BASE/app"
install -d -m 0700 "$RB_CONFIG"
printf 'independent-browser managed v1\n' >"$RB_BASE/.independent-browser-managed"
printf 'independent-browser managed v1\n' >"$RB_CONFIG/.independent-browser-managed"
for file in server.py ui.py runtime.py transport.py egress.py configure.py requirements.lock images.json; do install -m 0644 "$RB_SOURCE/$file" "$RB_BASE/app/$file"; done
[[ -x $RB_BASE/.venv/bin/python ]] || python3 -m venv "$RB_BASE/.venv"
"$RB_BASE/.venv/bin/python" -m pip install --require-hashes -r "$RB_BASE/app/requirements.lock"
RB_BROWSER_IMAGE=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["browser_image"])' "$RB_SOURCE/images.json")
docker --host=unix:///var/run/docker.sock pull "$RB_BROWSER_IMAGE"
docker --host=unix:///var/run/docker.sock build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt --tag independent-browser-egress:local "$RB_SOURCE"
RB_EGRESS_IMAGE=$(docker --host=unix:///var/run/docker.sock image inspect --format '{{.Id}}' independent-browser-egress:local)
if [[ ! -f $RB_CONFIG/cert.pem || ! -f $RB_CONFIG/key.pem ]]; then
    RB_SAN=$(python3 -c 'import ipaddress,sys
try: print("IP:"+str(ipaddress.ip_address(sys.argv[1])))
except ValueError: print("DNS:"+sys.argv[1])' "$RB_HOSTNAME")
    openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj "/CN=$RB_HOSTNAME" -addext "subjectAltName=$RB_SAN" -keyout "$RB_CONFIG/key.pem" -out "$RB_CONFIG/cert.pem" 2>/dev/null
    chmod 600 "$RB_CONFIG/key.pem" "$RB_CONFIG/cert.pem"
fi
"$RB_BASE/.venv/bin/python" "$RB_BASE/app/configure.py" --config "$RB_CONFIG/config.json" --hostname "$RB_HOSTNAME" --browser-image "$RB_BROWSER_IMAGE" --egress-image "$RB_EGRESS_IMAGE" --cert "$RB_CONFIG/cert.pem" --key "$RB_CONFIG/key.pem"
cat >/etc/systemd/system/independent-browser.service <<'UNIT'
# independent-browser managed unit v1
[Unit]
Description=Independent disposable remote browser
After=network-online.target
Requires=independent-browser.socket
[Service]
Type=simple
User=root
WorkingDirectory=/opt/independent-browser/app
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=DOCKER_CONFIG=/run/independent-browser/docker-client
ExecStartPre=/usr/bin/mkdir -p /run/independent-browser/docker-client
ExecStart=/opt/independent-browser/.venv/bin/python /opt/independent-browser/app/server.py --config /etc/independent-browser/config.json
Restart=on-failure
RestartSec=10
RuntimeDirectory=independent-browser
RuntimeDirectoryMode=0700
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
MemoryMax=192M
CPUQuota=50%
TasksMax=128
UMask=0077
UNIT
cat >/etc/systemd/system/independent-browser.socket <<'UNIT'
# independent-browser managed unit v1
[Unit]
Description=Independent browser HTTPS activation socket
[Socket]
ListenStream=0.0.0.0:9443
Accept=no
NoDelay=true
[Install]
WantedBy=sockets.target
UNIT
systemctl daemon-reload
systemctl stop independent-browser.service
systemctl enable --now independent-browser.socket
echo "Remote Browser: https://$RB_HOSTNAME:9443/rb/"
echo 'Users: 1-9. Password configured privately. Self-signed TLS; install a trusted certificate for normal browser trust.'
echo 'Allow TCP 9443 in the VPS firewall/provider panel if needed. Dashboard/Nginx/Docker services were not restarted.'
