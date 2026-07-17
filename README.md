<div align="center">

<img src="https://raw.githubusercontent.com/fireph/sonarr_youtubedl/refs/heads/main/logo.png" alt="sonarr_youtubedl Logo" width="180" height="180">

# sonarr_youtubedl

*Automatically download web series for Sonarr using YT-DLP*

![Docker Pulls](https://img.shields.io/docker/pulls/dungfu/sonarr_youtubedl?style=flat-square)
![Docker Stars](https://img.shields.io/docker/stars/dungfu/sonarr_youtubedl?style=flat-square)
![Docker Image Size](https://img.shields.io/docker/image-size/dungfu/sonarr_youtubedl/latest)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/fireph/sonarr_youtubedl/main.yaml?style=flat-square)

[![Docker Hub](https://img.shields.io/badge/Open%20On-DockerHub-blue?style=for-the-badge&logo=docker)](https://hub.docker.com/r/dungfu/sonarr_youtubedl)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?style=for-the-badge&logo=github)](https://github.com/fireph/sonarr_youtubedl)

</div>

---

## Overview

**sonarr_youtubedl** is a [Sonarr v4](https://sonarr.tv/) companion script that enables automatic downloading of web series normally unavailable to Sonarr. Leveraging [YT-DLP](https://github.com/yt-dlp/yt-dlp), it downloads your favorite web series from hundreds of [supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

## Features

- **Web Series Download** - Access online sources unavailable to Sonarr
- **Format Control** - Specify video format globally or per series
- **Automatic Downloads** - New episodes downloaded as they become available
- **Low Idle Memory** - A cron daemon starts the app only on the configured schedule
- **Seamless Integration** - Direct import to Sonarr with media server updates
- **Time Offset Support** - Handle prerelease series with custom timing
- **Cookie Support** - Pass cookies.txt for authenticated site access

## Quick Start Guide

1. **Find Your Series** - Locate a series on any [YT-DLP supported site](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
2. **Add to Sonarr** - Add the series to Sonarr and monitor desired episodes
3. **Configure** - Edit `config.yml` to specify Sonarr location, target series, and source URLs
4. **TVDB Matching** - Ensure episode titles match TVDB exactly (usually automatic)

## Supported Architectures

| Architecture | Available Tags |
|:------------:|:-------------:|
| **x86-64** | `latest` |
| **ARM64** | `latest` |

## Version Tags

| Tag | Description |
|:---:|:----------:|
| `latest` | Current stable release |

---

## Installation

> [!NOTE]
> **Prerequisites**: Docker must be installed on your system. New to Docker? [Get started here](https://docs.docker.com/get-started/).

### Docker CLI

```bash
docker create \
  --name=sonarr_youtubedl \
  -v /path/to/data:/config \
  -v /path/to/sonarrmedia:/sonarr_root \
  -v /path/to/logs:/logs \
  --restart unless-stopped \
  dungfu/sonarr_youtubedl
```

### Docker Compose

```yaml
---
version: '3.4'
services:
  sonarr_youtubedl:
    image: dungfu/sonarr_youtubedl
    container_name: sonarr_youtubedl
    restart: unless-stopped
    volumes:
      - /path/to/data:/config
      - /path/to/sonarrmedia:/sonarr_root
      - /path/to/logs:/logs
```

---

## Configuration

### Volume Mapping

| Volume | Purpose | Required |
|:------:|:--------|:--------:|
| `/config` | Configuration files | ✅ |
| `/sonarr_root` | Sonarr library root | ✅ |
| `/logs` | Application logs | ✅ |

### Understanding `sonarr_root`

> [!IMPORTANT]
> The `sonarr_root` volume maps to Sonarr's root library directory.

**Example Setup:**
- If Sonarr saves to: `/mnt/video/tv/Helluva Boss/`
- Sonarr shows path as: `/tv/Helluva Boss/`
- Then `sonarr_root` = `/mnt/video/`

**For different filesystem paths** (e.g., TrueNAS):
```bash
-v /parent/os/path/to/video:/sonarr_root/mnt/video
```

---

## Configuration File

On first run, a template configuration file will be created automatically.

1. Locate the template: [`config.yml.template`](./app/config.yml.template)
2. Copy to `config.yml` in your config directory
3. Edit the configuration to match your setup

The scheduler uses a standard five-field cron expression:

```yaml
sonarrytdl:
  cron: "*/15 * * * *"  # every 15 minutes
  debug: false
```

Some other useful schedules are `0 * * * *` (hourly), `0 3 * * *` (daily at 03:00), and `0 3 * * MON` (Mondays at 03:00). Cron uses the container's local timezone, which is UTC unless you configure the container otherwise. Restart the container after changing the cron expression so it can reinstall the job.

Older configs containing `scan_interval` are translated when possible, including
hourly and whole-hour intervals, and log a deprecation warning with the exact
replacement expression. Replace that setting with `cron`; the app no longer keeps
Python and yt-dlp loaded between scans.

### Sonarr compatibility

Only Sonarr v4 is supported. Do not add a `version` setting. Sonarr v4 names its current HTTP routes `/api/v3`; that route name is the API contract version and does not enable support for the old Sonarr v3 application.

If Sonarr is behind a reverse proxy URL base, configure it without worrying about leading or trailing slashes:

```yaml
sonarr:
  host: sonarr.example.com
  port: 443
  ssl: true
  basedir: /sonarr
  apikey: your-api-key
```

### Running a scan manually

The scheduled command uses a lock so a slow download cannot overlap the next run. You can invoke that same one-shot command manually:

```bash
docker exec sonarr_youtubedl \
  flock -n /var/lock/sonarr_youtube.lock \
  uv run --project /opt/sonarr_youtubedl --locked --no-dev --no-sync \
  python -u /app/sonarr_youtubedl.py --config /config/config.yml
```

## Code layout and tests

The executable files in `app/` only handle cron startup and one-shot CLI errors. The testable application code is split by responsibility under `app/sytdl/`:

- `config.py` loads and validates YAML.
- `sonarr.py` is the injected HTTP client for Sonarr v4.
- `media.py` handles UTC dates, title matching patterns, and filenames.
- `downloader.py` is the injected yt-dlp adapter.
- `service.py` coordinates series, episodes, downloads, and rescans.

Dependencies and the reproducible environment are managed by [uv](https://docs.astral.sh/uv/). The committed `uv.lock` is the source of truth; there are no pip requirements files. yt-dlp is deliberately pinned to an exact version in `pyproject.toml`; the daily `update-ytdlp.yml` workflow updates that pin and the lockfile together, then dispatches a new Docker build. Docker syncs only the locked production dependencies, and every scheduled application run uses `uv run --locked --no-sync`. Sync the locked project and run the focused regression suite with:

```bash
uv sync --locked
uv run --locked pytest
```

<div align="center">

---

*Made with ❤️ for the Sonarr community*

</div>
