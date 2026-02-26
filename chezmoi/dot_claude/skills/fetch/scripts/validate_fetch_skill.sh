#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SKILL_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
SOURCE_DIR="$(CDPATH= cd -- "$SKILL_DIR/../../.." && pwd)"
TEMPLATE_PATH="$SKILL_DIR/scripts/fetch_url.py.tmpl"
LOCK_PATH="$SKILL_DIR/uv.lock"

REMOVE_LOCK_ON_EXIT=0
if [[ ! -f "$LOCK_PATH" ]]; then
  REMOVE_LOCK_ON_EXIT=1
fi

cleanup() {
  if [[ "$REMOVE_LOCK_ON_EXIT" -eq 1 && -f "$LOCK_PATH" ]]; then
    rm -f "$LOCK_PATH"
  fi
}
trap cleanup EXIT

if [[ ! -f "$TEMPLATE_PATH" ]]; then
  echo "error: expected template not found at $TEMPLATE_PATH" >&2
  exit 1
fi

WORK_HOST="${WORK_HOST:-okzf68}"
HOME_HOST="${HOME_HOST:-home-host}"
HOME_DIR="${HOME_DIR:-/Users/asimi}"
WORK_URL="${WORK_URL:-https://example.com}"
HOME_URL="${HOME_URL:-https://example.com}"

TMP_WORK="/tmp/fetch-okzf68.py"
TMP_HOME="/tmp/fetch-home.py"
TMP_WORK_JSON="/tmp/fetch-okzf68.json"
TMP_HOME_JSON="/tmp/fetch-home.json"

echo "== render template variants =="
chezmoi -S "$SOURCE_DIR" execute-template \
  --file "$TEMPLATE_PATH" \
  --override-data "{\"chezmoi\":{\"hostname\":\"$WORK_HOST\",\"homeDir\":\"$HOME_DIR\"}}" \
  > "$TMP_WORK"

chezmoi -S "$SOURCE_DIR" execute-template \
  --file "$TEMPLATE_PATH" \
  --override-data "{\"chezmoi\":{\"hostname\":\"$HOME_HOST\",\"homeDir\":\"$HOME_DIR\"}}" \
  > "$TMP_HOME"

echo "== syntax check rendered files =="
python3 -m py_compile "$TMP_WORK" "$TMP_HOME"

echo "== assert rendered TLS constants =="
rg -n "^EXTRA_CA_CERT = \"$HOME_DIR/.config/certs/node-extra-ca.pem\"\$" "$TMP_WORK" >/dev/null
rg -n '^EXTRA_CA_CERT = None$' "$TMP_HOME" >/dev/null

echo "== runtime checks (uv-managed deps) =="
set +e
uv run --project "$SKILL_DIR" python "$TMP_WORK" --url "$WORK_URL" --timeout 10 > "$TMP_WORK_JSON"
work_exit=$?
uv run --project "$SKILL_DIR" python "$TMP_HOME" --url "$HOME_URL" --timeout 10 > "$TMP_HOME_JSON"
home_exit=$?
set -e

echo "== assert JSON diagnostics =="
python3 - "$TMP_WORK_JSON" "$TMP_HOME_JSON" "$HOME_DIR" "$work_exit" "$home_exit" <<'PY'
import json
import sys

work_path, home_path, home_dir, work_exit, home_exit = sys.argv[1:]
work_exit = int(work_exit)
home_exit = int(home_exit)

work = json.load(open(work_path, encoding="utf-8"))
home = json.load(open(home_path, encoding="utf-8"))

assert work["tls_extra_ca_configured"] is True
assert work["tls_extra_ca_path"] == f"{home_dir}/.config/certs/node-extra-ca.pem"
if work_exit == 0:
    assert work["ok"] is True
else:
    assert work["ok"] is False
    assert "error" in work and work["error"]

assert home["tls_extra_ca_configured"] is False
assert home["tls_extra_ca_loaded"] is False
assert home["tls_extra_ca_path"] is None
if home_exit == 0:
    assert home["ok"] is True
else:
    assert home["ok"] is False
    assert "error" in home and home["error"]

print("diagnostics checks passed")
PY

echo "== validate skill metadata =="
python3 "$SKILL_DIR/../skill-creator/scripts/quick_validate.py" "$SKILL_DIR"

echo "== complete =="
echo "work_exit=$work_exit home_exit=$home_exit"
echo "output: $TMP_WORK_JSON $TMP_HOME_JSON"
