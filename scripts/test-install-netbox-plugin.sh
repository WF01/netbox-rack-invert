#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="${SCRIPT_DIR}/install-netbox-plugin.sh"

pass() { printf 'PASS: %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }

mk_fake_python() {
  local target="$1"
  local mode="${2:-pip_ok}"
  mkdir -p "$(dirname "${target}")"
  cat > "${target}" <<PY
#!/usr/bin/env bash
set -euo pipefail
mode='${mode}'
if [[ "\$*" == "-m pip --version" ]]; then
  if [[ "\${mode}" == "pip_ok" ]]; then
    echo 'pip 24.0'
    exit 0
  fi
  exit 1
fi
if [[ "\$1" == "-m" && "\$2" == "pip" && "\$3" == "install" ]]; then
  exit 0
fi
exit 0
PY
  chmod +x "${target}"
}

mk_fake_manage_py() {
  local target="$1"
  mkdir -p "$(dirname "${target}")"
  cat > "${target}" <<'PY'
#!/usr/bin/env python
print("manage")
PY
}

test_autodetect_success() {
  local t
  t="$(mktemp -d)"
  trap 'rm -rf "${t}"' RETURN

  printf 'dummy-package==0.0.1\n' > "${t}/req.txt"
  mk_fake_python "${t}/netbox/venv/bin/python" pip_ok
  mk_fake_manage_py "${t}/netbox/netbox/manage.py"

  NETBOX_ROOT="${t}/netbox" REQUIREMENT_FILE="${t}/req.txt" bash "${INSTALLER}" >/dev/null
  pass "autodetect success path"
}

test_explicit_override_success() {
  local t
  t="$(mktemp -d)"
  trap 'rm -rf "${t}"' RETURN

  printf 'dummy-package==0.0.1\n' > "${t}/req.txt"
  mk_fake_python "${t}/custom/pybin" pip_ok
  mk_fake_manage_py "${t}/custom/manage.py"

  NETBOX_ROOT="${t}/missing" \
  NETBOX_PYTHON="${t}/custom/pybin" \
  NETBOX_MANAGE_PY="${t}/custom/manage.py" \
  REQUIREMENT_FILE="${t}/req.txt" \
  bash "${INSTALLER}" >/dev/null

  pass "explicit override success path"
}

test_uv_fallback_success() {
  local t
  t="$(mktemp -d)"
  trap 'rm -rf "${t}"' RETURN

  printf 'dummy-package==0.0.1\n' > "${t}/req.txt"
  mk_fake_python "${t}/netbox/venv/bin/python" pip_missing
  mk_fake_manage_py "${t}/netbox/netbox/manage.py"

  mkdir -p "${t}/bin"
  cat > "${t}/bin/uv" <<'UV'
#!/usr/bin/env bash
set -euo pipefail
if [[ "$1" == "pip" && "$2" == "install" ]]; then
  exit 0
fi
exit 1
UV
  chmod +x "${t}/bin/uv"

  PATH="${t}/bin:${PATH}" \
  NETBOX_ROOT="${t}/netbox" REQUIREMENT_FILE="${t}/req.txt" \
  bash "${INSTALLER}" >/dev/null

  pass "uv fallback success path"
}

test_missing_manage_fails() {
  local t
  t="$(mktemp -d)"
  trap 'rm -rf "${t}"' RETURN

  printf 'dummy-package==0.0.1\n' > "${t}/req.txt"
  mk_fake_python "${t}/netbox/venv/bin/python" pip_ok

  set +e
  local out
  out="$(NETBOX_ROOT="${t}/netbox" REQUIREMENT_FILE="${t}/req.txt" bash "${INSTALLER}" 2>&1)"
  local ec=$?
  set -e

  [[ $ec -ne 0 ]] || fail "missing manage should fail"
  grep -q 'NETBOX_MANAGE_PY explicitly' <<<"${out}" || fail "missing manage should mention NETBOX_MANAGE_PY"
  pass "missing manage fails with actionable message"
}

test_persist_requirements_idempotent() {
  local t
  t="$(mktemp -d)"
  trap 'rm -rf "${t}"' RETURN

  printf 'dummy-package==0.0.1\n' > "${t}/req.txt"
  mk_fake_python "${t}/netbox/venv/bin/python" pip_ok
  mk_fake_manage_py "${t}/netbox/netbox/manage.py"

  local lr="${t}/netbox/local_requirements.txt"
  NETBOX_ROOT="${t}/netbox" REQUIREMENT_FILE="${t}/req.txt" PERSIST_LOCAL_REQUIREMENTS=1 bash "${INSTALLER}" >/dev/null
  NETBOX_ROOT="${t}/netbox" REQUIREMENT_FILE="${t}/req.txt" PERSIST_LOCAL_REQUIREMENTS=1 bash "${INSTALLER}" >/dev/null

  local count
  count="$(grep -c '^dummy-package==0.0.1$' "${lr}")"
  [[ "${count}" == "1" ]] || fail "persisted requirement should not duplicate"
  pass "persist local requirements is idempotent"
}

test_autodetect_success
test_explicit_override_success
test_uv_fallback_success
test_missing_manage_fails
test_persist_requirements_idempotent

echo "All installer tests passed."
