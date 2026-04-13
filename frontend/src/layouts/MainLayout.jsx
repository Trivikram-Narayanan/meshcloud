import Sidebar from "../components/Sidebar";

export default function MainLayout({ children }) {
  return (
    <div className="App">
      {/* Background gradient layer */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950"></div>
        {/* Accent glow effects */}
        <div className="absolute top-20 left-1/3 w-72 h-72 bg-sky-500/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl"></div>
      </div>

      <div className="app-container">
        <Sidebar />
        <main className="flex-1 flex flex-col overflow-hidden">
          <div className="page-container">
            <div className="max-w-7xl mx-auto h-full">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
