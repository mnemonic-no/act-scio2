FROM docker.io/debian:buster

RUN apt update
RUN apt -y install openjdk-11-jdk-headless curl inetutils-ping telnet python3 python3-setuptools python3-pip

# Download tika jar+md5 that will be used by tika-server
RUN mkdir /opt/tika
ENV TIKA_VERSION=1.28.1
RUN curl --insecure -o /opt/tika/tika-server.jar \
    https://repo1.maven.org/maven2/org/apache/tika/tika-server/${TIKA_VERSION}/tika-server-${TIKA_VERSION}.jar
RUN curl --insecure -o /opt/tika/tika-server.jar.md5 \
    https://repo1.maven.org/maven2/org/apache/tika/tika-server/${TIKA_VERSION}/tika-server-${TIKA_VERSION}.jar.md5
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

RUN mkdir -p /home/scio/.cache/scio
RUN chown scio:scio /home/scio/.cache/scio

RUN cd scio && \
    rm -f dist/*gz && \
    python3 setup.py sdist && \
    pip3 install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org dist/*gz
