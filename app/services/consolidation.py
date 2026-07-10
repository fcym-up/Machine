"""Memory consolidation engine — events → working → short → long → semantic."""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from loguru import logger
from app.models.event import Event
from app.models.memory import Memory
from app.services.embedding import embedder
from app.core.llm import chat_simple

LAYER_CONFIG = {
    "working": {"decay": 1.0, "ttl_hours": 1, "next": "short"},
    "short": {"decay": 0.5, "ttl_hours": 24, "next": "long"},
    "long": {"decay": 0.1, "ttl_hours": 720, "next": "semantic"},
    "semantic": {"decay": 0.0, "ttl_hours": None, "next": None},
}


class ConsolidationService:
    def __init__(self, db: Session):
        self.db = db

    def consolidate_hourly(self):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        events = self.db.query(Event).filter(Event.created_at >= cutoff).all()
        if not events:
            return {"consolidated": 0, "message": "No new events"}
        grouped = {}
        for e in events:
            cat = e.payload.get("category", "other") if isinstance(e.payload, dict) else "other"
            grouped.setdefault(cat, []).append(e)
        count = 0
        for cat, evts in grouped.items():
            summary_text = f"{len(evts)} {cat} events in the last hour"
            if len(evts) >= 3:
                payloads = [str(e.payload)[:100] for e in evts[:10]]
                llm_prompt = f"Summarize these {cat} activities in one sentence: {'; '.join(payloads)}"
                llm_summary = chat_simple(llm_prompt, "You are a memory consolidation engine. Reply in Chinese.")
                if llm_summary:
                    summary_text = llm_summary
            memory = Memory(
                memory_type="episode",
                content=f"[{cat}] {summary_text}",
                summary=summary_text,
                layer="working",
                decay_rate=1.0,
                embedding=embedder.embed(summary_text),
            )
            self.db.add(memory)
            count += 1
        self.db.commit()
        logger.info(f"Hourly consolidation: {count} working memories from {len(events)} events")
        self._decay_memories()
        return {"consolidated": count, "events_processed": len(events)}

    def consolidate_daily(self):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        working_mems = self.db.query(Memory).filter(
            Memory.layer == "working", Memory.created_at >= cutoff).all()
        if not working_mems:
            return {"consolidated": 0, "message": "No working memories to consolidate"}
        by_type = {}
        for m in working_mems:
            typ = m.content.split("]")[0].lstrip("[") if "[" in m.content else "general"
            by_type.setdefault(typ, []).append(m)
        count = 0
        for typ, mems in by_type.items():
            contents = [m.summary or m.content for m in mems]
            combined = "; ".join(contents[:5])
            llm_prompt = f"Summarize today's key points about {typ} in 2-3 sentences: {combined}"
            daily_summary = chat_simple(llm_prompt, "You are a daily memory consolidation engine. Reply in Chinese.")
            if not daily_summary:
                daily_summary = f"Today: {len(mems)} activities in {typ}"
            memory = Memory(
                memory_type="long",
                content=f"[daily:{typ}] {daily_summary}",
                summary=daily_summary,
                layer="short",
                decay_rate=0.5,
                embedding=embedder.embed(daily_summary),
                consolidated_from=[m.id for m in mems[:10]],
            )
            self.db.add(memory)
            count += 1
            for m in mems[:10]:
                m.layer = "short"
                m.decay_rate = 0.5
        self.db.commit()
        self._decay_memories()
        logger.info(f"Daily consolidation: {count} short memories from {len(working_mems)} working")
        return {"consolidated": count, "source_memories": len(working_mems)}

    def consolidate_weekly(self):
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        short_mems = self.db.query(Memory).filter(
            Memory.layer.in_(["short", "long"]), Memory.created_at >= cutoff).all()
        if not short_mems:
            return {"consolidated": 0, "message": "No short memories to refine"}
        summaries = [m.summary or m.content for m in short_mems]
        combined = " | ".join(summaries[:10])
        llm_prompt = f"Extract permanent knowledge about the user from this week's activities: {combined}"
        knowledge = chat_simple(llm_prompt, "You are a knowledge extraction engine. Reply in Chinese. Only state facts, no speculation.")
        if not knowledge:
            knowledge = f"Weekly summary of {len(short_mems)} activity categories"
        memory = Memory(
            memory_type="semantic",
            content=f"[semantic:weekly] {knowledge}",
            summary=knowledge,
            layer="semantic",
            decay_rate=0.0,
            embedding=embedder.embed(knowledge),
            consolidated_from=[m.id for m in short_mems[:20]],
        )
        self.db.add(memory)
        for m in short_mems:
            m.layer = "long"
            m.decay_rate = 0.1
        self.db.commit()
        self._decay_memories()
        logger.info(f"Weekly consolidation: 1 semantic memory from {len(short_mems)} short")
        return {"consolidated": 1, "source_memories": len(short_mems)}

    def _decay_memories(self):
        now = datetime.now(timezone.utc)
        for layer_name, cfg in LAYER_CONFIG.items():
            if cfg["ttl_hours"] is None:
                continue
            cutoff = now - timedelta(hours=cfg["ttl_hours"])
            expired = self.db.query(Memory).filter(
                Memory.layer == layer_name, Memory.created_at < cutoff).all()
            for m in expired:
                m.decay_rate = min(m.decay_rate * 1.5, 0.99)
                self.db.add(m)
        self.db.commit()