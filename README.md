# act-scio2
SCIO v2 is a reimplementation of SCIO in Python3

## Source dode

The source code the workers are available on [github](https://github.com/mnemonic-no/act-scio2).

## Setup

To setup, install from PyPi:

```bash
sudo pip3 install act-scio
```

## API

To run the api, execute:


```bash
scio-api
```

This will setup the API on 127.0.0.1:3000. Use `--port <PORT> and --host <IP>` to listen on another port and/or another interface.

## Local development

Use pip to install in [local development mode](https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs). act-scio uses namespacing, so it is not compatible with using `setup.py install` or `setup.py develop`.

In repository, run:

```bash
pip3 install --user -e .
```
