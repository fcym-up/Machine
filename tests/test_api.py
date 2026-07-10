"""API 集成测试（FastAPI TestClient）。

测试完整的请求-响应流程，包括：
- 认证（有效/缺失/无效 API Key）
- Event CRUD、搜索和统计
- Memory CRUD 和语义搜索
- Knowledge 实体创建
- Intelligence 模式/风险/趋势端点
"""
from fastapi.testclient import TestClient

API_KEY = "machine-dev-key-change-me"


def _client():
    import app.main
    return TestClient(app.main.app)


class TestHealthCheck:
    def test_root_public(self):
        response = _client().get("/")
        assert response.status_code == 200

    def test_docs_public(self):
        response = _client().get("/docs")
        assert response.status_code == 200


class TestAuth:
    def test_api_without_key(self):
        response = _client().get("/api/v1/events")
        assert response.status_code == 401

    def test_api_with_wrong_key(self):
        response = _client().get("/api/v1/events", headers={"X-API-Key": "wrong"})
        assert response.status_code == 403

    def test_api_with_valid_key(self):
        response = _client().get("/api/v1/events", headers={"X-API-Key": API_KEY})
        assert response.status_code == 200


class TestEventAPI:
    def _headers(self):
        return {"X-API-Key": API_KEY}

    def test_create_event(self):
        response = _client().post(
            "/api/v1/events",
            json={"event_type": "user-action", "source": "browser", "payload": {"a": "t"}},
            headers=self._headers(),
        )
        assert response.status_code == 201

    def test_search(self):
        response = _client().get("/api/v1/events/search?event_type=user-action", headers=self._headers())
        assert response.status_code == 200

    def test_stats(self):
        response = _client().get("/api/v1/events/stats", headers=self._headers())
        assert response.status_code == 200


class TestMemoryAPI:
    def _headers(self):
        return {"X-API-Key": API_KEY}

    def test_create_memory(self):
        response = _client().post(
            "/api/v1/memories",
            json={"memory_type": "short", "content": "API test"},
            headers=self._headers(),
        )
        assert response.status_code == 201

    def test_search(self):
        response = _client().get("/api/v1/memories/search?query=test", headers=self._headers())
        assert response.status_code == 200


class TestKnowledgeAPI:
    def _headers(self):
        return {"X-API-Key": API_KEY}

    def test_create_entity(self):
        response = _client().post(
            "/api/v1/knowledge/entities",
            json={"name": "TestCorp", "entity_type": "organization"},
            headers=self._headers(),
        )
        assert response.status_code == 201


class TestIntelligenceAPI:
    def _headers(self):
        return {"X-API-Key": API_KEY}

    def test_patterns(self):
        response = _client().get("/api/v1/intelligence/patterns", headers=self._headers())
        assert response.status_code == 200

    def test_risk(self):
        response = _client().get("/api/v1/intelligence/risk", headers=self._headers())
        assert response.status_code == 200

    def test_trends(self):
        response = _client().get("/api/v1/intelligence/trends", headers=self._headers())
        assert response.status_code == 200
