import datetime
import re
import unicodedata
from datetime import timezone

from .config import ConfigError


_APOSTROPHE_TRANSLATION = str.maketrans(
    {
        "’": "'",
        "‘": "'",
        "ʼ": "'",
        "＇": "'",
    }
)


def parse_air_date(value):
    """Parse a Sonarr UTC timestamp into an aware UTC datetime."""
    if not value:
        return None
    try:
        parsed = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid Sonarr airDateUtc value {!r}".format(value)) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def offset_air_date(airdate, offset):
    """Adjust an episode air date by the configured offset."""
    offset = offset or {}
    try:
        delta = datetime.timedelta(
            weeks=int(offset.get("weeks", 0)),
            days=int(offset.get("days", 0)),
            hours=int(offset.get("hours", 0)),
            minutes=int(offset.get("minutes", 0)),
        )
    except (TypeError, ValueError) as exc:
        raise ConfigError("Episode offset values must be integers") from exc
    return airdate + delta


def sanitize_filename_part(value):
    """Return a string that is safe to use as part of a media filename."""
    value = str(value).replace(" ", ".")
    value = re.sub(r'[<>:"/\\|?*]', "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip(". ")


def normalize_title(value):
    """Return a canonical title for conservative, punctuation-insensitive matching."""
    value = unicodedata.normalize("NFKC", str(value))
    value = value.casefold().translate(_APOSTROPHE_TRANSLATION)
    value = value.replace("&", " and ")
    value = re.sub(r"(?<=\w)'(?=\w)", "", value)
    value = re.sub(r"[\W_]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def title_pattern(value):
    """Build a whole-title regex from a normalized episode title."""
    normalized = normalize_title(value)
    if not normalized:
        return r"(?!)"
    body = r"\s+".join(re.escape(token) for token in normalized.split())
    return r"(?<!\w){}(?!\w)".format(body)
