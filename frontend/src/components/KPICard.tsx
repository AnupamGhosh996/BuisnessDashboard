import React from 'react';
import {
  DollarSign,
  TrendingUp,
  ShoppingCart,
  CreditCard,
  Percent,
  Users,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { KPICardData } from '../services/api';

const iconMap: Record<string, any> = {
  DollarSign,
  TrendingUp,
  ShoppingCart,
  CreditCard,
  Percent,
  Users,
  Activity,
};

export const KPICard: React.FC<{ kpi: KPICardData }> = ({ kpi }) => {
  const IconComponent = (kpi.icon && iconMap[kpi.icon]) || Activity;
  const isPositive = (kpi.change_pct ?? 0) >= 0;

  return (
    <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 hover:border-slate-700/80 transition-all duration-200 shadow-sm relative overflow-hidden group">
      {/* Decorative subtle background aura */}
      <div className="absolute -top-12 -right-12 w-28 h-28 bg-indigo-500/5 rounded-full blur-2xl group-hover:bg-indigo-500/10 transition-colors pointer-events-none" />

      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          {kpi.label}
        </span>
        <div className="w-8 h-8 rounded-lg bg-slate-800/80 border border-slate-700/50 flex items-center justify-center text-indigo-400 group-hover:text-cyan-400 transition-colors">
          <IconComponent className="w-4 h-4" />
        </div>
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <div className="text-2xl font-extrabold text-white tracking-tight">
          {kpi.formatted_value}
        </div>

        {kpi.change_pct !== undefined && (
          <span
            className={`inline-flex items-center gap-0.5 text-xs font-semibold px-2 py-0.5 rounded ${
              isPositive
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
            }`}
          >
            {isPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
            {Math.abs(kpi.change_pct)}%
          </span>
        )}
      </div>

      {kpi.subtext && (
        <p className="text-[11px] text-slate-400 mt-2 font-medium">
          {kpi.subtext}
        </p>
      )}
    </div>
  );
};
