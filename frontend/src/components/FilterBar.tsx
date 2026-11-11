import React from 'react';
import { useApp } from '../context/AppContext';
import { Filter, Calendar, RotateCcw } from 'lucide-react';

interface FilterBarProps {
  categories?: string[];
  regions?: string[];
  dateRange?: { start: string; end: string };
  onFilterChange?: () => void;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  categories = [],
  regions = [],
  dateRange,
  onFilterChange,
}) => {
  const { filters, setFilters } = useApp();

  const handleDateChange = (type: 'start_date' | 'end_date', value: string) => {
    setFilters((prev) => ({ ...prev, [type]: value || undefined }));
    onFilterChange?.();
  };

  const handleCategoryToggle = (cat: string) => {
    setFilters((prev) => {
      const current = prev.category || [];
      const updated = current.includes(cat) ? current.filter((c) => c !== cat) : [...current, cat];
      return { ...prev, category: updated.length ? updated : undefined };
    });
    onFilterChange?.();
  };

  const handleRegionToggle = (reg: string) => {
    setFilters((prev) => {
      const current = prev.region || [];
      const updated = current.includes(reg) ? current.filter((r) => r !== reg) : [...current, reg];
      return { ...prev, region: updated.length ? updated : undefined };
    });
    onFilterChange?.();
  };

  const handleReset = () => {
    setFilters({});
    onFilterChange?.();
  };

  const hasActiveFilters = Boolean(
    filters.start_date || filters.end_date || filters.category?.length || filters.region?.length
  );

  return (
    <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-4 mb-6 flex flex-wrap items-center gap-4 text-xs">
      <div className="flex items-center gap-1.5 text-slate-400 font-semibold uppercase tracking-wider">
        <Filter className="w-3.5 h-3.5 text-indigo-400" />
        <span>Filters</span>
      </div>

      {/* Date Range Inputs */}
      {dateRange && (
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5">
          <Calendar className="w-3.5 h-3.5 text-slate-400" />
          <input
            type="date"
            min={dateRange.start}
            max={dateRange.end}
            value={filters.start_date || ''}
            onChange={(e) => handleDateChange('start_date', e.target.value)}
            className="bg-transparent text-slate-200 outline-none cursor-pointer"
          />
          <span className="text-slate-400">to</span>
          <input
            type="date"
            min={dateRange.start}
            max={dateRange.end}
            value={filters.end_date || ''}
            onChange={(e) => handleDateChange('end_date', e.target.value)}
            className="bg-transparent text-slate-200 outline-none cursor-pointer"
          />
        </div>
      )}

      {/* Category Filter Pills */}
      {categories.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-slate-400 font-medium mr-1">Category:</span>
          {categories.slice(0, 6).map((cat) => {
            const isSelected = filters.category?.includes(cat);
            return (
              <button
                key={cat}
                onClick={() => handleCategoryToggle(cat)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition ${
                  isSelected
                    ? 'bg-indigo-600 text-white font-semibold'
                    : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {cat}
              </button>
            );
          })}
        </div>
      )}

      {/* Region Filter Pills */}
      {regions.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-slate-400 font-medium mr-1">Region:</span>
          {regions.slice(0, 5).map((reg) => {
            const isSelected = filters.region?.includes(reg);
            return (
              <button
                key={reg}
                onClick={() => handleRegionToggle(reg)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition ${
                  isSelected
                    ? 'bg-cyan-600 text-white font-semibold'
                    : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {reg}
              </button>
            );
          })}
        </div>
      )}

      {/* Reset Filter Button */}
      {hasActiveFilters && (
        <button
          onClick={handleReset}
          className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500/20 font-medium transition"
        >
          <RotateCcw className="w-3 h-3" />
          Reset Filters
        </button>
      )}
    </div>
  );
};
