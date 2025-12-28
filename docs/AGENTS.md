# Agent Intelligence Layer

This service exposes LangGraph agents through FastAPI. Agents are treated as
first-class products with structured metadata so humans (via `/agents/catalog`)
and orchestrators like n8n (via `/agents/registry`) can discover and use them
reliably.

## Agent layout

Each agent lives under `docker/langgraph/app/agents/` using the pattern:

```
agents/
 └─ <agent_id>/
    └─ <version>/
       ├─ agent.py
       └─ manifest.json
```

- `agent.py` must export `agent_id`, `agent_version`, `agent_input_model`,
  `agent_output_model`, `build_graph()`, and `prepare_state()`.
- `manifest.json` contains human- and machine-readable metadata (see schema
  below). Agents **without** a manifest are skipped during discovery.

### Manifest schema

```json
{
  "agent_id": "string",
  "version": "string",
  "name": "string",
  "category": "string",
  "description": "string",
  "when_to_use": "string",
  "inputs": { "key": "description" },
  "outputs": { "key": "description" },
  "owner": "string",
  "frequency": "string",
  "cost": "string"
}
```

Invalid or missing manifests raise a startup error so issues surface quickly.

## Adding a new agent

1. Create a folder under `docker/langgraph/app/agents/<agent_id>/<version>/`.
2. Implement `agent.py` exporting the required symbols. Keep agent logic inside
   this folder to avoid side effects elsewhere.
3. Add `manifest.json` that matches the schema. The `agent_id` and `version`
   must match the values exported by `agent.py`.
4. (Optional) Add `__init__.py` under `<agent_id>/` to re-export the latest
   version for backwards-compatible imports.
5. Deploy; the registry will auto-discover the agent without changing app code.

### Versioning

- Versions are folders (e.g., `v1`, `v2`).
- The latest version is selected using semantic/lexicographic ordering; the
  highest version wins when no version is specified on a run request.
- You can ship multiple versions side-by-side for safe migrations.

## Registry and catalog endpoints

- `GET /agents/registry`: machine-readable registry used by n8n. Includes the
  latest version, all available versions, and manifest metadata for each agent.
- `GET /agents/catalog`: human-readable HTML catalog grouped by category.
- `GET /agents/{agent_id}/versions`: lists available versions and indicates the
  latest.
- `POST /agents/{agent_id}/run?version=<version>`: executes the requested agent
  version. Omitting `version` runs the latest. Invalid versions return `400`.

The legacy `/agents` route still returns a lightweight list of agents for quick
checks.

## n8n integration

n8n can call `GET /agents/registry` to populate dropdowns and build payload
schemas:

- `agent_id`: stable identifier for routing.
- `latest_version`: default when users do not specify a version.
- `versions`: ordered list of available versions.
- `manifests`: map of version to manifest payload (inputs/outputs are suitable
  for form builders).

Use `POST /agents/{agent_id}/run` with the selected version to trigger
execution.
