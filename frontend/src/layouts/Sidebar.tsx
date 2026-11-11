import React from 'react';
import { useApp } from '../context/AppContext';
import {
  LayoutDashboard,
  UploadCloud,
  Table,
  Sparkles,
  BarChart2,
  LineChart,
  Bot,
  AlertTriangle,
  TrendingUp,
  FileText,
  Settings,
  Database,
  CheckCircle2,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { activeTab, setActiveTab, activeDataset, datasets } = useApp();

  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'upload', label: 'Data Upload', icon: UploadCloud, badge: datasets.length },
    { id: 'explorer', label: 'Data Explorer', icon: Table },
    { id: 'cleaning', label: 'Automated Cleaning', icon: Sparkles },
    { id: 'eda', label: 'Exploratory EDA', icon: LineChart },
    { id: 'dashboard', label: 'BI Dashboard', icon: BarChart2, highlight: true },
    { id: 'ai', label: 'AI Data Analyst', icon: Bot, ai: true },
    { id: 'anomaly', label: 'Anomaly Detection', icon: AlertTriangle },
    { id: 'forecasting', label: 'Forecasting', icon: TrendingUp },
    { id: 'reports', label: 'Business Reports', icon: FileText },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-[#090d16] border-r border-slate-800/80 flex flex-col h-screen select-none">
      {/* Brand Logo */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800/80 gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 font-black text-white text-base">
          IQ
        </div>
        <div>
          <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
            InsightIQ
            <span className="text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-1.5 py-0.5 rounded">
              v1.0
            </span>
          </span>
          <p className="text-[11px] text-slate-400 font-medium">Enterprise AI Analytics</p>
        </div>
      </div>

      {/* Active Dataset Status Widget */}
      <div className="p-3 mx-3 my-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
          <span className="flex items-center gap-1.5 font-medium">
            <Database className="w-3.5 h-3.5 text-cyan-400" />
            Active Dataset
          </span>
          {activeDataset && (
            <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-medium">
              <CheckCircle2 className="w-3 h-3" /> Ready
            </span>
          )}
        </div>
        <p className="text-xs font-semibold text-slate-200 truncate" title={activeDataset?.filename || 'No dataset loaded'}>
          {activeDataset?.filename || 'No dataset loaded'}
        </p>
        {activeDataset && (
          <div className="flex items-center gap-2 mt-1.5 text-[11px] text-slate-400">
            <span>{activeDataset.row_count.toLocaleString()} rows</span>
            <span>•</span>
            <span>{activeDataset.column_count} cols</span>
            {activeDataset.is_cleaned && (
              <span className="ml-auto text-[10px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.2 rounded font-medium border border-emerald-500/20">
                Cleaned
              </span>
            )}
          </div>
        )}
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 space-y-1 overflow-y-auto pt-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon
                className={`w-4 h-4 transition-colors ${
                  isActive ? 'text-white' : item.ai ? 'text-indigo-400' : 'text-slate-400'
                }`}
              />
              <span className="flex-1 text-left">{item.label}</span>
              {item.badge !== undefined && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-semibold">
                  {item.badge}
                </span>
              )}
              {item.ai && (
                <span className="text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider bg-gradient-to-r from-indigo-500 to-cyan-500 text-white shadow-xs">
                  AI
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer System Status */}
      <div className="p-3 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>System Healthy</span>
        </div>
        <span className="text-[10px] text-slate-400">REST API 8000</span>
      </div>
    </aside>
  );
};
