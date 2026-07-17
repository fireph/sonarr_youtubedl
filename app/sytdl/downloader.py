import logging
import os
import re
from pathlib import Path

try:
    import yt_dlp
except ModuleNotFoundError:  # Unit tests can inject a lightweight adapter.
    yt_dlp = None

from .logging_utils import (
    YoutubeDLLogger,
    ytdl_hooks,
    ytdl_hooks_debug,
)
from .media import normalize_title, sanitize_filename_part, title_pattern


logger = logging.getLogger("sonarr_youtubedl")


class EpisodeDownloader(object):
    """Find and download configured episodes through yt-dlp."""

    def __init__(
        self,
        default_format,
        config_file,
        debug=False,
        ytdl_factory=None,
        sonarr_root=None,
    ):
        self.default_format = default_format
        self.config_file = Path(config_file)
        self.debug = debug
        if ytdl_factory is None:
            if yt_dlp is None:
                raise RuntimeError("yt-dlp is required to run downloads")
            ytdl_factory = yt_dlp.YoutubeDL
        self.ytdl_factory = ytdl_factory
        self.sonarr_root = (
            sonarr_root or os.environ.get("SONARR_ROOT", "/sonarr_root")
        ).rstrip("/")

    def _add_cookie(self, options, cookies=None):
        if cookies is None:
            return options
        cookie_path = Path(str(cookies)).expanduser()
        if not cookie_path.is_absolute():
            cookie_path = self.config_file.parent / cookie_path
        cookie_path = cookie_path.resolve()
        if cookie_path.is_file():
            options["cookiefile"] = str(cookie_path)
            logger.debug("Cookies file used: %s", cookie_path)
        else:
            logger.warning("Configured cookies file does not exist: %s", cookie_path)
        return options

    def _search_options(self, series):
        options = {
            "ignoreerrors": True,
            "playlistreverse": series["playlistreverse"],
            "extract_flat": True,
            "quiet": True,
        }
        if self.debug:
            options.update(
                {
                    "quiet": False,
                    "logger": YoutubeDLLogger(),
                    "progress_hooks": [ytdl_hooks],
                }
            )
        self._add_cookie(options, series.get("cookies_file"))
        logger.debug("yt-dlp episode matching options: %s", options)
        return options

    @staticmethod
    def _title_matches(title, pattern, site_match=None, site_replace=""):
        if not title:
            return False
        candidate = str(title)
        if site_match is not None:
            candidate = re.sub(site_match, site_replace, candidate)
        candidate = normalize_title(candidate)
        return re.search(pattern, candidate) is not None

    @staticmethod
    def _series_urls(series):
        """Return normalized source URLs, including legacy single-URL series."""
        urls = series.get("urls")
        if urls is None:
            urls = series["url"]
            if isinstance(urls, list):
                return list(urls)
            return [urls]
        return list(urls)

    def _extract_series(self, series, search_options=None, source_url=None):
        """Fetch one configured channel or playlist."""
        options = search_options or self._search_options(series)
        source_url = source_url or self._series_urls(series)[0]
        try:
            with self.ytdl_factory(options) as ydl:
                return ydl.extract_info(source_url, download=False)
        except Exception as exc:
            logger.error("yt-dlp could not inspect %s: %s", source_url, exc)
            return None

    def _find_episode_in_result(self, series, episode, result, source_url=None):
        if not isinstance(result, dict):
            return None
        pattern = title_pattern(episode["title"])
        site_match = series.get("site_regex_match")
        site_replace = series.get("site_regex_replace", "")
        entries = result.get("entries")
        if entries is not None:
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                if self._title_matches(
                    entry.get("title"), pattern, site_match, site_replace
                ):
                    download_url = (
                        entry.get("webpage_url")
                        or entry.get("original_url")
                        or entry.get("url")
                    )
                    if download_url:
                        return download_url
            return None

        if self._title_matches(
            result.get("title"), pattern, site_match, site_replace
        ):
            return (
                result.get("webpage_url")
                or result.get("original_url")
                or result.get("url")
                or source_url
                or self._series_urls(series)[0]
            )
        return None

    def find_episode(self, series, episode, search_options=None):
        """Return the matching video URL, or None when the episode is absent."""
        options = search_options or self._search_options(series)
        for source_url in self._series_urls(series):
            result = self._extract_series(series, options, source_url)
            download_url = self._find_episode_in_result(
                series, episode, result, source_url
            )
            if download_url:
                return download_url
        return None

    def _download_options(self, series, episode):
        series_path = str(series["path"])
        if not series_path.startswith("/"):
            series_path = "/" + series_path
        season_folder = (
            "Specials"
            if episode["seasonNumber"] == 0
            else "Season {}".format(episode["seasonNumber"])
        )
        outtmpl = (
            "{}{}/{}/{}.S{:02d}E{:02d}.{}.WEBDL-%(height)sp.%(acodec)s."
            "%(vcodec)s-SonarrYTDL.%(ext)s"
        ).format(
            self.sonarr_root,
            series_path,
            season_folder,
            sanitize_filename_part(series["title"]),
            episode["seasonNumber"],
            episode["episodeNumber"],
            sanitize_filename_part(episode["title"]),
        )
        options = {
            "format": series.get("format", self.default_format),
            "quiet": True,
            "noprogress": True,
            "merge_output_format": "mkv",
            "outtmpl": outtmpl,
            "progress_hooks": [ytdl_hooks],
            "noplaylist": True,
            "retries": 10,
            "fragment_retries": 10,
            "postprocessors": [
                {"key": "FFmpegVideoRemuxer", "preferedformat": "mkv"}
            ],
        }
        self._add_cookie(options, series.get("cookies_file"))
        if series.get("subtitles", False):
            options.update(
                {
                    "writesubtitles": True,
                    "writeautomaticsub": series["subtitles_autogenerated"],
                    "subtitleslangs": series["subtitles_languages"],
                    "sleep_interval": 2,
                    "sleep_interval_requests": 3,
                }
            )
            options["postprocessors"].extend(
                [
                    {"key": "FFmpegSubtitlesConvertor", "format": "srt"},
                    {"key": "FFmpegEmbedSubtitle"},
                ]
            )
        if self.debug:
            options.update(
                {
                    "quiet": False,
                    "logger": YoutubeDLLogger(),
                    "progress_hooks": [ytdl_hooks_debug],
                }
            )
        return options

    def download_episode(self, series, episode, download_url):
        """Download one matched episode and return whether it succeeded."""
        options = self._download_options(series, episode)
        logger.debug("yt-dlp download options: %s", options)
        try:
            with self.ytdl_factory(options) as ydl:
                result_code = ydl.download([download_url])
            if result_code not in (None, 0):
                raise RuntimeError("yt-dlp returned status {}".format(result_code))
        except Exception as exc:
            logger.error("      Failed - %s - %s", episode["title"], exc)
            return False
        logger.info("      Downloaded - %s", episode["title"])
        return True

    def download_series(self, series, episodes):
        """Find and download all wanted episodes belonging to one series."""
        wanted = [ep for ep in episodes if ep["seriesId"] == series["id"]]
        if not wanted:
            return 0

        downloaded = 0
        search_options = self._search_options(series)
        search_results = [
            (
                source_url,
                self._extract_series(series, search_options, source_url),
            )
            for source_url in self._series_urls(series)
        ]
        for index, episode in enumerate(wanted, start=1):
            download_url = None
            for source_url, search_result in search_results:
                download_url = self._find_episode_in_result(
                    series, episode, search_result, source_url
                )
                if download_url:
                    break
            if not download_url:
                logger.info("    %d: Missing - %s", index, episode["title"])
                continue
            logger.info("    %d: Found - %s", index, episode["title"])
            if self.download_episode(series, episode, download_url):
                downloaded += 1
        return downloaded
