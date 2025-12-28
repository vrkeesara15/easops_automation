import { AgentMetadata } from './types';

const baseUrl = (import.meta.env.VITE_AGENTS_API_BASE_URL || '').replace(/\/$/, '');

export const agentsApiBase = baseUrl || '';

export async function fetchAgentsRegistry(): Promise<AgentMetadata[]> {
  const endpoint = agentsApiBase ? `${agentsApiBase}/agents/registry` : '/agents/registry';
  const response = await fetch(endpoint);

  if (!response.ok) {
    throw new Error(`Unable to fetch agents: ${response.status}`);
  }

  return response.json();
}
