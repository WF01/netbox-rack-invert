#!/usr/bin/env bash
set -euo pipefail

NETBOX_ROOT="${NETBOX_ROOT:-/opt/netbox}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REQUIREMENT_FILE="${SCRIPT_DIR}/../requirements/netbox-plugin.txt"
REQUIREMENT_FILE="${REQUIREMENT_FILE:-${DEFAULT_REQUIREMENT_FILE}}"
PYTHON_BIN="${NETBOX_PYTHON:-}"
MANAGE_PY="${NETBOX_MANAGE_PY:-}"
PERSIST_LOCAL_REQUIREMENTS="${PERSIST_LOCAL_REQUIREMENTS:-0}"
LOCAL_REQUIREMENTS_FILE="${NETBOX_LOCAL_REQUIREMENTS:-${NETBOX_ROOT}/local_requirements.txt}"

find_first_existing() {
  for candidate in "$@"; do
    if [[ -n "${candidate}" && -e "${candidate}" ]]; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

if [[ -z "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="$(find_first_existing \
    "${NETBOX_ROOT}/venv/bin/python" \
    "/opt/netbox/venv/bin/python" \
    "/usr/local/netbox/venv/bin/python" \
    "$(command -v python3 2>/dev/null || true)" \
    "$(command -v python 2>/dev/null || true)" \
  )" || true
fi

if [[ -z "${MANAGE_PY}" ]]; then
  MANAGE_PY="$(find_first_existing \
    "${NETBOX_ROOT}/netbox/manage.py" \
    "/opt/netbox/netbox/manage.py" \
    "/usr/local/netbox/netbox/manage.py" \
  )" || true
fi

if [[ ! -f "${REQUIREMENT_FILE}" ]]; then
  echo "Requirement file not found: ${REQUIREMENT_FILE}" >&2
  exit 1
fi

PACKAGE_SPEC="$(grep -Ehv '^\s*($|#)' "${REQUIREMENT_FILE}" | head -n 1)"
if [[ -z "${PACKAGE_SPEC}" ]]; then
  echo "No pip package spec found in ${REQUIREMENT_FILE}" >&2
  exit 1
fi

if [[ -z "${PYTHON_BIN}" || ! -x "${PYTHON_BIN}" ]]; then
  echo "NetBox python executable not found. Set NETBOX_PYTHON explicitly (example: /opt/netbox/venv/bin/python)." >&2
  exit 1
fi

if [[ -z "${MANAGE_PY}" || ! -f "${MANAGE_PY}" ]]; then
  echo "NetBox manage.py not found. Set NETBOX_MANAGE_PY explicitly (example: /opt/netbox/netbox/manage.py)." >&2
  exit 1
fi

if "${PYTHON_BIN}" -m pip --version >/dev/null 2>&1; then
  "${PYTHON_BIN}" -m pip install --upgrade pip
  "${PYTHON_BIN}" -m pip install "${PACKAGE_SPEC}"
elif command -v uv >/dev/null 2>&1; then
  uv pip install --python "${PYTHON_BIN}" "${PACKAGE_SPEC}"
else
  echo "Neither pip nor uv was found for package installation." >&2
  exit 1
fi

if [[ "${PERSIST_LOCAL_REQUIREMENTS}" == "1" || "${PERSIST_LOCAL_REQUIREMENTS}" == "true" ]]; then
  touch "${LOCAL_REQUIREMENTS_FILE}"
  if ! grep -Fxq "${PACKAGE_SPEC}" "${LOCAL_REQUIREMENTS_FILE}"; then
    echo "${PACKAGE_SPEC}" >> "${LOCAL_REQUIREMENTS_FILE}"
    echo "Added plugin requirement to ${LOCAL_REQUIREMENTS_FILE}"
  else
    echo "Plugin requirement already present in ${LOCAL_REQUIREMENTS_FILE}"
  fi
fi

echo
echo "Package installed successfully."
echo
echo "Next steps:"
echo "1) Ensure ${NETBOX_ROOT}/netbox/netbox/configuration/plugins.py contains:"
echo "   PLUGINS = [\"netbox_rack_inverter\"]"
echo "   PLUGINS_CONFIG = {\"netbox_rack_inverter\": {}}"
echo "2) Run migrations:"
echo "   ${PYTHON_BIN} ${MANAGE_PY} migrate"
echo "3) Restart NetBox services:"
echo "   systemctl restart netbox netbox-rq"
echo "4) (Recommended) Persist for upgrades by adding the requirement to local_requirements.txt:"
echo "   PERSIST_LOCAL_REQUIREMENTS=1 NETBOX_ROOT=${NETBOX_ROOT} ./scripts/install-netbox-plugin.sh"
