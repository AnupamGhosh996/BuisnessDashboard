import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import {
  Search,
  ArrowUpDown,
  Download,
  ChevronLeft,
  ChevronRight,
  Eye,
  SlidersHorizontal,
  X,
  FileSpreadsheet,
} from 'lucide-react';

export const DataExplorerPage: React.FC = () => {
  const { activeDataset } = useApp();
  const [data, setData] = useState<any>(null);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(25);
  const [search, setSearch] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [selectedRow, setSelectedRow] = useState<any>(null);
  const [visibleColumns, setVisibleColumns] = useState<string[]>([]);
  const [showColPicker, setShowColPicker] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = async () => {
    if (!activeDataset) return;
    try {
      setIsLoading(true);
      const res = await api.getPreview(activeDataset.id, page, pageSize, search, sortBy, sortOrder);
      setData(res);
      if (visibleColumns.length === 0 && res.column_info) {
        setVisibleColumns(res.column_info.map((c: any) => c.name));
      }
    } catch (err) {
      console.error('Failed to load explorer data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeDataset, page, pageSize, sortBy, sortOrder]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadData();
  };

  const handleSort = (colName: string) => {
    if (sortBy === colName) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(colName);
      setSortOrder('asc');
    }
  };

  const exportFilteredCSV = () => {
    if (!data?.sample_rows?.length) return;
    const cols = visibleColumns;
    const header = cols.join(',');
    const rows = data.sample_rows.map((r: any) => cols.map((c) => `"${r[c] ?? ''}"`).join(','));
    const csvContent = 'data:text/csv;charset=utf-8,' + [header, ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `InsightIQ_${activeDataset?.filename || 'dataset'}_export.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!activeDataset) {
    return <div className="text-center p-12 text-slate-400">Please select an active dataset.</div>;
  }

  return (
    <div className="space-y-4">
      {/* Search, Filter, & Actions Control Bar */}
      <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search across all fields..."
              className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-200 outline-none focus:border-indigo-500 transition"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-2">
          {/* Column Visibility Selector Toggle */}
          <button
            onClick={() => setShowColPicker(!showColPicker)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs font-medium text-slate-300 hover:bg-slate-800 transition"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>Columns ({visibleColumns.length})</span>
          </button>

          {/* Export to CSV */}
          <button
            onClick={exportFilteredCSV}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs font-medium text-slate-300 hover:bg-slate-800 transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Column Visibility Dropdown Modal */}
      {showColPicker && data?.column_info && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-200">Toggle Visible Columns</span>
            <button onClick={() => setShowColPicker(false)} className="text-slate-400 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.column_info.map((col: any) => {
              const isVis = visibleColumns.includes(col.name);
              return (
                <button
                  key={col.name}
                  onClick={() => {
                    setVisibleColumns((prev) =>
                      isVis ? prev.filter((c) => c !== col.name) : [...prev, col.name]
                    );
                  }}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                    isVis
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {col.name}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Data Table */}
      <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead className="bg-slate-900 text-slate-300 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="px-3 py-3 w-10 text-center">#</th>
                {data?.column_info
                  ?.filter((c: any) => visibleColumns.includes(c.name))
                  .map((col: any) => (
                    <th
                      key={col.name}
                      onClick={() => handleSort(col.name)}
                      className="px-3 py-3 whitespace-nowrap cursor-pointer hover:text-white transition select-none"
                    >
                      <div className="flex items-center gap-1.5">
                        <span>{col.name}</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-400" />
                        {sortBy === col.name && (
                          <span className="text-[10px] text-indigo-400">
                            {sortOrder === 'asc' ? '▲' : '▼'}
                          </span>
                        )}
                      </div>
                    </th>
                  ))}
                <th className="px-3 py-3 text-center">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {isLoading ? (
                <tr>
                  <td colSpan={visibleColumns.length + 2} className="text-center py-12 text-slate-400">
                    Loading records...
                  </td>
                </tr>
              ) : data?.sample_rows?.length ? (
                data.sample_rows.map((row: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-800/50 transition">
                    <td className="px-3 py-2.5 text-center text-slate-400 font-mono text-[11px]">
                      {(page - 1) * pageSize + idx + 1}
                    </td>
                    {data.column_info
                      .filter((c: any) => visibleColumns.includes(c.name))
                      .map((c: any) => (
                        <td key={c.name} className="px-3 py-2.5 whitespace-nowrap">
                          {row[c.name] !== undefined && row[c.name] !== null ? (
                            String(row[c.name])
                          ) : (
                            <span className="text-slate-400 italic">null</span>
                          )}
                        </td>
                      ))}
                    <td className="px-3 py-2.5 text-center">
                      <button
                        onClick={() => setSelectedRow(row)}
                        title="Inspect Record"
                        className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={visibleColumns.length + 2} className="text-center py-12 text-slate-400">
                    No matching records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="px-4 py-3 bg-slate-900 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing <span className="font-semibold text-slate-200">{(page - 1) * pageSize + 1}</span> to{' '}
            <span className="font-semibold text-slate-200">
              {Math.min(page * pageSize, data?.total_rows || 0)}
            </span>{' '}
            of <span className="font-semibold text-slate-200">{(data?.total_rows || 0).toLocaleString()}</span>{' '}
            records
          </div>

          <div className="flex items-center gap-3">
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 outline-none text-xs"
            >
              <option value={10}>10 per page</option>
              <option value={25}>25 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
            </select>

            <div className="flex items-center gap-1">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-2 font-medium text-slate-300">
                Page {page} of {data?.total_pages || 1}
              </span>
              <button
                disabled={page >= (data?.total_pages || 1)}
                onClick={() => setPage((p) => p + 1)}
                className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Row Record Inspector Modal */}
      {selectedRow && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-[#0f172a] border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-cyan-400" />
                <span>Record Details</span>
              </h3>
              <button
                onClick={() => setSelectedRow(null)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2.5 max-h-[60vh] overflow-y-auto pr-1">
              {Object.entries(selectedRow).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between py-1.5 border-b border-slate-800/60 text-xs">
                  <span className="font-semibold text-slate-400">{key}:</span>
                  <span className="font-mono text-slate-200">{String(value ?? 'null')}</span>
                </div>
              ))}
            </div>

            <div className="mt-5 text-right">
              <button
                onClick={() => setSelectedRow(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
