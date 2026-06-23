"""HTTP/HTTPS endpoint check — verifies 2xx response and optional keyword."""

import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class CheckResult:
    success: bool
    latency_ms: float | None
    status_code: int | None
    detail: str


def run(
    url: str,
    timeout_sec: float = 5.0,
    expected_status: int = 200,
    keyword: str | None = None,
) -> CheckResult:
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NetworkMonitor/1.0"})
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            latency_ms = (time.perf_counter() - start) * 1000
            status = response.status
            body = response.read(4096).decode("utf-8", errors="replace")

        if status != expected_status:
            return CheckResult(
                success=False,
                latency_ms=latency_ms,
                status_code=status,
                detail=f"HTTP {url} returned {status}, expected {expected_status}",
            )

        if keyword and keyword not in body:
            return CheckResult(
                success=False,
                latency_ms=latency_ms,
                status_code=status,
                detail=f"HTTP {url} OK ({status}) but keyword '{keyword}' not in response",
            )

        return CheckResult(
            success=True,
            latency_ms=latency_ms,
            status_code=status,
            detail=f"HTTP {url} OK — {status} in {latency_ms:.0f}ms",
        )

    except urllib.error.HTTPError as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return CheckResult(
            success=False,
            latency_ms=latency_ms,
            status_code=exc.code,
            detail=f"HTTP {url} error {exc.code}: {exc.reason}",
        )
    except urllib.error.URLError as exc:
        return CheckResult(
            success=False,
            latency_ms=None,
            status_code=None,
            detail=f"HTTP {url} unreachable — {exc.reason}",
        )
    except TimeoutError:
        return CheckResult(
            success=False,
            latency_ms=None,
            status_code=None,
            detail=f"HTTP {url} timed out after {timeout_sec}s",
        )
