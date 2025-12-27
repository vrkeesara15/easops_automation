#!/usr/bin/env bash
set -euo pipefail

# Import n8n workflows from JSON files.
# Requires: N8N_BASE_URL, N8N_BASIC_USER, N8N_BASIC_PASS

BASE_URL="${N8N_BASE_URL:?Missing N8N_BASE_URL}"
USER="${N8N_BASIC_USER:?Missing N8N_BASIC_USER}"
PASS="${N8N_BASIC_PASS:?Missing N8N_BASIC_PASS}"
IN_DIR="${N8N_WORKFLOW_DIR:-n8n/workflows}"

if [[ ! -d "${IN_DIR}" ]]; then
  echo "Workflow directory not found: ${IN_DIR}"
  exit 1
fi

for file in "${IN_DIR}"/*.json; do
  [[ -e "${file}" ]] || { echo "No workflow JSON files found in ${IN_DIR}"; exit 0; }

  wf_json="$(cat "${file}")"
  name=$(printf '%s' "${wf_json}" | python3 - <<'PY'
import json,sys
obj=json.load(sys.stdin)
print(obj.get('name',''))
PY
)

  if [[ -z "${name}" ]]; then
    echo "Skipping ${file}: missing name"
    continue
  fi

  existing_id=$(curl -fsS -u "${USER}:${PASS}" "${BASE_URL%/}/rest/workflows" | python3 - <<'PY' "${name}"
import json,sys
name=sys.argv[1]
obj=json.load(sys.stdin)
for w in obj.get('data', []):
    if w.get('name') == name:
        print(w.get('id'))
        break
PY
)

  if [[ -n "${existing_id}" ]]; then
    curl -fsS -u "${USER}:${PASS}" -X PATCH \
      -H "Content-Type: application/json" \
      -d "${wf_json}" \
      "${BASE_URL%/}/rest/workflows/${existing_id}" > /dev/null
    echo "Updated workflow: ${name}"
  else
    curl -fsS -u "${USER}:${PASS}" -X POST \
      -H "Content-Type: application/json" \
      -d "${wf_json}" \
      "${BASE_URL%/}/rest/workflows" > /dev/null
    echo "Created workflow: ${name}"
  fi

done
