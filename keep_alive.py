"""
server/keep_alive.py — Self-Ping Keep Alive
Prevents Render free tier sleep by pinging own health endpoint every 9 minutes.
"""
import time
import threading
import requests
import os
from rich.console import Console

console = Console()

SELF_URL = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:5000")
PING_INTERVAL = 540  # 9 minutes


def keep_alive():
    """Ping self health endpoint periodically."""
    time.sleep(60)
    while True:
        try:
            response = requests.get(f"{SELF_URL}/health", timeout=10)
            if response.status_code == 200:
                console.print(f"[dim]Keep-alive: OK[/dim]")
            else:
                console.print(f"[yellow]Keep-alive: HTTP {response.status_code}[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Keep-alive: {e}[/yellow]")
        time.sleep(PING_INTERVAL)


def start_keep_alive():
    """Start keep-alive if enabled."""
    if os.getenv("ENABLE_KEEP_ALIVE", "false").lower() == "true":
        thread = threading.Thread(target=keep_alive, daemon=True, name="keep-alive")
        thread.start()
        console.print("[dim]Keep-alive: ENABLED[/dim]")


if __name__ == "__main__":
    keep_alive()