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

**sonarr_youtubedl** is a powerful [Sonarr](https://sonarr.tv/) companion script that enables automatic downloading of web series normally unavailable to Sonarr. Leveraging [YT-DLP](https://github.com/yt-dlp/yt-dlp) (a feature-rich youtube-dl fork), it seamlessly downloads your favorite web series from hundreds of [supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

## Features

- **Web Series Download** - Access online sources unavailable to Sonarr
- **Format Control** - Specify video format globally or per series
- **Automatic Downloads** - New episodes downloaded as they become available
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
  -e USER_ID=1000 \
  -e GROUP_ID=1000 \
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
    environment:
      - USER_ID=1000
      - GROUP_ID=1000
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

### Environment Variables

| Variable | Default | Description |
|:--------:|:-------:|:------------|
| `USER_ID` | `1000` | Container user ID |
| `GROUP_ID` | `1000` | Container group ID |

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

<div align="center">

---

*Made with ❤️ for the Sonarr community*

</div>
