"""Interactive demonstration of the Sliding Window Rate Limiter."""

import time
from rate_limiter import SlidingWindowRateLimiter, WindowConfig


def main() -> None:
    print("=" * 60)
    print("   Sliding Window Rate Limiter - Live Demonstration")
    print("=" * 60)

    # Allow 3 requests per 2-second sliding window
    config = WindowConfig(max_requests=3, window_seconds=2.0)
    limiter = SlidingWindowRateLimiter(config=config)
    client_id = "user_premium_01"

    print(f"\n[Config] Max: {config.max_requests} requests / {config.window_seconds}s window")
    print(f"[Client] Testing client key: '{client_id}'\n")

    # Send 4 requests in rapid succession
    for i in range(1, 5):
        res = limiter.allow(client_id)
        status = "[ALLOWED]" if res.allowed else f"[BLOCKED] (retry after {res.retry_after:.2f}s)"
        print(f"Request #{i:02d} -> {status} [Count: {res.current_count}/{res.max_requests}]")

    print("\n... Sleeping 2.1 seconds for window to slide/expire ...")
    time.sleep(2.1)

    # After expiry
    res_after = limiter.allow(client_id)
    status_after = "[ALLOWED]" if res_after.allowed else "[BLOCKED]"
    print(f"Request #05 -> {status_after} [Count: {res_after.current_count}/{res_after.max_requests}]")

    # Inspect metrics
    metrics = limiter.metrics(client_id)
    print(f"\n[Metrics] Active in window: {metrics.count_in_window}, Remaining capacity: {metrics.remaining}")
    print("=" * 60)


if __name__ == "__main__":
    main()
