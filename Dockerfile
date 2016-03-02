FROM alpine
MAINTAINER Riku Lindblad "riku.lindblad@gmail.com"

RUN apk add --update \
    python \
    python-dev \
    build-base \
    git \
    py-pip \
    openssl-dev \
    libxml2-dev \
    libxslt-dev \
    libssl1.0 \
    libffi-dev

RUN pip install --upgrade pip

RUN git clone https://github.com/lepinkainen/pyfibot.git
WORKDIR pyfibot
RUN pip install --upgrade -r requirements.txt

RUN mkdir /config

VOLUME /config

ENTRYPOINT ["pyfibot/pyfibot.py", "/config/config.yml"]
