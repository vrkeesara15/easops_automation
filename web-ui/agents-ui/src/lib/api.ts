import { API_BASE_URL } from '../config/api';
import { AgentMetadata } from './types';

export async function fetchAgentsRegistry(): Promise<AgentMetadata[]> {
  const endpoint = `${API_BASE_URL}/agents/registry`;

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
