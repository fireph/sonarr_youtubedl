"""Command-line entry point for one sonarr_youtubedl run."""

import argparse
import logging
import sys

import requests

from sytdl.config import ConfigError
from sytdl.logging_utils import setup_logging
from sytdl.service import SonarrYTDLService


logger = logging.getLogger("sonarr_youtubedl")


def run_once(config_file=None, debug=False):
    return SonarrYTDLService(
        config_file=config_file, debug_override=debug
    ).run()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Download missing Sonarr v4 web-series episodes once"
    )
    parser.add_argument("--config", help="Path to config.yml (defaults to CONFIGPATH)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args(argv)

    setup_logging(True, True, args.debug)
    logger.info("Starting scheduled run")
    try:
        run_once(args.config, args.debug)
    except ConfigError as exc:
        logger.critical("Configuration error: %s", exc)
        return 2
    except requests.RequestException as exc:
        response = getattr(exc, "response", None)
        details = ""
        if response is not None:
            details = " (HTTP {}: {})".format(response.status_code, response.text[:500])
        logger.critical("Sonarr v4 API request failed: %s%s", exc, details)
        return 1
    except Exception:
        logger.exception("Scheduled run failed")
        return 1
    logger.info("Scheduled run complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
