import { API_BASE_URL } from '../config/api';
import { AgentMetadata } from './types';

export function buildExamplePayload(agent: AgentMetadata): Record<string, unknown> {
  return Object.fromEntries(
    Object.keys(agent.inputs || {}).map((key) => [key, `<${agent.inputs[key] || 'value'}>`])
  );
}

export function buildEndpointUrl(agent: AgentMetadata, baseUrl: string = API_BASE_URL): string {
  const root = baseUrl ? baseUrl.replace(/\/$/, '') : '';
  return `${root}/agents/${agent.agent_id}/run?version=${agent.latest_version}`;
}

export function buildN8nWebhook(agent: AgentMetadata, baseUrl: string = API_BASE_URL): Record<string, unknown> {
  return {
    method: 'POST',
    url: buildEndpointUrl(agent, baseUrl),
    headers: {
      'Content-Type': 'application/json',
    },
    body: buildExamplePayload(agent),
  };
}

export function formatList(items: Record<string, string>): { key: string; description: string }[] {
  return Object.entries(items || {}).map(([key, description]) => ({ key, description }));
}
