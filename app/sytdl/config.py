import logging
import os
import shutil
from pathlib import Path

import yaml


class ConfigError(ValueError):
    """Raised when config.yml is missing or invalid."""


def get_config_path(config_file=None):
    return Path(config_file or os.environ.get("CONFIGPATH", "/config/config.yml"))


def _copy_config_template(config_file):
    target = Path(str(config_file) + ".template")
    bundled_template = Path(__file__).resolve().parents[1] / "config.yml.template"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() and bundled_template.exists():
        shutil.copyfile(bundled_template, target)
    return target


def load_config(config_file=None):
    """Load config.yml safely and create a template beside it when missing."""
    logger = logging.getLogger("sonarr_youtubedl")
    config_path = get_config_path(config_file)

    if not config_path.is_file():
        template_path = _copy_config_template(config_path)
        raise ConfigError(
            "Configuration file not found at {}. Create it using {} as an example.".format(
                config_path, template_path
            )
        )

    logger.info("Configuration found at %s", config_path)
    try:
        with config_path.open("r", encoding="utf-8") as ymlfile:
            cfg = yaml.safe_load(ymlfile)
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError("Unable to read {}: {}".format(config_path, exc)) from exc

    if not isinstance(cfg, dict):
        raise ConfigError("{} must contain a YAML mapping".format(config_path))
    return cfg


def as_bool(value, default=False):
    """Coerce YAML booleans and common string forms to a real bool."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "on", "1"}:
            return True
        if normalized in {"false", "no", "off", "0"}:
            return False
    raise ConfigError("Expected a boolean value, got {!r}".format(value))

