# Window Module ¡ª tracks current window, emits duration events on switch

import ctypes
import ctypes.wintypes
import re
import os

import time
from pathlib import Path

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

user32.GetForegroundWindow.restype = ctypes.wintypes.HWND
user32.GetWindowTextW.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetWindowThreadProcessId.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = ctypes.wintypes.DWORD

kernel32.OpenProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]
kernel32.OpenProcess.restype = ctypes.wintypes.HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD, ctypes.wintypes.LPWSTR, ctypes.POINTER(ctypes.wintypes.DWORD)]
kernel32.QueryFullProcessImageNameW.restype = ctypes.wintypes.BOOL
kernel32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
kernel32.CloseHandle.restype = ctypes.wintypes.BOOL

NOISE_TITLES = ("program manager",)


class WindowModule:
    def __init__(self):
        self._last_hwnd = None
        self._last_start = None
        self._last_title = ""
        self._last_process = ""
        self._first = True

    def poll(self):
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None

        if hwnd == self._last_hwnd:
            return None

        is_first = self._first
        self._first = False
        now = time.time()
        event = None

        # Mark this hwnd as seen immediately ¡ª prevents re-processing on early returns
        self._last_hwnd = hwnd

        # Emit duration for previous window (skip on first poll)
        if self._last_hwnd and self._last_start and not is_first:
            duration = int(now - self._last_start)
            if duration >= 1:
                event = {
                    "module": "window",
                    "process": self._last_process,
                    "title": self._last_title,
                    "duration": duration,
                }

        # Look up new window
        title = _get_title(hwnd)
        if not title or any(kw in title.lower() for kw in NOISE_TITLES):
            self._last_start = None
            return event
        pid = _get_pid(hwnd)
        if pid == 0 or pid == os.getpid():
            self._last_start = None
            return event
        proc = _get_process_name(pid)
        if not proc:
            self._last_start = None
            return event
        title = _clean_title(title)

        # Valid window ¡ª update remaining tracking state (hwnd already set above)
        self._last_start = now
        self._last_title = title
        self._last_process = proc

        if is_first:
            return {"module": "window", "process": proc, "title": title, "duration": 0, "session": "start"}
        return event


def _get_title(hwnd):
    buf = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, buf, 512)
    return buf.value or ""


def _get_pid(hwnd):
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def _get_process_name(pid):
    h = kernel32.OpenProcess(0x1000, False, pid)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(260)
        size = ctypes.wintypes.DWORD(260)
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return Path(buf.value).stem
        return ""
    finally:
        kernel32.CloseHandle(h)


def _clean_title(raw):
    t = raw
    t = re.sub(r" - .+? - Microsoft.*Edge$", "", t)
    t = re.sub(r" - Microsoft.*Edge$", "", t)
    t = re.sub(r" - Google Chrome$", "", t)
    t = re.sub(r" [\u2014] Mozilla Firefox$", "", t)
    t = re.sub(r" \S+ \d+ [^\x01-\x7f]+$", "", t)
    return re.sub(r"\s*-\s*$", "", t).strip()