FROM docker.io/debian:buster

RUN apt update
RUN apt -y install curl inetutils-ping telnet python3 python3-setuptools python3-pip

RUN useradd -ms /bin/bash scio
USER scio

# All subsequent commands will be relative to /home/scio
WORKDIR /home/scio

RUN mkdir -p .config/pip scio/dist

COPY /docker/resources/pip.conf .config/pip
COPY /act scio/act
COPY /etc scio/etc
COPY /setup.py scio/setup.py
COPY /README.md scio/README.md

RUN mkdir -p /home/scio/.cache/scio
RUN chown scio:scio /home/scio/.cache/scio

RUN cd scio && \
    rm -f dist/*gz && \
    python3 setup.py sdist && \
    pip3 install dist/*gz

