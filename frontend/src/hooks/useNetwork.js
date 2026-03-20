import { useEffect } from "react";
import { fetchNodes } from "../services/api";
import useMeshcloudStore from "../state/meshcloudStore";

export default function useNetwork() {
  const setNodes = useMeshcloudStore((state) => state.setNodes);
  const setEdges = useMeshcloudStore((state) => state.setEdges);
  const events = useMeshcloudStore((state) => state.events);

  useEffect(() => {
    let mounted = true;
    
    const loadGraph = async () => {
      const data = await fetchNodes();
      // data: { nodes: [], edges: [], scores: {} }
      if (mounted) {
        setNodes(data.nodes || []);
        setEdges(data.edges || []);
      }
    };

    loadGraph();

    const interval = setInterval(loadGraph, 10000); // Poll purely for heartbeat topology updates

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [setNodes, setEdges, events]); 
}
