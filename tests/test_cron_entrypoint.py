import os
import subprocess

import pytest

import cron_entrypoint
from cron_entrypoint import (
    build_crontab,
    get_cron_expression,
    validate_cron_expression,
)
from sytdl.config import ConfigError


def test_generated_job_is_non_overlapping_and_preserves_config_path():
    expression = validate_cron_expression("*/15 * * * *")
    crontab = build_crontab(expression, "/config/config file.yml")

    assert "*/15 * * * * /usr/bin/flock -n /var/lock/sonarr_youtube.lock" in crontab
    assert (
        "/bin/uv run --project /opt/sonarr_youtubedl --locked --no-dev --no-sync "
        "python -u /app/sonarr_youtubedl.py --config '/config/config file.yml'"
    ) in crontab
    assert ">> /proc/1/fd/1 2>> /proc/1/fd/2" in crontab


def test_cron_expression_cannot_inject_another_crontab_line():
    with pytest.raises(ConfigError):
        validate_cron_expression("* * * * *\nMALICIOUS=value")


def test_legacy_scan_interval_is_migrated_to_cron_with_a_warning():
    expression, warning = get_cron_expression(
        {"sonarrytdl": {"scan_interval": 20}}
    )

    assert expression == "*/20 * * * *"
    assert "deprecated" in warning
    assert 'cron: "*/20 * * * *"' in warning


def test_legacy_hourly_scan_interval_does_not_cause_a_restart_loop():
    expression, warning = get_cron_expression(
        {"sonarrytdl": {"scan_interval": 60}}
    )

    assert expression == "0 * * * *"
    assert 'cron: "0 * * * *"' in warning


def test_scheduler_installs_the_configured_job_before_starting_cron(
    tmp_path, monkeypatch
):
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        'sonarrytdl:\n  cron: "0 3 * * MON"\n',
        encoding="utf-8",
    )
    installed = {}

    def record_crontab(command, **kwargs):
        installed["command"] = command
        installed["input"] = kwargs["input"]
        assert kwargs["text"] is True
        assert kwargs["check"] is True

    class CronStarted(Exception):
        pass

    def start_cron(executable, arguments):
        assert executable == "cron"
        assert arguments == ["cron", "-f"]
        raise CronStarted

    monkeypatch.setenv("CONFIGPATH", str(config_path))
    monkeypatch.setattr(subprocess, "run", record_crontab)
    monkeypatch.setattr(os, "execvp", start_cron)

    with pytest.raises(CronStarted):
        cron_entrypoint.main()

    assert installed["command"] == ["crontab", "-"]
    assert installed["input"].startswith(
        "SHELL=/bin/sh\n"
        "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n"
        "0 3 * * MON "
    )
    assert "--config {}".format(config_path) in installed["input"]
