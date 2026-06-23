"""
Core monitoring loop.

Tracks per-target state so alerts fire only on transitions
(UP→DOWN and DOWN→UP), not on every failed poll.
"""

from __future__ import annotations

import time
from collections import defaultdict

from monitor.alerting import event_log, log_file
from monitor.checks import dns_check, http_check, ping, tcp_port
from monitor.config import CheckConfig, MonitorConfig


# Sentinel values for the state machine
_UP = "up"
_DOWN = "down"
_UNKNOWN = "unknown"


def _run_check(address: str, cfg: CheckConfig):
    """Dispatch to the right check module and return a unified result."""
    if cfg.type == "ping":
        return ping.run(address, count=cfg.count, timeout_sec=int(cfg.timeout_sec))

    if cfg.type == "tcp":
        if not cfg.port:
            raise ValueError(f"TCP check for '{address}' missing 'port'")
        return tcp_port.run(address, cfg.port, timeout_sec=cfg.timeout_sec)

    if cfg.type == "http":
        url = cfg.url or f"http://{address}"
        return http_check.run(
            url,
            timeout_sec=cfg.timeout_sec,
            expected_status=cfg.expected_status,
            keyword=cfg.keyword,
        )

    if cfg.type == "dns":
        hostname = cfg.hostname or address
        return dns_check.run(hostname, expected_ip=cfg.expected_ip, timeout_sec=cfg.timeout_sec)

    raise ValueError(f"Unknown check type: {cfg.type}")


def _check_key(host_name: str, check_type: str, port: int | None = None) -> str:
    return f"{host_name}:{check_type}:{port or ''}"


def run_once(config: MonitorConfig, state: dict[str, str], logger) -> dict[str, str]:
    """Execute all checks once and update state. Returns updated state."""
    for host in config.hosts:
        for cfg in host.checks:
            key = _check_key(host.name, cfg.type, cfg.port)
            previous = state.get(key, _UNKNOWN)

            try:
                result = _run_check(host.address, cfg)
            except Exception as exc:
                logger.error("Unexpected error checking %s [%s]: %s", host.name, cfg.type, exc)
                continue

            current = _UP if result.success else _DOWN
            logger.info("%s [%s] %s — %s", host.name, cfg.type.upper(), current.upper(), result.detail)

            # Alert on state transitions only
            if current == _DOWN and previous != _DOWN:
                logger.warning("ALERT: %s [%s] went DOWN — %s", host.name, cfg.type, result.detail)
                event_log.alert_down(host.name, cfg.type, result.detail)

            elif current == _UP and previous == _DOWN:
                logger.info("RECOVERED: %s [%s] is back UP — %s", host.name, cfg.type, result.detail)
                event_log.alert_recovered(host.name, cfg.type, result.detail)

            state[key] = current

    return state


def run_loop(config: MonitorConfig):
    logger = log_file.get_logger(log_dir=config.log_dir)
    state: dict[str, str] = defaultdict(lambda: _UNKNOWN)

    logger.info("Network monitor started — %d host(s), interval %ds",
                len(config.hosts), config.interval_sec)

    while True:
        logger.info("--- Poll cycle ---")
        run_once(config, state, logger)
        logger.info("--- Cycle complete, sleeping %ds ---", config.interval_sec)
        time.sleep(config.interval_sec)
