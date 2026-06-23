"""TCP port reachability check."""

import socket
import time
from dataclasses import dataclass


@dataclass
class CheckResult:
    success: bool
    latency_ms: float | None
    detail: str


def run(host: str, port: int, timeout_sec: float = 3.0) -> CheckResult:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout_sec):
            latency_ms = (time.perf_counter() - start) * 1000
            return CheckResult(
                success=True,
                latency_ms=latency_ms,
                detail=f"TCP {host}:{port} open — {latency_ms:.0f}ms",
            )
    except (socket.timeout, TimeoutError):
        return CheckResult(
            success=False,
            latency_ms=None,
            detail=f"TCP {host}:{port} timed out",
        )
    except ConnectionRefusedError:
        return CheckResult(
            success=False,
            latency_ms=None,
            detail=f"TCP {host}:{port} connection refused",
        )
    except OSError as exc:
        return CheckResult(
            success=False,
            latency_ms=None,
            detail=f"TCP {host}:{port} error — {exc}",
        )
