FROM python:3-slim

RUN apt-get update && \
    apt-get install -y ffmpeg curl unzip && \
    rm -rf /var/lib/apt/lists/*

# Install Deno
ENV DENO_INSTALL="/usr/local"
RUN curl -fsSL https://deno.land/install.sh | sh

# Copy and install requirements with optimizations
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# create some files / folders
RUN mkdir -p /config /app /sonarr_root /logs && \
    touch /var/lock/sonarr_youtube.lock

# add volumes
VOLUME /config
VOLUME /sonarr_root
VOLUME /logs

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
