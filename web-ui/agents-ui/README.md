# Agents UI

Modern, static Agent Catalog UI for the EasOps automation platform. The app consumes the backend registry endpoint and presents a searchable catalog with rich details for each LangGraph agent.

## Features
- Responsive grid of agents with client-side search and filters (category, frequency, owner)
- Detail drawer showing when to use, inputs/outputs, versions, and example endpoints
- Copy helpers for API payloads and n8n webhook configuration
- Keyboard-friendly, single-page UX with light/dark theme toggle
- Production-ready static build deployable to Cloud Run or any CDN/Cloud Storage bucket

## Getting started

### Prerequisites
- Node.js 18+
- npm (bundled with Node)

### Installation
```bash
cd web-ui/agents-ui
npm install
```

### Configuration
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
# Set VITE_AGENTS_API_BASE_URL to the agents API origin (for example, https://agents.easops.com)
```
`VITE_AGENTS_API_BASE_URL` is prefixed to all requests. The UI will surface an error if it is missing so the API origin is always explicit.

### Development
```bash
npm run dev
```
Vite serves the UI at `http://localhost:5173` with hot reloading.

### Build
```bash
npm run build
```
The static site is emitted to `dist/`. You can preview the production bundle locally with `npm run preview`.

## Deploying

### Cloud Run
1. Build the static assets: `npm run build`.
2. Serve the `dist/` directory with any static server (e.g., `gcr.io/distroless/nodejs` + `serve` or `nginx`).
3. Containerize the static server and deploy to Cloud Run. Ensure `VITE_AGENTS_API_BASE_URL` is set in the environment so the UI calls the correct API host.

### Cloud Storage + CDN
1. Build the site with `npm run build`.
2. Upload the contents of `dist/` to your bucket (e.g., `gsutil -m rsync -r dist gs://your-bucket`).
3. Front it with a CDN or load balancer. No server-side rendering is required.

## How data is fetched
The UI calls `GET {VITE_AGENTS_API_BASE_URL}/agents/registry` to load metadata for all agents. All filtering and search are performed client-side for fast interactions with 100+ agents.

## Extending the catalog
- Add new filters or sorting by extending the state in `src/App.tsx`.
- Update card layouts or the detail drawer in `src/components/AgentCard.tsx` and `src/components/AgentDetails.tsx`.
- Shared types and helpers live in `src/lib/` to keep components typed and portable.

## Tech stack
- React + TypeScript
- Vite
- TailwindCSS
