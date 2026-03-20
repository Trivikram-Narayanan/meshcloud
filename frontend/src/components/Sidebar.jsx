import { Link, useLocation } from "react-router-dom";
import { Activity, HardDrive, Network, Settings, LayoutDashboard } from "lucide-react";

export default function Sidebar() {
  const location = useLocation();
  
  const navItems = [
    { name: "Dashboard", path: "/", icon: LayoutDashboard },
    { name: "Nodes", path: "/nodes", icon: Activity },
    { name: "Files", path: "/files", icon: HardDrive },
    { name: "Network", path: "/network", icon: Network },
    { name: "Settings", path: "/settings", icon: Settings },
  ];

  return (
    <div className="w-64 bg-slate-900 border-r border-slate-800 text-white min-h-screen p-6 flex flex-col shadow-2xl">
      <div className="flex items-center gap-3 mb-10">
        <Network className="w-8 h-8 text-blue-500" />
        <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
          MeshCloud
        </h2>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                isActive 
                  ? "bg-blue-600/20 text-blue-400 border border-blue-500/30 font-medium shadow-[0_0_15px_rgba(59,130,246,0.1)]" 
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? "text-blue-400" : "text-slate-500"}`} />
              {item.name}
            </Link>
          );
        })}
      </nav>
      
      <div className="mt-auto pt-8 border-t border-slate-800/50">
        <div className="text-xs text-slate-500 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
          Cluster Online
        </div>
      </div>
    </div>
  );
}
