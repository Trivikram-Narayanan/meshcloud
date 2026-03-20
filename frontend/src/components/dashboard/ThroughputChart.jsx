import React from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend
);

export default function ThroughputChart({ data, title = "System Throughput" }) {
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        mode: "index",
        intersect: false,
        backgroundColor: "rgba(15, 23, 42, 0.9)", // slate-900
        titleColor: "#f8fafc",
        bodyColor: "#cbd5e1",
        borderColor: "rgba(51, 65, 85, 0.5)",
        borderWidth: 1,
        padding: 10,
        displayColors: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: "rgba(51, 65, 85, 0.2)", // slate-700
          drawBorder: false,
        },
        ticks: {
          color: "#64748b", // slate-500
          maxTicksLimit: 6,
        },
      },
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: "#64748b",
          maxTicksLimit: 8,
        },
      },
    },
    interaction: {
      mode: "nearest",
      axis: "x",
      intersect: false,
    },
    elements: {
      point: {
        radius: 0,
        hitRadius: 10,
        hoverRadius: 4,
      },
      line: {
        tension: 0.4, // smooth curves
      },
    },
  };

  // Generate generic empty data if none provided
  const chartData = {
    labels: data?.time || ["10s", "8s", "6s", "4s", "2s", "Now"],
    datasets: [
      {
        label: title,
        data: data?.values || [0, 5, 2, 8, 15, 12],
        borderColor: "#3b82f6", // blue-500
        backgroundColor: "rgba(59, 130, 246, 0.1)", // blue-500 w/ opacity
        fill: true,
        borderWidth: 2,
      },
    ],
  };

  return (
    <div className="h-full w-full">
      <Line options={options} data={chartData} />
    </div>
  );
}
