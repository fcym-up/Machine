"""Process classifier - maps process names to activity categories."""
PROCESS_CATEGORY_MAP = {
    "codex": "coding", "code": "coding", "devenv": "coding",
    "pycharm64": "coding", "idea64": "coding", "cursor": "coding",
    "notepad": "coding", "sublime_text": "coding", "vim": "coding",
    "wechat": "social", "weixin": "social", "qq": "social",
    "telegram": "social", "dingtalk": "social", "slack": "social",
    "discord": "social", "teams": "social",
    "chrome": "browsing", "msedge": "browsing", "firefox": "browsing",
    "steam": "gaming", "league of legends": "gaming", "valorant": "gaming",
    "spotify": "music", "cloudmusic": "music", "qqmusic": "music",
    "word": "document", "excel": "document", "powerpoint": "document",
    "notion": "document", "wps": "document",
    "terminal": "terminal", "powershell": "terminal", "cmd": "terminal",
    "explorer": "other",
}

def classify_process(process_name: str) -> str:
    if not process_name:
        return "other"
    import os
    pn = os.path.basename(process_name).lower()
    for key, cat in PROCESS_CATEGORY_MAP.items():
        if key in pn:
            return cat
    return "other"