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
from email.utils import parsedate_to_datetime
from typing import Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def add_cache_buster(url: str, request_index: int, attempt: int) -> str:
    """Append a cache-buster query parameter to reduce CDN throttling/caching effects."""
    parsed = urlsplit(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["_cb"] = f"{int(time.time() * 1000)}-{request_index}-{attempt}"
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def get_retry_delay(exc: urllib.error.HTTPError, fallback_delay: float) -> float:
    """Read Retry-After header if present, otherwise return fallback delay."""
    retry_after = ""
    if getattr(exc, "headers", None) is not None:
        retry_after = exc.headers.get("Retry-After", "").strip()

    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            try:
                retry_dt = parsedate_to_datetime(retry_after)
                now = time.time()
                return max(0.0, retry_dt.timestamp() - now)
            except Exception:
                pass

    return max(0.0, fallback_delay)


def download_once(
    url: str,
    timeout: float,
    chunk_size: int = 64 * 1024,
    request_index: int = 0,
    max_retries: int = 2,
    retry_base_delay: float = 1.5,
) -> tuple[float, int]:
    """Download a URL once and return (elapsed_seconds, bytes_downloaded)."""
    attempts = max(0, max_retries) + 1
    for attempt in range(1, attempts + 1):
        request_url = add_cache_buster(url, request_index=request_index, attempt=attempt)
        request = urllib.request.Request(
            request_url,
            headers={
                "User-Agent": "internet-speed-meter/1.0",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )
        start = time.perf_counter()
        bytes_downloaded = 0

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    bytes_downloaded += len(chunk)
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < attempts:
                delay = get_retry_delay(exc, retry_base_delay * attempt)
                time.sleep(delay)
                continue
            raise

        elapsed = time.perf_counter() - start
        return elapsed, bytes_downloaded

    raise RuntimeError("Unexpected retry flow")


def format_bytes(num_bytes: int) -> str:
    """Human-readable bytes formatter."""
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} TB"


def run_measurement(
    url: str,
    requests_count: int,
    timeout: float,
    progress_callback: Callable[[int, int, float, int], None] | None = None,
    max_retries: int = 2,
    pause_between_requests: float = 0.8,
    fallback_urls: list[str] | None = None,
) -> dict[str, object]:
    """Run sequential requests and return detailed measurement results."""
    if requests_count <= 0:
        raise ValueError("requests_count must be > 0")
    if timeout <= 0:
        raise ValueError("timeout must be > 0")
    if pause_between_requests < 0:
        raise ValueError("pause_between_requests must be >= 0")

    per_request: list[dict[str, float | int]] = []
    total_time = 0.0
    total_bytes = 0
    all_urls = [url]
    if fallback_urls:
        all_urls.extend(item for item in fallback_urls if item and item != url)
    active_url_index = 0

    for idx in range(1, requests_count + 1):
        if idx > 1 and pause_between_requests > 0:
            time.sleep(pause_between_requests)

        while True:
            current_url = all_urls[active_url_index]
            try:
                elapsed, bytes_downloaded = download_once(
                    current_url,
                    timeout=timeout,
                    request_index=idx,
                    max_retries=max_retries,
                )
                break
            except urllib.error.HTTPError as exc:
                if exc.code == 429 and active_url_index + 1 < len(all_urls):
                    active_url_index += 1
                    continue
                raise

        per_request.append(
            {
                "index": idx,
                "elapsed_seconds": elapsed,
                "bytes_downloaded": bytes_downloaded,
                "used_url": all_urls[active_url_index],
            }
        )
        total_time += elapsed
        total_bytes += bytes_downloaded
        if progress_callback is not None:
            progress_callback(idx, requests_count, elapsed, bytes_downloaded)

    average_time = total_time / requests_count
    speed_mib_s = (total_bytes / total_time) / (1024 * 1024) if total_time > 0 else 0.0

    return {
        "url": url,
        "requests_count": requests_count,
        "timeout": timeout,
        "max_retries": max_retries,
        "pause_between_requests": pause_between_requests,
        "effective_url": all_urls[active_url_index],
        "fallback_used": active_url_index > 0,
        "total_time_seconds": total_time,
        "total_bytes": total_bytes,
        "average_time_seconds": average_time,
        "speed_mib_s": speed_mib_s,
        "per_request": per_request,
    }


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
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Retries on HTTP 429 per request (default: 2)",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=0.8,
        help="Pause between requests in seconds (default: 0.8)",
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
    if args.retries < 0:
        print("Error: --retries must be >= 0", file=sys.stderr)
        return 1
    if args.pause < 0:
        print("Error: --pause must be >= 0", file=sys.stderr)
        return 1

    print(f"URL: {args.url}")
    print(f"Sequential requests: {args.requests}")
    print(f"Timeout per request: {args.timeout:.1f}s")
    print("-" * 60)

    try:
        result = run_measurement(
            args.url,
            args.requests,
            args.timeout,
            max_retries=args.retries,
            pause_between_requests=args.pause,
        )
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 2
    except TimeoutError:
        print("Request timed out", file=sys.stderr)
        return 2

    for item in result["per_request"]:
        print(
            f"[{item['index']}/{args.requests}] "
            f"time={item['elapsed_seconds']:.3f}s, "
            f"downloaded={format_bytes(int(item['bytes_downloaded']))}"
        )

    print("-" * 60)
    print(f"Average request time: {result['average_time_seconds']:.3f}s")
    print(f"Total downloaded: {format_bytes(int(result['total_bytes']))} ({result['total_bytes']} bytes)")
    print(f"Approximate speed: {result['speed_mib_s']:.3f} MB/s")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
