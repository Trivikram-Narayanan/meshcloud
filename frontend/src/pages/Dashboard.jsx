import React from "react";
import useNodes from "../hooks/useNodes";
import useMeshcloudStore from "../state/meshcloudStore";
import ThroughputChart from "../components/dashboard/ThroughputChart";
import { Server, Activity, HardDrive, Wifi } from "lucide-react";

export default function Dashboard() {
  useNodes(); // Fetch node status globally or locally
  const status = useMeshcloudStore((state) => state.status);
  
  // Example dummy data extraction if backend lacks full metrics
  const activeNodes = status?.active_nodes || 1;
  const chunkCount = status?.chunk_count || 0;
  
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-slate-400 mt-1">Overview of your MeshCloud cluster</p>
      </div>
      
      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-panel p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-400">Active Nodes</p>
              <h3 className="text-2xl font-bold mt-1 text-blue-400">{activeNodes}</h3>
            </div>
            <div className="p-3 bg-blue-500/10 rounded-lg">
              <Server className="w-6 h-6 text-blue-500" />
            </div>
          </div>
        </div>

        <div className="glass-panel p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-400">Total Chunks</p>
              <h3 className="text-2xl font-bold mt-1 text-indigo-400">{chunkCount}</h3>
            </div>
            <div className="p-3 bg-indigo-500/10 rounded-lg">
              <HardDrive className="w-6 h-6 text-indigo-500" />
            </div>
          </div>
        </div>

        <div className="glass-panel p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-400">Cluster Health</p>
              <h3 className="text-2xl font-bold mt-1 text-emerald-400">Optimal</h3>
            </div>
            <div className="p-3 bg-emerald-500/10 rounded-lg">
              <Activity className="w-6 h-6 text-emerald-500" />
            </div>
          </div>
        </div>

        <div className="glass-panel p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-400">Network Traffic</p>
              <h3 className="text-2xl font-bold mt-1 text-amber-400">~ 2.4 MB/s</h3>
            </div>
            <div className="p-3 bg-amber-500/10 rounded-lg">
              <Wifi className="w-6 h-6 text-amber-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-96">
        <div className="lg:col-span-2 glass-panel p-6 flex flex-col">
          <h3 className="text-lg font-semibold mb-4 text-slate-200">System Throughput</h3>
          <div className="flex-1 min-h-0">
             <ThroughputChart />
          </div>
        </div>
        
        <div className="glass-panel p-6 overflow-y-auto">
          <h3 className="text-lg font-semibold mb-4 text-slate-200">Recent Events</h3>
          <div className="space-y-4">
             {/* Example dummy events, hook this into events array later */}
             <div className="flex gap-3 text-sm">
                <div className="w-2 h-2 mt-1.5 rounded-full bg-blue-500 shrink-0"></div>
                <div>
                  <p className="text-slate-300">File uploaded: <span className="font-mono text-xs">design.png</span></p>
                  <p className="text-slate-500 text-xs">2 mins ago</p>
                </div>
             </div>
             <div className="flex gap-3 text-sm">
                <div className="w-2 h-2 mt-1.5 rounded-full bg-emerald-500 shrink-0"></div>
                <div>
                  <p className="text-slate-300">Node xyz joined cluster</p>
                  <p className="text-slate-500 text-xs">15 mins ago</p>
                </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
