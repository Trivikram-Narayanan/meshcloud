import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Layers, User, Lock, AlertCircle, ArrowRight, Loader2 } from "lucide-react";
import { login, register } from "../services/api";
import api from "../services/api";
import useMeshcloudStore from "../state/meshcloudStore";

export default function Login() {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [firstRun, setFirstRun] = useState(false);
  const setToken = useMeshcloudStore((s) => s.setToken);
  const token = useMeshcloudStore((s) => s.token);
  const navigate = useNavigate();

  useEffect(() => {
    if (token) navigate("/", { replace: true });
  }, [token, navigate]);

  useEffect(() => {
    api.get("/api/setup/status").then((res) => {
      if (!res.data.has_users) {
        setMode("register");
        setFirstRun(true);
      }
    }).catch(() => {});
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "register") {
        await register(username, password);
      }
      const data = await login(username, password);
      setToken(data.access_token);
      navigate("/", { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
          ? detail.map((d) => d.msg).join(", ")
          : mode === "login"
          ? "Invalid username or password"
          : "Registration failed. Username may already exist."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/3 w-[500px] h-[500px] bg-indigo-600/8 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/3 w-[400px] h-[400px] bg-violet-600/8 rounded-full blur-3xl" />
        <div
          className="absolute inset-0 opacity-[0.015]"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, rgb(148 163 184) 1px, transparent 0)",
            backgroundSize: "32px 32px",
          }}
        />
      </div>

      <div className="relative w-full max-w-[400px]">
        {/* Branding */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-indigo-600/20 border border-indigo-500/30 rounded-2xl mb-4 shadow-lg shadow-indigo-900/20">
            <Layers className="w-7 h-7 text-indigo-400" />
          </div>
          <h1 className="text-2xl font-bold text-slate-50 tracking-tight">MeshCloud</h1>
          <p className="text-slate-500 text-sm mt-1">Distributed file storage for local networks</p>
        </div>

        {/* Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-7 shadow-2xl">
          {/* First-run welcome banner */}
          {firstRun && (
            <div className="flex items-start gap-2.5 bg-indigo-500/10 border border-indigo-500/25 text-indigo-300 rounded-lg px-3 py-2.5 text-sm mb-5">
              <Layers className="w-4 h-4 mt-0.5 shrink-0" />
              <span>Welcome! Create your first account to get started.</span>
            </div>
          )}

          {/* Mode tabs */}
          <div className="flex bg-slate-800/60 border border-slate-700/50 rounded-lg p-1 mb-6">
            <button
              type="button"
              onClick={() => { setMode("login"); setError(""); }}
              className={`flex-1 py-1.5 rounded-md text-sm font-medium transition-all duration-200 ${
                mode === "login"
                  ? "bg-slate-700 text-slate-100 shadow-sm"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setMode("register"); setError(""); }}
              className={`flex-1 py-1.5 rounded-md text-sm font-medium transition-all duration-200 ${
                mode === "register"
                  ? "bg-slate-700 text-slate-100 shadow-sm"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter username"
                  required
                  autoFocus
                  className="input pl-9"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  required
                  className="input pl-9"
                />
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-start gap-2.5 bg-red-500/8 border border-red-500/25 text-red-400 rounded-lg px-3 py-2.5 text-sm">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading || !username || !password}
              className="btn-primary w-full justify-center py-2.5 mt-1"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  {mode === "login" ? "Sign In" : "Create Account"}
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-slate-600 text-xs mt-6">
          MeshCloud v0.2.0 — Self-hosted distributed storage
        </p>
      </div>
    </div>
  );
}
