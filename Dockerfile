FROM lepinkainen/ubuntu-python-base
MAINTAINER Riku Lindblad "riku.lindblad@gmail.com"

RUN apt-get install -y libffi-dev libssl-dev

RUN useradd -ms /bin/bash pyfibot
WORKDIR /home/pyfibot
USER pyfibot

RUN git clone https://github.com/lepinkainen/pyfibot.git
#USER root
WORKDIR pyfibot
RUN virtualenv .
RUN bin/pip install --upgrade -r requirements.txt

COPY config.yml /tmp/config.yml

ENTRYPOINT ["bin/python", "pyfibot/pyfibot.py", "/tmp/config.yml"]
