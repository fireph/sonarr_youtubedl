import pytest

from sytdl.config import ConfigError, load_config


def test_missing_config_creates_a_usable_template_next_to_target(tmp_path):
    config_path = tmp_path / "nested" / "config.yml"

    with pytest.raises(ConfigError, match="Configuration file not found"):
        load_config(config_path)

    template = config_path.with_name(config_path.name + ".template")
    assert template.is_file()
    generated = load_config(template)
    assert generated["sonarrytdl"]["cron"] == "*/15 * * * *"
    assert {"host", "port", "apikey"} <= generated["sonarr"].keys()
    assert generated["series"]


def test_malformed_config_fails_before_any_external_work(tmp_path):
    config_path = tmp_path / "config.yml"
    config_path.write_text("series: [not closed", encoding="utf-8")

    with pytest.raises(ConfigError, match="Unable to read"):
        load_config(config_path)
