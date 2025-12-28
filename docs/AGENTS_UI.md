# Agents UI deployment

The agents UI (`web-ui/agents-ui`) is built with Vite, React, and Tailwind. It
is published as its own Cloud Run service so frontend releases do not interfere
with the backend agents API.

## Deployment flow

- A GitHub Actions workflow (`deploy-agents-ui.yml`) runs on every push to the
  `main` branch when files under `web-ui/agents-ui/` change.
- The workflow builds the UI with `VITE_AGENTS_API_BASE_URL` set to
  `https://agents.easops.com`, builds a container image with the provided
  `Dockerfile`, and pushes it to Google Cloud.
- The image is deployed to the `agents-ui` Cloud Run service in the configured
  region with unauthenticated access enabled. The service is expected to be
  reachable at `https://ui.agents.easops.com`.
- No manual steps are required after merging to `main`; Cloud Run will serve the
  latest build automatically once the workflow completes.

## Adding or updating agents

Agents are defined in the backend and exposed through `GET /agents/registry` on
`https://agents.easops.com`. The UI simply fetches that registry and renders the
results. Adding a new agent or updating metadata only requires backend changes;
the UI will display the new data automatically without a redeploy.

## Local development

1. Copy `.env.example` to `.env` under `web-ui/agents-ui` and adjust
   `VITE_AGENTS_API_BASE_URL` if you are pointing at a non-production API.
2. Run `npm install` and `npm run dev` from `web-ui/agents-ui`.
3. Build locally with `npm run build` to mirror the production workflow.
