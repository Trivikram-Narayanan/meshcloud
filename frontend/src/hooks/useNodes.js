import { useEffect } from "react";
import { fetchNodeStatus } from "../services/api";
import useMeshcloudStore from "../state/meshcloudStore";

export default function useNodes() {
  const setStatus = useMeshcloudStore((state) => state.setStatus);
  const events = useMeshcloudStore((state) => state.events); // Re-fetch when events occur

  useEffect(() => {
    let mounted = true;
    
    // Poll every 5s or just fetch on load/event
    const loadStatus = async () => {
      const data = await fetchNodeStatus();
      if (mounted) setStatus(data);
    };

    loadStatus();

    const interval = setInterval(loadStatus, 5000); // Polling as a fallback for metrics

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [setStatus, events]);
}
