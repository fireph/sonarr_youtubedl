import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


class YoutubeDLLogger(object):
    def __init__(self):
        self.logger = logging.getLogger("sonarr_youtubedl")

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def debug(self, msg: str) -> None:
        self.logger.debug(msg)

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)


def ytdl_hooks_debug(data):
    logger = logging.getLogger("sonarr_youtubedl")
    if data.get("status") == "finished" and data.get("filename"):
        logger.info("      Done downloading %s", os.path.basename(data["filename"]))
    if data.get("status") == "downloading":
        logger.debug(
            "      %s - %s - %s",
            data.get("filename", "unknown"),
            data.get("_percent_str", "unknown"),
            data.get("_eta_str", "unknown"),
        )


def ytdl_hooks(data):
    logger = logging.getLogger("sonarr_youtubedl")
    if data.get("status") == "finished" and data.get("filename"):
        logger.info("      Downloaded - %s", os.path.basename(data["filename"]))


def setup_logging(lf_enabled=True, lc_enabled=True, debugging=False):
    """Configure application logging without adding duplicate handlers."""
    log_level = logging.DEBUG if debugging else logging.INFO
    logger = logging.getLogger("sonarr_youtubedl")
    logger.setLevel(log_level)
    logger.propagate = False
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if lf_enabled and not any(h.name == "FileHandler" for h in logger.handlers):
        log_path = Path(
            os.environ.get(
                "LOGPATH",
                str(Path(__file__).resolve().parents[2] / "logs" / "sonarr_youtubedl.log"),
            )
        )
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            loggerfile = RotatingFileHandler(
                log_path, maxBytes=5_000_000, backupCount=5
            )
            loggerfile.set_name("FileHandler")
            loggerfile.setFormatter(log_format)
            logger.addHandler(loggerfile)
        except OSError as exc:
            if lc_enabled:
                print("Unable to open log file {}: {}".format(log_path, exc))

    if lc_enabled and not any(h.name == "StreamHandler" for h in logger.handlers):
        loggerconsole = logging.StreamHandler()
        loggerconsole.set_name("StreamHandler")
        loggerconsole.setFormatter(log_format)
        logger.addHandler(loggerconsole)

    for handler in logger.handlers:
        handler.setLevel(log_level)
    return logger

