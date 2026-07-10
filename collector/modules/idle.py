# Idle Module â€?detects when user is away from keyboard

import ctypes
import ctypes.wintypes
import time

user32 = ctypes.windll.user32


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.wintypes.UINT), ("dwTime", ctypes.wintypes.DWORD)]


class IdleModule:
    def __init__(self, threshold_sec: int = 300):
        self.threshold = threshold_sec
        self._idle = False
        self._idle_start = None

    def poll(self):
        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if not user32.GetLastInputInfo(ctypes.byref(info)):
            return None

        idle_ms = ctypes.windll.kernel32.GetTickCount() - info.dwTime
        idle_sec = idle_ms // 1000

        if not self._idle and idle_sec >= self.threshold:
            self._idle = True
            self._idle_start = time.time()
            return {"module": "idle", "state": "away", "seconds": idle_sec}

        if self._idle and idle_sec < 5:
            self._idle = False
            if self._idle_start:
                away_sec = int(time.time() - self._idle_start)
            else:
                away_sec = 0
            self._idle_start = None
            return {"module": "idle", "state": "back", "away_seconds": away_sec}

        return None
