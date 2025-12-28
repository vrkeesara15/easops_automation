import { ChangeEvent } from 'react';
import { CatalogFilters } from '../lib/types';

interface FiltersBarProps {
  filters: CatalogFilters;
  categories: string[];
  frequencies: string[];
  owners: string[];
  onChange: (filters: CatalogFilters) => void;
  onToggleTheme: () => void;
  theme: 'light' | 'dark';
}

const allOption = 'all';

export function FiltersBar({
  filters,
  categories,
  frequencies,
  owners,
  onChange,
  theme,
  onToggleTheme,
}: FiltersBarProps) {
  const handleSelect = (key: keyof CatalogFilters) => (event: ChangeEvent<HTMLSelectElement>) => {
    onChange({ ...filters, [key]: event.target.value });
  };

  const handleSearch = (event: ChangeEvent<HTMLInputElement>) => {
    onChange({ ...filters, search: event.target.value });
  };

  return (
    <div className="flex flex-col gap-4 rounded-2xl bg-white/80 p-4 shadow-card ring-1 ring-slate-200 backdrop-blur dark:bg-slate-900/70 dark:ring-slate-800">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-600 dark:text-slate-300">Agent Catalog</p>
          <h1 className="text-2xl font-bold leading-tight text-slate-900 dark:text-white">
            Discover and run LangGraph agents
          </h1>
        </div>
        <button
          onClick={onToggleTheme}
          className="inline-flex items-center justify-center rounded-full bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm ring-1 ring-slate-200 transition hover:-translate-y-0.5 hover:bg-white dark:bg-slate-800 dark:text-slate-100 dark:ring-slate-700"
          aria-label="Toggle color mode"
          type="button"
        >
          {theme === 'light' ? '🌙 Dark mode' : '☀️ Light mode'}
        </button>
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div className="col-span-2">
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Search
          </label>
          <input
            type="search"
            value={filters.search}
            onChange={handleSearch}
            placeholder="Search agents by name, description, or owner"
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none ring-indigo-200 transition focus:border-indigo-300 focus:ring-2 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Category
          </label>
          <select
            value={filters.category}
            onChange={handleSelect('category')}
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none ring-indigo-200 transition focus:border-indigo-300 focus:ring-2 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
          >
            <option value={allOption}>All</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Frequency
          </label>
          <select
            value={filters.frequency}
            onChange={handleSelect('frequency')}
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none ring-indigo-200 transition focus:border-indigo-300 focus:ring-2 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
          >
            <option value={allOption}>All</option>
            {frequencies.map((frequency) => (
              <option key={frequency} value={frequency}>
                {frequency}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Owner
          </label>
          <select
            value={filters.owner}
            onChange={handleSelect('owner')}
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none ring-indigo-200 transition focus:border-indigo-300 focus:ring-2 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
          >
            <option value={allOption}>All</option>
            {owners.map((owner) => (
              <option key={owner} value={owner}>
                {owner}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

export { allOption as allFilterValue };
