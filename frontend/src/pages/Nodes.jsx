import useNodes from "../hooks/useNodes";
import useNetwork from "../hooks/useNetwork";
import useMeshcloudStore from "../state/meshcloudStore";
import { Server, Cpu, Database, Wifi, Clock, Star } from "lucide-react";

function ProgressBar({ value, color = "bg-indigo-500" }) {
  const pct = Math.min(100, Math.max(0, value || 0));
  const barColor = pct > 85 ? "bg-red-500" : pct > 60 ? "bg-amber-500" : color;
  return (
    <div className="flex items-center gap-2">
      <div className="progress-bar flex-1">
        <div className={`progress-fill ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-500 tabular-nums w-9 text-right">{Math.round(pct)}%</span>
    </div>
  );
}

function formatUptime(s) {
  if (!s) return "—";
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

function ThisNodeCard({ status }) {
  const cpu = status?.metrics?.cpu_usage ?? null;
  const mem = status?.metrics?.memory_usage ?? null;
  const memUsed = status?.metrics?.memory_used_mb;
  const memTotal = status?.metrics?.memory_total_mb;

  return (
    <div className="card-p border-indigo-500/20 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-600/5 rounded-full blur-2xl pointer-events-none" />
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 bg-indigo-600/20 border border-indigo-500/30 rounded-xl flex items-center justify-center">
            <Star className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <p className="font-semibold text-slate-200">This Node</p>
            <p className="text-xs text-slate-500 font-mono">
              {status?.node_id ? status.node_id.slice(0, 18) + "…" : "—"}
            </p>
          </div>
        </div>
        <span className="badge badge-green">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          Online
        </span>
      </div>

      <div className="space-y-3">
        {status?.node_url && (
          <div>
            <p className="text-xs text-slate-600 mb-1">URL</p>
            <code className="text-xs text-indigo-400 font-mono break-all">{status.node_url}</code>
          </div>
        )}

        <div className="grid grid-cols-3 gap-3 pt-1">
          <div className="bg-slate-800/50 rounded-lg p-2.5 text-center">
            <Wifi className="w-4 h-4 text-cyan-400 mx-auto mb-1" />
            <p className="text-lg font-bold text-slate-100 tabular-nums">{status?.peers ?? "—"}</p>
            <p className="text-[10px] text-slate-600 uppercase tracking-widest">Peers</p>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-2.5 text-center">
            <Database className="w-4 h-4 text-indigo-400 mx-auto mb-1" />
            <p className="text-lg font-bold text-slate-100 tabular-nums">{status?.chunk_count ?? "—"}</p>
            <p className="text-[10px] text-slate-600 uppercase tracking-widest">Chunks</p>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-2.5 text-center">
            <Clock className="w-4 h-4 text-amber-400 mx-auto mb-1" />
            <p className="text-lg font-bold text-slate-100">{formatUptime(status?.metrics?.uptime)}</p>
            <p className="text-[10px] text-slate-600 uppercase tracking-widest">Uptime</p>
          </div>
        </div>

        {cpu != null && (
          <div>
            <span className="text-xs text-slate-500 flex items-center gap-1 mb-1">
              <Cpu className="w-3 h-3" /> CPU
            </span>
            <ProgressBar value={cpu} color="bg-cyan-500" />
          </div>
        )}

        {mem != null && (
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-slate-500">Memory</span>
              {memUsed && memTotal && (
                <span className="text-xs text-slate-600">
                  {Math.round(memUsed)} / {Math.round(memTotal)} MB
                </span>
              )}
            </div>
            <ProgressBar value={mem} color="bg-violet-500" />
          </div>
        )}
      </div>
    </div>
  );
}

function PeerCard({ nodeEl }) {
  // Cytoscape elements have shape { data: { id, label, status, type, score, file_count } }
  const d = nodeEl.data || nodeEl;
  const isAlive = d.status === "alive";
  const score = d.score ?? 0;

  return (
    <div className="card-p">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              isAlive
                ? "bg-emerald-500/10 border border-emerald-500/20"
                : "bg-slate-800 border border-slate-700"
            }`}
          >
            <Server className={`w-4 h-4 ${isAlive ? "text-emerald-400" : "text-slate-600"}`} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-slate-200 truncate max-w-[140px]">
              {d.label || d.id}
            </p>
            <p className="text-xs text-slate-600 truncate max-w-[140px] font-mono">
              {String(d.id).length > 22 ? String(d.id).slice(0, 22) + "…" : d.id}
            </p>
          </div>
        </div>
        <span className={isAlive ? "badge badge-green" : "badge badge-gray"}>
          {isAlive ? "Online" : "Unknown"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs mb-3">
        <div className="bg-slate-800/40 rounded p-2">
          <p className="text-slate-600 mb-0.5">Files</p>
          <p className="text-slate-300 font-semibold tabular-nums">{d.file_count ?? "—"}</p>
        </div>
        <div className="bg-slate-800/40 rounded p-2">
          <p className="text-slate-600 mb-0.5">Score</p>
          <p className="text-slate-300 font-semibold tabular-nums">{Math.round(score)}</p>
        </div>
      </div>

      <div>
        <p className="text-[10px] text-slate-700 mb-1 uppercase tracking-widest">Health</p>
        <div className="progress-bar">
          <div
            className={`progress-fill ${
              score > 70 ? "bg-emerald-500" : score > 30 ? "bg-amber-500" : "bg-red-500"
            }`}
            style={{ width: `${score}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export default function Nodes() {
  useNodes();
  useNetwork();

  const status = useMeshcloudStore((s) => s.status);
  const graphNodes = useMeshcloudStore((s) => s.nodes);

  // graphNodes are cytoscape elements: { data: { type, ... } }
  const peers = graphNodes.filter((n) => (n.data || n).type !== "self");

  return (
    <div className="page-container overflow-y-auto">
      <div className="page-header">
        <h1 className="page-title">Nodes</h1>
        <p className="page-subtitle">
          {status?.peers ?? 0} peer{status?.peers !== 1 ? "s" : ""} connected
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <ThisNodeCard status={status} />

        {peers.length === 0 ? (
          <div className="md:col-span-1 xl:col-span-2 card-p flex flex-col items-center justify-center py-12 text-center">
            <Server className="w-10 h-10 text-slate-800 mb-3" />
            <p className="text-slate-500 font-medium">No peer nodes discovered yet</p>
            <p className="text-slate-700 text-sm mt-1">Add peers in Settings to expand the mesh</p>
          </div>
        ) : (
          peers.map((nodeEl, i) => <PeerCard key={(nodeEl.data || nodeEl).id || i} nodeEl={nodeEl} />)
        )}
      </div>
    </div>
  );
}
