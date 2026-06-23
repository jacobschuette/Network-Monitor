"""DNS resolution check — verifies a hostname resolves and optionally matches an expected IP."""

import socket
import time
from dataclasses import dataclass, field


@dataclass
class CheckResult:
    success: bool
    latency_ms: float | None
    resolved_ips: list[str] = field(default_factory=list)
    detail: str = ""


def run(hostname: str, expected_ip: str | None = None, timeout_sec: float = 3.0) -> CheckResult:
    start = time.perf_counter()
    try:
        socket.setdefaulttimeout(timeout_sec)
        infos = socket.getaddrinfo(hostname, None)
        latency_ms = (time.perf_counter() - start) * 1000

        resolved = sorted({info[4][0] for info in infos})

        if expected_ip and expected_ip not in resolved:
            return CheckResult(
                success=False,
                latency_ms=latency_ms,
                resolved_ips=resolved,
                detail=(
                    f"DNS {hostname} resolved to {resolved} "
                    f"but expected {expected_ip}"
                ),
            )

        return CheckResult(
            success=True,
            latency_ms=latency_ms,
            resolved_ips=resolved,
            detail=f"DNS {hostname} → {resolved} in {latency_ms:.0f}ms",
        )

    except socket.gaierror as exc:
        return CheckResult(
            success=False,
            latency_ms=None,
            detail=f"DNS {hostname} resolution failed — {exc}",
        )
    except socket.timeout:
        return CheckResult(
            success=False,
            latency_ms=None,
            detail=f"DNS {hostname} timed out after {timeout_sec}s",
        )
    finally:
        socket.setdefaulttimeout(None)
