import { useRef, useState, useCallback } from "react";
import useFiles from "../hooks/useFiles";
import useMeshcloudStore from "../state/meshcloudStore";
import { uploadFile, downloadFile, fetchFiles } from "../services/api";
import {
  Upload,
  Download,
  FileText,
  Copy,
  Check,
  Loader2,
  CloudUpload,
  Search,
  X,
} from "lucide-react";

function ReplicationBar({ current, target }) {
  const pct = target > 0 ? Math.min(100, Math.round((current / target) * 100)) : 0;
  const color = pct >= 100 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="progress-bar flex-1 w-16">
        <div className={`progress-fill ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-500 tabular-nums w-9 text-right">
        {current}/{target}
      </span>
    </div>
  );
}

function CopyHash({ hash }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(hash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      onClick={copy}
      title="Copy hash"
      className="p-1 rounded text-slate-600 hover:text-slate-300 hover:bg-slate-700 transition-colors"
    >
      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
    </button>
  );
}

export default function Files() {
  const setFiles = useMeshcloudStore((s) => s.setFiles);
  const files = useMeshcloudStore((s) => s.files);
  useFiles();

  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadName, setUploadName] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [search, setSearch] = useState("");
  const [dragging, setDragging] = useState(false);

  const handleFiles = useCallback(
    async (selected) => {
      if (!selected.length) return;
      setUploadError("");
      setUploading(true);
      setUploadProgress(0);
      setUploadName(selected[0].name);
      try {
        for (const file of selected) {
          await uploadFile(file, setUploadProgress);
        }
        const data = await fetchFiles();
        setFiles(data);
      } catch (err) {
        setUploadError(err.response?.data?.detail || err.message || "Upload failed");
      } finally {
        setUploading(false);
        setUploadProgress(0);
        setUploadName("");
      }
    },
    [setFiles]
  );

  const onInputChange = (e) => {
    if (e.target.files?.length) handleFiles(Array.from(e.target.files));
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files?.length) handleFiles(Array.from(e.dataTransfer.files));
  };

  const filtered = files.filter(
    (f) =>
      !search ||
      f.hash?.toLowerCase().includes(search.toLowerCase()) ||
      f.filename?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="page-container overflow-y-auto flex flex-col gap-5">
      {/* Header */}
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Files</h1>
          <p className="page-subtitle">{files.length} file{files.length !== 1 ? "s" : ""} in mesh</p>
        </div>
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={onInputChange}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="btn-primary"
          >
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{uploadProgress}%</span>
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Upload
              </>
            )}
          </button>
        </div>
      </div>

      {/* Upload progress banner */}
      {uploading && (
        <div className="card-p flex items-center gap-4 border-indigo-500/30">
          <CloudUpload className="w-5 h-5 text-indigo-400 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-sm font-medium text-slate-300 truncate">{uploadName}</span>
              <span className="text-sm text-indigo-400 tabular-nums ml-3">{uploadProgress}%</span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill bg-indigo-500"
                style={{ width: `${uploadProgress}%`, transition: "width 0.2s ease" }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {uploadError && (
        <div className="flex items-center gap-2 bg-red-500/8 border border-red-500/25 text-red-400 rounded-lg px-4 py-3 text-sm">
          <X className="w-4 h-4 flex-shrink-0" />
          {uploadError}
          <button onClick={() => setUploadError("")} className="ml-auto">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Drop zone (when no files) or drag overlay */}
      {files.length === 0 && !uploading ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`flex flex-col items-center justify-center border-2 border-dashed rounded-xl py-16 cursor-pointer transition-colors ${
            dragging
              ? "border-indigo-500 bg-indigo-500/5"
              : "border-slate-800 hover:border-slate-700 hover:bg-slate-900/30"
          }`}
        >
          <CloudUpload className={`w-12 h-12 mb-3 ${dragging ? "text-indigo-400" : "text-slate-700"}`} />
          <p className="text-slate-400 font-medium">Drop files here or click to upload</p>
          <p className="text-slate-600 text-sm mt-1">Files are encrypted and distributed across the mesh</p>
        </div>
      ) : (
        <>
          {/* Search */}
          {files.length > 0 && (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600 pointer-events-none" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by filename or hash…"
                className="input pl-9"
              />
              {search && (
                <button
                  onClick={() => setSearch("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 hover:text-slate-400"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          )}

          {/* Drag overlay on table */}
          <div
            className="relative"
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
          >
            {dragging && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-indigo-500/10 border-2 border-dashed border-indigo-500 rounded-xl">
                <div className="text-center">
                  <CloudUpload className="w-10 h-10 text-indigo-400 mx-auto mb-2" />
                  <p className="text-indigo-300 font-semibold">Drop to upload</p>
                </div>
              </div>
            )}

            {/* Table */}
            <div className="card overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-900/60">
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-widest">
                      File
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-widest hidden md:table-cell">
                      Hash
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-widest hidden lg:table-cell">
                      Replication
                    </th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-widest">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="text-center py-10 text-slate-600">
                        No files match your search.
                      </td>
                    </tr>
                  ) : (
                    filtered.map((file) => (
                      <tr key={file.hash} className="table-row-hover border-b border-slate-800/50 last:border-0">
                        {/* File info */}
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-indigo-500/10 border border-indigo-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                              <FileText className="w-4 h-4 text-indigo-400" />
                            </div>
                            <div className="min-w-0">
                              <p className="font-medium text-slate-200 truncate max-w-[180px]">
                                {file.filename || "Unknown file"}
                              </p>
                              <p className="text-xs text-slate-600">
                                {file.holders?.length ?? 0} node{file.holders?.length !== 1 ? "s" : ""}
                              </p>
                            </div>
                          </div>
                        </td>

                        {/* Hash */}
                        <td className="px-4 py-3 hidden md:table-cell">
                          <div className="flex items-center gap-1">
                            <code className="text-xs text-slate-500 font-mono">
                              {file.hash.slice(0, 8)}…{file.hash.slice(-6)}
                            </code>
                            <CopyHash hash={file.hash} />
                          </div>
                        </td>

                        {/* Replication */}
                        <td className="px-4 py-3 hidden lg:table-cell">
                          <ReplicationBar
                            current={file.current ?? 0}
                            target={file.target ?? file.holders?.length ?? 1}
                          />
                        </td>

                        {/* Actions */}
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              onClick={() => downloadFile(file.hash)}
                              title="Download"
                              className="p-2 rounded-lg text-slate-500 hover:text-indigo-400 hover:bg-indigo-500/10 transition-colors"
                            >
                              <Download className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
