"""Tests for GitHub Actions workflow files in oriz-mmi.

Validates structure, security, and consistency of CI/CD workflows.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / ".github" / "workflows"


def _load(name: str) -> str:
    return (WORKFLOWS_DIR / name).read_text(encoding="utf-8")


def _workflow_files() -> list[str]:
    if not WORKFLOWS_DIR.exists():
        return []
    return [f.name for f in WORKFLOWS_DIR.iterdir() if f.suffix in (".yml", ".yaml")]


# ── Structure ────────────────────────────────────────────────────────

class TestWorkflowStructure:
    @pytest.fixture(params=_workflow_files())
    def yaml_text(self, request: pytest.FixtureRequest) -> str:
        return _load(request.param)

    def test_has_name(self, yaml_text: str) -> None:
        assert re.search(r"^name:\s+", yaml_text, re.MULTILINE)

    def test_has_on_trigger(self, yaml_text: str) -> None:
        assert re.search(r"^on:", yaml_text, re.MULTILINE)

    def test_has_jobs(self, yaml_text: str) -> None:
        assert re.search(r"^jobs:", yaml_text, re.MULTILINE)


# ── ci.yml ──────────────────────────────────────────────────────────

class TestCiYml:
    @pytest.fixture(scope="class")
    def yaml(self) -> str:
        return _load("ci.yml")

    def test_triggers_on_push_and_pr(self, yaml: str) -> None:
        assert "push:" in yaml
        assert "pull_request:" in yaml

    def test_python_job_runs_pytest(self, yaml: str) -> None:
        assert "pytest" in yaml

    def test_web_job_builds(self, yaml: str) -> None:
        assert "npm run build" in yaml

    def test_read_only_permissions(self, yaml: str) -> None:
        assert "contents: read" in yaml

    def test_no_hardcoded_secrets(self, yaml: str) -> None:
        assert not re.search(r"ghp_[A-Za-z0-9]{36}", yaml)


# ── scrape.yml (mmi-watch) ──────────────────────────────────────────

class TestScrapeYml:
    @pytest.fixture(scope="class")
    def yaml(self) -> str:
        return _load("scrape.yml")

    def test_named_mmi_watch(self, yaml: str) -> None:
        assert "mmi-watch" in yaml

    def test_has_schedule(self, yaml: str) -> None:
        assert "schedule:" in yaml
        assert "cron:" in yaml

    def test_has_write_permissions(self, yaml: str) -> None:
        assert "contents: write" in yaml

    def test_installs_playwright(self, yaml: str) -> None:
        assert "playwright install chromium" in yaml

    def test_runs_tests(self, yaml: str) -> None:
        assert "pytest" in yaml

    def test_commits_data(self, yaml: str) -> None:
        assert "git commit" in yaml
        assert "git push" in yaml

    def test_telegram_failure_alert(self, yaml: str) -> None:
        assert "TELEGRAM_BOT_TOKEN" in yaml
        assert "Alert on failure" in yaml

    def test_no_hardcoded_secrets(self, yaml: str) -> None:
        assert not re.search(r"ghp_[A-Za-z0-9]{36}", yaml)


# ── notify-3h.yml ───────────────────────────────────────────────────

class TestNotify3hYml:
    @pytest.fixture(scope="class")
    def yaml(self) -> str:
        return _load("notify-3h.yml")

    def test_named_mmi_notify_3h(self, yaml: str) -> None:
        assert "mmi-notify-3h" in yaml

    def test_triggers_on_schedule(self, yaml: str) -> None:
        assert "schedule:" in yaml
        assert "cron:" in yaml

    def test_uses_comparison_model(self, yaml: str) -> None:
        """Must use Comparison model instead of removed prev kwarg."""
        assert "Comparison" in yaml
        assert "comparisons" in yaml

    def test_no_removed_prev_kwarg(self, yaml: str) -> None:
        """Must NOT pass prev= as a keyword argument to MmiReading."""
        # The old broken code had: MmiReading(..., prev=..., week_ago=...)
        assert not re.search(r"prev=latest", yaml)
        assert not re.search(r"week_ago=latest", yaml)
        assert not re.search(r"month_ago=latest", yaml)
        assert not re.search(r"year_ago=latest", yaml)

    def test_imports_mmi_reading(self, yaml: str) -> None:
        assert "from mmi_watch.models import MmiReading" in yaml

    def test_has_staleness_guard(self, yaml: str) -> None:
        assert "age_h" in yaml or "staleness" in yaml.lower() or "4h" in yaml

    def test_failure_alert(self, yaml: str) -> None:
        assert "TELEGRAM_BOT_TOKEN" in yaml

    def test_no_hardcoded_secrets(self, yaml: str) -> None:
        assert not re.search(r"ghp_[A-Za-z0-9]{36}", yaml)
        assert not re.search(r"sk-[A-Za-z0-9]{48}", yaml)


# ── Cross-workflow consistency ───────────────────────────────────────

class TestCrossWorkflowConsistency:
    def test_all_use_checkout_v4(self) -> None:
        for name in _workflow_files():
            yaml = _load(name)
            assert "actions/checkout@v4" in yaml, f"{name} missing checkout@v4"

    def test_no_hardcoded_tokens(self) -> None:
        for name in _workflow_files():
            yaml = _load(name)
            assert not re.search(r"ghp_[A-Za-z0-9]{36}", yaml), \
                f"{name} has hardcoded GitHub PAT"
