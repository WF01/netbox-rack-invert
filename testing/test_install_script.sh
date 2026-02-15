#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
INSTALL_SCRIPT="${REPO_ROOT}/scripts/install-netbox-plugin.sh"

pass() { printf 'PASS: %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }

run_installer() {
  env "$@" bash "${INSTALL_SCRIPT}"
}

TMPDIR="$(mktemp -d)"
trap 'rm -rf "${TMPDIR}"' EXIT

REQ_FILE="${TMPDIR}/requirements.txt"
echo 'dummy-package==0.0.1' > "${REQ_FILE}"

make_fake_python() {
  local path="$1"
  local mode="${2:-pip}"
  cat > "${path}" <<'PY'
#!/usr/bin/env bash
MODE="${FAKE_PYTHON_MODE:-pip}"
if [[ "${MODE}" == "pip" ]]; then
  if [[ "$*" == "-m pip --version" ]]; then
    echo 'pip 24.0'
    exit 0
  fi
  if [[ "$1" == "-m" && "$2" == "pip" && "$3" == "install" ]]; then
    exit 0
  fi
fi
if [[ "${MODE}" == "no-pip" ]]; then
  if [[ "$*" == "-m pip --version" ]]; then
    exit 1
  fi
fi
exit 0
PY
  chmod +x "${path}"
  if [[ "${mode}" == "no-pip" ]]; then
    :
  fi
}

# Case 1: auto-detection succeeds via NETBOX_ROOT defaults + pip path
NETBOX1="${TMPDIR}/netbox1"
mkdir -p "${NETBOX1}/venv/bin" "${NETBOX1}/netbox"
make_fake_python "${NETBOX1}/venv/bin/python" pip
cat > "${NETBOX1}/netbox/manage.py" <<'PY'
#!/usr/bin/env python
print('manage')
PY

run_installer NETBOX_ROOT="${NETBOX1}" REQUIREMENT_FILE="${REQ_FILE}" >/dev/null
pass "auto-detection install path"

# Case 2: explicit override path succeeds
CUSTOM="${TMPDIR}/custom"
mkdir -p "${CUSTOM}/python" "${CUSTOM}/app"
cp "${NETBOX1}/venv/bin/python" "${CUSTOM}/python/pybin"
cp "${NETBOX1}/netbox/manage.py" "${CUSTOM}/app/manage.py"
chmod +x "${CUSTOM}/python/pybin"
run_installer NETBOX_ROOT="${TMPDIR}/missing" NETBOX_PYTHON="${CUSTOM}/python/pybin" NETBOX_MANAGE_PY="${CUSTOM}/app/manage.py" REQUIREMENT_FILE="${REQ_FILE}" >/dev/null
pass "explicit path override"

# Case 3: uv fallback path when pip unavailable
NETBOX2="${TMPDIR}/netbox2"
mkdir -p "${NETBOX2}/venv/bin" "${NETBOX2}/netbox" "${TMPDIR}/bin"
make_fake_python "${NETBOX2}/venv/bin/python" no-pip
cat > "${NETBOX2}/netbox/manage.py" <<'PY'
#!/usr/bin/env python
print('manage')
PY
cat > "${TMPDIR}/bin/uv" <<'UV'
#!/usr/bin/env bash
if [[ "$1" == "pip" && "$2" == "install" ]]; then
  exit 0
fi
exit 1
UV
chmod +x "${TMPDIR}/bin/uv"
PATH="${TMPDIR}/bin:${PATH}" FAKE_PYTHON_MODE=no-pip run_installer NETBOX_ROOT="${NETBOX2}" REQUIREMENT_FILE="${REQ_FILE}" >/dev/null
pass "uv fallback install path"

# Case 4: missing manage.py errors clearly
set +e
ERR_OUT="$(run_installer NETBOX_ROOT="${TMPDIR}/no-manage" REQUIREMENT_FILE="${REQ_FILE}" 2>&1)"
EC=$?
set -e
[[ ${EC} -ne 0 ]] || fail "missing manage.py should fail"
printf '%s' "${ERR_OUT}" | grep -q 'Set NETBOX_MANAGE_PY explicitly' || fail "missing manage.py message"
pass "missing manage.py failure message"

# Case 5: persistence writes once and is idempotent
NETBOX3="${TMPDIR}/netbox3"
mkdir -p "${NETBOX3}/venv/bin" "${NETBOX3}/netbox"
make_fake_python "${NETBOX3}/venv/bin/python" pip
cat > "${NETBOX3}/netbox/manage.py" <<'PY'
#!/usr/bin/env python
print('manage')
PY
LOCAL_REQ="${TMPDIR}/local_requirements.txt"
run_installer NETBOX_ROOT="${NETBOX3}" REQUIREMENT_FILE="${REQ_FILE}" PERSIST_LOCAL_REQUIREMENTS=1 NETBOX_LOCAL_REQUIREMENTS="${LOCAL_REQ}" >/dev/null
run_installer NETBOX_ROOT="${NETBOX3}" REQUIREMENT_FILE="${REQ_FILE}" PERSIST_LOCAL_REQUIREMENTS=1 NETBOX_LOCAL_REQUIREMENTS="${LOCAL_REQ}" >/dev/null
COUNT="$(grep -c '^dummy-package==0.0.1$' "${LOCAL_REQ}")"
[[ "${COUNT}" == "1" ]] || fail "local_requirements should contain one entry"
pass "local_requirements persistence"

printf '\nAll install script smoke tests passed.\n'
