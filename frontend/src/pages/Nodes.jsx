import React from "react";
import useNodes from "../hooks/useNodes";
import useMeshcloudStore from "../state/meshcloudStore";

export default function Nodes() {
  useNodes();
  const status = useMeshcloudStore((state) => state.status);
  
  // The backend might not explicitly list all node peers without the graph endpoint.
  // We can just show generic active node info from status here.
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Active Nodes</h1>
        <p className="text-slate-400 mt-1">Manage and view peer nodes in the local mesh network.</p>
      </div>

      <div className="glass-panel p-6">
        <h2 className="text-xl font-semibold mb-4 text-slate-200">Current Node Status</h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <p className="text-slate-400 text-sm">Active Peers</p>
            <p className="text-2xl font-mono text-blue-400 mt-1">{status?.active_nodes || 0}</p>
          </div>
          <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <p className="text-slate-400 text-sm">Total Chunks Hosted</p>
            <p className="text-2xl font-mono text-indigo-400 mt-1">{status?.chunk_count || 0}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
