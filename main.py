"""Entry point — load config and start the monitoring loop."""

import argparse
import sys
from pathlib import Path

from monitor.config import load
from monitor.runner import run_loop


def main():
    parser = argparse.ArgumentParser(description="Network Monitor")
    parser.add_argument(
        "--config", default="config/hosts.yaml",
        help="Path to hosts config YAML (default: config/hosts.yaml)",
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Run checks once and exit instead of looping",
    )
    args = parser.parse_args()

    try:
        config = load(args.config)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR loading config: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.once:
        from collections import defaultdict
        from monitor.alerting import log_file
        from monitor.runner import run_once, _UNKNOWN
        logger = log_file.get_logger(log_dir=config.log_dir)
        state = defaultdict(lambda: _UNKNOWN)
        run_once(config, state, logger)
    else:
        try:
            run_loop(config)
        except KeyboardInterrupt:
            print("\nMonitor stopped.")


if __name__ == "__main__":
    main()
