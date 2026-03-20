import useMeshcloudStore from "../state/meshcloudStore";

let socket = null;

export const connectWebSocket = (wsUrl) => {
  if (socket) return socket;

  // Ensure robust WebSocket reconnect logic
  const WEBSOCKET_URL = wsUrl || "ws://localhost:8000/ws";

  socket = new WebSocket(WEBSOCKET_URL);

  socket.onopen = () => {
    console.log("WebSocket connected to", WEBSOCKET_URL);
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log("Live Event:", data);

      const store = useMeshcloudStore.getState();

      switch (data.type) {
        case "node_joined":
        case "node_left":
        case "chunk_uploaded":
        case "sync":
          // Signal store that an update occurred so hooks can refresh API
          store.addEvent(data);
          break;
        default:
          store.addEvent(data);
          break;
      }
    } catch (err) {
      console.error("Failed to parse websocket message", err);
    }
  };

  socket.onerror = (err) => {
    console.error("WebSocket Error:", err);
  };

  socket.onclose = () => {
    console.log("WebSocket closed. Reconnecting in 5s...");
    socket = null;
    setTimeout(() => connectWebSocket(WEBSOCKET_URL), 5000);
  };

  return socket;
};

export const getSocket = () => socket;
export default connectWebSocket;
