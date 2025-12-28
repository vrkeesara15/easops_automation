import { AgentMetadata } from '../lib/types';
import { Badge } from './Badge';

interface AgentCardProps {
  agent: AgentMetadata;
  onSelect: (agent: AgentMetadata) => void;
}

export function AgentCard({ agent, onSelect }: AgentCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(agent)}
      className="group flex h-full flex-col gap-3 rounded-2xl border border-transparent bg-white p-4 text-left shadow-card transition hover:-translate-y-1 hover:border-indigo-200 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-indigo-400 dark:bg-slate-900 dark:hover:border-indigo-500/40"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <Badge>{agent.category}</Badge>
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-300">v{agent.latest_version}</span>
          </div>
          <h2 className="text-lg font-semibold text-slate-900 transition group-hover:text-indigo-600 dark:text-white">
            {agent.name}
          </h2>
        </div>
        <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 transition group-hover:bg-indigo-100 dark:bg-indigo-900/40 dark:text-indigo-100">
          {agent.owner}
        </span>
      </div>
      <p className="line-clamp-2 text-sm text-slate-600 dark:text-slate-300">{agent.description}</p>
      <div className="flex flex-wrap gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
        <span className="rounded-full bg-slate-100 px-2 py-1 dark:bg-slate-800">{agent.frequency}</span>
        <span className="rounded-full bg-slate-100 px-2 py-1 dark:bg-slate-800">Latest: {agent.latest_version}</span>
        <span className="rounded-full bg-slate-100 px-2 py-1 dark:bg-slate-800">{agent.versions.length} versions</span>
      </div>
    </button>
  );
}
