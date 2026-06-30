#!/usr/bin/env python3
"""
Simple internet speed meter based on sequential HTTP downloads.
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request


def download_once(url: str, timeout: float, chunk_size: int = 64 * 1024) -> tuple[float, int]:
    """Download a URL once and return (elapsed_seconds, bytes_downloaded)."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "internet-speed-meter/1.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    start = time.perf_counter()
    bytes_downloaded = 0

    with urllib.request.urlopen(request, timeout=timeout) as response:
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            bytes_downloaded += len(chunk)

    elapsed = time.perf_counter() - start
    return elapsed, bytes_downloaded


def format_bytes(num_bytes: int) -> str:
    """Human-readable bytes formatter."""
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} TB"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run sequential downloads from a URL and calculate average request time "
            "and approximate internet speed in MB/s."
        )
    )
    parser.add_argument("url", help="URL to download (prefer a large file/image)")
    parser.add_argument(
        "-n",
        "--requests",
        type=int,
        default=10,
        help="Number of sequential requests (default: 10)",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout per request in seconds (default: 30)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.requests <= 0:
        print("Error: --requests must be > 0", file=sys.stderr)
        return 1
    if args.timeout <= 0:
        print("Error: --timeout must be > 0", file=sys.stderr)
        return 1

    print(f"URL: {args.url}")
    print(f"Sequential requests: {args.requests}")
    print(f"Timeout per request: {args.timeout:.1f}s")
    print("-" * 60)

    total_time = 0.0
    total_bytes = 0

    for idx in range(1, args.requests + 1):
        try:
            elapsed, bytes_downloaded = download_once(args.url, timeout=args.timeout)
        except urllib.error.URLError as exc:
            print(f"[{idx}/{args.requests}] Request failed: {exc}", file=sys.stderr)
            return 2
        except TimeoutError:
            print(f"[{idx}/{args.requests}] Request timed out", file=sys.stderr)
            return 2

        total_time += elapsed
        total_bytes += bytes_downloaded
        print(
            f"[{idx}/{args.requests}] "
            f"time={elapsed:.3f}s, downloaded={format_bytes(bytes_downloaded)}"
        )

    average_time = total_time / args.requests
    speed_mib_s = (total_bytes / total_time) / (1024 * 1024) if total_time > 0 else 0.0

    print("-" * 60)
    print(f"Average request time: {average_time:.3f}s")
    print(f"Total downloaded: {format_bytes(total_bytes)} ({total_bytes} bytes)")
    print(f"Approximate speed: {speed_mib_s:.3f} MB/s")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
