
import sys, os, socket, time

def _check_singleton():
    """Prevent multiple collector instances on the same machine."""
    lock_port = 48765
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        if s.connect_ex(('127.0.0.1', lock_port)) == 0:
            print('Collector already running (port 48765 in use). Exiting.', flush=True)
            sys.exit(0)
        s.close()
    except:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', lock_port))
        s.listen(1)
        # Keep reference to prevent garbage collection
        import __main__
        __main__._lock_socket = s
    except:
        print('Collector already running. Exiting.', flush=True)
        sys.exit(0)

_check_singleton()

"""Machine Collector — modular entry point."""

import sys
from config import (
    API_KEY, API_URL, POLL_SEC,
    ENABLE_IDLE, ENABLE_MUSIC, ENABLE_WINDOW,
    IDLE_THRESHOLD_SEC, QUEUE_MAX_SIZE,
    SENDER_INTERVAL_SEC, SENDER_MAX_RETRIES,
)
from core.engine import Engine
from modules.idle import IdleModule
from modules.music import MusicModule
from modules.window import WindowModule


def main():
    window = WindowModule() if ENABLE_WINDOW else None
    idle = IdleModule(threshold_sec=IDLE_THRESHOLD_SEC) if ENABLE_IDLE else None
    music = MusicModule() if ENABLE_MUSIC else None

    engine = Engine(
        poll_sec=POLL_SEC,
        api_url=API_URL,
        api_key=API_KEY,
        queue_size=QUEUE_MAX_SIZE,
        sender_interval=SENDER_INTERVAL_SEC,
        sender_retries=SENDER_MAX_RETRIES,
        window_module=window,
        idle_module=idle,
        music_module=music,
    )
    engine.run()


if __name__ == "__main__":
    main()
