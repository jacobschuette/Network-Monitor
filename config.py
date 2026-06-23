"""Load and validate the YAML host configuration."""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CheckConfig:
    type: str           # ping | tcp | http | dns
    # ping
    count: int = 3
    timeout_sec: float = 2.0
    # tcp
    port: int | None = None
    # http
    url: str | None = None
    expected_status: int = 200
    keyword: str | None = None
    # dns
    hostname: str | None = None
    expected_ip: str | None = None


@dataclass
class HostConfig:
    name: str
    address: str
    checks: list[CheckConfig] = field(default_factory=list)


@dataclass
class MonitorConfig:
    interval_sec: int
    log_dir: str
    hosts: list[HostConfig]


def _parse_check(raw: dict[str, Any]) -> CheckConfig:
    check_type = raw.get("type", "").lower()
    if check_type not in ("ping", "tcp", "http", "dns"):
        raise ValueError(f"Unknown check type: '{check_type}'. Must be ping, tcp, http, or dns.")
    return CheckConfig(
        type=check_type,
        count=int(raw.get("count", 3)),
        timeout_sec=float(raw.get("timeout_sec", 2.0)),
        port=raw.get("port"),
        url=raw.get("url"),
        expected_status=int(raw.get("expected_status", 200)),
        keyword=raw.get("keyword"),
        hostname=raw.get("hostname"),
        expected_ip=raw.get("expected_ip"),
    )


def load(path: str | Path = "config/hosts.yaml") -> MonitorConfig:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    hosts = []
    for h in raw.get("hosts", []):
        checks = [_parse_check(c) for c in h.get("checks", [])]
        hosts.append(HostConfig(name=h["name"], address=h["address"], checks=checks))

    return MonitorConfig(
        interval_sec=int(raw.get("interval_sec", 60)),
        log_dir=raw.get("log_dir", "logs"),
        hosts=hosts,
    )
