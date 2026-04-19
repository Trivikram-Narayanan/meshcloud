import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  HardDrive,
  Server,
  Network,
  Settings,
  Layers,
  LogOut,
} from "lucide-react";
import useMeshcloudStore from "../state/meshcloudStore";

const NAV = [
  { name: "Dashboard", path: "/", icon: LayoutDashboard },
  { name: "Files", path: "/files", icon: HardDrive },
  { name: "Nodes", path: "/nodes", icon: Server },
  { name: "Network", path: "/network", icon: Network },
  { name: "Settings", path: "/settings", icon: Settings },
];

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const logout = useMeshcloudStore((s) => s.logout);
  const status = useMeshcloudStore((s) => s.status);
  const isOnline = !!status?.node_id;

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <aside className="w-[220px] flex-shrink-0 flex flex-col bg-slate-950 border-r border-slate-800/60 h-full">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 py-5 border-b border-slate-800/60">
        <div className="w-8 h-8 bg-indigo-600/20 border border-indigo-500/30 rounded-lg flex items-center justify-center flex-shrink-0">
          <Layers className="w-4 h-4 text-indigo-400" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-bold text-slate-100 leading-none">MeshCloud</p>
          <p className="text-[10px] text-slate-500 mt-0.5 truncate">
            {status?.node_id ? status.node_id.slice(0, 14) + "…" : "Connecting…"}
          </p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {NAV.map(({ name, path, icon: Icon }) => {
          const active = location.pathname === path;
          return (
            <Link
              key={path}
              to={path}
              className={active ? "nav-item-active" : "nav-item"}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-2 pb-3 border-t border-slate-800/60 pt-3 space-y-2">
        {/* Status pill */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-900 border border-slate-800">
          <span
            className={`w-2 h-2 rounded-full flex-shrink-0 ${
              isOnline ? "bg-emerald-500 pulse-dot" : "bg-slate-600"
            }`}
          />
          <span className={`text-xs font-medium ${isOnline ? "text-emerald-400" : "text-slate-500"}`}>
            {isOnline ? "Mesh Active" : "Connecting"}
          </span>
          {status?.peers != null && (
            <span className="ml-auto text-xs text-slate-500">{status.peers}p</span>
          )}
        </div>

        {/* Logout */}
        <button onClick={handleLogout} className="nav-item w-full text-red-500/70 hover:text-red-400 hover:bg-red-500/5">
          <LogOut className="w-4 h-4 flex-shrink-0" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
