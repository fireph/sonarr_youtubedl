import logging

import requests

from .config import ConfigError, as_bool


logger = logging.getLogger("sonarr_youtubedl")
SONARR_API_PATH = "api/v3"  # Sonarr v4's current HTTP API contract.


class SonarrClient(object):
    """Small client for the Sonarr v4 endpoints used by this app."""

    def __init__(self, base_url, api_key, http=None):
        self.base_url = base_url
        self.api_url = "{}/{}".format(base_url, SONARR_API_PATH)
        self.api_key = api_key
        self.http = http if http is not None else requests

    @classmethod
    def from_config(cls, sonarr_cfg, http=None):
        if not isinstance(sonarr_cfg, dict):
            raise ConfigError("sonarr must be a YAML mapping")
        missing = [
            key
            for key in ("host", "port", "apikey")
            if sonarr_cfg.get(key) in (None, "")
        ]
        if missing:
            raise ConfigError(
                "Missing required Sonarr setting(s): {}".format(", ".join(missing))
            )

        scheme = "https" if as_bool(sonarr_cfg.get("ssl"), False) else "http"
        host = str(sonarr_cfg["host"]).strip().rstrip("/")
        if "://" in host:
            raise ConfigError("sonarr.host must not include http:// or https://")
        try:
            port = int(sonarr_cfg["port"])
        except (TypeError, ValueError) as exc:
            raise ConfigError("sonarr.port must be an integer") from exc
        if not 1 <= port <= 65535:
            raise ConfigError("sonarr.port must be between 1 and 65535")

        base_value = str(sonarr_cfg.get("basedir", "")).strip().strip("/")
        basedir = "/{}".format(base_value) if base_value else ""
        base_url = "{}://{}:{}{}".format(scheme, host, port, basedir)
        return cls(base_url, str(sonarr_cfg["apikey"]), http=http)

    def _headers(self):
        return {"X-Api-Key": self.api_key, "Accept": "application/json"}

    def request_get(self, endpoint, params=None):
        url = "{}/{}".format(self.api_url, endpoint.lstrip("/"))
        logger.debug("GET %s params=%s", url, params)
        response = self.http.get(
            url, headers=self._headers(), params=params, timeout=30
        )
        response.raise_for_status()
        return response

    def request_post(self, endpoint, jsondata=None):
        url = "{}/{}".format(self.api_url, endpoint.lstrip("/"))
        logger.debug("POST %s", url)
        response = self.http.post(
            url,
            headers={**self._headers(), "Content-Type": "application/json"},
            json=jsondata,
            timeout=30,
        )
        response.raise_for_status()
        return response

    def get_episodes(self, series_id):
        logger.debug("Getting episodes for Sonarr series ID %s", series_id)
        return self.request_get("episode", {"seriesId": series_id}).json()

    def get_series(self):
        logger.debug("Getting series from Sonarr v4")
        return self.request_get("series").json()

    def rescan_series(self, series_id):
        logger.debug("Requesting rescan for Sonarr series ID %s", series_id)
        data = {"name": "RescanSeries", "seriesId": int(series_id)}
        try:
            return self.request_post("command", data).json()
        except requests.RequestException as exc:
            logger.error("Downloaded file but failed to rescan series %s: %s", series_id, exc)
            return None
