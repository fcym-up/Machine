# Core Engine â€?orchestrates modules, collects events, sends via queue

import sys
import time

from core.queue import EventQueue
from core.sender import Sender


class Engine:
    def __init__(self, poll_sec, api_url, api_key,
                 queue_size, sender_interval, sender_retries,
                 window_module=None, idle_module=None, music_module=None):
        self.poll_sec = poll_sec
        self.queue = EventQueue(max_size=queue_size)
        self.sender = Sender(api_url, api_key, max_retries=sender_retries)
        self.sender_interval = sender_interval

        self.window = window_module
        self.idle = idle_module
        self.music = music_module

        self._last_send = time.time()

    def run(self):
        print("Engine started. Modules:", flush=True)
        if self.window:
            print("  - Window", flush=True)
        if self.idle:
            print("  - Idle", flush=True)
        if self.music:
            print("  - Music", flush=True)

        while True:
            try:
                events = []

                # Window module
                if self.window:
                    e = self.window.poll()
                    if e:
                        events.append(e)
                        # Also check music for new window
                        if self.music:
                            me = self.music.poll(
                                title=self.window._last_title,
                                process=self.window._last_process,
                            )
                            if me:
                                events.append(me)

                # Idle module
                if self.idle:
                    e = self.idle.poll()
                    if e:
                        events.append(e)

                # Enqueue
                for e in events:
                    self.queue.push(e)

                # Periodic send
                now = time.time()
                if now - self._last_send >= self.sender_interval and len(self.queue) > 0:
                    batch = self.queue.drain()
                    ok = self.sender.send_batch(batch)
                    if ok > 0:
                        print(f"Sent {ok}/{len(batch)} events", flush=True)
                    self._last_send = now

            except Exception as exc:
                print(f"Engine error: {exc}", flush=True)

            time.sleep(self.poll_sec)
