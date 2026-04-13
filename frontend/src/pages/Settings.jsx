import React from "react";

export default function Settings() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-slate-400 mt-1">Configure your MeshCloud node and preferences.</p>
      </div>

      <div className="glass-panel p-6 max-w-2xl">
        <h3 className="text-lg font-semibold mb-4 text-slate-200">Network Preferences</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">API Base URL</label>
            <input 
              type="text" 
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              defaultValue="http://localhost:8000"
              disabled
            />
            <p className="text-xs text-slate-500 mt-1">Configured via environment variables.</p>
          </div>
          
          <div>
             <label className="block text-sm font-medium text-slate-400 mb-1">Theme</label>
             <select className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors">
                <option value="dark">Dark Theme (Default)</option>
             </select>
          </div>
        </div>
      </div>
    </div>
  );
}
