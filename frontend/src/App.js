import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Nodes from "./pages/Nodes";
import Files from "./pages/Files";
import Network from "./pages/Network";
import Settings from "./pages/Settings";
import useMeshcloudStore from "./state/meshcloudStore";

function PrivateRoute({ children }) {
  const token = useMeshcloudStore((s) => s.token);
  return token ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <PrivateRoute>
              <MainLayout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/nodes" element={<Nodes />} />
                  <Route path="/files" element={<Files />} />
                  <Route path="/network" element={<Network />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </MainLayout>
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
