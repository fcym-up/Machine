"""事件处理引擎。

EventClassifier：基于关键词的 event_type 自动检测。
EventNormalizer：按来源类型的 payload 标准化（browser/terminal/git）。
"""
from typing import Any


class EventClassifier:
    KEYWORD_MAP = {
        "browser": {
            "url": "web-activity",
            "page": "web-activity",
            "visit": "web-activity",
        },
        "terminal": {
            "command": "user-action",
            "output": "system-event",
            "error": "system-event",
        },
        "ide": {
            "file": "file-change",
            "edit": "file-change",
            "save": "file-change",
            "code": "file-change",
        },
        "git": {
            "commit": "git-commit",
            "push": "git-commit",
            "pull": "git-commit",
        },
        "chat": {
            "message": "chat-message",
            "response": "chat-message",
        },
        "api": {
            "request": "api-call",
            "response": "api-call",
        },
    }

    def classify(self, source: str, payload: dict[str, Any]) -> str:
        if source not in self.KEYWORD_MAP:
            return "user-action"
        for keyword, event_type in self.KEYWORD_MAP[source].items():
            if keyword in str(payload).lower():
                return event_type
        return "user-action"


class EventNormalizer:
    def normalize(self, source: str, payload: dict[str, Any]) -> dict[str, Any]:
        normalizers = {
            "browser": self._normalize_browser,
            "terminal": self._normalize_terminal,
            "git": self._normalize_git,
        }
        normalizer = normalizers.get(source, self._normalize_generic)
        return normalizer(payload)

    def _normalize_browser(self, payload: dict) -> dict:
        result = dict(payload)
        if "timestamp" in result:
            from datetime import datetime
            if isinstance(result["timestamp"], str):
                try:
                    result["_normalized_at"] = (
                        datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
                        .isoformat()
                    )
                except (ValueError, AttributeError):
                    pass
        result.setdefault("_source_normalized", "browser")
        return result

    def _normalize_terminal(self, payload: dict) -> dict:
        result = dict(payload)
        if "command" in result:
            result["_command"] = result["command"].strip()
        result.setdefault("_source_normalized", "terminal")
        return result

    def _normalize_git(self, payload: dict) -> dict:
        result = dict(payload)
        if "repo" not in result and "path" in result:
            result["_repo"] = result["path"]
        result.setdefault("_source_normalized", "git")
        return result

    def _normalize_generic(self, payload: dict) -> dict:
        result = dict(payload)
        result.setdefault("_source_normalized", "generic")
        return result
