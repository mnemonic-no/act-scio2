FROM docker.io/debian:bullseye

RUN apt update
RUN apt -y install openjdk-17-jdk-headless curl inetutils-ping telnet python3 python3-setuptools python3-pip

# Download tika jar+md5 that will be used by tika-server
RUN mkdir /opt/tika
ENV TIKA_VERSION=2.7.0
RUN curl -L --insecure -o /opt/tika/tika-server.jar \
    https://dlcdn.apache.org/tika/${TIKA_VERSION}/tika-server-standard-${TIKA_VERSION}.jar
RUN curl -L --insecure -o /opt/tika/tika-server.jar.md5 \
    https://dlcdn.apache.org/tika/${TIKA_VERSION}/tika-server-standard-${TIKA_VERSION}.jar.md5
RUN chmod -R go+rX /opt/tika

RUN useradd -ms /bin/bash scio
USER scio
WORKDIR /home/scio

# TIKA
COPY /docker/resources/nltk-download-insecure /var/tmp

RUN pip3 install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org nltk

RUN python3 /var/tmp/nltk-download-insecure

ENV PATH=$PATH:/home/scio/.local/bin

# All subsequent commands will be relative to /home/scio

RUN mkdir -p scio/dist

COPY /act scio/act
COPY /etc scio/etc
COPY /setup.py scio/setup.py
COPY /README.md scio/README.md

RUN mkdir -p .cache/scio .config
RUN chown scio:scio /home/scio/.cache/scio

RUN cd scio && \
    rm -f dist/*gz && \
    python3 setup.py sdist && \
    pip3 install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org dist/*gz

RUN scio-config user
