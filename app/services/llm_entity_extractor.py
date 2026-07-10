from __future__ import annotations
import json
import time
from collections import deque
from typing import Any
from loguru import logger
from app.core.llm import get_llm_client

LLM_ENTITY_TYPES = ["person","organization","technology","location","event","concept","product","topic"]
_ENRICH_QUEUE: deque = deque()
_QUEUE_MAX = 500


class LLMEntityExtractor:
    """Hybrid entity extractor: regex (fast, sync) + LLM (slow, async batch)."""

    def __init__(self):
        self._client = get_llm_client()
        self.has_llm = self._client is not None
        if self.has_llm:
            logger.info("LLM entity extractor ready (DeepSeek) - hybrid pipeline active")
        else:
            logger.warning("LLM unavailable, entity extraction will use regex only")

    def extract(self, text, event_id: str = "", async_enrich: bool = True):
        """Extract entities from text. Returns regex results immediately."""
        ts = str(text) if not isinstance(text, str) else text
        if not ts or len(ts) < 3:
            return []
        entities = self._regex_extract(ts)
        if async_enrich and self.has_llm and event_id:
            self._enqueue_for_enrichment(event_id, ts, entities)
        return entities

    def _llm_extract(self, text):
        prompt = "Extract entities as JSON. Text: " + text[:1200] + "\nReturn: [{\"name\":\"...\",\"entity_type\":\"person|organization|technology|location|event|concept|product|topic\",\"confidence\":0.0-1.0}]"
        try:
            response = self._client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role":"system","content":"Entity extractor. Return ONLY JSON array."},
                    {"role":"user","content":prompt}
                ],
                temperature=0.1, max_tokens=800, timeout=5
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("["):
                entities = json.loads(content)
            elif "```json" in content:
                entities = json.loads(content.split("```json")[1].split("```")[0].strip())
            elif "```" in content:
                entities = json.loads(content.split("```")[1].split("```")[0].strip())
            else:
                entities = json.loads(content)
            return [e for e in entities if isinstance(e,dict) and "name" in e and e.get("entity_type","concept") in LLM_ENTITY_TYPES]
        except Exception as e:
            logger.warning(f"LLM NER failed: {e}")
            return []

    def _enqueue_for_enrichment(self, event_id: str, text: str, regex_entities: list):
        """Push event to enrichment queue for batch LLM processing."""
        global _ENRICH_QUEUE
        _ENRICH_QUEUE.append({
            "event_id": event_id,
            "text": text[:1200],
            "regex_entities": regex_entities,
            "ts": time.time(),
        })
        while len(_ENRICH_QUEUE) > _QUEUE_MAX:
            _ENRICH_QUEUE.popleft()

    @staticmethod
    def _batch_enrich():
        """Consume queue and batch-enrich via LLM. Called by scheduler."""
        global _ENRICH_QUEUE
        if not _ENRICH_QUEUE:
            return
        items = []
        while _ENRICH_QUEUE:
            items.append(_ENRICH_QUEUE.popleft())
        if not items:
            return
        from loguru import logger as _log
        _log.info(f"Batch enriching {len(items)} events for entities")
        ext = LLMEntityExtractor()
        if not ext.has_llm:
            return
        combined_text = "\n---\n".join(
            f"[id={it['event_id']}] {it['text']}" for it in items
        )
        ents = ext._llm_extract(combined_text)
        if not ents:
            _log.info("LLM batch extraction returned no entities")
            return
        _log.info(f"Batch extracted {len(ents)} entities via LLM")

    @staticmethod
    def _regex_extract(text):
        import re
        entities = []
        for pat, etype in [
            (r"(?i)\b(Google|Microsoft|Apple|Amazon|Meta|OpenAI|GitHub|DeepSeek|Anthropic|Tesla|NVIDIA)\b","organization"),
            (r"(?i)\b(Python|JavaScript|TypeScript|Rust|Go|Java|PostgreSQL|MySQL|MongoDB|Redis|Docker|Kubernetes|FastAPI|React|Vue|PyTorch|TensorFlow|LangChain|Neo4j|Kafka)\b","technology"),
            (r"\b(\u5317\u4eac|\u4e0a\u6d77|\u6df1\u5733|\u676d\u5dde|\u5e7f\u5dde|\u6210\u90fd|\u6b66\u6c49|\u5357\u4eac|\u65e7\u91d1\u5c71|\u7ebd\u7ea6|\u4f26\u6566|\u4e1c\u4eac)\b","location")
        ]:
            for m in re.findall(pat, text):
                entities.append({"name":m,"entity_type":etype,"confidence":0.7})
        seen=set(); unique=[]
        for e in entities:
            k=(e["name"].lower(),e["entity_type"])
            if k not in seen: seen.add(k); unique.append(e)
        return unique


llm_extractor = LLMEntityExtractor()


def enqueue_for_enrichment(event_id: str, text: str, regex_entities: list):
    llm_extractor._enqueue_for_enrichment(event_id, text, regex_entities)


def batch_enrich_entities():
    LLMEntityExtractor._batch_enrich()
