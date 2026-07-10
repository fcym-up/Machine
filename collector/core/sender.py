# Sender — HTTP POST events to Machine API with retry

import json
import sys
import time
import urllib.request


class Sender:
    def __init__(self, api_url: str, api_key: str, max_retries: int = 3):
        self.api_url = api_url
        self.api_key = api_key
        self.max_retries = max_retries

    def send(self, event):
        module = event.get("module", "")

        if module == "window":
            body = json.dumps({
                "event_type": "user-action",
                "source": "activity",
                "payload": {
                    "action": "switch-to",
                    "app": event.get("title", ""),
                    "process": event.get("process", ""),
                    "module": "window",
                    "duration": event.get("duration", 0),
                    "session": event.get("session", ""),
                },
            }).encode("utf-8")
        elif module == "idle":
            body = json.dumps({
                "event_type": "system-event",
                "source": "system",
                "payload": event,
            }).encode("utf-8")
        elif module == "music":
            body = json.dumps({
                "event_type": "user-action",
                "source": "activity",
                "payload": {
                    "action": "listen",
                    "app": f"{event.get('artist','')} - {event.get('song','')}",
                    "process": event.get("player", ""),
                    "module": "music",
                },
            }).encode("utf-8")
        else:
            return True  # unknown module, skip

        for attempt in range(1, self.max_retries + 1):
            try:
                req = urllib.request.Request(
                    self.api_url, data=body,
                    headers={"X-API-Key": self.api_key, "Content-Type": "application/json; charset=utf-8"},
                    method="POST",
                )
                urllib.request.urlopen(req, timeout=5)
                return True
            except Exception as e:
                if attempt == self.max_retries:
                    print(f"Sender fail: {e}", file=sys.stderr, flush=True)
                else:
                    time.sleep(attempt * 2)
        return False

    def send_batch(self, events):
        ok = 0
        for event in events:
            if self.send(event):
                ok += 1
        return ok
