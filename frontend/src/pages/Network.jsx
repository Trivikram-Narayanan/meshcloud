import React from "react";
import useNetwork from "../hooks/useNetwork";
import useMeshcloudStore from "../state/meshcloudStore";
import NetworkGraph from "../components/network/NetworkGraph";

export default function Network() {
  useNetwork();
  const nodes = useMeshcloudStore((state) => state.nodes);
  const edges = useMeshcloudStore((state) => state.edges);

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Network Map</h1>
        <p className="text-slate-400 mt-1">Live representation of discovery protocol topology.</p>
      </div>

      <div className="glass-panel flex-1 min-h-[500px] p-4 relative">
        <NetworkGraph nodes={nodes} edges={edges} height="100%" />
      </div>
    </div>
  );
}
