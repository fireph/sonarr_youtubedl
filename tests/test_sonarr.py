from unittest.mock import Mock

import requests

from sytdl.sonarr import SonarrClient


def test_sonarr_v4_request_uses_normalized_url_and_api_key_header():
    response = Mock()
    response.raise_for_status.return_value = None
    http = Mock()
    http.get.return_value = response
    client = SonarrClient.from_config(
        {
            "host": "sonarr.example.test",
            "port": 443,
            "apikey": "secret",
            "ssl": True,
            "basedir": "/sonarr/",
        },
        http=http,
    )

    assert client.get_series() is response.json.return_value
    http.get.assert_called_once_with(
        "https://sonarr.example.test:443/sonarr/api/v3/series",
        headers={"X-Api-Key": "secret", "Accept": "application/json"},
        params=None,
        timeout=30,
    )


def test_rescan_uses_the_sonarr_v4_command_contract():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"id": 99, "status": "queued"}
    http = Mock()
    http.post.return_value = response
    client = SonarrClient("http://sonarr:8989", "secret", http=http)

    result = client.rescan_series(7)

    assert result == {"id": 99, "status": "queued"}
    http.post.assert_called_once_with(
        "http://sonarr:8989/api/v3/command",
        headers={
            "X-Api-Key": "secret",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json={"name": "RescanSeries", "seriesId": 7},
        timeout=30,
    )


def test_rescan_api_failure_does_not_lose_a_completed_download(caplog):
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("Sonarr unavailable")
    http = Mock()
    http.post.return_value = response
    client = SonarrClient("http://sonarr:8989", "secret", http=http)

    assert client.rescan_series(7) is None
    assert "Downloaded file but failed to rescan series 7" in caplog.text
