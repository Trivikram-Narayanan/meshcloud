import { useState } from "react";
import { addPeer } from "../services/api";
import useMeshcloudStore from "../state/meshcloudStore";
import {
  Copy,
  Check,
  Plus,
  Network,
  Server,
  Loader2,
  CheckCircle2,
  XCircle,
  Shield,
  Terminal,
} from "lucide-react";

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button onClick={copy} className="btn-secondary py-1.5 px-3 text-xs">
      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function Section({ title, icon: Icon, iconColor = "text-slate-400", children }) {
  return (
    <div className="card-p">
      <div className="flex items-center gap-2.5 mb-5 pb-4 border-b border-slate-800">
        <div className={`w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center ${iconColor}`}>
          <Icon className="w-4 h-4" />
        </div>
        <h2 className="font-semibold text-slate-200">{title}</h2>
      </div>
      {children}
    </div>
  );
}

export default function Settings() {
  const status = useMeshcloudStore((s) => s.status);
  const nodeUrl = status?.node_url || window.location.origin;
  const nodeId = status?.node_id || "—";

  const [peerUrl, setPeerUrl] = useState("");
  const [peerStatus, setPeerStatus] = useState(null);
  const [adding, setAdding] = useState(false);

  const handleAddPeer = async (e) => {
    e.preventDefault();
    if (!peerUrl.trim()) return;
    setAdding(true);
    setPeerStatus(null);
    try {
      await addPeer(peerUrl.trim());
      setPeerStatus({ ok: true, msg: "Peer added successfully" });
      setPeerUrl("");
    } catch (err) {
      setPeerStatus({
        ok: false,
        msg: err.response?.data?.detail || err.message || "Failed to add peer",
      });
    } finally {
      setAdding(false);
    }
  };

  const steps = [
    { n: 1, color: "bg-indigo-600", title: "Start a node", body: "Run MeshCloud on each device or server you want in the mesh." },
    { n: 2, color: "bg-violet-600", title: "Share your URL", body: "Copy the node URL above and send it to the operator of another node." },
    { n: 3, color: "bg-cyan-600", title: "Add peer", body: "Paste the other node's URL below and click Add Peer." },
    { n: 4, color: "bg-emerald-600", title: "Sync begins", body: "Nodes auto-discover each other via gossip and replicate chunks." },
  ];

  return (
    <div className="page-container overflow-y-auto">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Node configuration and network management</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Node Info */}
        <Section title="This Node" icon={Server} iconColor="text-indigo-400">
          <div className="space-y-4">
            <div>
              <p className="text-xs text-slate-600 uppercase tracking-widest mb-1.5">Node URL</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-sm text-indigo-400 font-mono bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 truncate">
                  {nodeUrl}
                </code>
                <CopyButton text={nodeUrl} />
              </div>
              <p className="text-xs text-slate-700 mt-1.5">Share with peers to join your mesh</p>
            </div>
            <div>
              <p className="text-xs text-slate-600 uppercase tracking-widest mb-1.5">Node ID</p>
              <code className="text-xs text-slate-400 font-mono bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 block break-all">
                {nodeId}
              </code>
            </div>
            {status?.peers != null && (
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-800/40 rounded-lg p-3">
                  <p className="text-[10px] text-slate-600 uppercase tracking-widest mb-0.5">Peers</p>
                  <p className="text-lg font-bold text-slate-200 tabular-nums">{status.peers}</p>
                </div>
                <div className="bg-slate-800/40 rounded-lg p-3">
                  <p className="text-[10px] text-slate-600 uppercase tracking-widest mb-0.5">Chunks</p>
                  <p className="text-lg font-bold text-slate-200 tabular-nums">{status.chunk_count ?? "—"}</p>
                </div>
              </div>
            )}
          </div>
        </Section>

        {/* Add Peer */}
        <Section title="Connect Peer" icon={Network} iconColor="text-cyan-400">
          <form onSubmit={handleAddPeer} className="space-y-3">
            <div>
              <label className="block text-xs text-slate-500 uppercase tracking-widest mb-1.5">
                Peer Node URL
              </label>
              <input
                type="url"
                value={peerUrl}
                onChange={(e) => setPeerUrl(e.target.value)}
                placeholder="http://192.168.1.x:8000"
                className="input"
                required
              />
              <p className="text-xs text-slate-700 mt-1.5">Enter the URL of another MeshCloud node</p>
            </div>
            <button
              type="submit"
              disabled={adding || !peerUrl.trim()}
              className="btn-primary w-full justify-center"
            >
              {adding ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              {adding ? "Adding…" : "Add Peer"}
            </button>
            {peerStatus && (
              <div
                className={`flex items-start gap-2.5 rounded-lg px-3 py-2.5 text-sm ${
                  peerStatus.ok
                    ? "bg-emerald-500/8 border border-emerald-500/25 text-emerald-400"
                    : "bg-red-500/8 border border-red-500/25 text-red-400"
                }`}
              >
                {peerStatus.ok ? (
                  <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                )}
                {peerStatus.msg}
              </div>
            )}
          </form>
        </Section>

        {/* How to join */}
        <Section title="How to Join a Network" icon={Shield} iconColor="text-emerald-400">
          <div className="space-y-4">
            {steps.map((s) => (
              <div key={s.n} className="flex gap-3">
                <div
                  className={`w-6 h-6 rounded-full ${s.color} flex items-center justify-center text-white text-xs font-bold flex-shrink-0 mt-0.5`}
                >
                  {s.n}
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-200">{s.title}</p>
                  <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{s.body}</p>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* Docker example */}
        <Section title="Quick Start" icon={Terminal} iconColor="text-amber-400">
          <div className="space-y-3">
            <p className="text-sm text-slate-500">Run a local multi-node mesh with Docker:</p>
            <pre className="bg-slate-950 border border-slate-800 rounded-lg p-4 text-xs text-slate-400 font-mono overflow-x-auto leading-relaxed">
{`# Start all nodes
docker-compose up -d

# Node 1: http://localhost:8001
# Node 2: http://localhost:8002
# Node 3: http://localhost:8003

# Add node 1 as peer from node 2:
# URL → http://node1:8000

# Nodes auto-discover via UDP gossip`}
            </pre>
            <p className="text-xs text-slate-600">
              Or use{" "}
              <code className="text-slate-500">./start_mesh.sh</code>{" "}
              for a local mesh on ports 8000–8002.
            </p>
          </div>
        </Section>
      </div>
    </div>
  );
}
