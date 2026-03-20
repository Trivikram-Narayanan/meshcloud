import React, { useEffect, useRef } from "react";
import cytoscape from "cytoscape";

export default function NetworkGraph({ nodes = [], edges = [], height = "500px" }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Transform raw nodes into cytoscape elements
    const cyNodes = nodes.map((n) => ({
      data: { 
        id: n.id, 
        label: n.name || n.id.substring(0, 8),
        status: n.status || "active"
      }
    }));

    const cyEdges = edges.map((e, idx) => ({
      data: { 
        id: `e${idx}`, 
        source: e.source, 
        target: e.target 
      }
    }));

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: [...cyNodes, ...cyEdges],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#3b82f6', // blue-500
            'label': 'data(label)',
            'color': '#cbd5e1', // slate-300
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 8,
            'font-family': 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
            'font-size': '12px',
            'width': 24,
            'height': 24,
            'border-width': 2,
            'border-color': '#60a5fa', // blue-400
            'border-opacity': 0.8,
            'shadow-blur': 15,
            'shadow-color': '#3b82f6',
            'shadow-opacity': 0.5
          }
        },
        {
          selector: 'node[status = "dead"]',
          style: {
            'background-color': '#ef4444', // red-500
            'border-color': '#f87171',
            'shadow-color': '#ef4444'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#475569', // slate-600
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'opacity': 0.6
          }
        }
      ],
      layout: {
        name: 'cose',
        padding: 50,
        animate: true,
        animationDuration: 300,
        randomize: false
      },
      userZoomingEnabled: false,
      userPanningEnabled: false,
    });

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [nodes, edges]);

  return (
    <div 
      ref={containerRef} 
      className="w-full rounded-xl"
      style={{ height }} 
    />
  );
}
