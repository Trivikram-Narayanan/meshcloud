import React, { useRef } from "react";
import useFiles from "../hooks/useFiles";
import useMeshcloudStore from "../state/meshcloudStore";
import { Upload, Download, FileText } from "lucide-react";

export default function Files() {
  const { handleUpload, handleDownload, loading } = useFiles();
  const files = useMeshcloudStore((state) => state.files);
  const fileInputRef = useRef(null);

  const onFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleUpload(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Files</h1>
          <p className="text-slate-400 mt-1">Distributed filesystem storage</p>
        </div>
        
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={onFileSelect} 
          className="hidden" 
        />
        <button 
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          <Upload className="w-5 h-5" />
          {loading ? "Uploading..." : "Upload File"}
        </button>
      </div>

      <div className="glass-panel overflow-hidden">
        <ul className="divide-y divide-slate-800">
          {files.length === 0 ? (
            <li className="p-8 text-center text-slate-500">
              No files replicated yet.
            </li>
          ) : (
            files.map((file, idx) => (
              <li key={idx} className="p-4 hover:bg-slate-800/30 transition-colors flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-indigo-500/10 rounded-lg">
                    <FileText className="w-6 h-6 text-indigo-400" />
                  </div>
                  <div>
                    <h4 className="font-medium text-slate-200">
                       {file.hash.substring(0, 16)}...
                    </h4>
                    <p className="text-sm text-slate-500">
                       Holders: {file.holders?.length || 0} / Current: {file.current || 0}
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => handleDownload(file.hash)}
                  className="p-2 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"
                  title="Download File"
                >
                  <Download className="w-5 h-5" />
                </button>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}
