# act-scio2
SCIO v2 is a reimplementation of [SCIO|https://github.com/mnemonic-no/act-scio] in Python3.


## Source dode

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

### Running as a service

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
