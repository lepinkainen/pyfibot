FROM debian:stretch-slim
LABEL maintainer="riku.lindblad@gmail.com"

RUN apt-get update && apt-get -y install \ 
    python \
    python-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/lepinkainen/pyfibot.git /pyfibot

WORKDIR /pyfibot

RUN pip install pipenv && pipenv install

WORKDIR /pyfibot
VOLUME /config

ENTRYPOINT ["/usr/local/bin/pipenv run", "pyfibot/pyfibot.py", "/config/config.yml"]
