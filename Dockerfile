FROM alpine
MAINTAINER Riku Lindblad "riku.lindblad@gmail.com"

RUN set -x \
    && apk add --no-cache --virtual .runtime-deps \
        python \
        libssl1.0 \
        ca-certificates \
    && apk add --no-cache --virtual .build-deps \
        python-dev \
        build-base \
        git \
        py-pip \
        openssl-dev \
        libxml2-dev \
        libxslt-dev \
        libffi-dev \
    && git clone https://github.com/lepinkainen/pyfibot.git /pyfibot \
    && rm -rf /pyfibot/.git \
    && cd /pyfibot \
    && pip install --upgrade -r requirements.txt \
    && apk del .build-deps \
    && mkdir /config

WORKDIR /pyfibot
VOLUME /config

ENTRYPOINT ["pyfibot/pyfibot.py", "/config/config.yml"]
