"""tests/test_notion.py - Tests for Notion read-only integration."""

import pytest
from app.integrations.notion_client import redact_text, truncate_preview


def test_redact_text():
    text = "Email: test@example.com, Token: sk-12345678901234567890, Auth: Bearer abcdef123456"
    redacted = redact_text(text)
    assert "***@***" in redacted
    assert "***REDACTED***" in redacted
    assert "sk-12345678901234567890" not in redacted


def test_truncate_preview():
    text = "This is a long text without sensitive data that should be truncated properly after redaction."
    preview = truncate_preview(text, 50)
    assert len(preview) == 53  # 50 + ...


def test_truncate_short():
    text = "Short text"
    preview = truncate_preview(text, 120)
    assert preview == "Short text"


# Contract tests (mocked, since no real Notion)
# Placeholder: assume env vars set for tests
@pytest.mark.asyncio
async def test_agents_endpoint_missing_config():
    # Mock missing env
    import os
    original = os.environ.get("NOTION_DB_ORDO36_AGENTS_ID")
    os.environ["NOTION_DB_ORDO36_AGENTS_ID"] = ""
    try:
        from app.integrations.notion_client import get_agents
        with pytest.raises(Exception, match="MISSING_CONFIG"):
            await get_agents()
    finally:
        if original:
            os.environ["NOTION_DB_ORDO36_AGENTS_ID"] = original


@pytest.mark.asyncio
async def test_governance_summary_no_rows():
    from app.integrations.notion_client import get_governance_summary
    summary = await get_governance_summary()
    assert "logos_count" in summary
    assert "deep_links" in summary
    # No row listing


@pytest.mark.asyncio
async def test_self_test_missing_env():
    import os
    # Temporarily unset a required env
    original = os.environ.get("NOTION_TOKEN")
    os.environ["NOTION_TOKEN"] = ""
    try:
        from app.integrations.notion_client import self_test
        results = await self_test()
        assert len(results) == 1
        assert results[0]["check_name"] == "env_validation"
        assert results[0]["status"] == "blocked"
        assert results[0]["reason_code"] == "MISSING_ENV_VARS"
    finally:
        if original:
            os.environ["NOTION_TOKEN"] = original


@pytest.mark.asyncio
async def test_self_test_all_pass():
    # Assuming envs are set (in test env), and mocks succeed
    from app.integrations.notion_client import self_test
    results = await self_test()
    assert len(results) > 1  # env + surfaces
    # In real, mock the functions to pass
    # For now, depends on actual env
    assert not any("rows" in k for k in summary.keys())


# Smoke test placeholder
def test_smoke_health():
    # In real, call /health then /v1/notion/agents
    pass