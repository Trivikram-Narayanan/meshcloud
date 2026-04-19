import useNodes from "../hooks/useNodes";
import useFiles from "../hooks/useFiles";
import useMeshcloudStore from "../state/meshcloudStore";
import ThroughputChart from "../components/dashboard/ThroughputChart";
import { Server, HardDrive, Cpu, MemoryStick, Activity, Clock } from "lucide-react";

function StatCard({ label, value, sub, icon: Icon, iconColor, trend }) {
  return (
    <div className="stat-card flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-widest">{label}</span>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${iconColor}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div>
        <p className="text-3xl font-bold text-slate-50 tabular-nums">{value}</p>
        {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
      </div>
      {trend != null && (
        <div className="progress-bar">
          <div
            className="progress-fill bg-indigo-500"
            style={{ width: `${Math.min(100, trend)}%` }}
          />
        </div>
      )}
    </div>
  );
}

function EventItem({ event }) {
  const typeConfig = {
    node_joined: { dot: "bg-emerald-500", label: "Node joined" },
    node_left: { dot: "bg-red-500", label: "Node left" },
    chunk_uploaded: { dot: "bg-indigo-500", label: "Chunk stored" },
    sync: { dot: "bg-amber-500", label: "Sync" },
  };
  const cfg = typeConfig[event.type] || { dot: "bg-slate-600", label: event.type || "Event" };
  const time = event.timestamp
    ? new Date(event.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : "";

  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-slate-800/60 last:border-0">
      <span className={`w-2 h-2 rounded-full mt-1 flex-shrink-0 ${cfg.dot}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-300 font-medium truncate">{cfg.label}</p>
        {event.node && (
          <p className="text-xs text-slate-600 truncate">{event.node}</p>
        )}
      </div>
      {time && <span className="text-xs text-slate-600 flex-shrink-0 tabular-nums">{time}</span>}
    </div>
  );
}

function formatUptime(seconds) {
  if (!seconds) return "—";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export default function Dashboard() {
  useNodes();
  useFiles();

  const status = useMeshcloudStore((s) => s.status);
  const events = useMeshcloudStore((s) => s.events);
  const files = useMeshcloudStore((s) => s.files);

  const peers = status?.peers ?? "—";
  const chunks = status?.chunk_count ?? "—";
  const cpu = status?.metrics?.cpu_usage != null ? Math.round(status.metrics.cpu_usage) : null;
  const mem = status?.metrics?.memory_usage != null ? Math.round(status.metrics.memory_usage) : null;
  const memUsed = status?.metrics?.memory_used_mb;
  const memTotal = status?.metrics?.memory_total_mb;
  const uptime = status?.metrics?.uptime;

  return (
    <div className="page-container overflow-y-auto">
      {/* Header */}
      <div className="page-header flex items-start justify-between">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle flex items-center gap-2">
            {status?.node_id ? (
              <>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
                <span className="font-mono">{status.node_id.slice(0, 16)}…</span>
                <span className="text-slate-700">·</span>
                <Clock className="w-3 h-3" />
                <span>{formatUptime(uptime)}</span>
              </>
            ) : (
              <span>Connecting to node…</span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
          <Activity className="w-3.5 h-3.5 text-emerald-500" />
          <span>Live</span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          label="Files"
          value={files.length}
          sub="distributed files"
          icon={HardDrive}
          iconColor="bg-indigo-500/15 text-indigo-400"
        />
        <StatCard
          label="Nodes"
          value={peers}
          sub="active peers"
          icon={Server}
          iconColor="bg-cyan-500/15 text-cyan-400"
        />
        <StatCard
          label="CPU"
          value={cpu != null ? `${cpu}%` : "—"}
          sub="processor load"
          icon={Cpu}
          iconColor="bg-emerald-500/15 text-emerald-400"
          trend={cpu}
        />
        <StatCard
          label="Memory"
          value={mem != null ? `${mem}%` : "—"}
          sub={memUsed && memTotal ? `${Math.round(memUsed)}/${Math.round(memTotal)} MB` : "RAM usage"}
          icon={MemoryStick}
          iconColor="bg-amber-500/15 text-amber-400"
          trend={mem}
        />
      </div>

      {/* Chart + Events */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Throughput chart */}
        <div className="lg:col-span-2 card-p">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-semibold text-slate-300">Network Throughput</p>
            <span className="badge badge-blue">Live</span>
          </div>
          <div style={{ height: 220 }}>
            <ThroughputChart />
          </div>
        </div>

        {/* Event log */}
        <div className="card-p flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-semibold text-slate-300">Live Events</p>
            {events.length > 0 && (
              <span className="badge badge-gray">{events.length}</span>
            )}
          </div>
          <div className="flex-1 overflow-y-auto" style={{ maxHeight: 260 }}>
            {events.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-8">
                <Activity className="w-8 h-8 text-slate-700 mb-2" />
                <p className="text-sm text-slate-600">Waiting for events…</p>
              </div>
            ) : (
              events.map((ev) => <EventItem key={ev.id} event={ev} />)
            )}
          </div>
        </div>
      </div>

      {/* Node details row */}
      {status?.node_url && (
        <div className="card-p mt-4 flex flex-wrap gap-6">
          <div>
            <p className="text-xs text-slate-600 uppercase tracking-widest mb-1">Node URL</p>
            <code className="text-sm text-indigo-400 font-mono">{status.node_url}</code>
          </div>
          <div>
            <p className="text-xs text-slate-600 uppercase tracking-widest mb-1">Chunks Stored</p>
            <p className="text-sm text-slate-300 font-semibold tabular-nums">{chunks}</p>
          </div>
          {status?.disk_used_gb != null && (
            <div>
              <p className="text-xs text-slate-600 uppercase tracking-widest mb-1">Disk Used</p>
              <p className="text-sm text-slate-300 font-semibold">{status.disk_used_gb.toFixed(1)} GB</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
