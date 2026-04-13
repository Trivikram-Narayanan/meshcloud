import { create } from "zustand";

const useMeshcloudStore = create((set) => ({
  nodes: [],
  edges: [],
  files: [],
  status: {},
  events: [],

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  setFiles: (files) => set({ files }),
  setStatus: (status) => set({ status }),
  
  addEvent: (event) => set((state) => ({ 
    events: [event, ...state.events].slice(0, 50)  // Keep last 50 events
  })),
}));

export default useMeshcloudStore;
