FROM lepinkainen/ubuntu-python-base
MAINTAINER Riku Lindblad "riku.lindblad@gmail.com"

# Add user to run as
RUN useradd -ms /bin/bash pyfibot
WORKDIR /home/pyfibot

# Clone as user to allow live upgrades etc
USER pyfibot
RUN git clone https://github.com/lepinkainen/pyfibot.git
WORKDIR pyfibot

# install requirements globally
USER root
RUN pip install --upgrade -r requirements.txt

# config
COPY config.yml /tmp/config.yml

USER pyfibot
ENTRYPOINT ["pyfibot/pyfibot.py", "/tmp/config.yml"]
