"""Agent 系统集成测试。

测试所有 Agent 的规则引擎回退模式（无需 LLM API Key）。
"""

from fastapi.testclient import TestClient

API_KEY = "machine-dev-key-change-me"


def _c():
    import app.main
    return TestClient(app.main.app)


def _h():
    return {"X-API-Key": API_KEY}


class TestAgentList:
    def test_list_agents(self):
        r = _c().get("/api/v1/agents/", headers=_h())
        assert r.status_code == 200
        names = [a["name"] for a in r.json()["agents"]]
        assert "ResearchAgent" in names
        assert len(r.json()["agents"]) == 5


class TestResearchAgent:
    def test_research(self):
        r = _c().post("/api/v1/agents/research", json={"task": "分析Python新特性"}, headers=_h())
        assert r.status_code == 200
        assert r.json()["success"] is True


class TestCodeAgent:
    def test_code(self):
        r = _c().post("/api/v1/agents/code", json={"task": "def foo(): pass"}, headers=_h())
        assert r.status_code == 200
        assert r.json()["success"] is True
        assert "def " in r.json()["result"].lower()


class TestMemoryAgent:
    def test_memory(self):
        r = _c().post("/api/v1/agents/memory", json={"task": "总结记忆"}, headers=_h())
        assert r.status_code == 200
        assert r.json()["success"] is True


class TestPlannerAgent:
    def test_plan(self):
        r = _c().post("/api/v1/agents/plan", json={"task": "开发聊天机器人"}, headers=_h())
        assert r.status_code == 200
        assert r.json()["success"] is True


class TestSecurityAgent:
    def test_security(self):
        r = _c().post("/api/v1/agents/security", json={"task": "分析安全风险"}, headers=_h())
        assert r.status_code == 200
        assert r.json()["success"] is True
