"""Machine Voice Client - STREAM mode. Just speak naturally."""
import sys, os, json, asyncio, time, threading, tempfile
sys.stdout.reconfigure(encoding="utf-8")
os.environ["MODELSCOPE_CACHE"] = r"D:\modelscope_cache"
import warnings; warnings.filterwarnings("ignore")
import sounddevice as sd
import numpy as np
import websockets

WS_URL = "ws://127.0.0.1:8000/api/v1/voice/v2/ws"
SR = 16000
CHUNK_SEC = 0.5

print("=" * 50)
print("  Machine Voice Client")
print("  Speak naturally - VAD detects when you stop")
print("  Ctrl+C to exit")
print("=" * 50)

running = True
audio_buffer = []

async def stream_voice():
    global running
    try:
        async with websockets.connect(WS_URL) as ws:
            welcome = json.loads(await ws.recv())
            print("  Connected: " + welcome["message"])

            # Enter STREAM mode (VAD automatic)
            await ws.send("STREAM")
            await ws.recv()  # mode_change response
            print("  VAD mode active - start speaking...")

            # Start continuous recording
            def record():
                global audio_buffer, running
                with sd.InputStream(samplerate=SR, channels=1, dtype="int16", device=1) as stream:
                    while running:
                        chunk, _ = stream.read(int(SR * CHUNK_SEC))
                        audio_buffer.append(chunk.copy())
                        time.sleep(0.01)
            rec_thread = threading.Thread(target=record, daemon=True)
            rec_thread.start()

            send_task = None
            while running:
                # Send accumulated audio
                if audio_buffer and (send_task is None or send_task.done()):
                    chunk = audio_buffer.pop(0)
                    send_task = asyncio.ensure_future(ws.send(chunk.tobytes()))

                # Check for replies
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=0.3)
                    if isinstance(msg, str):
                        data = json.loads(msg)
                        if data["type"] == "reply":
                            print("\n  Transcript: " + data.get("transcript", ""))
                            print("  Reply: " + data.get("text", ""))
                            # Check for audio
                            try:
                                audio_msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                                if isinstance(audio_msg, bytes):
                                    tf = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                                    tf.write(audio_msg); name = tf.name; tf.close()
                                    import subprocess
                                    subprocess.Popen(["start", "", name], shell=True)
                            except: pass
                except asyncio.TimeoutError:
                    pass
    except Exception as e:
        print("  Error: " + str(e))
    finally:
        running = False

try:
    asyncio.run(stream_voice())
except KeyboardInterrupt:
    print("\n  Stopped")
    running = False
