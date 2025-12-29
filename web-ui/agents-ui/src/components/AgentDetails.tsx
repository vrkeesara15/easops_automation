import { useMemo, useState } from 'react';
import { API_BASE_URL } from '../config/api';
import { AgentMetadata } from '../lib/types';
import { buildEndpointUrl, buildExamplePayload, buildN8nWebhook, formatList } from '../lib/utils';
import { Badge } from './Badge';

interface AgentDetailsProps {
  agent: AgentMetadata | null;
  onClose: () => void;
}

export function AgentDetails({ agent, onClose }: AgentDetailsProps) {
  const [copyMessage, setCopyMessage] = useState('');

  const payload = useMemo(() => (agent ? buildExamplePayload(agent) : {}), [agent]);
  const n8nWebhook = useMemo(() => (agent ? buildN8nWebhook(agent, API_BASE_URL) : {}), [agent]);
  const endpointUrl = useMemo(() => (agent ? buildEndpointUrl(agent, API_BASE_URL) : ''), [agent]);

  if (!agent) return null;

  const handleCopy = async (content: string, label: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopyMessage(`${label} copied`);
      setTimeout(() => setCopyMessage(''), 2000);
    } catch (error) {
      setCopyMessage('Clipboard unavailable');
      console.error('Failed to copy', error);
    }
  };

  return (
    <div className="fixed inset-0 z-40 flex items-start justify-end bg-black/30 backdrop-blur-sm">
      <div className="absolute inset-0" onClick={onClose} />
      <aside className="relative z-10 h-full w-full max-w-2xl overflow-y-auto border-l border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <Badge>{agent.category}</Badge>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                Latest v{agent.latest_version}
              </span>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{agent.name}</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{agent.description}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-400 dark:bg-slate-800 dark:text-slate-200"
            type="button"
          >
            Close
          </button>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-800/40">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Owner</p>
            <p className="text-base font-semibold text-slate-900 dark:text-white">{agent.owner}</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-800/40">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Frequency</p>
            <p className="text-base font-semibold text-slate-900 dark:text-white">{agent.frequency}</p>
          </div>
        </div>

        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/70">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">When to use</h3>
          <p className="mt-2 text-sm leading-relaxed text-slate-700 dark:text-slate-300">{agent.when_to_use}</p>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/70">
            <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Inputs</h4>
            <ul className="mt-2 space-y-2 text-sm text-slate-700 dark:text-slate-200">
              {formatList(agent.inputs).map((item) => (
                <li key={item.key} className="rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-800/60">
                  <span className="font-semibold text-indigo-600 dark:text-indigo-300">{item.key}</span>
                  <p className="text-xs text-slate-600 dark:text-slate-300">{item.description}</p>
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/70">
            <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Outputs</h4>
            <ul className="mt-2 space-y-2 text-sm text-slate-700 dark:text-slate-200">
              {formatList(agent.outputs).map((item) => (
                <li key={item.key} className="rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-800/60">
                  <span className="font-semibold text-indigo-600 dark:text-indigo-300">{item.key}</span>
                  <p className="text-xs text-slate-600 dark:text-slate-300">{item.description}</p>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/70">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Available versions</h3>
          <div className="mt-2 flex flex-wrap gap-2">
            {agent.versions.map((version) => (
              <span
                key={version}
                className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                v{version}
              </span>
            ))}
          </div>
        </div>

        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/70">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">API endpoint</h3>
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">POST</span>
          </div>
          <code className="mt-2 block rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-800 dark:bg-slate-800 dark:text-slate-100">
            {endpointUrl}
          </code>
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-600 dark:text-slate-300">
            <span>Full URL:</span>
            <span className="break-all font-mono">{endpointUrl}</span>
          </div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/70">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-slate-900 dark:text-white">API payload</h4>
              <button
                onClick={() => handleCopy(JSON.stringify(payload, null, 2), 'Payload')}
                className="rounded-full bg-indigo-600 px-3 py-1 text-xs font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                type="button"
              >
                Copy API payload
              </button>
            </div>
            <pre className="mt-2 max-h-60 overflow-auto rounded-lg bg-slate-100 p-3 text-xs text-slate-800 dark:bg-slate-800 dark:text-slate-100">
{JSON.stringify(payload, null, 2)}
            </pre>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/70">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-slate-900 dark:text-white">n8n webhook config</h4>
              <button
                onClick={() => handleCopy(JSON.stringify(n8nWebhook, null, 2), 'Webhook config')}
                className="rounded-full bg-indigo-600 px-3 py-1 text-xs font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                type="button"
              >
                Copy n8n webhook config
              </button>
            </div>
            <pre className="mt-2 max-h-60 overflow-auto rounded-lg bg-slate-100 p-3 text-xs text-slate-800 dark:bg-slate-800 dark:text-slate-100">
{JSON.stringify(n8nWebhook, null, 2)}
            </pre>
          </div>
        </div>

        {copyMessage && (
          <div className="mt-4 inline-flex items-center gap-2 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-100">
            {copyMessage}
          </div>
        )}
      </aside>
    </div>
  );
}
