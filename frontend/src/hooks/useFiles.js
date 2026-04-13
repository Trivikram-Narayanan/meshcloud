import { useEffect, useState } from "react";
import { fetchFiles, uploadFile, downloadFile } from "../services/api";
import useMeshcloudStore from "../state/meshcloudStore";

export default function useFiles() {
  const [loading, setLoading] = useState(false);
  const setFiles = useMeshcloudStore((state) => state.setFiles);
  const events = useMeshcloudStore((state) => state.events);

  useEffect(() => {
    let mounted = true;
    const loadFiles = async () => {
      const data = await fetchFiles();
      if (mounted) setFiles(data);
    };

    loadFiles();
  }, [setFiles, events]);

  const handleUpload = async (file) => {
    setLoading(true);
    try {
      await uploadFile(file);
      const data = await fetchFiles();
      setFiles(data);
    } catch(err) {
      console.error(err);
      alert("Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (hash) => {
    downloadFile(hash);
  };

  return { handleUpload, handleDownload, loading };
}
