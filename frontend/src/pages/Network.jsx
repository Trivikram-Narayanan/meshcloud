import useNetwork from "../hooks/useNetwork";
import useMeshcloudStore from "../state/meshcloudStore";
import NetworkGraph from "../components/network/NetworkGraph";
import { Network as NetworkIcon, Server, Link2 } from "lucide-react";

export default function Network() {
  useNetwork();
  const nodes = useMeshcloudStore((s) => s.nodes);
  const edges = useMeshcloudStore((s) => s.edges);

  // Cytoscape elements: { data: { id, label, status, type, file_count } }
  const alive = nodes.filter((n) => (n.data || n).status === "alive").length;
  const self = nodes.find((n) => (n.data || n).type === "self");
  const selfData = self?.data || self;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/60 flex-shrink-0">
        <div>
          <h1 className="page-title">Network</h1>
          <p className="page-subtitle">Live mesh topology</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs">
            <Server className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-400 tabular-nums">{nodes.length} nodes</span>
          </div>
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs">
            <Link2 className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-400 tabular-nums">{edges.length} links</span>
          </div>
          <div className="flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-1.5 text-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 pulse-dot" />
            <span className="text-emerald-400">{alive} alive</span>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        {/* Graph */}
        <div className="flex-1 relative bg-[#020617]">
          {nodes.length === 0 ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
              <NetworkIcon className="w-16 h-16 text-slate-800 mb-4" />
              <p className="text-slate-500 font-medium">No network data yet</p>
              <p className="text-slate-700 text-sm mt-1">Connect peers to see the topology</p>
            </div>
          ) : (
            <NetworkGraph nodes={nodes} edges={edges} height="100%" />
          )}
        </div>

        {/* Side panel */}
        {nodes.length > 0 && (
          <div className="w-52 flex-shrink-0 border-l border-slate-800/60 bg-slate-950 overflow-y-auto">
            <div className="px-3 py-2.5 border-b border-slate-800/60">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest">Nodes</p>
            </div>
            <div className="p-2 space-y-0.5">
              {nodes.map((nodeEl, i) => {
                const d = nodeEl.data || nodeEl;
                return (
                  <div
                    key={d.id || i}
                    className="flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-slate-900 transition-colors"
                  >
                    <span
                      className={`w-2 h-2 rounded-full flex-shrink-0 ${
                        d.status === "alive" ? "bg-emerald-500" : "bg-slate-700"
                      }`}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium text-slate-300 truncate">
                        {d.label || d.id}
                      </p>
                      {d.file_count != null && (
                        <p className="text-[10px] text-slate-600">{d.file_count} files</p>
                      )}
                    </div>
                    {d.type === "self" && (
                      <span className="text-[10px] text-indigo-400 font-semibold flex-shrink-0">you</span>
                    )}
                  </div>
                );
              })}
            </div>

            {selfData && (
              <div className="p-3 border-t border-slate-800/60 mt-1">
                <p className="text-[10px] text-slate-600 uppercase tracking-widest mb-1">This node</p>
                <code className="text-[10px] text-indigo-400 font-mono break-all leading-relaxed">
                  {selfData.id}
                </code>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
