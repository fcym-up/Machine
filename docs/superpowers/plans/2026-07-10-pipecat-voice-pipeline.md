# Pipecat Voice Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Replace current Baidu direct-connect voice with Pipecat pipeline (STT->LLM->TTS + Agent Bridge + Memory).

**Architecture:** Pipecat pipeline in FastAPI process. WebSocket transport. Custom BaiduSTT/BaiduTTS Services. Memory pre-inject + post-store processors. Agent bridge via Function Calling.

**Tech Stack:** Python 3.13, FastAPI, pipecat-ai, DeepSeek API, Baidu ASR/TTS, silero-vad

## Global Constraints

- Keep existing Baidu API Key and DeepSeek API Key unchanged
- Pipeline runs in FastAPI process, not as separate service
- All existing APIs remain unchanged
- Do not break existing tests

---

## File Structure

### New files
- app/services/voice_pipecat/__init__.py
- app/services/voice_pipecat/services/__init__.py
- app/services/voice_pipecat/services/baidu_stt.py
- app/services/voice_pipecat/services/baidu_tts.py
- app/services/voice_pipecat/services/agent_bridge.py
- app/services/voice_pipecat/processors/__init__.py
- app/services/voice_pipecat/processors/memory_injector.py
- app/services/voice_pipecat/processors/context_builder.py
- app/services/voice_pipecat/pipeline.py

### Modified files
- app/api/v1/voice.py (add /ws WebSocket endpoint)
- app/static/voice.js (full rewrite)
- app/static/index.html (update voice UI)
- requirements.txt (add pipecat-ai)

---

### Task 1: Install Pipecat + Scaffold Package

**Files:**
- Modify: requirements.txt
- Create: app/services/voice_pipecat/__init__.py
- Create: app/services/voice_pipecat/services/__init__.py
- Create: app/services/voice_pipecat/processors/__init__.py

**Interfaces:**
- Produces: Empty voice_pipecat package with sub-packages services/ and processors/

- [ ] Add pipecat-ai to requirements.txt
- [ ] pip install -r requirements.txt
- [ ] Create package structure with __init__.py files

### Task 2: BaiduSTTService — Custom Pipecat Service

**Files:**
- Create: app/services/voice_pipecat/services/baidu_stt.py

**Interfaces:**
- Produces: class BaiduSTTService(PipecatBaseService) with push_frame() and context()
- Consumes: BAIDU_API_KEY, BAIDU_SECRET_KEY from settings

- [ ] Create BaiduSTTService that wraps existing BaiduVoiceClient logic
- [ ] Implement push_frame(audio_bytes) -> text result
- [ ] Handle access_token refresh internally
- [ ] Write unit test: tests/test_voice_pipecat/test_baidu_stt.py

### Task 3: BaiduTTSService — Custom Pipecat Service

**Files:**
- Create: app/services/voice_pipecat/services/baidu_tts.py

**Interfaces:**
- Produces: class BaiduTTSService(PipecatBaseService) with push_text(text) -> audio generator
- Consumes: BAIDU_API_KEY, BAIDU_SECRET_KEY from settings

- [ ] Create BaiduTTSService that wraps existing BaiduTTSClient logic
- [ ] Implement push_text(text) yielding MP3 chunks
- [ ] Write unit test: tests/test_voice_pipecat/test_baidu_tts.py

### Task 4: AgentBridge — Function Calling to Machine Agents

**Files:**
- Create: app/services/voice_pipecat/services/agent_bridge.py

**Interfaces:**
- Produces: function get_tools() -> list[tool_dict], function execute_tool(name, args) -> str
- Consumes: MemoryService, KnowledgeService, UserModelService, Brain via injected DB session

- [ ] Define Function Calling tool schemas (search_memory, query_knowledge, get_user_state, analyze_pattern)
- [ ] Implement execute_tool() dispatcher
- [ ] Route to existing Service layer (not Agent classes)

### Task 5: ContextBuilder + MemoryInjector

**Files:**
- Create: app/services/voice_pipecat/processors/context_builder.py
- Create: app/services/voice_pipecat/processors/memory_injector.py

**Interfaces:**
- Consumes: MemoryService, UserModelService, Brain, ConversationMessage table
- Produces: ContextBuilder.build() -> str (system prompt), MemoryInjector.store(user, assistant) -> None

- [ ] ContextBuilder: reuse _build_instructions() logic, add memory retrieval
- [ ] MemoryInjector: write user+assistant to ConversationMessage, trigger Event + emotion signal

### Task 6: Pipeline Assembly

**Files:**
- Create: app/services/voice_pipecat/pipeline.py

**Interfaces:**
- Produces: async function run_pipeline(websocket) — full voice session lifecycle
- Consumes: All above services + processors

- [ ] Assemble Pipecat Pipeline: VAD -> BaiduSTT -> LLM(DeepSeek) -> BaiduTTS
- [ ] Configure LLM with DeepSeek base_url + tools from AgentBridge
- [ ] Add ContextBuilder as pre-processor, MemoryInjector as post-processor
- [ ] Wire WebSocket transport (audio in/out)
- [ ] Handle interrupt (barge-in) logic

### Task 7: WebSocket Endpoint + Frontend

**Files:**
- Modify: app/api/v1/voice.py (add /ws endpoint)
- Modify: app/static/voice.js (full rewrite for WebSocket->Pipecat)
- Modify: app/static/index.html (voice UI state updates)

**Interfaces:**
- Produces: WebSocket endpoint /api/v1/voice/ws
- Consumes: run_pipeline() from pipeline.py

- [ ] Add WebSocket /ws endpoint in voice.py
- [ ] Rewrite voice.js: AudioContext capture -> WebSocket -> receive TTS audio -> Audio output
- [ ] Update index.html voice state mapping

---

## Test Strategy

- Task 2-3: Unit tests for custom Services (mock Baidu API via httpx mock)
- Task 7: Integration test via WebSocket test client
