"""MemoryService — Memory 业务逻辑。

通过 SimpleEmbedder 生成 embedding，
实现语义相似度搜索（余弦相似度），
支持带验证的 CRUD 操作。
"""
from loguru import logger
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.repositories.memory_repository import MemoryRepository
from app.schemas.memory import MemoryCreate, MemoryUpdate
from app.services.embedding import embedder


class MemoryService:
    VALID_TYPES = {"short", "long", "semantic", "episode"}

    def __init__(self, db: Session):
        self.repo = MemoryRepository(db)
        self.db = db

    def create_memory(self, data: MemoryCreate) -> Memory:
        if data.memory_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid memory_type: {data.memory_type}")
        embedding = embedder.embed(data.content)
        memory = Memory(
            memory_type=data.memory_type,
            content=data.content,
            summary=data.summary,
            embedding=embedding,
            source_event_id=data.source_event_id,
            importance=data.importance,
            tags=data.tags,
        )
        created = self.repo.create(memory)
        logger.info(f"Memory created: id={created.id}, type={created.memory_type}")
        return created

    def get_memory(self, memory_id: int) -> Memory | None:
        return self.repo.get_by_id(memory_id)

    def list_memories(self, skip: int = 0, limit: int = 20, memory_type: str | None = None):
        items = self.repo.list(skip=skip, limit=limit, memory_type=memory_type)
        total = self.repo.count(memory_type=memory_type)
        return items, total

    def search_similar(self, query: str, limit: int = 5) -> list:
        query_vec = embedder.embed(query)
        all_memories = self.repo.list(skip=0, limit=1000)
        results = []
        for memory in all_memories:
            if memory.embedding:
                sim = embedder.similarity(query_vec, memory.embedding)
                if sim > 0.01:
                    results.append((memory, sim))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def update_memory(self, memory_id: int, data: MemoryUpdate) -> Memory | None:
        memory = self.repo.get_by_id(memory_id)
        if memory is None:
            return None
        if data.content is not None:
            memory.content = data.content
            memory.embedding = embedder.embed(data.content)
        if data.summary is not None:
            memory.summary = data.summary
        if data.importance is not None:
            memory.importance = data.importance
        if data.tags is not None:
            memory.tags = data.tags
        updated = self.repo.update(memory)
        logger.info(f"Memory updated: id={memory_id}")
        return updated

    def delete_memory(self, memory_id: int) -> bool:
        memory = self.repo.get_by_id(memory_id)
        if memory is None:
            return False
        self.repo.delete(memory)
        logger.info(f"Memory deleted: id={memory_id}")
        return True
