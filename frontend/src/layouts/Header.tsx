import React from 'react';
import { useApp } from '../context/AppContext';
import { Database, Sun, Moon, Sparkles, RefreshCw } from 'lucide-react';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
  const { datasets, activeDataset, selectDatasetById, refreshDatasets, theme, toggleTheme } = useApp();

  return (
    <header className="h-16 bg-[#090d16] border-b border-slate-800/80 px-8 flex items-center justify-between select-none">
      <div>
        <h1 className="text-lg font-bold text-slate-100 tracking-tight">{title}</h1>
        {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        {/* Quick Dataset Selector */}
        {datasets.length > 0 && (
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300">
            <Database className="w-3.5 h-3.5 text-indigo-400" />
            <select
              value={activeDataset?.id || ''}
              onChange={(e) => selectDatasetById(Number(e.target.value))}
              className="bg-transparent text-slate-200 outline-none cursor-pointer font-medium text-xs pr-1"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id} className="bg-slate-900 text-slate-200">
                  {d.filename} {d.is_cleaned ? '(Cleaned)' : ''}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Refresh button */}
        <button
          onClick={() => refreshDatasets()}
          title="Refresh dataset status"
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>

        {/* AI Engine Status Pill */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-950/60 border border-indigo-800/50 text-[11px] text-indigo-300 font-medium">
          <Sparkles className="w-3 h-3 text-cyan-400" />
          <span>Claude AI Engine</span>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          title="Toggle Theme"
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
        >
          {theme === 'dark' ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
        </button>
      </div>
    </header>
  );
};
