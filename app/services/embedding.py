"""
Embedding engine - ML semantic vectors with hash fallback.

Uses sentence-transformers (all-MiniLM-L6-v2, 384-dim) when available,
falls back to deterministic hash-based vectors otherwise.
Model is lazy-loaded to avoid blocking service startup.
"""
import hashlib, struct, numpy as np
from loguru import logger

_model = None
_model_loaded = False
USE_ML = False

class MLFallbackEmbedder:
    DIM = 384
    def __init__(self):
        self.USE_ML = USE_ML
        self._ensure_model()
    def _ensure_model(self):
        global _model, _model_loaded, USE_ML
        if _model_loaded: return
        _model_loaded = True
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            USE_ML = True; self.USE_ML = True
            logger.info('ML embedding loaded: all-MiniLM-L6-v2 (384-dim)')
        except Exception as e:
            logger.warning(f'ML embedding unavailable: {e}')
            _model = None; USE_ML = False; self.USE_ML = False
    def embed(self, text):
        self._ensure_model()
        if self.USE_ML and _model and text:
            vec = _model.encode(text)
            return vec.tolist() if hasattr(vec, 'tolist') else list(vec)
        return self._hash_embed(text)
    def similarity(self, v1, v2):
        a = np.nan_to_num(np.array(v1)); b = np.nan_to_num(np.array(v2))
        na = np.linalg.norm(a); nb = np.linalg.norm(b)
        if na == 0 or nb == 0: return 0.0
        return float(np.dot(a, b) / (na * nb))
    def _hash_embed(self, text):
        dim = self.DIM
        tokens = text.lower().split()[:100]
        if not tokens: return [0.0] * dim
        vecs = []
        for token in tokens:
            h = hashlib.sha256(token.encode()).digest()
            repeats = (dim // 8) + 1
            extended = h * repeats
            floats = list(struct.unpack('f' * dim, extended[:dim * 4]))
            vecs.append(floats)
        arr = np.mean(vecs, axis=0)
        n = np.linalg.norm(arr)
        return (arr / n).tolist() if n > 0 else [0.0] * dim

embedder = MLFallbackEmbedder()
