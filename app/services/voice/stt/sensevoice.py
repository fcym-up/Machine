"""SenseVoice STT — local GPU-based speech recognition via FunASR."""
import os
import warnings
import numpy as np
from loguru import logger

# Redirect model cache to D: drive
_DEFAULT_CACHE = r"D:\modelscope_cache"
os.environ.setdefault("MODELSCOPE_CACHE", _DEFAULT_CACHE)
warnings.filterwarnings("ignore", category=UserWarning, module="funasr")


class SenseVoiceSTT:
    """Speech-to-text using SenseVoiceSmall via FunASR AutoModel.
    
    Loads model on first use, cached thereafter.
    Runs on GPU by default.
    """
    
    MODEL_ID = "iic/SenseVoiceSmall"
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, device: str = "cuda:0"):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.device = device
        self._model = None
        self._load_model()
    
    def _load_model(self):
        try:
            from funasr import AutoModel
            logger.info(f"Loading SenseVoice on {self.device}...")
            self._model = AutoModel(
                model=self.MODEL_ID,
                vad_model=None,
                punc_model=None,
                device=self.device,
                disable_update=True,
            )
            logger.info("SenseVoice model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load SenseVoice: {e}")
            logger.info("Trying CPU fallback...")
            try:
                from funasr import AutoModel
                self._model = AutoModel(
                    model=self.MODEL_ID,
                    vad_model=None,
                    punc_model=None,
                    device="cpu",
                    disable_update=True,
                )
                logger.info("SenseVoice loaded on CPU as fallback")
            except Exception as e2:
                logger.error(f"CPU fallback also failed: {e2}")
                self._model = None
    
    def transcribe(self, audio: np.ndarray | bytes, sample_rate: int = 16000) -> str:
        """Transcribe audio to text.
        
        Args:
            audio: float32 numpy array (-1 to 1) or raw PCM16 bytes
            sample_rate: must be 16000
        
        Returns:
            Transcribed text.
        """
        if self._model is None:
            return ""
        
        if isinstance(audio, bytes):
            raw = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
        else:
            raw = audio.astype(np.float32)
        
        if len(raw) < 160:
            return ""
        
        try:
            result = self._model.generate(input=raw, language="zh", hotword="")
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("text", "") if isinstance(result[0], dict) else str(result[0])
            elif isinstance(result, dict):
                return result.get("text", "")
            return str(result)
        except Exception as e:
            logger.error(f"SenseVoice inference error: {e}")
            return ""
    
    @property
    def available(self) -> bool:
        return self._model is not None
    
    @property
    def model_path(self) -> str:
        cache = os.environ.get("MODELSCOPE_CACHE", _DEFAULT_CACHE)
        return os.path.join(cache, "models", self.MODEL_ID.replace("/", os.sep))
