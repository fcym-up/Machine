# Real-time Voice Interaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real-time voice interaction system with KWS wake word, streaming ASR, VAD endpoint detection, and VITS TTS over a single WebSocket connection.

**Architecture:** 5 sequential tasks: (1) KWS wrapper + activate wake word, (2) VAD wrapper, (3) Online ASR (rewrite asr.py), (4) Async pipeline state machine, (5) WebSocket endpoint + frontend client. Each task ends with pytest green.

**Tech Stack:** Python 3.13, FastAPI 0.122, sherpa_onnx 1.13.4, Ollama/Qwen2.5 7B

## Global Constraints

- Single WebSocket connection for entire voice pipeline
- Existing models only: no new downloads
- Do NOT change existing API endpoints (events, memories, knowledge, etc.)
- Do NOT change existing database schema
- All changes must pass `pytest tests/ -v` before commit

---

### Task 1: KWS Wrapper + Wake Word Inject

**Files:**
- Create: `app/voice/kws.py`
- Modify: `models/.../keywords_raw.txt` (append "终端")

**Interfaces:**
- Produces: `app.voice.kws.create_kws()` -> sherpa_onnx.KeywordSpotter
- Produces: `app.voice.kws.check_keyword(spotter, samples)` -> dict {"detected": bool, "keyword": str, "confidence": float}

- [ ] **Add wake word to keywords_raw.txt**

Append to: `models/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01/keywords_raw.txt`

Content: `终端`

- [ ] **Create app/voice/kws.py**
Content:

```python
"""KWS - Keyword Spotting with sherpa-onnx for wake word detection."""
import os
import sherpa_onnx
import numpy as np

MODEL_DIR = os.path.join(
    os.path.dirname(__file__),
    "../../models/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01",
)

def create_kws():
    """Create KeywordSpotter with custom keywords."""
    feat_config = sherpa_onnx.FeatureConfig()
    feat_config.fbank_opts.frame_opts.samp_freq = 16000
    feat_config.fbank_opts.mel_opts.num_bins = 80

    config = sherpa_onnx.KwsConfig(
        feat_config=feat_config,
        model=sherpa_onnx.KwsModelConfig(
            encoder=os.path.join(MODEL_DIR, "encoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx"),
            decoder=os.path.join(MODEL_DIR, "decoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx"),
            joiner=os.path.join(MODEL_DIR, "joiner-epoch-12-avg-2-chunk-16-left-64.int8.onnx"),
            tokens=os.path.join(MODEL_DIR, "tokens.txt"),
            num_threads=2,
        ),
        keywords_file=os.path.join(MODEL_DIR, "keywords_raw.txt"),
        max_active_paths=4,
        num_trailing_blanks=1,
        enable_endpoint_detection=True,
        endpoint_rule1_min_trailing_silence=2.4,
    )
    return sherpa_onnx.KeywordSpotter(config)


def check_keyword(spotter, samples):
    """Check if wake word appears in audio samples.
    
    Args:
        spotter: KeywordSpotter instance
        samples: list/array of float32 audio samples at 16kHz
        
    Returns:
        dict with keys: detected (bool), keyword (str or None), confidence (float)
    """
    stream = spotter.create_stream()
    stream.accept_waveform(16000, np.array(samples, dtype=np.float32))
    spotter.decode_stream(stream)
    result = stream.result
    if result and result.keyword:
        return {"detected": True, "keyword": result.keyword, "confidence": 0.8}
    return {"detected": False, "keyword": None, "confidence": 0.0}
```

- [ ] **Test KWS module loads correctly**

Run:
```python
cd D:\workplace
.venv\Scripts\python -c "from app.voice.kws import create_kws; k=create_kws(); print('KWS loaded:', type(k).__name__)"
```

Expected: `KWS loaded: KeywordSpotter`

- [ ] **Run pytest to confirm no regression**

```bash
.venv\Scripts\pytest tests/ -v
```
Expected: All tests pass (2 pre-existing failures unrelated).

---

### Task 2: VAD Wrapper

**Files:**
- Create: `app/voice/vad.py`

**Interfaces:**
- Produces: `app.voice.vad.create_vad()` -> sherpa_onnx.VoiceActivityDetector
- Produces: `app.voice.vad.process_chunk(vad, samples)` -> dict {"speech_start": bool, "speech_end": bool, "is_speech": bool}

- [ ] **Create app/voice/vad.py**

```python
"""VAD - Voice Activity Detection with sherpa-onnx."""
import sherpa_onnx
import numpy as np


def create_vad():
    """Create VoiceActivityDetector with default config (16kHz)."""
    config = sherpa_onnx.VadModelConfig()
    config.num_threads = 2
    config.sample_rate = 16000
    config.silence_threshold = 0.5
    return sherpa_onnx.VoiceActivityDetector(config)


def process_chunk(vad, samples):
    """Process audio chunk through VAD.
    
    Args:
        vad: VoiceActivityDetector instance
        samples: list/array of float32 audio samples at 16kHz
        
    Returns:
        dict with speech_start, speech_end, is_speech (all bool)
    """
    audio = np.array(samples, dtype=np.float32)
    speech_start = False
    speech_end = False

    if len(audio) > 0:
        vad.accept_waveform(audio)
        is_speech = vad.is_speech
        # Return segment info if available
        speech_start = len(vad.chunk) > 0
    else:
        # Flush triggers end detection
        vad.flush()
        is_speech = False
        speech_end = True
        return {"speech_start": False, "speech_end": True, "is_speech": False}

    return {"speech_start": speech_start, "speech_end": False, "is_speech": is_speech}
```

- [ ] **Test VAD module loads correctly**

Run:
```python
.venv\Scripts\python -c "from app.voice.vad import create_vad; v=create_vad(); print('VAD loaded:', type(v).__name__)"
```

Expected: `VAD loaded: VoiceActivityDetector`

- [ ] **Run pytest to confirm no regression**

```bash
.venv\Scripts\pytest tests/ -v
```

Expected: All tests pass.

---

### Task 3: Online ASR (Streaming)

**Files:**
- Rewrite: `app/voice/asr.py` (from OfflineRecognizer to OnlineRecognizer)

**Interfaces:**
- Produces: `app.voice.asr.create_asr()` -> sherpa_onnx.OnlineRecognizer
- Produces: `app.voice.asr.transcribe_stream(asr, samples)` -> dict {"text": str, "is_final": bool}

- [ ] **Rewrite app/voice/asr.py**

```python
"""SenseVoice Online ASR - streaming speech-to-text."""
import os
import sherpa_onnx
import numpy as np

MODEL_DIR = os.path.join(
    os.path.dirname(__file__),
    "../../models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17",
)
MODEL_PATH = os.path.join(MODEL_DIR, "model.int8.onnx")
TOKENS_PATH = os.path.join(MODEL_DIR, "tokens.txt")


def create_asr():
    """Create OnlineRecognizer (streaming ASR)."""
    feat_config = sherpa_onnx.FeatureConfig()
    feat_config.fbank_opts.frame_opts.samp_freq = 16000
    feat_config.fbank_opts.mel_opts.num_bins = 80

    config = sherpa_onnx.OnlineRecognizerConfig(
        feat_config=feat_config,
        model_config=sherpa_onnx.OnlineModelConfig(
            sense_voice=sherpa_onnx.OnlineSenseVoiceModelConfig(
                model=MODEL_PATH,
                tokens=TOKENS_PATH,
                use_itn=True,
            ),
            num_threads=2,
        ),
        decoding_method="greedy_search",
        max_active_paths=4,
        enable_endpoint_detection=True,
        endpoint_rule1_min_trailing_silence=2.4,
        endpoint_rule2_min_trailing_silence=1.2,
        endpoint_rule3_min_utterance_length=300,
    )
    return sherpa_onnx.OnlineRecognizer(config)


def transcribe_stream(recognizer, samples):
    """Process audio chunk and return (text, is_final).
    
    Args:
        recognizer: OnlineRecognizer instance
        samples: list/array of float32 audio samples at 16kHz
        
    Returns:
        dict with text (str) and is_final (bool)
    """
    stream = recognizer.create_stream()
    audio = np.array(samples, dtype=np.float32)

    # Feed in chunks of ~100ms (1600 samples)
    chunk_size = 1600
    for start in range(0, len(audio), chunk_size):
        chunk = audio[start:start + chunk_size]
        stream.accept_waveform(16000, chunk)
        recognizer.decode_stream(stream)

    text = stream.result.text.strip()
    is_endpoint = recognizer.is_endpoint(stream)

    return {"text": text, "is_final": is_endpoint}
```

- [ ] **Test ASR module loads correctly**

```bash
.venv\Scripts\python -c "from app.voice.asr import create_asr; a=create_asr(); print('ASR loaded:', type(a).__name__)"
```

Expected: `ASR loaded: OnlineRecognizer`

- [ ] **Run pytest to confirm no regression**

```bash
.venv\Scripts\pytest tests/ -v
```

Expected: All tests pass.

---

### Task 4: Async Pipeline State Machine

**Files:**
- Rewrite: `app/voice/pipeline.py`
- Rewrite: `app/voice/__init__.py`

**Interfaces:**
- Produces: `app.voice.pipeline.VoicePipeline` with:
  - `states`: IDLE, LISTENING, THINKING, SPEAKING
  - `feed_audio(pcm_bytes)`: async method to accept audio
  - `process_wake()`: check buffer for wake word, return detected keyword or None
  - `transcribe()`: run ASR on buffer, return text
  - `llm_chat(text)`: call LLM, return response text
  - `tts_speak(text)`: generate TTS audio chunks, yield PCM frames
  - `barge_in()`: interrupt current TTS

- [ ] **Rewrite app/voice/pipeline.py**

```python
"""Voice Pipeline - async state machine integrating KWS, VAD, ASR, LLM, TTS.

States: idle -> listening -> thinking -> speaking (supports barge-in).
Uses existingsherpa-onnx models: KWS, VAD, SenseVoice ASR, VITS TTS.
"""
import asyncio
import numpy as np
from loguru import logger

from app.voice.kws import create_kws, check_keyword
from app.voice.vad import create_vad, process_chunk
from app.voice.asr import create_asr, transcribe_stream
from app.voice.tts import create_tts, synthesize

# LLM config: can switch between DeepSeek API and local Ollama
import os
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_MODEL = os.getenv("LLM_MODEL_CHAT", "qwen2.5:7b")


class VoicePipeline:
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"

    def __init__(self):
        self.state = self.IDLE
        self.sample_rate = 16000

        # Load models (lazy init delay: ~1-2s on first call)
        self._kws = None
        self._vad = None
        self._asr = None
        self._tts = None

        # Audio ring buffer for wake word detection
        self._buffer = []
        self._max_buffer_seconds = 3  # keep last 3s of audio

        # ASR context (accumulate across chunks)
        self._asr_context = []
        self._silence_frames = 0
        self._vad_speech_active = False

        # TTS interrupt flag
        self._barge_in = False

        logger.info("VoicePipeline initialized (models loaded on first use)")

    def _ensure_models(self):
        if self._kws is None:
            self._kws = create_kws()
            self._vad = create_vad()
            self._asr = create_asr()
            self._tts = create_tts()
            logger.info("All voice models loaded")

    def _add_to_buffer(self, samples):
        self._buffer.extend(samples)
        max_samples = self._max_buffer_seconds * self.sample_rate
        if len(self._buffer) > max_samples:
            self._buffer = self._buffer[-max_samples:]

    def feed_audio(self, pcm_bytes):
        """Feed raw PCM audio bytes (16kHz, 16-bit, mono). Return list of actions."""
        self._ensure_models()
        samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        sample_list = samples.tolist()
        self._add_to_buffer(sample_list)

        actions = []

        if self.state == self.IDLE:
            # KWS wake word check on accumulated buffer
            result = check_keyword(self._kws, self._buffer)
            if result["detected"]:
                self.state = self.LISTENING
                self._asr_context = []
                self._silence_frames = 0
                self._vad_speech_active = False
                actions.append({"type": "kws", "keyword": result["keyword"]})
                actions.append({"type": "state", "state": self.LISTENING})
                logger.info(f"Wake word detected: {result['keyword']}")

        elif self.state == self.LISTENING:
            # VAD + ASR pipeline
            vad_result = process_chunk(self._vad, sample_list)
            if vad_result["is_speech"]:
                self._vad_speech_active = True
                self._silence_frames = 0
                # Feed to streaming ASR
                asr_result = transcribe_stream(self._asr, sample_list)
                if asr_result["text"]:
                    actions.append({"type": "transcript", "text": asr_result["text"], "is_final": False})
            else:
                if self._vad_speech_active:
                    self._silence_frames += 1
                    # ~1.5s of silence -> end of speech
                    if self._silence_frames > 90:  # 90 frames @ 20ms = 1.8s
                        # Flush ASR for final result with silence
                        final = transcribe_stream(self._asr, [0.0] * 1600)
                        if final["text"]:
                            self.state = self.THINKING
                            actions.append({"type": "transcript", "text": final["text"], "is_final": True})
                            actions.append({"type": "state", "state": self.THINKING})
                            logger.info(f"ASR final: {final['text']}")
                        else:
                            self._vad_speech_active = False
                            self._silence_frames = 0

        elif self.state == self.SPEAKING:
            # Check for barge-in: if VAD detects speech while TTS playing
            vad_result = process_chunk(self._vad, sample_list)
            if vad_result["is_speech"]:
                self._barge_in = True
                self.state = self.LISTENING
                self._vad_speech_active = True
                self._silence_frames = 0
                actions.append({"type": "state", "state": self.LISTENING})
                logger.info("Barge-in detected, returning to listening")

        return actions

    async def process_command(self, text):
        """Process transcribed text through LLM and TTS.
        
        Args:
            text: str, the transcribed user speech
            
        Returns:
            async generator yielding action dicts + audio bytes
        """
        self.state = self.THINKING
        yield {"type": "state", "state": self.THINKING}
        yield {"type": "transcript", "text": text, "is_final": True}

        # LLM call (blocking, run in executor to avoid blocking event loop)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self._call_llm, text)
        if not response:
            yield {"type": "error", "message": "LLM response failed"}
            self.state = self.IDLE
            yield {"type": "state", "state": self.IDLE}
            return

        yield {"type": "llm_reply", "text": response}

        # TTS streaming
        self.state = self.SPEAKING
        yield {"type": "state", "state": self.SPEAKING}

        audio_bytes = await loop.run_in_executor(None, self._do_tts, response)
        if audio_bytes:
            chunk_size = 4096
            self._barge_in = False
            for i in range(0, len(audio_bytes), chunk_size):
                if self._barge_in:
                    logger.info("TTS interrupted by barge-in")
                    break
                yield {"type": "audio", "data": audio_bytes[i:i+chunk_size]}
                await asyncio.sleep(0.01)

            if not self._barge_in:
                yield {"type": "tts_end"}
                # Return to listening for next round
                self.state = self.LISTENING
                yield {"type": "state", "state": self.LISTENING}
                logger.info("TTS complete, returning to listening")
        else:
            yield {"type": "error", "message": "TTS failed"}

    def _call_llm(self, text):
        """Call LLM (local Ollama or remote API)."""
        from openai import OpenAI
        client = OpenAI(base_url=LLM_BASE_URL, api_key="ollama")
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": text}],
                temperature=0.7,
                max_tokens=512,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def _do_tts(self, text):
        """Generate TTS audio bytes."""
        return synthesize(self._tts, text)

    def barge_in(self):
        """Signal to interrupt current TTS playback."""
        self._barge_in = True

    def reset(self):
        """Reset pipeline to idle state."""
        self.state = self.IDLE
        self._buffer.clear()
        self._asr_context.clear()
        self._silence_frames = 0
        self._vad_speech_active = False
        self._barge_in = False
        logger.info("Pipeline reset to idle")


pipeline = VoicePipeline()
```

- [ ] **Update app/voice/__init__.py**

```python
from .pipeline import pipeline, VoicePipeline

__all__ = ["pipeline", "VoicePipeline"]
```

- [ ] **Run pytest to confirm no regression**

```bash
.venv\Scripts\pytest tests/ -v
```

Expected: All tests pass.

---

### Task 5: WebSocket Endpoint + Frontend Client

**Files:**
- Rewrite: `app/api/v1/voice.py`
- Rewrite: `app/static/js/voice.js`
- Modify: `app/static/js/app.js` (wire up new voice client)

- [ ] **Rewrite app/api/v1/voice.py**

```python
"""WebSocket endpoint for Machine real-time voice pipeline.

Single WebSocket connection handles:
- Binary: PCM audio frames (16kHz, 16-bit, mono, 640 bytes per 20ms)
- JSON: control messages (state, transcript, llm_reply, barge_in, etc.)
"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.voice.pipeline import pipeline

router = APIRouter(prefix="/voice", tags=["voice"])


@router.websocket("/stream")
async def voice_stream(ws: WebSocket):
    await ws.accept()
    logger.info("Voice WebSocket connected")

    # Client <-> pipeline bridge: coroutine to send actions back to client
    async def send_actions(gen):
        async for action in gen:
            if action["type"] == "audio":
                await ws.send_bytes(action["data"])
            else:
                await ws.send_json(action)

    try:
        while True:
            data = await ws.receive()

            if "bytes" in data:
                # Audio frame from mic -> pipeline
                actions = pipeline.feed_audio(data["bytes"])
                for action in actions:
                    await ws.send_json(action)

                    # If transcript is final, trigger LLM+TTS pipeline
                    if action["type"] == "transcript" and action.get("is_final"):
                        text = action["text"]
                        asyncio.create_task(send_actions(pipeline.process_command(text)))

            elif "text" in data:
                msg = json.loads(data["text"])
                action_type = msg.get("type", "")

                if action_type == "barge_in":
                    pipeline.barge_in()
                    await ws.send_json({"type": "state", "state": "listening"})

                elif action_type == "mic_start":
                    logger.info("Mic stream started")
                    # Re-initialize models if needed (no-op if already loaded)
                    try:
                        pipeline._ensure_models()
                    except Exception as e:
                        await ws.send_json({"type": "error", "message": str(e)})

                elif action_type == "mic_stop":
                    logger.info("Mic stream stopped")

                elif action_type == "reset":
                    pipeline.reset()
                    await ws.send_json({"type": "state", "state": "idle"})

    except WebSocketDisconnect:
        pipeline.reset()
        logger.info("Voice WebSocket disconnected")
    except Exception as e:
        logger.error(f"Voice WS error: {e}")
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
```

- [ ] **Rewrite app/static/js/voice.js**

```javascript
/**
 * VoiceClient v4 - WebSocket-based real-time voice pipeline.
 * No browser SpeechRecognition/SpeechSynthesis.
 * Sends mic PCM to backend KWS/VAD/ASR/LLM/TTS, receives TTS audio back.
 */
export class VoiceController {
  constructor(config = {}) {
    this.onWake = config.onWake || null;
    this.onSilence = config.onSilence || null;
    this.onTranscript = config.onTranscript || null;
    this.onLLMReply = config.onLLMReply || null;
    this.onStateChange = config.onStateChange || null;
    this.onUnavailable = config.onUnavailable || null;

    this.ws = null;
    this.mediaRecorder = null;
    this.audioContext = null;
    this.audioQueue = [];           // Queue of PCM chunks to play
    this.isPlaying = false;
    this.inConversation = false;
    this._state = "idle";
  }

  async start() {
    const wsUrl = `ws://${window.location.host}/api/v1/voice/stream`;
    
    try {
      this.ws = new WebSocket(wsUrl);
      this.ws.binaryType = "arraybuffer";
    } catch(e) {
      console.error("[Voice] WebSocket failed:", e);
      if (this.onUnavailable) this.onUnavailable();
      return;
    }

    this.ws.onopen = () => {
      console.log("[Voice] WebSocket connected");
      this.ws.send(JSON.stringify({ type: "mic_start" }));
      this._startMic();
    };

    this.ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        // TTS audio frame
        const pcmData = new Int16Array(event.data);
        if (pcmData.length === 1 && pcmData[0] === -1) {
          // END_OF_AUDIO marker
          return;
        }
        this.audioQueue.push(pcmData);
        if (!this.isPlaying) this._playNextAudio();
      } else {
        // JSON control message
        try {
          const msg = JSON.parse(event.data);
          this._handleMessage(msg);
        } catch(e) {
          console.warn("[Voice] Invalid JSON:", e);
        }
      }
    };

    this.ws.onerror = (e) => {
      console.error("[Voice] WS error:", e);
    };

    this.ws.onclose = () => {
      console.log("[Voice] WS closed");
      this._stopMic();
    };
  }

  _handleMessage(msg) {
    switch (msg.type) {
      case "kws":
        console.log("[Voice] Wake word:", msg.keyword);
        this.inConversation = true;
        if (this.onWake) this.onWake();
        break;
      case "state":
        this._state = msg.state;
        if (this.onStateChange) this.onStateChange(msg.state);
        if (msg.state === "idle") {
          this.inConversation = false;
        }
        break;
      case "transcript":
        if (this.onTranscript && msg.is_final) {
          this.onTranscript(msg.text);
        }
        break;
      case "llm_reply":
        if (this.onLLMReply) this.onLLMReply(msg.text);
        break;
      case "tts_end":
        console.log("[Voice] TTS complete");
        break;
      case "error":
        console.error("[Voice] Error:", msg.message);
        break;
    }
  }

  _startMic() {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        const audioCtx = new AudioContext({ sampleRate: 16000 });
        const source = audioCtx.createMediaStreamSource(stream);
        const processor = audioCtx.createScriptProcessor(4096, 1, 1);

        processor.onaudioprocess = (e) => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const input = e.inputBuffer.getChannelData(0);
            // Convert float32 [-1,1] to int16 PCM
            const pcm = new Int16Array(input.length);
            for (let i = 0; i < input.length; i++) {
              pcm[i] = Math.max(-32768, Math.min(32767, Math.round(input[i] * 32767)));
            }
            this.ws.send(pcm.buffer);
          }
        };

        source.connect(processor);
        processor.connect(audioCtx.destination);
        this.audioContext = audioCtx;
        this.processor = processor;
        this.source = source;
        console.log("[Voice] Mic streaming started");
      })
      .catch(e => {
        console.error("[Voice] Mic access denied:", e);
        if (this.onUnavailable) this.onUnavailable();
      });
  }

  _stopMic() {
    if (this.source) {
      this.source.disconnect();
    }
    if (this.processor) {
      this.processor.disconnect();
    }
    if (this.audioContext) {
      this.audioContext.close();
    }
    this.source = null;
    this.processor = null;
    this.audioContext = null;
  }

  _playNextAudio() {
    if (this.audioQueue.length === 0) {
      this.isPlaying = false;
      return;
    }
    this.isPlaying = true;
    const pcmData = this.audioQueue.shift();

    // Create audio buffer from PCM data
    const audioCtx = new AudioContext({ sampleRate: 24000 });
    const buffer = audioCtx.createBuffer(1, pcmData.length, 24000);
    const channelData = buffer.getChannelData(0);
    for (let i = 0; i < pcmData.length; i++) {
      channelData[i] = pcmData[i] / 32768.0;
    }

    const source = audioCtx.createBufferSource();
    source.buffer = buffer;
    source.connect(audioCtx.destination);
    source.onended = () => {
      audioCtx.close();
      this._playNextAudio();
    };
    source.start();
  }

  sendBargeIn() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "barge_in" }));
    }
  }

  stop() {
    this._stopMic();
    this.audioQueue = [];
    this.isPlaying = false;
    this.inConversation = false;
    if (this.ws) {
      this.ws.send(JSON.stringify({ type: "reset" }));
      this.ws.close();
    }
  }

  isInConversation() { return this.inConversation; }
}
```

- [ ] **Update app/static/js/app.js**

Replace the existing voice initialization block (around lines 6-30 and lines 47-115) with the new WebSocket-based client.

The key changes:
1. Replace `VoiceController` constructor to use new callback: `onLLMReply` instead of `handleTranscript` HTTP fetch logic
2. Remove the old `speak()` function (browser SpeechSynthesis)
3. Update `handleWake` and `handleSilence` to match new state flow
4. Wire `onStateChange` to update UI

```javascript
// In the init() function, replace voice initialization with:
voice = new VoiceController({
  onWake: handleWake,
  onSilence: handleSilence,
  onTranscript: (text) => {
    document.getElementById('core-title').textContent = '你说: ';
    document.getElementById('core-response').textContent = text;
    document.getElementById('core-response').style.opacity = '1';
  },
  onLLMReply: (reply) => {
    document.getElementById('core-title').textContent = '';
    document.getElementById('core-response').textContent = reply;
    document.getElementById('core-response').style.transition = 'opacity 0.5s ease';
    document.getElementById('core-response').style.opacity = '1';
  },
  onStateChange: (state) => {
    const statusEl = document.getElementById('voice-status-text');
    const titleEl = document.getElementById('core-title');
    if (statusEl) {
      const labels = { idle: '唤醒词模式', listening: '对话中...', thinking: '思考中...', speaking: '说话中' };
      statusEl.textContent = labels[state] || state;
    }
    if (state === 'idle') {
      titleEl.textContent = 'AI Consciousness';
      document.getElementById('core-subtitle').textContent = '我一直都在。';
      document.getElementById('core-hint').textContent = '说 "终端"';
    }
  },
  onUnavailable: handleUnavailable,
});

// Remove the old speak() function and its usage in handleTranscript
```

- [ ] **Run pytest to confirm no regression**

```bash
.venv\Scripts\pytest tests/ -v
```

Expected: All tests pass.

---

## Verification

- pytest tests/ -v: all passing (existing tests unaffected)
- Start FastAPI server, open Dashboard in browser
- Speak "终端" -> observe wake word detected in console
- Speak a question -> observe ASR transcription -> LLM response -> TTS audio playback
- Test barge-in: speak during TTS playback -> should interrupt

## File Change Summary

| File | Action |
|------|--------|
| app/voice/kws.py | Create (new) |
| app/voice/vad.py | Create (new) |
| app/voice/asr.py | Rewrite (Offline -> Online) |
| app/voice/pipeline.py | Rewrite (async state machine) |
| app/voice/__init__.py | Update |
| app/api/v1/voice.py | Rewrite (WebSocket endpoint) |
| app/static/js/voice.js | Rewrite (WebSocket client) |
| app/static/js/app.js | Modify (wire up new voice) |
| models/.../keywords_raw.txt | Append "终端" |