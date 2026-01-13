import pytest

from deployment_service_enhanced import DeploymentService


@pytest.mark.asyncio
async def test_deploy_to_vercel_without_token(monkeypatch):
    service = DeploymentService()
    service.vercel_token = None

    result = await service.deploy_to_vercel([], "Sample Project")

    assert result["success"] is False
    assert "VERCEL_TOKEN not configured" in result["error"]


@pytest.mark.asyncio
async def test_deploy_to_render_without_token(monkeypatch):
    service = DeploymentService()
    service.render_token = None

    result = await service.deploy_to_render([], "Sample Project", repo_url="https://example.com/repo.git")

    assert result["success"] is False
    assert "RENDER_API_KEY not configured" in result["error"]


@pytest.mark.asyncio
async def test_deploy_to_railway_without_token():
    service = DeploymentService()
    service.railway_token = None

    result = await service.deploy_to_railway([], "Sample Project")

    assert result["success"] is False
    assert "RAILWAY_TOKEN not configured" in result["error"]


@pytest.mark.asyncio
async def test_generate_deployment_config_structure():
    service = DeploymentService()
    configs = await service.generate_deployment_config(project_files=[], tech_stack={})

    assert {"vercel.json", "render.yaml", "docker-compose.yml", "frontend/Dockerfile", "backend/Dockerfile"} <= configs.keys()

    vercel = configs["vercel.json"]
    assert vercel["builds"][0]["use"] == "@vercel/static-build"
    assert vercel["routes"][0]["dest"] == "/api/$1"

    render_yaml = configs["render.yaml"]
    assert "{name}-frontend" in render_yaml
    assert "{name}-backend" in render_yaml

    docker_compose = configs["docker-compose.yml"]
    assert "frontend:" in docker_compose
    assert "backend:" in docker_compose


@pytest.mark.asyncio
async def test_check_deployment_status_without_tokens():
    service = DeploymentService()

    vercel_status = await service.check_deployment_status("vercel", "123")
    assert "VERCEL_TOKEN not configured" in vercel_status["error"]

    render_status = await service.check_deployment_status("render", "456")
    assert "RENDER_API_KEY not configured" in render_status["error"]

    unsupported = await service.check_deployment_status("heroku", "789")
    assert "Platform heroku not supported" in unsupported["error"]
