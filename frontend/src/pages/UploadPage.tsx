import React, { useState, useRef, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import {
  UploadCloud,
  FileSpreadsheet,
  Check,
  Trash2,
  Database,
  ArrowRight,
  AlertCircle,
  Table,
} from 'lucide-react';

export const UploadPage: React.FC = () => {
  const { datasets, activeDataset, selectDatasetById, refreshDatasets, setActiveTab } = useApp();
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (file: File) => {
    try {
      setIsUploading(true);
      setUploadError(null);
      const res = await api.uploadDataset(file);
      await refreshDatasets();
      await loadPreview(res.id);
    } catch (err: any) {
      setUploadError(err.message || 'File upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this dataset?')) {
      await api.deleteDataset(id);
      await refreshDatasets();
      if (activeDataset?.id === id) {
        setPreviewData(null);
      }
    }
  };

  const loadPreview = async (datasetId: number) => {
    try {
      const data = await api.getPreview(datasetId, 1, 10);
      setPreviewData(data);
    } catch (err) {
      console.error('Failed to load dataset preview:', err);
    }
  };

  useEffect(() => {
    if (activeDataset) {
      loadPreview(activeDataset.id);
    }
  }, [activeDataset]);

  return (
    <div className="space-y-6">
      {/* Upload Drag & Drop Area */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center ${
          isDragging
            ? 'border-indigo-500 bg-indigo-500/10'
            : 'border-slate-800 bg-[#0f172a] hover:border-slate-700'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileUpload(e.target.files[0]);
            }
          }}
        />

        <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
          <UploadCloud className="w-7 h-7" />
        </div>

        <h3 className="text-base font-bold text-white mb-1">
          {isUploading ? 'Processing Dataset...' : 'Drag & Drop your business dataset here'}
        </h3>
        <p className="text-xs text-slate-400 max-w-sm mb-3">
          Support for CSV and Excel (.xlsx, .xls) files up to 50MB. Automatic schema understanding and column role detection.
        </p>

        <button
          type="button"
          disabled={isUploading}
          className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition"
        >
          {isUploading ? 'Uploading...' : 'Browse Computer'}
        </button>

        {uploadError && (
          <div className="mt-4 flex items-center gap-2 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3 py-1.5 rounded-lg">
            <AlertCircle className="w-4 h-4" />
            <span>{uploadError}</span>
          </div>
        )}
      </div>

      {/* Dataset History / Management Table */}
      <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-bold text-slate-100 mb-4 flex items-center gap-2">
          <Database className="w-4 h-4 text-cyan-400" />
          <span>Uploaded Datasets ({datasets.length})</span>
        </h3>

        <div className="divide-y divide-slate-800/60">
          {datasets.map((d) => {
            const isActive = activeDataset?.id === d.id;
            return (
              <div
                key={d.id}
                onClick={() => selectDatasetById(d.id)}
                className={`py-3.5 px-4 rounded-lg flex items-center justify-between cursor-pointer transition ${
                  isActive ? 'bg-indigo-950/40 border border-indigo-800/40' : 'hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                      isActive ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    <FileSpreadsheet className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-200">{d.filename}</span>
                      {d.is_cleaned && (
                        <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded font-semibold border border-emerald-500/20">
                          Cleaned Copy
                        </span>
                      )}
                      {isActive && (
                        <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full font-bold flex items-center gap-1 border border-indigo-500/30">
                          <Check className="w-2.5 h-2.5" /> Active
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {d.row_count.toLocaleString()} rows • {d.column_count} columns • {(d.file_size_bytes / 1024).toFixed(1)} KB • Uploaded {d.uploaded_at.slice(0, 10)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => handleDelete(d.id, e)}
                    title="Delete dataset"
                    className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Dataset Preview Card */}
      {previewData && (
        <div className="bg-[#0f172a] border border-slate-800/80 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Table className="w-4 h-4 text-indigo-400" />
                <span>Dataset Structure & Preview ({previewData.total_rows.toLocaleString()} rows, {previewData.total_columns} columns)</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Missing Values: <span className="text-amber-400 font-semibold">{previewData.missing_values_total}</span> • Duplicates: <span className="text-amber-400 font-semibold">{previewData.duplicate_rows_count}</span>
              </p>
            </div>
            <button
              onClick={() => setActiveTab('explorer')}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition flex items-center gap-1.5"
            >
              <span>Full Data Explorer</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Column metadata chips */}
          <div className="flex flex-wrap gap-2">
            {previewData.column_info.map((col: any) => (
              <div
                key={col.name}
                className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-[11px] flex items-center gap-2"
              >
                <span className="font-semibold text-slate-300">{col.name}</span>
                <span className="text-slate-400">({col.data_type})</span>
                {col.role_mapping && (
                  <span className="text-[9px] bg-indigo-500/20 text-indigo-300 px-1 py-0.2 rounded font-bold uppercase">
                    {col.role_mapping}
                  </span>
                )}
              </div>
            ))}
          </div>

          {/* Table Preview */}
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-xs text-left border-collapse">
              <thead className="bg-slate-900/90 text-slate-300 uppercase tracking-wider font-semibold">
                <tr>
                  {previewData.column_info.map((c: any) => (
                    <th key={c.name} className="px-3 py-2.5 whitespace-nowrap">
                      {c.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {previewData.sample_rows.map((row: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-800/50">
                    {previewData.column_info.map((c: any) => (
                      <td key={c.name} className="px-3 py-2 whitespace-nowrap">
                        {row[c.name] !== undefined && row[c.name] !== null ? String(row[c.name]) : <span className="text-slate-400 italic">null</span>}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
