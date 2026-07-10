# Real-time Voice Interaction Design

> Date: 2026-07-09
> Status: Draft

## Objective

Build a real-time voice interaction system (Jarvis/Doubao-style) using existing sherpa-onnx models: KWS for wake word detection, streaming ASR for speech-to-text, VAD for endpoint detection, and VITS TTS for voice response. All over a single WebSocket connection with barge-in support.

## Constraints

- Use existing downloaded sherpa-onnx models only (no new downloads)
- Single WebSocket connection for entire voice pipeline
- Sub-500ms first audio response latency target
- Full offline capability
- Support barge-in (user can interrupt TTS)
- Frontend no longer depends on browser SpeechRecognition/SpeechSynthesis
- All configuration via app.core.config.settings

---

## Architecture

[Browser Mic] -> PCM frames (20ms) -> WebSocket -> [Ring Buffer] -> [KWS: terminal detect]

[VAD: voice endpoint] -> [Online ASR] -> text -> [LLM: DeepSeek] -> text -> [TTS: VITS] -> PCM chunks -> WebSocket -> [Browser Speaker]

One single WebSocket connection for entire pipeline. Binary frames for audio, JSON frames for control messages.

---

## State Machine

States: idle -> listening -> thinking -> speaking

Transitions:
- idle -> listening: KWS detects wake word "terminal"
- listening -> thinking: VAD detects speech end, ASR produces final transcript
- thinking -> speaking: LLM response ready, TTS starts streaming
- speaking -> listening: TTS done (continue conversation)
- speaking -> listening: barge-in detected (user interrupts)

---

## WebSocket Protocol

### Binary: Audio PCM
- Format: 16kHz, 16-bit signed integer, mono
- Frame size: 640 bytes (20ms)
- Direction: Browser to Server (mic input) and Server to Browser (TTS output)

### JSON: Control Messages

Browser to Server:
| Type | Example | Trigger |
|------|---------|---------|
| audio frame | binary PCM | continuous while mic open |
| barge_in | {"type":"barge_in"} | user taps or speaks during TTS |
| stop | {"type":"stop"} | end conversation |

Server to Browser:
| Type | Example | Meaning |
|------|---------|---------|
| state | {"type":"state","state":"listening"} | state machine transition |
| kws | {"type":"kws","keyword":"terminal","confidence":0.85} | wake word detected |
| transcript | {"type":"transcript","text":"today weather","is_final":false} | ASR partial/final |
| llm_reply | {"type":"llm_reply","text":"Weather is fine."} | LLM response text |
| audio frame | binary PCM | TTS audio chunk |
| tts_end | {"type":"tts_end"} | last TTS chunk sent |
| error | {"type":"error","message":"..."} | error info |

---

## File Changes

### New Files (2)
- app/voice/vad.py - sherpa-onnx VoiceActivityDetector wrapper
- app/voice/kws.py - sherpa-onnx KeywordSpotter wrapper with custom keywords

### Rewritten Files (3)
- app/voice/pipeline.py - Async state machine with VAD/KWS/OnlineASR/TTS integration
- app/api/v1/voice.py - Single WebSocket endpoint handling binary + JSON frames
- app/static/js/voice.js - WebSocket-based voice client (no browser SpeechRecognition)

### Modified Files (2)
- app/core/config.py - Add WAKE_WORDS, VAD_THRESHOLD, SAMPLE_RATE config fields
- models/sherpa-onnx-kws-.../keywords.txt - Append terminal keyword

### Unchanged Files (2)
- app/voice/tts.py - Keep synthesize() interface, just called differently
- app/voice/asr.py - To be rewritten from OfflineRecognizer to OnlineRecognizer

---

## Model Usage

| Model | Component | Usage |
|-------|-----------|-------|
| kws-zipformer-wenetspeech-3.3M | KWS | KeywordSpotter with custom keywords.txt |
| sense-voice-zh-en-ja-ko-yue | ASR | OnlineRecognizer.from_sense_voice() |
| vits-melo-tts-zh_en | TTS | OfflineTts.generate() with chunked send |
| (built-in sherpa_onnx) | VAD | VoiceActivityDetector |

---

## Barge-in Design

When speaking state and user starts speaking again:
1. VAD detects new speech onset OR browser sends barge_in JSON
2. Server stops TTS immediately (discard remaining audio generation)
3. Server sends state: speaking -> listening
4. New audio enters ASR pipeline
5. System continues in listening state

---

## Verification

- pytest tests/ -v: all passing (existing tests unaffected)
- Manual WebSocket test
- Audio flow: mic -> KWS -> ASR -> LLM -> TTS -> speaker (end-to-end)
- Barge-in test: speak during TTS playback