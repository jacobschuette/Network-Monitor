"""ICMP ping check — returns (success, latency_ms, detail)."""

import platform
import subprocess
import re
import time
from dataclasses import dataclass


@dataclass
class CheckResult:
    success: bool
    latency_ms: float | None
    detail: str


def run(host: str, count: int = 3, timeout_sec: int = 2) -> CheckResult:
    system = platform.system()

    if system == "Windows":
        cmd = ["ping", "-n", str(count), "-w", str(timeout_sec * 1000), host]
        latency_pattern = re.compile(r"Average = (\d+)ms", re.IGNORECASE)
    else:
        cmd = ["ping", "-c", str(count), "-W", str(timeout_sec), host]
        latency_pattern = re.compile(r"rtt .* = [\d.]+/([\d.]+)/", re.IGNORECASE)

    try:
        start = time.perf_counter()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec * count + 5,
        )
        elapsed = (time.perf_counter() - start) * 1000

        output = result.stdout + result.stderr
        success = result.returncode == 0

        latency_ms = None
        match = latency_pattern.search(output)
        if match:
            latency_ms = float(match.group(1))

        if success:
            detail = f"Ping OK — avg {latency_ms:.0f}ms" if latency_ms else "Ping OK"
        else:
            detail = f"Ping FAILED — host unreachable ({host})"

        return CheckResult(success=success, latency_ms=latency_ms, detail=detail)

    except subprocess.TimeoutExpired:
        return CheckResult(success=False, latency_ms=None, detail=f"Ping timed out ({host})")
    except FileNotFoundError:
        return CheckResult(success=False, latency_ms=None, detail="'ping' command not found")
