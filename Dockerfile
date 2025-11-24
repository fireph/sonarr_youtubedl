FROM python:3-slim

COPY requirements.txt requirements.txt

ENV DENO_INSTALL="/usr/local"

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl unzip xz-utils && \
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
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# create some files / folders
RUN mkdir -p /config /app /sonarr_root /logs && \
    touch /var/lock/sonarr_youtube.lock

# add volumes
VOLUME /config /sonarr_root /logs

# add local files
COPY app/ /app

# update file permissions
RUN \
    chmod a+x \
    /app/sonarr_youtubedl.py \ 
    /app/utils.py \
    /app/config.yml.template

# ENV setup
ENV CONFIGPATH=/config/config.yml

CMD [ "python", "-u", "/app/sonarr_youtubedl.py" ]
