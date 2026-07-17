"""Install the configured cron job, then replace this process with cron."""

import os
import re
import shlex
import subprocess
import sys

from sytdl.config import ConfigError, get_config_path, load_config


CRON_FIELD = re.compile(r"^[A-Za-z0-9*/?,\-]+$")


def validate_cron_expression(expression):
    expression = str(expression).strip()
    fields = expression.split()
    if len(fields) != 5 or any(not CRON_FIELD.fullmatch(field) for field in fields):
        raise ConfigError(
            "sonarrytdl.cron must be a standard five-field cron expression"
        )
    return " ".join(fields)


def get_cron_expression(cfg):
    app_cfg = cfg.get("sonarrytdl", {})
    if not isinstance(app_cfg, dict):
        raise ConfigError("sonarrytdl must be a YAML mapping")
    expression = app_cfg.get("cron")
    if expression is not None:
        return validate_cron_expression(expression), None

    # Let existing installations boot once after upgrading, while directing them
    # to the new explicit setting. The Python application itself no longer loops.
    legacy_interval = app_cfg.get("scan_interval")
    if legacy_interval is None:
        raise ConfigError("sonarrytdl.cron is required")
    try:
        minutes = int(legacy_interval)
    except (TypeError, ValueError) as exc:
        raise ConfigError("sonarrytdl.scan_interval must be an integer") from exc
    if minutes < 1 or minutes > 59:
        raise ConfigError(
            "Replace sonarrytdl.scan_interval with a five-field sonarrytdl.cron value"
        )
    return "*/{} * * * *".format(minutes), (
        "sonarrytdl.scan_interval is deprecated; replace it with cron: \"*/{} * * * *\""
    ).format(minutes)


def build_crontab(expression, config_path):
    command = " ".join(
        [
            "/usr/bin/flock",
            "-n",
            "/var/lock/sonarr_youtube.lock",
            "/bin/uv",
            "run",
            "--project",
            "/opt/sonarr_youtubedl",
            "--locked",
            "--no-dev",
            "--no-sync",
            "python",
            "-u",
            "/app/sonarr_youtubedl.py",
            "--config",
            shlex.quote(str(config_path)),
            ">> /proc/1/fd/1 2>> /proc/1/fd/2",
        ]
    )
    return "\n".join(
        [
            "SHELL=/bin/sh",
            "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "{} {}".format(expression, command),
            "",
        ]
    )


def main():
    config_path = get_config_path()
    try:
        cfg = load_config(config_path)
        expression, warning = get_cron_expression(cfg)
        crontab = build_crontab(expression, config_path)
        subprocess.run(
            ["crontab", "-"],
            input=crontab,
            text=True,
            check=True,
        )
    except (ConfigError, OSError, subprocess.CalledProcessError) as exc:
        print("Unable to start scheduler: {}".format(exc), file=sys.stderr)
        return 2

    if warning:
        print("WARNING: {}".format(warning), flush=True)
    print(
        "Installed cron schedule '{}' from {}".format(expression, config_path),
        flush=True,
    )
    os.execvp("cron", ["cron", "-f"])


if __name__ == "__main__":
    sys.exit(main())
