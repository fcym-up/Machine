# Music Module â€?detects music playback from window titles

import re

# Known music player window title patterns
PLAYER_PATTERNS = [
    (r"(.+?) - (.+)", None),               # Generic: Artist - Song
]

# Process names that are music players
MUSIC_PROCESSES = {
    "cloudmusic",   # NetEase Cloud Music
    "qqmusic",      # QQ Music
    "spotify",
    "foobar2000",
}


class MusicModule:
    def __init__(self):
        self._last_song = ""

    def poll(self, title: str = "", process: str = ""):
        if not title or not process:
            return None

        pname = process.lower()
        if pname not in MUSIC_PROCESSES:
            return None

        for pat, _ in PLAYER_PATTERNS:
            m = re.match(pat, title)
            if m:
                artist = m.group(1).strip()
                song = m.group(2).strip()
                song_key = f"{artist}|{song}"
                if song_key == self._last_song:
                    return None
                self._last_song = song_key
                return {
                    "module": "music",
                    "artist": artist,
                    "song": song,
                    "player": pname,
                }

        return None
