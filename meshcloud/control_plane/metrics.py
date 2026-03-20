"""Monitoring and metrics collection for MeshCloud."""
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import psutil
from fastapi import APIRouter, Depends

from meshcloud.security.auth import User
from meshcloud.security.dependencies import get_current_user_db


class MetricsCollector:
    """Collect and manage application metrics."""

    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.request_duration = 0.0
        self.error_count = 0
        self.file_operations = defaultdict(int)
        self.chunk_operations = defaultdict(int)
        self.sync_operations = defaultdict(int)

        # Recent request history (last 1000 requests)
        self.recent_requests = deque(maxlen=1000)
        self.recent_errors = deque(maxlen=100)

        # Lock for thread safety
        self.lock = threading.Lock()

    def record_request(self, method: str, path: str, duration: float, status_code: int):
        """Record an HTTP request."""
        with self.lock:
            self.request_count += 1
            self.request_duration += duration

            if status_code >= 400:
                self.error_count += 1
                self.recent_errors.append(
                    {
                        "timestamp": datetime.now(timezone.utc),
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "duration": duration,
                    }
                )

            self.recent_requests.append(
                {
                    "timestamp": datetime.now(timezone.utc),
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration": duration,
                }
            )

    def record_file_operation(self, operation: str, file_size: int = 0):
        """Record a file operation."""
        with self.lock:
            self.file_operations[operation] += 1
            if file_size > 0:
                self.file_operations[f"{operation}_bytes"] += file_size

    def record_chunk_operation(self, operation: str):
        """Record a chunk operation."""
        with self.lock:
            self.chunk_operations[operation] += 1

    def record_sync_operation(self, operation: str, success: bool = True):
        """Record a synchronization operation."""
        with self.lock:
            status = "success" if success else "failure"
            self.sync_operations[f"{operation}_{status}"] += 1

    def get_uptime(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self.start_time

    def get_request_rate(self, window_seconds: int = 60) -> float:
        """Get requests per second over the last window."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        recent_count = sum(1 for req in self.recent_requests if req["timestamp"] > cutoff_time)
        return recent_count / window_seconds if window_seconds > 0 else 0

    def get_error_rate(self, window_seconds: int = 60) -> float:
        """Get error rate (errors per second) over the last window."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        recent_errors = sum(1 for err in self.recent_errors if err["timestamp"] > cutoff_time)
        return recent_errors / window_seconds if window_seconds > 0 else 0

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used_mb": psutil.virtual_memory().used / 1024 / 1024,
            "memory_available_mb": psutil.virtual_memory().available / 1024 / 1024,
            "disk_usage_percent": psutil.disk_usage("/").percent,
            "disk_free_gb": psutil.disk_usage("/").free / 1024 / 1024 / 1024,
        }

    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-level metrics."""
        with self.lock:
            avg_duration = (self.request_duration / self.request_count) if self.request_count > 0 else 0

            return {
                "uptime_seconds": self.get_uptime(),
                "total_requests": self.request_count,
                "total_errors": self.error_count,
                "average_request_duration": avg_duration,
                "request_rate_per_second": self.get_request_rate(),
                "error_rate_per_second": self.get_error_rate(),
                "file_operations": dict(self.file_operations),
                "chunk_operations": dict(self.chunk_operations),
                "sync_operations": dict(self.sync_operations),
            }

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        system_metrics = self.get_system_metrics()
        app_metrics = self.get_application_metrics()

        # Determine health based on thresholds
        is_healthy = (
            system_metrics["cpu_percent"] < 90
            and system_metrics["memory_percent"] < 90
            and system_metrics["disk_usage_percent"] < 95
            and app_metrics["error_rate_per_second"] < 1.0  # Less than 1 error per second
        )

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": system_metrics,
            "application": app_metrics,
        }


# Global metrics collector instance
metrics = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Dependency injection for metrics collector."""
    return metrics


# FastAPI router for metrics endpoints
router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with system and application metrics."""
    return metrics.get_health_status()


@router.get("/system")
async def system_metrics(current_user: User = Depends(get_current_user_db)):
    """Get system-level metrics (requires authentication)."""
    return metrics.get_system_metrics()


@router.get("/application")
async def application_metrics(current_user: User = Depends(get_current_user_db)):
    """Get application-level metrics (requires authentication)."""
    return metrics.get_application_metrics()


@router.get("/requests/recent")
async def recent_requests(limit: int = 50, current_user: User = Depends(get_current_user_db)):
    """Get recent request history (requires authentication)."""
    with metrics.lock:
        recent = list(metrics.recent_requests)[-limit:]
        return {"requests": recent, "count": len(recent)}


@router.get("/errors/recent")
async def recent_errors(limit: int = 20, current_user: User = Depends(get_current_user_db)):
    """Get recent error history (requires authentication)."""
    with metrics.lock:
        recent = list(metrics.recent_errors)[-limit:]
        return {"errors": recent, "count": len(recent)}


@router.get("/prometheus")
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint."""
    app_metrics = metrics.get_application_metrics()
    system_metrics = metrics.get_system_metrics()

    prometheus_output = f"""# HELP meshcloud_uptime_seconds Application uptime in seconds
# TYPE meshcloud_uptime_seconds gauge
meshcloud_uptime_seconds {app_metrics['uptime_seconds']}

# HELP meshcloud_requests_total Total number of HTTP requests
# TYPE meshcloud_requests_total counter
meshcloud_requests_total {app_metrics['total_requests']}

# HELP meshcloud_errors_total Total number of HTTP errors
# TYPE meshcloud_errors_total counter
meshcloud_errors_total {app_metrics['total_errors']}

# HELP meshcloud_request_duration_seconds Average request duration
# TYPE meshcloud_request_duration_seconds gauge
meshcloud_request_duration_seconds {app_metrics['average_request_duration']}

# HELP meshcloud_cpu_percent CPU usage percentage
# TYPE meshcloud_cpu_percent gauge
meshcloud_cpu_percent {system_metrics['cpu_percent']}

# HELP meshcloud_memory_percent Memory usage percentage
# TYPE meshcloud_memory_percent gauge
meshcloud_memory_percent {system_metrics['memory_percent']}

# HELP meshcloud_disk_usage_percent Disk usage percentage
# TYPE meshcloud_disk_usage_percent gauge
meshcloud_disk_usage_percent {system_metrics['disk_usage_percent']}
"""

    return prometheus_output
