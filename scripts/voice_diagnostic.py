# -*- coding: utf-8 -*-
\"\"\"Machine 语音系统诊断脚本 — 逐环节测试并记录日志.\"\"\"
import sys, os, json, time, base64, struct
from datetime import datetime

LOG_FILE = r"D:\workplace\logs\voice_diagnostic.log"

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

def sep(title):
    log('=' * 60)
    log(f'  {title}')
    log('=' * 60)

# ===== 1. 环境检测 =====
sep('1. 环境检测')
log(f'Python: {sys.version}')
log(f'CWD: {os.getcwd()}')
log(f'DATABASE_URL: {os.environ.get(\"DATABASE_URL\", \"NOT SET\")}')
log(f'BAIDU_API_KEY: {\"SET\" if os.environ.get(\"BAIDU_API_KEY\") else \"NOT SET\"}')
log(f'BAIDU_SECRET_KEY: {\"SET\" if os.environ.get(\"BAIDU_SECRET_KEY\") else \"NOT SET\"}')
log(f'LLM_API_KEY: {\"SET (len=\" + str(len(os.environ.get(\"LLM_API_KEY\",\"\"))) + \")\" if os.environ.get(\"LLM_API_KEY\") else \"NOT SET\"}')

# ===== 2. 服务可用性检测 =====
sep('2. 服务可用性检测')
import httpx
try:
    r = httpx.get('http://127.0.0.1:8000/', timeout=5)
    log(f'GET / -> {r.status_code} {r.json()}')
except Exception as e:
    log(f'GET / FAILED: {e}')

try:
    r = httpx.get('http://127.0.0.1:8000/api/v1/voice/token', timeout=10)
    data = r.json()
    log(f'GET /voice/token -> {r.status_code}')
    log(f'  access_token: {data[\"access_token\"][:20]}...')
    log(f'  model: {data.get(\"model\")}')
    log(f'  voice: {data.get(\"voice\")}')
    log(f'  instructions ({len(data[\"instructions\"])} chars): {data[\"instructions\"][:80]}...')
except Exception as e:
    log(f'GET /voice/token FAILED: {e}')

# ===== 3. 模块导入检测 =====
sep('3. 模块导入检测')
import warnings
warnings.filterwarnings('ignore')
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:machine123@localhost:5432/machine')

try:
    from app.services.voice.baidu_stt import BaiduSTTService
    log(f'BaiduSTTService: {BaiduSTTService.__module__}.{BaiduSTTService.__qualname__}')
except Exception as e:
    log(f'BaiduSTTService IMPORT FAILED: {e}')

try:
    from app.services.voice.baidu_tts import BaiduTTSService
    log(f'BaiduTTSService: {BaiduTTSService.__module__}.{BaiduTTSService.__qualname__}')
except Exception as e:
    log(f'BaiduTTSService IMPORT FAILED: {e}')

try:
    from app.services.voice.pipeline import run_pipeline, PipelineResult, SYSTEM_INSTRUCTION
    log(f'run_pipeline: {run_pipeline}')
    log(f'SYSTEM_INSTRUCTION ({len(SYSTEM_INSTRUCTION)} chars): {SYSTEM_INSTRUCTION[:80]}...')
except Exception as e:
    log(f'pipeline IMPORT FAILED: {e}')

try:
    from app.api.v1.voice import router, _build_instructions
    routes = [r.path for r in router.routes]
    log(f'voice router routes: {routes}')
    instr = _build_instructions()
    log(f'_build_instructions() ({len(instr)} chars): {instr[:80]}...')
except Exception as e:
    log(f'voice API IMPORT FAILED: {e}')

# ===== 4. 依赖检测 =====
sep('4. 依赖检测')
try:
    import httpx; log(f'httpx: {httpx.__version__}')
except: log('httpx: NOT INSTALLED')
try:
    import aiohttp; log(f'aiohttp: {aiohttp.__version__}')
except: log('aiohttp: NOT INSTALLED')
try:
    import websockets; log(f'websockets: {websockets.__version__}')
except: log('websockets: NOT INSTALLED')
try:
    import openai; log(f'openai: {openai.__version__}')
except: log('openai: NOT INSTALLED')
try:
    from fastapi import FastAPI; log(f'fastapi: installed')
except: log('fastapi: NOT INSTALLED')

# ===== 5. 文件完整性检测 =====
sep('5. 文件完整性检测')
expected = {
    r'app\services\voice\__init__.py': '包入口',
    r'app\services\voice\baidu_stt.py': 'STT 服务',
    r'app\services\voice\baidu_tts.py': 'TTS 服务',
    r'app\services\voice\pipeline.py': '编排管线',
    r'app\api\v1\voice.py': 'API 端点',
}
for fn, desc in expected.items():
    full = os.path.join(r'D:\workplace', fn)
    if os.path.exists(full):
        size = os.path.getsize(full)
        log(f'  [OK] {desc}: {fn} ({size} bytes)')
    else:
        log(f'  [MISSING] {desc}: {fn}')

# ===== 6. 数据库连接检测 =====
sep('6. 数据库连接检测')
try:
    from app.core.database import SessionLocal
    db = SessionLocal()
    from sqlalchemy import text
    result = db.execute(text('SELECT 1'))
    log(f'Database: connected, SELECT 1 = {result.scalar()}')
    db.close()
except Exception as e:
    log(f'Database connection FAILED: {e}')

# ===== 7. LLM 连接检测 =====
sep('7. LLM 连接检测')
try:
    from app.core.llm import chat_simple
    reply = chat_simple('你好', system='请用两个字回应')
    log(f'LLM reply: {reply}')
except Exception as e:
    log(f'LLM FAILED: {e}')

log('')
log('===== 诊断完成 =====')
log(f'完整日志已保存到: {LOG_FILE}')
