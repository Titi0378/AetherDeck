"""
AetherDeck — Main Entry Point & Windows Desktop App Launcher.
Starts the local Tornado backend, synchronizes controller configurations,
and opens the standalone Windows application window.
"""

import argparse
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
import tornado.ioloop

from backend.server import create_tornado_app


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def find_free_port(preferred: int = 8765) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", preferred)) != 0:
            return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def open_native_window(url: str) -> None:
    time.sleep(0.6)
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for edge in edge_paths:
        if os.path.exists(edge):
            try:
                subprocess.Popen([
                    edge,
                    f"--app={url}",
                    "--window-size=1380,880",
                    "--disable-features=Translate",
                ])
                return
            except Exception:
                pass
    webbrowser.open(url)


def main():
    parser = argparse.ArgumentParser(description="AetherDeck Multi-System Emulation & Preservation Hub")
    parser.add_argument("--port", type=int, default=8765, help="Local server port")
    parser.add_argument("--headless", action="store_true", help="Run server without opening GUI window")
    args = parser.parse_args()

    port = find_free_port(args.port)
    app = create_tornado_app(BASE_DIR)
    app.listen(port, address="127.0.0.1")

    url = f"http://127.0.0.1:{port}"
    print("=" * 68)
    print(f"  AetherDeck — Architecture d'Émulation Multi-Systèmes prête sur {url}")
    print("=" * 68)

    if not args.headless:
        threading.Thread(target=open_native_window, args=(url,), daemon=True).start()

    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        print("\nArrêt d'AetherDeck.")


if __name__ == "__main__":
    main()
