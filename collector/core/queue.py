# Event Queue — in-memory buffer with max size

from collections import deque


class EventQueue:
    def __init__(self, max_size: int = 100):
        self._q = deque()
        self.max_size = max_size

    def push(self, event):
        self._q.append(event)
        while len(self._q) > self.max_size:
            self._q.popleft()

    def drain(self):
        items = list(self._q)
        self._q.clear()
        return items

    def __len__(self):
        return len(self._q)
