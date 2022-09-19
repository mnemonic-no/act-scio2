# Docker files for scio

## Requirements

You will need docker and docker-compose to run scio in docker.

## Create network for SCIO containers

```bash
sudo docker network create scio
```

## Build images

```bash
docker-compose build
```

Build With proxy:

```bash
docker-compose build --build-arg http_proxy=http://<PROXY>:<PORT> --build-arg https_proxy http://<PROXY>:<PORT>
```

## Run

Run all components (currently except scio-feeds):

```bash
docker-compose up --remove-orphans
```

###
Remove all data from docker instance

```bash
docker-compose down --volumes
```
