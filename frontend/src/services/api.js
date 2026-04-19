import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("meshcloud_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("meshcloud_token");
      if (!window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

export const login = async (username, password) => {
  const body = new URLSearchParams({ username, password });
  const res = await api.post("/token", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return res.data;
};

export const register = async (username, password) => {
  const res = await api.post("/register", { username, password });
  return res.data;
};

export const fetchNodeStatus = async () => {
  try {
    const res = await api.get("/api/status");
    return res.data;
  } catch {
    return {};
  }
};

export const fetchFiles = async () => {
  try {
    const res = await api.get("/api/network/replication_map");
    return Object.entries(res.data || {}).map(([hash, info]) => ({ hash, ...info }));
  } catch {
    return [];
  }
};

export const fetchNodes = async () => {
  try {
    const res = await api.get("/api/network/graph");
    return res.data;
  } catch {
    return { nodes: [], edges: [], scores: {} };
  }
};

export const uploadFile = async (file, onProgress) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  });
};

export const downloadFile = (fileHash) => {
  const token = localStorage.getItem("meshcloud_token");
  const url = `${BASE_URL}/download/${fileHash}`;
  const a = document.createElement("a");
  a.href = token ? `${url}?token=${token}` : url;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  a.click();
};

export const addPeer = async (peerUrl) => {
  const res = await api.post("/api/peers", { url: peerUrl });
  return res.data;
};

export const getCurrentUser = async () => {
  const res = await api.get("/users/me");
  return res.data;
};

export default api;
