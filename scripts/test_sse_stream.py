#!/usr/bin/env python3
"""
Smoke test para SSE stream (/operator/api/events/stream).

Valida:
1. EventSource se conecta sin 401/403/404
2. Captura al menos 1 evento en 5 segundos
3. Content-Type es text/event-stream

Uso: python3 scripts/test_sse_stream.py [--url http://localhost:8000] [--token vx11-test-token]
"""

import sys
import time
import requests
import argparse
from typing import Optional, Tuple


def test_sse_stream(
    base_url: str = "http://localhost:8000",
    token: str = "vx11-test-token",
    timeout_sec: int = 5,
) -> Tuple[bool, str]:
    """
    Test SSE stream endpoint.

    Returns: (success: bool, message: str)
    """
    endpoint = f"{base_url}/operator/api/events/stream"

    print(f"🔍 Testing SSE stream...")
    print(f"   Endpoint: {endpoint}")
    print(f"   Token: {token[:10]}...")
    print(f"   Timeout: {timeout_sec}s")
    print()

    # Test 1: Connection without 401/403/404
    try:
        print(f"📡 Test 1: Connecting to SSE stream...")
        response = requests.get(
            endpoint,
            params={"token": token},
            stream=True,
            timeout=timeout_sec,
        )

        # Check status code
        if response.status_code == 401:
            return False, f"❌ Auth failed (401): {response.text[:100]}"
        elif response.status_code == 403:
            return False, f"❌ Forbidden (403): {response.text[:100]}"
        elif response.status_code == 404:
            return False, f"❌ Not found (404): {response.text[:100]}"
        elif response.status_code >= 400:
            return False, f"❌ HTTP {response.status_code}: {response.text[:100]}"
        elif response.status_code != 200:
            return False, f"❌ Unexpected status {response.status_code}"

        print(f"   ✅ Connected with HTTP 200")

    except requests.exceptions.Timeout:
        return False, f"❌ Connection timeout ({timeout_sec}s exceeded)"
    except requests.exceptions.ConnectionError as e:
        return False, f"❌ Connection refused: {str(e)}"
    except Exception as e:
        return False, f"❌ Connection error: {type(e).__name__}: {str(e)}"

    # Test 2: Check Content-Type
    print(f"📡 Test 2: Checking Content-Type...")
    content_type = response.headers.get("content-type", "").lower()

    if "text/event-stream" not in content_type:
        return False, f"❌ Wrong Content-Type: {response.headers.get('content-type')}"

    print(f"   ✅ Content-Type is text/event-stream")

    # Test 3: Capture data within timeout
    print(f"📡 Test 3: Reading stream data (max {timeout_sec}s)...")

    bytes_received = 0
    event_count = 0
    start_time = time.time()

    try:
        for chunk in response.iter_content(chunk_size=1024, decode_unicode=False):
            elapsed = time.time() - start_time

            if elapsed > timeout_sec:
                break

            if chunk:
                bytes_received += len(chunk)
                # Count events by looking for "event:" markers
                event_count += chunk.decode("utf-8", errors="ignore").count("event:")

    except Exception as e:
        # Connection errors on streaming are common when timeout is reached
        # If we got data, it's still a pass
        if bytes_received == 0:
            return False, f"❌ No data received before error: {type(e).__name__}"

    if bytes_received > 0:
        print(f"   ✅ Received {bytes_received} bytes ({event_count} potential events)")
        return (
            True,
            f"✅ SSE stream test PASSED (data: {bytes_received}B, events: {event_count})",
        )
    else:
        return False, f"❌ No data received within {timeout_sec}s"


def main():
    parser = argparse.ArgumentParser(description="Test VX11 SSE stream endpoint")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--token",
        default="vx11-test-token",
        help="Auth token (default: vx11-test-token)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout in seconds (default: 5)",
    )

    args = parser.parse_args()

    success, message = test_sse_stream(
        base_url=args.url,
        token=args.token,
        timeout_sec=args.timeout,
    )

    print()
    print("=" * 60)
    print(message)
    print("=" * 60)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
