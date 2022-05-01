# Docker files for scio

## Requirements

You will need docker and docker-compose to run scio in docker.

## Create network for SCIO containers

```bash
sudo docker network create scio
```

## Build using proxy

```bash
docker-compose build --build-arg http_proxy=http://<PROXY>:<PORT> --build-arg https_proxy http://<PROXY>:<PORT>
```

## Run

Build and run all components (currently except scio-feeds):

```bash
docker-compose up --build --remove-orphans
```

###
Remove all data from docker instance

```bash
docker-compose down --volumes
```
