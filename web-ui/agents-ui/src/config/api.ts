const rawApiBaseUrl = (import.meta.env?.VITE_AGENTS_API_BASE_URL || '').toString().trim();

if (!rawApiBaseUrl) {
  console.warn(
    'VITE_AGENTS_API_BASE_URL is not set. Falling back to https://agents.easops.com. Set the env var to point to your API if needed.'
  );
}

const normalizedBaseUrl = (rawApiBaseUrl || 'https://agents.easops.com').replace(/\/$/, '');

export const API_BASE_URL = normalizedBaseUrl;
