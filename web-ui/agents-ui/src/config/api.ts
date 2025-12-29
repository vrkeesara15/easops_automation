const rawApiBaseUrl = (import.meta.env.VITE_AGENTS_API_BASE_URL || '').replace(/\/$/, '');

if (!rawApiBaseUrl) {
  const message =
    'VITE_AGENTS_API_BASE_URL is not set. Provide it in your environment before building (e.g. VITE_AGENTS_API_BASE_URL=https://agents.easops.com).';
  console.error(message);
  throw new Error(message);
}

export const API_BASE_URL = rawApiBaseUrl;
