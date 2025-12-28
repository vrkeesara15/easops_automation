# LangGraph Agent n8n Workflow Template

This folder contains a reusable n8n workflow export for invoking LangGraph agents via the platform's `run` endpoint. Import `agent_workflow_template.json` into n8n to get started.

## Prerequisites
- n8n instance (self-hosted or cloud) with access to the LangGraph Agents API.
- Environment variables set in n8n for values used by the workflow:
  - `AGENTS_BASE_URL` (required) – Base URL for the Agents service (e.g., `https://agents.example.com`).
  - `AGENT_ID` (optional) – Default agent identifier used by the manual trigger.
  - `AGENT_VERSION` (optional) – Default agent version for manual runs.
  - `AGENT_INPUT_PAYLOAD` (optional) – JSON string with a default payload for manual runs.
  - `AGENT_METADATA` (optional) – JSON string containing default metadata for manual runs.

## Importing the Workflow
1. In n8n, choose **Import from File** and select `agent_workflow_template.json` from this folder.
2. Save the workflow. The **Webhook Trigger** node will display the public URL after saving; use it for external integrations.
3. Ensure the workflow is **active** if you want to receive webhook calls. Manual runs work even when inactive.

## How It Works
1. **Triggers**: Either the **Manual Trigger** (for quick tests) or **Webhook Trigger** (for external calls) can start the workflow.
2. **Manual Defaults**: Populates `agent_id`, `agent_version`, `input_payload`, and `metadata` from environment variables so the template is reusable across agents.
3. **Merge Inputs**: Merges manual and webhook inputs to a common payload.
4. **Prepare Payload**: Normalizes the request, adds a UUID `run_id`, and enriches metadata with the n8n execution ID.
5. **Invoke Agent**: Sends a `POST` to `{{AGENTS_BASE_URL}}/agents/{{agent_id}}/run` with JSON body and `Content-Type: application/json`.
6. **Check Success**: Routes on `success === true`.
7. **Log Agent Run**: Writes execution details to the n8n log.
8. **Optional Branches**: Add file storage nodes to **Save Artifacts (Optional)** and communication nodes to **Notify (Optional)**.
9. **Respond Success / Respond Failure**: Sends structured responses to webhook callers. Manual runs will simply show these nodes' outputs in the UI.

## Customization Tips
- Swap the **Save Artifacts (Optional)** node with cloud storage nodes (e.g., S3, GCS, Azure Blob) to persist outputs.
- Replace the **Notify (Optional)** node with Slack, Email, or other messaging integrations.
- Adjust the webhook path in **Webhook Trigger** to fit your routing conventions.
- Update the manual default values or environment variables to target different agents without modifying the workflow logic.

## Testing the Template
- **Manual**: Click **Execute Workflow** in n8n. The **Manual Defaults** node uses environment variables for agent ID/version and payload.
- **Webhook**: Send a `POST` to the webhook URL with JSON body:

```json
{
  "agent_id": "your-agent-id",
  "agent_version": "latest",
  "input_payload": {"message": "Hello"},
  "metadata": {"source": "webhook-test"}
}
```

A successful response returns the agent's output; failures return a 500 response with an error message.
