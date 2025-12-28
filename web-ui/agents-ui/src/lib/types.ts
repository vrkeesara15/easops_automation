export interface AgentMetadata {
  agent_id: string;
  name: string;
  category: string;
  description: string;
  when_to_use: string;
  inputs: Record<string, string>;
  outputs: Record<string, string>;
  owner: string;
  frequency: string;
  cost: string;
  latest_version: string;
  versions: string[];
  manifests: Record<string, unknown>;
}

export interface CatalogFilters {
  search: string;
  category: string;
  frequency: string;
  owner: string;
}
