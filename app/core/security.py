"""API Key 认证。

从环境变量读取 MACHINE_API_KEY。
提供 verify_api_key 依赖注入函数保护 API 端点。
使用 secrets.compare_digest 防止时序攻击。
"""
import os
import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.core.logger import logger

MACHINE_API_KEY = os.getenv("MACHINE_API_KEY", "machine-dev-key-change-me")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if api_key is None:
        logger.warning("Auth attempt with no API key")
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    if not secrets.compare_digest(api_key, MACHINE_API_KEY):
        logger.warning("Auth attempt with invalid API key")
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
