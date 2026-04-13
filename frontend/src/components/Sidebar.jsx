import { Link, useLocation } from "react-router-dom";
import { Activity, HardDrive, Network, Settings, LayoutDashboard, Zap } from "lucide-react";

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
    <div className="app-sidebar">
      {/* Logo section */}
      <div className="px-6 mb-8 pb-6 border-b border-slate-700/50">
        <div className="flex items-center gap-2.5 mb-2">
          <div className="p-1.5 bg-sky-600/20 rounded-lg">
            <Network className="w-5 h-5 text-sky-500" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-50 tracking-tight">MeshCloud</h1>
            <p className="text-xs text-slate-400 font-medium">Distributed Storage</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav px-3">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span className="flex-1 text-sm font-medium">{item.name}</span>
              {isActive && (
                <Zap className="w-4 h-4 text-sky-500 opacity-60" />
              )}
            </Link>
          );
        })}
      </nav>
      
      {/* Status indicator */}
      <div className="px-6 mt-auto pt-8 border-t border-slate-700/50">
        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/30">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse mr-1.5"></div>
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" style={{ animationDelay: '0.3s' }}></div>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-slate-200">Online</p>
              <p className="text-xs text-slate-400">Mesh Active</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
