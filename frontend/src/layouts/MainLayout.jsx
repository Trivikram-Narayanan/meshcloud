import { useEffect, useRef } from "react";
import Sidebar from "../components/Sidebar";
import useMeshcloudStore from "../state/meshcloudStore";

export default function MainLayout({ children }) {
  const addEvent = useMeshcloudStore((s) => s.addEvent);
  const wsRef = useRef(null);
  const reconnectRef = useRef(null);

  useEffect(() => {
    const WS_URL = (process.env.REACT_APP_API_URL || "http://localhost:8000")
      .replace(/^http/, "ws")
      .replace(/\/$/, "") + "/ws";

    const connect = () => {
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;
        ws.onmessage = (e) => {
          try { addEvent(JSON.parse(e.data)); } catch {}
        };
        ws.onclose = () => {
          reconnectRef.current = setTimeout(connect, 5000);
        };
        ws.onerror = () => ws.close();
      } catch {}
    };

    connect();
    return () => {
      clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [addEvent]);

  return (
    <div className="flex h-screen bg-[#020617] overflow-hidden">
      <Sidebar />
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">{children}</main>
    </div>
  );
}
