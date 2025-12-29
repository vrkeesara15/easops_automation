import { API_BASE_URL } from '../config/api';
import { AgentMetadata } from './types';

export async function fetchAgentsRegistry(): Promise<AgentMetadata[]> {
  const endpoint = `${API_BASE_URL}/agents/registry`;

  try {
    const response = await fetch(endpoint);

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status} (${response.statusText || 'unknown'})`);
    }

    const data = await response.json();

    const agents = Array.isArray(data)
      ? data
      : Array.isArray(data?.agents)
        ? data.agents
        : [];

    return agents as AgentMetadata[];
  } catch (error) {
    console.error('Failed to fetch agents registry from', endpoint, error);
    throw new Error('Failed to fetch agents registry.');
  }
}
