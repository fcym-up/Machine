"""Database compatibility helpers — JSONB -> Text (SQLite) or JSONB (PostgreSQL)."""
import os
import json

from sqlalchemy import TypeDecorator, String


class JSONField(TypeDecorator):
    """Cross-dialect JSON: native JSONB on Postgres, TEXT+json on SQLite."""
    impl = String

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB)
        return dialect.type_descriptor(String)

    def process_bind_param(self, value, dialect):
        if dialect.name == "postgresql":
            return value
        return json.dumps(value, ensure_ascii=False) if value is not None else None

    def process_result_value(self, value, dialect):
        if dialect.name == "postgresql":
            return value
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return value


def is_sqlite():
    url = os.getenv("DATABASE_URL", "")
    return not url.startswith("postgresql")
