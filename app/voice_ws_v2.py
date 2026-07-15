"""Voice WebSocket - streaming VAD + manual + wake word mode."""
import traceback, time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from app.services.voice.pipeline import run_pipeline
from app.services.voice.manager import VoiceManager

router = APIRouter()
_manager = VoiceManager()

@router.websocket('/api/v1/voice/v2/ws')
async def voice_ws_v2(ws: WebSocket):
    await ws.accept()
    session_id = 'ws_%d_%f' % (id(ws), time.time())
    buf = bytearray()
    mode = 'manual'
    started = False
    try:
        await ws.send_json({'type': 'connected', 'session': session_id, 'mode': mode,
            'message': 'Voice v2 ready. Send PCM16 16kHz mono audio.'})
        while True:
            msg = await ws.receive()
            if 'bytes' in msg:
                if not started:
                    _manager.create_session(session_id); started = True
                data = msg['bytes']
                if mode == 'stream':
                    utterance = _manager.feed_audio(session_id, data)
                    if utterance is not None:
                        result = await run_pipeline(utterance, use_vad=False)
                        await _send_result(ws, result)
                elif mode == 'wake':
                    event = _manager.feed_wake_audio(session_id, data)
                    if event:
                        if event['type'] == 'wake':
                            await ws.send_json({'type': 'wake', 'message': 'Wake word detected, listening...'})
                        elif event['type'] == 'utterance':
                            result = await run_pipeline(event['audio'], use_vad=False)
                            await _send_result(ws, result)
                else:
                    buf.extend(data)
            elif 'text' in msg:
                text = msg['text']
                if text == 'END':
                    if not buf:
                        await ws.send_json({'type': 'error', 'message': 'No audio data'}); continue
                    audio = bytes(buf); buf = bytearray()
                    if mode == 'stream':
                        utterance = _manager.force_flush(session_id)
                        if utterance is not None:
                            result = await run_pipeline(utterance, use_vad=False)
                            await _send_result(ws, result)
                    else:
                        result = await run_pipeline(audio, use_vad=True)
                        await _send_result(ws, result)
                elif text == 'STREAM':
                    mode = 'stream'
                    await ws.send_json({'type': 'mode_change', 'mode': 'stream',
                        'message': 'Streaming mode: VAD detects speech end automatically.'})
                elif text == 'MANUAL':
                    mode = 'manual'; _manager.remove_session(session_id); started = False
                    await ws.send_json({'type': 'mode_change', 'mode': 'manual',
                        'message': 'Manual mode: send audio, use END to process.'}); buf = bytearray()
                elif text == 'WAKE':
                    mode = 'wake'
                    if not started:
                        _manager.create_session(session_id); started = True
                    await ws.send_json({'type': 'mode_change', 'mode': 'wake',
                        'message': 'Wake word mode: say alexa to activate.'})
                elif text == 'NOWAKE':
                    mode = 'manual'; _manager.remove_session(session_id); started = False
                    await ws.send_json({'type': 'mode_change', 'mode': 'manual',
                        'message': 'Wake word disabled.'}); buf = bytearray()
                elif text == 'PING':
                    await ws.send_json({'type': 'pong'})
                elif text.startswith('VAD_THRESHOLD:'):
                    try:
                        threshold = float(text.split(':')[1])
                        _manager._vad.threshold = threshold
                        await ws.send_json({'type': 'vad_threshold', 'value': threshold})
                    except: await ws.send_json({'type': 'error', 'message': 'Invalid threshold'})
                elif text == 'STATUS':
                    await ws.send_json({'type': 'status', 'session': session_id, 'mode': mode,
                        'buffer_size': len(buf),
                        'stt_loaded': run_pipeline.__globals__.get('_stt') is not None})
    except WebSocketDisconnect:
        logger.info('Voice WS disconnect: %s' % session_id)
    except Exception as e:
        logger.error('Voice WS error: %s' % e)
        traceback.print_exc()
        try: await ws.send_json({'type': 'error', 'message': str(e)})
        except: pass
    finally:
        _manager.remove_session(session_id)
        try: await ws.close()
        except: pass

async def _send_result(ws, result):
    if result.error:
        try: await ws.send_json({'type': 'error', 'message': result.error})
        except: pass
        return
    try:
        await ws.send_json({'type': 'reply', 'transcript': result.text, 'text': result.reply})
        if result.audio: await ws.send_bytes(result.audio)
    except Exception as e:
        logger.error('Send error: %s' % e)
