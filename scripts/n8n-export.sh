#!/usr/bin/env bash
set -euo pipefail

# Export n8n workflows as JSON files without credentials.
# Requires: N8N_BASE_URL, N8N_BASIC_USER, N8N_BASIC_PASS

BASE_URL="${N8N_BASE_URL:?Missing N8N_BASE_URL}"
USER="${N8N_BASIC_USER:?Missing N8N_BASIC_USER}"
PASS="${N8N_BASIC_PASS:?Missing N8N_BASIC_PASS}"
OUT_DIR="${N8N_WORKFLOW_DIR:-n8n/workflows}"

mkdir -p "${OUT_DIR}"

workflows_json="$(curl -fsS -u "${USER}:${PASS}" "${BASE_URL%/}/rest/workflows")"

ids=$(printf '%s' "${workflows_json}" | python3 - <<'PY'
import json,sys
obj=json.load(sys.stdin)
for w in obj.get('data', []):
    print(w.get('id'))
PY
)

if [[ -z "${ids}" ]]; then
  echo "No workflows found."
  exit 0
fi

for id in ${ids}; do
  wf_json="$(curl -fsS -u "${USER}:${PASS}" "${BASE_URL%/}/rest/workflows/${id}")"
  printf '%s' "${wf_json}" | python3 - <<'PY' "${OUT_DIR}"
import json,sys,os
out_dir=sys.argv[1]
obj=json.load(sys.stdin)
# Strip any credential references just in case
obj.pop('credentials', None)
name=obj.get('name','workflow')
safe="".join(c if c.isalnum() or c in ('-','_') else '-' for c in name).strip('-')
if not safe:
    safe=f"workflow-{obj.get('id','unknown')}"
path=os.path.join(out_dir, f"{safe}.json")
with open(path,'w') as f:
    json.dump(obj,f,indent=2,sort_keys=True)
PY
  echo "Exported workflow ${id}"
done
