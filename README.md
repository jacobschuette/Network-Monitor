# Network-Monitor
Developed a script to monitor network connectivity and alert on failures via email/log output
[README.md](https://github.com/user-attachments/files/28977557/README.md)
# Network Monitoring & Alert Script

Python-core monitoring engine with a PowerShell launcher. Runs four check types
against any host list and fires Windows Event Log alerts only on state transitions
(UP → DOWN and DOWN → UP), not on every failed poll.

## Architecture

```
launch.ps1 (PowerShell launcher / Task Scheduler registration)
    │
    └─► main.py
            │
        monitor/
        ├── config.py          Load + validate hosts.yaml
        ├── runner.py          Poll loop + state machine + alert dispatch
        ├── checks/
        │   ├── ping.py        ICMP reachability
        │   ├── tcp_port.py    TCP port open/closed
        │   ├── http_check.py  HTTP/HTTPS status + optional keyword
        │   └── dns_check.py   DNS resolution + optional IP assertion
        └── alerting/
            ├── event_log.py   Windows Application Event Log (via PowerShell)
            └── log_file.py    Rotating file + console logger
```

## Check Types

| Type | What it verifies |
|------|-----------------|
| `ping` | ICMP reachability + average latency |
| `tcp` | TCP port is open and accepts connections |
| `http` | HTTP/HTTPS returns expected status code (+ optional keyword in body) |
| `dns` | Hostname resolves (+ optional expected IP) |

## Event Log IDs

| Event ID | Type | Meaning |
|----------|------|---------|
| 1000 | Error | Host/service went DOWN |
| 1001 | Information | Host/service RECOVERED |
| 1002 | Warning | Check warning |

View in **Event Viewer → Windows Logs → Application → Source: NetworkMonitor**

## Quick Start

```powershell
# Install deps and run one poll cycle
.\launch.ps1 -Once

# Run continuously (Ctrl+C to stop)
.\launch.ps1

# Register as a Windows Scheduled Task (runs every minute, requires elevation)
.\launch.ps1 -Schedule -IntervalMinutes 5

# Run tests
python -m pytest tests/ -v
```

## Configuring Hosts

Edit [`config/hosts.yaml`](config/hosts.yaml):

```yaml
interval_sec: 60
log_dir: logs

hosts:
  - name: My Web Server
    address: 10.0.0.5
    checks:
      - type: ping
      - type: tcp
        port: 443
      - type: http
        url: https://mysite.internal
        expected_status: 200
        keyword: "Welcome"
      - type: dns
        hostname: mysite.internal
        expected_ip: 10.0.0.5
```

## Logs

Rotating log files are written to `logs/network_monitor.log` (5 MB × 5 backups).
All output is also mirrored to the console.

Sample output:
```
14:32:01  INFO     --- Poll cycle ---
14:32:01  INFO     Google DNS [PING] UP — Ping OK — avg 12ms
14:32:01  INFO     Google DNS [TCP] UP — TCP 8.8.8.8:53 open — 8ms
14:32:02  WARNING  ALERT: Internal Gateway [PING] went DOWN — Ping FAILED — host unreachable
14:32:02  INFO     --- Cycle complete, sleeping 60s ---
```
