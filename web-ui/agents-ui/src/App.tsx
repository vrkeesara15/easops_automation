import { useEffect, useMemo, useState } from 'react';
import { AgentCard } from './components/AgentCard';
import { AgentDetails } from './components/AgentDetails';
import { FiltersBar, allFilterValue } from './components/FiltersBar';
import { API_BASE_URL } from './config/api';
import { fetchAgentsRegistry } from './lib/api';
import { AgentMetadata, CatalogFilters } from './lib/types';

const defaultFilters: CatalogFilters = {
  search: '',
  category: allFilterValue,
  frequency: allFilterValue,
  owner: allFilterValue,
};

function uniqueSorted(values: string[]): string[] {
  return Array.from(new Set(values.filter(Boolean))).sort((a, b) => a.localeCompare(b));
}

export default function App() {
  const [agents, setAgents] = useState<AgentMetadata[]>([]);
  const [selected, setSelected] = useState<AgentMetadata | null>(null);
  const [filters, setFilters] = useState<CatalogFilters>(defaultFilters);
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [theme, setTheme] = useState<'light' | 'dark'>(() =>
    window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  );

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    setStatus('loading');
    fetchAgentsRegistry()
      .then((data) => {
        setAgents(data);
        setStatus('idle');
        setErrorMessage(null);
      })
      .catch((error) => {
        console.error(error);
        setStatus('error');
        setErrorMessage(error instanceof Error ? error.message : 'Unknown error');
      });
  }, []);

  const categories = useMemo(() => uniqueSorted(agents.map((agent) => agent.category)), [agents]);
  const frequencies = useMemo(() => uniqueSorted(agents.map((agent) => agent.frequency)), [agents]);
  const owners = useMemo(() => uniqueSorted(agents.map((agent) => agent.owner)), [agents]);

  const filteredAgents = useMemo(() => {
    const searchTerm = filters.search.trim().toLowerCase();

    return agents.filter((agent) => {
      const matchesSearch = searchTerm
        ? [agent.name, agent.description, agent.owner, agent.category]
            .filter(Boolean)
            .some((value) => value.toLowerCase().includes(searchTerm))
        : true;

      const matchesCategory =
        filters.category === allFilterValue || agent.category === filters.category;
      const matchesFrequency =
        filters.frequency === allFilterValue || agent.frequency === filters.frequency;
      const matchesOwner = filters.owner === allFilterValue || agent.owner === filters.owner;

      return matchesSearch && matchesCategory && matchesFrequency && matchesOwner;
    });
  }, [agents, filters]);

  const toggleTheme = () => setTheme((current) => (current === 'light' ? 'dark' : 'light'));

  return (
    <div className="min-h-screen bg-gradient-to-b from-surface-light via-white to-surface-light px-4 pb-12 pt-8 text-slate-900 dark:from-surface-dark dark:via-slate-900 dark:to-surface-dark dark:text-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <FiltersBar
          filters={filters}
          categories={categories}
          frequencies={frequencies}
          owners={owners}
          onChange={setFilters}
          theme={theme}
          onToggleTheme={toggleTheme}
        />

        <div className="flex items-center justify-between text-sm text-slate-600 dark:text-slate-300">
          <span>
            Showing {filteredAgents.length} of {agents.length || 0} agents
          </span>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
            Fast search, no page reloads
          </span>
        </div>

        {status === 'error' && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-red-800 shadow-sm dark:border-red-800 dark:bg-red-950/50 dark:text-red-100">
            <div className="font-semibold">Unable to load agents.</div>
            <p className="mt-1 text-sm">
              Attempted to fetch from
              <span className="font-mono">
                {' '}
                {`${API_BASE_URL}/agents/registry`}
              </span>
              . {errorMessage}
            </p>
            <p className="mt-2 text-sm">
              Set <code className="font-mono">VITE_AGENTS_API_BASE_URL</code> during the build if the API is on a different host
              than this UI.
            </p>
          </div>
        )}

        {status === 'loading' ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <div
                key={index}
                className="h-36 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-800"
                aria-hidden
              />
            ))}
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredAgents.map((agent) => (
              <AgentCard key={agent.agent_id} agent={agent} onSelect={setSelected} />
            ))}
          </div>
        )}
      </div>

      <AgentDetails agent={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
