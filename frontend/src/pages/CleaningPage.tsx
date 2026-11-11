import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import {
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Copy,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
} from 'lucide-react';

export const CleaningPage: React.FC = () => {
  const { activeDataset, refreshDatasets, setActiveTab } = useApp();
  const [preview, setPreview] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isApplying, setIsApplying] = useState<boolean>(false);
  const [cleanedResult, setCleanedResult] = useState<any>(null);

  // User cleaning preferences
  const [removeDuplicates, setRemoveDuplicates] = useState<boolean>(true);
  const [fillNumerical, setFillNumerical] = useState<string>('mean');
  const [fillCategorical, setFillCategorical] = useState<string>('mode');
  const [dropMissingRows, setDropMissingRows] = useState<boolean>(false);

  const loadPreview = async () => {
    if (!activeDataset) return;
    try {
      setIsLoading(true);
      const res = await api.previewCleaning(activeDataset.id);
      setPreview(res);
    } catch (err) {
      console.error('Failed to preview cleaning:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPreview();
  }, [activeDataset]);

  const handleApplyCleaning = async () => {
    if (!activeDataset) return;
    try {
      setIsApplying(true);
      const res = await api.applyCleaning(activeDataset.id, {
        remove_duplicates: removeDuplicates,
        fill_numerical: fillNumerical,
        fill_categorical: fillCategorical,
        drop_missing_rows: dropMissingRows,
      });
      setCleanedResult(res);
      await refreshDatasets();
    } catch (err) {
      console.error('Failed to apply cleaning:', err);
    } finally {
      setIsApplying(false);
    }
  };

  if (!activeDataset) {
    return <div className="text-center p-12 text-slate-400">Please select an active dataset.</div>;
  }

  return (
    <div className="space-y-6">
      {/* Quality Health Overview */}
      <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <span>Automated Preprocessing & Data Quality Studio</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Active Dataset: <span className="font-semibold text-slate-200">{activeDataset.filename}</span> ({activeDataset.row_count.toLocaleString()} rows)
            </p>
          </div>
          <button
            onClick={loadPreview}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-medium text-slate-300 hover:bg-slate-800 transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Re-scan Quality</span>
          </button>
        </div>

        {/* Quality Badges */}
        {preview && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4">
              <span className="text-xs text-slate-400 font-medium">Duplicate Rows Detected</span>
              <p className="text-xl font-bold text-white mt-1">
                {preview.duplicate_rows}
                <span className="text-xs font-normal text-slate-400 ml-1.5">records</span>
              </p>
            </div>
            <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4">
              <span className="text-xs text-slate-400 font-medium">Columns with Missing Values</span>
              <p className="text-xl font-bold text-white mt-1">
                {Object.keys(preview.missing_values_by_column || {}).length}
                <span className="text-xs font-normal text-slate-400 ml-1.5">columns</span>
              </p>
            </div>
            <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4">
              <span className="text-xs text-slate-400 font-medium">Outlier Candidates</span>
              <p className="text-xl font-bold text-white mt-1">
                {Object.values(preview.outliers_by_column || {}).reduce((a: any, b: any) => a + b, 0)}
                <span className="text-xs font-normal text-slate-400 ml-1.5">data points</span>
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Issues & Cleaning Configuration Studio */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Detected Issues List */}
        <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm space-y-3">
          <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>Detected Quality Issues ({preview?.issues?.length || 0})</span>
          </h4>

          <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
            {preview?.issues?.map((issue: any, idx: number) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-slate-900/70 border border-slate-800/80 text-xs space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-amber-300 uppercase text-[10px] tracking-wider">
                    {issue.issue_type.replace('_', ' ')}
                  </span>
                  <span className="text-[10px] text-slate-400">{issue.affected_count} affected</span>
                </div>
                <p className="text-slate-300">{issue.description}</p>
                <p className="text-slate-400 italic text-[11px] pt-1">
                  Suggested Action: {issue.suggested_action}
                </p>
              </div>
            ))}
            {preview?.issues?.length === 0 && (
              <div className="p-6 text-center text-slate-400 text-xs flex flex-col items-center">
                <CheckCircle2 className="w-8 h-8 text-emerald-400 mb-2" />
                <span>No severe quality defects detected. Dataset is clean!</span>
              </div>
            )}
          </div>
        </div>

        {/* Cleaning Action Configurator */}
        <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm space-y-4">
          <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
            <span>Configure Cleaning Operations</span>
          </h4>

          <div className="space-y-3 text-xs">
            {/* Duplicates */}
            <label className="flex items-center gap-2.5 p-3 rounded-lg bg-slate-900/60 border border-slate-800 cursor-pointer">
              <input
                type="checkbox"
                checked={removeDuplicates}
                onChange={(e) => setRemoveDuplicates(e.target.checked)}
                className="w-4 h-4 rounded text-indigo-600 focus:ring-0 cursor-pointer"
              />
              <div>
                <span className="font-semibold text-slate-200">Remove Duplicate Rows</span>
                <p className="text-slate-400 text-[11px]">Deduplicates exact row repetitions.</p>
              </div>
            </label>

            {/* Numerical Imputation */}
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2">
              <span className="font-semibold text-slate-200">Missing Numerical Values:</span>
              <div className="flex items-center gap-4">
                {['mean', 'median', 'none'].map((opt) => (
                  <label key={opt} className="flex items-center gap-1.5 cursor-pointer text-slate-300">
                    <input
                      type="radio"
                      name="fill_num"
                      value={opt}
                      checked={fillNumerical === opt}
                      onChange={(e) => setFillNumerical(e.target.value)}
                      className="text-indigo-600 focus:ring-0 cursor-pointer"
                    />
                    <span className="capitalize">{opt}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Categorical Imputation */}
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2">
              <span className="font-semibold text-slate-200">Missing Categorical Values:</span>
              <div className="flex items-center gap-4">
                {['mode', 'none'].map((opt) => (
                  <label key={opt} className="flex items-center gap-1.5 cursor-pointer text-slate-300">
                    <input
                      type="radio"
                      name="fill_cat"
                      value={opt}
                      checked={fillCategorical === opt}
                      onChange={(e) => setFillCategorical(e.target.value)}
                      className="text-indigo-600 focus:ring-0 cursor-pointer"
                    />
                    <span className="capitalize">{opt}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Drop missing rows */}
            <label className="flex items-center gap-2.5 p-3 rounded-lg bg-slate-900/60 border border-slate-800 cursor-pointer">
              <input
                type="checkbox"
                checked={dropMissingRows}
                onChange={(e) => setDropMissingRows(e.target.checked)}
                className="w-4 h-4 rounded text-indigo-600 focus:ring-0 cursor-pointer"
              />
              <div>
                <span className="font-semibold text-slate-200">Drop Rows With Missing Values</span>
                <p className="text-slate-400 text-[11px]">Removes incomplete records rather than imputing.</p>
              </div>
            </label>
          </div>

          <div className="pt-2">
            <button
              onClick={handleApplyCleaning}
              disabled={isApplying}
              className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xs transition flex items-center justify-center gap-2 shadow-sm"
            >
              <Copy className="w-4 h-4" />
              <span>{isApplying ? 'Creating Cleaned Copy...' : 'Create Cleaned Copy & Activate'}</span>
            </button>
            <p className="text-[10px] text-slate-400 text-center mt-2">
              * The original uploaded dataset is never modified. A verified clean clone will be created.
            </p>
          </div>
        </div>
      </div>

      {/* Cleaning Result Confirmation Summary */}
      {cleanedResult && (
        <div className="bg-emerald-950/30 border border-emerald-800/50 rounded-xl p-5 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <span>Dataset Successfully Cleaned & Activated!</span>
            </h4>
            <button
              onClick={() => setActiveTab('dashboard')}
              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition flex items-center gap-1.5"
            >
              <span>View in Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-1">
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400">Rows Before</span>
              <p className="text-base font-bold text-white mt-0.5">{cleanedResult.rows_before}</p>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400">Rows After</span>
              <p className="text-base font-bold text-white mt-0.5">{cleanedResult.rows_after}</p>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400">Duplicates Removed</span>
              <p className="text-base font-bold text-white mt-0.5">{cleanedResult.duplicates_removed}</p>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400">Values Imputed</span>
              <p className="text-base font-bold text-white mt-0.5">{cleanedResult.missing_imputed_count}</p>
            </div>
          </div>

          <div className="text-xs text-slate-300 space-y-1 pt-1">
            {cleanedResult.summary_notes.map((note: string, idx: number) => (
              <p key={idx} className="flex items-center gap-2">
                <span className="text-emerald-400 font-bold">•</span>
                <span>{note}</span>
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
