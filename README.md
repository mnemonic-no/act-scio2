# act-scio2
Scio v2 is a reimplementation of [Scio](https://github.com/mnemonic-no/act-scio) in Python3.

Scio uses [tika](https://tika.apache.org) to extract text from documents (PDF, HTML, DOC, etc).

The result is sent to the Scio Analyzer that extracts information using a combination of NLP
(Natural Language Processing) and pattern matching.

## Source code

The source code the workers are available on [github](https://github.com/mnemonic-no/act-scio2).

## Setup

To setup, first install from PyPi:

```bash
sudo pip3 install act-scio
```

You will also need to install [beanstalkd](https://beanstalkd.github.io/). On debian/ubuntu you can run:

```bash
sudo apt install beanstalkd
```

You then need to install NLTK data files. A helper utility to do this is included:

```bash
scio-nltk-download
```

You will also need to create a default configuration:

```bash
scio-config user
```

## API

To run the api, execute:


```bash
scio-api
```

This will setup the API on 127.0.0.1:3000. Use `--port <PORT> and --host <IP>` to listen on another port and/or another interface.

## Configuration

You can create a default configuration using this command (should be run as the user running scio):

```bash
scio-config user
```

Common configuration can be found under ~/.config/scio/etc/scio.ini

## Running Manually

### Scio Tika Server

The Scio Tika server reads jobs from the beanstalk tube `scio_doc` and the extracted text will be sent to the tube `scio_analyze`.

The first time the server runs, it will download tika using maven. It will use a proxy if `$https_proxy` is set.

```bash
scio-tika-server
```

### Scio Analyze Server

Scio Analyze Server reads (by default) jobs from the beanstalk tube `scio_analyze`.

```bash
scio-analyze
```

You can also read directly from stdin like this:

```bash
echo "The companies in the Bus; Finanical, Aviation and Automobile industry are large." | scio-analyze --beanstalk=
```

## Running as a service

Systemd compatible service scripts can be found under examples/systemd.

To install:

```bash
sudo cp examples/systemd/*.service /usr/lib/systemd/system
sudo systemctl enable scio-tika-server
sudo systemctl enable scio-analyze
sudo service start scio-tika-server
sudo service start scio-analyze
```

## Local development

Use pip to install in [local development mode](https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs). act-scio uses namespacing, so it is not compatible with using `setup.py install` or `setup.py develop`.

In repository, run:

```bash
pip3 install --user -e .
```
