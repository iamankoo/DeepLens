"""Focused test for WorkflowManager's cooperative time-budget enforcement
(Settings.RESEARCH_TIME_BUDGET_SECONDS / RESEARCH_JOB_TIMEOUT_SECONDS) — the
fix for research runs that could previously run unbounded (up to the old
1800s RQ job timeout) instead of the product-required 120s hard maximum.
Uses a monkeypatched near-zero budget so this doesn't depend on a real
pipeline run actually taking over a minute to reproduce."""

import pytest

from app.core.exceptions import ResearchTimeoutError
from app.workflows import workflow_manager as wm_module
from app.workflows.workflow_manager import WorkflowManager


def test_time_budget_stops_pipeline_between_nodes(monkeypatch):
    """With the budget set to 0, the very first node boundary (right after
    planner_node completes, a real LLM call) must be enough to raise
    ResearchTimeoutError — proving the cooperative check actually runs
    between nodes rather than only at the very end."""

    monkeypatch.setattr(wm_module.settings, "RESEARCH_TIME_BUDGET_SECONDS", 0)

    manager = WorkflowManager(max_iterations=1)

    with pytest.raises(ResearchTimeoutError, match="time budget"):
        manager.run("What is the capital of France?")


def test_time_budget_error_names_the_last_completed_stage(monkeypatch):
    """The error message must name a real node, not a stale placeholder —
    regression test for a bug where `last_node` only updated when an
    `on_step` callback was supplied, so calling WorkflowManager.run()
    without one (as this project's own e2e test does) always reported
    'planner' regardless of how far the pipeline actually got."""

    monkeypatch.setattr(wm_module.settings, "RESEARCH_TIME_BUDGET_SECONDS", 0)

    manager = WorkflowManager(max_iterations=1)

    with pytest.raises(ResearchTimeoutError) as exc_info:
        manager.run("What is the capital of France?", on_step=None)

    assert "planner" in str(exc_info.value)


def test_settings_clamp_stale_env_values_to_hard_ceiling():
    """RESEARCH_JOB_TIMEOUT_SECONDS and LLM_REQUEST_TIMEOUT_SECONDS must
    never exceed their hard product ceilings (120s / 30s) even if a
    deployment environment's variables still carry pre-120s-budget values —
    reproduced live against this project's own backend/.env, which still had
    RESEARCH_JOB_TIMEOUT_SECONDS=1800 and LLM_REQUEST_TIMEOUT_SECONDS=60
    before this was noticed."""

    from app.core.config import settings

    assert settings.RESEARCH_JOB_TIMEOUT_SECONDS <= 120
    assert settings.LLM_REQUEST_TIMEOUT_SECONDS <= 30
    assert settings.RESEARCH_TIME_BUDGET_SECONDS < settings.RESEARCH_JOB_TIMEOUT_SECONDS
