# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:0.11 AS uv
FROM python:3.14-slim

COPY --from=uv /uv /bin/uv

ENV DENO_INSTALL="/usr/local"

RUN apt-get update && \
    apt-get install -y --no-install-recommends cron curl tini unzip util-linux xz-utils && \
    curl -fsSL https://deno.land/install.sh | sh && \
    if [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
        FFMPEG_ARCH="linuxarm64"; \
    else \
        FFMPEG_ARCH="linux64"; \
    fi && \
    curl -L https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-${FFMPEG_ARCH}-gpl.tar.xz | tar xJ -C /tmp && \
    cp /tmp/ffmpeg-master-latest-${FFMPEG_ARCH}-gpl/bin/ffmpeg /usr/local/bin/ && \
    cp /tmp/ffmpeg-master-latest-${FFMPEG_ARCH}-gpl/bin/ffprobe /usr/local/bin/ && \
    rm -rf /tmp/ffmpeg-master-latest-${FFMPEG_ARCH}-gpl && \
    apt-get purge -y curl unzip xz-utils && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/sonarr_youtubedl

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# create some files / folders
RUN mkdir -p /config /app /sonarr_root /logs && \
    touch /var/lock/sonarr_youtube.lock

# add volumes
VOLUME /config /sonarr_root /logs

# add local files
COPY app/ /app

# update file permissions
RUN chmod a+x /app/sonarr_youtubedl.py /app/cron_entrypoint.py

# ENV setup
ENV CONFIGPATH=/config/config.yml
ENV LOGPATH=/logs/sonarr_youtubedl.log

ENTRYPOINT [ "/usr/bin/tini", "--" ]

# Use the uv-created environment for the short bootstrap, which then execs cron.
# Scheduled application runs themselves use `uv run` (see cron_entrypoint.py).
CMD [ "/opt/sonarr_youtubedl/.venv/bin/python", "-u", "/app/cron_entrypoint.py" ]
