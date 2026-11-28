#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

LOADER_PID=""
PIDS=()
cleanup() {
  if [ -n "$LOADER_PID" ] && kill -0 "$LOADER_PID" 2>/dev/null; then
    kill "$LOADER_PID" 2>/dev/null || true
  fi
  for pid in "${PIDS[@]:-}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  rm -f /tmp/.X99-lock
}
trap cleanup EXIT INT TERM

# Install required OS/Python packages if container rootfs was reset
if ! command -v Xvfb >/dev/null 2>&1 || ! command -v websockify >/dev/null 2>&1 || ! command -v pip3 >/dev/null 2>&1 || ! python3 -c "import PyQt5.QtSvg, psutil, requests, packaging, speedtest" >/dev/null 2>&1; then
  echo "Installing SpeedView Python & virtual display dependencies..."
  # Hold port 3000 open immediately with a lightweight loading screen so the dev server health check succeeds
  python3 -u -c '
import http.server, socketserver
HTML = b"<!doctype html><html><head><meta charset=utf-8><meta http-equiv=refresh content=3><title>SpeedView</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0b1220;color:#e2ecff;font-family:Inter,Segoe UI,sans-serif}div{text-align:center}h2{color:#22d3ee;margin-bottom:8px}</style></head><body><div><h2>SpeedView Desktop</h2><p>Preparing Qt5 &amp; display environment...</p></div></body></html>"
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","text/html"); self.send_header("Content-Length",str(len(HTML))); self.end_headers(); self.wfile.write(HTML)
    def log_message(self,*a): pass
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", 3000), H) as s: s.serve_forever()
' >/tmp/loader.log 2>&1 &
  LOADER_PID=$!

  while pgrep -x apt-get >/dev/null 2>&1 || pgrep -x dpkg >/dev/null 2>&1; do
    sleep 1
  done
  if ! command -v Xvfb >/dev/null 2>&1 || ! command -v websockify >/dev/null 2>&1 || ! command -v pip3 >/dev/null 2>&1 || ! python3 -c "import PyQt5.QtSvg, psutil, requests, packaging, speedtest" >/dev/null 2>&1; then
    apt-get update -qq </dev/null
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends -o Dpkg::Options::="--force-confold" \
      python3-pip python3-pyqt5 python3-pyqt5.qtsvg python3-psutil python3-requests \
      python3-packaging speedtest-cli xvfb xauth x11vnc novnc websockify openbox </dev/null
  fi

  if [ -n "$LOADER_PID" ] && kill -0 "$LOADER_PID" 2>/dev/null; then
    kill "$LOADER_PID" 2>/dev/null || true
    wait "$LOADER_PID" 2>/dev/null || true
    LOADER_PID=""
  fi
fi

# Allow pip3 install -r requirements.txt in Debian 12 container environments
if [ ! -f /etc/pip.conf ]; then
  printf "[global]\nbreak-system-packages = true\n" > /etc/pip.conf
fi

# Ensure noVNC default landing page redirects straight to scaled desktop view
if [ -d /usr/share/novnc ]; then
  cat > /usr/share/novnc/index.html <<'EOF'
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta http-equiv="refresh" content="0; url=vnc_lite.html?scale=true" />
    <title>SpeedView Desktop</title>
  </head>
  <body>
    <script>window.location.replace("vnc_lite.html?scale=true");</script>
  </body>
</html>
EOF
fi

# Clean up any orphaned display processes from a prior crash
rm -f /tmp/.X99-lock

export DISPLAY=:99
export XDG_RUNTIME_DIR="/tmp/runtime-root"
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

Xvfb :99 -screen 0 900x700x24 >/tmp/xvfb.log 2>&1 &
PIDS+=($!)
sleep 1

openbox >/tmp/openbox.log 2>&1 &
PIDS+=($!)

x11vnc -display :99 -forever -nopw -shared -rfbport 5900 >/tmp/x11vnc.log 2>&1 &
PIDS+=($!)
sleep 0.5

python3 -u "$APP_DIR/main.py" >/tmp/speedview.log 2>&1 &
PIDS+=($!)

echo "SpeedView dev server streaming DISPLAY=:99 on port 3000 via noVNC..."
websockify --web=/usr/share/novnc 3000 localhost:5900
