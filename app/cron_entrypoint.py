"""Install the configured cron job, then replace this process with cron."""

import os
import re
import shlex
import subprocess
import sys

from sytdl.config import ConfigError, as_bool, get_config_path, load_config


CRON_FIELD = re.compile(r"^[A-Za-z0-9*/?,\-]+$")
LOCK_FILE = "/var/lock/sonarr_youtube.lock"


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
    if minutes < 1:
        raise ConfigError("sonarrytdl.scan_interval must be at least one minute")

    if minutes < 60:
        expression = "*/{} * * * *".format(minutes)
    elif minutes == 60:
        expression = "0 * * * *"
    elif minutes < 24 * 60 and minutes % 60 == 0:
        expression = "0 */{} * * *".format(minutes // 60)
    elif minutes == 24 * 60:
        expression = "0 0 * * *"
    else:
        raise ConfigError(
            "sonarrytdl.scan_interval={} cannot be represented by one standard cron "
            "expression; replace it with a five-field sonarrytdl.cron value".format(
                minutes
            )
        )
    return expression, (
        'sonarrytdl.scan_interval is deprecated; replace it with cron: "{}"'
    ).format(expression)


def get_run_on_start(cfg):
    app_cfg = cfg.get("sonarrytdl", {})
    if not isinstance(app_cfg, dict):
        raise ConfigError("sonarrytdl must be a YAML mapping")
    return as_bool(app_cfg.get("run_on_start"), True)


def build_run_command(config_path):
    return [
        "/usr/bin/flock",
        "-n",
        LOCK_FILE,
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
        str(config_path),
    ]


def build_crontab(expression, config_path):
    command = "{} {}".format(
        " ".join(shlex.quote(value) for value in build_run_command(config_path)),
        ">> /proc/1/fd/1 2>> /proc/1/fd/2",
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
        run_on_start = get_run_on_start(cfg)
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
    if run_on_start:
        print("Running initial scan", flush=True)
        try:
            initial_run = subprocess.run(
                build_run_command(config_path),
                check=False,
            )
        except OSError as exc:
            print(
                "WARNING: Initial scan could not start: {}; cron will continue".format(
                    exc
                ),
                file=sys.stderr,
                flush=True,
            )
        else:
            if initial_run.returncode:
                print(
                    "WARNING: Initial scan exited with status {}; cron will "
                    "continue".format(initial_run.returncode),
                    file=sys.stderr,
                    flush=True,
                )
    else:
        print("Initial scan disabled by sonarrytdl.run_on_start", flush=True)
    os.execvp("cron", ["cron", "-f"])


if __name__ == "__main__":
    sys.exit(main())
