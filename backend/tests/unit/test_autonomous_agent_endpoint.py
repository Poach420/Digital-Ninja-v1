import json

import pytest

from server import app, User, get_current_user


class FakeProjectsCollection:
    def __init__(self):
        self.documents = {}
        self.last_inserted = None

    async def insert_one(self, document):
        self.last_inserted = document
        self.documents[document["project_id"]] = document


class FakeDatabase:
    def __init__(self):
        self.projects = FakeProjectsCollection()

    async def command(self, *_args, **_kwargs):
        return {"ok": 1}


class DummyAutonomousAgent:
    def __init__(self, *_, **__):
        pass

    async def run_autonomous_build(self, prompt, progress_callback, max_duration_minutes):
        await progress_callback({
            "message": f"Received prompt: {prompt}",
            "level": "info",
            "timestamp": "2026-01-13T00:00:00"
        })
        return {
            "status": "success",
            "files": [{"path": "frontend/src/App.jsx", "content": "export const App = () => null;"}],
            "test_results": {"total_tests": 0},
            "iterations": 1,
            "duration_minutes": 0.1,
            "fixes_applied": []
        }


@pytest.mark.asyncio
async def test_autonomous_agent_stream_success(monkeypatch):
    fake_db = FakeDatabase()
    monkeypatch.setattr("server.db", fake_db, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("autonomous_agent.AutonomousAgent", DummyAutonomousAgent, raising=False)

    async def override_current_user():
        return User(
            user_id="user_test",
            email="user@example.com",
            name="Test User",
            created_at="2026-01-13T00:00:00",
            team_id="team_test",
            role="owner",
            plan="pro",
            picture=""
        )

    app.dependency_overrides[get_current_user] = override_current_user

    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        with client.stream(
            "POST",
            "/api/projects/autonomous/stream",
            headers={"Authorization": "Bearer fake"},
            json={
                "prompt": "Build a status page",
                "tech_stack": {"frontend": "React", "backend": "FastAPI", "database": "MongoDB"}
            }
        ) as stream:
            events = [line for line in stream.iter_lines() if line.startswith("data:")]

    app.dependency_overrides.pop(get_current_user, None)

    assert any("Autonomous Agent starting" in e for e in events)

    complete_events = [json.loads(e.replace("data: ", "")) for e in events if "\"type\": \"complete\"" in e]
    assert complete_events, "Expected a completion event from autonomous build stream"
    complete_payload = complete_events[0]
    assert complete_payload["project_id"] == fake_db.projects.last_inserted["project_id"]
    assert fake_db.projects.last_inserted["autonomous_build"] is True