import { AgentMetadata } from './types';

const baseUrl = (import.meta.env.VITE_AGENTS_API_BASE_URL || '').replace(/\/$/, '');

export const agentsApiBase = baseUrl || '';

export async function fetchAgentsRegistry(): Promise<AgentMetadata[]> {
  const endpoint = agentsApiBase ? `${agentsApiBase}/agents/registry` : '/agents/registry';

  try {
    const response = await fetch(endpoint);

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status} (${response.statusText || 'unknown'})`);
    }

    return response.json();
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Unable to fetch agents from ${endpoint}: ${message}`);
  }
}
