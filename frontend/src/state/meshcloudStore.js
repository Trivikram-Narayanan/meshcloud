import { create } from "zustand";

const useMeshcloudStore = create((set) => ({
  nodes: [],
  edges: [],
  files: [],
  status: {},
  events: [],
  token: localStorage.getItem("meshcloud_token") || null,
  user: null,

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  setFiles: (files) => set({ files }),
  setStatus: (status) => set({ status }),

  addEvent: (event) =>
    set((state) => ({
      events: [{ ...event, id: Date.now() }, ...state.events].slice(0, 100),
    })),

  setToken: (token) => {
    if (token) localStorage.setItem("meshcloud_token", token);
    else localStorage.removeItem("meshcloud_token");
    set({ token });
  },

  setUser: (user) => set({ user }),

  logout: () => {
    localStorage.removeItem("meshcloud_token");
    set({ token: null, user: null, nodes: [], edges: [], files: [], status: {}, events: [] });
  },
}));

export default useMeshcloudStore;
