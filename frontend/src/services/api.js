import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const fetchNodes = async () => {
  try {
    const res = await api.get("/api/network/graph");
    return res.data;
  } catch (err) {
    console.error("Failed to fetch node graph:", err);
    return { nodes: [], edges: [], scores: {} };
  }
};

export const fetchFiles = async () => {
  try {
    const res = await api.get("/api/network/replication_map");
    // The backend returns { [file_hash]: { target, current, holders, ... } }
    // Convert to array of objects with hash included
    return Object.entries(res.data).map(([hash, info]) => ({ hash, ...info }));
  } catch (err) {
    console.error("Failed to fetch files/replication map:", err);
    return [];
  }
};

export const fetchNodeStatus = async () => {
  try {
    const res = await api.get("/status");
    return res.data;
  } catch (err) {
    console.error("Failed to fetch status:", err);
    return {};
  }
};

export const uploadFile = async (file) => {
  const data = new FormData();
  data.append("file", file);
  return api.post("/upload", data, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
};

export const downloadFile = (fileHash) => {
  window.open(`${API_BASE_URL}/download/${fileHash}`, "_blank");
};

export default api;
